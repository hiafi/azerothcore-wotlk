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
 * Warlock rework - Demonology pass (S3) spell/aura scripts
 * (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5, warlock-rework.DEMONOLOGY.md §2.7/§7).
 * Replacement classes for stock spell_warlock.cpp bindings the Demonology tree displaces - stock
 * spell_warlock.cpp stays unedited and every class it replaces is left unbound (unbind_script,
 * WP-A's job) rather than rewritten in place (.agents/docs/upstream-merge.md).
 *
 * One class (or SpellScript/AuraScript pair) per row in DEMONOLOGY.md §2.7's binding table; each
 * class's header comment cites the exact §7 subsection it implements. Script names below must
 * match WP-A's `scripted_by`/`unbind_script` calls byte for byte (case-sensitive) - see the
 * DEMONOLOGY-WP-BRIEF.md checklist. Wild Imp / Dreadstalker / Doomguard / Infernal AIs live in
 * src/server/scripts/Pet/pet_warlock_rework.cpp, not here (DEMONOLOGY.md §2.7).
 *
 * WP-0 (2026-09-28) scaffolded this file with only the Molten Core instant-cast source
 * registration (SHARED §4 arbiter; DEMONOLOGY.md §3.4/§7.7) - kept verbatim below, first in
 * AddSC_warlock_demonology_spell_scripts(). Every other class in this file is WP-B's (this pass).
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Containers.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Trainer.h"
#include "Unit.h"
#include "WarlockMechanics.h"
#include "WorldPacket.h"
#include <algorithm>
#include <array>
#include <list>
#include <vector>

namespace
{
    // ------------------------------------------------------------------
    // Stock/cross-spec ids this file needs that aren't part of the frozen WarlockMechanics.h
    // Demonology block - duplicated locally, same shape as spell_warlock_destruction.cpp/
    // warlock_hooks.cpp duplicating cross-spec ids rather than widening the header.
    // ------------------------------------------------------------------
    constexpr uint32 SPELL_DESTRO_DEMONIC_POWER_R1 = 18126;   // Destruction talent (2,0) r1
    constexpr uint32 SPELL_DESTRO_DEMONIC_POWER_R2 = 18127;   // r2
    constexpr std::array<uint32, 3> RANKS_CATACLYSM = { 17778, 17779, 17780 }; // Destruction (§0.2 item 5)
    constexpr uint32 NPC_DEMON_VOIDWALKER = 1860;
    constexpr uint32 NPC_DEMON_FELGUARD = 17252;
    constexpr uint32 SPELL_WARLOCK_SUMMON_FELGUARD = 30146;

    // Summon Infernal's meteor (stock SpellVisual 4859 -> InstantAreaKit 9166 ->
    // spells\infernal_impact_base.m2): its falling bone's translation track reaches the ground at
    // 1000 ms of the model's 2500 ms animation.
    constexpr uint32 INFERNAL_METEOR_IMPACT_MS = 1000;

    // Highest known rank's aura-effect amount / rank index - private copies of
    // WarlockMechanics.cpp's own helpers (internal linkage; every WP-B file that needs a "read live
    // from whichever rank is known" lookup duplicates this small helper rather than exporting it).
    template <std::size_t N>
    int32 GetHighestRankAmount(Unit const* unit, std::array<uint32, N> const& ranksLowToHigh, uint8 effIndex)
    {
        if (!unit)
            return 0;

        for (std::size_t i = ranksLowToHigh.size(); i-- > 0;)
            if (AuraEffect const* eff = unit->GetAuraEffect(ranksLowToHigh[i], effIndex))
                return eff->GetAmount();
        return 0;
    }

    template <std::size_t N>
    uint8 GetHighestKnownRank(Unit const* unit, std::array<uint32, N> const& ranksLowToHigh)
    {
        if (!unit)
            return 0;

        for (std::size_t i = ranksLowToHigh.size(); i-- > 0;)
            if (unit->HasAura(ranksLowToHigh[i]))
                return uint8(i + 1);
        return 0;
    }
}

// ===========================================================================================
// 200820 - Hand of Gul'dan - DEMONOLOGY.md §7.3
// ===========================================================================================
class spell_warl_hand_of_guldan : public SpellScript
{
    PrepareSpellScript(spell_warl_hand_of_guldan);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_SUMMON_WILD_IMP, Warlock::SPELL_SUMMON_IMP_GANG_BOSS,
            Warlock::SPELL_HAND_OF_GULDAN_SPLASH });
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !target)
            return;

        // Base imp count read live from the spell's own eff1 (DUMMY, $s2) rather than hard-coded,
        // so a future retune of that value needs no C++ change.
        int32 count = GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster);

        // Decimation: consume the buff's stack count as bonus imps (§8 native proc trigger already
        // applied the buff; this class only reads and clears it).
        if (Aura* decimation = player->GetAura(Warlock::SPELL_DECIMATION_BUFF))
        {
            if (AuraEffect const* eff = decimation->GetEffect(EFFECT_0))
                count += eff->GetAmount();
            decimation->Remove();
        }

        // Imp Gang Boss - one roll per (non-triggered) cast; the first imp summoned becomes the boss.
        bool gangBoss = false;
        if (!GetSpell()->IsTriggered())
        {
            int32 const chancePct = GetHighestRankAmount(player, Warlock::RANKS_IMP_GANG_BOSS, EFFECT_0);
            if (chancePct > 0)
                gangBoss = roll_chance_f(float(chancePct) * (1.0f + player->GetProcChancePercentage() / 100.0f));
        }

        for (int32 i = 0; i < count; ++i)
            Warlock::TrySummonWildImp(player, target, gangBoss && i == 0);

        if (Warlock::IsInMetamorphosis(player))
            player->CastSpell(target, Warlock::SPELL_HAND_OF_GULDAN_SPLASH, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_hand_of_guldan::HandleAfterHit);
    }
};

