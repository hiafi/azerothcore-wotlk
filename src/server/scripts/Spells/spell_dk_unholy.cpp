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
 * Death Knight Unholy spec scripts (death-knight-rework S3a). Spell ids come from DeathKnightData:: (generated,
 * DSL-declared). Script table and rules: .agents/plans/death-knight-rework/death-knight-rework.S3a-WP-BRIEF.md.
 *
 * Rules every script here follows:
 *   - a non-player caster returns at once (NPC initiates cast 47632, Dancing Rune Weapon 27893 copies Plague Strike,
 *     Scourge Strike and Death Coil; 55078 / 55095 are spawn auras on four creatures);
 *   - hit damage changes only in OnHit with SetHitDamage;
 *   - per-cast / per-player state lives on CustomData, nothing is file-static.
 */

#include "CellImpl.h"
#include "Creature.h"
#include "DataMap.h"
#include "DeathKnightMechanics.h"
#include "EngagementMechanics.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Map.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <unordered_map>

namespace
{
    // Stock ids without a DeathKnightData:: name (D14)
    constexpr uint32 SPELL_SCOURGE_STRIKE_SHADOW = 70890;
    constexpr uint32 SPELL_ITEM_T8_MELEE_4P_BONUS = 64736;
    constexpr uint32 SPELL_SHADOWMOURNE = 71903;
    constexpr uint32 SPELL_SHADOWMOURNE_CHAOS_BANE_DAMAGE = 71904;
    constexpr uint32 SPELL_SHADOWMOURNE_SOUL_FRAGMENT = 71905;
    constexpr uint32 SPELL_SHADOWMOURNE_CHAOS_BANE_BUFF = 73422;
    constexpr uint32 SPELL_CORPSE_EXPLOSION_SUICIDE = 43999;
    constexpr uint32 SPELL_CORPSE_EXPLOSION_VISUAL = 51270;
    constexpr uint32 SPELL_GHOUL_CLAW = 47468;
    constexpr uint32 NPC_GHOUL = 26125;

    constexpr char const* LESSER_GHOUL_MARK_KEY = "deathknight_unholy_lesser_ghoul_mark";

    // Shadowmourne: 75% soul fragment per Scourge Strike hit, never in battlegrounds / arenas (stock rule)
    constexpr int32 SHADOWMOURNE_FRAGMENT_CHANCE_PCT = 75;
    constexpr uint32 SHADOWMOURNE_FRAGMENTS_FOR_CHAOS_BANE = 10;

    // A Lesser Ghoul whose lifetime timer has been handed to the mechanics layer
    struct LesserGhoulMark : DataMap::Base
    {
        bool started = false;
    };

    Player* GetPlayerCaster(Unit* caster)
    {
        return caster ? caster->ToPlayer() : nullptr;
    }

    // The Proc Chance stat as Aura::CalcProcChance applies it to every native proc
    float GetProcChanceFactor(Player const* dk)
    {
        return 1.0f + dk->GetProcChancePercentage() / 100.0f;
    }

    // A rank passive carries its value as the amount of its first effect; the highest rank known wins
    int32 GetRankAmount(Unit const* unit, std::initializer_list<uint32> ranksHighestFirst)
    {
        for (uint32 const rank : ranksHighestFirst)
            if (AuraEffect const* effect = unit->GetAuraEffect(rank, EFFECT_0))
                return effect->GetAmount();

        return 0;
    }

    // Reaping: percent added to Scourge Strike's Death Rune chance
    int32 GetReapingPct(Unit const* dk)
    {
        return GetRankAmount(dk, { DeathKnightData::SPELL_REAPING_56835, DeathKnightData::SPELL_REAPING_56834,
            DeathKnightData::SPELL_REAPING });
    }

    // Only the Death Knight's own Blood Plague and Frost Fever count for Scourge Strike (U11)
    uint32 CountOwnDiseases(Unit const* target, ObjectGuid dkGuid)
    {
        uint32 count = 0;
        if (target->HasAura(DeathKnightData::SPELL_BLOOD_PLAGUE, dkGuid))
            ++count;
        if (target->HasAura(DeathKnightData::SPELL_FROST_FEVER, dkGuid))
            ++count;

        return count;
    }

    // The Death Knight's permanent (Master of Ghouls) ghoul, alive, or nullptr
    Pet* GetGhoulPet(Player* dk)
    {
        Pet* pet = dk->GetPet();
        return pet && pet->IsAlive() && pet->GetEntry() == NPC_GHOUL ? pet : nullptr;
    }

    // Shadow Infusion is gained only by a Death Knight who knows Dark Transformation, with the ghoul out and not
    // transformed (no stacks build while transformed)
    bool CanGainShadowInfusion(Player* dk)
    {
        if (!dk->HasSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION))
            return false;

