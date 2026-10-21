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
 * Shaman rework - Restoration spec scripts (shaman-rework S2a; docs/reworks/shaman-restoration-rework.md). Ids and
 * tunables come from ShamanData::; shared state (Tidal Waves, Cloudburst, Totemic Resonance, Tidal Force extension)
 * lives in ShamanMechanics' S2 block.
 *
 * Rules every script here follows (S2-NOTES section 3, S2a-WP-BRIEF):
 *  - Only a player caster/owner gets the talents. NPCs cast 8004 (Nak) and their own Mana Tide / Healing Stream
 *    totems, and keep the stock behaviour. Every check reads the shaman's own talents and auras, so a non-shaman with
 *    a talent gets do-nothing.
 *  - Triggered casts roll nothing: the Rip Current copy is a triggered 61295, so every Riptide side effect gates on
 *    !IsTriggered(). Totem, guardian and triggered heals never roll the shaman's procs.
 *  - Once per cast: Tidal Waves grants, Rip Current, Rainfall, Kindling, the Improved Water Shield capstone, the Tidal
 *    Mastery extension and the Undulation count. Per target: the Riptide consume (first target only, stock).
 *  - Proc Chance rolls go through Shaman::RollProcChance; real-second cooldown cuts through ModifySpellCooldown.
 *  - Smart picks choose players only (Heal::SelectMostInjured).
 *  - Amounts passed to CastCustomSpell / SetHitHeal are live values (SKILL "Sign convention").
 */

#include "Creature.h"
#include "DataMap.h"
#include "DynamicObject.h"
#include "GameTime.h"
#include "Group.h"
#include "HealMechanics.h"
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
#include "Unit.h"
#include <algorithm>
#include <array>
#include <limits>
#include <list>
#include <span>
#include <vector>

namespace
{
    // Stock ids the Restoration DSL never declares (script-only; NOTES section 3, 0-verify 2b)
    constexpr uint32 SPELL_EARTH_SHIELD_HEAL = 379;               // ignores caster modifiers (SpellInfoCorrections)
    constexpr uint32 SPELL_GLYPH_OF_EARTH_SHIELD = 63279;
    constexpr uint32 SPELL_ANCESTRAL_AWAKENING_HEAL = 52752;      // family 0, ignores caster modifiers
    constexpr uint32 SPELL_MANA_TIDE_ENERGIZE = 39609;

    // Stock Earth Shield heal throttle (spell_sha_earth_shield, kept as is) and the Improved Shields icon it reads
    constexpr uint32 EARTH_SHIELD_HEAL_THROTTLE_MS = 3500;
    constexpr uint32 SPELL_ICON_IMPROVED_SHIELDS = 19;

    // Values the doc fixes with no brief const yet (S1-L8: ask A3 for RIPTIDE_CHAIN_HEAL_PCT and IES_TW_GRANT)
    constexpr int32 RIPTIDE_CHAIN_HEAL_BONUS_PCT = 25;            // Riptide: the next Chain Heal on it heals 25% more
    constexpr uint8 IES_TIDAL_WAVES_GRANT = 1;                    // Improved Earth Shield capstone: 1 charge

    // Engine chain-heal jump radius (Spell::SearchChainTargets, 12.5 yd since 3.2) for the Undulating Currents jumps
    constexpr float CHAIN_HEAL_JUMP_RADIUS_YD = 12.5f;

    // Talent rank chains (rank order). Each rank is a passive aura on the shaman.
    constexpr std::array<uint32, 3> TIDAL_WAVES_RANKS = { ShamanData::SPELL_TIDAL_WAVES,
        ShamanData::SPELL_TIDAL_WAVES_51563, ShamanData::SPELL_TIDAL_WAVES_51564 };
    constexpr std::array<uint32, 3> TIDAL_MASTERY_RANKS = { ShamanData::SPELL_TIDAL_MASTERY,
        ShamanData::SPELL_TIDAL_MASTERY_16218, ShamanData::SPELL_TIDAL_MASTERY_16219 };
    constexpr std::array<uint32, 2> TORRENT_RANKS = { ShamanData::SPELL_FOCUSED_MIND,
        ShamanData::SPELL_FOCUSED_MIND_30865 };
    constexpr std::array<uint32, 2> RAINFALL_RANKS = { ShamanData::SPELL_RAINFALL_RANK1,
        ShamanData::SPELL_RAINFALL_RANK2 };
    constexpr std::array<uint32, 2> KINDLING_RANKS = { ShamanData::SPELL_KINDLING_RANK1,
        ShamanData::SPELL_KINDLING_RANK2 };
    constexpr std::array<uint32, 3> IMPROVED_HEALING_STREAM_RANKS = { ShamanData::SPELL_HEALING_GRACE,
        ShamanData::SPELL_HEALING_GRACE_29189, ShamanData::SPELL_HEALING_GRACE_29191 };
    constexpr std::array<uint32, 3> TIDAL_FOCUS_RANKS = { ShamanData::SPELL_TIDAL_FOCUS,
        ShamanData::SPELL_TIDAL_FOCUS_16214, ShamanData::SPELL_TIDAL_FOCUS_16215 };
    constexpr std::array<uint32, 3> IMPROVED_EARTH_SHIELD_RANKS = { ShamanData::SPELL_IMPROVED_EARTH_SHIELD,
        ShamanData::SPELL_IMPROVED_EARTH_SHIELD_51561, ShamanData::SPELL_IMPROVED_EARTH_SHIELD_RANK3 };
    constexpr std::array<uint32, 3> RESTORATIVE_TOTEMS_RANKS = { ShamanData::SPELL_RESTORATIVE_TOTEMS,
        ShamanData::SPELL_RESTORATIVE_TOTEMS_16205, ShamanData::SPELL_RESTORATIVE_TOTEMS_16206 };

