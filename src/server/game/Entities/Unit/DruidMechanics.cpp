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

#include "Player.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include "Util.h"
#include <algorithm>
#include <array>

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
}
