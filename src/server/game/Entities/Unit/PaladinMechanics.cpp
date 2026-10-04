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

#include "PaladinMechanics.h"
#include "Creature.h"
#include "GameTime.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <deque>
#include <mutex>
#include <unordered_map>
#include <vector>

/*
 * WP-B2 bodies (paladin-rework.SHARED.md Part A4 / B2.1 / B2.2 / B2.3 / B3.3 / B4, CR1-CR5;
 * paladin-rework.RETRIBUTION.md §0.4 / §2.7 / §6.2 / §6.3 / §6.12). Defines no script classes: the
 * spell scripts live in spell_paladin_seals.cpp / spell_paladin_retribution.cpp and call in here.
 *
 * State is per player and keyed by the low guid (Priest precedent). Map structure changes (find /
 * emplace / erase) go through `stateLock` because maps update on several threads; the per-player
 * entry itself is only touched from that player's own map update, and unordered_map entries keep
 * their address across other keys' insertions, so callers hold a pointer without the lock. Every
 * removal-path function (OnSealRemoved, OnPrimedRemoved, ClearState*) is find-only and casts
 * nothing that depends on a missing entry (CR5: logout erases the state before the aura removals).
 */

namespace Paladin
{
    namespace
    {
        constexpr uint8 MAX_SEAL_STACKS = 10;
        constexpr uint32 BUILDER_CRIT_WINDOW_MS = 1000;   // SHARED B2.3

        // SpellFamilyFlags dwords (SpellClassMask_1/_2/_3) this file tests; the masks are
        // `apps/dbc-tools/source/classes/paladin/_masks.py` values (SHARED A3).
        constexpr uint32 FAMILY_D0_UNLEASH = 0x800000;          // U
        constexpr uint32 FAMILY_D1_EXORCISM = 0x2;
        constexpr uint32 FAMILY_D1_MULTI_TARGET = 0x260000;     // Divine Storm, Hammer of the Righteous, Holy Wrath
        constexpr uint32 FAMILY_D2_JUDGEMENT = 0x8;             // J
        constexpr uint32 FAMILY_D2_SEAL_PASSIVE = 0x200;        // P
        constexpr uint32 FAMILY_D2_SEAL_PASSIVE_COMMAND = 0x400; // C
        constexpr uint32 FAMILY_D2_BLADE_OF_JUSTICE = 0x800;    // BoJ
        constexpr uint32 FAMILY_D2_WAKE_OF_ASHES = 0x1000;      // WoA
        constexpr uint32 FAMILY_D2_DELIVERANCE = 0x10000;       // Dv
        constexpr uint32 FAMILY_D2_SEAL_VETO = FAMILY_D2_JUDGEMENT | FAMILY_D2_SEAL_PASSIVE
            | FAMILY_D2_SEAL_PASSIVE_COMMAND | FAMILY_D2_DELIVERANCE;
        constexpr uint32 ICON_RIGHTEOUS_VENGEANCE = 3025;       // stock SoC check (spell_paladin.cpp:223)

        // Retribution ids with no stock name: minted talent ranks stay hand literals (RETRIBUTION §2.7).
        constexpr uint32 SPELL_IMPROVED_JUDGEMENTS_RANK3 = 201468;
        constexpr uint32 SPELL_SANCTIFIED_SEALS_RANK1 = 201454;
        constexpr uint32 SPELL_SANCTIFIED_SEALS_RANK2 = 201455;
        constexpr uint32 SPELL_SANCTIFIED_SEALS_RANK3 = 201456;
        constexpr uint32 SPELL_CRUSADE_RANK3 = 201465;

        // Ret numbers the spec writes into the C++ (RETRIBUTION §6.12)
        constexpr int32 CRUSADE_RAMP_PER_STACK = 2;
        constexpr int32 CRUSADE_RAMP_CAP = 15;
        constexpr float SANCTIFIED_SEALS_LIGHT_PER_MASTERY = 0.0625f;

        constexpr std::array<uint32, size_t(SealType::Count)> SEAL_SPELLS =
        {
            PaladinData::SPELL_SEAL_OF_RIGHTEOUSNESS, PaladinData::SPELL_SEAL_OF_COMMAND,
            PaladinData::SPELL_SEAL_OF_VENGEANCE, PaladinData::SPELL_SEAL_OF_JUSTICE,
            PaladinData::SPELL_SEAL_OF_LIGHT, PaladinData::SPELL_SEAL_OF_WISDOM
        };

        constexpr std::array<uint32, size_t(SealType::Count)> PRIMED_SPELLS =
        {
            PaladinData::SPELL_PRIMED_RIGHTEOUSNESS, PaladinData::SPELL_PRIMED_COMMAND,
            PaladinData::SPELL_PRIMED_VENGEANCE, PaladinData::SPELL_PRIMED_JUSTICE,
            PaladinData::SPELL_PRIMED_LIGHT, PaladinData::SPELL_PRIMED_WISDOM
        };

