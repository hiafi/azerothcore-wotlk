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

#include "WarlockMechanics.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <vector>

/*
 * WP-B bodies (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5/§6,
 * warlock-rework.AFFLICTION.md §7 for the per-clause mapping, §0.4 item 9 for
 * AddSC_warlock_hooks()'s name). Call sites: the one Unit.cpp/SpellInfo.cpp line (Warlock::IsBane,
 * B14) and script call sites in spell_warlock_affliction.cpp / warlock_hooks.cpp for everything
 * else.
 *
 * Everything below the anonymous namespace is `namespace Warlock` (the frozen header's contract).
 * The anonymous namespace holds pure implementation detail: per-player state maps, cross-spec ids
 * this pass references but doesn't own (Destruction's/Demonology's future spell ids, pre-assigned
 * in SHARED.md - referencing the literal is safe, the spells not existing yet just makes a lookup
 * miss), and small local helpers shared by more than one exported function.
 */

namespace
{
    // ------------------------------------------------------------------
    // Soul Shards (B9, AFFLICTION.md §7.10) - per-player deque of expiry timestamps (game-time ms,
    // Priest tentacle-ICD precedent, PriestMechanics.cpp:748). Each shard independently expires
    // 120 s after it was granted; the visible buff's stack count and remaining duration mirror the
    // deque (Mage Ignite display-stack precedent).
    // ------------------------------------------------------------------
    constexpr uint32 SOUL_SHARD_DURATION_MS = 120000;
    constexpr uint8 SOUL_SHARD_MAX = 5;

    std::unordered_map<ObjectGuid, std::deque<uint32>> soulShardExpiryByPlayer;

    // Prunes expired entries; if the deque is empty (never touched this process, or just drained)
    // and the buff aura is still up with N stacks / D ms left (a relog - the deque is per-process,
    // not persisted), rebuilds N entries all expiring at now + D. Approximation accepted in
    // AFFLICTION.md §7.10/§12: every shard from before the relog gets the same remaining time.
    void NormalizeSoulShards(Player* player, std::deque<uint32>& shards)
    {
        uint32 const now = uint32(GameTime::GetGameTimeMS().count());

        if (shards.empty())
        {
            if (Aura const* aura = player->GetAura(Warlock::SPELL_SOUL_SHARD_BUFF))
            {
                uint8 const stacks = aura->GetStackAmount();
                uint32 const expiry = now + uint32(std::max(0, aura->GetDuration()));
                for (uint8 i = 0; i < stacks; ++i)
                    shards.push_back(expiry);
            }
            return;
        }

        while (!shards.empty() && shards.front() <= now)
            shards.pop_front();
    }

    // Mirrors the deque's size/soonest-to-outlast-remaining-time onto the visible buff (200709).
    void SyncSoulShardBuff(Player* player, std::deque<uint32> const& shards)
    {
        if (shards.empty())
        {
            player->RemoveAurasDueToSpell(Warlock::SPELL_SOUL_SHARD_BUFF);
            return;
        }

        uint32 const now = uint32(GameTime::GetGameTimeMS().count());
        uint32 const latestExpiry = shards.back();
        int32 const remaining = int32(latestExpiry > now ? latestExpiry - now : 0);

        Aura* aura = player->GetAura(Warlock::SPELL_SOUL_SHARD_BUFF);
        if (!aura)
            aura = player->AddAura(Warlock::SPELL_SOUL_SHARD_BUFF, player);
        if (!aura)
            return;

        aura->SetStackAmount(uint8(shards.size()));
        aura->SetMaxDuration(remaining);
        aura->SetDuration(remaining);
    }

    // ------------------------------------------------------------------
    // Instant-cast priority arbiter (SHARED §4's "Arbiter timing contract"). The registry is empty
    // in this pass - Destruction/Demonology populate it in S2/S3 - so OnPrepareGrantInstantCast
    // never actually finds a ready source yet, but the mechanism has to be complete now.
    // ------------------------------------------------------------------

