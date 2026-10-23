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
 * Shaman rework - totem, elemental and area spell scripts (shaman-rework SH0b; docs/reworks/shaman-shared-rework.md).
 * The elemental lockout, the Earthbind root and Healing Stream pulses, Earthen Wall, the Water Bolt heal, the
 * elemental owner-stat refresh, Earthquake and Healing Rain. Ids and tunables come from ShamanData::; the totem and
 * guardian creature AIs live in pet_shaman_rework.cpp. Every script treats a non-player or missing owner as "keep the
 * stock behaviour" (NPC shamans keep the stock spell ids). shaman-rework S1a adds the Fire Nova rework (baseline Fire
 * Elemental origin, Rising Flames) and Call of the Elements (docs/reworks/shaman-elemental-rework.md).
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DynamicObject.h"
#include "EngagementMechanics.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "HealMechanics.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ShamanMechanics.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Totem.h"
#include "TotemPackets.h"
#include "Unit.h"
#include <array>
#include <list>
#include <vector>

namespace
{
    // Stock Healing Stream heal (52042), the NPC-owner path of the 52041 pulse
    constexpr uint32 SPELL_HEALING_STREAM_HEAL_STOCK = 52042;

    // The Earthbind slow is a periodic trigger; its first tick is the placement pulse (EXTRA_INITIAL_PERIOD)
    constexpr uint32 EARTHBIND_PLACEMENT_TICK = 1;

    // Molten Fury's ramping capstone is its third rank
    constexpr uint8 MOLTEN_FURY_CAPSTONE_RANK = 3;

    // The id handed to the Earthen Wall totem AI through SetGUID (the shield target)
    constexpr int32 EARTHEN_WALL_TARGET_GUID_ID = 0;

    // A target the caster cannot see is an expected miss, not a wiring error: only the rest is logged
    void LogCastFailure(char const* script, uint32 spellId, Unit const* caster, Unit const* target,
        SpellCastResult result)
    {
        if (result == SPELL_CAST_OK || result == SPELL_FAILED_LINE_OF_SIGHT)
            return;

        LOG_ERROR("scripts.spells", "{}: cast of {} by {} at {} failed (result {})", script, spellId,
            caster ? caster->GetGUID().ToString() : "none", target ? target->GetGUID().ToString() : "none",
            uint32(result));
    }

    // Keeps only the enemies already in combat with the shaman or the shaman's group, plus the elemental's own current
    // victim (SH0b m2): the stock area abilities of the Earth and Fire Elementals must never pull an idle pack. A
    // guardian without a player owner (an NPC shaman's elemental) is left alone.
    void FilterEngagedTargets(Unit* elemental, std::list<WorldObject*>& targets)
    {
        Player const* owner = Shaman::GetOwningPlayer(elemental);
        if (!owner)
            return;

        Unit const* victim = elemental->GetVictim();
        targets.remove_if([owner, victim](WorldObject* target)
        {
            Unit* unit = target->ToUnit();
            return !unit || (unit != victim && !Engagement::IsEngagedWithOwnerOrGroup(unit, owner));
        });
    }

    // Re-runs the owner-stat refresh while the aura stays on the guardian. `aura` is only compared, never
    // dereferenced: a removed and re-added aura starts its own chain, so the old one ends here. The event lives in
    // the guardian's own m_Events, so the captured guardian pointer is valid whenever it runs.
    void ScheduleElementalStatRefresh(Unit* guardian, ObjectGuid ownerGuid, Aura const* aura)
    {
        guardian->m_Events.AddEventAtOffset([guardian, ownerGuid, aura]()
        {
            if (!guardian->IsInWorld() || !guardian->IsAlive() ||
                guardian->GetAura(ShamanData::SPELL_ELEMENTAL_OWNER_STATS) != aura)
                return;

            Player* owner = ObjectAccessor::FindPlayer(ownerGuid);
            if (!owner)
                return;

            Shaman::RefreshElementalAuras(owner, guardian);
            ScheduleElementalStatRefresh(guardian, ownerGuid, aura);
        }, Milliseconds(ShamanData::ELEMENTAL_STAT_REFRESH_MS));
    }

