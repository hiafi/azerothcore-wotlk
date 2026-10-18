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
 * Hunter rework - Survival spell scripts (hunter-rework.SHARED.md §A4 / §C4, SURVIVAL.md §0, §5.1-§5.8, §6, §7,
 * §8, §9.2, S3a-HANDOFF A6-A14, S3a-WP-BRIEF resolutions 2, 3, 6). Ids come from the Hunter:: S3 aliases of
 * HunterMechanics.h, or from HunterData:: where the header has no alias; stock ids the hunter DSL never declares stay
 * named constants below. Every per-cast value (the Explosive Shot carry, the Cluster Bombs centre) lives in the
 * SpellScript instance or is captured by value (N9); the shared state lives in HunterMechanics (N15).
 */

#include "HunterMechanics.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Position.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <cmath>
#include <initializer_list>
#include <list>

namespace
{
    // The hunter Player behind a spell's caster or an aura's owner (CR3), nullptr otherwise
    Player* GetHunterPlayer(Unit* unit)
    {
        Player* player = unit ? unit->ToPlayer() : nullptr;
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    // The spell's per-target record for `guid` (missCondition and crit, set at launch), nullptr when there is none.
    // Spell::GetUniqueTargetInfo() is public (Spell.h); the pointer is only used inside the calling hook.
    TargetInfo const* FindTargetInfo(Spell* spell, ObjectGuid const& guid)
    {
        if (!spell || guid.IsEmpty())
            return nullptr;

        for (TargetInfo const& info : *spell->GetUniqueTargetInfo())
            if (info.targetGUID == guid)
                return &info;

        return nullptr;
    }

    // True when the unit hit right now is `spell`'s own target and the launch rolled SPELL_MISS_NONE (the S2a A7
    // gate). A reflected hit lands on the caster, who has no target record, so it fails here too.
    bool HasLanded(Spell* spell, Unit const* target)
    {
        if (!target)
            return false;

        TargetInfo const* info = FindTargetInfo(spell, target->GetGUID());
        return info && info->missCondition == SPELL_MISS_NONE;
    }

    // SURVIVAL §0.4 / §5.6, brief resolution 2: the 40% share of a primary hit (202054) or blast (202055) as dealt.
    // The percent lives on 202054 eff1 for both (read through SpellInfo, L10). Both splashes are TARGET_DEST_DEST
    // area spells: the dest is the primary's position (its corpse on a killing blow, so the share still lands), and
    // the primary is the cast's unit target only so that InitExplicitTargets saves it as the original target before
    // stripping it; spell_hun_explosive_shot_splash removes it from the area list.
    void CastExplosiveSplash(Player* player, Unit* primary, uint32 splashId, int32 dealt)
    {
        if (!player || !primary || dealt <= 0)
            return;

        SpellInfo const* percentInfo = sSpellMgr->AssertSpellInfo(Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH);
        int32 const share = CalculatePct(dealt, percentInfo->Effects[EFFECT_1].CalcValue(player));
        if (share <= 0)
            return;

        SpellCastTargets targets;
        targets.SetDst(*primary);
        targets.SetUnitTarget(primary);

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, share);

        SpellCastResult const result = player->CastSpell(targets, sSpellMgr->AssertSpellInfo(splashId), &values,
            TRIGGERED_FULL_MASK);
        if (result != SPELL_CAST_OK)
            LOG_ERROR("scripts.hunter", "Explosive Shot: splash {} at {} failed (result {})", splashId,
                primary->GetGUID().ToString(), uint32(result));
    }

    // SURVIVAL §5.8: the follow-up offsets, evenly spaced from the first to the last (brief resolution 11:
    // 500, 600, 700, 800 ms with the shipped consts)
    uint32 GetClusterBombsOffset(uint8 index)
    {
        uint8 const count = Hunter::CLUSTER_BOMBS_FOLLOWUP_COUNT;
        if (count < 2)
            return Hunter::CLUSTER_BOMBS_FOLLOWUP_MS;

        uint32 const span = Hunter::CLUSTER_BOMBS_FOLLOWUP_LAST_MS - Hunter::CLUSTER_BOMBS_FOLLOWUP_MS;
        return Hunter::CLUSTER_BOMBS_FOLLOWUP_MS + uint32(index) * span / uint32(count - 1);
    }

