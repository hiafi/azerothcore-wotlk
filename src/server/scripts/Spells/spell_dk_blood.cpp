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
 * Death Knight rework - Blood spell scripts (death-knight-rework S1a; docs/reworks/death-knight-blood-rework.md).
 * The UnitScript / PlayerScript hooks (Purgatory, Voracious, leech, Blood Shield, Red Thirst, Bloodworm damage) live
 * in deathknight_hooks.cpp and DeathKnightMechanics.cpp; this file holds the spell and aura scripts.
 */

#include "DataMap.h"
#include "DeathKnightMechanics.h"
#include "DynamicObject.h"
#include "EngagementMechanics.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Timer.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <vector>

namespace
{
    // Stock ids the DSL does not declare (the rework does not edit them), so DeathKnightData has no name for them.
    constexpr uint32 SPELL_DK_DEATH_COIL_DAMAGE = 47632;
    constexpr uint32 SPELL_DK_DEATH_GRIP_JUMP = 57604;
    constexpr uint32 SPELL_DK_SCENT_OF_BLOOD_ENERGIZE = 50422;

    // Blood Boil's family bit (SpellClassSet 15, d0 b18): the one area spell a Dancing Rune Weapon copy repeats
    constexpr uint32 BLOOD_BOIL_FAMILY_D0 = 0x00040000;
    // Raise Dead / Raise Ally, Death Grip, Dark Command, Death Pact, Death and Decay, Anti-Magic Shell (stock mask)
    constexpr uint32 DRW_STOCK_EXCLUDED_D0 = 0x020A1220;
    constexpr uint32 DRW_STOCK_EXCLUDED_D1 = 0x10000000;

    // Gorefiend's Grasp: where the explicit target stands, handed to the per-target helper cast. The helper is cast
    // synchronously from the same call, so the value is set and cleared around the casts and never outlives them.
    struct GraspDestination : DataMap::Base
    {
        bool valid = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    constexpr char const* GRASP_DESTINATION_KEY = "deathknight_gorefiends_grasp_destination";

    Player* GetPlayerCaster(Unit* caster)
    {
        return caster ? caster->ToPlayer() : nullptr;
    }

    // Bloody Vengeance stack for the highest rank the Death Knight knows (rank spell -> its stack buff)
    uint32 GetBloodyVengeanceBuff(Unit const* dk)
    {
        if (dk->HasAura(DeathKnightData::SPELL_BLOODY_VENGEANCE_49504))
            return DeathKnightData::SPELL_BLOODY_VENGEANCE_50449;
        if (dk->HasAura(DeathKnightData::SPELL_BLOODY_VENGEANCE_49503))
            return DeathKnightData::SPELL_BLOODY_VENGEANCE_50448;
        if (dk->HasAura(DeathKnightData::SPELL_BLOODY_VENGEANCE))
            return DeathKnightData::SPELL_BLOODY_VENGEANCE_50447;
        return 0;
    }

    // Rune of Unending Thirst's crit proc (20% chance, 30 s internal cooldown on the rune aura), rolled by hand for a
    // hit that is flagged SUPPRESS_CASTER_PROCS and so never reaches the proc system (Bonestorm's tick).
    void TryGrantUnendingThirst(Player* dk)
    {
        Aura* rune = dk->GetAura(DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST);
        SpellProcEntry const* procEntry = sSpellMgr->GetSpellProcEntry(DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST);
        if (!rune || !procEntry)
            return;

        TimePoint const now = Acore::Time::SteadyNow();
        if (rune->IsProcOnCooldown(now))
            return;

        float chance = procEntry->Chance;
        dk->ApplySpellMod(DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST, SPELLMOD_CHANCE_OF_SUCCESS, chance);
        // the Proc Chance stat, as Aura::CalcProcChance applies it to every native proc
        chance *= 1.0f + dk->GetProcChancePercentage() / 100.0f;
        if (!roll_chance_f(chance))
            return;

        rune->AddProcCooldown(procEntry, now);
        dk->CastSpell(dk, DeathKnightData::SPELL_UNENDING_THIRST, TRIGGERED_FULL_MASK);
    }