    // Tidal Waves grant chance per rank (33/66/100%; Proc Chance multiplies the base)
    constexpr std::array<int32, 3> TIDAL_WAVES_CHANCE_PCT = { int32(ShamanData::TW_CHANCE_R1),
        int32(ShamanData::TW_CHANCE_R2), int32(ShamanData::TW_CHANCE_R3) };

    // Per-player state the Restoration scripts keep (lives as long as the player object)
    struct RestorationScriptState : DataMap::Base
    {
        uint32 earthShieldWavesReadyMs = 0;     // Improved Earth Shield capstone internal cooldown
    };

    constexpr char const* RESTORATION_SCRIPT_STATE_KEY = "shaman_restoration_script_state";

    RestorationScriptState* GetState(Player* player)
    {
        return player->CustomData.GetDefault<RestorationScriptState>(RESTORATION_SCRIPT_STATE_KEY);
    }

    uint32 NowMs()
    {
        return uint32(GameTime::GetGameTimeMS().count());
    }

    // Once-per-cast guard: one proc attempt per Spell object per world tick (paladin CastGuard shape). A Chain Heal's
    // targets are all hit in the same tick; the ms check keeps a reused Spell address from matching.
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

    template <std::size_t N>
    bool HasFullTalent(Player const* player, std::array<uint32, N> const& ranks)
    {
        return Shaman::GetTalentRank(player, ranks) == N;
    }

    // The player behind a proc on a talent aura: the aura's owner, and only when it is the actor itself
    Player* GetProcPlayer(Unit* auraOwner, ProcEventInfo& eventInfo)
    {
        Player* player = auraOwner ? auraOwner->ToPlayer() : nullptr;
        if (!player || !Shaman::IsOwnAction(player, eventInfo.GetActor()))
            return nullptr;

        return player;
    }

    // The player casting `spell` itself (never a triggered cast, never an NPC)
    Player* GetUntriggeredPlayerCaster(Spell const* spell, Unit* caster)
    {
        if (!spell || spell->IsTriggered() || !caster)
            return nullptr;

        return caster->ToPlayer();
    }

    // The crit roll the spell made for `target` at launch (TargetInfo, spell_priest_holy.cpp Echo of Light precedent)
    bool DidCritTarget(Spell* spell, Unit const* target)
    {
        if (!spell || !target)
            return false;

        for (TargetInfo const& info : *spell->GetUniqueTargetInfo())
            if (info.targetGUID == target->GetGUID())
                return info.missCondition == SPELL_MISS_NONE && info.crit;

        return false;
    }

    bool DidCritAnyTarget(Spell* spell)
    {
        if (!spell)
            return false;

        std::list<TargetInfo> const& targets = *spell->GetUniqueTargetInfo();
        return std::any_of(targets.begin(), targets.end(), [](TargetInfo const& info)
        {
            return info.missCondition == SPELL_MISS_NONE && info.crit;
        });
    }

    uint32 GetAuraCount(Player const* player, uint32 spellId)
    {
        Aura const* aura = player->GetAura(spellId);
        if (!aura)
            return 0;

        return aura->IsUsingCharges() ? aura->GetCharges() : aura->GetStackAmount();
    }

    // Casts `spellId` on the player (create or refresh) and leaves it at exactly `count` stacks (or charges)
    void SetAuraCount(Player* player, uint32 spellId, uint32 count)
    {
        player->CastSpell(player, spellId, true);

        Aura* aura = player->GetAura(spellId);
        if (!aura || !count)
            return;

        uint8 const wanted = uint8(std::min<uint32>(count, std::numeric_limits<uint8>::max()));
        if (aura->IsUsingCharges())
        {
            if (aura->GetCharges() != wanted)
                aura->SetCharges(wanted);
        }
        else if (aura->GetStackAmount() != wanted)
            aura->SetStackAmount(wanted);
    }

    // Tidal Waves: Chain Heal (TW_GRANT_CHAIN_HEAL) and Riptide (TW_GRANT_RIPTIDE) roll 33/66/100% x Proc Chance by
    // rank; a success raises the charges to `amount` (Shaman::GrantTidalWaves: never lowers, cap 3, refresh).
    void TryTidalWavesGrant(Player* player, uint8 amount)
    {
        uint8 const rank = Shaman::GetTalentRank(player, TIDAL_WAVES_RANKS);
        if (!rank)
            return;

        if (!Shaman::RollProcChance(player, float(TIDAL_WAVES_CHANCE_PCT[rank - 1])))
            return;

        Shaman::GrantTidalWaves(player, amount);
    }

    // Tidal Mastery capstone: a crit of this cast extends an active Tidal Force by `ms` (once per cast; the caller
    // decides the crit and the guard)
    void TryTidalMasteryExtension(Player* player, uint32 ms)
    {
        if (!HasFullTalent(player, TIDAL_MASTERY_RANKS) || !player->HasAura(ShamanData::SPELL_TIDAL_FORCE_AURA))
            return;

        Shaman::ExtendTidalForce(player, ms);
    }