        Pet* ghoul = GetGhoulPet(dk);
        return ghoul && !ghoul->HasAura(DeathKnightData::SPELL_DARK_TRANSFORMATION);
    }

    // Engagement filter shared by every area spell here: only enemies already in combat with the Death Knight or the
    // group are hit, so none of them ever pulls an idle pack.
    void KeepEngagedEnemies(Player* owner, std::list<WorldObject*>& targets)
    {
        targets.remove_if([owner](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !unit->IsAlive() || !Engagement::IsEngagedWithOwnerOrGroup(unit, owner);
        });
    }

    // Owner of a damage spell cast either by the Death Knight or by one of his minions
    Player* ResolveOwner(Unit* caster)
    {
        if (Player* player = GetPlayerCaster(caster))
            return player;

        return DeathKnight::GetMinionOwner(caster);
    }

    // Minion terms a corpse Corpse Explosion applies itself (the Death Knight casts it, so the minion damage seam
    // never sees it): Dread Host, All Will Serve and the Gargoyle's Necromancy stacks. The Death Knight's own
    // percent-done auras (Desolation) already ride a player cast.
    float GetCorpseExplosionMinionTerms(Player* dk)
    {
        float multiplier = (1.0f + float(DeathKnight::GetDreadHostPct(dk)) / 100.0f) *
            (1.0f + float(DeathKnight::GetAllWillServePct(dk)) / 100.0f);
        if (Aura const* necromancy = dk->GetAura(DeathKnightData::SPELL_GARGOYLE_NECROMANCY))
            multiplier *= 1.0f +
                float(DeathKnightData::GARGOYLE_NECROMANCY_PCT * necromancy->GetStackAmount()) / 100.0f;

        return multiplier;
    }

    // Dead creature to explode when no Lesser Ghoul is up: the stock corpse test (a corpse still wearing its own
    // look) without the mechanical / elemental exclusion.
    Creature* FindCorpse(Player* dk)
    {
        float const range = float(DeathKnightData::CORPSE_EXPLOSION_CORPSE_RANGE_YARDS);
        std::list<Unit*> dead;
        Acore::AllDeadCreaturesInRange check(dk, range);
        Acore::UnitListSearcher<Acore::AllDeadCreaturesInRange> searcher(dk, dead, check);
        Cell::VisitObjects(dk, searcher, range);

        Creature* best = nullptr;
        float bestDist = 0.0f;
        for (Unit* unit : dead)
        {
            Creature* corpse = unit->ToCreature();
            if (!corpse || corpse->IsAlive() || corpse->IsPet() || corpse->IsSummon() ||
                corpse->GetDisplayId() != corpse->GetNativeDisplayId())
                continue;

            // the detonation is a dest cast: it fails silently without line of sight to the corpse
            if (!dk->IsWithinLOSInMap(corpse))
                continue;

            float const dist = dk->GetDistance(corpse);
            if (!best || dist < bestDist)
            {
                best = corpse;
                bestDist = dist;
            }
        }

        return best;
    }
}

// -55090 - Scourge Strike. OnCast snapshots the runes (before TakePower). EFFECT_2 counts the Death Knight's own
// diseases. AfterHit (a real hit only) casts the Shadow part (stock shape, the Shadowmourne hack included) and bursts
// max(WOUND_BURST_MIN, stacks / 2) wounds, never more than the stack. AfterCast: Necromancy with energy spends one
// Necromantic Energy for a Lesser Ghoul and extra Runic Power (no Death Runes); Necromancy without energy does
// nothing extra; otherwise each plain rune the cast spent rolls (33 + Reaping)% x Proc Chance to return as a ready
// Death Rune.
class spell_dk_scourge_strike_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_scourge_strike_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_SCOURGE_STRIKE_SHADOW, SPELL_SHADOWMOURNE_CHAOS_BANE_DAMAGE,
            SPELL_SHADOWMOURNE_SOUL_FRAGMENT, DeathKnightData::SPELL_UNHOLY_RP_ENERGIZE,
            DeathKnightData::SPELL_BLOOD_PLAGUE, DeathKnightData::SPELL_FROST_FEVER });
    }

    bool Load() override
    {
        _multiplier = 0.0f;
        _target.Clear();
        _snapshotted = false;
        return true;
    }

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        // a triggered cast that skips the cost spends no runes: nothing to roll for
        if (!dk || GetSpell()->HasTriggeredCastFlag(TRIGGERED_IGNORE_POWER_AND_REAGENT_COST))
            return;

        DeathKnight::SnapshotRunes(dk, GetSpellInfo()->Id);
        _snapshotted = true;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        float percent = float(GetEffectValue());
        // Death Knight T8 Melee 4P Bonus
        if (AuraEffect const* t8 = dk->GetAuraEffect(SPELL_ITEM_T8_MELEE_4P_BONUS, EFFECT_0))
            AddPct(percent, t8->GetAmount());

        _multiplier = percent * float(CountOwnDiseases(target, dk->GetGUID())) / 100.0f;
        _target = target->GetGUID();
    }

    void HandleAfterHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target || target->GetGUID() != _target)
            return;

        int32 const bp = int32(float(GetHitDamage()) * _multiplier);
        if (bp > 0)
            dk->CastCustomSpell(target, SPELL_SCOURGE_STRIKE_SHADOW, &bp, nullptr, nullptr, true);

        // Shadowmourne hack (stock): the strike's trigger proc is disabled, so the soul fragment is granted here
        if (roll_chance_i(SHADOWMOURNE_FRAGMENT_CHANCE_PCT) && dk->FindMap() &&
            !dk->FindMap()->IsBattlegroundOrArena() && dk->HasAura(SPELL_SHADOWMOURNE) &&
            !dk->HasAura(SPELL_SHADOWMOURNE_CHAOS_BANE_BUFF))
        {
            dk->CastSpell(dk, SPELL_SHADOWMOURNE_SOUL_FRAGMENT, true);

            // this can't be handled in the soul fragment's AuraScript because the victim is needed
            if (Aura* fragments = dk->GetAura(SPELL_SHADOWMOURNE_SOUL_FRAGMENT))
                if (fragments->GetStackAmount() >= SHADOWMOURNE_FRAGMENTS_FOR_CHAOS_BANE)
                {
                    dk->CastSpell(dk, SPELL_SHADOWMOURNE_CHAOS_BANE_DAMAGE, true, nullptr);
                    fragments->Remove();
                }
        }

        if (!target->IsAlive())
            return;

        uint8 const stacks = DeathKnight::GetFesteringWounds(target, dk->GetGUID());
        if (stacks == 0)
            return;

        int32 const half = std::max<int32>(DeathKnightData::WOUND_BURST_MIN, stacks / 2);
        uint8 const burst = uint8(std::min<int32>(stacks, half));
        DeathKnight::BurstFesteringWounds(dk, target, burst, DeathKnight::WoundSource::ScourgeStrike);
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        // a dodged / parried / missed strike neither spends Necromantic Energy nor returns runes (a miss still puts
        // the paid runes on the short miss cooldown, which the rune diff would count as spent)
        bool hit = false;
        for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
            if (info.missCondition == SPELL_MISS_NONE)
            {
                hit = true;
                break;
            }

        if (!hit)
            return;

        if (DeathKnight::HasNecromancy(dk))
        {
            if (!DeathKnight::ConsumeNecromanticEnergy(dk))
                return;

            // the target may have died to this very strike: the summon is cast at its position
            if (Unit* target = GetExplTargetUnit())
                DeathKnight::SummonLesserGhoul(dk, target);

            dk->CastCustomSpell(DeathKnightData::SPELL_UNHOLY_RP_ENERGIZE, SPELLVALUE_BASE_POINT0,
                DeathKnightData::NECROMANCY_RP * 10, dk, TRIGGERED_FULL_MASK);
            return;
        }

        if (!_snapshotted)
            return;

        uint8 slots[6];
        uint8 const spent = DeathKnight::GetSpentPlainRuneSlots(dk, GetSpellInfo()->Id, slots);
        float const chance = std::min(100.0f, float(DeathKnightData::SCOURGE_STRIKE_DEATH_RUNE_PCT +
            GetReapingPct(dk)) * GetProcChanceFactor(dk));
        for (uint8 i = 0; i < spent; ++i)
            if (roll_chance_f(chance))
                DeathKnight::ConvertToDeathRune(dk, slots[i], true);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_scourge_strike_rework::HandleCast);
        OnEffectHitTarget += SpellEffectFn(spell_dk_scourge_strike_rework::HandleDummy, EFFECT_2, SPELL_EFFECT_DUMMY);
        AfterHit += SpellHitFn(spell_dk_scourge_strike_rework::HandleAfterHit);
        AfterCast += SpellCastFn(spell_dk_scourge_strike_rework::HandleAfterCast);
    }