    // Vendetta's strike heal percent for the highest rank known (the percent is a const per rank, not an effect)
    int32 GetVendettaStrikeHealPct(Unit const* dk)
    {
        if (dk->HasAura(DeathKnightData::SPELL_VENDETTA_55136))
            return DeathKnightData::VENDETTA_STRIKE_HEAL_PCT_RANK3;
        if (dk->HasAura(DeathKnightData::SPELL_VENDETTA_50154))
            return DeathKnightData::VENDETTA_STRIKE_HEAL_PCT_RANK2;
        if (dk->HasAura(DeathKnightData::SPELL_VENDETTA))
            return DeathKnightData::VENDETTA_STRIKE_HEAL_PCT_RANK1;
        return 0;
    }
}

// 203123 - Marrowrend. The weapon effects deal 80% weapon damage plus a flat; the hit also gives Bone Shield charges
// (a Death Knight cast only: a Dancing Rune Weapon copy deals plain damage and grants nothing). At the charge cap the
// hit deals MARROWREND_CAP_BONUS_PCT% more damage instead. OnHit, not OnEffectHitTarget: the effect hook runs before
// the default handler has produced any damage.
class spell_dk_marrowrend : public SpellScript
{
    PrepareSpellScript(spell_dk_marrowrend);

    void HandleHit()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
            return;

        if (DeathKnight::GetBoneShieldCharges(player) < DeathKnightData::BONE_SHIELD_MAX_CHARGES)
            return;

        int64 const damage = GetHitDamage();
        SetHitDamage(int32(damage * (100 + DeathKnightData::MARROWREND_CAP_BONUS_PCT) / 100));
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player || _granted)
            return;

        _granted = true;
        DeathKnight::AddBoneShieldCharges(player, uint8(DeathKnightData::MARROWREND_CHARGES));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dk_marrowrend::HandleHit);
        AfterHit += SpellHitFn(spell_dk_marrowrend::HandleAfterHit);
    }

    bool _granted = false;
};

// 203127 - Gorefiend's Grasp. An explicit target (enemy, friend or self); the 15 yd area around it keeps only enemies
// already in combat with the Death Knight or the group, never a world or dungeon boss, never the caster. After the
// cast each kept enemy gets the helper 203128 (triggered; its Grip mechanic lets grip-immune creatures resist), which
// moves it to the explicit target's position and adds the threat.
class spell_dk_gorefiends_grasp : public SpellScript
{
    PrepareSpellScript(spell_dk_gorefiends_grasp);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_GOREFIENDS_GRASP_PULL });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        _pulled.clear();

        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
        {
            targets.clear();
            return;
        }

        targets.remove_if([player](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            if (!unit || unit == player || !unit->IsAlive() || !player->IsValidAttackTarget(unit))
                return true;

            if (Creature const* creature = unit->ToCreature())
                if (creature->isWorldBoss() || creature->IsDungeonBoss())
                    return true;

            return !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });

        for (WorldObject* object : targets)
            _pulled.push_back(object->GetGUID());
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player || _pulled.empty())
            return;

        Unit* anchor = GetExplTargetUnit();
        if (!anchor)
            anchor = player;

        GraspDestination* destination = player->CustomData.GetDefault<GraspDestination>(GRASP_DESTINATION_KEY);
        destination->valid = true;
        destination->x = anchor->GetPositionX();
        destination->y = anchor->GetPositionY();
        destination->z = anchor->GetPositionZ();

        for (ObjectGuid const& guid : _pulled)
            if (Unit* enemy = ObjectAccessor::GetUnit(*player, guid))
                if (enemy->IsAlive())
                    player->CastSpell(enemy, DeathKnightData::SPELL_GOREFIENDS_GRASP_PULL, TRIGGERED_FULL_MASK);

        destination->valid = false;
        _pulled.clear();
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_gorefiends_grasp::FilterTargets, EFFECT_ALL,
            TARGET_UNIT_DEST_AREA_ENEMY);
        AfterCast += SpellCastFn(spell_dk_gorefiends_grasp::HandleAfterCast);
    }

    std::vector<ObjectGuid> _pulled;
};

// 203128 - Gorefiend's Grasp Pull (hidden helper, cast by the Death Knight at each enemy). The enemy jumps to the
// position the main spell stored (the Death Grip 57604 shape) and the Death Knight gets threat on it: the helper's
// 50-potency value, read from the generated coefficient (the flat plus the AP coefficient times attack power, the
// Anti-Magic Zone pool shape: the engine adds neither to a non-damage effect).
class spell_dk_gorefiends_grasp_pull : public SpellScript
{
    PrepareSpellScript(spell_dk_gorefiends_grasp_pull);