    // Restorative Totems' Mana Tide bonus in percent: the rank aura's DUMMY amount (+10/20/30), 0 without the talent
    int32 GetRestorativeTotemsPct(Player const* owner)
    {
        uint8 const rank = Shaman::GetTalentRank(owner, RESTORATIVE_TOTEMS_RANKS);
        if (!rank)
            return 0;

        Aura const* aura = owner->GetAura(RESTORATIVE_TOTEMS_RANKS[rank - 1]);
        if (!aura)
            return 0;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i))
                if (effect->GetAuraType() == SPELL_AURA_DUMMY)
                    return effect->GetAmount();

        return 0;
    }
}

// 61295 Riptide - the Restoration side effects of a cast Riptide, once per cast, never for the triggered Rip Current
// copy (it releases no torrent, grants no Tidal Waves and rolls nothing; Torrent and Healing Way still reach it by
// family bit):
//  - Healing Rain torrent: the primary target stands in the shaman's own rain -> the torrent heal on up to
//    HEALING_RAIN_TARGETS most injured players inside the rain (shared doc "Healing Rain").
//  - Rip Current (Torrent rank 2): RIP_CURRENT_CHANCE x Proc Chance -> a triggered Riptide on the lowest-percent
//    injured player within RIP_CURRENT_RADIUS_YD of the primary, not the primary.
//  - Rainfall rank 2: RAINFALL_CHANCE x Proc Chance -> the next Healing Rain is instant (refresh, no stack).
//  - Tidal Waves: raise to TW_GRANT_RIPTIDE charges.
//  - Tidal Mastery capstone: a crit of the direct heal extends Tidal Force by TM_EXT_RIPTIDE_MS.
class spell_sha_resto_riptide : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_riptide);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_RIPTIDE, ShamanData::SPELL_HEALING_RAIN,
            ShamanData::SPELL_TORRENT_HEAL, ShamanData::SPELL_RAINFALL_BUFF, ShamanData::SPELL_TIDAL_FORCE_AURA });
    }

    bool _done = false;

    void ReleaseTorrent(Player* player, Unit* target)
    {
        DynamicObject* zone = player->GetDynObject(ShamanData::SPELL_HEALING_RAIN);
        if (!zone || !zone->IsWithinDistInMap(target, zone->GetRadius()))
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(player, zone, zone->GetRadius(), uint8(ShamanData::HEALING_RAIN_TARGETS), allies);
        for (Unit* ally : allies)
            player->CastSpell(ally, ShamanData::SPELL_TORRENT_HEAL, TRIGGERED_FULL_MASK);
    }

    void TryRipCurrent(Player* player, Unit* target)
    {
        if (!HasFullTalent(player, TORRENT_RANKS))
            return;

        if (!Shaman::RollProcChance(player, float(ShamanData::RIP_CURRENT_CHANCE)))
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(player, target, float(ShamanData::RIP_CURRENT_RADIUS_YD), 1, allies, target);
        if (allies.empty() || allies.front()->IsFullHealth())
            return;

        // Triggered: no cost, no cooldown, no GCD; this script skips every side effect on it
        player->CastSpell(allies.front(), ShamanData::SPELL_RIPTIDE, TRIGGERED_FULL_MASK);
    }

    void TryRainfall(Player* player)
    {
        if (!HasFullTalent(player, RAINFALL_RANKS))
            return;

        if (Shaman::RollProcChance(player, float(ShamanData::RAINFALL_CHANCE)))
            player->CastSpell(player, ShamanData::SPELL_RAINFALL_BUFF, true);
    }

    void HandleAfterHit()
    {
        if (_done)
            return;

        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        _done = true;

        ReleaseTorrent(player, target);
        TryRipCurrent(player, target);
        TryRainfall(player);
        TryTidalWavesGrant(player, uint8(ShamanData::TW_GRANT_RIPTIDE));

        if (DidCritTarget(GetSpell(), target))
            TryTidalMasteryExtension(player, uint32(ShamanData::TM_EXT_RIPTIDE_MS));
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_sha_resto_riptide::HandleAfterHit);
    }
};

// -1064 Chain Heal (replaces spell_sha_chain_heal; group 1088's stock "-1064" row is not copied, X8).
//  - Riptide (stock): the first target's Riptide from this caster is consumed and every target heals
//    RIPTIDE_CHAIN_HEAL_BONUS_PCT% more. Improved Chain Heal's buff keeps the Riptide instead (the +25% still applies)
//    and is spent by that Chain Heal; a Chain Heal with no Riptide to keep leaves the buff up.
//  - Once per cast (player caster, not triggered): Tidal Waves raise to TW_GRANT_CHAIN_HEAL, Kindling rank 2
//    (KINDLING_CHANCE x Proc Chance -> Undulating Currents Totem cooldown -KINDLING_CDR_MS, real seconds), Tidal
//    Mastery extension TM_EXT_CH_MS when any target crit. Earthliving and Ancestral Healing stay per target (their
//    own procs); Tidal Force's no-falloff is data (SPELLMOD_DAMAGE_MULTIPLIER).
class spell_sha_resto_chain_heal : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_chain_heal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF,
            ShamanData::SPELL_UNDULATING_CURRENTS_TOTEM, ShamanData::SPELL_TIDAL_FORCE_AURA });
    }

    bool _firstHeal = true;
    bool _riptide = false;

    void HandleHeal(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        if (_firstHeal)
        {
            _firstHeal = false;
            if (AuraEffect* riptide = target->GetAuraEffect(SPELL_AURA_PERIODIC_HEAL, SPELLFAMILY_SHAMAN, 0, 0, 0x10,
                caster->GetGUID()))
            {
                _riptide = true;
                if (caster->HasAura(ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF))
                    caster->RemoveAurasDueToSpell(ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF);
                else
                    target->RemoveAura(riptide->GetBase());
            }
        }

        if (!_riptide)
            return;

        int32 heal = GetHitHeal();
        AddPct(heal, RIPTIDE_CHAIN_HEAL_BONUS_PCT);
        SetHitHeal(heal);
    }

    void TryKindling(Player* player)
    {
        if (!HasFullTalent(player, KINDLING_RANKS))
            return;

        if (Shaman::RollProcChance(player, float(ShamanData::KINDLING_CHANCE)))
            player->ModifySpellCooldown(ShamanData::SPELL_UNDULATING_CURRENTS_TOTEM,
                -int32(ShamanData::KINDLING_CDR_MS));
    }

    void HandleAfterCast()
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        if (!player)
            return;

        TryTidalWavesGrant(player, uint8(ShamanData::TW_GRANT_CHAIN_HEAL));
        TryKindling(player);

        // Crit is rolled at launch, before AfterCast
        if (DidCritAnyTarget(GetSpell()))
            TryTidalMasteryExtension(player, uint32(ShamanData::TM_EXT_CH_MS));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_chain_heal::HandleHeal, EFFECT_0, SPELL_EFFECT_HEAL);
        AfterCast += SpellCastFn(spell_sha_resto_chain_heal::HandleAfterCast);
    }
};

