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
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
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
#include <cmath>
#include <list>
#include <memory>
#include <mutex>
#include <unordered_map>
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

        // Barkskin cast times (game-time ms) by player GUID, for the 30 s floor (B7, CORE-AUDIT row
        // 34; FERAL §0.15: once Cooldown Haste has shortened the entry, its maxduration no longer
        // says when Barkskin was cast). Process-wide rather than the player's CustomData so a relog
        // inside the window keeps the floor; locked because maps update on several threads.
        std::mutex barkskinCastTimesLock;
        std::unordered_map<ObjectGuid, uint32> barkskinCastTimeByPlayer;

        // Game-time ms before which Barkskin's cooldown may not end, or 0 when no cast was recorded
        // (a server restart since the cast) - callers then skip the floor.
        uint32 GetBarkskinFloorEnd(Player const* player)
        {
            std::lock_guard<std::mutex> lock(barkskinCastTimesLock);
            auto const itr = barkskinCastTimeByPlayer.find(player->GetGUID());
            return itr != barkskinCastTimeByPlayer.end() ? itr->second + BARKSKIN_COOLDOWN_FLOOR_MS : 0;
        }

        // FERAL-ADDENDUM §3.1/§3.4: a chance this file rolls itself is scaled by Proc Chance, the
        // same formula spell_druid_feral.cpp's own (separate) copy uses for its script-rolled chances.
        bool RollProcChance(Player const* player, float chancePct)
        {
            float const scaled = chancePct * (1.0f + player->GetProcChancePercentage() / 100.0f);
            return roll_chance_f(std::min(100.0f, scaled));
        }
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

        // Feral pass (CORE-AUDIT row 1): Feral Aggression, Rending Swipes on Swipe (Bear), Shredded
        // Defense and Primal Gore's Mastery for spells with a SCHOOL_DAMAGE effect and every DoT
        // snapshot (A4) - weapon-damage abilities and autoattacks get the same multiplier from
        // druid_hooks.cpp. Before the nature/arcane early-out: the clauses are physical/any school.
        if (player->getClass() == CLASS_DRUID)
            doneTotalMod *= GetFeralDamageDoneMultiplier(player, victim, spellProto, spellProto->GetSchoolMask());

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

        // Barkskin's 30 s floor (B7, CORE-AUDIT row 34): a reduction never ends the cooldown
        // earlier than the cast time + BARKSKIN_COOLDOWN_FLOOR_MS (Iron Hide is the Feral caller).
        if (spellId == SPELL_BARKSKIN)
        {
            SpellCooldowns const& cooldowns = player->GetSpellCooldownMap();
            auto const itr = cooldowns.find(SPELL_BARKSKIN);
            if (itr == cooldowns.end())
                return;

            if (uint32 const floorEnd = GetBarkskinFloorEnd(player))
            {
                if (itr->second.end <= floorEnd)
                    return;

                ms = std::min(ms, itr->second.end - floorEnd);
            }
        }

        // PLAN A8 (CORE-AUDIT row 36): ModifySpellCooldown() now resends the corrected cooldown
        // to the client itself (Player::ResendSpellCooldown), and is a safe no-op if spellId has
        // no tracked cooldown entry (e.g. Shooting Stars having just cleared Starsurge's).
        player->ModifySpellCooldown(spellId, -int32(ms));
    }

    bool TryStartInternalCooldown(Player* player, uint32 markerId, uint32 icdMs)
    {
        if (!player || player->HasSpellCooldown(markerId))
            return false;

        player->AddSpellCooldown(markerId, 0, icdMs);
        return true;
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

            uint8 const effIndex = effect->GetEffIndex();
            Aura* const expected = aura;

            // Doubling the tick rate = one extra tick halfway between every pair of regular ticks
            // inside the window. The next regular tick fires in GetPeriodicTimer() ms, so the
            // nearest upcoming midpoint is half an amplitude before it (or, if that's already
            // past, half an amplitude after it); from there, one every amplitude until the window
            // closes. (Offsets of tick * amplitude / 2 from "now" bunched every extra tick into
            // the first few seconds, often on top of a regular tick.)
            int32 firstOffset = effect->GetPeriodicTimer() - amplitude / 2;
            if (firstOffset < 0)
                firstOffset += amplitude;

            for (int32 offset = firstOffset; offset < windowMs; offset += amplitude)
            {
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
        constexpr TriggerCastFlags BLOOM_JUMP_CAST_FLAGS =
            TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_DISALLOW_PROC_EVENTS);

        void ScheduleBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                                std::shared_ptr<std::vector<ObjectGuid>> frontier, Milliseconds delay);

        // Mirrors Spell::AddUnitTarget's projectile delay: launcher-to-target distance, at least
        // 5 yards, over the spell's Speed.
        Milliseconds GetBloomFlightTime(Unit const* launcher, Unit const* target)
        {
            SpellInfo const* jump = sSpellMgr->GetSpellInfo(SPELL_BLOOM_JUMP);
            if (!jump || jump->Speed <= 0.0f || launcher == target)
                return 0ms;

            float const dist = std::max(launcher->GetDistance(target->GetPositionX(), target->GetPositionY(),
                                                              target->GetPositionZ()), 5.0f);
            return Milliseconds(static_cast<int64>(std::floor(dist / jump->Speed * 1000.0f)));
        }

        void RunBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                           std::shared_ptr<std::vector<ObjectGuid>> frontier)
        {
            auto nextFrontier = std::make_shared<std::vector<ObjectGuid>>();
            Milliseconds longestFlight = 0ms;

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

                    // SPELL_BLOOM_JUMP is a projectile, so `source` (the previous hop) launches it
                    // and the orb visibly bounces target to target. The druid stays the original
                    // caster, so the heal, its crit and its procs stay the druid's (Spell::EffectHeal
                    // and DoAllEffectOnTarget use m_originalCaster). A dead source can't launch, so
                    // the druid launches instead; the same fallback covers a source whose own
                    // CheckCast fails. Code-review fix: only count/track a target once a cast
                    // actually resolved, instead of consuming a jump slot for a failed cast.
                    Unit* launcher = source->IsAlive() ? source : caster;
                    SpellCastResult result = launcher->CastSpell(unit, SPELL_BLOOM_JUMP, BLOOM_JUMP_CAST_FLAGS, nullptr,
                                                                 nullptr, caster->GetGUID());
                    if (result != SPELL_CAST_OK && launcher != caster)
                    {
                        launcher = caster;
                        result = caster->CastSpell(unit, SPELL_BLOOM_JUMP, BLOOM_JUMP_CAST_FLAGS);
                    }

                    if (result != SPELL_CAST_OK)
                        continue;

                    visited->push_back(unit->GetGUID());
                    nextFrontier->push_back(unit->GetGUID());
                    longestFlight = std::max(longestFlight, GetBloomFlightTime(launcher, unit));
                    ++taken;
                }
            }

            // The next wave waits for this wave's slowest orb to land before its own short delay.
            if (!nextFrontier->empty())
                ScheduleBloomWave(caster, visited, nextFrontier, longestFlight + BLOOM_JUMP_DELAY);
        }

        void ScheduleBloomWave(Unit* caster, std::shared_ptr<std::vector<ObjectGuid>> visited,
                                std::shared_ptr<std::vector<ObjectGuid>> frontier, Milliseconds delay)
        {
            // The event lives on the caster's own m_Events, so it dies with the caster - safe to
            // capture the raw pointer (RESTO §6: "the events die with the caster").
            caster->m_Events.AddEventAtOffset(
                [caster, visited, frontier]() { RunBloomWave(caster, visited, frontier); }, delay);
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

        // Called from Bloom's AfterHit, i.e. once its own orb has landed.
        ScheduleBloomWave(caster, visited, frontier, BLOOM_JUMP_DELAY);
    }

    /*
     * ---------------------------------------------------------------------------------------
     * Feral pass bodies (druid-rework.FERAL.md §0.15-§0.17, FERAL-WP-BRIEF §5 "WP-B2",
     * CORE-AUDIT rows 1, 22-34). Call sites: spell_druid_feral.cpp and druid_hooks.cpp - no Feral
     * core line; the one core call is Balance's ApplyDoneDamagePctMods above.
     * ---------------------------------------------------------------------------------------
     */

    bool IsInBearForm(Unit const* unit)
    {
        if (!unit)
            return false;

        ShapeshiftForm const form = unit->GetShapeshiftForm();
        return form == FORM_BEAR || form == FORM_DIREBEAR;
    }

    bool IsBestialFuryActive(Unit const* unit)
    {
        return unit && unit->GetShapeshiftForm() == FORM_BEAR;
    }

    uint8 GetSwellStacks(Unit const* unit)
    {
        if (!unit)
            return 0;

        Aura const* swell = unit->GetAura(SPELL_SWELL, unit->GetGUID());
        return swell ? swell->GetStackAmount() : 0;
    }

    uint8 GetSwellStacksForDamage(Unit const* unit)
    {
        if (!unit)
            return 0;

        // Berserk: "Pulverize and Upheaval consume no Swell and deal damage as though they
        // consumed 2" - the 2 is Berserk's EFFECT_1 value.
        if (Aura const* berserk = unit->GetAura(SPELL_BERSERK))
        {
            AuraEffect const* effect = berserk->GetEffect(EFFECT_1);
            int32 const amount = effect ? effect->GetAmount()
                                        : berserk->GetSpellInfo()->Effects[EFFECT_1].CalcValue(unit);
            return uint8(std::clamp<int32>(amount, 0, SWELL_MAX_STACKS));
        }

        return std::min(GetSwellStacks(unit), SWELL_MAX_CONSUMED);
    }

    void AddSwell(Unit* unit, uint8 count)
    {
        if (!unit || !count || !IsBestialFuryActive(unit))
            return;

        Aura* swell = unit->GetAura(SPELL_SWELL, unit->GetGUID());
        uint32 const current = swell ? swell->GetStackAmount() : 0;
        if (!swell)
        {
            swell = unit->AddAura(SPELL_SWELL, unit);
            if (!swell)
                return;
        }

        uint8 const stacks = uint8(std::min<uint32>(current + count, SWELL_MAX_STACKS));
        if (swell->GetStackAmount() != stacks)
            swell->SetStackAmount(stacks);

        // One shared timer that every gain restarts - 15 s in combat, 20 s out of combat.
        int32 const duration = unit->IsInCombat() ? SWELL_DURATION_IN_COMBAT_MS : SWELL_DURATION_OUT_OF_COMBAT_MS;
        swell->SetMaxDuration(duration);
        swell->SetDuration(duration);

        OnSwellChanged(unit);
    }

    uint8 ConsumeSwell(Unit* unit, uint8 count)
    {
        if (!unit || !count || unit->HasAura(SPELL_BERSERK))
            return 0;

        Aura* swell = unit->GetAura(SPELL_SWELL, unit->GetGUID());
        if (!swell)
            return 0;

        uint8 const removed = std::min<uint8>(count, swell->GetStackAmount());

        // Consuming never restarts the timer. Spending the last stacks removes the aura with
        // AURA_REMOVE_BY_DEFAULT, which spell_dru_swell's expire-only decay leaves alone.
        swell->ModStackAmount(-int32(count));

        OnSwellChanged(unit);
        return removed;
    }

    void OnSwellChanged(Unit* unit)
    {
        if (!unit)
            return;

        // The AuraScripts' DoEffectCalcAmount (canBeRecalculated) reads GetSwellStacks; only the
        // rank the unit knows exists.
        for (uint32 rankId : { SPELL_SPLINTERING_BLOWS_R1, SPELL_SPLINTERING_BLOWS_R2, SPELL_SPLINTERING_BLOWS_R3,
                               SPELL_BONEBREAKER_R1, SPELL_BONEBREAKER_R2, SPELL_BONEBREAKER_R3 })
            if (AuraEffect* effect = unit->GetAuraEffect(rankId, EFFECT_0))
                effect->RecalculateAmount();
    }

    void TryGrantToothAndClaw(Player* caster, float chancePct)
    {
        if (!caster || chancePct <= 0.0f || !IsBestialFuryActive(caster))
            return;

        if (!RollProcChance(caster, chancePct))
            return;

        caster->CastSpell(caster, SPELL_TOOTH_AND_CLAW, TRIGGERED_FULL_MASK);
    }

    void OnSwellSpent(Player* caster, uint8 consumed)
    {
        if (!caster || !consumed)
            return;

        // Predatory Strikes' bear clause (FERAL-ADDENDUM §3.4): rankTenths/10 x stacks consumed,
        // e.g. rank 3 (37.5%) at 2 stacks -> 75% - RollProcChance caps the total at 100%.
        int32 const tenths = GetRankAmount(caster,
            { SPELL_PREDATORY_STRIKES_R3, SPELL_PREDATORY_STRIKES_R2, SPELL_PREDATORY_STRIKES_R1 }, EFFECT_1);
        if (tenths > 0)
            TryGrantToothAndClaw(caster, float(tenths) * float(consumed) / 10.0f);
    }

    void TryPrimalPrecisionBearReduction(Player* caster, uint32 reductionMs)
    {
        if (!caster || !caster->HasAura(SPELL_PRIMAL_PRECISION_R2) || caster->HasAura(SPELL_BERSERK))
            return;

        // 48410 doubles as the ICD marker shared with the cat clause (spell_dru_primal_precision).
        if (!TryStartInternalCooldown(caster, SPELL_PRIMAL_PRECISION_R2, PRIMAL_PRECISION_ICD_MS))
            return;

        ReduceSpellCooldown(caster, SPELL_BERSERK, reductionMs);
    }

    void ApplyNurturingInstinctEmpower(Player* caster)
    {
        if (!caster)
            return;

        int32 const bonus = GetRankAmount(caster,
            { SPELL_NURTURING_INSTINCT_R2, SPELL_NURTURING_INSTINCT_R1 }, EFFECT_1);
        if (bonus <= 0)
            return;

        // Both effects (damage and periodic damage) take the rank's value.
        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, bonus);
        values.AddSpellMod(SPELLVALUE_BASE_POINT1, bonus);
        caster->CastCustomSpell(SPELL_NI_EMPOWER, values, caster, TRIGGERED_FULL_MASK);
    }

    void RestartWithStacks(Unit* target, uint32 spellId, uint8 stacks, int32 durationMs)
    {
        if (!target || !stacks)
            return;

        // The event lives on target's own m_Events, so it dies with target - the raw pointer
        // capture is safe (AccelerateHotTicks above). Everything else is re-resolved when it fires.
        target->m_Events.AddEventAtOffset([target, spellId, stacks, durationMs]()
        {
            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
            if (!spellInfo || !target->IsAlive())
                return;

            // Left the form the aura needs in the meantime (Ironfur: bear, Swell: Bestial Fury).
            if (spellInfo->CheckShapeshift(target->GetShapeshiftForm()) != SPELL_CAST_OK)
                return;

            // A recast inside the 1 ms window already created a fresh aura: add the surviving stacks
            // to it instead of replacing it.
            uint32 newStacks = stacks;
            Aura* aura = target->GetAura(spellId, target->GetGUID());
            if (aura)
                newStacks += aura->GetStackAmount();
            else
            {
                aura = target->AddAura(spellId, target);
                if (!aura)
                    return;
            }

            newStacks = std::min<uint32>(newStacks, std::max<uint32>(spellInfo->StackAmount, 1));
            if (aura->GetStackAmount() != newStacks)
                aura->SetStackAmount(uint8(newStacks));

            if (durationMs > 0)
            {
                aura->SetMaxDuration(durationMs);
                aura->SetDuration(durationMs);
            }

            if (spellId == SPELL_SWELL)
                OnSwellChanged(target);
        }, Milliseconds(1));
    }

    void OnBarkskinCast(Player* player)
    {
        if (!player)
            return;

        uint32 const now = GameTime::GetGameTimeMS().count();

        std::lock_guard<std::mutex> lock(barkskinCastTimesLock);

        // Entries older than the floor can no longer clamp anything - drop them so the map only
        // ever holds the druids with a Barkskin inside its window.
        for (auto itr = barkskinCastTimeByPlayer.begin(); itr != barkskinCastTimeByPlayer.end();)
        {
            if (now - itr->second >= BARKSKIN_COOLDOWN_FLOOR_MS)
                itr = barkskinCastTimeByPlayer.erase(itr);
            else
                ++itr;
        }

        barkskinCastTimeByPlayer[player->GetGUID()] = now;
    }

    void ApplyBarkskinFloor(Player* player)
    {
        if (!player)
            return;

        uint32 const floorEnd = GetBarkskinFloorEnd(player);
        if (!floorEnd)
            return;

        SpellCooldowns const& cooldowns = player->GetSpellCooldownMap();
        auto const itr = cooldowns.find(SPELL_BARKSKIN);
        if (itr == cooldowns.end() || itr->second.end >= floorEnd)
            return;

        // Positive delta: pushes the entry's end out to the floor and resends it (PLAN A8).
        player->ModifySpellCooldown(SPELL_BARKSKIN, int32(floorEnd - itr->second.end));
    }

    float GetHeartOfTheWildMasteryPct(Player const* player)
    {
        if (!player)
            return 0.0f;

        AuraEffect const* capstone = player->GetAuraEffect(SPELL_HEART_OF_THE_WILD_R3, EFFECT_2);
        if (!capstone)
            return 0.0f;

        return CalculatePct(player->GetMasteryPercentage(), float(capstone->GetAmount()));
    }

    float GetFeralDamageDoneMultiplier(Player const* player, Unit const* victim, SpellInfo const* spellInfo,
                                       SpellSchoolMask schoolMask)
    {
        if (!player || !victim)
            return 1.0f;

        float mult = 1.0f;
        ObjectGuid const casterGuid = player->GetGUID();

        // Feral Aggression (1,3): targets above 75% health.
        if (victim->HealthAbovePct(75))
            if (int32 pct = GetRankAmount(player,
                    { SPELL_FERAL_AGGRESSION_R3, SPELL_FERAL_AGGRESSION_R2, SPELL_FERAL_AGGRESSION_R1 }, EFFECT_0))
                AddPct(mult, pct);

        if (spellInfo)
        {
            uint32 const id = spellInfo->Id;

            // Rending Swipes (4,0): Swipe and Upheaval vs a target carrying the caster's Thrash.
            if ((id == SPELL_SWIPE_BEAR || id == SPELL_SWIPE_CAT || id == SPELL_UPHEAVAL) &&
                victim->HasAura(SPELL_THRASH, casterGuid))
                if (int32 pct = GetRankAmount(player, { SPELL_RENDING_SWIPES_R2, SPELL_RENDING_SWIPES_R1 }, EFFECT_2))
                    AddPct(mult, pct);

            // Rend and Tear (9,1): Maul and Shred vs a target carrying the caster's Rip or Lacerate.
            if ((id == SPELL_MAUL || id == SPELL_SHRED) &&
                (victim->HasAura(SPELL_RIP, casterGuid) || victim->HasAura(SPELL_LACERATE, casterGuid)))
                if (int32 pct = GetRankAmount(player,
                        { SPELL_REND_AND_TEAR_R3, SPELL_REND_AND_TEAR_R2, SPELL_REND_AND_TEAR_R1 }, EFFECT_0))
                    AddPct(mult, pct);

            // Primal Gore r3 (9,2) Mastery: bleed damage in Cat Form. Infected Wound (200427) is
            // Nature with no bleed mechanic, so it never matches.
            if (player->GetShapeshiftForm() == FORM_CAT &&
                (spellInfo->GetAllEffectsMechanicMask() & (1ULL << MECHANIC_BLEED)))
                if (AuraEffect const* gore = player->GetAuraEffect(SPELL_PRIMAL_GORE_R3, EFFECT_1))
                    AddPct(mult, CalculatePct(player->GetMasteryPercentage(), float(gore->GetAmount())));
        }

        // Shredded Defense (Shredding Attacks r2): physical damage vs the caster's debuff - its
        // EFFECT_0 amount already includes the stacks (5% each).
        if (schoolMask & SPELL_SCHOOL_MASK_NORMAL)
            if (AuraEffect const* shredded = victim->GetAuraEffect(SPELL_SHREDDED_DEFENSE, EFFECT_0, casterGuid))
                AddPct(mult, shredded->GetAmount());

        return mult;
    }

    float GetIronHideDamageTakenMultiplier(Unit const* victim, SpellSchoolMask schoolMask)
    {
        if (!victim || !(schoolMask & SPELL_SCHOOL_MASK_MAGIC))
            return 1.0f;

        Aura const* ironfur = victim->GetAura(SPELL_IRONFUR, victim->GetGUID());
        if (!ironfur)
            return 1.0f;

        int32 const tenths = GetRankAmount(victim, { SPELL_IRON_HIDE_R3, SPELL_IRON_HIDE_R2, SPELL_IRON_HIDE_R1 },
                                           EFFECT_0);
        if (tenths <= 0)
            return 1.0f;

        float const reduction = float(tenths) / 1000.0f * float(ironfur->GetStackAmount());
        return std::max(0.0f, 1.0f - reduction);
    }

    float GetExternalHealingReceivedMultiplier(Player const* target)
    {
        if (!target)
            return 1.0f;

        float mult = 1.0f;
        ShapeshiftForm const form = target->GetShapeshiftForm();

        // Heart of the Wild r3 Mastery - suppressed in Bestial Fury, so the everyday bear (form 8)
        // only.
        if (form == FORM_DIREBEAR)
            if (float pct = GetHeartOfTheWildMasteryPct(target))
                AddPct(mult, pct);

        // Elder Hide r3 capstone: per Ironfur stack.
        if (AuraEffect const* elderHide = target->GetAuraEffect(SPELL_ELDER_HIDE_R3, EFFECT_2))
            if (Aura const* ironfur = target->GetAura(SPELL_IRONFUR, target->GetGUID()))
                AddPct(mult, elderHide->GetAmount() * int32(ironfur->GetStackAmount()));

        // Nurturing Instinct (4,3): Cat, Bear and Dire Bear Form; Survival Instincts triples it.
        if (form == FORM_CAT || IsInBearForm(target))
        {
            if (int32 pct = GetRankAmount(target, { SPELL_NURTURING_INSTINCT_R2, SPELL_NURTURING_INSTINCT_R1 },
                                          EFFECT_0))
            {
                if (target->HasAura(SPELL_SURVIVAL_INSTINCTS))
                    pct *= 3;

                AddPct(mult, pct);
            }
        }

        return mult;
    }

    void OnFeralFormChanged(Player* player, bool refreshBoosts)
    {
        if (!player)
            return;

        if (refreshBoosts)
        {
            // The four boosts carry Stances, but a bear <-> Bestial Fury swap (forms 8 and 5) keeps
            // them, so always drop and recast them for the current form.
            ObjectGuid const guid = player->GetGUID();
            player->RemoveAurasDueToSpell(SPELL_HOTW_CAT_BUFF, guid);
            player->RemoveAurasDueToSpell(SPELL_HOTW_BEAR_BUFF, guid);
            player->RemoveAurasDueToSpell(SPELL_FERAL_SWIFTNESS_SPEED, guid);
            player->RemoveAurasDueToSpell(SPELL_ELDER_HIDE_ARMOR, guid);

            int32 const heartOfTheWild = GetRankAmount(player,
                { SPELL_HEART_OF_THE_WILD_R3, SPELL_HEART_OF_THE_WILD_R2, SPELL_HEART_OF_THE_WILD_R1 }, EFFECT_1);
            int32 const aggression = GetRankAmount(player,
                { SPELL_FERAL_AGGRESSION_R3, SPELL_FERAL_AGGRESSION_R2, SPELL_FERAL_AGGRESSION_R1 }, EFFECT_1);
            int32 const swiftness = GetRankAmount(player, { SPELL_FERAL_SWIFTNESS_R2, SPELL_FERAL_SWIFTNESS_R1 },
                                                  EFFECT_1);

            if (player->GetShapeshiftForm() == FORM_CAT)
            {
                // 24900: BP0 haste %, BP1 attack power %.
                if (heartOfTheWild || aggression)
                {
                    CustomSpellValues values;
                    values.AddSpellMod(SPELLVALUE_BASE_POINT0, heartOfTheWild);
                    values.AddSpellMod(SPELLVALUE_BASE_POINT1, aggression);
                    player->CastCustomSpell(SPELL_HOTW_CAT_BUFF, values, player, TRIGGERED_FULL_MASK);
                }

                if (swiftness)
                    player->CastCustomSpell(SPELL_FERAL_SWIFTNESS_SPEED, SPELLVALUE_BASE_POINT0, swiftness, player,
                                             true);
            }
            else if (IsInBearForm(player))
            {
                // 24899: BP0 Stamina %, BP1 attack power %.
                if (heartOfTheWild || aggression)
                {
                    CustomSpellValues values;
                    values.AddSpellMod(SPELLVALUE_BASE_POINT0, heartOfTheWild);
                    values.AddSpellMod(SPELLVALUE_BASE_POINT1, heartOfTheWild + aggression);
                    player->CastCustomSpell(SPELL_HOTW_BEAR_BUFF, values, player, TRIGGERED_FULL_MASK);
                }

                if (int32 armor = GetRankAmount(player,
                        { SPELL_ELDER_HIDE_R3, SPELL_ELDER_HIDE_R2, SPELL_ELDER_HIDE_R1 }, EFFECT_1))
                    player->CastCustomSpell(SPELL_ELDER_HIDE_ARMOR, SPELLVALUE_BASE_POINT0, armor, player, true);

                // Bear Form gets half of the cat speed.
                if (int32 bearSpeed = swiftness / 2)
                    player->CastCustomSpell(SPELL_FERAL_SWIFTNESS_SPEED, SPELLVALUE_BASE_POINT0, bearSpeed, player,
                                             true);
            }
        }

        // Form-gated talent amounts (their AuraScripts zero them outside the required form).
        for (uint32 rankId : { SPELL_PROTECTOR_OF_THE_PACK_R1, SPELL_PROTECTOR_OF_THE_PACK_R2,
                               SPELL_PROTECTOR_OF_THE_PACK_R3, SPELL_SURVIVAL_OF_THE_FITTEST_R1,
                               SPELL_SURVIVAL_OF_THE_FITTEST_R2, SPELL_SURVIVAL_OF_THE_FITTEST_R3 })
            if (AuraEffect* effect = player->GetAuraEffect(rankId, EFFECT_1))
                effect->RecalculateAmount();

        for (uint32 rankId : { SPELL_PREDATORY_INSTINCTS_R1, SPELL_PREDATORY_INSTINCTS_R2,
                               SPELL_PREDATORY_INSTINCTS_R3 })
            if (AuraEffect* effect = player->GetAuraEffect(rankId, EFFECT_0))
                effect->RecalculateAmount();

        // Primal Precision's Bestial Fury haste clause (FERAL-ADDENDUM §3.7), EFFECT_2 on both ranks.
        for (uint32 rankId : { SPELL_PRIMAL_PRECISION_R1, SPELL_PRIMAL_PRECISION_R2 })
            if (AuraEffect* effect = player->GetAuraEffect(rankId, EFFECT_2))
                effect->RecalculateAmount();

        // Heart of the Wild's Mastery max health follows the form (C4).
        player->UpdateMaxHealth();
    }
}
