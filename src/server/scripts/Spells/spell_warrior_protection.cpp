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
 * Warrior rework - Protection SpellScripts (warrior-rework S1; docs/reworks/warrior-protection-rework.md). The Prot
 * classes that used to live in stock spell_warrior.cpp moved here under their old names (their spell_script_names rows
 * keep working). Storm's Bulwark, the cooldown helper, Sword and Board and the percent-of-damage bleed live in
 * WarriorMechanics; the cast-start dispatcher (Incite stamp, Sword and Board roll, Improved Bloodrage, Last Stand
 * record) lives in warrior_hooks.cpp.
 */

#include "EngagementMechanics.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "Unit.h"
#include "WarriorMechanics.h"
#include <algorithm>
#include <initializer_list>
#include <list>

namespace
{
    // Stock rows not in WarriorData.
    constexpr uint32 SPELL_SUNDER_ARMOR_DEVASTATE = 58567; // the Sunder Armor Devastate applies (SpellEffects.cpp)
    constexpr uint32 SPELL_GROWL = 6795;

    // Storm's Bulwark grants (D5), in percent of maximum health.
    constexpr uint32 BULWARK_MAX_TARGETS = 5;
    constexpr float SHOCKWAVE_BULWARK_PCT = 20.0f;
    constexpr float ECHO_BULWARK_SHARE = 0.5f;
    constexpr float REPRISAL_PER_SUNDER = 0.2f;

    // Focused Rage capstone: 5 rage (power units are tenths), at most once per second.
    constexpr int32 FOCUSED_RAGE_CAPSTONE_RAGE = 50;
    constexpr uint32 FOCUSED_RAGE_CAPSTONE_GATE_MS = 1000;

    // The highest learned rank's amount on effIndex (ranks listed highest first); 0 when none is learned.
    int32 GetRankAmount(Unit const* unit, std::initializer_list<uint32> ranksHighFirst, SpellEffIndex effIndex)
    {
        for (uint32 rankId : ranksHighFirst)
            if (AuraEffect const* aurEff = unit->GetAuraEffect(rankId, effIndex))
                return aurEff->GetAmount();

        return 0;
    }

    // Drops chain/area targets that are not in combat with the warrior or the warrior's group (D6, D12).
    void RemoveNotEngaged(std::list<WorldObject*>& targets, Player const* warrior)
    {
        targets.remove_if([warrior](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !Engagement::IsEngagedWithOwnerOrGroup(unit, warrior);
        });
    }
}