// 331 Healing Wave, 8004 Lesser Healing Wave - player caster only (Nak 3434 casts 8004), never triggered.
//  - Undulation (Tidal Waves rank 3): every UNDULATION_CASTS-th cast heals UNDULATION_BONUS_PCT% more. The counter
//    buff shows the casts made toward it and goes when the empowered cast lands; it counts casts, never heals, so the
//    Tidal Force echo (its own spell) never counts.
//  - Tidal Waves: the buff's per-stack SpellMods are read by the engine at cast; AfterCast drops one charge
//    (Shaman::ConsumeTidalWaves, which also feeds the Improved Chain Heal count).
//  - Tidal Force (caster aura up): Healing Wave echoes TF_ECHO_PCT% of its heal (crit included) on the target after
//    TF_ECHO_DELAY_MS; Lesser Healing Wave puts a stack of the healing-received aura on the target.
//  - Tidal Mastery capstone: a crit extends Tidal Force (Healing Wave TM_EXT_HW_MS, Lesser TM_EXT_LHW_MS).
class spell_sha_resto_healing_wave : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_healing_wave);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_HEALING_WAVE, ShamanData::SPELL_LESSER_HEALING_WAVE,
            ShamanData::SPELL_UNDULATION_COUNTER, ShamanData::SPELL_TIDAL_FORCE_AURA,
            ShamanData::SPELL_TIDAL_FORCE_STACK, ShamanData::SPELL_TIDAL_FORCE_ECHO });
    }

    bool _undulation = false;
    bool _hitDone = false;

    bool IsHealingWave()
    {
        return GetSpellInfo()->Id == ShamanData::SPELL_HEALING_WAVE;
    }

    void HandleBeforeCast()
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        if (!player || !HasFullTalent(player, TIDAL_WAVES_RANKS))
            return;

        uint32 const counted = GetAuraCount(player, ShamanData::SPELL_UNDULATION_COUNTER) + 1;
        if (counted >= uint32(ShamanData::UNDULATION_CASTS))
        {
            _undulation = true;
            player->RemoveAurasDueToSpell(ShamanData::SPELL_UNDULATION_COUNTER);
        }
        else
            SetAuraCount(player, ShamanData::SPELL_UNDULATION_COUNTER, counted);
    }

    // The echo lands TF_ECHO_DELAY_MS later from the shaman, if the target is still there and alive. The event lives
    // in the player's own m_Events, so the captured pointer is valid whenever it runs.
    static void ScheduleEcho(Player* player, Unit* target, int32 amount)
    {
        if (amount <= 0)
            return;

        ObjectGuid const targetGuid = target->GetGUID();
        player->m_Events.AddEventAtOffset([player, targetGuid, amount]()
        {
            Unit* echoTarget = ObjectAccessor::GetUnit(*player, targetGuid);
            if (!echoTarget || !echoTarget->IsAlive() || !player->IsAlive())
                return;

            // GetHitHeal() already carries the target's healing-taken modifiers and the echo's own cast applies them
            // again: divide them out so they count once (WP-R L1).
            int32 base = amount;
            if (SpellInfo const* echoInfo = sSpellMgr->GetSpellInfo(ShamanData::SPELL_TIDAL_FORCE_ECHO))
            {
                constexpr uint32 PROBE = 10000;
                if (uint32 const taken = echoTarget->SpellHealingBonusTaken(player, echoInfo, PROBE, HEAL))
                    base = int32(uint64(uint32(amount)) * PROBE / taken);
            }

            player->CastCustomSpell(ShamanData::SPELL_TIDAL_FORCE_ECHO, SPELLVALUE_BASE_POINT0, base, echoTarget,
                TRIGGERED_FULL_MASK);
        }, Milliseconds(ShamanData::TF_ECHO_DELAY_MS));
    }

    void HandleHeal(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        int32 heal = GetHitHeal();
        if (_undulation)
        {
            AddPct(heal, int32(ShamanData::UNDULATION_BONUS_PCT));
            SetHitHeal(heal);
        }

        if (!IsHealingWave() || !player->HasAura(ShamanData::SPELL_TIDAL_FORCE_AURA))
            return;

        // At OnEffectHitTarget the heal is pre-crit; re-derive the crit the way the engine applies it next
        uint32 amount = uint32(std::max(heal, 0));
        if (amount && DidCritTarget(GetSpell(), target))
            amount = Unit::SpellCriticalHealingBonus(player, GetSpellInfo(), amount, nullptr);

        ScheduleEcho(player, target, int32(CalculatePct(amount, uint32(ShamanData::TF_ECHO_PCT))));
    }

    void HandleAfterHit()
    {
        if (_hitDone)
            return;

        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        _hitDone = true;

        if (!IsHealingWave() && player->HasAura(ShamanData::SPELL_TIDAL_FORCE_AURA) && target->IsAlive())
            player->CastSpell(target, ShamanData::SPELL_TIDAL_FORCE_STACK, true);

        if (DidCritTarget(GetSpell(), target))
            TryTidalMasteryExtension(player, uint32(IsHealingWave() ? ShamanData::TM_EXT_HW_MS :
                ShamanData::TM_EXT_LHW_MS));
    }

    void HandleAfterCast()
    {
        if (Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster()))
            Shaman::ConsumeTidalWaves(player);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_sha_resto_healing_wave::HandleBeforeCast);
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_healing_wave::HandleHeal, EFFECT_0, SPELL_EFFECT_HEAL);
        AfterHit += SpellHitFn(spell_sha_resto_healing_wave::HandleAfterHit);
        AfterCast += SpellCastFn(spell_sha_resto_healing_wave::HandleAfterCast);
    }
};