    // Destruction's data row (S2, SHARED §1.3): -100% cast time, 1 charge, no spell_proc row. Not
    // declared this pass - referenced here only so the arbiter can grant/consume it once a source
    // registers.
    constexpr uint32 SPELL_INSTANT_CAST_HELPER = 200713;

    struct InstantCastSourceEntry
    {
        Warlock::InstantCastSource source;
        std::function<bool(Player*)> isReady;
        std::function<void(Player*)> onConsumed;
    };

    struct InstantCastGrant
    {
        uint32 spellId = 0;
        Warlock::InstantCastSource source = Warlock::InstantCastSource::EmpoweredImp;
    };

    std::unordered_map<uint32, std::vector<InstantCastSourceEntry>> instantCastRegistry;
    std::unordered_map<ObjectGuid, InstantCastGrant> instantCastGrantByPlayer;

    // ------------------------------------------------------------------
    // Leech-talent exclusivity (SHARED §4). Soul Leech (Destruction, stock ids) and Fel Immolation
    // (Demonology, minted at these SHARED-pre-assigned ids in S3) aren't Affliction's to declare in
    // WarlockMechanics.h, but GetActiveLeechTalent must compare every source from this pass on - a
    // HasTalent() miss on a not-yet-minted id is just `false`, so referencing the literal now is
    // safe and avoids a second edit to this function in S2/S3.
    // ------------------------------------------------------------------
    constexpr uint32 SPELL_SOUL_LEECH_R1 = 30293;
    constexpr uint32 SPELL_SOUL_LEECH_R2 = 30295;
    constexpr uint32 SPELL_SOUL_LEECH_R3 = 30296;
    constexpr uint32 SPELL_FEL_IMMOLATION_R1 = 200874;
    constexpr uint32 SPELL_FEL_IMMOLATION_R2 = 200875;
    constexpr uint32 SPELL_FEL_IMMOLATION_R3 = 200876;
    constexpr uint32 SPELL_BLAZING_SPEED_R1 = 31641;
    constexpr uint32 SPELL_BLAZING_SPEED_R2 = 31642;
    constexpr uint32 SPELL_BLAZING_SPEED_R3 = 200107;

    // Highest known rank's leech % among a talent's own ranks (ranks are mutually exclusive - only
    // one is ever known at once), 0 if the talent isn't taken at all.
    float GetKnownLeechPct(Player const* player, std::initializer_list<std::pair<uint32, float>> ranksHighestFirst)
    {
        for (auto const& rank : ranksHighestFirst)
            if (player->HasTalent(rank.first, player->GetActiveSpec()))
                return rank.second;
        return 0.0f;
    }

    // Seed of Corruption's own visual (stock spell_warlock.cpp precedent) - played once whenever a
    // Seed detonates, whichever script (chain-fix or death) triggers it.
    constexpr uint32 SPELL_SEED_OF_CORRUPTION_VISUAL = 37826;

    // ------------------------------------------------------------------
    // Soul Swap (AFFLICTION.md §7.9) - per-player copy store. Keyed by the inhaling player's GUID;
    // one copy at a time (a second Inhale before an Exhale simply replaces the pending copy).
    // ------------------------------------------------------------------
    struct SoulSwapStore
    {
        ObjectGuid sourceGuid;
        std::vector<Warlock::SoulSwapEntry> entries;
    };

    std::unordered_map<ObjectGuid, SoulSwapStore> soulSwapByPlayer;

    // ------------------------------------------------------------------
    // Destruction pass (S2) additions - local implementation detail only, not part of the frozen
    // header contract (DESTRUCTION.md §2.6's "WarlockMechanics additions"). Stock/talent ids this
    // pass needs that weren't minted new (so the frozen header doesn't name them) are duplicated
    // here rather than widening WarlockMechanics.h - same shape as this file's own
    // SPELL_SEED_OF_CORRUPTION_VISUAL above.
    // ------------------------------------------------------------------
    constexpr uint32 SPELL_DESTRUCTIVE_REACH_R2 = 17918;   // capstone rank - the >20 yd crit clause
    constexpr uint32 SPELL_HELLFIRE = 1949;