    // SURVIVAL §5.8, stale line 12: a point CLUSTER_BOMBS_SCATTER_YD from `centre` in a random direction, on the
    // ground (WorldObject::MovePosition's ground / floor rule: whichever height is nearer the centre's), or the
    // centre itself when no height is found or the centre has no line of sight to the point.
    Position GetClusterBombsPoint(Player* player, Position const& centre)
    {
        float const angle = float(rand_norm()) * 2.0f * float(M_PI);
        float const x = centre.GetPositionX() + Hunter::CLUSTER_BOMBS_SCATTER_YD * std::cos(angle);
        float const y = centre.GetPositionY() + Hunter::CLUSTER_BOMBS_SCATTER_YD * std::sin(angle);
        float const centreZ = centre.GetPositionZ();

        float const ground = player->GetMapHeight(x, y, MAX_HEIGHT);
        float const floor = player->GetMapHeight(x, y, centreZ);
        float const z = std::fabs(ground - centreZ) <= std::fabs(floor - centreZ) ? ground : floor;
        if (z <= INVALID_HEIGHT)
            return centre;

        // Eye height at both ends, as WorldObject::IsWithinLOS adds the collision height to a point
        float const eye = player->GetCollisionHeight();
        if (!player->GetMap()->isInLineOfSight(centre.GetPositionX(), centre.GetPositionY(), centreZ + eye, x, y,
            z + eye, player->GetPhaseMask(), LINEOFSIGHT_ALL_CHECKS, VMAP::ModelIgnoreFlags::M2))
            return centre;

        return Position(x, y, z, centre.GetOrientation());
    }
}

// 202040 Mantis Strike (SURVIVAL §5.1, S3a A9). The enable 202041 (CasterAuraSpell) is checked by CheckCast before
// AfterCast; the cast consumes it for any Player caster (a non-hunter on the Classless / Freepick realm too, R-cpp
// M-1). Improved Mantis Strike 3/3 cuts Wildfire Bomb by 202102 eff1 (real seconds; hunter only, CR3).
class spell_hun_mantis_strike : public SpellScript
{
    PrepareSpellScript(spell_hun_mantis_strike);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_MANTIS_STRIKE_ENABLE, HunterData::SPELL_WILDFIRE_BOMB,
            HunterData::SPELL_IMPROVED_MANTIS_STRIKE_202102 });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        if (Player* casterPlayer = caster ? caster->ToPlayer() : nullptr)
            casterPlayer->RemoveAurasDueToSpell(HunterData::SPELL_MANTIS_STRIKE_ENABLE);

        Player* player = GetHunterPlayer(caster);
        if (!player || !player->HasAura(HunterData::SPELL_IMPROVED_MANTIS_STRIKE_202102))
            return;

        int32 const cut = sSpellMgr->AssertSpellInfo(HunterData::SPELL_IMPROVED_MANTIS_STRIKE_202102)
            ->Effects[EFFECT_1].CalcValue(player);
        if (cut > 0)
            Hunter::ReduceSpellCooldown(player, HunterData::SPELL_WILDFIRE_BOMB, uint32(cut));
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_hun_mantis_strike::HandleAfterCast);
    }
};