    // Fire Nova: the owner's Fire-slot occupant (any totem), or nullptr
    Creature* GetFireSlotTotem(Unit* caster)
    {
        ObjectGuid const guid = caster->m_SummonSlot[SUMMON_SLOT_TOTEM_FIRE];
        return guid.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*caster, guid);
    }

    // The owner's live Greater Fire Elemental guardian, or nullptr
    Creature* GetLiveFireElemental(Unit* caster)
    {
        std::list<Creature*> guardians;
        caster->GetAllMinionsByEntry(guardians, ShamanData::NPC_GREATER_FIRE_ELEMENTAL);
        for (Creature* guardian : guardians)
            if (guardian->IsInWorld() && guardian->IsAlive())
                return guardian;

        return nullptr;
    }

    // The unit Fire Nova erupts from. A player whose Fire slot holds the invisible Fire Elemental totem erupts from the
    // live Fire Elemental (no Fire totem needed, baseline for every shaman); that totem without a live guardian
    // yields nullptr, never an eruption from the invisible totem's drop point. Any other player or NPC Fire-slot
    // totem is the stock origin.
    Unit* GetFireNovaOrigin(Unit* caster)
    {
        Creature* totem = GetFireSlotTotem(caster);
        if (!totem)
            return nullptr;

        if (caster->IsPlayer() && totem->GetEntry() == ShamanData::NPC_FIRE_ELEMENTAL_TOTEM)
            return GetLiveFireElemental(caster);

        return totem->IsTotem() ? totem : nullptr;
    }

    // The four elementals' summon spell, player-side totem entry and totem slot (Call of the Elements)
    struct ElementalSummonInfo
    {
        uint32 summonSpellId;
        uint32 totemEntry;
        uint8 slot;
    };

    constexpr std::array<ElementalSummonInfo, 4> ELEMENTAL_SUMMONS =
    {{
        { ShamanData::SPELL_EARTH_ELEMENTAL_TOTEM, ShamanData::NPC_EARTH_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_EARTH },
        { ShamanData::SPELL_FIRE_ELEMENTAL_TOTEM, ShamanData::NPC_FIRE_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_FIRE },
        { ShamanData::SPELL_WATER_ELEMENTAL_TOTEM, ShamanData::NPC_WATER_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_WATER },
        { ShamanData::SPELL_STORM_ELEMENTAL_TOTEM, ShamanData::NPC_STORM_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_AIR }
    }};
}

// 2062 Earth Elemental, 2894 Fire Elemental, Water Elemental, Storm Elemental - summoning one locks the other three
// for the shared lockout (CORE-AUDIT-A A14). Triggered casts (Call of the Elements) start nothing.
class spell_sha_elemental_lockout : public SpellScript
{
    PrepareSpellScript(spell_sha_elemental_lockout);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTH_ELEMENTAL_TOTEM, ShamanData::SPELL_FIRE_ELEMENTAL_TOTEM,
            ShamanData::SPELL_WATER_ELEMENTAL_TOTEM, ShamanData::SPELL_STORM_ELEMENTAL_TOTEM });
    }

    void HandleAfterCast()
    {
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        Shaman::ApplyElementalLockout(player, GetSpellInfo()->Id);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_sha_elemental_lockout::HandleAfterCast);
    }
};

// 6474 - Earthbind Totem passive (replaces spell_sha_earthbind_totem): on the placement pulse the totem roots the
// enemies around it for 2 sec; the stock trigger keeps casting the slow. A non-player owner (NPC totems share this
// passive) gets the slow only.
class spell_sha_earthbind_pulse : public AuraScript
{
    PrepareAuraScript(spell_sha_earthbind_pulse);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTHBIND_ROOT });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        if (aurEff->GetTickNumber() != EARTHBIND_PLACEMENT_TICK)
            return;

        Unit* totem = GetCaster();
        if (!totem || !Shaman::GetOwningPlayer(totem))
            return;

        LogCastFailure("spell_sha_earthbind_pulse", ShamanData::SPELL_EARTHBIND_ROOT, totem, totem,
            totem->CastSpell(totem, ShamanData::SPELL_EARTHBIND_ROOT, true));
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_earthbind_pulse::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL);
    }
};

