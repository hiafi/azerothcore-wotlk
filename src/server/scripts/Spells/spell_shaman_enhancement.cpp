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
 * Shaman rework - Enhancement spec scripts (shaman-rework S3a; docs/reworks/shaman-enhancement-rework.md). Ids and
 * tunables come from ShamanData::; shared state (charges, Ascendances, Stoneskin scaling) lives in ShamanMechanics'
 * S3 block.
 *
 * Rules every script here follows (S3-NOTES section 4, S3a-WP-BRIEF):
 *  - Only a player does anything, and owner-side procs only for the shaman's own actions (Shaman::IsOwnAction):
 *    totems, wolves and other guardians never roll the shaman's procs.
 *  - Triggered hits roll nothing (Windfury/Flametongue/Frostbrand Attacks, Gusts, Bursts, Stormstrike strikes and
 *    cleaves, Blizzard ticks, Flame Shock spreads). Named exceptions: Windfury Attacks and the shaman's own Gusts roll
 *    Maelstrom Weapon; Fire Nova's eruption (cast triggered by Fire Nova) grants Elemental Charge once.
 *  - Once per cast: Elemental Charge, Maelstrom Weapon and Mental Quickness from an ability count one event per Spell
 *    (CastGuard); Stormstrike's own effects run once on its primary target.
 *  - Scripted rolls use Shaman::RollProcChance (Proc Chance applies); their spell_proc rows must proc at 100%.
 *  - Per-rank percentages come from the rank's DUMMY effect or the generated consts (L-8).
 */

#include "CellImpl.h"
#include "DataMap.h"
#include "DynamicObject.h"
#include "EngagementMechanics.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
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
#include "UnitScript.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <initializer_list>
#include <list>
#include <span>
#include <vector>

namespace
{
    // Stock ids with no stable DSL header name (npc.csv pulls): the Stormstrike strikes (17364 E2/E3 TRIGGER_SPELL)
    // and Frozen Power's root.
    constexpr uint32 SPELL_STORMSTRIKE_MAIN_HAND = 32175;
    constexpr uint32 SPELL_STORMSTRIKE_OFF_HAND = 32176;
    constexpr uint32 SPELL_FROZEN_POWER_ROOT = 63685;

    // Talent rank chains (rank order).
    constexpr std::array<uint32, 2> IMPROVED_STORMSTRIKE_RANKS = { ShamanData::SPELL_IMPROVED_STORMSTRIKE,
        ShamanData::SPELL_IMPROVED_STORMSTRIKE_51522 };
    constexpr std::array<uint32, 3> STATIC_SHOCK_RANKS = { ShamanData::SPELL_STATIC_SHOCK,
        ShamanData::SPELL_STATIC_SHOCK_51526, ShamanData::SPELL_STATIC_SHOCK_51527 };
    constexpr std::array<uint32, 3> IMPROVED_LIGHTNING_SHIELD_RANKS = { ShamanData::SPELL_IMPROVED_SHIELDS,
        ShamanData::SPELL_IMPROVED_SHIELDS_16290, ShamanData::SPELL_IMPROVED_SHIELDS_51881 };
    constexpr std::array<uint32, 3> FROZEN_POWER_RANKS = { ShamanData::SPELL_FROZEN_POWER,
        ShamanData::SPELL_FROZEN_POWER_63374, ShamanData::SPELL_FROZEN_POWER_RANK3 };
    constexpr std::array<uint32, 3> SPIRIT_GUARD_RANKS = { ShamanData::SPELL_SPIRIT_GUARD_RANK1,
        ShamanData::SPELL_SPIRIT_GUARD_RANK2, ShamanData::SPELL_SPIRIT_GUARD_RANK3 };
    constexpr std::array<uint32, 1> ASCENDANCE_RANKS = { ShamanData::SPELL_ASCENDANCE };
    constexpr std::array<uint32, 2> GUARDIAN_TOTEMS_RANKS = { ShamanData::SPELL_GUARDIAN_TOTEMS,
        ShamanData::SPELL_GUARDIAN_TOTEMS_16293 };

    constexpr std::array<int32, 3> SPIRIT_GUARD_STONESKIN = { ShamanData::SPIRIT_GUARD_STONESKIN_R1,
        ShamanData::SPIRIT_GUARD_STONESKIN_R2, ShamanData::SPIRIT_GUARD_STONESKIN_R3 };

    // Stormstrike's cleave hits: Frost Ascendance 1, Elemental Ascendance 2 (doc Ascendance values, [fixed])
    constexpr uint32 SS_CLEAVE_FROST = 1;
    constexpr uint32 SS_CLEAVE_ELEMENTAL = 2;

    constexpr char const* ENHANCEMENT_STATE_KEY = "shaman_enhancement_script_state";

    // Per-player state the Enhancement scripts share (lives as long as the player object)
    struct EnhancementScriptState : DataMap::Base
    {
        // Stormstrike landed-damage window (Frost Spirit copy): open from the primary cast's OnCast to its AfterHit
        Spell const* stormstrike = nullptr;
        ObjectGuid stormstrikeTarget;
        uint32 stormstrikeDamage = 0;
    };

    EnhancementScriptState* GetState(Player* player)
    {
        return player->CustomData.GetDefault<EnhancementScriptState>(ENHANCEMENT_STATE_KEY);
    }

    uint32 NowMs()
    {
        return uint32(GameTime::GetGameTimeMS().count());
    }

    // Once-per-cast guard: one claim per Spell object per world tick (elemental CastGuard shape). Every target of a
    // multi-target spell is hit in the same tick; the ms check keeps a reused Spell address from matching.
    struct CastGuard
    {
        Spell const* spell = nullptr;
        uint32 ms = 0;

        bool Claim(Spell const* procSpell)
        {
            uint32 const now = NowMs();
            if (procSpell == spell && now == ms)
                return false;

            spell = procSpell;
            ms = now;
            return true;
        }
    };