        constexpr std::array<uint32, size_t(SealType::Count)> UNLEASH_SPELLS =
        {
            PaladinData::SPELL_UNLEASH_RIGHTEOUSNESS, PaladinData::SPELL_UNLEASH_COMMAND,
            PaladinData::SPELL_UNLEASH_VENGEANCE, PaladinData::SPELL_UNLEASH_JUSTICE,
            PaladinData::SPELL_UNLEASH_LIGHT, PaladinData::SPELL_UNLEASH_WISDOM
        };

        constexpr std::array<uint32, size_t(SealType::Count)> UNLEASH_AOE_SPELLS =
        {
            PaladinData::SPELL_UNLEASH_RIGHTEOUSNESS_AOE, PaladinData::SPELL_UNLEASH_COMMAND_AOE,
            PaladinData::SPELL_UNLEASH_VENGEANCE_AOE, PaladinData::SPELL_UNLEASH_JUSTICE_AOE,
            PaladinData::SPELL_UNLEASH_LIGHT_AOE, PaladinData::SPELL_UNLEASH_WISDOM_AOE
        };

        constexpr std::array<uint32, size_t(SealType::Count)> PASSIVE_SPELLS =
        {
            PaladinData::SPELL_SEAL_OF_RIGHTEOUSNESS_HIT, PaladinData::SPELL_SEAL_OF_COMMAND_HIT,
            PaladinData::SPELL_SEAL_OF_VENGEANCE_HIT, PaladinData::SPELL_SEAL_OF_JUSTICE_HIT,
            PaladinData::SPELL_SEAL_OF_LIGHT_HIT, PaladinData::SPELL_SEAL_OF_WISDOM_HIT
        };

        constexpr std::array<uint32, size_t(SealType::Count)> PASSIVE_NORMALIZED_SPELLS =
        {
            PaladinData::SPELL_SEAL_OF_RIGHTEOUSNESS_HIT_NORMALIZED, PaladinData::SPELL_SEAL_OF_COMMAND_HIT_NORMALIZED,
            PaladinData::SPELL_SEAL_OF_VENGEANCE_HIT_NORMALIZED, PaladinData::SPELL_SEAL_OF_JUSTICE_HIT_NORMALIZED,
            PaladinData::SPELL_SEAL_OF_LIGHT_HIT_NORMALIZED, PaladinData::SPELL_SEAL_OF_WISDOM_HIT_NORMALIZED
        };

        uint32 LookupSpell(std::array<uint32, size_t(SealType::Count)> const& table, SealType type)
        {
            return type < SealType::Count ? table[size_t(type)] : 0;
        }

        // Retribution per-player state (RETRIBUTION §2.7): the Execution Sentence tracker. The crit-capture
        // fields live in SealState (SHARED B2.1).
        struct RetState
        {
            ObjectGuid esTarget;
            uint8 esGained = 0;
        };

        std::mutex stateLock;
        std::unordered_map<ObjectGuid::LowType, SealState> sealStates;
        std::unordered_map<ObjectGuid::LowType, RetState> retStates;
        // deque: references stay valid across push_back/pop_back (GetUnleashContext hands out a pointer)
        std::unordered_map<ObjectGuid::LowType, std::deque<UnleashContext>> unleashContexts;
        std::atomic<uint32> primedSerialCounter{ 0 };

        // Registries: appended once from AddSC_* on the main thread before any map update, read-only afterwards.
        std::vector<StackGainModifier> stackGainModifiers;
        std::vector<StacksGainedListener> stacksGainedListeners;
        std::vector<SealSourceFilter> sealPassiveVetoes;
        std::vector<SealSourceFilter> sealPassiveMagicSources;
        std::vector<UnleashBonusProvider> unleashBonusProviders;
        std::vector<ConsecrationAppliedHook> consecrationAppliedHooks;

        struct JudgementHookEntry
        {
            JudgementCastHook fn;
            bool onlyWhenPrimedConsumed = false;
        };

        std::vector<JudgementHookEntry> judgementCastHooks;

        SealState* FindState(ObjectGuid::LowType low)
        {
            std::lock_guard<std::mutex> lock(stateLock);
            auto const itr = sealStates.find(low);
            return itr != sealStates.end() ? &itr->second : nullptr;
        }

        SealState& GetOrCreateState(ObjectGuid::LowType low)
        {
            std::lock_guard<std::mutex> lock(stateLock);
            return sealStates[low];
        }