// 5672 - Healing Stream Totem passive (the totem's periodic aura, first tick on placement then every 2 sec). For a
// player-owned totem the pulse runs from here instead of the party-wide dummy 52041: that dummy needs a member of the
// shaman's own party within 30 yd of the totem to hit anything, which would gate the 40 yd pulse (solo, or a raid
// subgroup standing far from the totem). The 5 most injured players around the totem (never pets) get the heal, cast
// by the totem with no owner GUID (CORE-AUDIT-A A11). A non-player owner keeps the stock trigger of 52041.
// The Healing Tide Totem (Improved Healing Stream capstone, S2a) shares this passive: it heals the TIDE_TARGETS most
// injured players, and in a 5-player (non-raid) party with the 30-potency party heal instead of the normal one.
class spell_sha_healing_stream_passive : public AuraScript
{
    PrepareAuraScript(spell_sha_healing_stream_passive);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_HEALING_STREAM_HEAL, ShamanData::SPELL_HEALING_TIDE_PARTY_HEAL });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* totem = GetTarget();
        Player* owner = Shaman::GetOwningPlayer(totem);
        if (!owner)
            return;

        PreventDefaultAction();

        uint32 healId = ShamanData::SPELL_HEALING_STREAM_HEAL;
        uint8 targets = uint8(ShamanData::HEALING_STREAM_TARGETS);
        if (totem->GetEntry() == ShamanData::NPC_HEALING_TIDE_TOTEM)
        {
            targets = uint8(ShamanData::TIDE_TARGETS);

            Group const* group = owner->GetGroup();
            if (group && !group->isRaidGroup())
                healId = ShamanData::SPELL_HEALING_TIDE_PARTY_HEAL;
        }

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(owner, totem, ShamanData::HEALING_STREAM_RANGE_YD, targets, allies);
        for (Unit* ally : allies)
            LogCastFailure("spell_sha_healing_stream_passive", healId, totem, ally,
                totem->CastSpell(ally, healId, TRIGGERED_FULL_MASK));
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_healing_stream_passive::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL);
    }
};

// 52041 - Healing Stream Totem pulse (replaces spell_sha_healing_stream_totem): now the NPC-owner path only. A player
// totem's pulse is run by spell_sha_healing_stream_passive, which stops this spell from being cast at all; the early
// return is a guard so a player totem can never heal twice. The stock per-target heal keeps the player talents out.
class spell_sha_healing_stream_pulse : public SpellScript
{
    PrepareSpellScript(spell_sha_healing_stream_pulse);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_HEALING_STREAM_HEAL_STOCK });
    }

    // The stock path (spell_shaman.cpp spell_sha_healing_stream_totem) without the player talents
    void HandleDummy(SpellEffIndex effIndex)
    {
        Unit* totem = GetCaster();
        Unit* target = GetHitUnit();
        if (!totem || !target || Shaman::GetOwningPlayer(totem))
            return;

        int32 heal = GetEffectValue();
        SpellInfo const* triggeringSpell = GetTriggeringSpell();
        if (Unit* owner = totem->GetOwner())
            if (triggeringSpell)
            {
                heal = int32(owner->SpellHealingBonusDone(target, triggeringSpell, heal, HEAL, effIndex));
                heal = int32(target->SpellHealingBonusTaken(owner, triggeringSpell, heal, HEAL));
            }

        totem->CastCustomSpell(target, SPELL_HEALING_STREAM_HEAL_STOCK, &heal, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_healing_stream_pulse::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 202261 - Earthen Wall Totem: the summon (eff0) lands at the ally's feet; after the cast the ally's GUID goes to the
// totem's AI, which shields it on every pulse (CORE-AUDIT-A A32).
class spell_sha_earthen_wall : public SpellScript
{
    PrepareSpellScript(spell_sha_earthen_wall);

    void RememberTarget(SpellEffIndex /*effIndex*/)
    {
        if (Unit* target = GetHitUnit())
            _target = target->GetGUID();
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        if (_target.IsEmpty())
            if (Unit* explicitTarget = GetExplTargetUnit())
                _target = explicitTarget->GetGUID();

        // No friendly target: the cast falls back to the shaman, like every beneficial target-ally spell
        if (_target.IsEmpty())
            _target = caster->GetGUID();

        ObjectGuid const totemGuid = caster->m_SummonSlot[SUMMON_SLOT_TOTEM_EARTH];
        Creature* totem = totemGuid.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*caster, totemGuid);
        if (!totem || totem->GetEntry() != ShamanData::NPC_EARTHEN_WALL_TOTEM || !totem->AI())
        {
            LOG_ERROR("scripts.spells", "spell_sha_earthen_wall: no Earthen Wall totem AI in the earth slot of {}",
                caster->GetGUID().ToString());
            return;
        }

        totem->AI()->SetGUID(_target, EARTHEN_WALL_TARGET_GUID_ID);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_earthen_wall::RememberTarget, EFFECT_1, SPELL_EFFECT_DUMMY);
        AfterCast += SpellCastFn(spell_sha_earthen_wall::HandleAfterCast);
    }

private:
    ObjectGuid _target;
};