// 6343 - Thunder Clap. Storm's Bulwark (D5): talent rank 2/4/6% + 1% per target struck (first counted, at most 5),
// the Thunder Clap part raised by Shield Discipline's 25/50% (consumed by any Thunder Clap, D23); the unamplified
// percent is recorded for the echo. Blood and Thunder (D7): each landed target bleeds for 15/30% of the final hit
// through Bloodstorm. Thunderstruck's capstone casts the echo's 3 s holder, which keeps this cast's spot.
class spell_warr_thunder_clap : public SpellScript
{
    PrepareSpellScript(spell_warr_thunder_clap);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_BLOODSTORM, WarriorData::SPELL_BLOOD_AND_THUNDER,
            WarriorData::SPELL_BLOOD_AND_THUNDER_200055, WarriorData::SPELL_STORM_S_BULWARK_200058,
            WarriorData::SPELL_STORM_S_BULWARK_200059, WarriorData::SPELL_STORM_S_BULWARK_200060,
            WarriorData::SPELL_SHIELD_DISCIPLINE, WarriorData::SPELL_SHIELD_DISCIPLINE_200063,
            WarriorData::SPELL_SHIELD_DISCIPLINE_200064, WarriorData::SPELL_THUNDERSTRUCK_200053,
            WarriorData::SPELL_THUNDERSTRUCK_200066 });
    }

    // EFFECT_0 is the damage (landed targets only); EFFECT_1 is the stock slow, untouched.
    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        if (GetHitUnit())
            ++_targetsHit;
    }

    // AfterHit sees the final damage (crit, armor, absorb applied) and runs only for a landed target.
    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!player || !target || GetHitDamage() <= 0)
            return;

        int32 const bleedPct = GetRankAmount(player, { WarriorData::SPELL_BLOOD_AND_THUNDER_200055,
            WarriorData::SPELL_BLOOD_AND_THUNDER }, EFFECT_0);
        if (bleedPct <= 0)
            return;

        uint32 const total = CalculatePct(uint32(GetHitDamage()), bleedPct);
        if (total)
            Warrior::ApplyPercentBleed(player, target, WarriorData::SPELL_BLOODSTORM, total);
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return;

        int32 const talentPct = GetRankAmount(player, { WarriorData::SPELL_STORM_S_BULWARK_200060,
            WarriorData::SPELL_STORM_S_BULWARK_200059, WarriorData::SPELL_STORM_S_BULWARK_200058 }, EFFECT_0);
        float unamplifiedPct = 0.0f;
        if (talentPct > 0)
            unamplifiedPct = float(talentPct + std::min(_targetsHit, BULWARK_MAX_TARGETS));

        // The echo always reads this cast's value (0 without the talent).
        Warrior::RecordThunderClapBulwarkPct(player, unamplifiedPct);

        float grantPct = unamplifiedPct;
        if (Aura* boost = player->GetAura(WarriorData::SPELL_SHIELD_DISCIPLINE_200064))
        {
            int32 const disciplinePct = GetRankAmount(player, { WarriorData::SPELL_SHIELD_DISCIPLINE_200063,
                WarriorData::SPELL_SHIELD_DISCIPLINE }, EFFECT_0);
            if (disciplinePct > 0)
                grantPct *= 1.0f + disciplinePct / 100.0f;
            boost->Remove();
        }

        if (grantPct > 0.0f)
            Warrior::GrantStormsBulwark(player, grantPct, Warrior::BulwarkSource::ThunderClap);

        // Thunderstruck capstone: 200066 fires the echo once, 3 s later, where this Thunder Clap was cast. A holder
        // still pending (only possible past the 6 s category cooldown) is dropped first: a refresh would keep the
        // older spot, so the newest Thunder Clap's spot gets the one echo.
        if (player->HasAura(WarriorData::SPELL_THUNDERSTRUCK_200053))
        {
            player->RemoveAurasDueToSpell(WarriorData::SPELL_THUNDERSTRUCK_200066);
            player->CastSpell(player, WarriorData::SPELL_THUNDERSTRUCK_200066, true);
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_thunder_clap::HandleDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_warr_thunder_clap::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warr_thunder_clap::HandleAfterCast);
    }

private:
    uint32 _targetsHit = 0;
};

// 200066 - Thunderstruck, the echo's 3 s holder (D6). Applied in the Thunder Clap's own AfterCast, so the warrior's
// position at apply is the Thunder Clap's spot; the one periodic tick casts the echo at that spot instead of the native
// trigger, wherever the warrior has gone since (user 2026-10-30, S1 playtest).
class spell_warr_thunderstruck_echo_holder : public AuraScript
{
    PrepareAuraScript(spell_warr_thunderstruck_echo_holder);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_THUNDER_CLAP_ECHO });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* warrior = GetTarget();
        _spot = warrior->GetPosition();
        _mapId = warrior->GetMapId();
        _instanceId = warrior->GetInstanceId();
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();

        // The spot is only meaningful on the map it was taken on.
        Unit* warrior = GetTarget();
        if (warrior->GetMapId() != _mapId || warrior->GetInstanceId() != _instanceId)
            return;

        warrior->CastSpell(_spot.GetPositionX(), _spot.GetPositionY(), _spot.GetPositionZ(),
            WarriorData::SPELL_THUNDER_CLAP_ECHO, true, nullptr, aurEff);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warr_thunderstruck_echo_holder::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_thunderstruck_echo_holder::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL);
    }

private:
    Position _spot;
    uint32 _mapId = 0;
    uint32 _instanceId = 0;
};

// 200065 - Thunder Clap Echo (D6). Cast by the warrior at the holder's stored spot (TARGET_DEST_DEST): the area, its
// line of sight and the radius mods centre there. Hits only enemies engaged with the warrior or group; once per cast
// adds 50% of the unamplified Thunder Clap shield percent and rolls Sword and Board (a triggered cast skips the
// dispatcher). No Bloodstorm, no Shield Discipline.
class spell_warr_thunder_clap_echo : public SpellScript
{
    PrepareSpellScript(spell_warr_thunder_clap_echo);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_STORM_S_BULWARK });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* player = GetCaster()->ToPlayer())
            RemoveNotEngaged(targets, player);
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return;

        float const pct = Warrior::GetRecordedThunderClapBulwarkPct(player) * ECHO_BULWARK_SHARE;
        if (pct > 0.0f)
            Warrior::GrantStormsBulwark(player, pct, Warrior::BulwarkSource::Echo);

        Warrior::RollSwordAndBoard(player, 1);
    }

    void Register() override
    {
        // EFFECT_ALL: the damage (0) and the slow (1) share their targets; one hook on both keeps them merged.
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_thunder_clap_echo::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_DEST_AREA_ENEMY);
        AfterCast += SpellCastFn(spell_warr_thunder_clap_echo::HandleAfterCast);
    }
};

