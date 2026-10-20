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
 * Shaman rework - Elemental spec scripts (shaman-rework S1a; docs/reworks/shaman-elemental-rework.md). Ids and
 * tunables come from ShamanData::; shared state hooks live in ShamanMechanics.
 *
 * Rules every script here follows (S1-NOTES section 3):
 *  - Only a player caster/owner does anything: NPCs cast 421, 8050 and 8056 and keep the stock behaviour. Every check
 *    reads the shaman's own talents, auras and totem slots, so a non-shaman with the talents gets do-nothing (Q21).
 *  - Lightning Overload copies roll nothing: they are triggered with no NOT_A_PROC (the proc system drops them) and
 *    every proc script also drops them by id. Echo (granted when a copy is cast) and Shamanism (the copy's own
 *    SpellScript) are the two named exceptions. Triggered spells never roll the shaman's procs (B25).
 *  - Proc rows that the scripts roll themselves (Lightning Overload, Lightning Mastery, Elemental Precision and
 *    Elemental Reach capstones) must proc at 100%: the scripted roll is the only one (Shaman::RollProcChance).
 *  - Amounts passed to ChangeAmount are live values (SKILL "Sign convention").
 */

#include "Creature.h"
#include "DataMap.h"
#include "GameTime.h"
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
#include "UnitScript.h"
#include <algorithm>
#include <array>
#include <initializer_list>
#include <list>
#include <span>

namespace
{
    // Talent rank chains (rank order). Each rank is a passive aura on the shaman.
    constexpr std::array<uint32, 3> LIGHTNING_OVERLOAD_RANKS = { ShamanData::SPELL_LIGHTNING_OVERLOAD,
        ShamanData::SPELL_LIGHTNING_OVERLOAD_30678, ShamanData::SPELL_LIGHTNING_OVERLOAD_30679 };
    constexpr std::array<uint32, 3> LAVA_FLOWS_RANKS = { ShamanData::SPELL_LAVA_FLOWS,
        ShamanData::SPELL_LAVA_FLOWS_51481, ShamanData::SPELL_LAVA_FLOWS_51482 };
    constexpr std::array<uint32, 3> UNRELENTING_STORM_RANKS = { ShamanData::SPELL_UNRELENTING_STORM,
        ShamanData::SPELL_UNRELENTING_STORM_30665, ShamanData::SPELL_UNRELENTING_STORM_30666 };
    constexpr std::array<uint32, 3> REVERBERATION_RANKS = { ShamanData::SPELL_REVERBERATION,
        ShamanData::SPELL_REVERBERATION_16113, ShamanData::SPELL_REVERBERATION_16114 };
    constexpr std::array<uint32, 3> SHAMANISM_RANKS = { ShamanData::SPELL_SHAMANISM,
        ShamanData::SPELL_SHAMANISM_62098, ShamanData::SPELL_SHAMANISM_62099 };
    constexpr std::array<uint32, 3> LIGHTNING_MASTERY_RANKS = { ShamanData::SPELL_LIGHTNING_MASTERY,
        ShamanData::SPELL_LIGHTNING_MASTERY_16579, ShamanData::SPELL_LIGHTNING_MASTERY_16580 };
    constexpr std::array<uint32, 3> DEVASTATION_RANKS = { ShamanData::SPELL_ELEMENTAL_DEVASTATION_30160,
        ShamanData::SPELL_ELEMENTAL_DEVASTATION, ShamanData::SPELL_ELEMENTAL_DEVASTATION_29180 };
    constexpr std::array<uint32, 2> ELEMENTAL_FOCUS_RANKS = { ShamanData::SPELL_ELEMENTAL_FOCUS,
        ShamanData::SPELL_ELEMENTAL_FOCUS_RANK2 };
    constexpr std::array<uint32, 3> ASTRAL_SHIFT_RANKS = { ShamanData::SPELL_ASTRAL_SHIFT,
        ShamanData::SPELL_ASTRAL_SHIFT_51478, ShamanData::SPELL_ASTRAL_SHIFT_51479 };
    constexpr std::array<uint32, 2> FUSION_RANKS = { ShamanData::SPELL_FUSION_RANK1, ShamanData::SPELL_FUSION_RANK2 };
    constexpr std::array<uint32, 1> POWER_OF_THE_ELEMENTS_RANKS = { ShamanData::SPELL_POWER_OF_THE_ELEMENTS };
    constexpr std::array<uint32, 1> ICEFURY_RANKS = { ShamanData::SPELL_ICEFURY };

    // Per-rank values the doc fixes and the brief has no const for (the script sets the buff amount by rank).
    constexpr std::array<int32, 3> LO_CHANCE_PCT = { ShamanData::LO_CHANCE_R1, ShamanData::LO_CHANCE_R2,
        ShamanData::LO_CHANCE_R3 };
    constexpr std::array<int32, 3> RAW_POWER_CHANCE_PCT = { ShamanData::RAW_POWER_CHANCE_R1,
        ShamanData::RAW_POWER_CHANCE_R2, ShamanData::RAW_POWER_CHANCE_R3 };
    constexpr std::array<int32, 3> DEVASTATION_PROC_CHANCE_PCT = { ShamanData::DEVASTATION_PC_R1,
        ShamanData::DEVASTATION_PC_R2, ShamanData::DEVASTATION_PC_R3 };
    constexpr std::array<int32, 3> UNRELENTING_STORM_HASTE_TENTHS = { ShamanData::US_HASTE_TENTHS_R1,
        ShamanData::US_HASTE_TENTHS_R2, ShamanData::US_HASTE_TENTHS_R3 };

    // Raw Power has no stack cap: the engine's uint8 stack counter is the cap (known-hard item 7)
    constexpr uint32 RAW_POWER_ENGINE_CAP = 255;

    // A cast-time Nature spell counts as "being cast" for Astral Shift until its cast time plus this margin
    // (pushback) has passed, unless it finished first
    constexpr uint32 ASTRAL_SHIFT_CAST_MARGIN_MS = 1000;

    // How often the plain Astral Shift checks that the stun, fear or silence still holds
    constexpr uint32 ASTRAL_SHIFT_WATCH_MS = 250;
    // A watcher this late past its due time was dropped with the player's events (far teleport)
    constexpr uint32 ASTRAL_SHIFT_WATCH_LATE_MS = 2000;