// 202262 - Earthen Wall shield: the absorb gets no engine spell power, so the amount comes from
// Shaman::GetEarthenWallAbsorb (base plus the owner's healing power times the generated coefficient, times Totemic
// Resonance; potency.md). The caster is the totem; the power is the owner's (S1.2). The Earthen Bulwark pulse
// (npc_sha_earthen_wall_totem) sizes its shields from the same helper. A non-player owner keeps the plain formula.
class spell_sha_earthen_wall_shield : public AuraScript
{
    PrepareAuraScript(spell_sha_earthen_wall_shield);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Unit* totem = GetCaster();
        if (!totem)
            return;

        SpellInfo const* spellInfo = GetSpellInfo();
        if (Player const* player = Shaman::GetOwningPlayer(totem))
        {
            amount = int32(Shaman::GetEarthenWallAbsorb(player, spellInfo, aurEff->GetEffIndex()));
            return;
        }

        Unit* owner = totem->GetCharmerOrOwnerOrSelf();
        float bonus = spellInfo->Effects[aurEff->GetEffIndex()].BonusMultiplier;
        bonus *= owner->SpellBaseHealingBonusDone(spellInfo->GetSchoolMask());
        bonus *= owner->CalculateLevelPenalty(spellInfo);

        amount += int32(bonus);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sha_earthen_wall_shield::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// 202276 - Water Bolt: every hit also heals the 3 most injured players around the elemental, cast by the elemental.
// No player owner, no heal.
class spell_sha_water_bolt : public SpellScript
{
    PrepareSpellScript(spell_sha_water_bolt);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_WATER_BOLT_HEAL });
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* elemental = GetCaster();
        Player* owner = Shaman::GetOwningPlayer(elemental);
        if (!elemental || !owner)
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(owner, elemental, ShamanData::WATER_BOLT_HEAL_RANGE_YD,
            uint8(ShamanData::WATER_BOLT_HEAL_TARGETS), allies);
        for (Unit* ally : allies)
            LogCastFailure("spell_sha_water_bolt", ShamanData::SPELL_WATER_BOLT_HEAL, elemental, ally,
                elemental->CastSpell(ally, ShamanData::SPELL_WATER_BOLT_HEAL, TRIGGERED_FULL_MASK));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_water_bolt::HandleHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 202279 - elemental owner-stat aura (H1): damage and healing done from the owner's spell power. The amounts are set by