// ===========================================================================================
// 200821 - Hand of Gul'dan (splash) - DEMONOLOGY.md §7.3
// ===========================================================================================
class spell_warl_hand_of_guldan_splash : public SpellScript
{
    PrepareSpellScript(spell_warl_hand_of_guldan_splash);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        Unit* explTarget = GetExplTargetUnit();
        targets.remove_if([&](WorldObject* obj)
        {
            if (obj == explTarget)
                return true;
            Unit* unit = obj->ToUnit();
            return !unit || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warl_hand_of_guldan_splash::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// ===========================================================================================
// 200827 - Implosion - DEMONOLOGY.md §7.3
// ===========================================================================================
class spell_warl_implosion : public SpellScript
{
    PrepareSpellScript(spell_warl_implosion);

    SpellCastResult CheckCast()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player || Warlock::CountWildImps(player) == 0)
            return SPELL_FAILED_CANT_DO_THAT_RIGHT_NOW;
        return SPELL_CAST_OK;
    }

    void HandleOnHit()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        ObjectGuid const targetGuid = target->GetGUID();
        for (Creature* imp : Warlock::GetWildImps(player))
        {
            if (!imp->AI())
                continue;
            imp->AI()->SetGUID(targetGuid, Warlock::GUID_SLOT_IMPLODE_TARGET);
            imp->AI()->DoAction(Warlock::ACTION_WILD_IMP_IMPLODE);
        }
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_implosion::CheckCast);
        OnHit += SpellHitFn(spell_warl_implosion::HandleOnHit);
    }
};

// ===========================================================================================
// 200829 - Call Dreadstalkers - DEMONOLOGY.md §7.4
// ===========================================================================================
class spell_warl_call_dreadstalkers : public SpellScript
{
    PrepareSpellScript(spell_warl_call_dreadstalkers);

    void HandleBeforeCast()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player)
            return;

        Unit* target = GetExplTargetUnit();
        Warlock::SetPendingSummon(player,
            { target ? target->GetGUID() : ObjectGuid::Empty, Warlock::NextDreadstalkerPairToken(player) });
    }

    void HandleAfterCast()
    {
        if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
            Warlock::ClearPendingSummon(player);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_warl_call_dreadstalkers::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_warl_call_dreadstalkers::HandleAfterCast);
    }
};

// ===========================================================================================
// 200833 - Summon Infernal - DEMONOLOGY.md §5.1. The SUMMON effect lands on the spell's go, but
// the meteor visual only hits the ground INFERNAL_METEOR_IMPACT_MS later, so the default summon is
// deferred to the impact. The deferred summon mirrors Spell::SummonGuardian for one guardian
// (the caster is always the level-capped player, so no summon-level override is needed).
// ===========================================================================================
class spell_warl_summon_infernal : public SpellScript
{
    PrepareSpellScript(spell_warl_summon_infernal);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return sSummonPropertiesStore.LookupEntry(spellInfo->Effects[EFFECT_0].MiscValueB) != nullptr;
    }

    void HandleSummon(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);

        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        WorldLocation const* dest = GetHitDest();
        if (!player || !dest)
            return;

        SpellInfo const* spellInfo = GetSpellInfo();
        uint32 const spellId = spellInfo->Id;
        uint32 const entry = spellInfo->Effects[effIndex].MiscValue;
        SummonPropertiesEntry const* properties =
            sSummonPropertiesStore.LookupEntry(spellInfo->Effects[effIndex].MiscValueB);
        int32 duration = spellInfo->GetDuration();
        player->ApplySpellMod(spellId, SPELLMOD_DURATION, duration);

        // The spell's dest only carries coordinates (its m_mapId stays MAPID_INVALID), so the map is
        // captured from the caster.
        ObjectGuid const playerGuid = player->GetGUID();
        uint32 const mapId = player->GetMapId();
        uint32 const instanceId = player->GetInstanceId();
        Position const pos = *dest;

        player->m_Events.AddEventAtOffset([playerGuid, mapId, instanceId, pos, entry, properties, duration, spellId]()
        {
            Player* self = ObjectAccessor::FindPlayer(playerGuid);
            if (!self || !self->IsInWorld() || self->GetMapId() != mapId || self->GetInstanceId() != instanceId)
                return;

            TempSummon* summon = self->GetMap()->SummonCreature(entry, pos, properties, duration, self, spellId);
            if (!summon)
                return;

            if (!summon->IsInCombat())
            {
                summon->GetMotionMaster()->Clear(false);
                summon->GetMotionMaster()->MoveFollow(self, PET_FOLLOW_DIST, summon->GetFollowAngle(),
                    MOTION_SLOT_ACTIVE);
            }

            if (properties->Category == SUMMON_CATEGORY_ALLY)
                summon->SetFaction(self->GetFaction());

            // The spell's own SPELL_SUMMON combat-log line (Spell::ExecuteLogEffectSummonObject)
            // was skipped along with the default effect; damage meters need it to credit the
            // Infernal's damage to its owner. Same layout as Spell::SendLogExecute.
            WorldPacket data(SMSG_SPELLLOGEXECUTE, 8 + 4 + 4 + 4 + 4 + 8);
            data << self->GetPackGUID();
            data << uint32(spellId);
            data << uint32(1);                      // effect count
            data << uint32(SPELL_EFFECT_SUMMON);
            data << uint32(1);                      // target count
            data << summon->GetPackGUID();
            self->SendMessageToSet(&data, true);
        }, Milliseconds(INFERNAL_METEOR_IMPACT_MS));
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_warl_summon_infernal::HandleSummon, EFFECT_0, SPELL_EFFECT_SUMMON);
    }
};

// ===========================================================================================
// 686 - Shadow Bolt (Demonology additive) - DEMONOLOGY.md §7.6 (SHARED §4)
// ===========================================================================================
class spell_warl_shadow_bolt_demonology : public SpellScript
{
    PrepareSpellScript(spell_warl_shadow_bolt_demonology);

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        // Legion Strength.
        int32 const perImp = GetHighestRankAmount(player, Warlock::RANKS_LEGION_STRENGTH, EFFECT_0);
        if (perImp > 0)
        {
            float bonusPct = float(perImp);
            if (player->HasAura(Warlock::RANKS_LEGION_STRENGTH[2]))
                bonusPct *= 1.0f + player->GetMasteryPercentage() / 100.0f;

            uint32 const n = Warlock::CountWildImps(player);
            if (n)
                SetHitDamage(int32(float(GetHitDamage()) * (1.0f + float(n) * bonusPct / 100.0f)));
        }