    constexpr uint32 FAMILY_FLAG0_IMBUE_ATTACKS = 0x1200000;  // Frostbrand Attack d0 b24, Flametongue Attack d0 b21

    // Per-player state the Elemental scripts share (lives as long as the player object)
    struct ElementalState : DataMap::Base
    {
        Spell const* precisionConsumer = nullptr;  // the Elemental Blast that spent Elemental Precision's buff
        uint32 natureCastUntilMs = 0;              // Astral Shift capstone: a Nature spell is being cast until then
        uint32 reachReadyMs = 0;                   // Elemental Reach capstone internal cooldown
        uint32 astralShiftWatchDueMs = 0;          // the plain Astral Shift watcher's next run, 0 when none
    };

    constexpr char const* ELEMENTAL_STATE_KEY = "shaman_elemental_state";

    ElementalState* GetState(Player* player)
    {
        return player->CustomData.GetDefault<ElementalState>(ELEMENTAL_STATE_KEY);
    }

    uint32 NowMs()
    {
        return uint32(GameTime::GetGameTimeMS().count());
    }

    // Once-per-cast guard: one proc attempt per Spell object per world tick (paladin CastGuard shape). A Chain
    // Lightning's targets are all hit in the same tick; the ms check keeps a reused Spell address from matching.
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

    // 1-based position of `spellId` in `ranks`, 0 if absent (the proccing talent aura's own rank)
    uint8 RankOf(uint32 spellId, std::span<uint32 const> ranks)
    {
        for (std::size_t i = 0; i < ranks.size(); ++i)
            if (ranks[i] == spellId)
                return uint8(i + 1);

        return 0;
    }

    bool HasElemental(Player const* player, uint8 elementalBit)
    {
        return (Shaman::GetActiveElementals(player) & elementalBit) != 0;
    }

    // The player behind a proc on a talent aura: the aura's owner, and only when it is the actor itself
    Player* GetProcPlayer(Unit* auraOwner, ProcEventInfo& eventInfo)
    {
        Player* player = auraOwner ? auraOwner->ToPlayer() : nullptr;
        if (!player || eventInfo.GetActor() != player)
            return nullptr;

        return player;
    }

    // The shared "may this event roll an Elemental proc" gate: a non-triggered spell event of the shaman's own that
    // is not an overload copy (B25)
    bool IsOwnSpellEvent(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        Spell const* procSpell = eventInfo.GetProcSpell();
        if (!spellInfo || !procSpell || procSpell->IsTriggered())
            return false;

        return !Shaman::IsOverloadCopy(spellInfo->Id);
    }

    bool IsShamanSpell(SpellInfo const* spellInfo)
    {
        return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_SHAMAN;
    }

    bool IsDirectDamage(ProcEventInfo& eventInfo)
    {
        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        return damageInfo && damageInfo->GetDamageType() == SPELL_DIRECT_DAMAGE;
    }

    // Sets `amount` (live) on every effect of `aura` whose aura type is in `types`; only when it moved
    void SetAuraAmount(Aura* aura, std::initializer_list<AuraType> types, int32 amount)
    {
        if (!aura)
            return;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (!effect || std::find(types.begin(), types.end(), effect->GetAuraType()) == types.end())
                continue;

            if (effect->GetAmount() != amount)
                effect->ChangeAmount(amount);
        }
    }

    // Casts `spellId` on the player (create or refresh) and leaves it at min(current + add, max) charges, or stacks
    // when the aura uses no charges. A refresh resets charges to the DBC maximum, so the count is always re-set.
    Aura* AddAuraCount(Player* player, uint32 spellId, uint32 add, uint32 max)
    {
        uint32 current = 0;
        if (Aura const* aura = player->GetAura(spellId))
            current = aura->IsUsingCharges() ? aura->GetCharges() : aura->GetStackAmount();

        uint32 const desired = std::min<uint32>(std::min(current + add, max), RAW_POWER_ENGINE_CAP);
        player->CastSpell(player, spellId, true);

        Aura* aura = player->GetAura(spellId);
        if (!aura || !desired)
            return aura;

        if (aura->IsUsingCharges())
        {
            if (aura->GetCharges() != desired)
                aura->SetCharges(uint8(desired));
        }
        else if (aura->GetStackAmount() != desired)
            aura->SetStackAmount(uint8(desired));

        return aura;
    }

    // Clears a spell's own cooldown and its category cooldown (Lava Burst Category 1224, known-hard item 6)
    void ResetCooldown(Player* player, uint32 spellId)
    {
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo)
            return;

        if (uint32 const category = spellInfo->GetCategory())
            player->RemoveCategoryCooldown(category);

        player->RemoveSpellCooldown(spellId, true);
    }

    // Shamanism: each Lightning Bolt / Chain Lightning damage event (copies included) has SHAMANISM_CHANCE x Proc
    // Chance to take SHAMANISM_CDR_MS off Elemental Mastery and both Thunderstorm ranks, in real time (known-hard 9)
    void TryShamanism(Player* player)
    {
        if (!Shaman::GetTalentRank(player, SHAMANISM_RANKS))
            return;

        if (!Shaman::RollProcChance(player, float(ShamanData::SHAMANISM_CHANCE)))
            return;

        int32 const cut = -int32(ShamanData::SHAMANISM_CDR_MS);
        player->ModifySpellCooldown(ShamanData::SPELL_ELEMENTAL_MASTERY, cut);
        player->ModifySpellCooldown(ShamanData::SPELL_THUNDERSTORM, cut);
        player->ModifySpellCooldown(ShamanData::SPELL_THUNDERSTORM_RANK2, cut);
    }

    // Stunned, feared or silenced: the states Astral Shift covers
    bool IsAstralShiftControlled(Unit const* unit)
    {
        return unit->HasUnitState(UNIT_STATE_STUNNED) || unit->HasUnitState(UNIT_STATE_FLEEING) ||
            unit->HasUnitFlag(UNIT_FLAG_SILENCED);
    }

    void ApplyAstralShift(Player* player, uint32 spellId, int32 pct)
    {
        player->CastSpell(player, spellId, true);
        SetAuraAmount(player->GetAura(spellId), { SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN }, -pct);
    }

    // The plain Astral Shift lasts while the control does: re-checked every ASTRAL_SHIFT_WATCH_MS. The event lives in
    // the player's own m_Events, so the captured pointer is valid whenever it runs.
    void WatchAstralShift(Player* player)
    {
        ElementalState* state = GetState(player);
        uint32 const now = NowMs();
        if (state->astralShiftWatchDueMs && now <= state->astralShiftWatchDueMs + ASTRAL_SHIFT_WATCH_LATE_MS)
            return;

        state->astralShiftWatchDueMs = now + ASTRAL_SHIFT_WATCH_MS;
        player->m_Events.AddEventAtOffset([player]()
        {
            GetState(player)->astralShiftWatchDueMs = 0;

            if (!player->IsAlive() || !IsAstralShiftControlled(player) ||
                !Shaman::GetTalentRank(player, ASTRAL_SHIFT_RANKS))
            {
                player->RemoveAurasDueToSpell(ShamanData::SPELL_ASTRAL_SHIFT_BUFF);
                return;
            }

            // The empowered shift replaces the plain one while it lasts; the plain one returns if control outlasts it
            if (player->HasAura(ShamanData::SPELL_ASTRAL_SHIFT_EMPOWERED))
                player->RemoveAurasDueToSpell(ShamanData::SPELL_ASTRAL_SHIFT_BUFF);
            else if (!player->HasAura(ShamanData::SPELL_ASTRAL_SHIFT_BUFF))
                ApplyAstralShift(player, ShamanData::SPELL_ASTRAL_SHIFT_BUFF, ShamanData::ASTRAL_SHIFT_PLAIN_PCT);

            WatchAstralShift(player);
        }, Milliseconds(ASTRAL_SHIFT_WATCH_MS));
    }
}