    // 1-based position of `spellId` in `ranks`, 0 if absent
    uint8 RankOf(uint32 spellId, std::span<uint32 const> ranks)
    {
        for (std::size_t i = 0; i < ranks.size(); ++i)
            if (ranks[i] == spellId)
                return uint8(i + 1);

        return 0;
    }

    // The player behind a proc on a talent aura: the aura's owner, and only for its own action (never a totem's,
    // wolf's or other guardian's)
    Player* GetProcPlayer(Unit* auraOwner, ProcEventInfo& eventInfo)
    {
        Player* player = auraOwner ? auraOwner->ToPlayer() : nullptr;
        if (!player || !Shaman::IsOwnAction(player, eventInfo.GetActor()))
            return nullptr;

        return player;
    }

    bool IsTriggeredEvent(ProcEventInfo const& eventInfo)
    {
        Spell const* procSpell = eventInfo.GetProcSpell();
        return procSpell && procSpell->IsTriggered();
    }

    // A landed (or absorbed) direct hit: damage on a non-periodic event
    bool IsDirectDamageHit(ProcEventInfo& eventInfo)
    {
        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC)
            return false;

        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        return damageInfo && (damageInfo->GetDamage() || damageInfo->GetAbsorb());
    }

    // Stormstrike's own hit carries no damage (its strikes are triggered); it counts as one landed melee ability
    bool IsStormstrikeHit(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && spellInfo->Id == ShamanData::SPELL_STORMSTRIKE && !IsTriggeredEvent(eventInfo) &&
            (eventInfo.GetHitMask() & (PROC_HIT_NORMAL | PROC_HIT_CRITICAL));
    }

    // Amounts of the APPLY_AURA DUMMY effects of a rank spell, in effect order (rank data, L-8)
    std::vector<int32> GetRankDummyAmounts(uint32 rankSpellId)
    {
        std::vector<int32> amounts;
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(rankSpellId);
        if (!spellInfo)
            return amounts;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (spellInfo->Effects[i].Effect == SPELL_EFFECT_APPLY_AURA &&
                spellInfo->Effects[i].ApplyAuraName == SPELL_AURA_DUMMY)
                amounts.push_back(spellInfo->Effects[i].CalcValue());

        return amounts;
    }

    // The first DUMMY aura effect amount of a live aura (the proccing rank's own value)
    int32 GetAuraDummyAmount(Aura const* aura)
    {
        if (!aura)
            return 0;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i))
                if (effect->GetAuraType() == SPELL_AURA_DUMMY)
                    return effect->GetAmount();

        return 0;
    }

    // Any effect of `aura`, for the triggeredByAura argument of a cast made from an aura-level proc handler
    AuraEffect const* GetAnyEffect(Aura const* aura)
    {
        if (!aura)
            return nullptr;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i))
                return effect;

        return nullptr;
    }

    // Hostile units around `center` within `range` that `player` may attack, alive, in line of sight of `center`;
    // `exclude` is left out. Unsorted.
    std::list<Unit*> FindEnemiesAround(Player* player, WorldObject* center, float range, Unit const* exclude)
    {
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, player, range);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, nearby, check);
        Cell::VisitObjects(center, searcher, range);

        nearby.remove_if([player, center, exclude](Unit* unit)
        {
            return unit == exclude || !unit->IsAlive() || !player->IsValidAttackTarget(unit) ||
                !center->IsWithinLOSInMap(unit);
        });

        return nearby;
    }

    // The SPELLMOD_DOT percent of the shaman's Fire or Elemental Ascendance (live: RefreshAscendance keeps the
    // Mastery part current); 0 when neither is up
    int32 GetFlameShockAscendancePct(Player const* player)
    {
        for (uint32 spellId : { ShamanData::SPELL_ELEMENTAL_ASCENDANCE, ShamanData::SPELL_FIRE_ASCENDANCE })
        {
            Aura const* aura = player->GetAura(spellId, player->GetGUID());
            if (!aura)
                continue;

            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect const* effect = aura->GetEffect(i))
                    if (effect->GetAuraType() == SPELL_AURA_ADD_PCT_MODIFIER && effect->GetMiscValue() == SPELLMOD_DOT)
                        return effect->GetAmount();
        }

        return 0;
    }
}

// 202360 Elemental Charge (passive proc carrier). While Flametongue, Frostbrand or Windfury is active (Earth Charge
// under Rockbiter), the shaman's own direct damaging abilities grant charges once per cast: Stormstrike, Lava Lash and
// the shock matching the imbue 2 (Flame/Flametongue, Frost/Frostbrand, Earth/Windfury), every other one 1 (Earth Shock
// under Rockbiter 1). Melee auto attacks of either hand roll EC_AUTO_CHANCE x Proc Chance per hit for 1. Periodic
// damage and triggered hits grant nothing; Fire Nova's eruption (8349, cast triggered by Fire Nova) is the one
// triggered cast that counts, once. Caps, the Elemental/Earthen Ascendance block and the talent check are AddCharge's.
// spell_proc: autos + melee + magic-negative spells, HIT phase, SpellTypeMask 0 (Stormstrike's own hit has no damage),
// Chance 100; TRIGGERED_CAN_PROC only so Fire Nova's eruption reaches the script.
class spell_sha_enh_elemental_charge : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_elemental_charge);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || Shaman::GetImbueElement(Shaman::GetActiveImbue(player)) == Shaman::EnhElement::None)
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
        {
            // Melee auto attack, either hand
            if (!(eventInfo.GetTypeMask() & PROC_FLAG_DONE_MELEE_AUTO_ATTACK))
                return false;

            if (!(eventInfo.GetHitMask() & (PROC_HIT_NORMAL | PROC_HIT_CRITICAL | PROC_HIT_ABSORB)))
                return false;

            _amount = 1;
            return Shaman::RollProcChance(player, float(ShamanData::EC_AUTO_CHANCE));
        }

        if (IsTriggeredEvent(eventInfo) && spellInfo->Id != ShamanData::SPELL_FIRE_NOVA_8349)
            return false;

        if (!IsDirectDamageHit(eventInfo) && !IsStormstrikeHit(eventInfo))
            return false;

        if (!_guard.Claim(eventInfo.GetProcSpell()))
            return false;

        _amount = GetAbilityAmount(player, spellInfo->Id);
        return true;
    }

    static uint8 GetAbilityAmount(Player const* player, uint32 spellId)
    {
        switch (spellId)
        {
            case ShamanData::SPELL_STORMSTRIKE:
            case ShamanData::SPELL_LAVA_LASH:
                return 2;
            default:
                break;
        }

        switch (Shaman::GetImbueElement(Shaman::GetActiveImbue(player)))
        {
            case Shaman::EnhElement::Fire:
                return spellId == ShamanData::SPELL_FLAME_SHOCK ? 2 : 1;
            case Shaman::EnhElement::Frost:
                return spellId == ShamanData::SPELL_FROST_SHOCK ? 2 : 1;
            case Shaman::EnhElement::Wind:
                return spellId == ShamanData::SPELL_EARTH_SHOCK ? 2 : 1;
            default:
                return 1;   // Rockbiter: no shock matches
        }
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        if (Player* player = GetUnitOwner()->ToPlayer())
            Shaman::AddCharge(player, _amount, false);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_elemental_charge::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_elemental_charge::HandleProc);
    }

    CastGuard _guard;
    uint8 _amount = 1;
};