        // Metamorphosis: extend Bane of Doom by 3 s, capped at 30 s remaining.
        if (Warlock::IsInMetamorphosis(player))
        {
            if (Aura* bane = target->GetAura(Warlock::SPELL_BANE_OF_DOOM, player->GetGUID()))
            {
                int32 const rem = bane->GetDuration();
                int32 const newDur = std::min(rem + 3000, 30000);
                if (newDur > rem)
                {
                    bane->SetMaxDuration(bane->GetMaxDuration() + (newDur - rem));
                    bane->SetDuration(newDur);
                }
            }
        }
    }

    void HandleAfterCast()
    {
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetExplTargetUnit();
        if (!player)
            return;

        // Master Summoner.
        int32 const masterSummonerPct = GetHighestRankAmount(player, Warlock::RANKS_MASTER_SUMMONER, EFFECT_0);
        if (masterSummonerPct > 0 && target &&
            roll_chance_f(float(masterSummonerPct) * (1.0f + player->GetProcChancePercentage() / 100.0f)))
            Warlock::TrySummonWildImp(player, target, false);

        // Demonic Calling - resets Hand of Gul'dan's cooldown, gated by its own 10 s ICD (stored on
        // the rank spell id, never cast - druid-rework ICD-key precedent).
        uint8 const rank = GetHighestKnownRank(player, Warlock::RANKS_DEMONIC_CALLING);
        if (rank)
        {
            uint32 const rankId = Warlock::RANKS_DEMONIC_CALLING[rank - 1];
            if (!player->HasSpellCooldown(rankId))
            {
                AuraEffect const* eff = player->GetAuraEffect(rankId, EFFECT_0);
                int32 const chancePct = eff ? eff->GetAmount() : 0;
                if (chancePct > 0 &&
                    roll_chance_f(float(chancePct) * (1.0f + player->GetProcChancePercentage() / 100.0f)))
                {
                    player->RemoveSpellCooldown(Warlock::SPELL_HAND_OF_GULDAN, true);
                    player->AddSpellCooldown(rankId, 0, uint32(GameTime::GetGameTimeMS().count()) + 10000);
                }
            }
        }
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warl_shadow_bolt_demonology::HandleHit);
        AfterCast += SpellCastFn(spell_warl_shadow_bolt_demonology::HandleAfterCast);
    }
};

// ===========================================================================================
// 6353 - Soul Fire (Demonology additive) - DEMONOLOGY.md §7.9
// ===========================================================================================
class spell_warl_soul_fire_demonology : public SpellScript
{
    PrepareSpellScript(spell_warl_soul_fire_demonology);

    void HandleAfterHit()
    {
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !target)
            return;

        HandleImprovedSoulFire(player);
        HandleFelImmolationSpread(player, target);
    }

private:
    void HandleImprovedSoulFire(Player* player)
    {
        uint8 const rank = GetHighestKnownRank(player, Warlock::RANKS_IMPROVED_SOUL_FIRE);
        if (!rank)
            return;

        uint32 const rankId = Warlock::RANKS_IMPROVED_SOUL_FIRE[rank - 1];

        if (!Warlock::IsInDarkApotheosis(player))
        {
            AuraEffect const* eff = player->GetAuraEffect(rankId, EFFECT_0);
            if (eff && player->HasSpellCooldown(Warlock::SPELL_METAMORPHOSIS))
                player->ModifySpellCooldown(Warlock::SPELL_METAMORPHOSIS, -eff->GetAmount());
            return;
        }

        AuraEffect const* pctEff = player->GetAuraEffect(rankId, EFFECT_1);
        int32 const pct = pctEff ? pctEff->GetAmount() : 0;
        if (pct <= 0)
            return;

        int32 amt = int32(CalculatePct(player->GetMaxHealth(), pct));
        int32 const decimationPct = GetHighestRankAmount(player, Warlock::RANKS_DECIMATION, EFFECT_1);
        amt = int32(float(amt) * (1.0f + float(decimationPct) / 100.0f));

        Aura* shield = player->GetAura(Warlock::SPELL_IMPROVED_SOUL_FIRE_SHIELD, player->GetGUID());
        if (shield)
        {
            AuraEffect* shieldEff = shield->GetEffect(EFFECT_0);
            if (shieldEff && shieldEff->GetAmount() >= amt)
            {
                shield->RefreshDuration();
                return;
            }
        }

        player->CastCustomSpell(Warlock::SPELL_IMPROVED_SOUL_FIRE_SHIELD, SPELLVALUE_BASE_POINT0, amt, player, true);
    }

    void HandleFelImmolationSpread(Player* player, Unit* target)
    {
        if (!player->HasAura(Warlock::RANKS_FEL_IMMOLATION[2]) || !Warlock::IsInDarkApotheosis(player) ||
            !target->HasAura(Warlock::SPELL_IMMOLATE, player->GetGUID()))
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, player, 8.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, 8.0f);

        nearby.remove_if([&](Unit* u)
        {
            return u == target || !u->IsAlive() || !player->IsValidAttackTarget(u) ||
                   !u->IsInCombatWith(player) || u->HasAura(Warlock::SPELL_IMMOLATE, player->GetGUID()) ||
                   u->HasAura(Warlock::SPELL_UNSTABLE_AFFLICTION, player->GetGUID());
        });

        nearby.sort(Acore::ObjectDistanceOrderPred(target));

        uint8 placed = 0;
        for (Unit* u : nearby)
        {
            if (placed >= 5)
                break;
            player->AddAura(Warlock::SPELL_IMMOLATE, u);
            ++placed;
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_soul_fire_demonology::HandleAfterHit);
    }
};

// ===========================================================================================
// 47241 - Metamorphosis - DEMONOLOGY.md §5.2, §7.13
// ===========================================================================================
class spell_warl_metamorphosis_demo : public AuraScript
{
    PrepareAuraScript(spell_warl_metamorphosis_demo);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        if (player)
            amount += GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_FORM, EFFECT_0);
    }

    void HandleApplyRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
            Warlock::RefreshDemonicPotency(player);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_metamorphosis_demo::CalculateAmount, EFFECT_2,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        AfterEffectApply += AuraEffectApplyFn(spell_warl_metamorphosis_demo::HandleApplyRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_metamorphosis_demo::HandleApplyRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 200836, 200837, 200838 - Dark Apotheosis / Metamorphosis / Demonic Bulwark form passives -
// DEMONOLOGY.md §5.2, §7.13
// ===========================================================================================
class spell_warl_demonology_form_passive : public AuraScript
{
    PrepareAuraScript(spell_warl_demonology_form_passive);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        if (!player)
            return;

        uint32 const spellId = GetSpellInfo()->Id;
        if (spellId == Warlock::SPELL_METAMORPHOSIS_PASSIVE)
        {
            if (aurEff->GetEffIndex() == EFFECT_1)
                amount = GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_FORM, EFFECT_1);
            else if (aurEff->GetEffIndex() == EFFECT_2)
                amount = player->HasAura(Warlock::RANKS_NEMESIS[2]) ? -50 : 0;
        }
        else if (spellId == Warlock::SPELL_DEMONIC_BULWARK_FORM)
            amount = -GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_BULWARK, EFFECT_0);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_demonology_form_passive::CalculateAmount,
            EFFECT_ALL, SPELL_AURA_ANY);
    }
};