// 202654 Tidal Force castable (talent 582, replaces 55198 which stays stock and unbound from
// spell_sha_tidal_force_dummy): its DUMMY (eff0, on the caster) applies the caster aura (10 s: Healing Rain +50%
// duration, Chain Heal no falloff by data; the echo, the Lesser Healing Wave stack and the Tidal Mastery extension read
// it from spell_sha_resto_healing_wave / _chain_heal / _riptide). Off the GCD, 2 min (Cooldown Haste, Tidal Mastery's
// cut) by data.
class spell_sha_resto_tidal_force : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_tidal_force);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_TIDAL_FORCE_AURA });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (Unit* target = GetHitUnit())
            target->CastSpell(target, ShamanData::SPELL_TIDAL_FORCE_AURA, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_tidal_force::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 5394 Healing Stream Totem - Improved Healing Stream capstone (rank 3): the placement count shows as the counter
// buff; the IHS_PLACEMENTS-th placement summons the Healing Tide Totem instead (SPELLVALUE_MISCVALUE0 swap of the
// summon entry, A27: same properties, slot, duration and cooldown) and resets the count. Player casts only.
class spell_sha_resto_healing_stream_totem : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_healing_stream_totem);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_HEALING_TIDE_COUNTER });
    }

    void HandleBeforeCast()
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        if (!player || !HasFullTalent(player, IMPROVED_HEALING_STREAM_RANKS))
            return;

        uint32 const placements = GetAuraCount(player, ShamanData::SPELL_HEALING_TIDE_COUNTER) + 1;
        if (placements < uint32(ShamanData::IHS_PLACEMENTS))
        {
            SetAuraCount(player, ShamanData::SPELL_HEALING_TIDE_COUNTER, placements);
            return;
        }

        player->RemoveAurasDueToSpell(ShamanData::SPELL_HEALING_TIDE_COUNTER);
        GetSpell()->SetSpellValue(SPELLVALUE_MISCVALUE0, int32(ShamanData::NPC_HEALING_TIDE_TOTEM));
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_sha_resto_healing_stream_totem::HandleBeforeCast);
    }
};

// 8170 Cleansing Totem - Tidal Focus capstone (rank 3): placing it also removes TIDAL_FOCUS_CLEANSE_COUNT disease and
// poison effects from each party member within TIDAL_FOCUS_CLEANSE_RADIUS_YD (the helper spell does the dispels), on
// top of the totem's own first pulse. Player casts only.
class spell_sha_resto_cleansing_totem : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_cleansing_totem);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_TIDAL_FOCUS_CLEANSE });
    }

    void HandleAfterCast()
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        if (!player || !HasFullTalent(player, TIDAL_FOCUS_RANKS))
            return;

        float const radius = float(ShamanData::TIDAL_FOCUS_CLEANSE_RADIUS_YD);
        std::vector<Player*> members = { player };
        if (Group* group = player->GetGroup())
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player* member = ref->GetSource())
                    if (member != player && member->IsInMap(player) && player->IsInSameGroupWith(member))
                        members.push_back(member);

        for (Player* member : members)
            if (member->IsAlive() && player->IsWithinDistInMap(member, radius))
                player->CastSpell(member, ShamanData::SPELL_TIDAL_FOCUS_CLEANSE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_sha_resto_cleansing_totem::HandleAfterCast);
    }
};