// -51528 Maelstrom Weapon (51528-51530). The chance is data (rank ProcChance 7/14/21, native Proc Chance); the
// script filters: the shaman's own melee auto attacks per hit, its non-triggered melee abilities once per cast
// (Stormstrike's own hit, so it rolls once and never per weapon), and of the triggered hits only Windfury Attacks and
// the shaman's own Gusts (cast from its Wind/Elemental Ascendance; a Wind Spirit's Gust carries no such aura). The
// default PROC_TRIGGER_SPELL then grants the buff. spell_proc: autos + melee spells, HIT, TRIGGERED_CAN_PROC.
class spell_sha_enh_maelstrom_weapon : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_maelstrom_weapon);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcPlayer(GetUnitOwner(), eventInfo))
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_MELEE_AUTO_ATTACK) != 0;

        if (IsTriggeredEvent(eventInfo))
        {
            if (!IsDirectDamageHit(eventInfo))
                return false;

            switch (spellInfo->Id)
            {
                case ShamanData::SPELL_WINDFURY_ATTACK_MH:
                case ShamanData::SPELL_WINDFURY_ATTACK_OH:
                    return true;
                case ShamanData::SPELL_GUST:
                {
                    // ProcEventInfo::GetTriggerAuraSpell is never filled by the proc pipeline; the Spell carries it
                    Spell const* procSpell = eventInfo.GetProcSpell();
                    SpellInfo const* trigger = procSpell ? procSpell->GetTriggeredByAuraSpellInfo() : nullptr;
                    return trigger && (trigger->Id == ShamanData::SPELL_WIND_ASCENDANCE ||
                        trigger->Id == ShamanData::SPELL_ELEMENTAL_ASCENDANCE);
                }
                default:
                    return false;
            }
        }

        if (spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE)
            return false;

        if (!IsDirectDamageHit(eventInfo) && !IsStormstrikeHit(eventInfo))
            return false;

        return _guard.Claim(eventInfo.GetProcSpell());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_maelstrom_weapon::CheckProc);
    }

    CastGuard _guard;
};

// -51525 Static Shock (replaces spell_sha_static_shock). Chance 5/10/15% and the 1.5 s cooldown are data (native
// Proc Chance). The shaman's own Lightning Shield fires an orb at the target and spends a charge; with Improved
// Lightning Shield rank 3 the charge is kept ILS_NO_EXPEND_CHANCE x Proc Chance of the time; under Rockbiter with
// Improved Lightning Shield the orb grants ILS_ORB_STONESKIN (its double threat is the Rockbiter child's SpellMod).
class spell_sha_enh_static_shock : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_static_shock);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_LIGHTNING_SHIELD, ShamanData::SPELL_LIGHTNING_SHIELD_26364 });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || !player->HasAura(ShamanData::SPELL_LIGHTNING_SHIELD, player->GetGUID()))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && target != player && target->IsAlive() && player->IsValidAttackTarget(target);
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        Unit* target = eventInfo.GetActionTarget();
        Aura* shield = player ? player->GetAura(ShamanData::SPELL_LIGHTNING_SHIELD, player->GetGUID()) : nullptr;
        if (!shield || !target)
            return;

        if (player->CastSpell(target, ShamanData::SPELL_LIGHTNING_SHIELD_26364, true) != SPELL_CAST_OK)
            return;

        uint8 const ilsRank = Shaman::GetTalentRank(player, IMPROVED_LIGHTNING_SHIELD_RANKS);
        if (ilsRank && Shaman::GetActiveImbue(player) == ShamanData::SPELL_ROCKBITER_WEAPON)
            Shaman::AddStoneskin(player, uint32(ShamanData::ILS_ORB_STONESKIN));

        if (ilsRank >= IMPROVED_LIGHTNING_SHIELD_RANKS.size() &&
            Shaman::RollProcChance(player, float(ShamanData::ILS_NO_EXPEND_CHANCE)))
            return;

        shield->DropCharge();
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_static_shock::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_static_shock::HandleProc);
    }
};