private:
    float _multiplier = 0.0f;
    ObjectGuid _target;
    bool _snapshotted = false;
};

// 45462 - Plague Strike, the Unholy rules (Frost's class on the same id is untouched). Only a Death Knight with
// Necromancy or Festering Plague is affected.
//  - Necromancy: +NECROMANTIC_ENERGY_PER_STRIKE energy per cast (a miss included), the plain rune the strike spent
//    returns as a ready Death Rune (100%), no wounds, and no Rotten Touch (the proc row grants it before AfterCast).
//  - Festering Plague: one Festering Wound, plus one exclusive roll (+2 under 5% x Proc Chance, else +1 under another
//    25% x Proc Chance) and +1 for a critical hit. Nothing on a miss.
class spell_dk_plague_strike_unholy : public SpellScript
{
    PrepareSpellScript(spell_dk_plague_strike_unholy);

    bool Load() override
    {
        _snapshotted = false;
        return true;
    }

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk || !DeathKnight::HasNecromancy(dk) ||
            GetSpell()->HasTriggeredCastFlag(TRIGGERED_IGNORE_POWER_AND_REAGENT_COST))
            return;

        DeathKnight::SnapshotRunes(dk, GetSpellInfo()->Id);
        _snapshotted = true;
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        if (DeathKnight::HasNecromancy(dk))
        {
            DeathKnight::GrantNecromanticEnergy(dk);
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_ROTTEN_TOUCH_BUFF);
            // a missed strike puts the paid rune on the short miss cooldown, which the rune diff would count as
            // spent: only a real hit returns a ready Death Rune (the energy above is per cast, a miss included)
            bool hit = false;
            for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
                if (info.missCondition == SPELL_MISS_NONE)
                {
                    hit = true;
                    break;
                }

            if (_snapshotted && hit)
            {
                uint8 slots[6];
                uint8 const spent = DeathKnight::GetSpentPlainRuneSlots(dk, GetSpellInfo()->Id, slots);
                for (uint8 i = 0; i < spent; ++i)
                    DeathKnight::ConvertToDeathRune(dk, slots[i], true);
            }

            return;
        }

        if (!dk->HasAura(DeathKnightData::SPELL_FESTERING_PLAGUE))
            return;

        for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
        {
            if (info.missCondition != SPELL_MISS_NONE)
                continue;

            Unit* target = ObjectAccessor::GetUnit(*dk, info.targetGUID);
            if (!target || !target->IsAlive())
                continue;

            float const factor = GetProcChanceFactor(dk);
            float const roll = rand_chance();
            uint8 wounds = 1;
            if (roll < float(DeathKnightData::FESTERING_PLAGUE_PLUS2_PCT) * factor)
                wounds += 2;
            else if (roll < float(DeathKnightData::FESTERING_PLAGUE_PLUS2_PCT +
                DeathKnightData::FESTERING_PLAGUE_PLUS1_PCT) * factor)
                wounds += 1;

            if (info.crit)
                wounds += 1;

            DeathKnight::AddFesteringWounds(dk, target, wounds, DeathKnight::WoundSource::PlagueStrikeOverflow);
            break;
        }
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_plague_strike_unholy::HandleCast);
        AfterCast += SpellCastFn(spell_dk_plague_strike_unholy::HandleAfterCast);
    }