// -30675 Lightning Overload (replaces spell_sha_lightning_overload). Rolls per target hit (Chain Lightning per
// jump): rank chance 6/13/20%, x3 on a crit, x Proc Chance, capped at 100%. A success casts the parent's copy at
// that target (triggered, no NOT_A_PROC, so the copy rolls nothing) and grants 1 Echo with Booming Echoes rank 3.
// Rank 3 capstone: Lava Burst also overloads while the Fire Elemental is active. The spell_proc row must proc at
// 100% (the scripted roll is the only one).
class spell_sha_ele_lightning_overload : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_lightning_overload);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_LIGHTNING_BOLT_OVERLOAD,
            ShamanData::SPELL_CHAIN_LIGHTNING_OVERLOAD, ShamanData::SPELL_LAVA_BURST_OVERLOAD,
            ShamanData::SPELL_BOOMING_ECHOES_RANK3 });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    // The copy for a parent spell id; 0 for anything else (or a Lava Burst without the capstone)
    uint32 GetCopySpell(Player const* player, uint32 parentId) const
    {
        switch (parentId)
        {
            case ShamanData::SPELL_LIGHTNING_BOLT:
                return ShamanData::SPELL_LIGHTNING_BOLT_OVERLOAD;
            case ShamanData::SPELL_CHAIN_LIGHTNING:
                return ShamanData::SPELL_CHAIN_LIGHTNING_OVERLOAD;
            case ShamanData::SPELL_LAVA_BURST:
                if (GetId() == ShamanData::SPELL_LIGHTNING_OVERLOAD_30679 &&
                    HasElemental(player, Shaman::ELEMENTAL_MASK_FIRE))
                    return ShamanData::SPELL_LAVA_BURST_OVERLOAD;
                return 0;
            default:
                return 0;
        }
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || !IsOwnSpellEvent(eventInfo))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsAlive() || !(eventInfo.GetHitMask() & (PROC_HIT_NORMAL | PROC_HIT_CRITICAL)))
            return false;

        if (!GetCopySpell(player, eventInfo.GetSpellInfo()->Id))
            return false;

        uint8 const rank = RankOf(GetId(), LIGHTNING_OVERLOAD_RANKS);
        if (!rank)
            return false;

        float chance = float(LO_CHANCE_PCT[rank - 1]);
        if (eventInfo.GetHitMask() & PROC_HIT_CRITICAL)
            chance *= float(ShamanData::LO_CRIT_MULT);

        // Proc Chance multiplies the base; anything at or above 100% always succeeds (cap 100%)
        return Shaman::RollProcChance(player, std::min(chance, 100.0f));
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        Unit* target = eventInfo.GetActionTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !target || !spellInfo)
            return;

        uint32 const copy = GetCopySpell(player, spellInfo->Id);
        if (!copy)
            return;

        // A copy that fails its cast (target gone, line of sight) grants nothing
        if (player->CastSpell(target, copy, true) != SPELL_CAST_OK)
            return;

        // Booming Echoes capstone: 1 Echo per copy (per target for Chain Lightning), refreshed to ECHO_DURATION_MS
        if (player->HasAura(ShamanData::SPELL_BOOMING_ECHOES_RANK3))
            Shaman::AddEcho(player, 1);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_lightning_overload::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_lightning_overload::HandleProc);
    }
};

// 202591 Lightning Bolt overload, 202592 Chain Lightning overload, 202593 Lava Burst overload - the copies roll no
// aura procs; Shamanism reaches the Lightning Bolt and Chain Lightning copies here, once per damage event. A copy hits
// only its own target: the Chain Lightning copy carries d0 b1, so Frostbrand / Storm SPELLMOD_JUMP_TARGETS would give
// it jumps; the chain list (primary excluded) is emptied.
class spell_sha_ele_overload_copy : public SpellScript
{
    PrepareSpellScript(spell_sha_ele_overload_copy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_ELEMENTAL_MASTERY, ShamanData::SPELL_THUNDERSTORM,
            ShamanData::SPELL_THUNDERSTORM_RANK2 });
    }

    void HandleAfterHit()
    {
        uint32 const id = GetSpellInfo()->Id;
        if (id != ShamanData::SPELL_LIGHTNING_BOLT_OVERLOAD && id != ShamanData::SPELL_CHAIN_LIGHTNING_OVERLOAD)
            return;

        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || GetHitDamage() <= 0)
            return;

        TryShamanism(player);
    }

    void FilterJumps(std::list<WorldObject*>& targets)
    {
        targets.clear();
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sha_ele_overload_copy::FilterJumps, EFFECT_0,
            TARGET_UNIT_TARGET_ENEMY);
        AfterHit += SpellHitFn(spell_sha_ele_overload_copy::HandleAfterHit);
    }
};