// -63373 Frozen Power (63373, 63374, 202375; replaces spell_sha_frozen_power, which refused targets within 15 yd).
// A Frost Shock hit rolls the rank's DUMMY chance (33/66/100%) x Proc Chance to root the target (63685). Rank 3: an
// Elemental Blast hit while Frostbrand is active creates the Blizzard (202404) at the target. spell_proc: Frost Shock
// d0 b31 and Elemental Blast d2 b20, magic negative, HIT, Chance 100 (the script rolls).
class spell_sha_enh_frozen_power : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_frozen_power);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_FROZEN_POWER_ROOT, ShamanData::SPELL_FROZEN_BLIZZARD });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !spellInfo || IsTriggeredEvent(eventInfo) || !IsDirectDamageHit(eventInfo))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsAlive())
            return false;

        switch (spellInfo->Id)
        {
            case ShamanData::SPELL_FROST_SHOCK:
                return Shaman::RollProcChance(player, float(GetAuraDummyAmount(GetAura())));
            case ShamanData::SPELL_ELEMENTAL_BLAST:
                return RankOf(GetId(), FROZEN_POWER_RANKS) >= FROZEN_POWER_RANKS.size() &&
                    Shaman::GetActiveImbue(player) == ShamanData::SPELL_FROSTBRAND_WEAPON &&
                    _guard.Claim(eventInfo.GetProcSpell());
            default:
                return false;
        }
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        Unit* target = eventInfo.GetActionTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !target || !spellInfo)
            return;

        if (spellInfo->Id == ShamanData::SPELL_FROST_SHOCK)
        {
            player->CastSpell(target, SPELL_FROZEN_POWER_ROOT, true);
            return;
        }

        // The Blizzard sits at the target's position (unit + destination set, whichever the row's targets read)
        SpellInfo const* blizzard = sSpellMgr->GetSpellInfo(ShamanData::SPELL_FROZEN_BLIZZARD);
        if (!blizzard)
            return;

        SpellCastTargets targets;
        targets.SetUnitTarget(target);
        targets.SetDst(*target);
        player->CastSpell(targets, blizzard, nullptr, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_frozen_power::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_frozen_power::HandleProc);
    }

    CastGuard _guard;
};

// 202404 Frozen Power's Blizzard (spell_sha_earthquake shape): eff0 is the ground zone (its dynamic object), eff1 a
// 1 s periodic dummy on the shaman. Each tick the shaman casts one Blizzard tick (202405) at every valid attackable
// enemy inside the zone with line of sight: per target, no cap, no split; the tick is triggered and rolls nothing.
// Unhasted (PERIODIC_DUMMY gets no haste).
class spell_sha_enh_frozen_blizzard : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_frozen_blizzard);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FROZEN_BLIZZARD_TICK });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer() || !caster->IsAlive())
            return;

        DynamicObject* zone = caster->GetDynObject(GetId());
        SpellInfo const* tickInfo = sSpellMgr->GetSpellInfo(ShamanData::SPELL_FROZEN_BLIZZARD_TICK);
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

            caster->CastSpell(enemy, tickInfo, TRIGGERED_FULL_MASK, nullptr, aurEff);
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(GetId());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_enh_frozen_blizzard::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_enh_frozen_blizzard::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 17364 Stormstrike (added next to spell_sha_stoneskin_grant). Once per cast, on the primary target's hit:
//  - Improved Stormstrike: the debuff 202402 (aura 271 by mask) at the rank's first DUMMY amount (5/10%), and the
//    energize 202403 for the rank's second DUMMY amount (10/20%) of base mana.
//  - Static Shock rank 3: +SS_STATIC_SHOCK_CHARGES Lightning Shield charges, up to SS_STATIC_SHOCK_CAP.
//  - Frost Spirit: the landed main- and off-hand strike damage of this cast (summed by the window below) is handed to
//    Shaman::OnStormstrikeLanded.
//  - Cleave (D3): Frost Ascendance 1, Elemental Ascendance 2 extra strikes on the nearest enemies within
//    SS_CLEAVE_RADIUS_YD that are in combat with the shaman; weapon strikes only (no Nature debuff, no Improved
//    Stormstrike, no copy). They are the dedicated clones 202413 / 202415, not the stock 32175 / 32176: the stock
//    strikes carry NOT_A_PROC (that is how the primary hits feed Flametongue, Windfury and the rest), the clones carry
//    SUPPRESS_CASTER_PROCS and SUPPRESS_WEAPON_PROCS, so a cleave hit rolls no proc and no enchant.
class spell_sha_enh_stormstrike : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_stormstrike);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_STORMSTRIKE_MAIN_HAND, SPELL_STORMSTRIKE_OFF_HAND,
            ShamanData::SPELL_STORMSTRIKE_CLEAVE_MAIN_HAND, ShamanData::SPELL_STORMSTRIKE_CLEAVE_OFF_HAND,
            ShamanData::SPELL_IMPROVED_STORMSTRIKE_DEBUFF, ShamanData::SPELL_IMPROVED_STORMSTRIKE_MANA });
    }

    bool Load() override
    {
        return GetCaster() && GetCaster()->IsPlayer();
    }

    // The strikes are cast at launch (TRIGGER_SPELL), after OnCast and before the primary's hit hooks
    void HandleOnCast()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetExplTargetUnit();
        if (!player || !target)
            return;

        EnhancementScriptState* state = GetState(player);
        state->stormstrike = GetSpell();
        state->stormstrikeTarget = target->GetGUID();
        state->stormstrikeDamage = 0;
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!player || !target || _done)
            return;

        _done = true;

        EnhancementScriptState* state = GetState(player);
        uint32 landed = 0;
        if (state->stormstrike == GetSpell() && state->stormstrikeTarget == target->GetGUID())
            landed = state->stormstrikeDamage;

        CloseWindow(player);

        ApplyImprovedStormstrike(player, target);
        ApplyStaticShockCapstone(player);

        if (landed)
            Shaman::OnStormstrikeLanded(player, target, landed);

        Cleave(player, target);
    }

    void HandleAfterCast()
    {
        if (Player* player = GetCaster()->ToPlayer())
            CloseWindow(player);
    }

    void CloseWindow(Player* player)
    {
        EnhancementScriptState* state = GetState(player);
        if (state->stormstrike != GetSpell())
            return;

        state->stormstrike = nullptr;
        state->stormstrikeTarget.Clear();
        state->stormstrikeDamage = 0;
    }

    static void ApplyImprovedStormstrike(Player* player, Unit* target)
    {
        uint8 const rank = Shaman::GetTalentRank(player, IMPROVED_STORMSTRIKE_RANKS);
        if (!rank)
            return;

        std::vector<int32> const amounts = GetRankDummyAmounts(IMPROVED_STORMSTRIKE_RANKS[rank - 1]);
        if (amounts.size() < 2)
        {
            LOG_ERROR("scripts.spells", "spell_sha_enh_stormstrike: Improved Stormstrike rank {} needs two DUMMY "
                "effects (debuff %, mana % of base), found {}", IMPROVED_STORMSTRIKE_RANKS[rank - 1], amounts.size());
            return;
        }

        if (amounts[0] > 0)
            player->CastCustomSpell(ShamanData::SPELL_IMPROVED_STORMSTRIKE_DEBUFF, SPELLVALUE_BASE_POINT0, amounts[0],
                target, true);

        int32 const mana = int32(CalculatePct(player->GetCreateMana(), amounts[1]));
        if (mana > 0)
            player->CastCustomSpell(ShamanData::SPELL_IMPROVED_STORMSTRIKE_MANA, SPELLVALUE_BASE_POINT0, mana, player,
                true);
    }

    static void ApplyStaticShockCapstone(Player* player)
    {
        if (Shaman::GetTalentRank(player, STATIC_SHOCK_RANKS) < STATIC_SHOCK_RANKS.size())
            return;

        Aura* shield = player->GetAura(ShamanData::SPELL_LIGHTNING_SHIELD, player->GetGUID());
        if (!shield || !shield->IsUsingCharges())
            return;

        uint32 const added = uint32(shield->GetCharges()) + uint32(ShamanData::SS_STATIC_SHOCK_CHARGES);
        uint32 const charges = std::min<uint32>(added, uint32(ShamanData::SS_STATIC_SHOCK_CAP));
        if (charges > shield->GetCharges())
            shield->SetCharges(uint8(charges));
    }

    static void Cleave(Player* player, Unit* primary)
    {
        uint32 count = 0;
        if (player->HasAura(ShamanData::SPELL_ELEMENTAL_ASCENDANCE, player->GetGUID()))
            count = SS_CLEAVE_ELEMENTAL;
        else if (player->HasAura(ShamanData::SPELL_FROST_ASCENDANCE, player->GetGUID()))
            count = SS_CLEAVE_FROST;

        if (!count)
            return;

        std::list<Unit*> candidates = FindEnemiesAround(player, player, ShamanData::SS_CLEAVE_RADIUS_YD, primary);
        candidates.remove_if([player](Unit* unit) { return !unit->IsInCombatWith(player); });
        candidates.sort([player](Unit const* a, Unit const* b)
        {
            return player->GetExactDist(a) < player->GetExactDist(b);
        });

        for (Unit* unit : candidates)
        {
            if (!count)
                break;

            --count;
            player->CastSpell(unit, ShamanData::SPELL_STORMSTRIKE_CLEAVE_MAIN_HAND, true);
            player->CastSpell(unit, ShamanData::SPELL_STORMSTRIKE_CLEAVE_OFF_HAND, true);
        }
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_sha_enh_stormstrike::HandleOnCast);
        AfterHit += SpellHitFn(spell_sha_enh_stormstrike::HandleAfterHit);
        AfterCast += SpellCastFn(spell_sha_enh_stormstrike::HandleAfterCast);
    }

    bool _done = false;
};