// 39610 Mana Tide Totem pulse (replaces spell_sha_mana_tide_totem): each party member the totem's pulse reaches gets
// MANA_TIDE_PARTY_PCT_X10 / 10 % of its maximum mana, the owning shaman MANA_TIDE_SELF_PCT %, both x (1 + Restorative
// Totems %), and the visible "Mana restored over time." aura. A non-player owner keeps the stock effect value.
class spell_sha_resto_mana_tide_totem : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_mana_tide_totem);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MANA_TIDE_ENERGIZE, ShamanData::SPELL_MANA_TIDE_PARTY_AURA });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* totem = GetCaster();
        Unit* target = GetHitUnit();
        if (!totem || !target || !target->IsAlive() || !target->HasActivePowerType(POWER_MANA))
            return;

        float pct = float(GetEffectValue());
        Player* owner = Shaman::GetOwningPlayer(totem);
        if (owner)
        {
            pct = target == owner ? float(ShamanData::MANA_TIDE_SELF_PCT) :
                float(ShamanData::MANA_TIDE_PARTY_PCT_X10) / 10.0f;
            AddPct(pct, GetRestorativeTotemsPct(owner));
        }

        int32 amount = int32(CalculatePct(float(target->GetMaxPower(POWER_MANA)), pct));
        if (amount > 0)
            totem->CastCustomSpell(target, SPELL_MANA_TIDE_ENERGIZE, &amount, nullptr, nullptr, true);

        // The marker's DUMMY targets its caster, so the member puts it on itself (refreshed by every pulse)
        if (owner)
            target->CastSpell(target, ShamanData::SPELL_MANA_TIDE_PARTY_AURA, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_mana_tide_totem::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -974 Earth Shield (replaces spell_sha_earth_shield; the stock heal path is kept as is). The per-charge amount is
// fixed at application through SpellHealingBonusDone, which already carries the caster's healing-done multiplier
// (Totemic Resonance's MOD_HEALING_DONE_PERCENT, Versatility) and the d1 b10 SpellMods (Healing Way, Improved Earth
// Shield, Purification): 379 ignores caster modifiers, so nothing is added at heal time. Improved Earth Shield
// capstone (rank 3 with Tidal Waves rank 3): an Earth Shield heal grants the shaman IES_TIDAL_WAVES_GRANT Tidal
// Waves charge, at most once per IES_TW_ICD_MS.
class spell_sha_resto_earth_shield : public AuraScript
{
    PrepareAuraScript(spell_sha_resto_earth_shield);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_EARTH_SHIELD_HEAL, SPELL_GLYPH_OF_EARTH_SHIELD });
    }

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        int32 baseAmount = amount;
        amount = caster->SpellHealingBonusDone(GetUnitOwner(), GetSpellInfo(), amount, HEAL, aurEff->GetEffIndex());

        // Glyph of Earth Shield (stock workaround: the glyph is a proc)
        if (AuraEffect const* glyph = caster->GetAuraEffect(SPELL_GLYPH_OF_EARTH_SHIELD, EFFECT_0))
            AddPct(amount, glyph->GetAmount());

        // Improved Shields (stock): raises the bonus part only
        if ((baseAmount = amount - baseAmount))
            if (AuraEffect const* improvedShields = caster->GetAuraEffect(SPELL_AURA_ADD_PCT_MODIFIER,
                SPELLFAMILY_SHAMAN, SPELL_ICON_IMPROVED_SHIELDS, EFFECT_1))
            {
                ApplyPct(baseAmount, improvedShields->GetAmount());
                amount += baseAmount;
            }
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        return !GetTarget()->HasSpellCooldown(SPELL_EARTH_SHIELD_HEAL);
    }

    void TryTidalWavesCapstone()
    {
        Unit* caster = GetCaster();
        Player* shaman = caster ? caster->ToPlayer() : nullptr;
        if (!shaman || !HasFullTalent(shaman, IMPROVED_EARTH_SHIELD_RANKS) || !HasFullTalent(shaman, TIDAL_WAVES_RANKS))
            return;

        RestorationScriptState* state = GetState(shaman);
        uint32 const now = NowMs();
        if (now < state->earthShieldWavesReadyMs)
            return;

        state->earthShieldWavesReadyMs = now + uint32(ShamanData::IES_TW_ICD_MS);
        Shaman::GrantTidalWaves(shaman, IES_TIDAL_WAVES_GRANT);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        SpellCastResult const result = target->CastCustomSpell(SPELL_EARTH_SHIELD_HEAL, SPELLVALUE_BASE_POINT0,
            aurEff->GetAmount(), target, true, nullptr, aurEff, GetCasterGUID());
        target->AddSpellCooldown(SPELL_EARTH_SHIELD_HEAL, 0, EARTH_SHIELD_HEAL_THROTTLE_MS);

        if (result == SPELL_CAST_OK)
            TryTidalWavesCapstone();
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sha_resto_earth_shield::CalculateAmount, EFFECT_0,
            SPELL_AURA_DUMMY);
        DoCheckProc += AuraCheckProcFn(spell_sha_resto_earth_shield::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sha_resto_earth_shield::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 52759 Ancestral Awakening (proc; replaces spell_sha_ancestral_awakening_proc): the spirit heals the lowest-percent
// player of the shaman's party or raid within AA_RADIUS_YD (the shaman included, never a pet). The heal (52752) is
// stock: family 0, ignores caster modifiers, triggered, so it rolls nothing.
class spell_sha_resto_ancestral_awakening_proc : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_ancestral_awakening_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_ANCESTRAL_AWAKENING_HEAL });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        targets.clear();
        if (!caster)
            return;

        std::vector<Unit*> picks;
        Heal::SelectMostInjured(caster, caster, float(ShamanData::AA_RADIUS_YD), 1, picks);
        if (!picks.empty())
            targets.push_back(picks.front());
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 amount = GetEffectValue();
        caster->CastCustomSpell(target, SPELL_ANCESTRAL_AWAKENING_HEAL, &amount, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(
            spell_sha_resto_ancestral_awakening_proc::FilterTargets, EFFECT_0, TARGET_UNIT_CASTER_AREA_RAID);
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_ancestral_awakening_proc::HandleDummy, EFFECT_0,
            SPELL_EFFECT_DUMMY);
    }
};