// 53301 Explosive Shot - the hit, the recast carry, the hit splash and Shrapnel (SURVIVAL §0.1, §5.5, §5.6, S3a A6;
// stock spell_hun_explosive_shot unbound from -53301). Built: eff0 SCHOOL_DAMAGE (the hit), eff1 APPLY_AURA
// PERIODIC_DUMMY 1000 ms (a bare timer, 2 ticks). Hook order (Spell.cpp DoAllEffectOnTarget): BeforeHit -> the aura
// apply / refresh -> OnHit -> crit, armor, absorb -> damage -> AfterHit.
class spell_hun_explosive_shot_rework : public SpellScript
{
    PrepareSpellScript(spell_hun_explosive_shot_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_EXPLOSIVE_SHOT, Hunter::SPELL_EXPLOSIVE_SHOT_BLAST,
            Hunter::SPELL_SHRAPNEL_HIT, Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH, Hunter::SPELL_SHRAPNEL_R1,
            Hunter::SPELL_SHRAPNEL_R2 });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // V3 done-final carry, read at landing time (before the refresh resets the ticks): every blast the old charge
    // still owes, each valued as one fresh 53352 (no bp: one potency application) through SpellDamageBonusDone (it
    // already holds SPELLMOD_DAMAGE, so T.N.T., Demolitions and Mastery apply once), plus the old charge's own
    // pending carry for each of those blasts. Kept in this instance until AfterHit (N9).
    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        _carry = 0;
        if (missInfo != SPELL_MISS_NONE)
            return;

        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        Aura const* aura = target->GetAura(Hunter::SPELL_EXPLOSIVE_SHOT, player->GetGUID());
        AuraEffect const* timer = aura ? aura->GetEffect(EFFECT_1) : nullptr;
        if (!timer)
            return;

        int32 const left = timer->GetTotalTicks() - int32(timer->GetTickNumber());
        if (left <= 0)
            return;

        SpellInfo const* blastInfo = sSpellMgr->AssertSpellInfo(Hunter::SPELL_EXPLOSIVE_SHOT_BLAST);
        int32 const oldBase = blastInfo->Effects[EFFECT_0].CalcValue(player);
        uint32 const done = oldBase > 0 ? player->SpellDamageBonusDone(target, blastInfo, uint32(oldBase),
            SPELL_DIRECT_DAMAGE, EFFECT_0) : 0;
        _carry = uint32(left) * (done + Hunter::GetExplosiveShotCarry(player, target));
    }

    // Hit only (AfterHit never runs on a miss); gated on the primary's own launch result. GetHitDamage() here is the
    // dealt damage (Spell.cpp m_damage = damageInfo.damage: after crit, armor, taken mods and absorb, V5).
    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        uint32 const carry = _carry;
        _carry = 0;
        if (!player || !target || !HasLanded(GetSpell(), target))
            return;

        // (1) the hit splash, (2) Shrapnel (order kept from §5.6; neither reads the other)
        CastExplosiveSplash(player, target, Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH, GetHitDamage());
        Hunter::TryShrapnel(player, target);

        // (3) the carry per fresh blast, replacing any older value; an immune target holds no aura, so nothing is
        // stored (the old charge's remove hook already cleared it). Only on a charge this hit just applied or
        // refreshed (duration == max in the same call): a target immune to eff1 alone keeps the old, un-refreshed
        // charge, which must not get the carry on top of its own blasts (R-cpp m-3), so its entry is dropped.
        Aura const* aura = target->GetAura(Hunter::SPELL_EXPLOSIVE_SHOT, player->GetGUID());
        AuraEffect const* timer = aura ? aura->GetEffect(EFFECT_1) : nullptr;
        if (!timer || aura->GetDuration() != aura->GetMaxDuration())
        {
            Hunter::SetExplosiveShotCarry(player, target, 0);
            return;
        }

        int32 const ticks = timer->GetTotalTicks();
        Hunter::SetExplosiveShotCarry(player, target, ticks > 0 ? carry / uint32(ticks) : 0);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_hun_explosive_shot_rework::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_hun_explosive_shot_rework::HandleAfterHit);
    }

private:
    uint32 _carry = 0;
};