    // Hellstorm's per-player scheduling generation counter (DESTRUCTION.md §7.4; Flourish /
    // Druid::AccelerateHotTicks precedent, DruidMechanics.cpp:701-767, adapted for a 1.5x rate -
    // one extra tick every 2 x amplitude instead of Flourish's every-amplitude doubling). Bumped
    // every time StartHellstormAcceleration finds a fresh Hellfire aura to drive, so a chain
    // started by the other starter script (or an earlier Hellfire cast) recognizes itself as
    // superseded and stops instead of injecting a second, overlapping set of extra ticks.
    std::unordered_map<ObjectGuid, uint32> hellstormGenerationByPlayer;

    void ScheduleHellstormTick(ObjectGuid playerGuid, uint32 generation, int32 amplitude, int32 offsetMs)
    {
        Player* player = ObjectAccessor::FindPlayer(playerGuid);
        if (!player)
            return;

        player->m_Events.AddEventAtOffset([playerGuid, generation, amplitude]()
        {
            Player* self = ObjectAccessor::FindPlayer(playerGuid);
            if (!self)
                return;

            auto itr = hellstormGenerationByPlayer.find(playerGuid);
            if (itr == hellstormGenerationByPlayer.end() || itr->second != generation)
                return;

            if (!self->HasAura(Warlock::SPELL_HELLSTORM_BUFF))
                return;

            Warlock::FirePeriodicTickNow(self, playerGuid, SPELL_HELLFIRE, EFFECT_0);

            // 1.5x rate: one extra tick every 2 regular intervals, not every one (a 2x-rate,
            // every-amplitude schedule like Flourish's would double the tick count instead of the
            // specced 50% faster).
            ScheduleHellstormTick(playerGuid, generation, amplitude, 2 * amplitude);
        }, Milliseconds(offsetMs));
    }
}

namespace Warlock
{
    // ------------------------------------------------------------------
    // B14 bane slot
    // ------------------------------------------------------------------
    bool IsBane(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;

        // Demonology adds Bane of Doom's id here in S3 (PLAN B14) - a short id list rather than a
        // single-id compare so that pass only needs one more `case`.
        switch (spellInfo->Id)
        {
            case SPELL_BANE_OF_AGONY:
                return true;
            default:
                return false;
        }
    }

    // ------------------------------------------------------------------
    // Soul Shards (B9)
    // ------------------------------------------------------------------
    void GrantSoulShard(Player* player)
    {
        if (!player)
            return;

        std::deque<uint32>& shards = soulShardExpiryByPlayer[player->GetGUID()];
        NormalizeSoulShards(player, shards);

        if (shards.size() < SOUL_SHARD_MAX)
            shards.push_back(uint32(GameTime::GetGameTimeMS().count()) + SOUL_SHARD_DURATION_MS);

        SyncSoulShardBuff(player, shards);
    }

    void ConsumeSoulShards(Player* player, uint8 count)
    {
        if (!player || !count)
            return;

        auto itr = soulShardExpiryByPlayer.find(player->GetGUID());
        if (itr == soulShardExpiryByPlayer.end())
            return;

        NormalizeSoulShards(player, itr->second);

        for (uint8 i = 0; i < count && !itr->second.empty(); ++i)
            itr->second.pop_front();

        SyncSoulShardBuff(player, itr->second);
    }

    uint8 GetSoulShardCount(Player* player)
    {
        if (!player)
            return 0;

        std::deque<uint32>& shards = soulShardExpiryByPlayer[player->GetGUID()];
        NormalizeSoulShards(player, shards);
        SyncSoulShardBuff(player, shards);
        return uint8(shards.size());
    }