// 200030 - Bloodstorm (D7, Rogue Doomblade shape). Every 3 s the holder deals this warrior's stored per-tick share
// through 204775 (no crit, no caster modifiers, ignores armor: the share already went through all of that).
class spell_warr_bloodstorm : public AuraScript
{
    PrepareAuraScript(spell_warr_bloodstorm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_BLOODSTORM, WarriorData::SPELL_BLOODSTORM_TICK });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Player* warrior = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetUnitOwner();
        if (!warrior || !target || !target->IsAlive())
            return;

        uint32 const tick = Warrior::GetPercentBleedTick(warrior, target, WarriorData::SPELL_BLOODSTORM);
        if (!tick)
            return;

        // No triggering aura, so the bleed keeps ticking if the warrior dies (Doomblade precedent).
        int32 basePoints = int32(tick);
        warrior->CastCustomSpell(target, WarriorData::SPELL_BLOODSTORM_TICK, &basePoints, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_bloodstorm::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 20243 - Devastate (D12). Extra (Improved Revenge) targets must be engaged. Once per cast, on the landed main
// target: Reprisal adds 0.5/1% x (1 + 0.2 x Sunder stacks after this hit) to Storm's Bulwark; Unrelenting grants
// Empowered Revenge. The per-Sunder flat damage stays in the SpellEffects.cpp hardcode.
class spell_warr_devastate : public SpellScript
{
    PrepareSpellScript(spell_warr_devastate);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_SUNDER_ARMOR_DEVASTATE, WarriorData::SPELL_REPRISAL,
            WarriorData::SPELL_REPRISAL_200057, WarriorData::SPELL_UNRELENTING,
            WarriorData::SPELL_EMPOWERED_REVENGE });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* player = GetCaster()->ToPlayer())
            RemoveNotEngaged(targets, player);
    }

    // AfterHit runs only for a landed target.
    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (_done || !player || !target || target != GetExplTargetUnit())
            return;

        _done = true;

        // Reprisal's carrier holds tenths of a percent (5/10).
        int32 const reprisal = GetRankAmount(player, { WarriorData::SPELL_REPRISAL_200057,
            WarriorData::SPELL_REPRISAL }, EFFECT_0);
        if (reprisal > 0)
        {
            uint32 stacks = 0;
            if (Aura const* sunder = target->GetAura(SPELL_SUNDER_ARMOR_DEVASTATE, player->GetGUID()))
                stacks = sunder->GetStackAmount();

            float const pct = reprisal / 10.0f * (1.0f + REPRISAL_PER_SUNDER * stacks);
            Warrior::GrantStormsBulwark(player, pct, Warrior::BulwarkSource::Reprisal);
        }

        if (player->HasAura(WarriorData::SPELL_UNRELENTING))
            player->CastSpell(player, WarriorData::SPELL_EMPOWERED_REVENGE, true);
    }

    void Register() override
    {
        // EFFECT_ALL: effect 0 is empty; the weapon-percent (1) and normalized (2) effects each pick chain targets.
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_devastate::FilterTargets, EFFECT_ALL,
            TARGET_UNIT_TARGET_ENEMY);
        AfterHit += SpellHitFn(spell_warr_devastate::HandleAfterHit);
    }

private:
    bool _done = false;
};