// 53301 Explosive Shot - the blasts (SURVIVAL §0.1, V2). PeriodicTick runs the scripts before the default tick
// (SpellAuraEffects.cpp PeriodicTick), so PreventDefaultAction skips the stock d1 b31 hardcode
// (HandlePeriodicDummyAuraTick: CastCustomSpell(53352, BP0 = m_amount)) and 53352 is cast with NO bp: its own
// CalcValue and potency run exactly once. aurEff is the triggering aura, as in the hardcode (a failed blast ends the
// charge: stock, accepted, brief resolution 8). The blast is cast for ANY Player caster (a non-hunter on the
// Classless / Freepick realm holds 53301 too, R-cpp M-1); only the carry, splash and Shrapnel are hunter-only, because
// Hunter::ClearState runs for hunters only.
class spell_hun_explosive_shot_rework_aura : public AuraScript
{
    PrepareAuraScript(spell_hun_explosive_shot_rework_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_EXPLOSIVE_SHOT, Hunter::SPELL_EXPLOSIVE_SHOT_BLAST,
            Hunter::SPELL_SHRAPNEL_HIT, Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH, Hunter::SPELL_SHRAPNEL_R1,
            Hunter::SPELL_SHRAPNEL_R2 });
    }

    // By GUID: the charge sits on the enemy, the caster is a Player (an NPC's 53301 keeps the stock hardcode)
    bool Load() override
    {
        return GetCasterGUID().IsPlayer();
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();

        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (!player || !target || !target->IsAlive() || !player->IsValidAttackTarget(target))
            return;

        player->CastSpell(target, Hunter::SPELL_EXPLOSIVE_SHOT_BLAST, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    // REAL only: a same-caster recast refreshes the aura (no remove), so the carry it just stored survives. A caster
    // that left the map resolves to nullptr here; its entry is replaced by the next hit or cleared at logout (N15).
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (GetHunterPlayer(caster))
            Hunter::ClearExplosiveShotCarry(caster, GetTarget());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_explosive_shot_rework_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_explosive_shot_rework_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 53352 Explosive Shot - one blast (SURVIVAL §5.6, S3a A6, brief resolution 3). Built: eff0 SCHOOL_DAMAGE, A 6. For
// SCHOOL_DAMAGE both the done and the taken bonus run at launch (SpellEffects.cpp EffectSchoolDMG), before OnHit, so
// the done-final carry goes through the target's taken path here; crit, armor and absorb still follow, once.
class spell_hun_explosive_shot_blast : public SpellScript
{
    PrepareSpellScript(spell_hun_explosive_shot_blast);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_SHRAPNEL_HIT, Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH,
            Hunter::SPELL_EXPLOSIVE_SHOT_BLAST_SPLASH });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    // An immune target has no damage to add to (m_damage 0)
    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        int32 const damage = GetHitDamage();
        if (damage <= 0)
            return;

        uint32 const carry = Hunter::GetExplosiveShotCarry(player, target);
        if (!carry)
            return;

        SetHitDamage(damage + int32(target->SpellDamageBonusTaken(player, GetSpellInfo(), carry,
            SPELL_DIRECT_DAMAGE)));
    }

    // The blast splash from the dealt blast, then Shrapnel (the 53301 order). 53352 is on OnDirectFireHit's exclusion
    // list: no Burning Tar call here (SURVIVAL §0.23).
    void HandleAfterHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || !HasLanded(GetSpell(), target))
            return;

        CastExplosiveSplash(player, target, Hunter::SPELL_EXPLOSIVE_SHOT_BLAST_SPLASH, GetHitDamage());
        Hunter::TryShrapnel(player, target);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_hun_explosive_shot_blast::HandleOnHit);
        AfterHit += SpellHitFn(spell_hun_explosive_shot_blast::HandleAfterHit);
    }
};

// 202054 / 202055 Explosive Shot splashes (SURVIVAL §0.4, §5.6, brief resolution 2). Built: eff0 SCHOOL_DAMAGE,
// TargetA 87 (TARGET_DEST_DEST) / TargetB 16 (TARGET_UNIT_DEST_AREA_ENEMY), 8 yd, on both bound rows. A dest spell has
// no explicit unit target (GetExplTargetUnit() is null), so the primary is Spell::GetOriginalTarget() (saved by
// InitExplicitTargets from CastExplosiveSplash's unit target). No in-combat filter (§0.4).
class spell_hun_explosive_shot_splash : public SpellScript
{
    PrepareSpellScript(spell_hun_explosive_shot_splash);

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (!GetHunterPlayer(GetCaster()))
            return;

        Unit* primary = GetSpell()->GetOriginalTarget();
        if (!primary)
            return;

        ObjectGuid const primaryGuid = primary->GetGUID();
        targets.remove_if([primaryGuid](WorldObject const* object)
        {
            return !object || object->GetGUID() == primaryGuid;
        });
    }

    // SUPPRESS_CASTER_PROCS hides the hit splash from Tarred's row, so it counts through OnDirectFireHit; the blast
    // splash 202055 never counts (SURVIVAL §0.23 exclusion list)
    void HandleAfterHit()
    {
        if (!GetHunterPlayer(GetCaster()) || GetSpellInfo()->Id != Hunter::SPELL_EXPLOSIVE_SHOT_SPLASH)
            return;

        if (GetHitDamage() > 0)
            Hunter::OnDirectFireHit(GetCaster(), GetHitUnit(), GetSpellInfo());
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_explosive_shot_splash::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
        AfterHit += SpellHitFn(spell_hun_explosive_shot_splash::HandleAfterHit);
    }
};