// Sums the primary Stormstrike's strike damage (32175/32176 by the shaman on the primary target, while the window of
// spell_sha_enh_stormstrike is open) for the Frost Spirit copy. Observational: mitigated damage before absorbs.
class ShamanEnhancementUnitScript : public UnitScript
{
public:
    ShamanEnhancementUnitScript() : UnitScript("ShamanEnhancementUnitScript", true,
        { UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL }) { }

    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/) override
    {
        if (damage <= 0 || !spellInfo || !target || !attacker || !attacker->IsPlayer())
            return;

        if (spellInfo->Id != SPELL_STORMSTRIKE_MAIN_HAND && spellInfo->Id != SPELL_STORMSTRIKE_OFF_HAND)
            return;

        EnhancementScriptState* state =
            attacker->ToPlayer()->CustomData.Get<EnhancementScriptState>(ENHANCEMENT_STATE_KEY);
        if (!state || !state->stormstrike || state->stormstrikeTarget != target->GetGUID())
            return;

        state->stormstrikeDamage += uint32(damage);
    }
};

// 30823 Shamanistic Rage (added next to the stock mana proc). On apply: SR_CHARGES charges of the active imbue (Earth
// Charge under Rockbiter; banked during Elemental Ascendance by AddCharge) and the Unleashed Rage clause; on remove the
// clause is re-checked. A login aura reload grants nothing.
class spell_sha_enh_shamanistic_rage : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_shamanistic_rage);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->IsInWorld() || player->GetSession()->PlayerLoading())
            return;

        Shaman::AddCharge(player, uint8(ShamanData::SR_CHARGES), true);
        Shaman::UpdateUnleashedRage(player);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Shaman::UpdateUnleashedRage(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_enh_shamanistic_rage::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_enh_shamanistic_rage::HandleRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 202361 Living Earth (castable; Rockbiter required by CasterAuraSpell 8017, the absorb is data). After the cast:
// LE_STONESKIN Stoneskin; with Ascendance known and at least LE_EARTH_CHARGE_COST Earth Charge, spends it and grants
// Earthen Ascendance (202393).
class spell_sha_enh_living_earth : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_living_earth);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTHEN_ASCENDANCE, ShamanData::SPELL_ASCENDANCE_EARTH_STOMP });
    }

    bool Load() override
    {
        return GetCaster() && GetCaster()->IsPlayer();
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return;

        Shaman::AddStoneskin(player, uint32(ShamanData::LE_STONESKIN));

        if (!Shaman::GetTalentRank(player, ASCENDANCE_RANKS))
            return;

        if (Shaman::SpendEarthCharge(player, uint8(ShamanData::LE_EARTH_CHARGE_COST)))
        {
            player->CastSpell(player, ShamanData::SPELL_EARTHEN_ASCENDANCE, true);
            Shaman::CastAscendanceVisual(player, Shaman::EnhElement::Earth);
        }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_sha_enh_living_earth::HandleAfterCast);
    }
};