        RetState* FindRetState(ObjectGuid::LowType low)
        {
            std::lock_guard<std::mutex> lock(stateLock);
            auto const itr = retStates.find(low);
            return itr != retStates.end() ? &itr->second : nullptr;
        }

        void ResetPrimed(SealState& state)
        {
            state.primedSeal = SealType::None;
            state.primedStacks = 0;
            state.primedSerial = 0;
        }

        bool IsPaladinFamily(SpellInfo const* spellInfo)
        {
            return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_PALADIN;
        }
    }

    // ------------------------------------------------------------------
    // SHARED Part A4: id lookups
    // ------------------------------------------------------------------
    SealType GetSealType(uint32 sealSpellId)
    {
        for (size_t i = 0; i < SEAL_SPELLS.size(); ++i)
            if (SEAL_SPELLS[i] == sealSpellId)
                return SealType(i);

        return SealType::None;
    }

    uint32 GetSealSpell(SealType type) { return LookupSpell(SEAL_SPELLS, type); }
    uint32 GetPrimedSpell(SealType type) { return LookupSpell(PRIMED_SPELLS, type); }
    uint32 GetUnleashSpell(SealType type, bool aoe)
    {
        return LookupSpell(aoe ? UNLEASH_AOE_SPELLS : UNLEASH_SPELLS, type);
    }

    uint32 GetPassiveSpell(SealType type, bool normalized)
    {
        return LookupSpell(normalized ? PASSIVE_NORMALIZED_SPELLS : PASSIVE_SPELLS, type);
    }

    bool IsPrimedAura(uint32 spellId)
    {
        return std::find(PRIMED_SPELLS.begin(), PRIMED_SPELLS.end(), spellId) != PRIMED_SPELLS.end();
    }

    // ------------------------------------------------------------------
    // SHARED Part A4 / B2.2: seal state
    // ------------------------------------------------------------------
    uint8 GetSealStacks(Player const* player)
    {
        if (!player)
            return 0;

        SealState const* state = FindState(player->GetGUID().GetCounter());
        return state && state->activeSeal != SealType::None ? state->activeStacks : 0;
    }

    SealType GetActiveSeal(Player const* player)
    {
        if (!player)
            return SealType::None;

        SealState const* state = FindState(player->GetGUID().GetCounter());
        return state ? state->activeSeal : SealType::None;
    }

    uint8 AddSealStacks(Player* player, uint8 count, uint32 sourceSpellId, bool crit)
    {
        if (!player || !count)
            return 0;

        SealState* state = FindState(player->GetGUID().GetCounter());
        // "only if activeSeal != None at grant time"; no state means no seal was ever applied
        if (!state || state->activeSeal == SealType::None)
            return 0;

        // The state must never claim a seal that is not on the player (a stale entry after an unusual removal)
        Aura* sealAura = player->GetAura(GetSealSpell(state->activeSeal), player->GetGUID());
        if (!sealAura)
        {
            state->activeSeal = SealType::None;
            state->activeStacks = 0;
            return 0;
        }

        // Conviction 2-on-crit, Improved Judgements +1 (registered by Ret / Holy)
        for (StackGainModifier const& modifier : stackGainModifiers)
            count = modifier(player, count, sourceSpellId, crit);

        uint8 const oldStacks = state->activeStacks;
        uint8 const newStacks = uint8(std::min<uint32>(MAX_SEAL_STACKS, uint32(oldStacks) + count));
        uint8 const gained = newStacks - oldStacks;
        state->activeStacks = newStacks;

        // Display = max(1, stacks); SetStackAmount does not refresh the duration (SpellAuras.cpp:1028-1052)
        uint8 const display = std::max<uint8>(1, newStacks);
        if (sealAura->GetStackAmount() != display)
            sealAura->SetStackAmount(display);

        // Overflow past 10 is not "gained" (FEAS-S2)
        if (gained)
            NotifyStacksGained(player, gained);

        return gained;
    }

    void OnSealRemoved(Player* player, SealType type, AuraRemoveMode mode)
    {
        if (!player || type >= SealType::Count)
            return;

        // CR5: find-only, a logout has already erased the entry
        SealState* state = FindState(player->GetGUID().GetCounter());
        if (!state || state->activeSeal != type)
            return;

        uint8 const stacks = state->activeStacks;
        state->activeSeal = SealType::None;
        state->activeStacks = 0;

        if (mode != AURA_REMOVE_BY_EXPIRE)   // replaced / clicked off / death: the stacks are lost
            return;

        uint32 const primedId = GetPrimedSpell(type);
        if (!primedId || !player->IsInWorld() || !player->IsAlive())
            return;

        // (1) A same-id Primed would take the recast through ModStackAmount(+stacks) and run no
        // AfterEffectApply, leaving a stale serial. Its OnPrimedRemoved clears primed* on a serial match.
        // A different-id Primed is left to spell_group 1211.
        if (player->HasAura(primedId, player->GetGUID()))
            player->RemoveAura(primedId, player->GetGUID());

        // (2)-(3) transient hand-off, valid only during this one synchronous cast; OnPrimedApplied is the
        // only writer of primed*
        state->pendingPrimedSeal = type;
        state->pendingPrimedStacks = stacks;
        player->CastCustomSpell(primedId, SPELLVALUE_AURA_STACK, int32(std::max<uint8>(1, stacks)), player,
            TRIGGERED_FULL_MASK);

        // (4) a failed cast leaves no state behind
        state->pendingPrimedSeal = SealType::None;
        state->pendingPrimedStacks = 0;
    }