// 202053 Shrapnel (SURVIVAL §5.7, S3a A7). Cast by Hunter::TryShrapnel. No family bit, so Mastery (202062) and Point
// of No Escape (aura 271 on 202058 only matches spells whose family flags overlap its mask, V-m7) are applied here as
// separate multipliers; the marker never exists in S3a. Built: eff0 SCHOOL_DAMAGE, A 6.
class spell_hun_shrapnel : public SpellScript
{
    PrepareSpellScript(spell_hun_shrapnel);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_TNT_MASTERY, Hunter::SPELL_POINT_OF_NO_ESCAPE_MARKER });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleOnHit()
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        int32 const damage = GetHitDamage();
        if (damage <= 0)
            return;

        float multiplier = 1.0f;
        if (player->HasAura(Hunter::SPELL_TNT_MASTERY))
            multiplier *= 1.0f + player->GetMasteryPercentage() / 100.0f;

        if (target->HasAura(Hunter::SPELL_POINT_OF_NO_ESCAPE_MARKER, player->GetGUID()))
            multiplier *= 1.0f + Hunter::GetPointOfNoEscapePct(player) / 100.0f;

        if (multiplier != 1.0f)
            SetHitDamage(int32(float(damage) * multiplier));
    }

    // SUPPRESS_CASTER_PROCS hides it from Tarred's row (SURVIVAL §0.23)
    void HandleAfterHit()
    {
        if (GetHunterPlayer(GetCaster()) && GetHitDamage() > 0)
            Hunter::OnDirectFireHit(GetCaster(), GetHitUnit(), GetSpellInfo());
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_hun_shrapnel::HandleOnHit);
        AfterHit += SpellHitFn(spell_hun_shrapnel::HandleAfterHit);
    }
};

// 202051 Cluster Bombs - the follow-up scheduler (SURVIVAL §5.8, S3a A8). Built: eff0 SCHOOL_DAMAGE (the first blast,
// A 87 / B 16, 5 yd), eff1 DUMMY A 87 (dest only, so OnEffectHit in HIT mode, never OnEffectHitTarget). Each of the
// CLUSTER_BOMBS_FOLLOWUP_COUNT events captures the hunter's GUID, his map / instance and its point by value (N9) and
// re-fetches the hunter when it fires.
class spell_hun_cluster_bombs : public SpellScript
{
    PrepareSpellScript(spell_hun_cluster_bombs);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_CLUSTER_BOMBS_BLAST });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleScheduler(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetHunterPlayer(GetCaster());
        WorldLocation const* dest = GetExplTargetDest();
        if (!player || !dest)
            return;

        Position const centre = *dest;
        ObjectGuid const playerGuid = player->GetGUID();
        uint32 const mapId = player->GetMapId();
        uint32 const instanceId = player->GetInstanceId();

        for (uint8 i = 0; i < Hunter::CLUSTER_BOMBS_FOLLOWUP_COUNT; ++i)
        {
            Position const point = GetClusterBombsPoint(player, centre);
            player->m_Events.AddEventAtOffset([playerGuid, mapId, instanceId, point]()
            {
                Player* hunter = ObjectAccessor::FindPlayer(playerGuid);
                if (!hunter || hunter->GetMapId() != mapId || hunter->GetInstanceId() != instanceId)
                    return;

                SpellCastTargets targets;
                targets.SetDst(point);

                // A point the hunter can't see fizzles (hunter -> dest LoS, stale line 12; accepted, rare)
                hunter->CastSpell(targets, sSpellMgr->AssertSpellInfo(Hunter::SPELL_CLUSTER_BOMBS_BLAST), nullptr,
                    TRIGGERED_FULL_MASK);
            }, Milliseconds(GetClusterBombsOffset(i)));
        }
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_hun_cluster_bombs::HandleScheduler, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

// 202052 Cluster Bombs - a follow-up blast (SURVIVAL §0.23, §5.8, V1): SUPPRESS_CASTER_PROCS hides it from Tarred's
// row, so each hit target counts through OnDirectFireHit (a centred Tarred enemy gets all five stacks)
class spell_hun_cluster_bombs_blast : public SpellScript
{
    PrepareSpellScript(spell_hun_cluster_bombs_blast);

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleAfterHit()
    {
        if (GetHunterPlayer(GetCaster()) && GetHitDamage() > 0)
            Hunter::OnDirectFireHit(GetCaster(), GetHitUnit(), GetSpellInfo());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_hun_cluster_bombs_blast::HandleAfterHit);
    }
};