    void ClearSoulShards(Player* player)
    {
        if (!player)
            return;

        // Deque only (§11 Q9: shards drop on death) - the buff aura itself is removed by the
        // engine because it carries no keep-while-dead attribute; the caller resyncs separately.
        soulShardExpiryByPlayer.erase(player->GetGUID());
    }

    // ------------------------------------------------------------------
    // Soulburn (B10)
    // ------------------------------------------------------------------
    bool TryConsumeSoulburnMarker(Player* caster)
    {
        if (!caster || !caster->HasAura(SPELL_SOULBURN_MARKER))
            return false;

        caster->RemoveAurasDueToSpell(SPELL_SOULBURN_MARKER);
        return true;
    }

    // ------------------------------------------------------------------
    // Instant-cast priority arbiter
    // ------------------------------------------------------------------
    void RegisterInstantCastSource(uint32 baseSpellId, InstantCastSource source,
                                    std::function<bool(Player*)> isReady,
                                    std::function<void(Player*)> onConsumed)
    {
        instantCastRegistry[baseSpellId].push_back({ source, std::move(isReady), std::move(onConsumed) });
    }

    void OnPrepareGrantInstantCast(Player* caster, Spell* spell)
    {
        if (!caster || !spell || !spell->m_spellInfo)
            return;

        if (spell->IsTriggered())
            return;

        uint32 const spellId = spell->m_spellInfo->Id;
        auto itr = instantCastRegistry.find(spellId);
        if (itr == instantCastRegistry.end())
            return;

        // Timing contract item 1: no non-melee cast already in progress unless this spell allows
        // casting while casting (Spell.cpp:3626's own check, mirrored here).
        if (caster->IsNonMeleeSpellCast(false, true, true) &&
            !spell->m_spellInfo->HasAttribute(SPELL_ATTR4_ALLOW_CAST_WHILE_CASTING))
            return;

        // Strip a stale helper from an earlier failed attempt before granting a fresh one.
        caster->RemoveAurasDueToSpell(SPELL_INSTANT_CAST_HELPER);
        instantCastGrantByPlayer.erase(caster->GetGUID());

        for (InstantCastSourceEntry const& entry : itr->second)
        {
            if (entry.isReady && entry.isReady(caster))
            {
                caster->CastSpell(caster, SPELL_INSTANT_CAST_HELPER, true);
                instantCastGrantByPlayer[caster->GetGUID()] = { spellId, entry.source };
                return;
            }
        }
    }

    void OnCastConsumeInstantCast(Player* caster, Spell* spell)
    {
        if (!caster || !spell || !spell->m_spellInfo)
            return;

        auto grantItr = instantCastGrantByPlayer.find(caster->GetGUID());
        if (grantItr == instantCastGrantByPlayer.end())
            return;

        if (grantItr->second.spellId != spell->m_spellInfo->Id)
            return;

        uint32 const baseSpellId = grantItr->second.spellId;
        InstantCastSource const source = grantItr->second.source;
        instantCastGrantByPlayer.erase(grantItr);

        auto regItr = instantCastRegistry.find(baseSpellId);
        if (regItr == instantCastRegistry.end())
            return;

        for (InstantCastSourceEntry const& entry : regItr->second)
        {
            if (entry.source == source)
            {
                if (entry.onConsumed)
                    entry.onConsumed(caster);
                break;
            }
        }
    }