    static float ComputeThreat(Unit* caster)
    {
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_GOREFIENDS_GRASP_PULL);
        if (!spellInfo)
            return 0.0f;

        float threat = float(std::max<int32>(0, spellInfo->Effects[EFFECT_0].CalcValue(caster)));
        if (SpellBonusEntry const* bonus = sSpellMgr->GetSpellBonusData(DeathKnightData::SPELL_GOREFIENDS_GRASP_PULL))
            if (bonus->ap_bonus > 0.0f)
                threat += bonus->ap_bonus * caster->GetTotalAttackPowerValue(BASE_ATTACK);

        return std::max(0.0f, threat);
    }

    void HandlePull(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster || !target->IsAlive())
            return;

        GraspDestination* destination = caster->CustomData.Get<GraspDestination>(GRASP_DESTINATION_KEY);
        if (!destination || !destination->valid)
            return;

        // Same as Death Grip: a pulled caster stops casting; the jump itself is the 57604 helper cast from the target
        if (target->GetExactDist(destination->x, destination->y, destination->z) > 1.0f)
        {
            target->InterruptNonMeleeSpells(false);
            target->CastSpell(destination->x, destination->y, destination->z, SPELL_DK_DEATH_GRIP_JUMP, true);
        }

        if (float const threat = ComputeThreat(caster))
            target->AddThreat(caster, threat);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dk_gorefiends_grasp_pull::HandlePull, EFFECT_FIRST_FOUND,
            SPELL_EFFECT_ANY);
    }
};

// 203132 - Sanguine Ground (hidden self aura, cast by the 43265 script when the Death Knight knows the capstone).
// Every second the Death Knight standing inside their own Death and Decay is healed for SANGUINE_HEAL_PCT% of
// maximum health, enemies or not; the heal is a separate spell so it takes Versatility and the healing-taken mods.
class spell_dk_sanguine_ground : public AuraScript
{
    PrepareAuraScript(spell_dk_sanguine_ground);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_SANGUINE_GROUND_HEAL });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* target = GetTarget();
        if (!target || !target->IsAlive())
            return;

        DynamicObject* zone = target->GetDynObject(DeathKnightData::SPELL_DEATH_AND_DECAY);
        if (!zone || !zone->IsWithinDist(target, zone->GetRadius()))
            return;

        int32 const heal = int32(target->CountPctFromMaxHealth(DeathKnightData::SANGUINE_HEAL_PCT));
        if (heal > 0)
            target->CastCustomSpell(DeathKnightData::SPELL_SANGUINE_GROUND_HEAL, SPELLVALUE_BASE_POINT0, heal, target,
                TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_sanguine_ground::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 43265 - Death and Decay (a player-gated script beside the stock pair; Hexlord Malacrass casts the same id, so a
// non-player caster returns at once). Before the cast: a new Death and Decay replaces the old one, Blood Gorged's
// state is snapshotted (U13), and Crimson Scourge's buff and the Runic Power are remembered. After the cast: when the
// free cast ate the buff, the Runic Power the rune cost still paid out is put back (the free cast makes none), and
// the Sanguine Ground capstone starts its heal aura. The buff's charge is taken by the spell mod when the immediate
// cast finishes, which is before the cast's AfterCast hook, so the buff is gone by then.
class spell_dk_death_and_decay_blood : public SpellScript
{
    PrepareSpellScript(spell_dk_death_and_decay_blood);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_CRIMSON_SCOURGE_BUFF,
            DeathKnightData::SPELL_SANGUINE_GROUND_203131, DeathKnightData::SPELL_SANGUINE_GROUND_TICK });
    }

    void HandleBeforeCast()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
            return;

        player->RemoveDynObject(DeathKnightData::SPELL_DEATH_AND_DECAY);
        DeathKnight::SnapshotBloodGorged(player, DeathKnightData::SPELL_DEATH_AND_DECAY);

        _hadBuff = player->HasAura(DeathKnightData::SPELL_CRIMSON_SCOURGE_BUFF);
        _power = player->GetPower(POWER_RUNIC_POWER);
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
            return;

        if (_hadBuff && !player->HasAura(DeathKnightData::SPELL_CRIMSON_SCOURGE_BUFF) &&
            player->GetPower(POWER_RUNIC_POWER) > _power)
            player->SetPower(POWER_RUNIC_POWER, _power);

        if (player->HasAura(DeathKnightData::SPELL_SANGUINE_GROUND_203131))
            player->CastSpell(player, DeathKnightData::SPELL_SANGUINE_GROUND_TICK, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_dk_death_and_decay_blood::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_dk_death_and_decay_blood::HandleAfterCast);
    }

    bool _hadBuff = false;
    uint32 _power = 0;
};