// 403 Lightning Bolt, 421 Chain Lightning, 51505 Lava Burst, 202282 Elemental Blast, 8042 Earth Shock, 8050 Flame
// Shock (replaces spell_sha_flame_shock's Lava Flows dispel), 8056 Frost Shock - the Elemental cast and hit hooks.
// A player caster only (NPCs cast 421, 8050, 8056); triggered casts do nothing.
//  BeforeCast: remembers the Unrelenting Storm "ready" buff (Chain Lightning), the Icefury charges (Frost Shock)
//              and the Elemental Precision buff (Elemental Blast) before the cast spends them.
//  AfterCast (once per cast): Unrelenting Storm stack / Chain Lightning consume + debuff, Gathering Flames, Lava
//              Flows haste, Icefury grant, Fusion pick.
//  AfterHit (per damage event): Shamanism (Lightning Bolt, Chain Lightning), Reverberation grant (shocks), Earth
//              Shock's Echo spend, Icefury's Water-window mana.
//  CheckCast: records a cast-time Nature spell for the Astral Shift capstone.
class spell_sha_ele_spell_hooks : public SpellScript
{
    PrepareSpellScript(spell_sha_ele_spell_hooks);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_UNRELENTING_STORM_BUFF,
            ShamanData::SPELL_UNRELENTING_STORM_READY, ShamanData::SPELL_UNRELENTING_STORM_DEBUFF,
            ShamanData::SPELL_GATHERING_FLAMES, ShamanData::SPELL_ICEFURY_CHARGES, ShamanData::SPELL_FUSION_FIRE,
            ShamanData::SPELL_FUSION_STORM, ShamanData::SPELL_FUSION_MASTERY, ShamanData::SPELL_REVERBERATION_EARTH,
            ShamanData::SPELL_REVERBERATION_FROST, ShamanData::SPELL_REVERBERATION_FLAME,
            ShamanData::SPELL_BOOMING_ECHO, ShamanData::SPELL_PRECISION_BUFF, ShamanData::SPELL_ELEMENTAL_MASTERY,
            ShamanData::SPELL_THUNDERSTORM, ShamanData::SPELL_THUNDERSTORM_RANK2 });
    }

    bool _usReady = false;
    uint32 _icefuryBefore = 0;

    Player* GetPlayerCaster()
    {
        if (GetSpell()->IsTriggered())
            return nullptr;

        Unit* caster = GetCaster();
        return caster ? caster->ToPlayer() : nullptr;
    }

    static uint32 GetIcefuryCount(Player const* player)
    {
        Aura const* aura = player->GetAura(ShamanData::SPELL_ICEFURY_CHARGES);
        if (!aura)
            return 0;

        return aura->IsUsingCharges() ? aura->GetCharges() : aura->GetStackAmount();
    }

    static bool IsNatureCast(uint32 spellId)
    {
        return spellId == ShamanData::SPELL_LIGHTNING_BOLT || spellId == ShamanData::SPELL_CHAIN_LIGHTNING ||
            spellId == ShamanData::SPELL_ELEMENTAL_BLAST;
    }

    SpellCastResult HandleCheckCast()
    {
        Player* player = GetPlayerCaster();
        if (!player || !IsNatureCast(GetSpellInfo()->Id))
            return SPELL_CAST_OK;

        // Prepare-time check: the cast time is not on the Spell yet, so compute it (no Spell passed: no charge use)
        uint32 const castMs = GetSpellInfo()->CalcCastTime(player);
        if (castMs)
            GetState(player)->natureCastUntilMs = NowMs() + castMs + ASTRAL_SHIFT_CAST_MARGIN_MS;

        return SPELL_CAST_OK;
    }

    void HandleBeforeCast()
    {
        Player* player = GetPlayerCaster();
        if (!player)
            return;

        switch (GetSpellInfo()->Id)
        {
            case ShamanData::SPELL_CHAIN_LIGHTNING:
                _usReady = player->HasAura(ShamanData::SPELL_UNRELENTING_STORM_READY);
                break;
            case ShamanData::SPELL_FROST_SHOCK:
                _icefuryBefore = GetIcefuryCount(player);
                break;
            case ShamanData::SPELL_ELEMENTAL_BLAST:
                // The Elemental Blast that spends the guaranteed crit never rolls Elemental Precision's capstone
                GetState(player)->precisionConsumer =
                    player->HasAura(ShamanData::SPELL_PRECISION_BUFF) ? GetSpell() : nullptr;
                break;
            default:
                break;
        }
    }

    // Lightning Bolt, Lava Burst, Elemental Blast: one Unrelenting Storm stack; the capstone readies Chain Lightning
    // at UNRELENTING_STORM_STACKS
    void AddUnrelentingStorm(Player* player)
    {
        uint8 const rank = Shaman::GetTalentRank(player, UNRELENTING_STORM_RANKS);
        if (!rank)
            return;

        uint32 const maxStacks = uint32(ShamanData::UNRELENTING_STORM_STACKS);
        Aura* aura = AddAuraCount(player, ShamanData::SPELL_UNRELENTING_STORM_BUFF, 1, maxStacks);
        if (!aura)
            return;

        // 0.5/1/1.5% haste per stack, rounded to whole percent on the total
        int32 const total = (UNRELENTING_STORM_HASTE_TENTHS[rank - 1] * int32(aura->GetStackAmount()) + 5) / 10;
        SetAuraAmount(aura, { SPELL_AURA_MELEE_SLOW, SPELL_AURA_MOD_CASTING_SPEED_NOT_STACK,
            SPELL_AURA_MOD_MELEE_HASTE, SPELL_AURA_HASTE_SPELLS }, total);

        if (std::size_t(rank) == UNRELENTING_STORM_RANKS.size() && aura->GetStackAmount() >= maxStacks)
            player->CastSpell(player, ShamanData::SPELL_UNRELENTING_STORM_READY, true);
    }

    // Chain Lightning that spent the ready buff: the stacks go and its primary target takes the debuff
    void ConsumeUnrelentingStorm(Player* player)
    {
        if (!_usReady)
            return;

        // The ready buff itself is spent by its own spell_proc row (PROC_ATTR_REQ_SPELLMOD), never here
        player->RemoveAurasDueToSpell(ShamanData::SPELL_UNRELENTING_STORM_BUFF);

        Unit* target = GetExplTargetUnit();
        if (target && target->IsAlive() && target != player)
            player->CastSpell(target, ShamanData::SPELL_UNRELENTING_STORM_DEBUFF, true);
    }

    void TryLavaFlowsHaste(Player* player)
    {
        if (uint32 const haste = Shaman::LavaFlowsHasteSpell(Shaman::GetTalentRank(player, LAVA_FLOWS_RANKS)))
            player->CastSpell(player, haste, true);
    }

    // Power of the Elements: each Lava Burst cast in the Fire window adds a Gathering Flames stack
    void TryGatheringFlames(Player* player)
    {
        if (!Shaman::GetTalentRank(player, POWER_OF_THE_ELEMENTS_RANKS) ||
            !HasElemental(player, Shaman::ELEMENTAL_MASK_FIRE))
            return;

        AddAuraCount(player, ShamanData::SPELL_GATHERING_FLAMES, 1, uint32(ShamanData::GATHERING_FLAMES_MAX));
    }

    // Icefury: 1 charge per Elemental Blast (+ICEFURY_WATER_EXTRA in the Water window), up to the maximum
    void TryIcefuryGrant(Player* player)
    {
        if (!Shaman::GetTalentRank(player, ICEFURY_RANKS))
            return;

        uint32 charges = 1;
        if (HasElemental(player, Shaman::ELEMENTAL_MASK_WATER))
            charges += uint32(ShamanData::ICEFURY_WATER_EXTRA);

        AddAuraCount(player, ShamanData::SPELL_ICEFURY_CHARGES, charges, uint32(ShamanData::ICEFURY_MAX_CHARGES));
    }

    // Fusion of Elements capstone: the bonus by active elemental, Fire > Storm > Mastery (Q13); replaces the last
    void TryFusion(Player* player)
    {
        if (std::size_t(Shaman::GetTalentRank(player, FUSION_RANKS)) != FUSION_RANKS.size())
            return;

        uint8 const active = Shaman::GetActiveElementals(player);
        uint32 buff = ShamanData::SPELL_FUSION_MASTERY;
        if (active & Shaman::ELEMENTAL_MASK_FIRE)
            buff = ShamanData::SPELL_FUSION_FIRE;
        else if (active & Shaman::ELEMENTAL_MASK_STORM)
            buff = ShamanData::SPELL_FUSION_STORM;

        for (uint32 fusion : { ShamanData::SPELL_FUSION_FIRE, ShamanData::SPELL_FUSION_STORM,
            ShamanData::SPELL_FUSION_MASTERY })
            if (fusion != buff)
                player->RemoveAurasDueToSpell(fusion);

        player->CastSpell(player, buff, true);
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerCaster();
        if (!player)
            return;

        uint32 const id = GetSpellInfo()->Id;
        if (IsNatureCast(id))
            GetState(player)->natureCastUntilMs = 0;  // finished: no longer "being cast"

        switch (id)
        {
            case ShamanData::SPELL_LIGHTNING_BOLT:
                AddUnrelentingStorm(player);
                break;
            case ShamanData::SPELL_CHAIN_LIGHTNING:
                ConsumeUnrelentingStorm(player);
                break;
            case ShamanData::SPELL_LAVA_BURST:
                AddUnrelentingStorm(player);
                TryGatheringFlames(player);
                TryLavaFlowsHaste(player);
                break;
            case ShamanData::SPELL_ELEMENTAL_BLAST:
                AddUnrelentingStorm(player);
                TryIcefuryGrant(player);
                TryFusion(player);
                break;
            case ShamanData::SPELL_FLAME_SHOCK:
                TryLavaFlowsHaste(player);
                break;
            default:
                break;
        }
    }

    // Reverberation: a shock that deals damage grants the buff naming it (it raises the other two shocks and
    // Elemental Blast); one variant at a time
    void TryReverberation(Player* player, uint32 shockId)
    {
        if (!Shaman::GetTalentRank(player, REVERBERATION_RANKS))
            return;

        uint32 buff = 0;
        switch (shockId)
        {
            case ShamanData::SPELL_EARTH_SHOCK:
                buff = ShamanData::SPELL_REVERBERATION_EARTH;
                break;
            case ShamanData::SPELL_FROST_SHOCK:
                buff = ShamanData::SPELL_REVERBERATION_FROST;
                break;
            case ShamanData::SPELL_FLAME_SHOCK:
                buff = ShamanData::SPELL_REVERBERATION_FLAME;
                break;
            default:
                return;
        }

        for (uint32 variant : { ShamanData::SPELL_REVERBERATION_EARTH, ShamanData::SPELL_REVERBERATION_FROST,
            ShamanData::SPELL_REVERBERATION_FLAME })
            if (variant != buff)
                player->RemoveAurasDueToSpell(variant);

        player->CastSpell(player, buff, true);
    }

    // Earth Shock reads Echo when it lands (its damage already took the stacks): it spends all of them, or half
    // rounded down but at least 1 while the Earth Elemental is active (1 -> 1, 3 -> 1, 4 -> 2)
    void SpendEcho(Player* player)
    {
        Aura* echo = player->GetAura(ShamanData::SPELL_BOOMING_ECHO);
        if (!echo)
            return;

        if (!HasElemental(player, Shaman::ELEMENTAL_MASK_EARTH))
        {
            echo->Remove();
            return;
        }

        uint8 const stacks = echo->GetStackAmount();
        uint8 const spent = std::max<uint8>(1, uint8(stacks / 2));
        if (spent >= stacks)
            echo->Remove();
        else if (spent)
            echo->SetStackAmount(uint8(stacks - spent));
    }

    // Icefury: a Frost Shock that spent a charge while any elemental is active restores ICEFURY_MANA_PCT of max mana
    void TryIcefuryMana(Player* player)
    {
        if (!_icefuryBefore || GetIcefuryCount(player) >= _icefuryBefore)
            return;

        _icefuryBefore = 0;
        if (!Shaman::GetActiveElementals(player))
            return;

        uint32 const mana = CalculatePct(player->GetMaxPower(POWER_MANA), ShamanData::ICEFURY_MANA_PCT);
        if (mana)
            player->EnergizeBySpell(player, ShamanData::SPELL_ICEFURY_CHARGES, mana, POWER_MANA);
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerCaster();
        if (!player)
            return;

        uint32 const id = GetSpellInfo()->Id;
        bool const dealtDamage = GetHitDamage() > 0;
        switch (id)
        {
            case ShamanData::SPELL_LIGHTNING_BOLT:
            case ShamanData::SPELL_CHAIN_LIGHTNING:
                if (dealtDamage)
                    TryShamanism(player);
                break;
            case ShamanData::SPELL_EARTH_SHOCK:
                if (dealtDamage)
                    TryReverberation(player, id);
                SpendEcho(player);
                break;
            case ShamanData::SPELL_FROST_SHOCK:
                if (dealtDamage)
                    TryReverberation(player, id);
                TryIcefuryMana(player);
                break;
            case ShamanData::SPELL_FLAME_SHOCK:
                if (dealtDamage)
                    TryReverberation(player, id);
                break;
            default:
                break;
        }
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_sha_ele_spell_hooks::HandleCheckCast);
        BeforeCast += SpellCastFn(spell_sha_ele_spell_hooks::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_sha_ele_spell_hooks::HandleAfterCast);
        AfterHit += SpellHitFn(spell_sha_ele_spell_hooks::HandleAfterHit);
    }
};