// Shaman::RefreshElementalAuras (never from here); this script is the periodic refresh, so the amounts follow the
// owner's live spell power for as long as the aura stays on the guardian.
class spell_sha_elemental_owner_stats : public AuraScript
{
    PrepareAuraScript(spell_sha_elemental_owner_stats);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* guardian = GetTarget();
        Player* owner = Shaman::GetOwningPlayer(guardian);
        if (!owner)
            return;

        ScheduleElementalStatRefresh(guardian, owner->GetGUID(), GetAura());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_elemental_owner_stats::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 202280 - Earthquake: eff0 is the ground zone (its dynamic object), eff1 a 1 s periodic dummy on the shaman. Each tick
// casts the single-target tick, as the shaman, at every valid attackable enemy inside the zone with line of sight
// (H7, no target cap; T0b section 4 and 8). The zone is unhasted: PERIODIC_DUMMY gets no haste.
class spell_sha_earthquake : public AuraScript
{
    PrepareAuraScript(spell_sha_earthquake);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTHQUAKE_TICK });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsAlive())
            return;

        DynamicObject* zone = caster->GetDynObject(GetId());
        SpellInfo const* tickInfo = sSpellMgr->GetSpellInfo(ShamanData::SPELL_EARTHQUAKE_TICK);
        if (!zone || !tickInfo)
            return;

        float const radius = zone->GetRadius();
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(zone, caster, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(zone, nearby, check);
        Cell::VisitObjects(zone, searcher, radius);

        for (Unit* enemy : nearby)
        {
            if (!caster->IsValidAttackTarget(enemy, tickInfo) || !zone->IsWithinLOSInMap(enemy))
                continue;

            LogCastFailure("spell_sha_earthquake", ShamanData::SPELL_EARTHQUAKE_TICK, caster, enemy,
                caster->CastSpell(enemy, tickInfo, TRIGGERED_FULL_MASK, nullptr, aurEff));
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(GetId());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_earthquake::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_earthquake::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 202283 - Healing Rain: one rain per shaman. A new cast tears the old zone and aura down first (BeforeCast, the Rain
// of Fire shape).
class spell_sha_healing_rain : public SpellScript
{
    PrepareSpellScript(spell_sha_healing_rain);

    void RemoveExisting()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->RemoveDynObject(GetSpellInfo()->Id);
        caster->RemoveAurasDueToSpell(GetSpellInfo()->Id, caster->GetGUID());
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_sha_healing_rain::RemoveExisting);
    }
};

// 202283 - Healing Rain periodic (eff1, 2 s, unhasted): the 5 most injured players inside the zone each get one
// single-target heal from the shaman, read live (P0 spike 6, T0b section 4).
class spell_sha_healing_rain_aura : public AuraScript
{
    PrepareAuraScript(spell_sha_healing_rain_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_HEALING_RAIN_HEAL });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsAlive())
            return;

        DynamicObject* zone = caster->GetDynObject(GetId());
        if (!zone)
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(caster, zone, zone->GetRadius(), uint8(ShamanData::HEALING_RAIN_TARGETS), allies);
        for (Unit* ally : allies)
            LogCastFailure("spell_sha_healing_rain_aura", ShamanData::SPELL_HEALING_RAIN_HEAL, caster, ally,
                caster->CastSpell(ally, ShamanData::SPELL_HEALING_RAIN_HEAL, TRIGGERED_FULL_MASK, nullptr, aurEff));
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(GetId());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_healing_rain_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_healing_rain_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 12470 Fire Nova (Fire Elemental, 10 yd) and 13376 Fire Shield pulse (Fire Elemental, 5 yd): effect 0 is school
// damage at target A 22 (TARGET_SRC_CASTER) / B 15 (TARGET_UNIT_SRC_AREA_ENEMY). Only enemies already engaged with the
// owner or the group take the hit, so neither pulls an idle mob (SH0b m2; a player-owned elemental only).
class spell_sha_elemental_engaged_aoe : public SpellScript
{
    PrepareSpellScript(spell_sha_elemental_engaged_aoe);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_NOVA,
            ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_SHIELD_PULSE });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Unit* elemental = GetCaster())
            FilterEngagedTargets(elemental, targets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_elemental_engaged_aoe::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// 36213 Angered Earth (Earth Elemental, 15 yd): effect 0 is ATTACK_ME and effect 1 the bonus threat, both at target
// A 22 / B 15. Both effects get the same filter, so an idle mob is neither taunted nor given threat (SH0b m2).
class spell_sha_angered_earth_engaged : public SpellScript
{
    PrepareSpellScript(spell_sha_angered_earth_engaged);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_ANGERED_EARTH });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Unit* elemental = GetCaster())
            FilterEngagedTargets(elemental, targets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_angered_earth_engaged::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_angered_earth_engaged::FilterTargets,
            EFFECT_1, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// -1535 Fire Nova (replaces spell_sha_fire_nova): baseline Fire Elemental origin and Rising Flames (docs/reworks/
// shaman-shared-rework.md Fire Elemental, shaman-elemental-rework.md Rising Flames).
//  - A player whose Fire slot holds the Fire Elemental totem (300271) needs no Fire totem: the nova is cast at the live
//    Fire Elemental, which sets the eruption point (8349 erupts at its explicit target's position) and the range
//    check. Any other Fire-slot totem, and every NPC caster, keeps the stock behaviour, error message included.
//  - Rising Flames: the stack count of the player's buff is passed to the nova as MISCVALUE0 (read by
//    spell_sha_fire_nova_rework_damage on 8349), then all stacks are consumed.
class spell_sha_fire_nova_rework : public SpellScript
{
    PrepareSpellScript(spell_sha_fire_nova_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FIRE_NOVA_8349, ShamanData::SPELL_RISING_FLAMES_BUFF });
    }

    SpellCastResult CheckFireTotem()
    {
        Unit* caster = GetCaster();
        Unit* origin = GetFireNovaOrigin(caster);
        if (!origin)
        {
            SetCustomCastResultMessage(SPELL_CUSTOM_ERROR_MUST_HAVE_FIRE_TOTEM);
            return SPELL_FAILED_CUSTOM_ERROR;
        }

        if (!caster->IsWithinDistInMap(origin, caster->GetSpellMaxRangeForTarget(origin, GetSpellInfo())))
            return SPELL_FAILED_OUT_OF_RANGE;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* origin = GetFireNovaOrigin(caster);
        if (!origin)
            return;

        int32 stacks = 0;
        if (caster->IsPlayer())
            if (Aura const* risingFlames = caster->GetAura(ShamanData::SPELL_RISING_FLAMES_BUFF))
                stacks = int32(risingFlames->GetStackAmount());

        LogCastFailure("spell_sha_fire_nova_rework", ShamanData::SPELL_FIRE_NOVA_8349, caster, origin,
            caster->CastCustomSpell(ShamanData::SPELL_FIRE_NOVA_8349, SPELLVALUE_MISCVALUE0, stacks, origin, true));

        if (stacks)
            caster->RemoveAurasDueToSpell(ShamanData::SPELL_RISING_FLAMES_BUFF);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_sha_fire_nova_rework::CheckFireTotem);
        OnEffectHitTarget += SpellEffectFn(spell_sha_fire_nova_rework::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 8349 Fire Nova (the eruption): +RISING_FLAMES_PCT_PER_STACK% damage per Rising Flames stack the player's Fire Nova
// (spell_sha_fire_nova_rework) passed in MISCVALUE0. Any other cast of 8349 carries 0 and is untouched.
class spell_sha_fire_nova_rework_damage : public SpellScript
{
    PrepareSpellScript(spell_sha_fire_nova_rework_damage);

    void HandleHit()
    {
        uint32 const stacks = GetSpell()->GetSpellValue()->MiscVal[0];
        if (!stacks)
            return;

        float const factor = 1.0f + float(stacks * uint32(ShamanData::RISING_FLAMES_PCT_PER_STACK)) / 100.0f;
        SetHitDamage(int32(float(GetHitDamage()) * factor));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_sha_fire_nova_rework_damage::HandleHit);
    }
};