private:
    bool _snapshotted = false;
};

// 47541 - Death Coil, the Unholy riders (the stock dummy script stays and launches 47632 / 47633). AfterCast:
// Shadow Infusion for a Coil at an enemy or at the ghoul; a ready Rotten Touch is spent on a Coil at an enemy and the
// target recorded for the missile (spell_dk_death_coil_damage_unholy bursts on its hit).
class spell_dk_death_coil_unholy : public SpellScript
{
    PrepareSpellScript(spell_dk_death_coil_unholy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DARK_TRANSFORMATION,
            DeathKnightData::SPELL_ROTTEN_TOUCH_BUFF });
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetExplTargetUnit();
        if (!dk || !target)
            return;

        bool const enemy = !dk->IsFriendlyTo(target);
        if ((enemy || target == dk->GetPet()) && CanGainShadowInfusion(dk))
            DeathKnight::AddShadowInfusion(dk);

        if (enemy && dk->HasAura(DeathKnightData::SPELL_ROTTEN_TOUCH_BUFF))
        {
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_ROTTEN_TOUCH_BUFF);
            DeathKnight::RecordRottenTouchTarget(dk, target->GetGUID());
        }
        // An unarmed Coil leaves the record alone: the armed missile may still be in flight. A stale record expires
        // with the helper's window or is cleared by the damage script's BeforeHit on a miss.
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dk_death_coil_unholy::HandleAfterCast);
    }
};

// 47632 - Death Coil damage (the missile). Cast by initiates and Dancing Rune Weapon too: a player caster only. On a
// real hit: Morbidity's capstone recasts each of the Death Knight's diseases already on the target at full duration
// (never a missing one); Rotten Touch bursts 2 wounds if this is the target the armed Coil was cast at.
class spell_dk_death_coil_damage_unholy : public SpellScript
{
    PrepareSpellScript(spell_dk_death_coil_damage_unholy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_MORBIDITY_49565, DeathKnightData::SPELL_BLOOD_PLAGUE,
            DeathKnightData::SPELL_FROST_FEVER });
    }

    // a missile that misses or is resisted, evaded or immuned drops the armed record: it must never outlive its Coil
    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        if (missInfo == SPELL_MISS_NONE)
            return;

        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (dk && target)
            DeathKnight::ConsumeRottenTouchTarget(dk, target->GetGUID());
    }

    void HandleAfterHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target || !target->IsAlive() || dk->IsFriendlyTo(target))
            return;

        if (dk->HasAura(DeathKnightData::SPELL_MORBIDITY_49565))
            for (uint32 const disease : { DeathKnightData::SPELL_BLOOD_PLAGUE, DeathKnightData::SPELL_FROST_FEVER })
                if (target->HasAura(disease, dk->GetGUID()))
                    dk->CastSpell(target, disease, true);

        if (DeathKnight::ConsumeRottenTouchTarget(dk, target->GetGUID()))
        {
            uint8 const stacks = DeathKnight::GetFesteringWounds(target, dk->GetGUID());
            if (stacks > 0)
                DeathKnight::BurstFesteringWounds(dk, target, std::min<uint8>(stacks, 2),
                    DeathKnight::WoundSource::RottenTouch);
        }
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_dk_death_coil_damage_unholy::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_dk_death_coil_damage_unholy::HandleAfterHit);
    }
};

// -203445 - Doomed Bidding. A cast-phase proc on Death Coil (chance native, once per cast): raises a Lesser Ghoul at
// the Coil's target, an enemy or the ghoul.
class spell_dk_doomed_bidding : public AuraScript
{
    PrepareAuraScript(spell_dk_doomed_bidding);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        return dk && eventInfo.GetActor() == dk && eventInfo.GetProcSpell();
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        Spell const* spell = eventInfo.GetProcSpell();
        Unit* target = spell ? spell->m_targets.GetUnitTarget() : nullptr;
        if (dk && target)
            DeathKnight::SummonLesserGhoul(dk, target);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_doomed_bidding::CheckProc);
        OnProc += AuraProcFn(spell_dk_doomed_bidding::HandleProc);
    }
};

