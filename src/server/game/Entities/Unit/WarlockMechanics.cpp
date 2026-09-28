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
#include "CreatureAI.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
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
#include <cmath>
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

    // ------------------------------------------------------------------
    // Demonology pass (S3) additions (DEMONOLOGY.md §7 for the per-clause mapping, §3.4 for the
    // "WarlockMechanics additions" list). Frozen signatures - see the header for the contract.
    // ------------------------------------------------------------------

    // Main-pet creature entries (DEMONOLOGY.md §7.1's "Who gets what" table) - not warlock-specific
    // ids, so not part of the frozen header; duplicated here the same way this file's own
    // SPELL_SOUL_LEECH_R1/etc. (Destruction section above) duplicate cross-spec/stock ids rather
    // than widening WarlockMechanics.h.
    constexpr uint32 NPC_DEMON_IMP = 416;
    constexpr uint32 NPC_DEMON_VOIDWALKER = 1860;
    constexpr uint32 NPC_DEMON_SUCCUBUS = 1863;
    constexpr uint32 NPC_DEMON_FELHUNTER = 417;
    constexpr uint32 NPC_DEMON_FELGUARD = 17252;

    // Highest known rank's aura-effect amount among a talent's own ranks (ranks are mutually
    // exclusive), 0 if the talent isn't taken at all. Generalizes AFFLICTION's GetKnownLeechPct
    // (above) to read a live AuraEffect::GetAmount() instead of a hard-coded float, for every
    // Demonology "read live from the rank spell id" lookup (SHARED §4 convention; DEMONOLOGY.md §6
    // header/§7.1).
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

    // 1-based rank of the highest currently-known spell in the array, 0 if none are known.
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

    // Per-player Demonology state (Priest tentacle-map precedent, PriestMechanics.cpp) - cleared by
    // ClearDemonologyPlayerState on OnPlayerLogout.
    std::unordered_map<ObjectGuid, Warlock::PendingSummon> pendingSummonByPlayer;
    std::unordered_map<ObjectGuid, uint32> dreadstalkerTokenCounterByPlayer;
    // pairToken -> number of the pair's two Dreadstalkers that have departed so far (§7.4: "the
    // second stalker of the pair is a no-op" - Molten Core grants only on the *first* departure of
    // each token, and the entry is dropped once both have departed).
    std::unordered_map<ObjectGuid, std::unordered_map<uint32, uint8>> dreadstalkerDepartureCountByPlayer;
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

        switch (spellInfo->Id)
        {
            case SPELL_BANE_OF_AGONY:
            case SPELL_BANE_OF_DOOM:
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

    // ------------------------------------------------------------------
    // Demonology pass (S3) additions (DEMONOLOGY.md §7 for the per-clause mapping, §3.4 for the
    // "WarlockMechanics additions" list). Frozen signatures - see the header for the contract.
    // ------------------------------------------------------------------
    bool IsInMetamorphosis(Unit const* unit)
    {
        return unit && unit->GetShapeshiftForm() == FORM_METAMORPHOSIS;
    }

    bool IsInDarkApotheosis(Unit const* unit)
    {
        return unit && unit->GetShapeshiftForm() == FORM_DARK_APOTHEOSIS;
    }

    DemonKind GetDemonKind(Unit const* demon, Player const* owner)
    {
        if (!demon || !owner)
            return DemonKind::None;

        // Enslave Demon (1098) charms an arbitrary demon - checked before the entry switch so an
        // enslaved copy of e.g. an Imp-shaped demon isn't mistaken for the warlock's own Imp pet.
        if (demon->GetCharmerGUID() == owner->GetGUID())
            return DemonKind::Enslaved;

        switch (demon->GetEntry())
        {
            case NPC_DEMON_IMP: return DemonKind::Imp;
            case NPC_DEMON_VOIDWALKER: return DemonKind::Voidwalker;
            case NPC_DEMON_SUCCUBUS: return DemonKind::Succubus;
            case NPC_DEMON_FELHUNTER: return DemonKind::Felhunter;
            case NPC_DEMON_FELGUARD: return DemonKind::Felguard;
            case NPC_WILD_IMP: return DemonKind::WildImp;
            case NPC_IMP_GANG_BOSS: return DemonKind::ImpGangBoss;
            case NPC_DREADSTALKER: return DemonKind::Dreadstalker;
            case NPC_DOOMGUARD_GUARDIAN: return DemonKind::Doomguard;
            case NPC_INFERNAL_GUARDIAN: return DemonKind::Infernal;
            default: return DemonKind::None;
        }
    }

    // ------------------------------------------------------------------
    // Wild Imps (§7.2)
    // ------------------------------------------------------------------
    std::vector<Creature*> GetWildImps(Player* owner)
    {
        std::vector<Creature*> imps;
        if (!owner)
            return imps;

        for (Unit* controlled : owner->m_Controlled)
        {
            if (controlled->GetEntry() != NPC_WILD_IMP && controlled->GetEntry() != NPC_IMP_GANG_BOSS)
                continue;

            Creature* creature = controlled->ToCreature();
            if (!creature || !creature->AI() || creature->AI()->GetData(DATA_WILD_IMP_DEPARTING))
                continue;

            imps.push_back(creature);
        }

        return imps;
    }

    uint32 CountWildImps(Player const* owner)
    {
        if (!owner)
            return 0;

        uint32 count = 0;
        for (Unit* controlled : owner->m_Controlled)
        {
            if (controlled->GetEntry() != NPC_WILD_IMP && controlled->GetEntry() != NPC_IMP_GANG_BOSS)
                continue;

            Creature const* creature = controlled->ToCreature();
            if (!creature || !creature->AI() || creature->AI()->GetData(DATA_WILD_IMP_DEPARTING))
                continue;

            ++count;
        }

        return count;
    }

    bool TrySummonWildImp(Player* owner, Unit* target, bool gangBoss)
    {
        if (!owner || !target)
            return false;

        if (CountWildImps(owner) >= WILD_IMP_CAP)
            return false;

        SetPendingSummon(owner, { target->GetGUID(), 0 });
        owner->CastSpell(target, gangBoss ? SPELL_SUMMON_IMP_GANG_BOSS : SPELL_SUMMON_WILD_IMP, TRIGGERED_FULL_MASK);
        ClearPendingSummon(owner);
        return true;
    }

    void OnWildImpDespawn(Player* owner, WildImpDespawnReason reason)
    {
        if (!owner)
            return;

        // Timeout never rolls Molten Core (§7.2's Expire clause) - only an energy-death or an
        // Implosion consumption does.
        if (reason != WildImpDespawnReason::Energy && reason != WildImpDespawnReason::Implosion)
            return;

        int32 const chancePct = GetHighestRankAmount(owner, RANKS_MOLTEN_CORE, EFFECT_0);
        if (chancePct <= 0)
            return;

        float const chance = float(chancePct) * (1.0f + owner->GetProcChancePercentage() / 100.0f);
        if (roll_chance_f(chance))
            GrantMoltenCore(owner, 1);
    }

    void GrantMoltenCore(Player* owner, uint8 stacks)
    {
        if (!owner || !stacks)
            return;

        // Repeated self-casts of a CumulativeAura spell add a stack and refresh the duration each
        // time (stock stacking semantics) - exactly "+1 stack, max 4, refresh 30 s" per cast.
        for (uint8 i = 0; i < stacks; ++i)
            owner->CastSpell(owner, SPELL_MOLTEN_CORE, true);
    }

    // ------------------------------------------------------------------
    // Summon hand-off / Dreadstalker pairing (§7.2-§7.4)
    // ------------------------------------------------------------------
    void SetPendingSummon(Player* owner, PendingSummon const& pending)
    {
        if (owner)
            pendingSummonByPlayer[owner->GetGUID()] = pending;
    }

    PendingSummon GetPendingSummon(Player const* owner)
    {
        if (!owner)
            return {};

        auto itr = pendingSummonByPlayer.find(owner->GetGUID());
        return itr != pendingSummonByPlayer.end() ? itr->second : PendingSummon{};
    }

    void ClearPendingSummon(Player* owner)
    {
        if (owner)
            pendingSummonByPlayer.erase(owner->GetGUID());
    }

    uint32 NextDreadstalkerPairToken(Player* owner)
    {
        if (!owner)
            return 0;

        return ++dreadstalkerTokenCounterByPlayer[owner->GetGUID()];
    }

    void OnDreadstalkerDeparted(Player* owner, uint32 pairToken)
    {
        if (!owner)
            return;

        auto& counts = dreadstalkerDepartureCountByPlayer[owner->GetGUID()];
        uint8& count = counts[pairToken];
        ++count;

        // Molten Core only on the pair's first departure (§7.4) - the second stalker's own
        // departure is a no-op beyond bookkeeping cleanup.
        if (count == 1)
            GrantMoltenCore(owner, 1);
        if (count >= 2)
            counts.erase(pairToken);
    }

    // ------------------------------------------------------------------
    // Guardian base points / targeting (B21, §7.4)
    // ------------------------------------------------------------------
    int32 ComputeGuardianBasePoints(Unit const* guardian, uint32 spellId, float spCoefficient)
    {
        if (!guardian)
            return 0;

        SpellInfo const* spellInfo = sSpellMgr->AssertSpellInfo(spellId);
        if (!spellInfo)
            return 0;

        Unit* owner = guardian->GetOwner();
        int32 sp = 0;
        if (owner)
            sp = std::max(0, owner->SpellBaseDamageBonusDone(spellInfo->GetSchoolMask()));

        int32 const base = spellInfo->Effects[EFFECT_0].BasePoints;
        int32 const dieBonus = spellInfo->Effects[EFFECT_0].DieSides ? 1 : 0;
        return base + dieBonus + int32(std::lround(spCoefficient * float(sp)));
    }

    Unit* SelectGuardianTarget(Creature* guardian, Player* owner, ObjectGuid preferred)
    {
        if (!guardian || !owner)
            return nullptr;

        if (!preferred.IsEmpty())
        {
            if (Unit* preferredUnit = ObjectAccessor::GetUnit(*guardian, preferred))
                if (preferredUnit->IsAlive() && guardian->IsValidAttackTarget(preferredUnit) &&
                    preferredUnit->GetMap() == guardian->GetMap())
                    return preferredUnit;
        }

        // §11 Q10: no pulling - only follow onto a target the owner is already fighting.
        if (Unit* current = ObjectAccessor::GetUnit(*owner, owner->GetTarget()))
            if (current->IsAlive() && owner->IsValidAttackTarget(current) && current->IsInCombatWith(owner))
                return current;

        return nullptr;
    }

    // ------------------------------------------------------------------
    // Demonic Potency and the other hidden demon auras (§7.1)
    // ------------------------------------------------------------------
    int32 ComputeDemonAuraAmount(Player const* owner, Unit const* target, uint32 spellId, uint8 effIndex)
    {
        if (!owner || !target)
            return 0;

        // The owner's own Fel Bond copy (200851 self-cast) tracks whichever demon the warlock
        // currently has (main pet or enslaved) rather than `target` itself.
        bool const isOwnerCopy = spellId == SPELL_FEL_BOND_AURA && target->GetGUID() == owner->GetGUID();

        DemonKind kind = DemonKind::None;
        if (isOwnerCopy)
        {
            if (Unit* pet = owner->GetPet())
                kind = GetDemonKind(pet, owner);
            else if (Unit* charm = owner->GetCharm())
                kind = GetDemonKind(charm, owner);
        }
        else
            kind = GetDemonKind(target, owner);

        float const mastery = owner->GetMasteryPercentage();

        if (spellId == SPELL_DEMONIC_POTENCY)
        {
            if (kind == DemonKind::None)
                return 0;

            bool const unholyPowerKind = kind == DemonKind::Imp || kind == DemonKind::Voidwalker ||
                kind == DemonKind::Felhunter || kind == DemonKind::Felguard || kind == DemonKind::WildImp ||
                kind == DemonKind::ImpGangBoss || kind == DemonKind::Dreadstalker || kind == DemonKind::Doomguard ||
                kind == DemonKind::Infernal;

            float sum = 0.0f;
            if (unholyPowerKind)
            {
                sum += float(GetHighestRankAmount(owner, RANKS_UNHOLY_POWER, EFFECT_0));
                if (owner->HasAura(RANKS_UNHOLY_POWER[2]))
                    sum += mastery;
            }

            if (IsInMetamorphosis(owner))
                sum += 15.0f + mastery + float(GetHighestRankAmount(owner, RANKS_DEMONIC_FORM, EFFECT_0));

            if (owner->HasAura(SPELL_FEL_CRUELTY_BUFF))
                sum += 10.0f;

            if (kind == DemonKind::Felguard || kind == DemonKind::Enslaved)
                sum += float(GetHighestRankAmount(owner, RANKS_FEL_BOND, EFFECT_1));

            if (kind == DemonKind::Imp)
                sum += float(GetHighestRankAmount(owner, RANKS_IMPROVED_IMP, EFFECT_1));

            switch (effIndex)
            {
                case EFFECT_0:
                    return int32(std::lround(sum));
                case EFFECT_1:
                {
                    float magic = sum;
                    if (owner->HasAura(SPELL_DEMONIC_PACT_EMPOWER) && owner->GetPet() == target)
                        magic += 5.0f;
                    return int32(std::lround(magic));
                }
                case EFFECT_2:
                {
                    bool const critKind = kind == DemonKind::Imp || kind == DemonKind::Voidwalker ||
                        kind == DemonKind::Succubus || kind == DemonKind::Felhunter || kind == DemonKind::Felguard ||
                        kind == DemonKind::WildImp || kind == DemonKind::ImpGangBoss || kind == DemonKind::Dreadstalker;
                    if (!critKind)
                        return 0;

                    float const dt = float(GetHighestRankAmount(owner, RANKS_DEMONIC_TACTICS, EFFECT_1));
                    float const idtPct = float(GetHighestRankAmount(owner, RANKS_IMPROVED_DEMONIC_TACTICS, EFFECT_0));
                    float const shadowCrit =
                        owner->GetFloatValue(PLAYER_SPELL_CRIT_PERCENTAGE1 + uint32(SPELL_SCHOOL_SHADOW));
                    return int32(std::lround(dt + idtPct / 100.0f * shadowCrit));
                }
                default:
                    return 0;
            }
        }

        if (spellId == SPELL_DEMONIC_VERSATILITY)
        {
            // §11 Q16: every warlock's demons, no talent gate.
            float const v = owner->GetVersatilityPercentage();
            switch (effIndex)
            {
                case EFFECT_0: return int32(std::lround(v));
                case EFFECT_1: return -int32(std::lround(v / 2.0f));
                case EFFECT_2: return int32(std::lround(v));
                default: return 0;
            }
        }

        if (spellId == SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA)
            return effIndex == EFFECT_0 ? GetHighestRankAmount(owner, RANKS_GRIMOIRE_OF_SYNERGY, EFFECT_0) : 0;

        if (spellId == SPELL_FEL_VITALITY_DEMON)
        {
            bool const felVitalityKind = kind == DemonKind::Voidwalker || kind == DemonKind::Felhunter ||
                kind == DemonKind::Felguard || kind == DemonKind::Dreadstalker;
            if (!felVitalityKind || (effIndex != EFFECT_1 && effIndex != EFFECT_2))
                return 0;

            return GetHighestRankAmount(owner, RANKS_FEL_VITALITY, EFFECT_1);
        }

        if (spellId == SPELL_BRUTALITY_VOIDWALKER)
        {
            if (kind != DemonKind::Voidwalker || (effIndex != EFFECT_0 && effIndex != EFFECT_1))
                return 0;

            return GetHighestRankAmount(owner, RANKS_DEMONIC_BRUTALITY, EFFECT_2);
        }

        if (spellId == SPELL_FEL_BOND_AURA)
        {
            int32 const felBondFgEnslaved = GetHighestRankAmount(owner, RANKS_FEL_BOND, EFFECT_1);
            int32 const felBondVW = GetHighestRankAmount(owner, RANKS_FEL_BOND, EFFECT_0);
            uint8 const resilienceRank = GetHighestKnownRank(owner, RANKS_DEMONIC_RESILIENCE);
            int32 const resilienceDR = resilienceRank ? int32(DEMONIC_RESILIENCE_DEMON_DR[resilienceRank - 1]) : 0;

            bool const fgOrEnslaved = kind == DemonKind::Felguard || kind == DemonKind::Enslaved;
            bool const isVW = kind == DemonKind::Voidwalker;

            switch (effIndex)
            {
                case EFFECT_0:
                    // Demon damage-done is granted through Potency instead - only the owner's own
                    // copy carries the +damage-done half of Fel Bond's Felguard/enslaved clause.
                    return isOwnerCopy && fgOrEnslaved ? felBondFgEnslaved : 0;
                case EFFECT_1:
                {
                    int32 amount = 0;
                    if (fgOrEnslaved)
                        amount += felBondFgEnslaved;
                    if (!isOwnerCopy)
                        amount += resilienceDR;
                    return -amount;
                }
                case EFFECT_2:
                    return isVW ? -felBondVW : 0;
                default:
                    return 0;
            }
        }

        return 0;
    }

    // Recalculates every effect of an already-applied aura (RecalculateAmount() routes back through
    // ComputeDemonAuraAmount) - used below so a buff that stays on the demon/warlock across a
    // rank-up, a pet swap or a talent reset doesn't keep whatever amount it had when first applied
    // (found in user review, 2026-09-28: RefreshDemonAuras used to only Add-if-missing/Remove-if-
    // unwanted, never recalculate an aura already present).
    void RecalculateAllEffects(Aura* aura)
    {
        if (!aura)
            return;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect* eff = aura->GetEffect(i))
                eff->RecalculateAmount();
    }

    void RefreshDemonAuras(Player* owner, Unit* demon)
    {
        if (!owner || !demon)
            return;

        DemonKind const kind = GetDemonKind(demon, owner);
        if (kind == DemonKind::None)
            return;

        // Potency and Versatility are unconditional (every demon, §7.1); their own 5 s periodic
        // tick / explicit RefreshDemonicPotency() calls keep them current, so add-if-missing here
        // is enough.
        if (!demon->HasAura(SPELL_DEMONIC_POTENCY, owner->GetGUID()))
            owner->AddAura(SPELL_DEMONIC_POTENCY, demon);
        if (!demon->HasAura(SPELL_DEMONIC_VERSATILITY, owner->GetGUID()))
            owner->AddAura(SPELL_DEMONIC_VERSATILITY, demon);

        bool const wantsGrimoire =
            kind == DemonKind::Felguard && GetHighestKnownRank(owner, RANKS_GRIMOIRE_OF_SYNERGY) != 0;
        if (wantsGrimoire)
        {
            Aura* aura = demon->GetAura(SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA, owner->GetGUID());
            if (!aura)
                aura = owner->AddAura(SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA, demon);
            RecalculateAllEffects(aura);
        }
        else
            demon->RemoveAura(SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA, owner->GetGUID());

        bool const felVitalityKind = kind == DemonKind::Imp || kind == DemonKind::Voidwalker ||
            kind == DemonKind::Succubus || kind == DemonKind::Felhunter || kind == DemonKind::Felguard ||
            kind == DemonKind::Enslaved || kind == DemonKind::Dreadstalker;
        bool const wantsFelVitality = felVitalityKind && GetHighestKnownRank(owner, RANKS_FEL_VITALITY) != 0;
        if (wantsFelVitality)
        {
            Aura* aura = demon->GetAura(SPELL_FEL_VITALITY_DEMON, owner->GetGUID());
            if (!aura)
                aura = owner->AddAura(SPELL_FEL_VITALITY_DEMON, demon);
            RecalculateAllEffects(aura);
        }
        else
            demon->RemoveAura(SPELL_FEL_VITALITY_DEMON, owner->GetGUID());

        bool const wantsBrutality =
            kind == DemonKind::Voidwalker && GetHighestKnownRank(owner, RANKS_DEMONIC_BRUTALITY) != 0;
        if (wantsBrutality)
        {
            Aura* aura = demon->GetAura(SPELL_BRUTALITY_VOIDWALKER, owner->GetGUID());
            if (!aura)
                aura = owner->AddAura(SPELL_BRUTALITY_VOIDWALKER, demon);
            RecalculateAllEffects(aura);
        }
        else
            demon->RemoveAura(SPELL_BRUTALITY_VOIDWALKER, owner->GetGUID());

        bool const isMainOrEnslaved = kind == DemonKind::Imp || kind == DemonKind::Voidwalker ||
            kind == DemonKind::Succubus || kind == DemonKind::Felhunter || kind == DemonKind::Felguard ||
            kind == DemonKind::Enslaved;
        bool const wantsFelBond = isMainOrEnslaved && (GetHighestKnownRank(owner, RANKS_FEL_BOND) != 0 ||
            GetHighestKnownRank(owner, RANKS_DEMONIC_RESILIENCE) != 0);
        if (wantsFelBond)
        {
            Aura* demonAura = demon->GetAura(SPELL_FEL_BOND_AURA, owner->GetGUID());
            if (!demonAura)
                demonAura = owner->AddAura(SPELL_FEL_BOND_AURA, demon);
            RecalculateAllEffects(demonAura);

            Aura* ownerAura = owner->GetAura(SPELL_FEL_BOND_AURA, owner->GetGUID());
            if (!ownerAura)
                ownerAura = owner->AddAura(SPELL_FEL_BOND_AURA, owner);
            RecalculateAllEffects(ownerAura);
        }
        else if (isMainOrEnslaved)
        {
            demon->RemoveAura(SPELL_FEL_BOND_AURA, owner->GetGUID());
            owner->RemoveAura(SPELL_FEL_BOND_AURA, owner->GetGUID());
        }
    }

    void RefreshDemonicPotency(Player* owner)
    {
        if (!owner)
            return;

        constexpr std::array<uint32, 6> demonAuraIds = { SPELL_DEMONIC_POTENCY, SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA,
            SPELL_FEL_VITALITY_DEMON, SPELL_FEL_BOND_AURA, SPELL_BRUTALITY_VOIDWALKER, SPELL_DEMONIC_VERSATILITY };

        for (Unit* controlled : owner->m_Controlled)
        {
            if (GetDemonKind(controlled, owner) == DemonKind::None)
                continue;

            for (uint32 spellId : demonAuraIds)
            {
                Aura* aura = controlled->GetAura(spellId, owner->GetGUID());
                if (!aura)
                    continue;

                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect* eff = aura->GetEffect(i))
                        eff->RecalculateAmount();
            }
        }

        if (Aura* ownerFelBond = owner->GetAura(SPELL_FEL_BOND_AURA, owner->GetGUID()))
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect* eff = ownerFelBond->GetEffect(i))
                    eff->RecalculateAmount();
    }

    // ------------------------------------------------------------------
    // Legion's Call (§7.11)
    // ------------------------------------------------------------------
    void SyncLegionsCall(Player* player, bool losingTalent)
    {
        if (!player)
            return;

        bool const has = !losingTalent && player->HasTalent(SPELL_LEGIONS_CALL, player->GetActiveSpec());

        if (has)
        {
            player->removeSpell(SPELL_INFERNO, SPEC_MASK_ALL, false);
            player->removeSpell(SPELL_RITUAL_OF_DOOM, SPEC_MASK_ALL, false);
        }
        else
        {
            if (player->GetLevel() >= 50 && !player->HasSpell(SPELL_INFERNO))
                player->learnSpell(SPELL_INFERNO);
            if (player->GetLevel() >= 60 && !player->HasSpell(SPELL_RITUAL_OF_DOOM))
                player->learnSpell(SPELL_RITUAL_OF_DOOM);
        }
    }

    void ClearDemonologyPlayerState(ObjectGuid playerGuid)
    {
        pendingSummonByPlayer.erase(playerGuid);
        dreadstalkerTokenCounterByPlayer.erase(playerGuid);
        dreadstalkerDepartureCountByPlayer.erase(playerGuid);
    }
}