    // ------------------------------------------------------------------
    // Leech talents
    // ------------------------------------------------------------------
    LeechTalent GetActiveLeechTalent(Player const* player)
    {
        if (!player)
            return LeechTalent::None;

        // Fel Concentration only leeches on its capstone rank (SHARED §4: "17785 only").
        float const felConcentrationPct =
            player->HasTalent(SPELL_FEL_CONCENTRATION_R3, player->GetActiveSpec()) ? 20.0f : 0.0f;

        float const soulLeechPct = GetKnownLeechPct(player,
            { { SPELL_SOUL_LEECH_R3, 15.0f }, { SPELL_SOUL_LEECH_R2, 10.0f }, { SPELL_SOUL_LEECH_R1, 5.0f } });
        float const felImmolationPct = GetKnownLeechPct(player,
            { { SPELL_FEL_IMMOLATION_R3, 9.0f }, { SPELL_FEL_IMMOLATION_R2, 6.0f },
              { SPELL_FEL_IMMOLATION_R1, 3.0f } });
        float const siphonLifePct = GetKnownLeechPct(player,
            { { SPELL_SIPHON_LIFE_R2, 4.0f }, { SPELL_SIPHON_LIFE_R1, 2.0f } });
        float const blazingSpeedPct = GetKnownLeechPct(player,
            { { SPELL_BLAZING_SPEED_R3, 3.0f }, { SPELL_BLAZING_SPEED_R2, 2.0f }, { SPELL_BLAZING_SPEED_R1, 1.0f } });

        std::array<std::pair<LeechTalent, float>, 5> candidates
        {{
            { LeechTalent::SoulLeech, soulLeechPct },
            { LeechTalent::FelConcentration, felConcentrationPct },
            { LeechTalent::FelImmolation, felImmolationPct },
            { LeechTalent::SiphonLife, siphonLifePct },
            { LeechTalent::BlazingSpeed, blazingSpeedPct }
        }};

        LeechTalent best = LeechTalent::None;
        float bestPct = 0.0f;
        for (auto const& candidate : candidates)
        {
            if (candidate.second > bestPct)
            {
                bestPct = candidate.second;
                best = candidate.first;
            }
        }

        return best;
    }

    void RefreshLeechTalents(Player* player)
    {
        if (!player)
            return;

        for (uint32 spellId : { SPELL_BLAZING_SPEED_R1, SPELL_BLAZING_SPEED_R2, SPELL_BLAZING_SPEED_R3 })
        {
            if (Aura* aura = player->GetOwnedAura(spellId))
                if (AuraEffect* effect = aura->GetEffect(EFFECT_1))
                    effect->RecalculateAmount();
        }
    }

    // ------------------------------------------------------------------
    // Pet/guardian proc-chance passthrough
    // ------------------------------------------------------------------
    float GetOwnerProcChanceMultiplier(Unit* petOrGuardian)
    {
        if (!petOrGuardian)
            return 1.0f;

        Unit* owner = petOrGuardian->GetOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player)
            return 1.0f;