// 55078 Blood Plague, 55095 Frost Fever - Dread Host. The diseases' per-tick amount is raised by Dread Host once, at
// apply and at every refresh (the amount is the snapshot; never per tick). A non-player caster (the spawn auras, the
// rune weapon) keeps its amount.
class spell_dk_dread_host_disease : public AuraScript
{
    PrepareAuraScript(spell_dk_dread_host_disease);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        int32 const pct = DeathKnight::GetDreadHostPct(dk);
        if (pct > 0)
            amount = int32(float(amount) * (1.0f + float(pct) / 100.0f));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_dread_host_disease::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// 203456 - Festering Wound. Only a removal by DEATH explodes the stack (a burst down to 0 removes by DEFAULT, the
// timeout by EXPIRE): the helper defers the cast with the map, instance and corpse position captured.
class spell_dk_festering_wound : public AuraScript
{
    PrepareAuraScript(spell_dk_festering_wound);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* application = GetTargetApplication();
        if (!application || application->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        Player* dk = GetPlayerCaster(GetCaster());
        Unit* corpse = GetTarget();
        if (!dk || !corpse || !dk->IsInWorld() || dk->GetMap() != corpse->GetMap())
            return;

        DeathKnight::ScheduleWoundExplosion(dk, corpse, GetStackAmount());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_festering_wound::HandleRemove, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203457 burst, 203458 overflow, 203459 death explosion, 203043 Rune of Boiling Blight burst - one cast carries the
// wound count n in its second effect (the Boiling Blight burst is one wound). OnHit multiplies the whole damage by
// n x (1 + Dread Host%) before the crit roll, so the AP term is counted per wound. The explosion keeps only enemies
// in combat with the Death Knight or the group, the nearest WOUND_EXPLOSION_TARGETS of them. The burst's AfterHit
// feeds the Runic Power and Wandering Plague rules (the mechanics helper decides by the source it recorded).
class spell_dk_festering_wound_damage : public SpellScript
{
    PrepareSpellScript(spell_dk_festering_wound_damage);

    void FilterExplosionTargets(std::list<WorldObject*>& targets)
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        KeepEngagedEnemies(dk, targets);
        WorldLocation const* dest = GetExplTargetDest();
        Position const center = dest ? Position(*dest) : dk->GetPosition();
        targets.sort([&center](WorldObject* a, WorldObject* b)
        {
            return a->GetExactDistSq(center) < b->GetExactDistSq(center);
        });

        if (targets.size() > size_t(DeathKnightData::WOUND_EXPLOSION_TARGETS))
            targets.resize(size_t(DeathKnightData::WOUND_EXPLOSION_TARGETS));
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        int32 wounds = 1;
        if (GetSpellInfo()->Id != DeathKnightData::SPELL_BOILING_BLIGHT)
            wounds = std::max(1, GetSpell()->CalculateSpellDamage(EFFECT_1, target));

        float const multiplier = float(wounds) * (1.0f + float(DeathKnight::GetDreadHostPct(dk)) / 100.0f);
        SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void HandleAfterHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        int32 const wounds = std::max(1, GetSpell()->CalculateSpellDamage(EFFECT_1, target));
        // the helper that cast the burst / overflow knows its source; Pestilence is the no-resources fallback
        DeathKnight::OnWoundBurstHit(dk, target, uint32(std::max(0, GetHitDamage())),
            DeathKnight::WoundSource::Pestilence,
            uint8(std::min(wounds, int32(DeathKnightData::FESTERING_WOUND_MAX_STACKS))));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dk_festering_wound_damage::HandleHit);
        if (m_scriptSpellId == DeathKnightData::SPELL_FESTERING_WOUND_BURST ||
            m_scriptSpellId == DeathKnightData::SPELL_FESTERING_WOUND_OVERFLOW)
            AfterHit += SpellHitFn(spell_dk_festering_wound_damage::HandleAfterHit);
        if (m_scriptSpellId == DeathKnightData::SPELL_FESTERING_WOUND_EXPLOSION)
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(
                spell_dk_festering_wound_damage::FilterExplosionTargets, EFFECT_ALL, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 50526 - Wandering Plague (the stock crowd-control filter stays on -50526's first script). The splash only reaches
// enemies already in combat with the Death Knight or the group.
class spell_dk_wandering_plague_engaged : public SpellScript
{
    PrepareSpellScript(spell_dk_wandering_plague_engaged);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* dk = GetPlayerCaster(GetCaster()))
            KeepEngagedEnemies(dk, targets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_wandering_plague_engaged::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 50508 Crypt Fever (first effect, the linked disease-damage amount), 51726 Ebon Plague (second effect, the magic
// damage taken, after SpellInfoCorrections turned it into MOD_DAMAGE_PERCENT_TAKEN): the amount is the caster's talent
// rank value. Registered per spell id so no handler is bound to an effect the other row doesn't have.
class spell_dk_crypt_fever_amount : public AuraScript
{
    PrepareAuraScript(spell_dk_crypt_fever_amount);

    void CalcCryptFever(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Player* dk = GetPlayerCaster(GetCaster()))
            if (int32 const pct = DeathKnight::GetCryptFeverPct(dk))
                amount = pct;
    }

    void CalcEbonPlague(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Player* dk = GetPlayerCaster(GetCaster()))
            if (int32 const pct = DeathKnight::GetEbonPlagueMagicPct(dk))
                amount = pct;
    }

    void Register() override
    {
        if (m_scriptSpellId == DeathKnightData::SPELL_CRYPT_FEVER_50508)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_crypt_fever_amount::CalcCryptFever, EFFECT_0,
                SPELL_AURA_LINKED);
        if (m_scriptSpellId == DeathKnightData::SPELL_EBON_PLAGUE)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_crypt_fever_amount::CalcEbonPlague, EFFECT_1,
                SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// 49194 - Unholy Blight. On the stock proc (Death Coil damage) the Coil's damage x UNHOLY_BLIGHT_SHARE_PCT% is spread
// over the new DoT's HASTED tick count and rolled into any DoT already running (the carry-over of
// CastDelayedSpellWithPeriodicAmount). The stock script divides by the unhasted count.
class spell_dk_unholy_blight_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_unholy_blight_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_UNHOLY_BLIGHT_DOT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        return damageInfo && damageInfo->GetDamage();
    }

    // Ticks the DoT will have on this caster: the periodic timer is the amplitude after activation-time mods and the
    // caster's spell haste (AuraEffect::CalculatePeriodic)
    static int32 GetHastedTickCount(Unit* caster, SpellInfo const* dot)
    {
        float amplitude = float(dot->Effects[EFFECT_0].Amplitude > 0 ? dot->Effects[EFFECT_0].Amplitude : 1000);
        if (Player* modOwner = caster->GetSpellModOwner())
            modOwner->ApplySpellMod(dot->Id, SPELLMOD_ACTIVATION_TIME, amplitude);

        int32 const period = std::max(1, int32(amplitude * caster->GetFloatValue(UNIT_MOD_CAST_SPEED)));
        return std::max(1, dot->GetMaxDuration() / period);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* caster = GetCaster();
        Unit* target = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!caster || !target || !damageInfo)
            return;

        SpellInfo const* dot = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_UNHOLY_BLIGHT_DOT);
        if (!dot)
            return;

        int32 const total = CalculatePct(int32(damageInfo->GetDamage()), DeathKnightData::UNHOLY_BLIGHT_SHARE_PCT);
        int32 const bp = total / GetHastedTickCount(caster, dot);
        if (bp > 0)
            target->CastDelayedSpellWithPeriodicAmount(caster, DeathKnightData::SPELL_UNHOLY_BLIGHT_DOT,
                SPELL_AURA_PERIODIC_DAMAGE, bp);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_unholy_blight_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_unholy_blight_rework::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -49158 - Corpse Explosion. No target: the Death Knight's Lesser Ghoul with the most time left within 40 yd detonates
// (the ghoul casts the detonation at itself and is destroyed there), else the nearest corpse within 30 yd (the Death
// Knight casts it at the corpse and the corpse is spent like the stock spell does), else the cast fails.
class spell_dk_corpse_explosion_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_corpse_explosion_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_CORPSE_EXPLOSION_DETONATION, SPELL_CORPSE_EXPLOSION_SUICIDE,
            SPELL_CORPSE_EXPLOSION_VISUAL });
    }