// -16164 Elemental Focus (replaces spell_sha_elemental_focus) - a Fire, Frost or Nature damage crit puts
// Clearcasting (16246) at 2 charges with the rank's cost cut (15/30%). Not copies, not triggered spells (imbue
// attacks).
class spell_sha_ele_elemental_focus : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_elemental_focus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_CLEARCASTING });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcPlayer(GetUnitOwner(), eventInfo) || !IsOwnSpellEvent(eventInfo))
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return !(IsShamanSpell(spellInfo) && (spellInfo->SpellFamilyFlags[0] & FAMILY_FLAG0_IMBUE_ATTACKS));
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        uint8 const rank = RankOf(GetId(), ELEMENTAL_FOCUS_RANKS);
        if (!player || !rank)
            return;

        player->CastSpell(player, ShamanData::SPELL_CLEARCASTING, true);
        Aura* aura = player->GetAura(ShamanData::SPELL_CLEARCASTING);
        if (!aura)
            return;

        aura->SetCharges(aura->CalcMaxCharges());

        // The rank's cost cut is the proc effect's own value (talent rank spell effect 0: 15 / 30)
        AuraEffect const* rankEffect = GetEffect(EFFECT_0);
        if (!rankEffect)
            return;

        int32 const amount = -rankEffect->GetAmount();
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (effect && effect->GetAuraType() == SPELL_AURA_ADD_PCT_MODIFIER &&
                effect->GetMiscValue() == SPELLMOD_COST && effect->GetAmount() != amount)
                effect->ChangeAmount(amount);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_elemental_focus::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_elemental_focus::HandleProc);
    }
};