// 202097 Demolitions rank 3 - an Explosive Shot hit crit cuts Wildfire Bomb by eff2 (SURVIVAL §6 (3,1), S3a A10).
// The spell_proc row is HIT phase, hit mask CRIT, family mask d1 b31: only 53301's own hit carries that bit, so it
// fires at most once per cast. eff2 is the DUMMY carrier (deterministic, no roll).
class spell_hun_demolitions : public AuraScript
{
    PrepareAuraScript(spell_hun_demolitions);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_WILDFIRE_BOMB });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player)
            return;

        int32 const cut = GetSpellInfo()->Effects[EFFECT_2].CalcValue(player);
        if (cut > 0)
            Hunter::ReduceSpellCooldown(player, HunterData::SPELL_WILDFIRE_BOMB, uint32(cut));
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_hun_demolitions::HandleProc, EFFECT_2, SPELL_AURA_DUMMY);
    }
};

// 202105 Volatile Payload rank 3 - a Wildfire Bomb cast resets both fire traps (SURVIVAL §0.11, §6 (7,1), S3a A10).
// The spell_proc row is CAST phase on d1 b6, chance from the DBC (Proc Chance applies). Explosive and Immolation Trap
// share category 1250; RemoveCategoryCooldown clears the client timer of every spell in it (0-verify (6)).
class spell_hun_volatile_payload : public AuraScript
{
    PrepareAuraScript(spell_hun_volatile_payload);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_EXPLOSIVE_TRAP, HunterData::SPELL_IMMOLATION_TRAP });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        if (Player* player = GetHunterPlayer(GetUnitOwner()))
            player->RemoveCategoryCooldown(Hunter::CATEGORY_FIRE_TRAPS);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_hun_volatile_payload::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 202084 Favored Prey rank 3 - a once-per-cast ranged damage cast or an Auto Shot hit grants the buff for the
// target's creature type (SURVIVAL §0.15, §7.2, S3a A11). The row is CAST | HIT; at CAST there is no action target,
// so the target is Hunter::GetProcTarget (V7); a ground cast (Cluster Bombs) has none and grants nothing. The ten
// buffs share the exclusive spell_group 1242, so a new type replaces the old one. eff1 is the DUMMY carrier.
class spell_hun_favored_prey : public AuraScript
{
    PrepareAuraScript(spell_hun_favored_prey);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_FAVORED_PREY_BEAST, Hunter::SPELL_FAVORED_PREY_DRAGONKIN,
            Hunter::SPELL_FAVORED_PREY_DEMON, Hunter::SPELL_FAVORED_PREY_ELEMENTAL, Hunter::SPELL_FAVORED_PREY_GIANT,
            Hunter::SPELL_FAVORED_PREY_UNDEAD, Hunter::SPELL_FAVORED_PREY_HUMANOID,
            Hunter::SPELL_FAVORED_PREY_CRITTER, Hunter::SPELL_FAVORED_PREY_MECHANICAL,
            Hunter::SPELL_FAVORED_PREY_NOT_SPECIFIED });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    // The buff for `eventInfo`'s target, 0 for none (no target, or a totem / non-combat pet / gas cloud)
    static uint32 GetBuff(ProcEventInfo& eventInfo)
    {
        Unit* target = Hunter::GetProcTarget(eventInfo);
        return target ? Hunter::GetFavoredPreyBuff(target->GetCreatureType()) : 0;
    }

    // Every gate here, so the roll never runs on a no-op (L6)
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player || eventInfo.GetActor() != player || !Hunter::IsOncePerRangedCast(eventInfo))
            return false;

        return GetBuff(eventInfo) != 0;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player)
            return;

        if (uint32 const buff = GetBuff(eventInfo))
            player->CastSpell(player, buff, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_favored_prey::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_favored_prey::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 34500 / 34502 / 34503 Expose Weakness, 34506 / 34507 / 34508 Master Tactician - the once-per-cast gate (SURVIVAL
// §7.2, §8.1, S3a A11). The rows are CAST | HIT; the default action casts the trigger (Expose Weakness: aura 231
// passes the rank's BP0 into 34501; Master Tactician: 34837). The effects differ per talent, so only DoCheckProc.
class spell_hun_sv_ranged_cast_proc : public AuraScript
{
    PrepareAuraScript(spell_hun_sv_ranged_cast_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_EXPOSE_WEAKNESS_34501, HunterData::SPELL_MASTER_TACTICIAN_34837 });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetHunterPlayer(GetUnitOwner());
        return player && eventInfo.GetActor() == player && Hunter::IsOncePerRangedCast(eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_sv_ranged_cast_proc::CheckProc);
    }
};