// 46968 - Shockwave (D9). Damage is the potency row's; a stun-immune target takes double, then Thunderstruck's
// +10/20/30% (its rank's effect 2 carrier) on top. Once per cast, 20% + 1% per target struck (at most 5) to Storm's
// Bulwark, no talent needed.
class spell_warr_shockwave : public SpellScript
{
    PrepareSpellScript(spell_warr_shockwave);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_THUNDERSTRUCK, WarriorData::SPELL_THUNDERSTRUCK_200052,
            WarriorData::SPELL_THUNDERSTRUCK_200053 });
    }

    // EFFECT_0 is the stun; EFFECT_1 the school damage.
    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target)
            return;

        ++_targetsHit;

        if (!target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_0))
            return;

        int32 damage = GetHitDamage() * 2;
        int32 const extraPct = GetRankAmount(caster, { WarriorData::SPELL_THUNDERSTRUCK_200053,
            WarriorData::SPELL_THUNDERSTRUCK_200052, WarriorData::SPELL_THUNDERSTRUCK }, EFFECT_2);
        if (extraPct > 0)
            AddPct(damage, extraPct);

        SetHitDamage(damage);
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || !_targetsHit)
            return;

        float const pct = SHOCKWAVE_BULWARK_PCT + float(std::min(_targetsHit, BULWARK_MAX_TARGETS));
        Warrior::GrantStormsBulwark(player, pct, Warrior::BulwarkSource::Shockwave);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_shockwave::HandleDamage, EFFECT_1, SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterCast += SpellCastFn(spell_warr_shockwave::HandleAfterCast);
    }

private:
    uint32 _targetsHit = 0;
};

// 12809 - Concussion Blow (D9; replaces stock spell_warr_concussion_blow, unbound in data). Damage is the potency
// row on effect 1; a target that cannot be stunned is Concussed instead. No bonus threat.
class spell_warr_concussion_blow_rework : public SpellScript
{
    PrepareSpellScript(spell_warr_concussion_blow_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_CONCUSSED });
    }

    // AfterHit runs only for a landed target. EFFECT_0 is the stun, which the engine skips on an immune target.
    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (target && target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_0))
            caster->CastSpell(target, WarriorData::SPELL_CONCUSSED, true);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warr_concussion_blow_rework::HandleAfterHit);
    }
};

// 2565 Shield Block, 23920 Spell Reflection - Shield Cover capstone: with rank 3 either also reduces Magic damage taken
// by 30% for 3 sec (200061).
class spell_warr_shield_cover_capstone : public SpellScript
{
    PrepareSpellScript(spell_warr_shield_cover_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_SHIELD_COVER_200061 });
    }

    void HandleCast()
    {
        Unit* caster = GetCaster();
        if (caster->HasAura(WarriorData::SPELL_SHIELD_COVER_200043))
            caster->CastSpell(caster, WarriorData::SPELL_SHIELD_COVER_200061, true);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_shield_cover_capstone::HandleCast);
    }
};

// 6572, 25288 - Revenge (D12, D15, D16). Extra (Improved Revenge) targets must be engaged. Per cast: Unrelenting
// takes 1 s off Last Stand (never below its 50% floor); Iron Temper makes the warrior Tempered with the rank's
// -3/-6% (a recast refreshes it). The Incite stamp and Empowered Revenge's shield are the dispatcher's.
class spell_warr_revenge : public SpellScript
{
    PrepareSpellScript(spell_warr_revenge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_LAST_STAND, WarriorData::SPELL_UNRELENTING,
            WarriorData::SPELL_IRON_TEMPER, WarriorData::SPELL_IRON_TEMPER_29594, WarriorData::SPELL_TEMPERED });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* player = GetCaster()->ToPlayer())
            RemoveNotEngaged(targets, player);
    }

    void HandleCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return;

        // Last Stand is off the GCD: no deferral.
        if (player->HasAura(WarriorData::SPELL_UNRELENTING))
            Warrior::ReduceCooldown(player, WarriorData::SPELL_LAST_STAND, 1s, Warrior::GetLastStandFloorEnd(player));

        int32 const reduction = GetRankAmount(player, { WarriorData::SPELL_IRON_TEMPER_29594,
            WarriorData::SPELL_IRON_TEMPER }, EFFECT_0);
        if (reduction < 0)
        {
            int32 basePoints = reduction;
            player->CastCustomSpell(player, WarriorData::SPELL_TEMPERED, &basePoints, nullptr, nullptr, true);
        }
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_revenge::FilterTargets, EFFECT_0,
            TARGET_UNIT_TARGET_ENEMY);
        OnCast += SpellCastFn(spell_warr_revenge::HandleCast);
    }
};