// -30160 Elemental Devastation - a non-periodic Fire, Frost or Nature shaman spell crit raises Proc Chance by
// 3/6/10% for 10 sec (refresh, no stack). Classless: shaman spells only (Q21). Not copies, not triggered spells.
class spell_sha_ele_devastation : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_devastation);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_DEVASTATION_BUFF });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcPlayer(GetUnitOwner(), eventInfo) && IsOwnSpellEvent(eventInfo) &&
            IsShamanSpell(eventInfo.GetSpellInfo()) && IsDirectDamage(eventInfo);
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        uint8 const rank = RankOf(GetId(), DEVASTATION_RANKS);
        if (!player || !rank)
            return;

        player->CastSpell(player, ShamanData::SPELL_DEVASTATION_BUFF, true);
        SetAuraAmount(player->GetAura(ShamanData::SPELL_DEVASTATION_BUFF), { SPELL_AURA_MOD_CUSTOM_STAT_PCT },
            DEVASTATION_PROC_CHANCE_PCT[rank - 1]);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_devastation::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_devastation::HandleProc);
    }
};

// -16578 Lightning Mastery - once per crit cast: a Lightning Bolt / Chain Lightning crit first rolls Lightning
// Mastery (LM_CHANCE_PER_STACK % per Raw Power stack x Proc Chance), spending all Raw Power; otherwise, while
// Lightning Mastery is not up, any crit cast rolls 33/66/100% x Proc Chance for a Raw Power stack (15 sec,
// refreshed, engine cap). No copies.
class spell_sha_ele_lightning_mastery : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_lightning_mastery);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_RAW_POWER, ShamanData::SPELL_LIGHTNING_MASTERY_BUFF });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    CastGuard _guard;

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcPlayer(GetUnitOwner(), eventInfo) || !IsOwnSpellEvent(eventInfo) ||
            !(eventInfo.GetHitMask() & PROC_HIT_CRITICAL))
            return false;

        return _guard.Claim(eventInfo.GetProcSpell());
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        uint8 const rank = RankOf(GetId(), LIGHTNING_MASTERY_RANKS);
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!player || !rank || !spellInfo)
            return;

        if (player->HasAura(ShamanData::SPELL_LIGHTNING_MASTERY_BUFF))
            return;

        bool const lightning = spellInfo->Id == ShamanData::SPELL_LIGHTNING_BOLT ||
            spellInfo->Id == ShamanData::SPELL_CHAIN_LIGHTNING;
        if (lightning)
        {
            if (Aura const* rawPower = player->GetAura(ShamanData::SPELL_RAW_POWER))
            {
                float const chance = float(ShamanData::LM_CHANCE_PER_STACK) * float(rawPower->GetStackAmount());
                if (Shaman::RollProcChance(player, chance))
                {
                    player->RemoveAurasDueToSpell(ShamanData::SPELL_RAW_POWER);
                    player->CastSpell(player, ShamanData::SPELL_LIGHTNING_MASTERY_BUFF, true);
                    return;
                }
            }
        }

        if (Shaman::RollProcChance(player, float(RAW_POWER_CHANCE_PCT[rank - 1])))
            AddAuraCount(player, ShamanData::SPELL_RAW_POWER, 1, RAW_POWER_ENGINE_CAP);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_lightning_mastery::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_lightning_mastery::HandleProc);
    }
};