// 52212 - Death and Decay tick (a player-gated second script beside the stock one; the stock script keeps its own
// OnHit). Blood Gorged is checked when the Death and Decay is cast, not per tick (U13): the damage the engine just
// computed is corrected from the live state to the cast-time state. It grants no Bloody Vengeance and no Unending
// Thirst: the tick is not SUPPRESS_CASTER_PROCS, so a crit procs them natively.
class spell_dk_death_and_decay_tick_blood : public SpellScript
{
    PrepareSpellScript(spell_dk_death_and_decay_tick_blood);

    void HandleHit()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
            return;

        float const multiplier = DeathKnight::GetBloodGorgedTickMultiplier(player,
            DeathKnightData::SPELL_DEATH_AND_DECAY);
        if (multiplier != 1.0f)
            SetHitDamage(std::max<int32>(0, int32(float(GetHitDamage()) * multiplier)));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dk_death_and_decay_tick_blood::HandleHit);
    }
};

// -203134 - Crimson Scourge (rank chain, proc row: auto attacks of either hand). Only the owner's own auto attack
// against a target carrying the owner's Blood Plague rolls the proc.
class spell_dk_crimson_scourge : public AuraScript
{
    PrepareAuraScript(spell_dk_crimson_scourge);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!owner || !victim || eventInfo.GetActor() != owner || eventInfo.GetSpellInfo())
            return false;

        return victim->HasAura(DeathKnightData::SPELL_BLOOD_PLAGUE, owner->GetGUID());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_crimson_scourge::CheckProc);
    }
};

// 203137 - Crimson Scourge (the buff: the next Death and Decay costs no runes). Gaining it resets Death and Decay's
// cooldown; the free cast itself is the spell mod on 43265.
class spell_dk_crimson_scourge_buff : public AuraScript
{
    PrepareAuraScript(spell_dk_crimson_scourge_buff);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetPlayerCaster(GetTarget()))
            player->RemoveSpellCooldown(DeathKnightData::SPELL_DEATH_AND_DECAY, true);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_crimson_scourge_buff::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 203141 - Crimson Communion. The party area (40 yd) also reaches pets and guardians: only players are kept.
class spell_dk_crimson_communion : public SpellScript
{
    PrepareSpellScript(spell_dk_crimson_communion);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject* object)
        {
            return !object->IsPlayer();
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_crimson_communion::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_CASTER_AREA_PARTY);
    }
};

// 203143 - Blood Nova. The health is a cost, not damage: refused at or below BLOOD_NOVA_COST_PCT% of maximum health,
// taken with ModifyHealth (no damage path: no absorbs, no Purgatory, no Death Strike record). BLOOD_NOVA_DELAY_MS
// later the Death Knight, if still alive, erupts for BLOOD_NOVA_DAMAGE_PCT% of the maximum health at cast time.
class spell_dk_blood_nova : public SpellScript
{
    PrepareSpellScript(spell_dk_blood_nova);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_BLOOD_NOVA_ERUPTION });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster || caster->GetHealth() <= caster->CountPctFromMaxHealth(DeathKnightData::BLOOD_NOVA_COST_PCT))
            return SPELL_FAILED_CASTER_AURASTATE;   // what the engine returns for a health cost (Spell::CheckPower)

        return SPELL_CAST_OK;
    }

    void HandleCast()
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsAlive())
            return;

        int32 const cost = int32(caster->CountPctFromMaxHealth(DeathKnightData::BLOOD_NOVA_COST_PCT));
        int32 const eruption = int32(caster->CountPctFromMaxHealth(DeathKnightData::BLOOD_NOVA_DAMAGE_PCT));
        caster->ModifyHealth(-std::min<int32>(cost, std::max<int32>(0, int32(caster->GetHealth()) - 1)));

        // The event lives in the caster's own queue, so the captured pointer is valid whenever it runs
        caster->m_Events.AddEventAtOffset([caster, eruption]()
        {
            if (!caster->IsAlive())
                return;

            caster->CastCustomSpell(DeathKnightData::SPELL_BLOOD_NOVA_ERUPTION, SPELLVALUE_BASE_POINT0, eruption,
                caster, TRIGGERED_FULL_MASK);
        }, Milliseconds(DeathKnightData::BLOOD_NOVA_DELAY_MS));
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dk_blood_nova::CheckCast);
        OnCast += SpellCastFn(spell_dk_blood_nova::HandleCast);
    }
};