    bool ConsumePrimed(Player* player, SealType& outType, uint8& outStacks)
    {
        if (!player || !PeekPrimed(player, outType, outStacks))
            return false;

        SealState* state = FindState(player->GetGUID().GetCounter());
        if (!state)
            return false;

        // serial cleared first, so the aura removal's OnPrimedRemoved is a no-op
        ResetPrimed(*state);
        player->RemoveAura(GetPrimedSpell(outType), player->GetGUID());
        return true;
    }

    void ClearState(Player* player)
    {
        if (!player)
            return;

        ObjectGuid::LowType const low = player->GetGUID().GetCounter();
        {
            std::lock_guard<std::mutex> lock(stateLock);
            sealStates.erase(low);
            unleashContexts.erase(low);
        }

        ClearHolyState(player);
        ClearStateRet(player);
    }

    void NotifyStacksGained(Player* player, uint8 gained)
    {
        if (!player || !gained)
            return;

        for (StacksGainedListener const& listener : stacksGainedListeners)
            listener(player, gained);
    }

    void RegisterConsecrationAppliedHook(ConsecrationAppliedHook fn)
    {
        if (fn)
            consecrationAppliedHooks.push_back(std::move(fn));
    }

    bool RollScriptedChance(Player const* player, float baseChancePct)
    {
        float chance = baseChancePct;
        if (player)
            chance *= 1.0f + player->GetProcChancePercentage() / 100.0f;

        return roll_chance_f(std::min(100.0f, chance));
    }

    // Holy section bodies are written in S2 (HOLY.md); the Retribution pass leaves these as the
    // frozen no-ops so ClearState() and the dispatcher's call site already exist.
    void OnJudgementCastHoly(Player* /*player*/, Unit* /*target*/, bool /*deliverance*/, uint32 /*ownHitDamage*/) { }
    void ClearHolyState(Player* /*player*/) { }

    void ClearStateRet(Player* player)
    {
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        retStates.erase(player->GetGUID().GetCounter());
    }

    // ------------------------------------------------------------------
    // SHARED Part B2.1
    // ------------------------------------------------------------------
    void OnSealApplied(Player* player, SealType type, Aura* sealAura)
    {
        if (!player || !sealAura || type >= SealType::Count)
            return;

        SealState& state = GetOrCreateState(player->GetGUID().GetCounter());
        state.activeSeal = type;

        WorldSession const* session = player->GetSession();
        if (session && session->PlayerLoading())
        {
            // Login: auras load before the player enters the world; the saved display stack is all there
            // is (0/1 ambiguity accepted, PLAN B8)
            state.activeStacks = std::min<uint8>(MAX_SEAL_STACKS, sealAura->GetStackAmount());
            return;
        }

        state.activeStacks = 0;
        if (sealAura->GetStackAmount() != 1)
            sealAura->SetStackAmount(1);
    }

    void OnPrimedApplied(Player* player, SealType type, Aura* primedAura, uint32& outSerial)
    {
        outSerial = 0;
        if (!player || !primedAura || type >= SealType::Count)
            return;

        SealState& state = GetOrCreateState(player->GetGUID().GetCounter());
        state.primedSeal = type;
        // Hand-off from OnSealRemoved(EXPIRE); a login or GM cast falls back to the display stack
        state.primedStacks = state.pendingPrimedSeal == type ? state.pendingPrimedStacks : primedAura->GetStackAmount();

        uint32 serial = ++primedSerialCounter;
        if (!serial)   // never hand out 0: it means "no Primed" in primedSerial
            serial = ++primedSerialCounter;

        state.primedSerial = serial;
        outSerial = serial;
    }

    void OnPrimedRemoved(Player* player, SealType /*type*/, uint32 serial)
    {
        if (!player || !serial)
            return;

        // CR5: find-only. A replacement Primed has its own serial and must not be wiped by this removal.
        SealState* state = FindState(player->GetGUID().GetCounter());
        if (state && state->primedSerial == serial)
            ResetPrimed(*state);
    }