// 8187 Magma Totem pulse - Molten Fury's capstone (rank 3): the pulse deals MOLTEN_FURY_RAMP_PCT% more for each pulse
// this totem already fired. The caster is the totem; its 202269 passive ticks once per pulse (the placement pulse is
// tick 1, so the pulses already fired are tick - 1) and a new totem is a new aura, so the ramp restarts for free.
// The stock Magma Totem (an NPC's 8188) shares 8187: only the player-side totem entry with a player owner ramps. The
// flat 10/20/30% of the talent is data (a spell modifier on the pulse's own bit) and is not touched here.
class spell_sha_enh_molten_fury : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_molten_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_MAGMA_TOTEM_PASSIVE });
    }

    void HandleHit()
    {
        Unit* totem = GetCaster();
        if (!totem || totem->GetEntry() != ShamanData::NPC_MAGMA_TOTEM)
            return;

        Player const* owner = Shaman::GetOwningPlayer(totem);
        if (!owner || Shaman::GetTalentRank(owner, { ShamanData::SPELL_MOLTEN_FURY_RANK1,
            ShamanData::SPELL_MOLTEN_FURY_RANK2, ShamanData::SPELL_MOLTEN_FURY_RANK3 }) < MOLTEN_FURY_CAPSTONE_RANK)
            return;

        AuraEffect const* pulse = totem->GetAuraEffect(ShamanData::SPELL_MAGMA_TOTEM_PASSIVE, EFFECT_0);
        if (!pulse || pulse->GetTickNumber() <= 1)
            return;

        uint32 const fired = pulse->GetTickNumber() - 1;
        float const factor = 1.0f + float(fired * uint32(ShamanData::MOLTEN_FURY_RAMP_PCT)) / 100.0f;
        SetHitDamage(int32(float(GetHitDamage()) * factor));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_sha_enh_molten_fury::HandleHit);
    }
};