// 202361 Living Earth's shield. Absorbs get no engine spell power (potency.md), so the amount is the effect's base
// (Guardian Totems' SPELLMOD_EFFECT1 already applied inside CalcValue) plus the caster's healing power times the
// generated coefficient and level penalty; Guardian Totems' +10/20% (the rank's effect 3 value) is then applied to the
// spell-power part as well, so it covers the whole absorb (GetEarthenWallAbsorb precedent). Fixed at cast.
class spell_sha_enh_living_earth_aura : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_living_earth_aura);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        SpellInfo const* spellInfo = GetSpellInfo();
        SpellEffectInfo const& effect = spellInfo->Effects[aurEff->GetEffIndex()];

        float bonus = effect.BonusMultiplier * float(player->SpellBaseHealingBonusDone(spellInfo->GetSchoolMask()));
        bonus *= player->CalculateLevelPenalty(spellInfo);

        if (uint8 const rank = Shaman::GetTalentRank(player, GUARDIAN_TOTEMS_RANKS))
            if (SpellInfo const* rankInfo = sSpellMgr->GetSpellInfo(GUARDIAN_TOTEMS_RANKS[rank - 1]))
                AddPct(bonus, rankInfo->Effects[EFFECT_2].CalcValue());

        amount = std::max(0, amount + int32(bonus));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sha_enh_living_earth_aura::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// 202387-202390 Fire, Frost, Wind and Elemental Ascendance. Apply: the live Mastery amounts (RefreshAscendance);
// Elemental Ascendance also switches the Unleashed Rage clause on, and on its end off again (UpdateUnleashedRage also
// adds the charges Shamanistic Rage banked). Wind and Elemental Ascendance: each melee hit of the shaman (auto attack
// or melee ability; never triggered hits: Windfury Attacks, Stormstrike strikes and cleaves, Gust splash) rolls
// GUST_CHANCE x Proc Chance to cast a Gust at the struck target, from this aura (the Maelstrom Weapon whitelist reads
// it). spell_proc on 202389/202390: autos + melee spells, HIT, Chance 100.
class spell_sha_enh_ascendance : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_ascendance);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_GUST });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        Shaman::RefreshAscendance(player);
        if (GetId() == ShamanData::SPELL_ELEMENTAL_ASCENDANCE)
            Shaman::UpdateUnleashedRage(player);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (player && GetId() == ShamanData::SPELL_ELEMENTAL_ASCENDANCE)
            Shaman::UpdateUnleashedRage(player);
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (GetId() != ShamanData::SPELL_WIND_ASCENDANCE && GetId() != ShamanData::SPELL_ELEMENTAL_ASCENDANCE)
            return false;

        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || IsTriggeredEvent(eventInfo))
            return false;

        if (!(eventInfo.GetTypeMask() & (PROC_FLAG_DONE_MELEE_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS)))
            return false;

        if (!(eventInfo.GetHitMask() & (PROC_HIT_NORMAL | PROC_HIT_CRITICAL | PROC_HIT_ABSORB)))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsAlive() || !player->IsValidAttackTarget(target))
            return false;

        return Shaman::RollProcChance(player, float(ShamanData::GUST_CHANCE));
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        player->CastSpell(target, ShamanData::SPELL_GUST, true, nullptr, GetAnyEffect(GetAura()));
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_enh_ascendance::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_enh_ascendance::HandleRemove, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_ascendance::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_ascendance::HandleProc);
    }
};

// 202391 Gust. On a landed hit: the splash (202392, half damage by its own potency) on up to GUST_SPLASH_TARGETS
// enemies nearest the struck target within GUST_SPLASH_RADIUS_YD, never the target itself. The splash is triggered
// and rolls nothing (and never another Gust).
class spell_sha_enh_gust : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_gust);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_GUST_SPLASH });
    }

    bool Load() override
    {
        return GetCaster() && GetCaster()->IsPlayer();
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!player || !target || _done)
            return;

        _done = true;

        std::list<Unit*> candidates = FindEnemiesAround(player, target, ShamanData::GUST_SPLASH_RADIUS_YD, target);
        candidates.sort([target](Unit const* a, Unit const* b)
        {
            return target->GetExactDist(a) < target->GetExactDist(b);
        });

        uint32 left = uint32(ShamanData::GUST_SPLASH_TARGETS);
        for (Unit* unit : candidates)
        {
            if (!left)
                break;

            --left;
            player->CastSpell(unit, ShamanData::SPELL_GUST_SPLASH, true);
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_sha_enh_gust::HandleAfterHit);
    }

    bool _done = false;
};

// 202384-202386 Flame, Storm and Wind Burst (cast by Shaman::CastElementalBurst at its destination). Only enemies in
// combat with the shaman or its group (Q16), at most BURST_TARGETS, nearest to the destination first.
class spell_sha_enh_burst : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_burst);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
        {
            targets.clear();
            return;
        }

        targets.remove_if([player](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });

        WorldLocation const* dest = GetExplTargetDest();
        Position const center = dest ? Position(*dest) : player->GetPosition();
        targets.sort([&center](WorldObject const* a, WorldObject const* b)
        {
            return a->GetExactDist(center) < b->GetExactDist(center);
        });

        if (targets.size() > uint32(ShamanData::BURST_TARGETS))
            targets.resize(uint32(ShamanData::BURST_TARGETS));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_enh_burst::FilterTargets, EFFECT_0,
            TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// -202368 Spirit Guard (202368-202370). Parrying an attack under Rockbiter grants SPIRIT_GUARD_STONESKIN_R1..R3