// ===========================================================================================
// 200835 - Dark Apotheosis toggle - DEMONOLOGY.md §7.13 (Bestial Fury precedent)
// ===========================================================================================
class spell_warl_dark_apotheosis : public SpellScript
{
    PrepareSpellScript(spell_warl_dark_apotheosis);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster && caster->HasAura(Warlock::SPELL_DARK_APOTHEOSIS))
        {
            caster->RemoveAurasDueToSpell(Warlock::SPELL_DARK_APOTHEOSIS);
            return SPELL_FAILED_DONT_REPORT;
        }
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_dark_apotheosis::CheckCast);
    }
};

// ===========================================================================================
// 200826 - Unending Resolve - DEMONOLOGY.md §6 (3,3) Demonic Aegis extension
// ===========================================================================================
class spell_warl_unending_resolve : public AuraScript
{
    PrepareAuraScript(spell_warl_unending_resolve);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player || (!Warlock::IsInMetamorphosis(player) && !Warlock::IsInDarkApotheosis(player)))
            return;

        int32 const bonusMs = GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_AEGIS, EFFECT_2);
        if (bonusMs <= 0)
            return;

        if (Aura* aura = GetAura())
        {
            aura->SetMaxDuration(aura->GetMaxDuration() + bonusMs);
            aura->SetDuration(aura->GetDuration() + bonusMs);
        }
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_unending_resolve::HandleApply, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 50590 - Immolation (Aura tick) - DEMONOLOGY.md §7.13, §6 (4,3)/(7,3)
// ===========================================================================================
class spell_warl_immolation_aura_tick : public SpellScript
{
    PrepareSpellScript(spell_warl_immolation_aura_tick);

    void HandleOnHit()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player)
            return;

        // Immolation Aura has no warlock family bit (PLAN §2), so Fel Immolation's native SpellMod
        // on Immolate can't reach it - re-apply the same percentage here.
        int32 const felImmoPct = GetHighestRankAmount(player, Warlock::RANKS_FEL_IMMOLATION, EFFECT_0);
        if (felImmoPct > 0)
            SetHitDamage(int32(float(GetHitDamage()) * (1.0f + float(felImmoPct) / 100.0f)));
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        uint8 const rank = GetHighestKnownRank(player, Warlock::RANKS_DEMONIC_BULWARK);
        if (!rank)
            return;

        uint32 const rankId = Warlock::RANKS_DEMONIC_BULWARK[rank - 1];
        AuraEffect const* dmgEff = player->GetAuraEffect(rankId, EFFECT_1);
        AuraEffect const* hasteEff = player->GetAuraEffect(rankId, EFFECT_2);
        int32 const bp0 = -(dmgEff ? dmgEff->GetAmount() : 0);
        int32 const bp1 = -(hasteEff ? hasteEff->GetAmount() : 0);
        if (bp0 || bp1)
            player->CastCustomSpell(target, Warlock::SPELL_DEMONIC_BULWARK_DEBUFF, &bp0, &bp1, nullptr, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warl_immolation_aura_tick::HandleOnHit);
        AfterHit += SpellHitFn(spell_warl_immolation_aura_tick::HandleAfterHit);
    }
};

// ===========================================================================================
// 200840, 200844, 200850, 200851, 200852, 200854 - hidden demon auras - DEMONOLOGY.md §7.1
// ===========================================================================================
class spell_warl_demon_aura : public AuraScript
{
    PrepareAuraScript(spell_warl_demon_aura);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* target = GetUnitOwner();
        Unit* casterUnit = GetCaster();
        Player* owner = casterUnit ? casterUnit->ToPlayer() : nullptr;
        amount = (owner && target) ?
            Warlock::ComputeDemonAuraAmount(owner, target, GetSpellInfo()->Id, uint8(aurEff->GetEffIndex())) : 0;
    }

    // Only 200840 (Demonic Potency) self-ticks every 5 s (§7.1(a), stock spell_warl_demonic_knowledge
    // pattern) - every other id sharing this (EFFECT_0, MOD_DAMAGE_PERCENT_DONE) filter (200851's
    // own eff0) is left alone below (isPeriodic stays at its DBC default, false).
    void CalcPeriodic(AuraEffect const* aurEff, bool& isPeriodic, int32& amplitude)
    {
        if (aurEff->GetEffIndex() != EFFECT_0 || GetSpellInfo()->Id != Warlock::SPELL_DEMONIC_POTENCY)
            return;

        isPeriodic = true;
        amplitude = 5000;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        PreventDefaultAction();

        Unit* target = GetUnitOwner();
        Unit* casterUnit = GetCaster();

        if (Aura* aura = GetAura())
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect* eff = aura->GetEffect(i))
                    eff->RecalculateAmount();

        // §7.1(b): also keeps 200854 (a separate aura on the same demon) in sync.
        if (target && casterUnit)
            if (Aura* versatility = target->GetAura(Warlock::SPELL_DEMONIC_VERSATILITY, casterUnit->GetGUID()))
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect* eff = versatility->GetEffect(i))
                        eff->RecalculateAmount();
    }

    void Register() override
    {
        // EFFECT_ALL/SPELL_AURA_ANY on all three hooks, matching DoEffectCalcAmount above - this one
        // class is scripted_by'd onto 6 ids (200840, 200844, 200850, 200851, 200852, 200854) whose
        // effect layouts differ (e.g. 200844's eff0 is DUMMY, not MOD_DAMAGE_PERCENT_DONE), so a
        // fixed EFFECT_0/MOD_DAMAGE_PERCENT_DONE filter here left the engine unable to bind the
        // periodic hooks at all for most of them ("did not match dbc effect data", found via boot
        // log). CalcPeriodic/HandlePeriodic already gate on aurEff->GetEffIndex() == EFFECT_0 and
        // GetSpellInfo()->Id == SPELL_DEMONIC_POTENCY internally, so widening the bind is safe.
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_demon_aura::CalculateAmount, EFFECT_ALL,
            SPELL_AURA_ANY);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(spell_warl_demon_aura::CalcPeriodic, EFFECT_ALL,
            SPELL_AURA_ANY);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_demon_aura::HandlePeriodic, EFFECT_ALL,
            SPELL_AURA_ANY);
    }
};