    bool PeekPrimed(Player const* player, SealType& outType, uint8& outStacks)
    {
        outType = SealType::None;
        outStacks = 0;
        if (!player)
            return false;

        SealState* state = FindState(player->GetGUID().GetCounter());
        if (!state || state->primedSeal == SealType::None)
            return false;

        // The state may never claim a Primed aura that is not there
        if (!player->HasAura(GetPrimedSpell(state->primedSeal), player->GetGUID()))
        {
            ResetPrimed(*state);
            return false;
        }

        outType = state->primedSeal;
        outStacks = state->primedStacks;
        return true;
    }

    uint8 GetBuilderBaseCount(uint32 spellId)
    {
        return spellId == PaladinData::SPELL_WAKE_OF_ASHES ? 3 : 1;
    }

    void NoteBuilderCrit(Player* player, uint32 spellId)
    {
        if (!player)
            return;

        SealState& state = GetOrCreateState(player->GetGUID().GetCounter());
        state.builderCritSpellId = spellId;
        state.builderCritMs = uint32(GameTime::GetGameTimeMS().count());
    }

    bool ConsumeBuilderCrit(Player* player, uint32 spellId)
    {
        if (!player)
            return false;

        SealState* state = FindState(player->GetGUID().GetCounter());
        if (!state || !state->builderCritSpellId)
            return false;

        // unsigned subtraction: safe across the 32-bit millisecond wrap
        bool const fresh = uint32(GameTime::GetGameTimeMS().count()) - state->builderCritMs <= BUILDER_CRIT_WINDOW_MS;
        bool const match = fresh && state->builderCritSpellId == spellId;
        if (match || !fresh)   // consumed, or stale: either way it must not leak into a later cast
        {
            state->builderCritSpellId = 0;
            state->builderCritMs = 0;
        }

        return match;
    }

    void RegisterStackGainModifier(StackGainModifier fn)
    {
        if (fn)
            stackGainModifiers.push_back(std::move(fn));
    }

    void RegisterStacksGainedListener(StacksGainedListener fn)
    {
        if (fn)
            stacksGainedListeners.push_back(std::move(fn));
    }

    void RegisterSealPassiveVeto(SealSourceFilter fn)
    {
        if (fn)
            sealPassiveVetoes.push_back(std::move(fn));
    }

    void RegisterSealPassiveMagicSource(SealSourceFilter fn)
    {
        if (fn)
            sealPassiveMagicSources.push_back(std::move(fn));
    }

    bool IsSealPassiveSource(Player const* player, ProcEventInfo const& eventInfo)
    {
        if (!player)
            return false;

        // actor == target: Divine Storm's self DUMMY, stock Seal of Light check (spell_paladin.cpp:303-307).
        // `player` is the actor of a DONE proc (the seal auras only carry DONE flags); ProcEventInfo::GetActor()
        // is non-const so it cannot be read through the const reference.
        if (eventInfo.GetActionTarget() == player || eventInfo.GetProcTarget() == player)
            return false;

        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return true;   // a white swing

        if (IsPaladinFamily(procSpell))
        {
            // unleashes (U), seal passives and BoJ echoes (P), Command (C), Judgement (J), Deliverance (Dv)
            if ((procSpell->SpellFamilyFlags[0] & FAMILY_D0_UNLEASH)
                || (procSpell->SpellFamilyFlags[2] & FAMILY_D2_SEAL_VETO))
                return false;
        }

        if (procSpell->SpellIconID == ICON_RIGHTEOUS_VENGEANCE)   // stock SoC check
            return false;

        for (SealSourceFilter const& veto : sealPassiveVetoes)
            if (veto(player, procSpell))
                return false;

        switch (procSpell->DmgClass)
        {
            case SPELL_DAMAGE_CLASS_MELEE:
                return true;
            case SPELL_DAMAGE_CLASS_MAGIC:
                for (SealSourceFilter const& allow : sealPassiveMagicSources)
                    if (allow(player, procSpell))
                        return true;
                return false;
            default:
                return false;
        }
    }

    bool IsMultiTargetAttack(SpellInfo const* procSpell)
    {
        if (!procSpell)
            return false;

        if (IsPaladinFamily(procSpell) && ((procSpell->SpellFamilyFlags[1] & FAMILY_D1_MULTI_TARGET)
            || (procSpell->SpellFamilyFlags[2] & FAMILY_D2_WAKE_OF_ASHES)))
            return true;

        return procSpell->IsAffectingArea();
    }

    // ------------------------------------------------------------------
    // SHARED Part B3 / B4: Judgement and unleash
    // ------------------------------------------------------------------
    void RegisterUnleashBonusProvider(UnleashBonusProvider fn)
    {
        if (fn)
            unleashBonusProviders.push_back(std::move(fn));
    }