    bool Load() override
    {
        _ghoul.Clear();
        _corpse.Clear();
        return true;
    }

    SpellCastResult CheckCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return SPELL_CAST_OK;

        _ghoul.Clear();
        _corpse.Clear();
        if (Creature* ghoul = DeathKnight::FindCorpseExplosionGhoul(dk))
        {
            _ghoul = ghoul->GetGUID();
            return SPELL_CAST_OK;
        }

        if (Creature* corpse = FindCorpse(dk))
        {
            _corpse = corpse->GetGUID();
            return SPELL_CAST_OK;
        }

        return SPELL_FAILED_NO_VALID_TARGETS;
    }

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        if (Creature* ghoul = ObjectAccessor::GetCreature(*dk, _ghoul))
        {
            if (ghoul->IsAlive())
            {
                ghoul->StopMoving();
                ghoul->CastSpell(ghoul->GetPositionX(), ghoul->GetPositionY(), ghoul->GetPositionZ(),
                    DeathKnightData::SPELL_CORPSE_EXPLOSION_DETONATION, true);
            }

            return;
        }

        if (Creature* corpse = ObjectAccessor::GetCreature(*dk, _corpse))
        {
            dk->CastSpell(corpse->GetPositionX(), corpse->GetPositionY(), corpse->GetPositionZ(),
                DeathKnightData::SPELL_CORPSE_EXPLOSION_DETONATION, true);
            // spend the corpse (its look changes, so it can't be exploded again) and show the blast
            corpse->CastSpell(corpse, SPELL_CORPSE_EXPLOSION_SUICIDE, true);
            dk->CastSpell(corpse, SPELL_CORPSE_EXPLOSION_VISUAL, true);
        }
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dk_corpse_explosion_rework::CheckCast);
        OnCast += SpellCastFn(spell_dk_corpse_explosion_rework::HandleCast);
    }

private:
    ObjectGuid _ghoul;
    ObjectGuid _corpse;
};

// 203471 - Corpse Explosion detonation. Cast by the Lesser Ghoul at itself (damage scales with the time it has left,
// then the ghoul is destroyed) or by the Death Knight at a corpse (the minion terms are applied here: the seam only
// sees minion casters). Only enemies in combat with the Death Knight or the group are hit.
class spell_dk_corpse_explosion_detonation : public SpellScript
{
    PrepareSpellScript(spell_dk_corpse_explosion_detonation);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* owner = ResolveOwner(GetCaster()))
            KeepEngagedEnemies(owner, targets);
    }

    void HandleHit()
    {
        Unit* caster = GetCaster();
        float multiplier = 0.0f;
        if (Player* dk = GetPlayerCaster(caster))
            multiplier = GetCorpseExplosionMinionTerms(dk);
        else if (Creature* ghoul = caster->ToCreature();
            ghoul && ghoul->GetEntry() == DeathKnightData::NPC_LESSER_GHOUL)
            multiplier = DeathKnight::GetLesserGhoulRemainingFraction(ghoul);
        else
            return;

        SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        if (caster->GetEntry() != DeathKnightData::NPC_LESSER_GHOUL)
            return;

        if (TempSummon* ghoul = caster->ToTempSummon())
            ghoul->UnSummon();
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_corpse_explosion_detonation::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_DEST_AREA_ENEMY);
        OnHit += SpellHitFn(spell_dk_corpse_explosion_detonation::HandleHit);
        AfterCast += SpellCastFn(spell_dk_corpse_explosion_detonation::HandleAfterCast);
    }
};