// -16180 Improved Water Shield (replaces spell_sha_imp_water_shield; the stock orb clause is gone). Capstone (rank 3):
// a critical direct heal of the shaman's own (the spell_proc row: Healing Wave, Lesser Healing Wave, Chain Heal,
// Riptide; HIT phase, crit) restores IWS_CAPSTONE_MANA_PCT% of maximum mana, once per cast, never from a periodic,
// triggered, totem or pet heal. Ranks 1-2 have no proc of their own.
class spell_sha_resto_imp_water_shield : public AuraScript
{
    PrepareAuraScript(spell_sha_resto_imp_water_shield);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_WATER_SHIELD_ENERGIZE });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    CastGuard _guard;

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (GetId() != ShamanData::SPELL_IMPROVED_WATER_SHIELD_16198)
            return false;

        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        Spell const* procSpell = eventInfo.GetProcSpell();
        if (!player || !procSpell || procSpell->IsTriggered() || !eventInfo.GetHealInfo())
            return false;

        if ((eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) || !(eventInfo.GetHitMask() & PROC_HIT_CRITICAL))
            return false;

        return _guard.Claim(procSpell);
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        // The energize is ENERGIZE_PCT carrying IWS_CAPSTONE_MANA_PCT itself (stored 0 = 1% of maximum mana)
        if (Player* player = GetUnitOwner()->ToPlayer())
            player->CastSpell(player, ShamanData::SPELL_WATER_SHIELD_ENERGIZE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_resto_imp_water_shield::CheckProc);
        OnProc += AuraProcFn(spell_sha_resto_imp_water_shield::HandleProc);
    }
};

// -30881 Nature's Guardian (replaces spell_sha_nature_guardian; the stock threat drop and 10% heal are gone).
// Capstone (rank 2): a damaging non-periodic hit (triggered ones too: PROC_ATTR_TRIGGERED_CAN_PROC on the row) that
// takes the shaman from at or above NG_THRESHOLD_PCT to below it heals the shaman (100 potency, a plain cast so the
// potency applies) and grants the guaranteed Nature crit buff. The 30 s internal cooldown is the spell_proc row's.
class spell_sha_resto_nature_guardian : public AuraScript
{
    PrepareAuraScript(spell_sha_resto_nature_guardian);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_NATURES_GUARDIAN_HEAL, ShamanData::SPELL_NATURES_GUARDIAN_CRIT });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (GetId() != ShamanData::SPELL_NATURE_S_GUARDIAN_30883)
            return false;

        Unit* shaman = GetTarget();
        if (!shaman->IsAlive() || eventInfo.GetActionTarget() != shaman)
            return false;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || !damageInfo->GetDamage() || damageInfo->GetDamageType() == DOT ||
            (eventInfo.GetTypeMask() & PROC_FLAG_TAKEN_PERIODIC))
            return false;

        // The proc runs after the damage landed: this hit crossed the threshold
        uint64 const threshold = shaman->CountPctFromMaxHealth(int32(ShamanData::NG_THRESHOLD_PCT));
        uint64 const health = shaman->GetHealth();
        return health < threshold && health + damageInfo->GetDamage() >= threshold;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* shaman = GetTarget();
        shaman->CastSpell(shaman, ShamanData::SPELL_NATURES_GUARDIAN_HEAL, TRIGGERED_FULL_MASK);
        shaman->CastSpell(shaman, ShamanData::SPELL_NATURES_GUARDIAN_CRIT, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_resto_nature_guardian::CheckProc);
        OnProc += AuraProcFn(spell_sha_resto_nature_guardian::HandleProc);
    }
};

// Cloudburst Totem castable (known-hard 1): no DBC cooldown. While the player's Cloudburst totem holds the Air slot,
// casting it again recalls it: Shaman::ReleaseCloudburst releases the store, unsummons the totem and sets the
// cooldown, and CheckCast returns SPELL_FAILED_DONT_REPORT so no GCD, cost or cooldown starts (0-verify X6: bot probes
// never run script CheckCast). The placement record and the store buff come from Shaman::OnPlayerTotemAdded.
class spell_sha_resto_cloudburst : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_cloudburst);

    SpellCastResult HandleCheckCast()
    {
        Player* player = GetUntriggeredPlayerCaster(GetSpell(), GetCaster());
        if (!player)
            return SPELL_CAST_OK;

        ObjectGuid const totemGuid = player->m_SummonSlot[SUMMON_SLOT_TOTEM_AIR];
        Creature* totem = totemGuid.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*player, totemGuid);
        if (!totem || totem->GetEntry() != ShamanData::NPC_CLOUDBURST_TOTEM)
            return SPELL_CAST_OK;

        Shaman::ReleaseCloudburst(player, false);
        return SPELL_FAILED_DONT_REPORT;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_sha_resto_cloudburst::HandleCheckCast);
    }
};