// 53290 / 53291 / 53292 Hunting Party (stock spell_hun_hunting_party unbound from -53290) - a crit on the cast's
// primary target grants Replenishment (SURVIVAL §8.1, S3a A11). The row is HIT phase; the HIT phase runs per target,
// so the explicit-target check makes it once per cast without a Spell* memo (address reuse, V-m11). eff0 is the
// DUMMY carrier (deterministic, no roll).
class spell_hun_hunting_party_rework : public AuraScript
{
    PrepareAuraScript(spell_hun_hunting_party_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_REPLENISHMENT });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetHunterPlayer(GetUnitOwner());
        if (!player || eventInfo.GetActor() != player || !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_HIT))
            return false;

        Spell const* procSpell = eventInfo.GetProcSpell();
        Unit* actionTarget = eventInfo.GetActionTarget();
        return procSpell && actionTarget && actionTarget == procSpell->m_targets.GetUnitTarget();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        if (Player* player = GetHunterPlayer(GetUnitOwner()))
            player->CastSpell(player, Hunter::SPELL_REPLENISHMENT, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_hunting_party_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_hunting_party_rework::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 34497 / 34498 Thrill of the Hunt - the cooldown cut (SV-B1, SURVIVAL §0.8, S3a A12). Additive: the stock
// spell_hun_thrill_of_the_hunt stays on -34497 for the 40% mana (both prevent the DUMMY's default action). The row is
// CAST phase, hit mask CRIT, chance from the DBC (50 / 100, Proc Chance applies); the cut itself never rolls. The cut
// is the rank's eff1 (read through SpellInfo, L10), doubled by THRILL_MM_CUT_FACTOR for Aimed Shot, Multi-Shot and
// Chimera Shot. Arcane Shot and Explosive Shot share category 1173, so their cut walks the category. The cut lands
// inside the GCD the cast just started and clears that button's client sweep (brief resolution 6: accepted).
class spell_hun_thrill_of_the_hunt_sv : public AuraScript
{
    PrepareAuraScript(spell_hun_thrill_of_the_hunt_sv);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_ARCANE_SHOT, HunterData::SPELL_AIMED_SHOT,
            HunterData::SPELL_MULTI_SHOT, HunterData::SPELL_CHIMERA_SHOT });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetHunterPlayer(GetUnitOwner());
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!player || !procSpell)
            return;

        int32 const cut = GetSpellInfo()->Effects[EFFECT_1].CalcValue(player);
        if (cut <= 0)
            return;

        uint32 const id = procSpell->Id;
        if (id == HunterData::SPELL_ARCANE_SHOT || id == Hunter::SPELL_EXPLOSIVE_SHOT)
            Hunter::ReduceCategoryCooldown(player, Hunter::CATEGORY_ARCANE_EXPLOSIVE, uint32(cut));
        else if (id == HunterData::SPELL_AIMED_SHOT || id == HunterData::SPELL_MULTI_SHOT ||
            id == HunterData::SPELL_CHIMERA_SHOT)
            Hunter::ReduceSpellCooldown(player, id, uint32(cut) * Hunter::THRILL_MM_CUT_FACTOR);
        else
            Hunter::ReduceSpellCooldown(player, id, uint32(cut));   // a no-op without a running cooldown
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_hun_thrill_of_the_hunt_sv::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 202062 T.N.T. Mastery (T.N.T. 3/3, linked_spell) - eff0 (explosives' damage) and eff1 (explosives' DoTs) follow
// the live Mastery %, rounded, re-set only on change (SURVIVAL §7.1, S3a A13; the spell_hun_mm_mastery shape, so
// there is no 1 s window at the DBC 0 after apply)
class spell_hun_tnt_mastery : public AuraScript
{
    PrepareAuraScript(spell_hun_tnt_mastery);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    static int32 GetMasteryAmount(Unit const* owner)
    {
        Player const* player = owner ? owner->ToPlayer() : nullptr;
        return player ? int32(std::lround(player->GetMasteryPercentage())) : 0;
    }