// 30674 Elemental Precision rank 3 - a non-periodic spell crit, once per cast, 10% x Proc Chance: resets Elemental
// Blast's cooldown and grants the guaranteed-crit buff for 20 sec. Never the Elemental Blast that spent the buff,
// never a copy.
class spell_sha_ele_precision_capstone : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_precision_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_PRECISION_BUFF, ShamanData::SPELL_ELEMENTAL_BLAST });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    CastGuard _guard;

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || !IsOwnSpellEvent(eventInfo) || !(eventInfo.GetHitMask() & PROC_HIT_CRITICAL) ||
            !IsDirectDamage(eventInfo))
            return false;

        if (eventInfo.GetSpellInfo()->Id == ShamanData::SPELL_ELEMENTAL_BLAST &&
            GetState(player)->precisionConsumer == eventInfo.GetProcSpell())
            return false;

        if (!_guard.Claim(eventInfo.GetProcSpell()))
            return false;

        return Shaman::RollProcChance(player, float(ShamanData::PRECISION_CAPSTONE_CHANCE));
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        if (!player)
            return;

        ResetCooldown(player, ShamanData::SPELL_ELEMENTAL_BLAST);
        player->CastSpell(player, ShamanData::SPELL_PRECISION_BUFF, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_precision_capstone::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_precision_capstone::HandleProc);
    }
};

// 29000 Elemental Reach rank 2 - a direct Fire, Frost or Nature shaman spell hit on a target more than
// REACH_MIN_DISTANCE_YD away (measured at the hit) has 33% x Proc Chance to grant +6% magic damage for 10 sec;
// internal cooldown REACH_ICD_MS from a success. Classless: shaman spells only (Q21).
class spell_sha_ele_reach_capstone : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_reach_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_REACH_BUFF });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetProcPlayer(GetUnitOwner(), eventInfo);
        if (!player || !IsOwnSpellEvent(eventInfo) || !IsShamanSpell(eventInfo.GetSpellInfo()) ||
            !IsDirectDamage(eventInfo))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || target == player || player->GetDistance(target) <= ShamanData::REACH_MIN_DISTANCE_YD)
            return false;

        if (NowMs() < GetState(player)->reachReadyMs)
            return false;

        return Shaman::RollProcChance(player, float(ShamanData::REACH_CAPSTONE_CHANCE));
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        if (!player)
            return;

        GetState(player)->reachReadyMs = NowMs() + uint32(ShamanData::REACH_ICD_MS);
        player->CastSpell(player, ShamanData::SPELL_REACH_BUFF, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_reach_capstone::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_reach_capstone::HandleProc);
    }
};

// 51482 Lava Flows rank 3 (Lava Surge) - the spell_proc row rolls 15% (native, Proc Chance applies) on the
// shaman's own Flame Shock periodic damage, ICD 6 sec: resets Lava Burst (its category cooldown) and grants the
// instant-cast buff.
class spell_sha_ele_lava_surge : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_lava_surge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_LAVA_SURGE_BUFF, ShamanData::SPELL_LAVA_BURST });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return GetProcPlayer(GetUnitOwner(), eventInfo) && spellInfo &&
            spellInfo->Id == ShamanData::SPELL_FLAME_SHOCK;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner()->ToPlayer();
        if (!player)
            return;

        ResetCooldown(player, ShamanData::SPELL_LAVA_BURST);
        player->CastSpell(player, ShamanData::SPELL_LAVA_SURGE_BUFF, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_ele_lava_surge::CheckProc);
        OnProc += AuraProcFn(spell_sha_ele_lava_surge::HandleProc);
    }
};

// 16246 Clearcasting (second script; spell_sha_clearcasting is unbound, Decision 1) - Elemental Fury rank 3: while
// Clearcasting is up the hidden capstone aura adds Nature +8% and other magic +5%.
class spell_sha_ele_fury_capstone : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_fury_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FURY_CAPSTONE, ShamanData::SPELL_ELEMENTAL_FURY_60185 });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (player && player->HasAura(ShamanData::SPELL_ELEMENTAL_FURY_60185))
            player->CastSpell(player, ShamanData::SPELL_FURY_CAPSTONE, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(ShamanData::SPELL_FURY_CAPSTONE);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_ele_fury_capstone::HandleApply, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_ele_fury_capstone::HandleRemove, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
    }
};

// 57994 Wind Shear - Wind Rush rank 3: an interrupt that lands (the target was casting or channeling something
// Wind Shear can interrupt) grants 15% haste for 10 sec (refresh). Not Proc Chance.
class spell_sha_ele_wind_rush : public SpellScript
{
    PrepareSpellScript(spell_sha_ele_wind_rush);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_WIND_RUSH_HASTE, ShamanData::SPELL_WIND_RUSH_RANK3 });
    }

    // The condition of Spell::EffectInterruptCast (this handler runs before the default one)
    static bool WillInterrupt(Unit const* target)
    {
        for (uint32 i = CURRENT_FIRST_NON_MELEE_SPELL; i < CURRENT_AUTOREPEAT_SPELL; ++i)
        {
            Spell const* spell = target->GetCurrentSpell(CurrentSpellTypes(i));
            if (!spell)
                continue;

            SpellInfo const* info = spell->GetSpellInfo();
            bool const casting = spell->getState() == SPELL_STATE_CASTING ||
                (spell->getState() == SPELL_STATE_PREPARING && spell->GetCastTime() > 0);
            bool const interruptible = (i == CURRENT_GENERIC_SPELL &&
                (info->InterruptFlags & SPELL_INTERRUPT_FLAG_INTERRUPT)) ||
                (i == CURRENT_CHANNELED_SPELL && (info->ChannelInterruptFlags & CHANNEL_INTERRUPT_FLAG_INTERRUPT));
            if (casting && info->PreventionType == SPELL_PREVENTION_TYPE_SILENCE && interruptible)
                return true;
        }

        return false;
    }

    void HandleInterrupt(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!player || !target || !target->IsAlive() || !player->HasAura(ShamanData::SPELL_WIND_RUSH_RANK3))
            return;

        if (WillInterrupt(target))
            player->CastSpell(player, ShamanData::SPELL_WIND_RUSH_HASTE, true);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sha_ele_wind_rush::HandleInterrupt, EFFECT_0,
            SPELL_EFFECT_INTERRUPT_CAST);
    }
};