        return 1.0f + player->GetProcChancePercentage() / 100.0f;
    }

    // ------------------------------------------------------------------
    // Extra periodic tick without desyncing the timer (Druid::AccelerateHotTicks precedent,
    // DruidMechanics.cpp:701-769, generalized to any periodic-effect aura type).
    // ------------------------------------------------------------------
    void FirePeriodicTickNow(Unit* target, ObjectGuid casterGuid, uint32 spellId, uint8 effIndex)
    {
        if (!target)
            return;

        Aura* aura = target->GetAura(spellId, casterGuid);
        if (!aura)
            return;

        AuraEffect* effect = aura->GetEffect(effIndex);
        if (!effect)
            return;

        // AFFLICTION.md §7.5: guard against re-applying the final-tick leftover multiplier to an
        // injected tick - not a cap on injected ticks in general, just this one edge.
        if (effect->GetTickNumber() >= uint32(effect->GetTotalTicks()))
            return;

        AuraApplication* application = aura->GetApplicationOfTarget(target->GetGUID());
        if (!application)
            return;

        effect->PeriodicTick(application, aura->GetCaster());
    }

    void ApplyDoneDamagePctMods(Unit const* /*caster*/, Unit const* /*victim*/, SpellInfo const* /*spellInfo*/,
                                DamageEffectType /*damagetype*/, float& /*doneTotalMod*/)
    {
        // Declared for API symmetry with Druid/Priest (SHARED §4) - no call site this pass. Every
        // Affliction clause with a done-damage-pct-style bonus has its own DoEffectCalcAmount or
        // SpellScript path (Mastery on Agony/UA, Compounding Darkness, Soul Siphon) - PLAN §2/§5.3,
        // CORE-AUDIT headline.
    }

    // ------------------------------------------------------------------
    // Affliction-local members
    // ------------------------------------------------------------------
    uint8 GetAgonyStackCap(Unit const* caster)
    {
        constexpr uint8 BASE_CAP = 10;
        if (!caster)
            return BASE_CAP;

        if (caster->HasAura(SPELL_IMPROVED_CURSES_R2))
            return BASE_CAP + 5;
        if (caster->HasAura(SPELL_IMPROVED_CURSES_R1))
            return BASE_CAP + 2;
        return BASE_CAP;
    }

    uint8 GetAgonyStacks(Unit const* target, ObjectGuid casterGuid)
    {
        if (!target)
            return 0;

        Aura const* aura = target->GetAura(SPELL_BANE_OF_AGONY_STACKS, casterGuid);
        return aura ? aura->GetStackAmount() : 0;
    }

    void AddAgonyStacks(Unit* caster, Unit* target, uint8 count)
    {
        if (!caster || !target || !count)
            return;

        uint8 const cap = GetAgonyStackCap(caster);
        Aura* aura = target->GetAura(SPELL_BANE_OF_AGONY_STACKS, caster->GetGUID());
        uint8 const current = aura ? aura->GetStackAmount() : 0;
        uint8 const newStack = uint8(std::min<int32>(int32(cap), int32(current) + int32(count)));

        if (!aura)
            aura = caster->AddAura(SPELL_BANE_OF_AGONY_STACKS, target);
        if (!aura)
            return;

        aura->SetStackAmount(newStack);
        // Data note (§5, 200720): "duration refreshed every stack" - harmless either way since the
        // stack aura's 60 s duration always outlives Bane of Agony's own (<= 24 s + Lingering
        // Agony), but keeping it explicit matches the written behaviour.
        aura->RefreshDuration();
    }

    bool IsAfflictionDot(uint32 spellId)
    {
        switch (spellId)
        {
            case SPELL_CORRUPTION:
            case SPELL_BANE_OF_AGONY:
            case SPELL_UNSTABLE_AFFLICTION:
            case SPELL_PHANTOM_SINGULARITY:
                return true;
            default:
                return false;
        }
    }

    uint8 CountAfflictionDots(Unit const* target, ObjectGuid casterGuid, uint32 excludeSpellId)
    {
        if (!target)
            return 0;

        uint8 count = 0;
        for (uint32 spellId : { SPELL_CORRUPTION, SPELL_BANE_OF_AGONY, SPELL_UNSTABLE_AFFLICTION,
                                 SPELL_PHANTOM_SINGULARITY })
        {
            if (spellId == excludeSpellId)
                continue;
            if (target->HasAura(spellId, casterGuid))
                ++count;
        }
        return count;
    }

    float GetSoulSiphonMultiplier(Unit const* caster, Unit const* target)
    {
        if (!caster || !target)
            return 1.0f;

        uint32 rankSpellId = 0;
        if (caster->HasAura(SPELL_SOUL_SIPHON_R2))
            rankSpellId = SPELL_SOUL_SIPHON_R2;
        else if (caster->HasAura(SPELL_SOUL_SIPHON_R1))
            rankSpellId = SPELL_SOUL_SIPHON_R1;

        if (!rankSpellId)
            return 1.0f;

        AuraEffect const* stepEff = caster->GetAuraEffect(rankSpellId, EFFECT_0);
        AuraEffect const* capEff = caster->GetAuraEffect(rankSpellId, EFFECT_1);
        if (!stepEff || !capEff)
            return 1.0f;

        uint8 const n = CountAfflictionDots(target, caster->GetGUID());
        int32 const bonus = std::min(stepEff->GetAmount() * int32(n), capEff->GetAmount());
        return 1.0f + float(bonus) / 100.0f;
    }

    void AddTaintedSoul(Unit* caster, Unit* target, uint8 stacks)
    {
        if (!caster || !target || !stacks)
            return;

        Aura* aura = target->GetAura(SPELL_TAINTED_SOUL, caster->GetGUID());
        uint8 const current = aura ? aura->GetStackAmount() : 0;
        uint8 const newStack = uint8(std::min<int32>(255, int32(current) + int32(stacks)));

        if (newStack >= 10)
        {
            if (aura)
                aura->Remove();
            EruptTaintedSoul(caster, target, 100);
            return;
        }

        if (!aura)
            aura = caster->AddAura(SPELL_TAINTED_SOUL, target);
        if (aura)
            aura->SetStackAmount(newStack);
    }

    void EruptTaintedSoul(Unit* caster, Unit* target, uint8 pct)
    {
        if (!caster || !target)
            return;

        SpellInfo const* eruption = sSpellMgr->AssertSpellInfo(SPELL_TAINTED_SOUL_ERUPTION);
        if (!eruption)
            return;

        SpellCastTargets targets;
        targets.SetDst(*target);

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT1, int32(pct));

        caster->CastSpell(targets, eruption, &values, TRIGGERED_FULL_MASK);
    }

    void DetonateSeed(Aura* seed)
    {
        if (!seed)
            return;

        Unit* caster = seed->GetCaster();
        Unit* owner = seed->GetOwner() ? seed->GetOwner()->ToUnit() : nullptr;
        if (!caster || !owner)
            return;

        AuraEffect* effect = seed->GetEffect(EFFECT_0);
        owner->CastSpell(owner, SPELL_SEED_OF_CORRUPTION_VISUAL, true, nullptr, effect);
        caster->CastSpell(owner, SPELL_SEED_OF_CORRUPTION_DETONATION, true, nullptr, effect);
        seed->Remove();
    }

    void StoreSoulSwap(Player* player, ObjectGuid sourceGuid, std::vector<SoulSwapEntry> entries)
    {
        if (!player)
            return;

        soulSwapByPlayer[player->GetGUID()] = { sourceGuid, std::move(entries) };
    }

    bool HasSoulSwapCopy(Player const* player, ObjectGuid* outSource)
    {
        if (!player)
            return false;

        auto itr = soulSwapByPlayer.find(player->GetGUID());
        if (itr == soulSwapByPlayer.end())
            return false;

        if (outSource)
            *outSource = itr->second.sourceGuid;
        return true;
    }

    bool TakeSoulSwap(Player* player, ObjectGuid& outSource, std::vector<SoulSwapEntry>& outEntries)
    {
        if (!player)
            return false;

        auto itr = soulSwapByPlayer.find(player->GetGUID());
        if (itr == soulSwapByPlayer.end())
            return false;

        outSource = itr->second.sourceGuid;
        outEntries = std::move(itr->second.entries);
        soulSwapByPlayer.erase(itr);
        return true;
    }

    // ------------------------------------------------------------------
    // Destruction pass (S2) additions (DESTRUCTION.md §7 for the per-clause mapping, §2.6 for the
    // "WarlockMechanics additions" list). Frozen signatures - see the header for the contract.
    // ------------------------------------------------------------------
    Unit* GetHavocTarget(Unit* caster)
    {
        if (!caster)
            return nullptr;

        for (Aura* aura : caster->GetSingleCastAuras())
            if (aura->GetId() == SPELL_HAVOC)
                return aura->GetUnitOwner();

        return nullptr;
    }

    float GetAuraStateDoneFactor(Unit const* caster, Unit const* victim, SpellInfo const* spellInfo)
    {
        if (!caster || !victim || !spellInfo)
            return 1.0f;

        // Mirrors the stock done-damage aurastate clause (Unit.cpp:8310-8313) exactly, so dividing
        // it back out of a snapshot and re-applying it live per target (Rain of Fire, §7.1) uses
        // the identical factor the engine itself would have used for a normal direct hit.
        return caster->GetTotalAuraMultiplier(SPELL_AURA_MOD_DAMAGE_DONE_VERSUS_AURASTATE,
            [victim, spellInfo, caster](AuraEffect const* aurEff)
            {
                return victim->HasAuraState(AuraStateType(aurEff->GetMiscValue())) &&
                       spellInfo->ValidateAttribute6SpellDamageMods(caster, aurEff, false);
            });
    }

    void StartHellstormAcceleration(Player* player)
    {
        if (!player)
            return;

        Aura* hellfire = player->GetAura(SPELL_HELLFIRE, player->GetGUID());
        if (!hellfire)
            return;

        AuraEffect* effect = hellfire->GetEffect(EFFECT_0);
        if (!effect || effect->GetAuraType() != SPELL_AURA_PERIODIC_TRIGGER_SPELL)
            return;

        int32 const amplitude = effect->GetAmplitude();
        if (amplitude <= 0)
            return;

        ObjectGuid const guid = player->GetGUID();
        uint32 const generation = ++hellstormGenerationByPlayer[guid];

        // Phase off the live tick timer (bugs-and-fixes: "Flourish doesn't visibly speed up HoT
        // ticks") - the midpoint of the next regular interval, then every 2 x amplitude.
        int32 firstOffset = effect->GetPeriodicTimer() - amplitude / 2;
        if (firstOffset < 0)
            firstOffset += amplitude;

        ScheduleHellstormTick(guid, generation, amplitude, firstOffset);
    }

    void ApplyDestructiveReachCrit(Player* player, Spell* spell)
    {
        if (!player || !spell)
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo || !player->HasAura(SPELL_DESTRUCTIVE_REACH_R2))
            return;

        // Timing contract (SHARED §4): act only on a candidate prepare - a player's own real cast,
        // not already mid-cast-bar (a rejected re-prepare or a spell with
        // SPELL_ATTR4_ALLOW_CAST_WHILE_CASTING, e.g. Soulburn, would otherwise have the running
        // cast's own charge stripped out from under it - druid_hooks.cpp:461 precedent).
        if (spell->IsTriggered())
            return;

        if (player->IsNonMeleeSpellCast(false, true, true) &&
            !spellInfo->HasAttribute(SPELL_ATTR4_ALLOW_CAST_WHILE_CASTING))
            return;

        SpellInfo const* helperInfo = sSpellMgr->AssertSpellInfo(SPELL_DESTRUCTIVE_REACH_CRIT_HELPER);
        if (!helperInfo || !spellInfo->IsAffected(SPELLFAMILY_WARLOCK, helperInfo->Effects[EFFECT_0].SpellClassMask))
            return;

        Unit* target = spell->m_targets.GetUnitTarget();
        if (target && player->IsValidAttackTarget(target) && player->GetDistance(target) > 20.0f)
            player->CastSpell(player, SPELL_DESTRUCTIVE_REACH_CRIT_HELPER, true);
        else
            player->RemoveAurasDueToSpell(SPELL_DESTRUCTIVE_REACH_CRIT_HELPER);
    }

    void ReduceChaosBoltCooldown(Player* player, uint32 ms)
    {
        if (!player)
            return;

        // No-op when Chaos Bolt isn't currently cooling down (ModifySpellCooldown, Player.cpp:11391,
        // returns early when the spell has no cooldown entry to modify).
        player->ModifySpellCooldown(SPELL_CHAOS_BOLT, -int32(ms));
    }
}