// 202531 Call of the Elements: summons every known elemental that is not already out for COTE_SUMMON_MS and extends
// the active ones by COTE_EXTEND_MS. The summons are triggered full-mask casts, so they start neither their own 2 min
// cooldown nor the shared lockout (Spell::SendSpellCooldown returns on TRIGGERED_IGNORE_SPELL_AND_CATEGORY_CD, and
// spell_sha_elemental_lockout skips triggered casts). A totem in a slot being taken is dismissed first. The summon
// spells' own duration is 30 s, so each new totem is cut to COTE_SUMMON_MS after it appears (its guardian leaves
// with it) and its totem bar entry is re-sent with the new time.
// The client starts its own cooldown swipe for any spell of its own the moment it receives that spell's SMSG_SPELL_GO
// (Player::AddSpellAndCategoryCooldowns, CDH comment), triggered or not, so each summon cast here greys its button for
// the spell's full 2 min although the server stored nothing. One tick later (after the SMSG_SPELL_GO packets) the
// client is told the truth: a real cooldown the elemental already had is re-announced with its remaining time, no
// cooldown at all is cleared.
class spell_sha_ele_call_of_the_elements : public SpellScript
{
    PrepareSpellScript(spell_sha_ele_call_of_the_elements);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTH_ELEMENTAL_TOTEM, ShamanData::SPELL_FIRE_ELEMENTAL_TOTEM,
            ShamanData::SPELL_WATER_ELEMENTAL_TOTEM, ShamanData::SPELL_STORM_ELEMENTAL_TOTEM });
    }

    static Creature* GetSlotTotem(Player* player, uint8 slot)
    {
        ObjectGuid const guid = player->m_SummonSlot[slot];
        return guid.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*player, guid);
    }

    static void CutSummonDuration(Player* player, ElementalSummonInfo const& info)
    {
        Creature* creature = GetSlotTotem(player, info.slot);
        if (!creature || creature->GetEntry() != info.totemEntry)
            return;

        Totem* totem = creature->ToTotem();
        if (!totem)
            return;

        uint32 const duration = uint32(ShamanData::COTE_SUMMON_MS);
        if (totem->GetTotemDuration() <= duration)
            return;

        totem->SetTotemDuration(duration);

        // The first packet carried the summon spell's own duration. P0 2d: a plain re-send retimes the bar text but not
        // the swipe, so the slot is cleared first (empty GUID, 0 duration), exactly as Shaman::SendTotemTimer does.
        uint8 const barSlot = uint8(info.slot - SUMMON_SLOT_TOTEM_FIRE);

        WorldPackets::Totem::TotemCreated clear;
        clear.Slot = barSlot;
        player->SendDirectMessage(clear.Write());

        // Same fields as Totem::InitStats
        WorldPackets::Totem::TotemCreated data;
        data.Totem = totem->GetGUID();
        data.Slot = barSlot;
        data.Duration = duration;
        data.SpellID = totem->GetUInt32Value(UNIT_CREATED_BY_SPELL);
        player->SendDirectMessage(data.Write());
    }

    static void RestoreSummonCooldownDisplay(Player* player, std::vector<uint32> spellIds)
    {
        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid, spellIds]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self)
                return;

            for (uint32 const spellId : spellIds)
            {
                if (self->HasSpellCooldown(spellId))
                    self->ResendSpellCooldown(spellId);         // clear-then-set with the real remaining time
                else
                    self->RemoveSpellCooldown(spellId, true);   // nothing stored: SMSG_CLEAR_COOLDOWN only
            }
        }, 1ms);
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        // Extend first, so an elemental summoned below is not extended again
        Shaman::ExtendElementals(player, uint32(ShamanData::COTE_EXTEND_MS));

        std::vector<uint32> summoned;

        for (ElementalSummonInfo const& info : ELEMENTAL_SUMMONS)
        {
            // Below the level of a summon the shaman simply does not know it
            if (!player->HasSpell(info.summonSpellId))
                continue;

            Creature* occupant = GetSlotTotem(player, info.slot);
            if (occupant)
            {
                if (occupant->GetEntry() == info.totemEntry && occupant->IsAlive())
                    continue;

                // Another totem holds the slot: dismiss it
                if (Totem* totem = occupant->ToTotem())
                    totem->UnSummon();
            }

            LogCastFailure("spell_sha_ele_call_of_the_elements", info.summonSpellId, player, player,
                player->CastSpell(player, info.summonSpellId, TRIGGERED_FULL_MASK));
            CutSummonDuration(player, info);
            summoned.push_back(info.summonSpellId);
        }

        if (!summoned.empty())
            RestoreSummonCooldownDisplay(player, std::move(summoned));
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_sha_ele_call_of_the_elements::HandleAfterCast);
    }
};

void AddSC_shaman_totem_spell_scripts()
{
    RegisterSpellScript(spell_sha_elemental_lockout);
    RegisterSpellScript(spell_sha_earthbind_pulse);
    RegisterSpellScript(spell_sha_healing_stream_passive);
    RegisterSpellScript(spell_sha_healing_stream_pulse);
    RegisterSpellScript(spell_sha_earthen_wall);
    RegisterSpellScript(spell_sha_earthen_wall_shield);
    RegisterSpellScript(spell_sha_water_bolt);
    RegisterSpellScript(spell_sha_elemental_owner_stats);
    RegisterSpellScript(spell_sha_earthquake);
    RegisterSpellAndAuraScriptPair(spell_sha_healing_rain, spell_sha_healing_rain_aura);
    RegisterSpellScript(spell_sha_elemental_engaged_aoe);
    RegisterSpellScript(spell_sha_angered_earth_engaged);
    RegisterSpellScript(spell_sha_fire_nova_rework);
    RegisterSpellScript(spell_sha_fire_nova_rework_damage);
    RegisterSpellScript(spell_sha_ele_call_of_the_elements);
    RegisterSpellScript(spell_sha_enh_molten_fury);
}