// ===========================================================================================
// 200842, 200845 - Fel Cruelty buff / Demonic Pact Empower - push Potency on apply/remove -
// DEMONOLOGY.md §7.1, §7.8
// ===========================================================================================
class spell_warl_demonic_potency_input : public AuraScript
{
    PrepareAuraScript(spell_warl_demonic_potency_input);

    void HandleApplyRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr)
            Warlock::RefreshDemonicPotency(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_demonic_potency_input::HandleApplyRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_demonic_potency_input::HandleApplyRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 35696 - Demonic Knowledge (Intellect only) - DEMONOLOGY.md §7.13, §6 (1,1) (C8)
// ===========================================================================================
class spell_warl_demonic_knowledge_int : public AuraScript
{
    PrepareAuraScript(spell_warl_demonic_knowledge_int);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* caster = GetCaster())
        {
            uint8 const pct = uint8(aurEff->GetBaseAmount() + aurEff->GetDieSides());
            amount = CalculatePct(caster->GetStat(STAT_INTELLECT), pct);
        }
    }

    void CalcPeriodic(AuraEffect const* /*aurEff*/, bool& isPeriodic, int32& amplitude)
    {
        isPeriodic = true;
        amplitude = 5000;
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();
        GetEffect(aurEff->GetEffIndex())->RecalculateAmount();
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_demonic_knowledge_int::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_DONE);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(spell_warl_demonic_knowledge_int::CalcPeriodic, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_DONE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_demonic_knowledge_int::HandlePeriodic, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_DONE);
    }
};

// ===========================================================================================
// 25228 - Soul Link split - DEMONOLOGY.md §7.5 (C9)
// ===========================================================================================
class spell_warl_soul_link_split : public AuraScript
{
    PrepareAuraScript(spell_warl_soul_link_split);

    void HandleSplit(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& splitAmount)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        uint8 const rank = GetHighestKnownRank(player, Warlock::RANKS_DEMONIC_RESILIENCE);
        float const soulLinkBonus = rank ? float(Warlock::DEMONIC_RESILIENCE_SOUL_LINK[rank - 1]) : 0.0f;
        float const demonDR = rank ? float(Warlock::DEMONIC_RESILIENCE_DEMON_DR[rank - 1]) : 0.0f;
        float const mastery = player->GetMasteryPercentage();

        float share = 20.0f + soulLinkBonus + (rank == 3 ? mastery / 2.0f : 0.0f);
        share = std::min(share, 50.0f);

        uint32 const full = CalculatePct(dmgInfo.GetDamage(), share);
        float petMult = 1.0f - demonDR / 100.0f;
        if (rank == 3)
            petMult *= std::max(0.0f, 1.0f - mastery / 100.0f);

        uint32 const pet = uint32(float(full) * petMult);
        splitAmount = pet;
        dmgInfo.AbsorbDamage(full - pet);
    }

    void Register() override
    {
        OnEffectSplit += AuraEffectSplitFn(spell_warl_soul_link_split::HandleSplit, EFFECT_0);
    }
};

// ===========================================================================================
// 47193 - Demonic Empowerment (Demonology rewrite) - DEMONOLOGY.md §7.10 (R)
// ===========================================================================================
class spell_warl_demonic_empowerment_demo : public SpellScript
{
    PrepareSpellScript(spell_warl_demonic_empowerment_demo);

    void HandleScriptEffect(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* pet = GetHitUnit();
        if (!caster || !pet)
            return;

        if (pet->GetEntry() == NPC_DEMON_VOIDWALKER)
        {
            int32 const bp = int32(CalculatePct(pet->GetMaxHealth(), 20));
            pet->CastCustomSpell(pet, Warlock::SPELL_DEMONIC_EMPOWERMENT_VOIDWALKER, &bp, nullptr, nullptr, true);
        }
        else if (pet->GetEntry() == NPC_DEMON_FELGUARD)
            pet->CastSpell(pet, Warlock::SPELL_DEMONIC_EMPOWERMENT_FELGUARD, true);

        Player* player = caster->ToPlayer();
        if (!player)
            return;

        std::vector<Creature*> imps = Warlock::GetWildImps(player);
        std::sort(imps.begin(), imps.end(), [](Creature* a, Creature* b)
        {
            uint32 const ea = a->AI() ? a->AI()->GetData(Warlock::DATA_WILD_IMP_ENERGY) : 0;
            uint32 const eb = b->AI() ? b->AI()->GetData(Warlock::DATA_WILD_IMP_ENERGY) : 0;
            return ea < eb;
        });

        uint8 sacrificed = 0;
        for (Creature* imp : imps)
        {
            if (sacrificed >= 2)
                break;
            if (!imp->AI())
                continue;

            imp->AI()->DoAction(Warlock::ACTION_WILD_IMP_SACRIFICE);
            Warlock::GrantMoltenCore(player, 1);
            ++sacrificed;
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warl_demonic_empowerment_demo::HandleScriptEffect, EFFECT_0,
            SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// ===========================================================================================
// 53646, 54909 - Demonic Pact (pet proc) - DEMONOLOGY.md §7.13, §6 (9,2)
// ===========================================================================================
class spell_warl_demonic_pact_demo : public AuraScript
{
    PrepareAuraScript(spell_warl_demonic_pact_demo);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* actor = eventInfo.GetActor();
        if (!actor || !actor->IsPet())
            return false;

        Unit* owner = actor->GetOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        return player && player->HasAura(Warlock::RANKS_DEMONIC_PACT[2]);
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* actor = eventInfo.GetActor();
        Unit* owner = actor ? actor->GetOwner() : nullptr;
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player)
            return;

        int32 const sp = int32(CalculatePct(player->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_MAGIC), 10));

        AuraEffect const* existingInt = player->GetAuraEffect(Warlock::SPELL_DEMONIC_PACT_RAID, EFFECT_2);
        int32 const currentIntBonus = existingInt ? existingInt->GetAmount() : 0;
        int32 const baseInt = int32(player->GetStat(STAT_INTELLECT)) - currentIntBonus;
        int32 const intBonus = int32(CalculatePct(std::max(0, baseInt), 10));

        int32 bp0 = sp, bp1 = sp, bp2 = intBonus;
        player->CastCustomSpell(player, Warlock::SPELL_DEMONIC_PACT_RAID, &bp0, &bp1, &bp2, true);
        player->CastSpell(player, Warlock::SPELL_DEMONIC_PACT_EMPOWER, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_demonic_pact_demo::CheckProc);
        OnProc += AuraProcFn(spell_warl_demonic_pact_demo::HandleProc);
    }
};