// 203469 - Lesser Ghoul summon (dest-only: AfterHit never fires, so AfterCast). The new ghoul is already one of the
// Death Knight's controlled units: hand its lifetime to the mechanics layer, replace the oldest above the cap and
// refresh the counter buff.
class spell_dk_lesser_ghoul_summon : public SpellScript
{
    PrepareSpellScript(spell_dk_lesser_ghoul_summon);

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        std::list<Creature*> ghouls;
        dk->GetAllMinionsByEntry(ghouls, DeathKnightData::NPC_LESSER_GHOUL);
        for (Creature* ghoul : ghouls)
        {
            TempSummon* summon = ghoul->ToTempSummon();
            LesserGhoulMark* mark = ghoul->CustomData.GetDefault<LesserGhoulMark>(LESSER_GHOUL_MARK_KEY);
            if (!summon || mark->started)
                continue;

            mark->started = true;
            DeathKnight::StartLesserGhoulTimer(ghoul, summon->GetTimer());
        }

        DeathKnight::CapMinions(dk, DeathKnightData::NPC_LESSER_GHOUL, uint32(DeathKnightData::LESSER_GHOUL_CAP));
        DeathKnight::RefreshLesserGhoulCounter(dk);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dk_lesser_ghoul_summon::HandleAfterCast);
    }
};

// 203448 - Dark Transformation (spell half). Needs the permanent ghoul alive with SHADOW_INFUSION_STACKS stacks of
// Shadow Infusion; the cast spends them all. The marker (greys the button) is removed by the linked spell.
class spell_dk_dark_transformation : public SpellScript
{
    PrepareSpellScript(spell_dk_dark_transformation);

    SpellCastResult CheckCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return SPELL_CAST_OK;

        Pet* ghoul = GetGhoulPet(dk);
        if (!ghoul)
            return SPELL_FAILED_NO_PET;

        Aura const* infusion = ghoul->GetAura(DeathKnightData::SPELL_SHADOW_INFUSION);
        if (!infusion || infusion->GetStackAmount() < DeathKnightData::SHADOW_INFUSION_STACKS)
            return SPELL_FAILED_CANT_DO_THAT_RIGHT_NOW;

        return SPELL_CAST_OK;
    }

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        if (Pet* ghoul = GetGhoulPet(dk))
            ghoul->RemoveAurasDueToSpell(DeathKnightData::SPELL_SHADOW_INFUSION);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dk_dark_transformation::CheckCast);
        OnCast += SpellCastFn(spell_dk_dark_transformation::HandleCast);
    }
};

// 203448 - Dark Transformation (aura half, on the ghoul). A proc on the ghoul's melee hits and Claw: every other
// engaged enemy near the target takes DARK_TRANSFORMATION_CLEAVE_PCT% of the hit's unmitigated damage, cast by the
// ghoul (203466 is a triggered spell and never procs this again).
class spell_dk_dark_transformation_aura : public AuraScript
{
    PrepareAuraScript(spell_dk_dark_transformation_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DARK_TRANSFORMATION_CLEAVE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* ghoul = GetTarget();
        if (!ghoul || eventInfo.GetActor() != ghoul || !GetPlayerCaster(GetCaster()))
            return false;

        SpellInfo const* spell = eventInfo.GetSpellInfo();
        if (spell && spell->Id != SPELL_GHOUL_CLAW)
            return false;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        return eventInfo.GetActionTarget() && damageInfo && damageInfo->GetUnmitigatedDamage();
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* ghoul = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!ghoul || !victim || !damageInfo)
            return;

        int32 const bp = CalculatePct(int32(damageInfo->GetUnmitigatedDamage()),
            DeathKnightData::DARK_TRANSFORMATION_CLEAVE_PCT);
        if (bp > 0)
            ghoul->CastCustomSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION_CLEAVE, SPELLVALUE_BASE_POINT0, bp,
                victim, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_dark_transformation_aura::CheckProc);
        OnProc += AuraProcFn(spell_dk_dark_transformation_aura::HandleProc);
    }
};

// 203466 - Dark Transformation cleave (cast by the ghoul at the struck enemy). Hits the other enemies in combat with
// the Death Knight or the group, never the enemy that was struck.
class spell_dk_dark_transformation_cleave : public SpellScript
{
    PrepareSpellScript(spell_dk_dark_transformation_cleave);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Player* owner = ResolveOwner(GetCaster());
        if (!owner)
            return;