// 203146 - Shroud of Purgatory. The aura's removal always reaches the Death Knight mechanics (they clear the stored
// attacker); only running out with healing still owed is a death, which OnShroudExpired decides from the amount.
class spell_dk_shroud_of_purgatory : public AuraScript
{
    PrepareAuraScript(spell_dk_shroud_of_purgatory);

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target)
            return;

        bool const expired = GetTargetApplication() && GetTargetApplication()->GetRemoveMode() == AURA_REMOVE_BY_EXPIRE;
        DeathKnight::OnShroudExpired(target, expired ? std::max<int32>(0, aurEff->GetAmount()) : 0);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_shroud_of_purgatory::HandleRemove, EFFECT_0,
            SPELL_AURA_SCHOOL_HEAL_ABSORB, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203148 - Bonestorm. Spends all Runic Power (USE_ALL_MANA makes the engine's own check always pass, so the minimum is
// checked here) and is refused while already active. The aura lasts 1 s per 10 Runic Power actually spent, up to
// BONESTORM_MAX_MS. Blood Gorged's state is snapshotted at the cast (U13).
class spell_dk_bonestorm : public SpellScript
{
    PrepareSpellScript(spell_dk_bonestorm);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return SPELL_FAILED_DONT_REPORT;

        if (caster->HasAura(DeathKnightData::SPELL_BONESTORM))
            return SPELL_FAILED_AURA_BOUNCED;

        // Runic Power is stored x10
        if (caster->GetPower(POWER_RUNIC_POWER) < uint32(DeathKnightData::BONESTORM_MIN_RP) * 10)
            return SPELL_FAILED_NO_POWER;

        return SPELL_CAST_OK;
    }

    void HandleBeforeCast()
    {
        if (Player* player = GetPlayerCaster(GetCaster()))
            DeathKnight::SnapshotBloodGorged(player, DeathKnightData::SPELL_BONESTORM);
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        Aura* aura = caster ? caster->GetAura(DeathKnightData::SPELL_BONESTORM) : nullptr;
        if (!aura)
            return;

        // m_powerCost is the Runic Power spent, x10; 1 s per 10 displayed Runic Power
        uint64 const spent = uint64(std::max<int32>(0, GetSpell()->GetPowerCost()));
        uint64 const durationMs = std::min<uint64>(uint64(DeathKnightData::BONESTORM_MAX_MS),
            spent * uint64(DeathKnightData::BONESTORM_MS_PER_10_RP) / 100);
        if (!durationMs)
            return;

        aura->SetMaxDuration(int32(durationMs));
        aura->SetDuration(int32(durationMs));
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dk_bonestorm::CheckCast);
        BeforeCast += SpellCastFn(spell_dk_bonestorm::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_dk_bonestorm::HandleAfterCast);
    }
};

// 203149 - Bonestorm Tick (hasted, 8 yd, cast by the aura's periodic trigger; SUPPRESS_CASTER_PROCS). Per target the
// damage is corrected to the cast-time Blood Gorged state (U13). After the cast: the Death Knight heals
// BONESTORM_HEAL_PCT% of the current maximum health per enemy hit (at most BONESTORM_HEAL_TARGET_CAP enemies), and a
// crit anywhere in the tick grants Bloody Vengeance and rolls Rune of Unending Thirst, once per tick (the tick's
// procs are suppressed, so the stacks are explicit).
class spell_dk_bonestorm_tick : public SpellScript
{
    PrepareSpellScript(spell_dk_bonestorm_tick);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_BONESTORM_HEAL });
    }

    void HandleHit()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player)
            return;

        float const multiplier = DeathKnight::GetBloodGorgedTickMultiplier(player, DeathKnightData::SPELL_BONESTORM);
        if (multiplier != 1.0f)
            SetHitDamage(std::max<int32>(0, int32(float(GetHitDamage()) * multiplier)));
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerCaster(GetCaster());
        if (!player || !player->IsAlive())
            return;

        int32 hits = 0;
        bool crit = false;
        for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
        {
            if (info.missCondition != SPELL_MISS_NONE)
                continue;

            ++hits;
            crit = crit || info.crit;
        }

        if (hits > 0)
        {
            int32 const healed = std::min<int32>(hits, DeathKnightData::BONESTORM_HEAL_TARGET_CAP);
            int32 const heal = int32(player->CountPctFromMaxHealth(DeathKnightData::BONESTORM_HEAL_PCT * healed));
            if (heal > 0)
                player->CastCustomSpell(DeathKnightData::SPELL_BONESTORM_HEAL, SPELLVALUE_BASE_POINT0, heal, player,
                    TRIGGERED_FULL_MASK);
        }

        if (!crit)
            return;

        if (uint32 const buff = GetBloodyVengeanceBuff(player))
            player->CastSpell(player, buff, TRIGGERED_FULL_MASK);

        TryGrantUnendingThirst(player);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dk_bonestorm_tick::HandleHit);
        AfterCast += SpellCastFn(spell_dk_bonestorm_tick::HandleAfterCast);
    }
};