    // eff0 / eff1 start at the live Mastery on apply and on any engine recalculation
    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* owner = GetUnitOwner();
        if (!GetHunterPlayer(owner))
            return;

        amount = GetMasteryAmount(owner);
        canBeRecalculated = true;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!GetHunterPlayer(owner))
            return;

        // Changing the amount re-sends the spell mod to the client, so only do it when the rounded value moved
        int32 const amount = GetMasteryAmount(owner);
        for (uint8 effIndex : { uint8(EFFECT_0), uint8(EFFECT_1) })
        {
            AuraEffect* modEffect = GetEffect(effIndex);
            if (modEffect && modEffect->GetAuraType() == SPELL_AURA_ADD_PCT_MODIFIER &&
                modEffect->GetAmount() != amount)
                modEffect->ChangeAmount(amount, false);
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_tnt_mastery::CalculateAmount, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_tnt_mastery::CalculateAmount, EFFECT_1,
            SPELL_AURA_ADD_PCT_MODIFIER);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_tnt_mastery::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 201600 Glaive Toss - Improved Glaive Toss 3/3's slow on every target hit beyond IGT_SLOW_MIN_DISTANCE_YD (SURVIVAL
// §6 (1,1), S3a A14). Additive: SHARED's spell_hun_glaive_toss keeps its bounce filter. Built: eff0 SCHOOL_DAMAGE
// with chain targets (Improved Glaive Toss's JUMP_TARGETS mod applies to them). 202056 ignores LoS (already hit).
class spell_hun_glaive_toss_sv : public SpellScript
{
    PrepareSpellScript(spell_hun_glaive_toss_sv);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_GLAIVE_TOSS_SLOW, HunterData::SPELL_IMPROVED_GLAIVE_TOSS_202090 });
    }

    bool Load() override
    {
        Unit* caster = GetCaster();
        return caster && caster->IsPlayer();
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetHunterPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || !player->HasAura(HunterData::SPELL_IMPROVED_GLAIVE_TOSS_202090))
            return;

        if (!target->IsAlive() || !player->IsValidAttackTarget(target) ||
            player->GetDistance(target) <= Hunter::IGT_SLOW_MIN_DISTANCE_YD)
            return;

        player->CastSpell(target, HunterData::SPELL_GLAIVE_TOSS_SLOW, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_hun_glaive_toss_sv::HandleHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

void AddSC_hunter_survival_spell_scripts()
{
    RegisterSpellScript(spell_hun_mantis_strike);
    RegisterSpellAndAuraScriptPair(spell_hun_explosive_shot_rework, spell_hun_explosive_shot_rework_aura);
    RegisterSpellScript(spell_hun_explosive_shot_blast);
    RegisterSpellScript(spell_hun_explosive_shot_splash);
    RegisterSpellScript(spell_hun_shrapnel);
    RegisterSpellScript(spell_hun_cluster_bombs);
    RegisterSpellScript(spell_hun_cluster_bombs_blast);
    RegisterSpellScript(spell_hun_demolitions);
    RegisterSpellScript(spell_hun_volatile_payload);
    RegisterSpellScript(spell_hun_favored_prey);
    RegisterSpellScript(spell_hun_sv_ranged_cast_proc);
    RegisterSpellScript(spell_hun_hunting_party_rework);
    RegisterSpellScript(spell_hun_thrill_of_the_hunt_sv);
    RegisterSpellScript(spell_hun_tnt_mastery);
    RegisterSpellScript(spell_hun_glaive_toss_sv);
}