        KeepEngagedEnemies(owner, targets);
        if (Unit* primary = GetExplTargetUnit())
            targets.remove(primary);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_dark_transformation_cleave::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 203464 - Shadow Infusion (on the ghoul). The Death Knight's Dark Transformation marker follows the stack count:
// lit at full stacks, cleared below it and when the aura goes.
class spell_dk_shadow_infusion : public AuraScript
{
    PrepareAuraScript(spell_dk_shadow_infusion);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* ghoul = GetTarget())
            DeathKnight::OnShadowInfusionChanged(ghoul, GetStackAmount());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* ghoul = GetTarget())
            DeathKnight::OnShadowInfusionChanged(ghoul, 0);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_shadow_infusion::HandleApply, EFFECT_FIRST_FOUND, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_shadow_infusion::HandleRemove, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203467 - Infected Claws (hidden, cast onto the ghoul by its owner so the owner's Proc Chance applies). Fires on the
// ghoul's Claw: rank% x Proc Chance, rolled once per Claw. Effect: a Festering Wound on the target; under Necromancy
// one Shadow Infusion instead (none while transformed).
class spell_dk_infected_claws_pet : public AuraScript
{
    PrepareAuraScript(spell_dk_infected_claws_pet);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* ghoul = GetTarget();
        Player* dk = GetPlayerCaster(GetCaster());
        if (!ghoul || !dk || eventInfo.GetActor() != ghoul)
            return false;

        SpellInfo const* spell = eventInfo.GetSpellInfo();
        Unit* victim = eventInfo.GetActionTarget();
        if (!spell || spell->Id != SPELL_GHOUL_CLAW || !victim || !victim->IsAlive())
            return false;

        int32 const rank = GetRankAmount(dk, { DeathKnightData::SPELL_INFECTED_CLAWS_203444,
            DeathKnightData::SPELL_INFECTED_CLAWS });
        return rank > 0 && roll_chance_f(std::min(100.0f, float(rank) * GetProcChanceFactor(dk)));
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* ghoul = GetTarget();
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* victim = eventInfo.GetActionTarget();
        if (!ghoul || !dk || !victim)
            return;

        if (DeathKnight::HasNecromancy(dk))
        {
            if (!ghoul->HasAura(DeathKnightData::SPELL_DARK_TRANSFORMATION))
                DeathKnight::AddShadowInfusion(dk);
        }
        else
            DeathKnight::AddFesteringWounds(dk, victim, 1, DeathKnight::WoundSource::InfectedClaws);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_infected_claws_pet::CheckProc);
        OnProc += AuraProcFn(spell_dk_infected_claws_pet::HandleProc);
    }
};

// 203472 - Putrid Cloud (on the Abomination). Every second each enemy in combat with the Death Knight or the group
// within 8 yd takes a tick cast by the Abomination; every ABOMINATION_WOUND_EVERY_TICKS-th tick on the same enemy adds
// a Festering Wound (none under Necromancy).
class spell_dk_putrid_cloud : public AuraScript
{
    PrepareAuraScript(spell_dk_putrid_cloud);

    static constexpr float CLOUD_RADIUS_YARDS = 8.0f;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_PUTRID_CLOUD_TICK });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* abomination = GetTarget();
        Player* owner = abomination ? DeathKnight::GetMinionOwner(abomination) : nullptr;
        if (!owner || !abomination->IsAlive())
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(abomination, abomination, CLOUD_RADIUS_YARDS);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(abomination, nearby, check);
        Cell::VisitObjects(abomination, searcher, CLOUD_RADIUS_YARDS);

        bool const necromancy = DeathKnight::HasNecromancy(owner);
        for (Unit* enemy : nearby)
        {
            if (!enemy->IsAlive() || !Engagement::IsEngagedWithOwnerOrGroup(enemy, owner) ||
                !abomination->IsWithinLOSInMap(enemy))
                continue;

            abomination->CastSpell(enemy, DeathKnightData::SPELL_PUTRID_CLOUD_TICK, TRIGGERED_FULL_MASK);
            uint32& ticks = _ticks[enemy->GetGUID()];
            ++ticks;
            if (ticks % uint32(DeathKnightData::ABOMINATION_WOUND_EVERY_TICKS) == 0 && !necromancy &&
                enemy->IsAlive())
                DeathKnight::AddFesteringWounds(owner, enemy, 1, DeathKnight::WoundSource::Abomination);
        }
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_putrid_cloud::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }

private:
    std::unordered_map<ObjectGuid, uint32> _ticks;
};

// 51963 - Gargoyle Strike (cast by the Gargoyle, bound over the stock level-scaling script). A hit gives the owner a
// wound on the target, or a Gargoyle Necromancy stack under Necromancy (the helper decides).
class spell_dk_gargoyle_strike_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_gargoyle_strike_rework);

    void HandleAfterHit()
    {
        Unit* target = GetHitUnit();
        Player* owner = DeathKnight::GetMinionOwner(GetCaster());
        if (owner && target && target->IsAlive())
            DeathKnight::OnGargoyleStrikeHit(owner, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dk_gargoyle_strike_rework::HandleAfterHit);
    }
};

void AddSC_deathknight_unholy_spell_scripts()
{
    RegisterSpellScript(spell_dk_scourge_strike_rework);
    RegisterSpellScript(spell_dk_plague_strike_unholy);
    RegisterSpellScript(spell_dk_death_coil_unholy);
    RegisterSpellScript(spell_dk_death_coil_damage_unholy);
    RegisterSpellScript(spell_dk_doomed_bidding);
    RegisterSpellScript(spell_dk_dread_host_disease);
    RegisterSpellScript(spell_dk_festering_wound);
    RegisterSpellScript(spell_dk_festering_wound_damage);
    RegisterSpellScript(spell_dk_wandering_plague_engaged);
    RegisterSpellScript(spell_dk_crypt_fever_amount);
    RegisterSpellScript(spell_dk_unholy_blight_rework);
    RegisterSpellScript(spell_dk_corpse_explosion_rework);
    RegisterSpellScript(spell_dk_corpse_explosion_detonation);
    RegisterSpellScript(spell_dk_lesser_ghoul_summon);
    RegisterSpellAndAuraScriptPair(spell_dk_dark_transformation, spell_dk_dark_transformation_aura);
    RegisterSpellScript(spell_dk_dark_transformation_cleave);
    RegisterSpellScript(spell_dk_shadow_infusion);
    RegisterSpellScript(spell_dk_infected_claws_pet);
    RegisterSpellScript(spell_dk_putrid_cloud);
    RegisterSpellScript(spell_dk_gargoyle_strike_rework);
}