// Stoneskin. The parry chance itself is data (rank aura 47 at 0, Rockbiter child 202412). spell_proc: taken melee
// (auto + melee spell), HitMask PARRY.
class spell_sha_enh_spirit_guard : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_spirit_guard);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetUnitOwner()->ToPlayer();
        return player && (eventInfo.GetHitMask() & PROC_HIT_PARRY) &&
            Shaman::GetActiveImbue(player) == ShamanData::SPELL_ROCKBITER_WEAPON &&
            RankOf(GetId(), SPIRIT_GUARD_RANKS) != 0;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        uint8 const rank = RankOf(GetId(), SPIRIT_GUARD_RANKS);
        if (player && rank)
            Shaman::AddStoneskin(player, uint32(SPIRIT_GUARD_STONESKIN[rank - 1]));
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_spirit_guard::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_spirit_guard::HandleProc);
    }
};

// 30814 Mental Quickness rank 3 (capstone). Once per cast: a direct melee ability (Stormstrike, Lava Lash: melee
// damage class, not triggered) grants the spell buff (202399), a direct damaging spell (magic damage class: shocks,
// bolts, Chain Lightning, Lava Burst, Elemental Blast) the melee buff (202400). The latest replaces the other (group
// 1259 rule 1; removed here too). Auto attacks, periodic and triggered hits trigger nothing. spell_proc: melee +
// magic-negative spells, HIT, SpellTypeMask 0, Chance 100.
class spell_sha_enh_mental_quickness : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_mental_quickness);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_MENTAL_QUICKNESS_SPELLS,
            ShamanData::SPELL_MENTAL_QUICKNESS_MELEE });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !spellInfo || IsTriggeredEvent(eventInfo))
            return false;

        switch (spellInfo->DmgClass)
        {
            case SPELL_DAMAGE_CLASS_MELEE:
                if (!IsDirectDamageHit(eventInfo) && !IsStormstrikeHit(eventInfo))
                    return false;
                _buff = ShamanData::SPELL_MENTAL_QUICKNESS_SPELLS;
                break;
            case SPELL_DAMAGE_CLASS_MAGIC:
                if (!IsDirectDamageHit(eventInfo))
                    return false;
                _buff = ShamanData::SPELL_MENTAL_QUICKNESS_MELEE;
                break;
            default:
                return false;
        }

        return _guard.Claim(eventInfo.GetProcSpell());
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        if (!player || !_buff)
            return;

        uint32 const other = _buff == ShamanData::SPELL_MENTAL_QUICKNESS_SPELLS ?
            ShamanData::SPELL_MENTAL_QUICKNESS_MELEE : ShamanData::SPELL_MENTAL_QUICKNESS_SPELLS;
        player->RemoveAurasDueToSpell(other, player->GetGUID());
        player->CastSpell(player, _buff, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_mental_quickness::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_mental_quickness::HandleProc);
    }

    CastGuard _guard;
    uint32 _buff = 0;
};

// 16303 Thundering Strikes rank 3 (capstone). The roll (10% x Proc Chance, 6 s cooldown: spell_proc 16303, damaging or
// healing spells, HIT phase) is per spell cast, not per target: a HIT-phase row is evaluated once per target hit, and
// the cooldown only stops the rolls after a success. This claims the cast in CheckProc, which runs before the chance
// roll, so only the first target hit of each cast rolls (Chain Lightning, Fire Nova and Chain Heal roll
// once). The default PROC_TRIGGER_SPELL then grants the Agility buff (202397).
class spell_sha_enh_thundering_strikes : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_thundering_strikes);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcPlayer(GetUnitOwner(), eventInfo))
            return false;

        Spell const* procSpell = eventInfo.GetProcSpell();
        return procSpell && _guard.Claim(procSpell);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_thundering_strikes::CheckProc);
    }

    CastGuard _guard;
};

// 29080 Elemental Weapons rank 3 (capstone). A Lava Lash or Lava Burst hit (not triggered: overload copies roll
// nothing) while Flametongue is active, or while Fire Ascendance is held, spreads the shaman's Flame Shock from the
// target to up to FS_SPREAD_TARGETS other enemies within FS_SPREAD_RADIUS_YD of it that are in combat with the shaman
// or the group (D4): the periodic part only, as a fresh application with the shaman's bonuses fixed now (AddAura with
// the shaman as caster), never over a longer Flame Shock of the shaman's. Targets without one come first, then the
// shortest remaining, then the nearest. spell_proc: Lava Lash d2 b2 + Lava Burst d1 b12, melee + magic negative, HIT.
class spell_sha_enh_elemental_weapons : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_elemental_weapons);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FLAME_SHOCK });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !spellInfo || IsTriggeredEvent(eventInfo) || !IsDirectDamageHit(eventInfo))
            return false;

        if (spellInfo->Id != ShamanData::SPELL_LAVA_LASH && spellInfo->Id != ShamanData::SPELL_LAVA_BURST)
            return false;

        if (Shaman::GetActiveImbue(player) != ShamanData::SPELL_FLAMETONGUE_WEAPON &&
            !player->HasAura(ShamanData::SPELL_FIRE_ASCENDANCE, player->GetGUID()))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && target->HasAura(ShamanData::SPELL_FLAME_SHOCK, player->GetGUID());
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        Unit* source = eventInfo.GetActionTarget();
        SpellInfo const* flameShock = sSpellMgr->GetSpellInfo(ShamanData::SPELL_FLAME_SHOCK);
        if (!player || !source || !flameShock)
            return;

        int32 fresh = flameShock->GetMaxDuration();
        player->ApplySpellMod(ShamanData::SPELL_FLAME_SHOCK, SPELLMOD_DURATION, fresh);

        struct Candidate
        {
            Unit* unit;
            int32 remaining;   // -1: no Flame Shock of the shaman's
            float distance;
        };

        std::vector<Candidate> candidates;
        for (Unit* unit : FindEnemiesAround(player, source, ShamanData::FS_SPREAD_RADIUS_YD, source))
        {
            if (!Engagement::IsEngagedWithOwnerOrGroup(unit, player))
                continue;

            int32 remaining = -1;
            if (Aura const* existing = unit->GetAura(ShamanData::SPELL_FLAME_SHOCK, player->GetGUID()))
            {
                remaining = existing->GetDuration();
                if (remaining < 0 || remaining >= fresh)
                    continue;
            }

            candidates.push_back({ unit, remaining, source->GetExactDist(unit) });
        }

        std::sort(candidates.begin(), candidates.end(), [](Candidate const& a, Candidate const& b)
        {
            if (a.remaining != b.remaining)
                return a.remaining < b.remaining;
            return a.distance < b.distance;
        });

        uint32 left = uint32(ShamanData::FS_SPREAD_TARGETS);
        for (Candidate const& candidate : candidates)
        {
            if (!left)
                break;

            if (player->AddAura(ShamanData::SPELL_FLAME_SHOCK, candidate.unit))
                --left;
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_enh_elemental_weapons::CheckProc);
        OnProc += AuraProcFn(spell_sha_enh_elemental_weapons::HandleProc);
    }
};