// 23922 - Shield Slam. Shield Discipline arms the next Thunder Clap (200064, read by spell_warr_thunder_clap). The
// Wall rank 2 (D14): a landed Shield Slam, free ones included, takes 3 s off Shield Wall (off the GCD, no deferral).
// Gag Order, Critical Block and the block-value add stay in data and core.
class spell_warr_shield_slam : public SpellScript
{
    PrepareSpellScript(spell_warr_shield_slam);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_SHIELD_DISCIPLINE, WarriorData::SPELL_SHIELD_DISCIPLINE_200063,
            WarriorData::SPELL_SHIELD_DISCIPLINE_200064, WarriorData::SPELL_THE_WALL_12803,
            WarriorData::SPELL_SHIELD_WALL });
    }

    // AfterHit runs only for a landed target (OnHit also runs for a dodged, parried, missed or immune one), so only a
    // Shield Slam that hits arms Shield Discipline.
    void HandleAfterHit()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return;

        int32 const disciplinePct = GetRankAmount(caster, { WarriorData::SPELL_SHIELD_DISCIPLINE_200063,
            WarriorData::SPELL_SHIELD_DISCIPLINE }, EFFECT_0);
        if (disciplinePct > 0)
        {
            int32 basePoints = disciplinePct;
            caster->CastCustomSpell(caster, WarriorData::SPELL_SHIELD_DISCIPLINE_200064, &basePoints, nullptr, nullptr,
                true, nullptr);
        }

        if (caster->HasAura(WarriorData::SPELL_THE_WALL_12803))
            Warrior::ReduceCooldown(caster, WarriorData::SPELL_SHIELD_WALL, 3s);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warr_shield_slam::HandleAfterHit);
    }
};

// 50720 - Vigilance, second AuraScript (D2): Focused Rage's capstone. Each Vigilance proc (the ally is hit) gives the
// warrior with Focused Rage rank 3 5 rage, at most once per second. The stock spell_warr_vigilance does the rest.
class spell_warr_vigilance_focused_rage : public AuraScript
{
    PrepareAuraScript(spell_warr_vigilance_focused_rage);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_FOCUSED_RAGE_29792 });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        Unit* caster = GetCaster();
        Player* warrior = caster ? caster->ToPlayer() : nullptr;
        if (!warrior || !warrior->HasAura(WarriorData::SPELL_FOCUSED_RAGE_29792))
            return;

        // The passive rank's own id doubles as the 1 s gate key (it is never cast).
        if (warrior->HasSpellCooldown(WarriorData::SPELL_FOCUSED_RAGE_29792))
            return;

        warrior->EnergizeBySpell(warrior, WarriorData::SPELL_FOCUSED_RAGE_29792, FOCUSED_RAGE_CAPSTONE_RAGE,
            POWER_RAGE);
        warrior->AddSpellCooldown(WarriorData::SPELL_FOCUSED_RAGE_29792, 0, FOCUSED_RAGE_CAPSTONE_GATE_MS);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_vigilance_focused_rage::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 50725 - Vigilance, second SpellScript (D24): also refreshes Growl (classless realm). Taunt stays the stock
// spell_warr_vigilance_trigger's.
class spell_warr_vigilance_trigger_growl : public SpellScript
{
    PrepareSpellScript(spell_warr_vigilance_trigger_growl);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_GROWL });
    }

    void HandleScript(SpellEffIndex /*effIndex*/)
    {
        Player* target = GetHitPlayer();
        if (target && target->HasSpell(SPELL_GROWL) && target->HasSpellCooldown(SPELL_GROWL))
            target->RemoveSpellCooldown(SPELL_GROWL, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_vigilance_trigger_growl::HandleScript, EFFECT_0,
            SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

void AddSC_warrior_protection_spell_scripts()
{
    RegisterSpellScript(spell_warr_thunder_clap);
    RegisterSpellScript(spell_warr_thunderstruck_echo_holder);
    RegisterSpellScript(spell_warr_thunder_clap_echo);
    RegisterSpellScript(spell_warr_bloodstorm);
    RegisterSpellScript(spell_warr_devastate);
    RegisterSpellScript(spell_warr_shockwave);
    RegisterSpellScript(spell_warr_concussion_blow_rework);
    RegisterSpellScript(spell_warr_shield_cover_capstone);
    RegisterSpellScript(spell_warr_revenge);
    RegisterSpellScript(spell_warr_shield_slam);
    RegisterSpellScript(spell_warr_vigilance_focused_rage);
    RegisterSpellScript(spell_warr_vigilance_trigger_growl);
}
