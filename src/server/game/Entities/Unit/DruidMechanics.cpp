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

#include "DruidMechanics.h"

/*
 * WP-B bodies (.agents/plans/druid-rework/druid-rework.PLAN.md §5.1,
 * druid-rework.BALANCE.md §7/§10, corrections in the WP-B brief). Call sites: the one Unit.cpp
 * line (CORE-AUDIT row 1) for ApplyDoneDamagePctMods, and script call sites in
 * spell_druid_balance.cpp for everything else.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "DataMap.h"
#include "Duration.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include "Util.h"
#include <algorithm>
#include <array>
#include <list>
#include <memory>
#include <unordered_set>
#include <vector>

namespace Druid
{
    namespace
    {
        // Improved Insect Swarm's icon (talent table 4,2: "Icon -> 1790, so it no longer
        // duplicates Insect Swarm's 1771") - its eff2 (EFFECT_1) stays a plain SPELL_AURA_DUMMY
        // value (BALANCE.md corrections item 1: "WP-A declares it as a plain value with no
        // SpellMod effect type on that slot"), so the conditional bonus is read live off that
        // value via the icon, not a spell id constant.
        constexpr uint32 ICON_IMPROVED_INSECT_SWARM = 1790;
    }

    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto,
                                 DamageEffectType /*damagetype*/, float& doneTotalMod)
    {
        Player* player = caster->ToPlayer();
        if (!player)
            return;

        // Improved Insect Swarm's conditional bonus (BALANCE.md corrections item 1 - the
        // additive-bucket design in §8 is dropped per PLAN A2; this is an ordinary multiplicative
        // clause instead). x(1 + eff2%) when the victim carries the caster's Insect Swarm
        // (original or the Swarming Rot copy) for a Wrath cast, or the caster's Moonfire for a
        // Starfire/cleave cast.
        if (victim)
        {
            bool const isWrath = spellProto->Id == SPELL_WRATH;
            bool const isStarfire = spellProto->Id == SPELL_STARFIRE || spellProto->Id == SPELL_STARFIRE_CLEAVE;

            if (isWrath || isStarfire)
            {
                bool hasDot = isWrath
                    ? (victim->HasAura(SPELL_INSECT_SWARM, player->GetGUID())
                       || victim->HasAura(SPELL_INSECT_SWARM_COPY, player->GetGUID()))
                    : victim->HasAura(SPELL_MOONFIRE, player->GetGUID());

                if (hasDot)
                {
                    if (AuraEffect const* iis = player->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_DRUID,
                                                                       ICON_IMPROVED_INSECT_SWARM, EFFECT_1))
                        AddPct(doneTotalMod, iis->GetAmount());
                }
            }
        }

        // Resto pass addition (WP-B brief "Critical corrections" #6): Omen of Clarity's r3 capstone
        // damage-side +10% - the healing-side clause lives in GetDirectHealMultiplier below; this is
        // the one sanctioned extension to Balance's existing function body (its Unit.cpp call site
        // already exists from the Balance pass, so this is 0 new core lines). Placed before the
        // nature/arcane early-out below so it isn't school-gated - Omen of Clarity is a Resto talent
        // whose consumer can be any damaging spell or offensive ability.
        if (ConsumedEmpoweredClearcasting(player))
            if (AuraEffect const* capstone = player->GetAuraEffect(SPELL_CLEARCASTING_OMEN_CAPSTONE, EFFECT_1))
                AddPct(doneTotalMod, float(capstone->GetAmount()));

        // Eclipse / Celestial Alignment / Eclipse Mastery - BALANCE.md §7 "Eclipse" (§0.13's
        // AddPct correction already folded into the Mastery step below).
        SpellSchoolMask const schoolMask = spellProto->GetSchoolMask();
        bool const nature = (schoolMask & SPELL_SCHOOL_MASK_NATURE) != 0;
        bool const arcane = (schoolMask & SPELL_SCHOOL_MASK_ARCANE) != 0;
        if (!nature && !arcane)
            return;

        AuraEffect const* solar = player->GetAuraEffect(SPELL_ECLIPSE_SOLAR, EFFECT_0);
        AuraEffect const* lunar = player->GetAuraEffect(SPELL_ECLIPSE_LUNAR, EFFECT_0);
        AuraEffect const* celestialAlignment = player->GetAuraEffect(SPELL_CELESTIAL_ALIGNMENT, EFFECT_0);

        float s = solar ? float(solar->GetAmount()) : 0.0f;
        float l = lunar ? float(lunar->GetAmount()) : 0.0f;

        if (celestialAlignment)
        {
            s = std::max(s, float(celestialAlignment->GetAmount()));
            l = std::max(l, float(celestialAlignment->GetAmount()));
        }

        // Mastery gate: only 3/3 Eclipse (48525) benefits, and only the side(s) currently active.
        float const mastery = player->HasAura(SPELL_ECLIPSE_R3) ? player->GetMasteryPercentage() : 0.0f;
        if (s > 0.0f)
            AddPct(s, mastery);
        if (l > 0.0f)
            AddPct(l, mastery);

        float pct = 0.0f;
        if (nature && arcane)
            pct = celestialAlignment ? (s + l) : std::max(s, l);
        else if (nature)
            pct = s;
        else if (arcane)
            pct = l;

        if (pct != 0.0f)
            AddPct(doneTotalMod, pct);
    }

    void ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms)
    {
        if (!player || !ms)
            return;

        // Feral pass adds the Barkskin (22812) 30 s floor clamp here (PLAN §3.9/CORE-AUDIT row
        // 34); no Balance caller ever reduces Barkskin's cooldown, so there is nothing to clamp
        // yet.

        // PLAN A8 (CORE-AUDIT row 36): ModifySpellCooldown() now resends the corrected cooldown
        // to the client itself (Player::ResendSpellCooldown), and is a safe no-op if spellId has
        // no tracked cooldown entry (e.g. Shooting Stars having just cleared Starsurge's).
        player->ModifySpellCooldown(spellId, -int32(ms));
    }

    void ApplyAstralSurge(Unit* caster)
    {
        // Moonfury r3 capstone (16899) - BALANCE.md §7 "Astral Surge (Moonfury capstone)".
        static constexpr std::array<uint32, 3> slots =
            { SPELL_ASTRAL_SURGE_1, SPELL_ASTRAL_SURGE_2, SPELL_ASTRAL_SURGE_3 };

        for (uint32 slot : slots)
        {
            if (!caster->HasAura(slot))
            {
                caster->CastSpell(caster, slot, true);
                return;
            }
        }

        // All three are up - refresh whichever has the lowest remaining duration (overwrite the
        // oldest slot rather than always refreshing the same one).
        Aura* oldest = nullptr;
        for (uint32 slot : slots)
        {
            if (Aura* aura = caster->GetAura(slot))
                if (!oldest || aura->GetDuration() < oldest->GetDuration())
                    oldest = aura;
        }

        if (oldest)
            oldest->RefreshDuration();
    }

    bool IsDirectDamageCast(SpellInfo const* spellInfo)
    {
        // BALANCE.md §7 "One roll per cast": true for a SPELL_EFFECT_SCHOOL_DAMAGE effect (Wrath,
        // Starfire, Moonfire's direct part n/a - Moonfire is a pure DoT so it never has this
        // effect -, Starsurge) or Typhoon (50516, whose damage sits on a triggered missile so it
        // has no SCHOOL_DAMAGE effect of its own). A pure DoT (Insect Swarm) or channel
        // (Hurricane) returns false.
        if (!spellInfo)
            return false;

        if (spellInfo->Id == SPELL_TYPHOON)
            return true;

        return spellInfo->HasEffect(SPELL_EFFECT_SCHOOL_DAMAGE);
    }

    /*
     * ---------------------------------------------------------------------------------------
     * Resto pass bodies (druid-rework.RESTO.md, druid-rework.CORE-AUDIT.md rows 11-21). Call
     * sites: spell_druid_resto.cpp and druid_hooks.cpp - this pass makes zero core-file edits
     * beyond the one sanctioned extension to ApplyDoneDamagePctMods above.
     * ---------------------------------------------------------------------------------------
     */

    bool IsCoreHot(SpellInfo const* spellInfo)
    {
        // RESTO §9's closed "core heal over time spell" list, plus Lifebloom's bloom (33778) for
        // Empowered Rejuvenation's Harmony only (its own capstone lists it - GetHarmonyCoefficient
        // handles that spell id in its direct-heal branch, not via this predicate).
        if (!spellInfo)
            return false;

        switch (spellInfo->Id)
        {
            case SPELL_REJUVENATION:
            case SPELL_GERMINATION:
            case SPELL_REGROWTH:
            case SPELL_LIFEBLOOM:
            case SPELL_WILD_GROWTH:
            case SPELL_CENARION_WARD_HEAL:
                return true;
            default:
                return false;
        }
    }

    void ForEachCasterHot(Unit const* caster, Unit* target, std::function<void(Aura*)> const& fn)
    {
        if (!caster || !target)
            return;

        ObjectGuid const casterGuid = caster->GetGUID();
        std::vector<Aura*> seen;

        for (AuraEffect const* effect : target->GetAuraEffectsByType(SPELL_AURA_PERIODIC_HEAL))
        {
            if (effect->GetCasterGUID() != casterGuid)
                continue;

            if (IsFixedCadencePeriodic(effect->GetSpellInfo()->Id))
                continue;

            Aura* aura = effect->GetBase();
            if (std::find(seen.begin(), seen.end(), aura) != seen.end())
                continue;

            seen.push_back(aura);
            fn(aura);
        }
    }

    uint32 CountHarmonyHots(Unit const* caster, Unit const* target)
    {
        // RESTO §4's table: every distinct Aura counts, including Cenarion Ward's released heal and
        // Cultivation, excluding the ward itself (DUMMY, not PERIODIC_HEAL), Tranquility (no target
        // aura) and Living Seed (DUMMY proc aura) - all automatically excluded by only scanning
        // SPELL_AURA_PERIODIC_HEAL effects.
        uint32 count = 0;
        ForEachCasterHot(caster, const_cast<Unit*>(target), [&count](Aura*) { ++count; });
        return count;
    }

    uint32 CountActiveRejuvenations(Player const* caster)
    {
        // RESTO §13 Q34: "group" is the party or raid plus the druid, counted by a scan over group
        // members rather than a global counter; a non-group target's Rejuvenation is never counted.
        if (!caster)
            return 0;

        uint32 count = 0;
        ObjectGuid const casterGuid = caster->GetGUID();

        auto countOn = [&count, casterGuid](Unit const* unit)
        {
            if (!unit)
                return;
            if (unit->HasAura(SPELL_REJUVENATION, casterGuid))
                ++count;
            if (unit->HasAura(SPELL_GERMINATION, casterGuid))
                ++count;
        };

        countOn(caster);

        if (Group* group = const_cast<Player*>(caster)->GetGroup())
        {
            for (Group::MemberSlot const& slot : group->GetMemberSlots())
            {
                if (slot.guid == casterGuid)
                    continue;

                if (Player* member = ObjectAccessor::FindPlayer(slot.guid))
                    if (member->IsInWorld() && member->GetMap() == caster->GetMap())
                        countOn(member);
            }
        }

        return count;
    }

    float GetHarmonyCoefficient(Unit const* caster, SpellInfo const* spellInfo, bool isPeriodic)
    {
        Player const* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !spellInfo)
            return 0.0f;

        uint32 const id = spellInfo->Id;

        // Naturalist (4,0): direct Nature heals - Healing Touch benefits at twice the rate.
        if (id == SPELL_HEALING_TOUCH)
            return player->HasAura(SPELL_NATURALIST_R3) ? 0.40f : 0.0f;

        if (id == SPELL_SWIFTMEND || id == SPELL_BLOOM || id == SPELL_BLOOM_JUMP)
            return player->HasAura(SPELL_NATURALIST_R3) ? 0.20f : 0.0f;

        // Improved Tranquility (4,3): Tranquility's per-target, per-tick direct heal cast (44203).
        if (id == SPELL_TRANQUILITY_TICK)
            return player->HasAura(SPELL_IMPROVED_TRANQUILITY_R2) ? 0.20f : 0.0f;

        // Empowered Rejuvenation (5,1): Lifebloom's bloom is direct but is explicitly listed by this
        // capstone, not Naturalist's.
        if (id == SPELL_LIFEBLOOM_BLOOM)
            return player->HasAura(SPELL_EMPOWERED_REJUVENATION_R3) ? 0.20f : 0.0f;

        // Regrowth serves both Naturalist (direct part) and Empowered Rejuvenation (periodic part).
        if (id == SPELL_REGROWTH)
        {
            if (isPeriodic)
                return player->HasAura(SPELL_EMPOWERED_REJUVENATION_R3) ? 0.20f : 0.0f;
            return player->HasAura(SPELL_NATURALIST_R3) ? 0.20f : 0.0f;
        }

        if (id == SPELL_REJUVENATION || id == SPELL_GERMINATION || id == SPELL_LIFEBLOOM ||
            id == SPELL_WILD_GROWTH || id == SPELL_CENARION_WARD_HEAL)
            return player->HasAura(SPELL_EMPOWERED_REJUVENATION_R3) ? 0.20f : 0.0f;

        return 0.0f;
    }

    int32 GetRankAmount(Unit const* caster, std::initializer_list<uint32> rankSpellIds, uint8 effIndex)
    {
        if (!caster)
            return 0;

        for (uint32 id : rankSpellIds)
            if (AuraEffect const* eff = caster->GetAuraEffect(id, effIndex))
                return eff->GetAmount();

        return 0;
    }

    float GetDirectHealMultiplier(Unit* caster, Unit* victim, SpellInfo const* spellProto, uint32 harmonyHotCount)
    {
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !spellProto)
            return 1.0f;

        float mult = 1.0f;

        // Harmony (RESTO §4).
        if (float k = GetHarmonyCoefficient(player, spellProto, false))
            mult *= 1.0f + float(harmonyHotCount) * k * player->GetMasteryPercentage() / 100.0f;

        uint32 const id = spellProto->Id;

        // Nature's Mending (1,0): Regrowth's direct part heals a target below 50% health for more -
        // the tick hook (ApplyPeriodicHealTickMods) covers Rejuvenation/Germination/Regrowth ticks.
        if (id == SPELL_REGROWTH && victim)
            if (int32 rank = GetRankAmount(player,
                    { SPELL_NATURES_MENDING_R3, SPELL_NATURES_MENDING_R2, SPELL_NATURES_MENDING_R1 }, EFFECT_0))
                if (victim->HealthBelowPct(50))
                    AddPct(mult, float(rank));

        // Waking Dream (Ysera's Gift r3 capstone): +8% per active Rejuvenation.
        if (id == SPELL_YSERAS_GIFT_HEAL && player->HasAura(SPELL_YSERAS_GIFT_R3))
            AddPct(mult, 8.0f * float(CountActiveRejuvenations(player)));

        // Omen of Clarity r3 capstone: +10% on the spell/ability that consumed 200572.
        if (ConsumedEmpoweredClearcasting(player))
            if (AuraEffect const* capstone = player->GetAuraEffect(SPELL_CLEARCASTING_OMEN_CAPSTONE, EFFECT_1))
                AddPct(mult, float(capstone->GetAmount()));

        return mult;
    }

    void ApplyPeriodicHealTickMods(Unit* caster, Unit* target, SpellInfo const* spellInfo, uint32& heal)
    {
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !target || !spellInfo || !IsCoreHot(spellInfo))
            return;

        float mult = 1.0f;

        if (float k = GetHarmonyCoefficient(player, spellInfo, true))
            mult *= 1.0f + float(CountHarmonyHots(player, target)) * k * player->GetMasteryPercentage() / 100.0f;

        // Nature's Mending (1,0): Rejuvenation/Germination/Regrowth ticks on a target below 50%
        // health heal for more.
        uint32 const id = spellInfo->Id;
        if (id == SPELL_REJUVENATION || id == SPELL_GERMINATION || id == SPELL_REGROWTH)
            if (int32 rank = GetRankAmount(player,
                    { SPELL_NATURES_MENDING_R3, SPELL_NATURES_MENDING_R2, SPELL_NATURES_MENDING_R1 }, EFFECT_0))
                if (target->HealthBelowPct(50))
                    AddPct(mult, float(rank));

        if (mult != 1.0f)
            heal = uint32(float(heal) * mult);
    }

    bool ConsumedEmpoweredClearcasting(Player const* caster)
    {
        if (!caster)
            return false;

        Spell* spell = caster->m_spellModTakingSpell;
        if (!spell)
            return false;

        Aura* clearcasting = caster->GetAura(SPELL_CLEARCASTING_OMEN_CAPSTONE);
        if (!clearcasting)
            return false;

        return spell->m_appliedMods.count(clearcasting) != 0;
    }

    void ApplyShapeshiftFormBonuses(Unit* target, ShapeshiftForm form)
    {
        Player* player = target ? target->ToPlayer() : nullptr;
        if (!player || player->getClass() != CLASS_DRUID)
            return;

        // Only one form context is ever active at a time - clear every hidden bonus first. This is
        // cheap (RemoveAurasDueToSpell on an absent aura is a no-op) and avoids stale bonuses when
        // shifting directly from one form to another.
        player->RemoveAurasDueToSpell(SPELL_NATURAL_SHAPESHIFTER_BEAR);
        player->RemoveAurasDueToSpell(SPELL_NATURAL_SHAPESHIFTER_CAT);
        player->RemoveAurasDueToSpell(SPELL_NATURAL_SHAPESHIFTER_MOONKIN);
        player->RemoveAurasDueToSpell(SPELL_NATURAL_SHAPESHIFTER_HEALING_BUFF);

        // eff1 (EFFECT_0): bear physical / moonkin Arcane+Nature %. eff2 (EFFECT_1): cat crit % and
        // (numerically identical per rank) no-form/Tree of Life healing %.
        int32 const physOrMagicPct = GetRankAmount(player,
            { SPELL_NATURAL_SHAPESHIFTER_R3, SPELL_NATURAL_SHAPESHIFTER_R2, SPELL_NATURAL_SHAPESHIFTER_R1 },
            EFFECT_0);
        int32 const critOrHealPct = GetRankAmount(player,
            { SPELL_NATURAL_SHAPESHIFTER_R3, SPELL_NATURAL_SHAPESHIFTER_R2, SPELL_NATURAL_SHAPESHIFTER_R1 },
            EFFECT_1);

        if (!physOrMagicPct && !critOrHealPct)
            return;

        switch (form)
        {
            case FORM_BEAR:
            case FORM_DIREBEAR:
                if (physOrMagicPct)
                    player->CastCustomSpell(SPELL_NATURAL_SHAPESHIFTER_BEAR, SPELLVALUE_BASE_POINT0,
                                             physOrMagicPct, player, true);
                break;
            case FORM_CAT:
                if (critOrHealPct)
                    player->CastCustomSpell(SPELL_NATURAL_SHAPESHIFTER_CAT, SPELLVALUE_BASE_POINT0,
                                             critOrHealPct, player, true);
                break;
            case FORM_MOONKIN:
                if (physOrMagicPct)
                    player->CastCustomSpell(SPELL_NATURAL_SHAPESHIFTER_MOONKIN, SPELLVALUE_BASE_POINT0,
                                             physOrMagicPct, player, true);
                break;
            case FORM_NONE:
            case FORM_TREE:
                if (critOrHealPct)
                {
                    CustomSpellValues values;
                    values.AddSpellMod(SPELLVALUE_BASE_POINT0, critOrHealPct);
                    values.AddSpellMod(SPELLVALUE_BASE_POINT1, critOrHealPct);
                    player->CastCustomSpell(SPELL_NATURAL_SHAPESHIFTER_HEALING_BUFF, values, player,
                                             TRIGGERED_FULL_MASK);
                }
                break;
            default:
                // Any other form (Cat/Bear/Travel/Aquatic/Flight/etc. not covered above) - no bonus.
                break;
        }
    }

    void TriggerLifebloomBloom(Unit* caster, Unit* target, Aura* lifebloom, bool /*forced*/)
    {
        // `forced` (Photosynthesis) needs no branch here: this rework never returns mana on any
        // bloom (natural or forced - RESTO §3 "Lifebloom ... No longer returns mana when it
        // blooms"), and this function never touches the Lifebloom aura's own stacks/duration either
        // way - the caller (AfterRemove for a natural bloom, the Photosynthesis capstone script for
        // a forced one) is solely responsible for that.
        if (!target || !lifebloom)
            return;

        AuraEffect const* bloomEffect = lifebloom->GetEffect(EFFECT_1);
        if (!bloomEffect)
            return;

        int32 const stack = lifebloom->GetStackAmount();
        int32 healAmount = bloomEffect->GetAmount();
        SpellInfo const* finalHeal = sSpellMgr->GetSpellInfo(SPELL_LIFEBLOOM_BLOOM);
        if (!finalHeal)
            return;

        if (caster)
        {
            healAmount = int32(caster->SpellHealingBonusDone(target, finalHeal, healAmount, HEAL, EFFECT_1, 0.0f,
                                                               stack));

            // Harmony (RESTO §4): the bloom benefits at Empowered Rejuvenation's rate.
            if (float k = GetHarmonyCoefficient(caster, finalHeal, false))
            {
                if (Player* player = caster->ToPlayer())
                {
                    float const mult = 1.0f + float(CountHarmonyHots(caster, target)) * k *
                                        player->GetMasteryPercentage() / 100.0f;
                    healAmount = int32(float(healAmount) * mult);
                }
            }

            healAmount = int32(target->SpellHealingBonusTaken(caster, finalHeal, healAmount, HEAL, stack));
        }

        target->CastCustomSpell(target, SPELL_LIFEBLOOM_BLOOM, &healAmount, nullptr, nullptr, true, nullptr,
                                 bloomEffect, lifebloom->GetCasterGUID());
    }

    namespace
    {
        // Per-caster Lifebloom target tracking (RESTO §10's "state lives in caster's CustomData,
        // lost on relog by design").
        struct LifebloomTargets : DataMap::Base
        {
            std::vector<ObjectGuid> targets;
        };

        constexpr char const* LIFEBLOOM_TARGETS_KEY = "druid_resto_lifebloom_targets";

        // Per-target "already handled this aura instance" tracking for OnCoreHotApplied - see its
        // own doc comment in DruidMechanics.h for why this is needed.
        struct CoreHotApplicationTracker : DataMap::Base
        {
            std::unordered_set<Aura*> handled;
        };

        constexpr char const* CORE_HOT_APPLICATION_KEY = "druid_resto_core_hot_applications";
    }

    void OnLifebloomApplied(Player* caster, Unit* target)
    {
        if (!caster || !target)
            return;

        LifebloomTargets* state = caster->CustomData.GetDefault<LifebloomTargets>(LIFEBLOOM_TARGETS_KEY);
        ObjectGuid const casterGuid = caster->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();

        // Prune stale entries (target left the map, or lost the caster's Lifebloom without this
        // tracker hearing about it - e.g. a dispel or the old removal path below).
        state->targets.erase(std::remove_if(state->targets.begin(), state->targets.end(),
            [caster, casterGuid](ObjectGuid guid)
            {
                Unit* unit = ObjectAccessor::GetUnit(*caster, guid);
                return !unit || !unit->HasAura(SPELL_LIFEBLOOM, casterGuid);
            }), state->targets.end());

        // Move a refreshed target to the back (most-recently-touched) instead of leaving it at its
        // original position - code-review fix: this used to only push_back on a genuinely new
        // target, so a refresh of an already-tracked target never moved it, and eviction below
        // always evicted the earliest-ever-applied target even if it was the one just refreshed.
        auto it = std::find(state->targets.begin(), state->targets.end(), targetGuid);
        if (it != state->targets.end())
            state->targets.erase(it);
        state->targets.push_back(targetGuid);

        // Gift of the Earthmother r3 capstone (9,2): two Lifebloom targets instead of one.
        size_t const limit = caster->HasAura(SPELL_GIFT_OF_THE_EARTHMOTHER_R3) ? 2 : 1;

        while (state->targets.size() > limit)
        {
            ObjectGuid const oldest = state->targets.front();
            state->targets.erase(state->targets.begin());

            if (Unit* unit = ObjectAccessor::GetUnit(*caster, oldest))
                unit->RemoveAura(SPELL_LIFEBLOOM, casterGuid, 0, AURA_REMOVE_BY_DEFAULT);
        }
    }

    void OnRejuvenationApplied(Unit* caster, Unit* target, Aura* rejuvenation)
    {
        // Tree of Life (8,1): every application of the caster's own Rejuvenation/Germination while
        // shapeshifted into Tree of Life instantly heals for 25% of its total healing - including
        // Proliferation spreads and Germination itself.
        if (!caster || !target || !rejuvenation)
            return;

        Player* player = caster->ToPlayer();
        if (!player)
            return;

        AuraEffect const* effect = rejuvenation->GetEffect(EFFECT_0);
        if (!effect)
            return;

        // Tree of Life is a SPELL_AURA_TRANSFORM buff, not a real shapeshift (CORE-AUDIT row 38) -
        // GetShapeshiftForm() never returns FORM_TREE, so gate on the buff's own aura directly
        // (code-review fix: a stale GetShapeshiftForm() == FORM_TREE check here was permanently
        // dead, so this instant heal never fired).
        AuraEffect const* treeBonus = player->GetAuraEffect(SPELL_TREE_OF_LIFE_FORM, EFFECT_2);
        if (!treeBonus)
            return;

        int32 const totalHeal = effect->GetAmount() * effect->GetTotalTicks();
        int32 const amount = CalculatePct(totalHeal, treeBonus->GetAmount());
        if (amount <= 0)
            return;

        caster->CastCustomSpell(target, SPELL_TREE_OF_LIFE_REJUV_HEAL, &amount, nullptr, nullptr, true, nullptr,
                                 nullptr, caster->GetGUID());
    }

    void ExtendHot(Aura* aura, int32 ms)
    {
        if (!aura || !ms)
            return;

        aura->SetMaxDuration(aura->GetMaxDuration() + ms);
        aura->SetDuration(aura->GetDuration() + ms);
    }

    void AccelerateHotTicks(Aura* aura, int32 windowMs)
    {
        if (!aura || windowMs <= 0)
            return;

        if (IsFixedCadencePeriodic(aura->GetId()))
            return;

        Unit* target = aura->GetOwner() ? aura->GetOwner()->ToUnit() : nullptr;
        if (!target)
            return;

        ObjectGuid const casterGuid = aura->GetCasterGUID();
        uint32 const baseSpellId = aura->GetId();

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (!effect || effect->GetAuraType() != SPELL_AURA_PERIODIC_HEAL)
                continue;

            int32 const amplitude = effect->GetAmplitude();
            if (amplitude <= 0)
                continue;

            uint32 const extraTicks = uint32(windowMs) / uint32(amplitude);
            if (!extraTicks)
                continue;

            uint8 const effIndex = effect->GetEffIndex();
            Aura* const expected = aura;

            for (uint32 tick = 1; tick <= extraTicks; ++tick)
            {
                int32 const offset = int32(tick) * amplitude / 2;

                // The event lives on `target`'s own m_Events, so it dies with `target` - the raw
                // pointer capture is safe (Karazhan's boss_shade_of_aran precedent). The aura itself
                // may have been removed/refreshed by the time this fires, so it is re-resolved by
                // (casterGuid, baseSpellId) and compared against the instance captured here before
                // firing anything.
                target->m_Events.AddEventAtOffset(
                    [target, casterGuid, baseSpellId, effIndex, expected]()
                    {
                        Aura* current = target->GetAura(baseSpellId, casterGuid);
                        if (current != expected)
                            return;

                        AuraEffect* eff = current->GetEffect(effIndex);
                        if (!eff || eff->GetAuraType() != SPELL_AURA_PERIODIC_HEAL)
                            return;

                        if (eff->GetTickNumber() >= uint32(eff->GetTotalTicks()))
                            return;

                        AuraApplication* application = current->GetApplicationOfTarget(target->GetGUID());
                        if (!application)
                            return;

                        eff->PeriodicTick(application, current->GetCaster());
                    },
                    Milliseconds(offset));
            }
        }
    }

    void OnCoreHotApplied(Unit* target, Aura* aura)
    {
        if (!target || !aura)
            return;

        auto* tracker = target->CustomData.GetDefault<CoreHotApplicationTracker>(CORE_HOT_APPLICATION_KEY);
        if (!tracker->handled.insert(aura).second)
            return; // already handled this aura instance - see the header comment

        Unit* caster = aura->GetCaster();
        Player* casterPlayer = caster ? caster->ToPlayer() : nullptr;
        if (!casterPlayer || casterPlayer->getClass() != CLASS_DRUID)
            return;

        if (Aura const* flourish = casterPlayer->GetAura(SPELL_FLOURISH_BUFF))
            AccelerateHotTicks(aura, flourish->GetDuration());

        // Omen of Clarity r3 capstone: +10% on the spell/ability that consumed 200572.
        // GetDirectHealMultiplier covers direct heals and ApplyPeriodicHealTickMods covers every
        // later tick of a spell that also has a direct component, but a HoT-only consumer
        // (Rejuvenation, Wild Growth, Lifebloom) has no direct heal to multiply, so it must be
        // snapshotted once here, at application time, while m_spellModTakingSpell (which
        // ConsumedEmpoweredClearcasting reads) is still valid - ticks fire well after the cast that
        // applied the aura has already completed.
        if (ConsumedEmpoweredClearcasting(casterPlayer))
        {
            if (AuraEffect const* capstone = casterPlayer->GetAuraEffect(SPELL_CLEARCASTING_OMEN_CAPSTONE, EFFECT_1))
            {
                float const mult = 1.0f + float(capstone->GetAmount()) / 100.0f;
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                {
                    AuraEffect* effect = aura->GetEffect(i);
                    if (effect && effect->GetAuraType() == SPELL_AURA_PERIODIC_HEAL)
                        effect->ChangeAmount(int32(float(effect->GetAmount()) * mult));
                }
            }
        }
    }

    void ClearCoreHotApplication(Unit* target, Aura* aura)
    {
        if (!target || !aura)
            return;

        if (auto* tracker = target->CustomData.Get<CoreHotApplicationTracker>(CORE_HOT_APPLICATION_KEY))
            tracker->handled.erase(aura);
    }

    namespace
    {
        constexpr float BLOOM_JUMP_RANGE = 20.0f;
        constexpr uint32 BLOOM_JUMP_MAX_TARGETS = 3;
        constexpr Milliseconds BLOOM_JUMP_DELAY{ 300 };

        void ScheduleBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                                std::shared_ptr<std::vector<ObjectGuid>> frontier);

        void RunBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                           std::shared_ptr<std::vector<ObjectGuid>> frontier)
        {
            auto nextFrontier = std::make_shared<std::vector<ObjectGuid>>();

            for (ObjectGuid const& sourceGuid : *frontier)
            {
                Unit* source = ObjectAccessor::GetUnit(*caster, sourceGuid);
                if (!source)
                    continue;

                std::list<Unit*> nearby;
                Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck check(source, caster, BLOOM_JUMP_RANGE);
                Acore::UnitListSearcher<Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck> searcher(source, nearby,
                                                                                                    check);
                Cell::VisitObjects(source, searcher, BLOOM_JUMP_RANGE);

                nearby.remove_if([&](Unit* unit)
                {
                    if (std::find(visited->begin(), visited->end(), unit->GetGUID()) != visited->end())
                        return true;

                    if (!unit->HasAura(SPELL_REJUVENATION, caster->GetGUID()) &&
                        !unit->HasAura(SPELL_GERMINATION, caster->GetGUID()))
                        return true;

                    if (!source->IsWithinLOSInMap(unit))
                        return true;

                    return false;
                });

                if (nearby.empty())
                    continue;

                nearby.sort(Acore::HealthPctOrderPred());

                uint32 taken = 0;
                for (Unit* unit : nearby)
                {
                    if (taken >= BLOOM_JUMP_MAX_TARGETS)
                        break;

                    // The manual LoS check above is source->unit, but the actual cast below is
                    // caster->unit (SPELL_BLOOM_JUMP is cast by the original caster, not by
                    // `source`), so Spell::CheckCast can still fail this target on LoS/range from
                    // the caster on a multi-hop chain even though it passed the source-relative
                    // check. Code-review fix: only count/track a target once the cast actually
                    // resolved, instead of unconditionally consuming a jump slot and marking it
                    // visited for a cast that silently failed and healed nothing.
                    if (caster->CastSpell(unit, SPELL_BLOOM_JUMP,
                            TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_DISALLOW_PROC_EVENTS)) != SPELL_CAST_OK)
                        continue;

                    visited->push_back(unit->GetGUID());
                    nextFrontier->push_back(unit->GetGUID());
                    ++taken;
                }
            }

            if (!nextFrontier->empty())
                ScheduleBloomWave(caster, visited, nextFrontier);
        }

        void ScheduleBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                                std::shared_ptr<std::vector<ObjectGuid>> frontier)
        {
            // The event lives on the caster's own m_Events, so it dies with the caster - safe to
            // capture the raw pointer (RESTO §6: "the events die with the caster").
            caster->m_Events.AddEventAtOffset(
                [caster, visited, frontier]() { RunBloomWave(caster, visited, frontier); }, BLOOM_JUMP_DELAY);
        }
    }

    void StartBloomJumps(Unit* caster, Unit* primary)
    {
        if (!caster || !primary)
            return;

        auto visited = std::make_shared<std::vector<ObjectGuid>>();
        visited->push_back(primary->GetGUID());

        auto frontier = std::make_shared<std::vector<ObjectGuid>>();
        frontier->push_back(primary->GetGUID());

        ScheduleBloomWave(caster, visited, frontier);
    }
}