// ===========================================================================================
// 200892 - Fel Cruelty (capstone proc gate) - DEMONOLOGY.md §7.8
// ===========================================================================================
class spell_warl_fel_cruelty : public AuraScript
{
    PrepareAuraScript(spell_warl_fel_cruelty);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_WARLOCK)
            return false;

        if (!(spellInfo->GetSchoolMask() & (SPELL_SCHOOL_MASK_SHADOW | SPELL_SCHOOL_MASK_FIRE)))
            return false;

        if (!(eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC))
            return true;

        // Only Bane of Doom ticks count as periodic damage for this capstone (Immolate's DoT and
        // every other periodic effect are rejected).
        return spellInfo->Id == Warlock::SPELL_BANE_OF_DOOM;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_fel_cruelty::CheckProc);
    }
};

// ===========================================================================================
// 200870 - Impending Doom capstone proc - DEMONOLOGY.md §6 (2,2)
// ===========================================================================================
class spell_warl_impending_doom : public AuraScript
{
    PrepareAuraScript(spell_warl_impending_doom);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        Unit* target = eventInfo.GetProcTarget();
        if (player && target)
            Warlock::TrySummonWildImp(player, target, false);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warl_impending_doom::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 200874, 200875, 200876 - Fel Immolation leech - DEMONOLOGY.md §7.13, SHARED §4
// ===========================================================================================
class spell_warl_fel_immolation_leech : public AuraScript
{
    PrepareAuraScript(spell_warl_fel_immolation_leech);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player || Warlock::GetActiveLeechTalent(player) != Warlock::LeechTalent::FelImmolation)
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo &&
            (spellInfo->Id == Warlock::SPELL_IMMOLATE || spellInfo->Id == Warlock::SPELL_IMMOLATION_AURA_TICK);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        DamageInfo const* dmgInfo = eventInfo.GetDamageInfo();
        if (!caster || !dmgInfo)
            return;

        int32 const heal = int32(CalculatePct(dmgInfo->GetDamage(), aurEff->GetAmount()));
        if (heal > 0)
            caster->CastCustomSpell(Warlock::SPELL_FEL_IMMOLATION_HEAL, SPELLVALUE_BASE_POINT0, heal, caster, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_fel_immolation_leech::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warl_fel_immolation_leech::HandleProc, EFFECT_2, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 200899, 200900, 200901 - Fel Reprisal - DEMONOLOGY.md §6 (8,3)
// ===========================================================================================
class spell_warl_fel_reprisal : public AuraScript
{
    PrepareAuraScript(spell_warl_fel_reprisal);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = GetTarget();
        if (!target || !Warlock::IsInDarkApotheosis(target))
            return false;

        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC)
        {
            SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
            return spellInfo && spellInfo->Id == Warlock::SPELL_IMMOLATE;
        }

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_fel_reprisal::CheckProc);
    }
};

// ===========================================================================================
// 200844 (additional binding) - Grimoire of Synergy pet proc - DEMONOLOGY.md §7.13, §6 (5,2)
// ===========================================================================================
class spell_warl_grimoire_of_synergy_pet : public AuraScript
{
    PrepareAuraScript(spell_warl_grimoire_of_synergy_pet);

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        Unit* felguard = GetTarget();
        AuraEffect const* eff = felguard ?
            felguard->GetAuraEffect(Warlock::SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA, EFFECT_0) : nullptr;
        if (!eff)
            return false;

        return roll_chance_f(float(eff->GetAmount()) * Warlock::GetOwnerProcChanceMultiplier(felguard));
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        Unit* felguard = GetTarget();
        Unit* owner = felguard ? felguard->GetOwner() : nullptr;
        if (owner)
            owner->CastSpell(owner, Warlock::SPELL_GRIMOIRE_OF_SYNERGY_BUFF, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_grimoire_of_synergy_pet::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warl_grimoire_of_synergy_pet::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 200850 (additional binding) - Fel Vitality mana regen - DEMONOLOGY.md §7.1
// ===========================================================================================
class spell_warl_fel_vitality_regen : public AuraScript
{
    PrepareAuraScript(spell_warl_fel_vitality_regen);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* demon = GetTarget();
        Unit* casterUnit = GetCaster();
        Player* owner = casterUnit ? casterUnit->ToPlayer() : nullptr;
        if (!demon || !owner)
            return;

        // Regen is "for main/enslaved demons" only (§7.1) - Dreadstalkers get the Sta/Int half of
        // Fel Vitality but not this periodic tick.
        Warlock::DemonKind const kind = Warlock::GetDemonKind(demon, owner);
        bool const eligible = kind == Warlock::DemonKind::Imp || kind == Warlock::DemonKind::Voidwalker ||
            kind == Warlock::DemonKind::Succubus || kind == Warlock::DemonKind::Felhunter ||
            kind == Warlock::DemonKind::Felguard || kind == Warlock::DemonKind::Enslaved;
        if (!eligible || demon->GetMaxPower(POWER_MANA) == 0)
            return;

        int32 const regenPct = GetHighestRankAmount(owner, Warlock::RANKS_FEL_VITALITY, EFFECT_2);
        if (regenPct <= 0)
            return;

        int32 const missing = int32(demon->GetMaxPower(POWER_MANA)) - int32(demon->GetPower(POWER_MANA));
        int32 const amount = int32(CalculatePct(missing, regenPct));
        if (amount > 0)
            demon->EnergizeBySpell(demon, Warlock::SPELL_FEL_VITALITY_DEMON, amount, POWER_MANA);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_fel_vitality_regen::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// ===========================================================================================
// Healthstone-use spells (DATA-INVENTORY §9) - Improved Healthstone SP buff - DEMONOLOGY.md §6 (0,2)
// ===========================================================================================
class spell_warl_healthstone_sp : public SpellScript
{
    PrepareSpellScript(spell_warl_healthstone_sp);

    void HandleAfterCast()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player)
            return;

        int32 const pct = GetHighestRankAmount(player, Warlock::RANKS_IMPROVED_HEALTHSTONE, EFFECT_1);
        if (pct <= 0)
            return;

        int32 const sp = int32(CalculatePct(player->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_MAGIC), pct));
        if (sp > 0)
            player->CastCustomSpell(player, Warlock::SPELL_IMPROVED_HEALTHSTONE_SP, &sp, &sp, nullptr, true);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_warl_healthstone_sp::HandleAfterCast);
    }
};