// 49491 - Subversion rank 3. The Runic Power effect rolls once per cast (Heart Strike's second target adds nothing).
class spell_dk_subversion_capstone : public AuraScript
{
    PrepareAuraScript(spell_dk_subversion_capstone);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return _guard.OwnerFirst(GetTarget(), eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_subversion_capstone::CheckProc);
    }

    DeathKnight::OncePerCastGuard _guard;
};

// 203153 - Vendetta Strike (hidden passive granted with every Vendetta rank). The Death Knight's own Heart Strike and
// Marrowrend hits heal for the rank's percent of the damage each hit dealt (per target: Heart Strike's second target
// heals too). A Dancing Rune Weapon copy is another actor and never triggers it.
class spell_dk_vendetta_strike : public AuraScript
{
    PrepareAuraScript(spell_dk_vendetta_strike);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_VENDETTA_STRIKE_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (eventInfo.GetActor() != GetTarget())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!spellInfo || !damageInfo || !damageInfo->GetDamage())
            return false;

        return spellInfo->Id == DeathKnightData::SPELL_HEART_STRIKE ||
            spellInfo->Id == DeathKnightData::SPELL_MARROWREND;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* owner = GetTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!owner || !damageInfo)
            return;

        int32 const heal = int32(CalculatePct(damageInfo->GetDamage(), GetVendettaStrikeHealPct(owner)));
        if (heal > 0)
            owner->CastCustomSpell(DeathKnightData::SPELL_VENDETTA_STRIKE_HEAL, SPELLVALUE_BASE_POINT0, heal, owner,
                TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_vendetta_strike::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_vendetta_strike::HandleProc, EFFECT_0, SPELL_AURA_ANY);
    }
};

// 203155 - Blood Gorged Mastery (hidden passive on Blood Gorged rank 3). Every second the damage passive's amount is
// brought to the rank percent plus half of Mastery.
class spell_dk_blood_gorged_mastery : public AuraScript
{
    PrepareAuraScript(spell_dk_blood_gorged_mastery);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetPlayerCaster(GetTarget()))
            DeathKnight::RefreshBloodGorged(player);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_blood_gorged_mastery::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// -49027 - Bloodworms (talent rank chain). Auto attacks roll per hit; abilities once per cast. The summon itself is the
// aura's own effect (fixed 2 worms); the cap is applied by spell_dk_bloodworms_rework.
class spell_dk_bloodworms_talent : public AuraScript
{
    PrepareAuraScript(spell_dk_bloodworms_talent);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return _guard.OwnerFirst(GetTarget(), eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_bloodworms_talent::CheckProc);
    }

    DeathKnight::OncePerCastGuard _guard;
};

// 50452 - Bloodworm (replaces the stock spell_dk_bloodworms, whose irand(2, 4) count is gone: the count is the effect
// value). After the summon at most BLOODWORM_CAP worms stay, the oldest dismissed. A player caster only.
class spell_dk_bloodworms_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_bloodworms_rework);

    void HandleAfterCast()
    {
        if (Player* player = GetPlayerCaster(GetCaster()))
            DeathKnight::CapBloodworms(player);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dk_bloodworms_rework::HandleAfterCast);
    }
};