    UnleashBonus GetUnleashBonus(Player const* player, SealType type)
    {
        UnleashBonus bonus;
        if (!player)
            return bonus;

        for (UnleashBonusProvider const& provider : unleashBonusProviders)
            provider(player, type, bonus);

        return bonus;
    }

    UnleashContext const* GetUnleashContext(Player const* player)
    {
        if (!player)
            return nullptr;

        std::lock_guard<std::mutex> lock(stateLock);
        auto const itr = unleashContexts.find(player->GetGUID().GetCounter());
        return itr != unleashContexts.end() && !itr->second.empty() ? &itr->second.back() : nullptr;
    }

    UnleashContextScope::UnleashContextScope(Player* player, UnleashContext const& ctx)
        : _guid(player ? player->GetGUID() : ObjectGuid::Empty)
    {
        if (_guid.IsEmpty())
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        unleashContexts[_guid.GetCounter()].push_back(ctx);
    }

    UnleashContextScope::UnleashContextScope(Player* player, SealType type, uint8 stacks, bool aoe, bool controlled)
        : UnleashContextScope(player, UnleashContext{ type, stacks, aoe, controlled })
    {
    }

    UnleashContextScope::~UnleashContextScope()
    {
        if (_guid.IsEmpty())
            return;

        // find-only: a logout in between has already erased the stack
        std::lock_guard<std::mutex> lock(stateLock);
        auto const itr = unleashContexts.find(_guid.GetCounter());
        if (itr == unleashContexts.end())
            return;

        if (!itr->second.empty())
            itr->second.pop_back();

        if (itr->second.empty())
            unleashContexts.erase(itr);
    }

    float GetUnleashMultiplier(Player const* player, UnleashContext const& ctx)
    {
        // (1 + 0.10 * stacks) * (1 + effectPct / 100) * (controlled ? 2 : 1)
        UnleashBonus const bonus = GetUnleashBonus(player, ctx.type);
        float multiplier = (1.0f + 0.10f * float(ctx.stacks)) * (1.0f + bonus.effectPct / 100.0f);
        if (ctx.controlled)
            multiplier *= 2.0f;

        return multiplier;
    }

    uint32 BeginJudgementCast(Player* player)
    {
        if (!player)
            return 0;

        SealState& state = GetOrCreateState(player->GetGUID().GetCounter());
        if (++state.judgementSerial == 0)   // 0 is "no cast has begun"
            state.judgementSerial = 1;

        state.claimedSerials.clear();
        return state.judgementSerial;
    }

    bool TryClaimJudgementCast(Player* player, uint32 guardKey)
    {
        if (!player)
            return false;

        SealState* state = FindState(player->GetGUID().GetCounter());
        // No cast has begun (a GM cast of an unleash outside the dispatcher): nothing to guard against
        if (!state || !state->judgementSerial)
            return true;

        auto const [itr, inserted] = state->claimedSerials.try_emplace(guardKey, state->judgementSerial);
        if (inserted)
            return true;

        if (itr->second == state->judgementSerial)
            return false;

        itr->second = state->judgementSerial;
        return true;
    }

    void RegisterJudgementCastHook(JudgementCastHook fn, bool onlyWhenPrimedConsumed)
    {
        if (fn)
            judgementCastHooks.push_back({ std::move(fn), onlyWhenPrimedConsumed });
    }

    void FireJudgementCastHooks(JudgementCastInfo const& info)
    {
        for (JudgementHookEntry const& entry : judgementCastHooks)
            if (!entry.onlyWhenPrimedConsumed || info.primedConsumed)
                entry.fn(info);
    }

    bool IsControlled(Unit const* target)
    {
        if (!target)
            return false;

        return target->HasAuraType(SPELL_AURA_MOD_STUN) || target->HasAuraType(SPELL_AURA_MOD_CONFUSE)
            || target->HasAuraType(SPELL_AURA_MOD_SILENCE) || target->HasAuraType(SPELL_AURA_MOD_PACIFY_SILENCE)
            || target->HasAuraType(SPELL_AURA_MOD_DISARM) || target->HasAuraType(SPELL_AURA_MOD_DISARM_OFFHAND)
            || target->HasAuraType(SPELL_AURA_MOD_DISARM_RANGED);
    }