// ===========================================================================================
// 7812 - Sacrifice (Voidwalker absorb) - DEMONOLOGY.md §6 (2,3)
// ===========================================================================================
class spell_warl_sacrifice_brutality : public AuraScript
{
    PrepareAuraScript(spell_warl_sacrifice_brutality);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* caster = GetCaster();
        Unit* owner = caster ? caster->GetOwner() : nullptr;
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player)
            return;

        int32 const genPct = GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_BRUTALITY, EFFECT_0);
        int32 const sacPct = GetHighestRankAmount(player, Warlock::RANKS_DEMONIC_BRUTALITY, EFFECT_1);
        if (!genPct && !sacPct)
            return;

        // The engine's own SpellMod already applied genPct on top of the base amount - this layers
        // the sacPct/genPct ratio on top of that to reach the talent's real +15/30/50% total.
        amount = int32(float(amount) * float(100 + sacPct) / float(100 + genPct));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_sacrifice_brutality::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// ===========================================================================================
// 1098 - Enslave Demon - DEMONOLOGY.md §7.13
// ===========================================================================================
class spell_warl_enslave_demon_potency : public AuraScript
{
    PrepareAuraScript(spell_warl_enslave_demon_potency);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (player && target)
            Warlock::RefreshDemonAuras(player, target);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (!player || !target)
            return;

        for (uint32 spellId : { Warlock::SPELL_DEMONIC_POTENCY, Warlock::SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA,
                                 Warlock::SPELL_FEL_VITALITY_DEMON, Warlock::SPELL_FEL_BOND_AURA,
                                 Warlock::SPELL_BRUTALITY_VOIDWALKER, Warlock::SPELL_DEMONIC_VERSATILITY })
            target->RemoveAura(spellId, player->GetGUID());

        player->RemoveAura(Warlock::SPELL_FEL_BOND_AURA, player->GetGUID());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_enslave_demon_potency::HandleApply, EFFECT_0,
            SPELL_AURA_MOD_CHARM, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_enslave_demon_potency::HandleRemove, EFFECT_0,
            SPELL_AURA_MOD_CHARM, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 200824, 200834 - guardian hit-damage multipliers (Demonic Power / Cataclysm) - DEMONOLOGY.md
// §7.2, §7.4, §11 Q7/Q8. Guardian spells stay SpellClassSet 0 (leak rule) - any owner talent bonus
// is applied to the hit here, never to bp0.
// ===========================================================================================
class spell_warl_guardian_hit_mods : public SpellScript
{
    PrepareSpellScript(spell_warl_guardian_hit_mods);

    void HandleOnHit()
    {
        Unit* guardian = GetCaster();
        Unit* owner = guardian ? guardian->GetOwner() : nullptr;
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player)
            return;

        uint32 const spellId = GetSpellInfo()->Id;
        int32 pct = 0;

        if (spellId == Warlock::SPELL_FEL_FIREBOLT)
        {
            if (player->HasAura(SPELL_DESTRO_DEMONIC_POWER_R2))
                pct = 14;
            else if (player->HasAura(SPELL_DESTRO_DEMONIC_POWER_R1))
                pct = 7;
        }
        else if (spellId == Warlock::SPELL_INFERNAL_IMMOLATION)
            pct = GetHighestRankAmount(player, RANKS_CATACLYSM, EFFECT_0);

        if (pct)
            SetHitDamage(int32(float(GetHitDamage()) * (1.0f + float(pct) / 100.0f)));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warl_guardian_hit_mods::HandleOnHit);
    }
};

// ===========================================================================================
// ScriptMgr classes (not spell_script_names rows) - DEMONOLOGY-WP-BRIEF.md's checklist
// ===========================================================================================

// PlayerScript: Legion's Call sync (§7.11), Potency refresh on talent/spec changes (§7.1),
// per-player state cleanup on logout.
class warlock_demonology_player_script : public PlayerScript
{
public:
    warlock_demonology_player_script()
        : PlayerScript("warlock_demonology_player_script",
                        { PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET,
                          PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_LOGIN,
                          PLAYERHOOK_ON_GET_TRAINER_SPELL_STATE, PLAYERHOOK_ON_LOGOUT })
    {
    }

    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 /*spellid*/) override
    {
        if (!IsWarlock(player))
            return;
        Warlock::SyncLegionsCall(player);
        RefreshCurrentDemon(player);
    }

    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        if (!IsWarlock(player))
            return;
        Warlock::SyncLegionsCall(player, true);
        // This hook fires before the reset actually removes any talent (Player.cpp:3895, same
        // reason SyncLegionsCall takes an explicit losingTalent flag rather than re-checking
        // HasTalent here), and Player::resetTalents() unconditionally dismisses the pet right
        // after (Player.cpp:3921) - so RefreshDemonAuras never runs again until a new pet is
        // summoned. Without this, the warlock's own Fel Bond self-copy (the only demon-aura state
        // that lives on the warlock rather than the dismissed pet) would keep its pre-reset amount
        // until then (found in user review, 2026-09-28). Unconditional and harmless if not present.
        player->RemoveAura(Warlock::SPELL_FEL_BOND_AURA, player->GetGUID());
    }

    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        if (!IsWarlock(player))
            return;
        Warlock::SyncLegionsCall(player);
        RefreshCurrentDemon(player);
    }

    void OnPlayerLogin(Player* player) override
    {
        if (IsWarlock(player))
            Warlock::SyncLegionsCall(player);
    }

    void OnPlayerGetTrainerSpellState(Player const* player, uint32 /*trainerId*/, uint32 spellId,
        Trainer::SpellState& state) override
    {
        if (!player || player->getClass() != CLASS_WARLOCK)
            return;

        if ((spellId == Warlock::SPELL_INFERNO || spellId == Warlock::SPELL_RITUAL_OF_DOOM) &&
            player->HasTalent(Warlock::SPELL_LEGIONS_CALL, player->GetActiveSpec()))
            state = Trainer::SpellState::Unavailable;
    }

    void OnPlayerLogout(Player* player) override
    {
        if (IsWarlock(player))
            Warlock::ClearDemonologyPlayerState(player->GetGUID());
    }