// 50453 - Bloodworms Health Leech (replaces the stock spell_dk_blood_gorged; the aura is on each worm). Damage the
// worm deals heals its owner for BLOODWORM_HEAL_PCT% of it, as the worm's own heal spell (so the owner's
// healing-taken mods and the Voracious capstone see it).
class spell_dk_bloodworm_heal_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_bloodworm_heal_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_HEALTH_LEECH_50454 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* worm = GetTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!worm || eventInfo.GetActor() != worm || !damageInfo || !damageInfo->GetDamage())
            return false;

        Unit* owner = worm->GetOwner();
        return owner && owner->IsPlayer() && owner->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* worm = GetTarget();
        Unit* owner = worm ? worm->GetOwner() : nullptr;
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!owner || !damageInfo)
            return;

        int32 const heal = int32(CalculatePct(damageInfo->GetDamage(), DeathKnightData::BLOODWORM_HEAL_PCT));
        if (heal > 0)
            worm->CastCustomSpell(DeathKnightData::SPELL_HEALTH_LEECH_50454, SPELLVALUE_BASE_POINT0, heal, owner,
                TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_bloodworm_heal_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_bloodworm_heal_rework::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 49028 - Dancing Rune Weapon (replaces the stock spell_dk_dancing_rune_weapon). The stock CheckProc / HandleProc
// shape with: one copy per cast (Heart Strike's two hits gave two copies, each cleaving), the exclusion list of
// DeathKnight::IsRuneWeaponExcluded, Blood Boil copied once per cast from the weapon (stock never copies a
// self-centred area spell), and the threat redirect registered on EFFECT_1 (stock used EFFECT_2, which the core
// zeroes). The once-per-cast guard is this aura's own (DeathKnight::OncePerCastGuard).
class spell_dk_dancing_rune_weapon_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_dancing_rune_weapon_rework);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        // Redirect 100% of the rune weapon's threat to the Death Knight
        uint32 const npcEntry = GetSpellInfo()->Effects[EFFECT_0].MiscValue;
        std::list<Creature*> runeWeapons;
        caster->GetAllMinionsByEntry(runeWeapons, npcEntry);
        for (Creature* runeWeapon : runeWeapons)
            runeWeapon->GetThreatMgr().RegisterRedirectThreat(GetId(), caster->GetGUID(), 100);
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* actor = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();
        if (!actor || !target || !target->IsAlive() || !actor->IsPlayer() || actor != GetTarget())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return true;

        // Death Coil exception, check that the spell is from the spellbook
        if (spellInfo->Id != SPELL_DK_DEATH_COIL_DAMAGE && !actor->ToPlayer()->HasActiveSpell(spellInfo->Id))
            return false;

        // Raise dead/ally, death grip, dark command, death pact, death and decay, anti-magic shell
        if (spellInfo->SpellFamilyFlags.HasFlag(DRW_STOCK_EXCLUDED_D0, DRW_STOCK_EXCLUDED_D1, 0x0))
            return false;

        if (DeathKnight::IsRuneWeaponExcluded(spellInfo->Id))
            return false;

        // Area spells: only Blood Boil, once per cast
        if (spellInfo->IsTargetingArea() && !spellInfo->SpellFamilyFlags.HasFlag(BLOOD_BOIL_FAMILY_D0, 0x0, 0x0))
            return false;

        // No spells with summoning
        if (spellInfo->HasEffect(SPELL_EFFECT_SUMMON))
            return false;

        // No positive spells
        if (spellInfo->IsPositive())
            return false;

        return _guard.First(eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* player = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();
        Unit* runeWeapon = nullptr;
        int32 const npcEntry = GetSpellInfo()->Effects[EFFECT_0].MiscValue;
        for (Unit* controlled : player->m_Controlled)
            if (int32(controlled->GetEntry()) == npcEntry)
            {
                runeWeapon = controlled;
                break;
            }

        if (!runeWeapon)
            return;

        runeWeapon->SetOrientation(runeWeapon->GetAngle(target));
        if (SpellInfo const* procSpell = eventInfo.GetSpellInfo())
        {
            if (procSpell->IsAffectingArea())
            {
                // Blood Boil: the weapon erupts around itself
                runeWeapon->CastSpell(runeWeapon, procSpell->Id, true, nullptr, aurEff, runeWeapon->GetGUID());
                return;
            }

            // xinef: ugly hack, kept from stock
            player->SetFloatValue(UNIT_FIELD_COMBATREACH, 10.0f);
            runeWeapon->CastSpell(target, procSpell->Id, true, nullptr, aurEff, runeWeapon->GetGUID());
            player->SetFloatValue(UNIT_FIELD_COMBATREACH, 0.01f);
        }
        else if (eventInfo.GetDamageInfo())
        {
            target = player->GetMeleeHitRedirectTarget(target);
            CalcDamageInfo damageInfo;
            player->CalculateMeleeDamage(target, &damageInfo, eventInfo.GetDamageInfo()->GetAttackType());
            for (uint8 i = 0; i < MAX_ITEM_PROTO_DAMAGES; ++i)
            {
                Unit::DealDamageMods(target, damageInfo.damages[i].damage, &damageInfo.damages[i].absorb);
                damageInfo.damages[i].damage /= 2.0f;
            }
            damageInfo.attacker = runeWeapon;
            runeWeapon->SendAttackStateUpdate(&damageInfo);
            runeWeapon->DealMeleeDamage(&damageInfo, true);
        }
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_dancing_rune_weapon_rework::HandleApply, EFFECT_1,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        DoCheckProc += AuraCheckProcFn(spell_dk_dancing_rune_weapon_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_dancing_rune_weapon_rework::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }

    DeathKnight::OncePerCastGuard _guard;
};