// 51533 Elemental Spirits (reworked Feral Spirit). Effects 1-3 summon the Fire, Frost and Wind Spirit through
// SummonProperties 61 (no pet bar); with Rockbiter active at the cast, effect 3 summons the Rock Spirit instead. After
// the cast the caster gets the timer buff (202407). Any class can cast it (Classless: the wolves need no shaman state;
// without Rockbiter a non-shaman gets Fire, Frost and Wind Spirits).
class spell_sha_enh_elemental_spirits : public SpellScript
{
    PrepareSpellScript(spell_sha_enh_elemental_spirits);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_ELEMENTAL_SPIRITS_TIMER });
    }

    bool Load() override
    {
        return GetCaster() && GetCaster()->IsPlayer();
    }

    void HandleBeforeCast()
    {
        if (Shaman::GetActiveImbue(GetCaster()) == ShamanData::SPELL_ROCKBITER_WEAPON)
            GetSpell()->SetSpellValue(SPELLVALUE_MISCVALUE2, int32(ShamanData::NPC_ROCK_SPIRIT));
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        caster->CastSpell(caster, ShamanData::SPELL_ELEMENTAL_SPIRITS_TIMER, true);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_sha_enh_elemental_spirits::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_sha_enh_elemental_spirits::HandleAfterCast);
    }
};

// 202408 Spirit Flame Shock (cast by the Fire Spirit). The owner's Fire or Elemental Ascendance raises the periodic
// damage by that Ascendance's Flame Shock (SPELLMOD_DOT) percent, fixed when applied (a refresh re-applies).
class spell_sha_enh_spirit_flame_shock : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_spirit_flame_shock);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player const* owner = Shaman::GetOwningPlayer(GetCaster());
        if (!owner || amount <= 0)
            return;

        if (int32 const pct = GetFlameShockAscendancePct(owner))
            AddPct(amount, pct);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sha_enh_spirit_flame_shock::CalculateAmount,
            EFFECT_FIRST_FOUND, SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// 16287 Improved Ghost Wolf rank 2 (stance-bound passive, re-applied on every entry into Ghost Wolf). Its effect 3
// DUMMY applying = entering Ghost Wolf: the sprint (202396: speed and snare/root removal), at most once per
// IGW_SPRINT_ICD_MS. A login in Ghost Wolf (aura reload) does not sprint.
class spell_sha_enh_improved_ghost_wolf : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_improved_ghost_wolf);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_GHOST_WOLF_SPRINT });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->IsInWorld() || player->GetSession()->PlayerLoading() || !player->IsAlive())
            return;

        if (player->HasSpellCooldown(ShamanData::SPELL_GHOST_WOLF_SPRINT))
            return;

        player->CastSpell(player, ShamanData::SPELL_GHOST_WOLF_SPRINT, true);
        player->AddSpellCooldown(ShamanData::SPELL_GHOST_WOLF_SPRINT, 0, uint32(ShamanData::IGW_SPRINT_ICD_MS));
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_enh_improved_ghost_wolf::HandleApply, EFFECT_2,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_shaman_enhancement_spell_scripts()
{
    RegisterSpellScript(spell_sha_enh_elemental_charge);
    RegisterSpellScript(spell_sha_enh_maelstrom_weapon);
    RegisterSpellScript(spell_sha_enh_static_shock);
    RegisterSpellScript(spell_sha_enh_frozen_power);
    RegisterSpellScript(spell_sha_enh_frozen_blizzard);
    RegisterSpellScript(spell_sha_enh_stormstrike);
    RegisterSpellScript(spell_sha_enh_shamanistic_rage);
    RegisterSpellAndAuraScriptPair(spell_sha_enh_living_earth, spell_sha_enh_living_earth_aura);
    RegisterSpellScript(spell_sha_enh_ascendance);
    RegisterSpellScript(spell_sha_enh_gust);
    RegisterSpellScript(spell_sha_enh_burst);
    RegisterSpellScript(spell_sha_enh_spirit_guard);
    RegisterSpellScript(spell_sha_enh_mental_quickness);
    RegisterSpellScript(spell_sha_enh_thundering_strikes);
    RegisterSpellScript(spell_sha_enh_elemental_weapons);
    RegisterSpellScript(spell_sha_enh_elemental_spirits);
    RegisterSpellScript(spell_sha_enh_spirit_flame_shock);
    RegisterSpellScript(spell_sha_enh_improved_ghost_wolf);
    new ShamanEnhancementUnitScript();
}