private:
    static bool IsWarlock(Player const* player)
    {
        return player && player->getClass() == CLASS_WARLOCK;
    }

    static void RefreshCurrentDemon(Player* player)
    {
        if (Unit* pet = player->GetPet())
            Warlock::RefreshDemonAuras(player, pet);
        else if (Unit* charm = player->GetCharm())
            Warlock::RefreshDemonAuras(player, charm);
    }
};

// UnitScript: Hand of Gul'dan splash crit -> Fel Cruelty (§7.8). 200821 carries
// SPELL_ATTR3_SUPPRESS_CASTER_PROCS so the native proc system never sees its crits.
class warlock_demonology_unit_script : public UnitScript
{
public:
    warlock_demonology_unit_script()
        : UnitScript("warlock_demonology_unit_script", true, { UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL })
    {
    }

    void OnSpellDamageTakenFinal(Unit* /*target*/, Unit* attacker, int32 /*damage*/, SpellInfo const* spellInfo,
        bool isCrit) override
    {
        if (!spellInfo || spellInfo->Id != Warlock::SPELL_HAND_OF_GULDAN_SPLASH || !isCrit)
            return;

        Player* player = attacker ? attacker->ToPlayer() : nullptr;
        if (player && player->HasAura(Warlock::SPELL_FEL_CRUELTY_R3))
            player->CastSpell(player, Warlock::SPELL_FEL_CRUELTY_BUFF, true);
    }
};

// UnitScript: Felguard auto-attacks -10% (user ruling 2026-10-08, DPS balance pass). White hits only; Cleave and
// Legion Strike are spells and do not pass through UNITHOOK_MODIFY_MELEE_DAMAGE.
class warlock_felguard_melee_unit_script : public UnitScript
{
public:
    warlock_felguard_melee_unit_script()
        : UnitScript("warlock_felguard_melee_unit_script", true, { UNITHOOK_MODIFY_MELEE_DAMAGE })
    {
    }

    void ModifyMeleeDamage(Unit* /*target*/, Unit* attacker, uint32& damage) override
    {
        if (!attacker || !damage || attacker->GetEntry() != NPC_DEMON_FELGUARD)
            return;

        Unit* owner = attacker->GetOwner();
        if (!owner || !owner->IsPlayer())
            return;

        // Felguard white-hit damage, in percent: dbc-tools data in Summon Felguard 30146 effect 2 (EFFECT_1)
        // (user ruling 2026-10-08, DPS balance pass). Unchanged if the spell is missing.
        if (SpellInfo const* summonInfo = sSpellMgr->GetSpellInfo(SPELL_WARLOCK_SUMMON_FELGUARD))
            damage = uint32(float(damage) * float(summonInfo->Effects[EFFECT_1].CalcValue()) / 100.0f);
    }
};

void AddSC_warlock_demonology_spell_scripts()
{
    // Molten Core: third Soul Fire instant-cast source (SHARED §4 arbiter, priority = registration
    // order - Empowered Imp > Soulburn > Molten Core). onConsumed drops one 71165 stack if it is
    // still up when the arbiter's OnSpellCast handler fires for the recorded cast (DEMONOLOGY.md
    // §3.4, §7.7 - "must not assume grant time"). WP-0's original registration - do not duplicate.
    Warlock::RegisterInstantCastSource(Warlock::SPELL_SOUL_FIRE, Warlock::InstantCastSource::MoltenCore,
        [](Player* p) { return p->HasAura(Warlock::SPELL_MOLTEN_CORE); },
        [](Player* p) { if (Aura* mc = p->GetAura(Warlock::SPELL_MOLTEN_CORE)) mc->ModStackAmount(-1); });

    RegisterSpellScript(spell_warl_hand_of_guldan);
    RegisterSpellScript(spell_warl_hand_of_guldan_splash);
    RegisterSpellScript(spell_warl_implosion);
    RegisterSpellScript(spell_warl_call_dreadstalkers);
    RegisterSpellScript(spell_warl_summon_infernal);
    RegisterSpellScript(spell_warl_shadow_bolt_demonology);
    RegisterSpellScript(spell_warl_soul_fire_demonology);
    RegisterSpellScript(spell_warl_metamorphosis_demo);
    RegisterSpellScript(spell_warl_demonology_form_passive);
    RegisterSpellScript(spell_warl_dark_apotheosis);
    RegisterSpellScript(spell_warl_unending_resolve);
    RegisterSpellScript(spell_warl_immolation_aura_tick);
    RegisterSpellScript(spell_warl_demon_aura);
    RegisterSpellScript(spell_warl_demonic_potency_input);
    RegisterSpellScript(spell_warl_demonic_knowledge_int);
    RegisterSpellScript(spell_warl_soul_link_split);
    RegisterSpellScript(spell_warl_demonic_empowerment_demo);
    RegisterSpellScript(spell_warl_demonic_pact_demo);
    RegisterSpellScript(spell_warl_fel_cruelty);
    RegisterSpellScript(spell_warl_impending_doom);
    RegisterSpellScript(spell_warl_fel_immolation_leech);
    RegisterSpellScript(spell_warl_fel_reprisal);
    RegisterSpellScript(spell_warl_grimoire_of_synergy_pet);
    RegisterSpellScript(spell_warl_fel_vitality_regen);
    RegisterSpellScript(spell_warl_healthstone_sp);
    RegisterSpellScript(spell_warl_sacrifice_brutality);
    RegisterSpellScript(spell_warl_enslave_demon_potency);
    RegisterSpellScript(spell_warl_guardian_hit_mods);

    new warlock_demonology_player_script();
    new warlock_demonology_unit_script();
    new warlock_felguard_melee_unit_script();
}