// 55078 - Blood Plague, 55095 - Frost Fever. A Dancing Rune Weapon copy (Plague Strike, Icy Touch) applies no disease.
// Both ids are also static creature auras and an NPC can cast them: every other caster is left alone.
class spell_dk_disease_rune_weapon_guard : public SpellScript
{
    PrepareSpellScript(spell_dk_disease_rune_weapon_guard);

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (caster && DeathKnight::IsRuneWeapon(caster))
            PreventHitAura();
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dk_disease_rune_weapon_guard::HandleHit, EFFECT_0,
            SPELL_EFFECT_APPLY_AURA);
    }
};

// 50421 - Scent of Blood (replaces the stock spell_dk_scent_of_blood, which removed a stack). The buff now carries
// ProcCharges 3, which the engine takes one at a time for every accepted proc, so the script only decides which
// events count (an auto attack or an ability once per cast, not a second target's hit) and pays the Runic Power.
class spell_dk_scent_of_blood_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_scent_of_blood_rework);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return _guard.OwnerFirst(GetTarget(), eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        target->CastSpell(target, SPELL_DK_SCENT_OF_BLOOD_ENERGIZE, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_scent_of_blood_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_scent_of_blood_rework::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }

    DeathKnight::OncePerCastGuard _guard;
};

// -49018 - Sudden Doom (a second script beside the stock spell_dk_sudden_doom, which keeps HandleProc). Heart Strike
// and Blood Boil roll once per cast, not once per target.
class spell_dk_sudden_doom_once : public AuraScript
{
    PrepareAuraScript(spell_dk_sudden_doom_once);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return _guard.OwnerFirst(GetTarget(), eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_sudden_doom_once::CheckProc);
    }

    DeathKnight::OncePerCastGuard _guard;
};

void AddSC_deathknight_blood_spell_scripts()
{
    RegisterSpellScript(spell_dk_marrowrend);
    RegisterSpellScript(spell_dk_gorefiends_grasp);
    RegisterSpellScript(spell_dk_gorefiends_grasp_pull);
    RegisterSpellScript(spell_dk_sanguine_ground);
    RegisterSpellScript(spell_dk_death_and_decay_blood);
    RegisterSpellScript(spell_dk_death_and_decay_tick_blood);
    RegisterSpellScript(spell_dk_crimson_scourge);
    RegisterSpellScript(spell_dk_crimson_scourge_buff);
    RegisterSpellScript(spell_dk_crimson_communion);
    RegisterSpellScript(spell_dk_blood_nova);
    RegisterSpellScript(spell_dk_shroud_of_purgatory);
    RegisterSpellScript(spell_dk_bonestorm);
    RegisterSpellScript(spell_dk_bonestorm_tick);
    RegisterSpellScript(spell_dk_subversion_capstone);
    RegisterSpellScript(spell_dk_vendetta_strike);
    RegisterSpellScript(spell_dk_blood_gorged_mastery);
    RegisterSpellScript(spell_dk_bloodworms_talent);
    RegisterSpellScript(spell_dk_bloodworms_rework);
    RegisterSpellScript(spell_dk_bloodworm_heal_rework);
    RegisterSpellScript(spell_dk_dancing_rune_weapon_rework);
    RegisterSpellScript(spell_dk_disease_rune_weapon_guard);
    RegisterSpellScript(spell_dk_scent_of_blood_rework);
    RegisterSpellScript(spell_dk_sudden_doom_once);
}