    bool IsBossForStun(Unit const* target)
    {
        Creature const* creature = target ? target->ToCreature() : nullptr;
        return creature && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    int32 RoundPctAmount(float pct)
    {
        if (pct <= 0.0f)
            return 0;

        return std::max<int32>(1, int32(std::lround(pct)));
    }

    // ------------------------------------------------------------------
    // SHARED Part B5: class-wide baseline helpers
    // ------------------------------------------------------------------
    int32 CalculateAbsorbBonus(Unit* caster, AuraEffect const* aurEff, int32 /*amount*/)
    {
        // Returns the BONUS only (RET §4.6: callers write `amount += CalculateAbsorbBonus(...)`)
        if (!caster || !aurEff)
            return 0;

        // SCHOOL_ABSORB gets no engine spell-power bonus (SpellAuraEffects.cpp:527-530), so the generated
        // coefficient is applied here - the spell_priest.cpp Power Word: Shield shape (B5.11).
        SpellInfo const* spellInfo = aurEff->GetSpellInfo();
        uint8 const effIndex = aurEff->GetEffIndex();

        float bonus = spellInfo->Effects[effIndex].BonusMultiplier;
        bonus *= caster->SpellBaseHealingBonusDone(spellInfo->GetSchoolMask());
        bonus = caster->ApplyEffectModifiers(spellInfo, effIndex, bonus);
        bonus *= caster->CalculateLevelPenalty(spellInfo);

        return int32(bonus);
    }

    void FireConsecrationAppliedHooks(Unit* caster, DynamicObject* dynObj, int32 tickBasePoints)
    {
        for (ConsecrationAppliedHook const& hook : consecrationAppliedHooks)
            hook(caster, dynObj, tickBasePoints);
    }

    // ------------------------------------------------------------------
    // Retribution section (RETRIBUTION.md §6.12)
    // ------------------------------------------------------------------
    bool HasImprovedJudgements(Player const* player)
    {
        return player && (player->HasAura(PaladinData::SPELL_IMPROVED_JUDGEMENTS)
            || player->HasAura(PaladinData::SPELL_IMPROVED_JUDGEMENTS_25957)
            || player->HasAura(SPELL_IMPROVED_JUDGEMENTS_RANK3));
    }

    uint8 ModifyStackGainRet(Player* player, uint8 count, uint32 sourceSpellId, bool crit)
    {
        if (!player)
            return count;

        // Conviction (rank 3 capstone): a critting Crusader Strike / Hammer of Wrath / Exorcism / Divine Storm
        // grants 2. Wake of Ashes is never a source.
        if (crit && player->HasAura(PaladinData::SPELL_CONVICTION_20119))
        {
            if (sourceSpellId == PaladinData::SPELL_CRUSADER_STRIKE
                || sourceSpellId == PaladinData::SPELL_HAMMER_OF_WRATH
                || sourceSpellId == PaladinData::SPELL_EXORCISM
                || sourceSpellId == PaladinData::SPELL_DIVINE_STORM)
                count = std::max<uint8>(count, 2);
        }

        // Improved Judgements' capstone marker: +1 on the next grant, consumed
        if (player->HasAura(PaladinData::SPELL_IMPROVED_JUDGEMENTS_MARKER))
        {
            if (count < 255)
                ++count;

            player->RemoveAura(PaladinData::SPELL_IMPROVED_JUDGEMENTS_MARKER);
        }

        return count;
    }

    void OnStacksGainedRet(Player* player, uint8 gained)
    {
        if (!player || !gained)
            return;

        // Execution Sentence counter: only while the hammer is still on the tracked target
        if (RetState* ret = FindRetState(player->GetGUID().GetCounter()); ret && !ret->esTarget.IsEmpty())
        {
            Unit* target = ObjectAccessor::GetUnit(*player, ret->esTarget);
            if (target && target->HasAura(PaladinData::SPELL_EXECUTION_SENTENCE, player->GetGUID()))
                ret->esGained = uint8(std::min<uint32>(255, uint32(ret->esGained) + gained));
        }

        // Crusade ramp: +2% per stack gained while Avenging Wrath is up, capped at 15%
        if (player->HasAura(SPELL_CRUSADE_RANK3) && player->HasAura(PaladinData::SPELL_AVENGING_WRATH))
        {
            Aura* ramp = player->GetAura(PaladinData::SPELL_CRUSADE_RAMP, player->GetGUID());
            int32 current = 0;
            if (!ramp)
            {
                player->CastSpell(player, PaladinData::SPELL_CRUSADE_RAMP, TRIGGERED_FULL_MASK);
                ramp = player->GetAura(PaladinData::SPELL_CRUSADE_RAMP, player->GetGUID());
            }
            else if (AuraEffect const* existing = ramp->GetEffect(EFFECT_0))
                current = existing->GetAmount();

            if (!ramp)
                return;

            if (AuraEffect* effect = ramp->GetEffect(EFFECT_0))
            {
                effect->SetCanBeRecalculated(false);   // a later RecalculateAmount would reset the ramp
                effect->ChangeAmount(std::min(CRUSADE_RAMP_CAP, current + CRUSADE_RAMP_PER_STACK * int32(gained)));
            }
        }
    }

    void OnJudgementCastRet(JudgementCastInfo const& info)
    {
        // registered with onlyWhenPrimedConsumed = true, so this only runs on an unleash
        if (info.caster && info.caster->HasAura(SPELL_IMPROVED_JUDGEMENTS_RANK3))
            info.caster->CastSpell(info.caster, PaladinData::SPELL_IMPROVED_JUDGEMENTS_MARKER, TRIGGERED_FULL_MASK);
    }

    float GetSanctifiedSealsPct(Player const* player)
    {
        if (!player)
            return 0.0f;

        // Only the top learned rank is on the player; read it live (2 / 4 / 6)
        for (uint32 const rankId : { SPELL_SANCTIFIED_SEALS_RANK3, SPELL_SANCTIFIED_SEALS_RANK2,
            SPELL_SANCTIFIED_SEALS_RANK1 })
        {
            if (AuraEffect const* effect = player->GetAuraEffect(rankId, EFFECT_0))
            {
                float pct = float(effect->GetAmount());
                if (rankId == SPELL_SANCTIFIED_SEALS_RANK3)
                    pct += player->GetMasteryPercentage();   // additive, read live (R "Mastery hook")

                return pct;
            }
        }

        return 0.0f;
    }

    float GetSanctifiedSealsLightBuffPerStackPct(Player const* player)
    {
        if (!player || !player->HasAura(SPELL_SANCTIFIED_SEALS_RANK3))
            return 0.0f;

        return SANCTIFIED_SEALS_LIGHT_PER_MASTERY * player->GetMasteryPercentage();
    }

    void RegisterRetributionHooks()
    {
        static bool registered = false;   // called once from AddSC_paladin_retribution_spell_scripts()
        if (registered)
            return;

        registered = true;

        // Improved Judgements: Exorcism triggers the active seal's ability-form passive and chance auras
        RegisterSealPassiveMagicSource([](Player const* player, SpellInfo const* spellInfo)
        {
            return IsPaladinFamily(spellInfo) && (spellInfo->SpellFamilyFlags[1] & FAMILY_D1_EXORCISM)
                && HasImprovedJudgements(player);
        });

        // Blade of Justice releases the seal through its own echo (SHARED B1.6 "Ret's call"), so the
        // blade's own hit never also triggers the passive or the chance auras
        RegisterSealPassiveVeto([](Player const* /*player*/, SpellInfo const* spellInfo)
        {
            return IsPaladinFamily(spellInfo) && (spellInfo->SpellFamilyFlags[2] & FAMILY_D2_BLADE_OF_JUSTICE);
        });

        RegisterStackGainModifier(ModifyStackGainRet);
        RegisterStacksGainedListener(OnStacksGainedRet);
        RegisterJudgementCastHook(OnJudgementCastRet, true);

        RegisterUnleashBonusProvider([](Player const* player, SealType /*type*/, UnleashBonus& bonus)
        {
            bonus.effectPct += GetSanctifiedSealsPct(player);
            bonus.lightPerStackPct += GetSanctifiedSealsLightBuffPerStackPct(player);
        });
    }

    void LogRegistrySizes()
    {
        // A missing registration fails silently (no extra stack, no ramp), so the sizes are checkable at boot
        LOG_INFO("server.loading", "Paladin registries: {} stack-gain modifiers, {} stacks-gained listeners, "
            "{} judgement-cast hooks, {} unleash bonus providers, {} passive vetoes, {} magic sources, "
            "{} consecration hooks", stackGainModifiers.size(), stacksGainedListeners.size(),
            judgementCastHooks.size(), unleashBonusProviders.size(), sealPassiveVetoes.size(),
            sealPassiveMagicSources.size(), consecrationAppliedHooks.size());
    }

    void StartExecutionSentence(Player* player, ObjectGuid target)
    {
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        RetState& ret = retStates[player->GetGUID().GetCounter()];
        ret.esTarget = target;
        ret.esGained = 0;
    }

    ObjectGuid GetExecutionSentenceTarget(Player const* player)
    {
        if (!player)
            return ObjectGuid::Empty;

        RetState const* ret = FindRetState(player->GetGUID().GetCounter());
        return ret ? ret->esTarget : ObjectGuid::Empty;
    }

    uint8 GetExecutionSentenceGained(Player const* player)
    {
        if (!player)
            return 0;

        RetState const* ret = FindRetState(player->GetGUID().GetCounter());
        return ret ? ret->esGained : 0;
    }

    void EndExecutionSentence(Player* player)
    {
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        retStates.erase(player->GetGUID().GetCounter());
    }
}