// 16544 Rising Flames rank 2 (repurposed Improved Fire Nova) - every RISING_FLAMES_TICK_MS (the rank's periodic
// dummy) a stack while the Magma Totem or the Fire Elemental holds the Fire slot; the buff caps itself (5) and lasts
// until a Fire Nova spends it (spell_sha_fire_nova_rework).
class spell_sha_ele_rising_flames : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_rising_flames);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_RISING_FLAMES_BUFF });
    }

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    static bool HasMagmaTotem(Player* player)
    {
        ObjectGuid const guid = player->m_SummonSlot[SUMMON_SLOT_TOTEM_FIRE];
        if (!guid)
            return false;

        Creature const* totem = ObjectAccessor::GetCreature(*player, guid);
        return totem && totem->IsAlive() && totem->GetEntry() == ShamanData::NPC_MAGMA_TOTEM;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* player = GetUnitOwner()->ToPlayer();
        if (!player || !player->IsAlive())
            return;

        if (HasElemental(player, Shaman::ELEMENTAL_MASK_FIRE) || HasMagmaTotem(player))
            player->CastSpell(player, ShamanData::SPELL_RISING_FLAMES_BUFF, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_ele_rising_flames::HandlePeriodic, EFFECT_FIRST_FOUND,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// Astral Shift (talent chain 51474/51478/51479; replaces spell_sha_astral_shift and spell_sha_astral_shift_aura) - a
// stun, fear or silence from a hostile source that lands on a shaman with the talent gives -10% damage taken for as
// long as it holds. Rank 3 capstone: if a cast-time Nature spell was being cast when it landed, the empowered shift
// (-25%, 6 sec) replaces the plain one. Runs from the unit aura-apply hook, not from a talent proc, so triggered
// spells (Charge / Intercept stuns, Mace Specialization, boss casts) and script-added auras count too (S1a review
// M1). The talent carries no proc. Cheapest checks first: the hook runs for every aura application in the world.
class ShamanAstralShiftUnitScript : public UnitScript
{
public:
    ShamanAstralShiftUnitScript() : UnitScript("ShamanAstralShiftUnitScript", true, { UNITHOOK_ON_AURA_APPLY }) { }

    static bool IsControlAura(Aura const* aura)
    {
        return aura->HasEffectType(SPELL_AURA_MOD_STUN) || aura->HasEffectType(SPELL_AURA_MOD_FEAR) ||
            aura->HasEffectType(SPELL_AURA_MOD_SILENCE);
    }

    void OnAuraApply(Unit* unit, Aura* aura) override
    {
        if (!unit || !aura || !unit->IsPlayer() || !IsControlAura(aura))
            return;

        Player* player = unit->ToPlayer();
        uint8 const rank = Shaman::GetTalentRank(player, ASTRAL_SHIFT_RANKS);
        if (!rank)
            return;

        // A hostile source only; an aura with no caster (the caster despawned) still counts
        Unit* caster = aura->GetCaster();
        if (caster && !caster->IsHostileTo(player))
            return;

        // The control is in effect by now (the hook runs after the aura's effects were applied)
        if (!player->IsAlive() || !IsAstralShiftControlled(player))
            return;

        ElementalState* state = GetState(player);
        bool const wasCasting = state->natureCastUntilMs && NowMs() <= state->natureCastUntilMs;
        state->natureCastUntilMs = 0;

        if (wasCasting && rank >= ASTRAL_SHIFT_RANKS.size())
        {
            player->RemoveAurasDueToSpell(ShamanData::SPELL_ASTRAL_SHIFT_BUFF);
            ApplyAstralShift(player, ShamanData::SPELL_ASTRAL_SHIFT_EMPOWERED,
                ShamanData::ASTRAL_SHIFT_EMPOWERED_PCT);
            if (Aura* empowered = player->GetAura(ShamanData::SPELL_ASTRAL_SHIFT_EMPOWERED))
            {
                empowered->SetMaxDuration(ShamanData::ASTRAL_SHIFT_EMPOWERED_MS);
                empowered->SetDuration(ShamanData::ASTRAL_SHIFT_EMPOWERED_MS);
            }
        }
        else if (!player->HasAura(ShamanData::SPELL_ASTRAL_SHIFT_EMPOWERED))
            ApplyAstralShift(player, ShamanData::SPELL_ASTRAL_SHIFT_BUFF, ShamanData::ASTRAL_SHIFT_PLAIN_PCT);

        WatchAstralShift(player);
    }
};

// 202560-202563 Elemental Empowerment (Earth, Fire, Water, Storm) - the buff's periodic dummy keeps the amount live
// (Conduit of the Elements capstone: 10% + Mastery) through Shaman::RefreshEmpowerment, which changes an effect only
// when the value moved.
class spell_sha_ele_empowerment : public AuraScript
{
    PrepareAuraScript(spell_sha_ele_empowerment);

    bool Load() override
    {
        return GetOwner() && GetOwner()->IsPlayer();
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetUnitOwner()->ToPlayer())
            Shaman::RefreshEmpowerment(player);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sha_ele_empowerment::HandlePeriodic, EFFECT_FIRST_FOUND,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

void AddSC_shaman_elemental_spell_scripts()
{
    RegisterSpellScript(spell_sha_ele_lightning_overload);
    RegisterSpellScript(spell_sha_ele_overload_copy);
    RegisterSpellScript(spell_sha_ele_spell_hooks);
    RegisterSpellScript(spell_sha_ele_elemental_focus);
    RegisterSpellScript(spell_sha_ele_devastation);
    RegisterSpellScript(spell_sha_ele_lightning_mastery);
    RegisterSpellScript(spell_sha_ele_precision_capstone);
    RegisterSpellScript(spell_sha_ele_reach_capstone);
    RegisterSpellScript(spell_sha_ele_lava_surge);
    RegisterSpellScript(spell_sha_ele_fury_capstone);
    RegisterSpellScript(spell_sha_ele_wind_rush);
    RegisterSpellScript(spell_sha_ele_rising_flames);
    RegisterSpellScript(spell_sha_ele_empowerment);
    new ShamanAstralShiftUnitScript();
}