// Cloudburst store buff: the shaman's own effective Nature healing (direct and periodic, never the release itself)
// goes into the store (Shaman::AddCloudburstStore takes CLOUDBURST_STORE_PCT); totem and Water Elemental heals are
// stored by the OnHeal hook in shaman_hooks.cpp. Removed by the shaman's death: the store is discarded. Every other
// removal (expiry, recall, Totemic Recall, Air replacement) is driven by the totem's removal, never from here.
class spell_sha_resto_cloudburst_store : public AuraScript
{
    PrepareAuraScript(spell_sha_resto_cloudburst_store);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_CLOUDBURST_RELEASE });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcPlayer(GetUnitOwner(), eventInfo))
            return false;

        HealInfo* healInfo = eventInfo.GetHealInfo();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!healInfo || !healInfo->GetEffectiveHeal() || !spellInfo ||
            spellInfo->Id == ShamanData::SPELL_CLOUDBURST_RELEASE)
            return false;

        return (healInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_NATURE) != 0;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        if (Player* player = GetUnitOwner()->ToPlayer())
            Shaman::AddCloudburstStore(player, eventInfo.GetHealInfo()->GetEffectiveHeal());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        if (Player* player = GetTarget()->ToPlayer())
            Shaman::ReleaseCloudburst(player, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_resto_cloudburst_store::CheckProc);
        OnProc += AuraProcFn(spell_sha_resto_cloudburst_store::HandleProc);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_resto_cloudburst_store::HandleRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// Undulating Currents Totem heal (cast by the totem at the lowest-percent player in range): the engine's chain search
// picks the highest absolute deficit and includes pets (0-verify X4), so the jump list is rebuilt here: from the
// primary, each jump takes the lowest-percent injured player within the chain-heal jump radius of the previous target,
// in line of sight, never the primary or a pet (the list order is the jump order, so the falloff follows it). A
// totem without a player owner keeps the engine's list.
class spell_sha_resto_undulating_heal : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_undulating_heal);

    void FilterJumps(std::list<WorldObject*>& targets)
    {
        Player* owner = Shaman::GetOwningPlayer(GetCaster());
        if (!owner)
            return;

        targets.clear();

        Unit* primary = GetExplTargetUnit();
        uint32 const chainTargets = GetSpellInfo()->Effects[EFFECT_0].ChainTarget;
        if (!primary || chainTargets < 2)
            return;

        uint32 const jumps = chainTargets - 1;
        float const jumpRadius = GetSpellInfo()->JumpDistance > 0.0f ? GetSpellInfo()->JumpDistance :
            CHAIN_HEAL_JUMP_RADIUS_YD;

        // Lowest health percent first (stable), players only, the primary excluded
        std::vector<Unit*> pool;
        Heal::SelectMostInjured(owner, primary, jumpRadius * float(jumps), std::numeric_limits<uint8>::max(), pool,
            primary);

        WorldObject const* source = primary;
        for (uint32 i = 0; i < jumps; ++i)
        {
            auto next = std::find_if(pool.begin(), pool.end(), [source, jumpRadius](Unit const* unit)
            {
                return unit->IsAlive() && !unit->IsFullHealth() && source->IsWithinDist(unit, jumpRadius) &&
                    source->IsWithinLOSInMap(unit);
            });

            if (next == pool.end())
                break;

            targets.push_back(*next);
            source = *next;
            pool.erase(next);
        }
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_resto_undulating_heal::FilterJumps,
            EFFECT_0, TARGET_UNIT_TARGET_CHAINHEAL_ALLY);
    }
};

// Totemic Resonance aura: its periodic dummy (TR_REFRESH_MS) keeps the stack count and the amount in line with the
// totem slots and the live Mastery (Shaman::RecountTotemicResonance changes an effect only when it moved).
class spell_sha_resto_totemic_resonance : public AuraScript
{
    PrepareAuraScript(spell_sha_resto_totemic_resonance);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetUnitOwner()->ToPlayer())
            Shaman::RecountTotemicResonance(player);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_resto_totemic_resonance::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 202277 Water Bolt heal (cast by the Water Elemental guardian): the owner's Totemic Resonance cannot reach a
// guardian's heal through the aura (a guardian reads its own healing-done auras, 0-verify item 6), so the heal is
// multiplied here, live. Tidecaller and Purification reach it by SpellMod (d2 b24).
class spell_sha_resto_water_bolt_heal : public SpellScript
{
    PrepareSpellScript(spell_sha_resto_water_bolt_heal);

    void HandleHeal(SpellEffIndex /*effIndex*/)
    {
        Player* owner = Shaman::GetOwningPlayer(GetCaster());
        if (!owner)
            return;

        float const pct = Shaman::GetTotemicResonancePct(owner);
        if (pct <= 0.0f)
            return;

        SetHitHeal(int32(float(GetHitHeal()) * (1.0f + pct / 100.0f)));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_sha_resto_water_bolt_heal::HandleHeal, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

void AddSC_shaman_restoration_spell_scripts()
{
    RegisterSpellScript(spell_sha_resto_riptide);
    RegisterSpellScript(spell_sha_resto_chain_heal);
    RegisterSpellScript(spell_sha_resto_healing_wave);
    RegisterSpellScript(spell_sha_resto_tidal_force);
    RegisterSpellScript(spell_sha_resto_healing_stream_totem);
    RegisterSpellScript(spell_sha_resto_cleansing_totem);
    RegisterSpellScript(spell_sha_resto_mana_tide_totem);
    RegisterSpellScript(spell_sha_resto_earth_shield);
    RegisterSpellScript(spell_sha_resto_ancestral_awakening_proc);
    RegisterSpellScript(spell_sha_resto_imp_water_shield);
    RegisterSpellScript(spell_sha_resto_nature_guardian);
    RegisterSpellScript(spell_sha_resto_cloudburst);
    RegisterSpellScript(spell_sha_resto_cloudburst_store);
    RegisterSpellScript(spell_sha_resto_undulating_heal);
    RegisterSpellScript(spell_sha_resto_totemic_resonance);
    RegisterSpellScript(spell_sha_resto_water_bolt_heal);
}
