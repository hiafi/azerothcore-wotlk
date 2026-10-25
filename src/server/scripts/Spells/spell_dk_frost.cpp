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
 * Death Knight Frost spec scripts (death-knight-rework S2a). Spell ids come from DeathKnightData:: (generated,
 * DSL-declared). Script table and rules: .agents/plans/death-knight-rework/death-knight-rework.S2a-WP-BRIEF.md.
 *
 * Rules every script here follows:
 *   - a non-player caster returns at once (Dancing Rune Weapon 27893 copies Heart Strike / Plague Strike / Obliterate /
 *     Frost Strike; Frost Fever 55095 is also a spawn aura on two creatures);
 *   - the school of a cast changes only through DeathKnight::SetCastSchool, only in OnCast;
 *   - hit damage changes only in OnHit with SetHitDamage (OnEffectHitTarget runs before the weapon damage exists);
 *   - per-cast state lives on the Death Knight's CustomData, nothing is file-static.
 */

#include "Containers.h"
#include "DataMap.h"
#include "DeathKnightMechanics.h"
#include "EngagementMechanics.h"
#include "Map.h"
#include "ModelIgnoreFlags.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <list>
#include <unordered_set>
#include <vector>

namespace
{
    constexpr char const* FROST_CAST_STATE_KEY = "deathknight_frost_cast_state";
    constexpr char const* FINAL_ROAR_KEY = "deathknight_frost_final_roar";
    constexpr char const* GLACIAL_HITS_KEY = "deathknight_frost_glacial_hits";

    // Heart Strike / Plague Strike under Gravefrost's capstone deal Shadowfrost (both schools)
    constexpr SpellSchoolMask SCHOOL_MASK_SHADOWFROST =
        SpellSchoolMask(SPELL_SCHOOL_MASK_FROST | SPELL_SCHOOL_MASK_SHADOW);

    // Threat of Thassarian: the SpellClassSet 15 bit of each strike it copies (the stock mapping, minus Blood Strike
    // and Rune Strike)
    constexpr uint32 TOT_PLAGUE_STRIKE_D0 = 0x00000001;
    constexpr uint32 TOT_DEATH_STRIKE_D0 = 0x00000010;
    constexpr uint32 TOT_HEART_STRIKE_D0 = 0x01000000;
    constexpr uint32 TOT_FROST_STRIKE_D1 = 0x00000004;
    constexpr uint32 TOT_OBLITERATE_D1 = 0x00020000;

    // Login: seconds the Deathchill grant waits for the player to finish loading
    constexpr int32 DEATHCHILL_LOAD_RETRIES = 30;

    // Auto attacks of a non-two-hander roll the two-hander value halved
    constexpr int32 ONE_HANDER_CHANCE_PCT = 50;

    // Glacial Advance geometry (U26): each spike is placed from the one before it
    constexpr float GLACIAL_PROBE_UP_YARDS = 4.0f;          // height probe starts this far above the previous spike
    constexpr float GLACIAL_PROBE_DISTANCE_YARDS = 10.0f;   // and searches down this far
    constexpr float GLACIAL_MAX_STEP_Z_YARDS = 3.5f;        // a bigger step than this ends the line
    constexpr float GLACIAL_LOS_HEIGHT_YARDS = 1.5f;        // line of sight is checked at this height above the ground
    constexpr float GLACIAL_CAST_LIFT_YARDS = 0.1f;         // eruptions are cast this far above the ground point

    // Per-cast scratch on the Death Knight. Set in OnCast, read by the hits (and by the off-hand copy cast during the
    // main hit), cleared in AfterCast; a cast always reaches AfterCast once OnCast ran.
    struct FrostCastState : DataMap::Base
    {
        bool killingMachine = false;    // main-hand Obliterate: a Killing Machine one (school switched to Frost)
        bool gravefrost = false;        // Heart / Plague Strike: switched to Shadowfrost
        bool deathchill = false;        // the cast armed Deathchill (never a Killing Machine Obliterate)
        bool rime = false;              // Howling Blast paid by Rime
        bool avalanche = false;         // ... with the Avalanche capstone known

        void Reset()
        {
            killingMachine = false;
            gravefrost = false;
            deathchill = false;
            rime = false;
            avalanche = false;
        }
    };

    // Breath's stored damage, handed from the aura's removal to the Final Roar burst cast right after it
    struct FinalRoarState : DataMap::Base
    {
        uint32 stored = 0;
        uint32 targets = 0;
    };

    // Glacial Advance: the enemies a cast's eruptions already hit (one hit per enemy per cast)
    struct GlacialAdvanceHits : DataMap::Base
    {
        std::unordered_set<ObjectGuid> hit;
    };

    Player* GetPlayerCaster(Unit* caster)
    {
        return caster ? caster->ToPlayer() : nullptr;
    }

    FrostCastState* GetCastState(Player* dk)
    {
        return dk->CustomData.GetDefault<FrostCastState>(FROST_CAST_STATE_KEY);
    }

    FrostCastState* FindCastState(Player* dk)
    {
        return dk->CustomData.Get<FrostCastState>(FROST_CAST_STATE_KEY);
    }

    int32 ScaleDamage(int32 damage, float multiplier)
    {
        return int32(std::max(0.0f, float(damage) * multiplier));
    }

    // The Frost multiplier of U14 applied to a hit's damage (before crit and armor, so the terms multiply)
    int32 ApplyFrostMultiplier(int32 damage, Player const* dk, SpellInfo const* spellInfo, Unit const* target,
        uint32 flags)
    {
        return ScaleDamage(damage, DeathKnight::GetFrostDamageMultiplier(dk, spellInfo, target, flags));
    }

    // A rank passive carries its value as the amount of its first effect; the highest rank known wins
    int32 GetRankAmount(Unit const* unit, std::initializer_list<uint32> ranksHighestFirst)
    {
        for (uint32 const rank : ranksHighestFirst)
            if (AuraEffect const* effect = unit->GetAuraEffect(rank, EFFECT_0))
                return effect->GetAmount();

        return 0;
    }

    // Deathchill (U9): armed in OnCast of Icy Touch / Howling Blast / Frost Strike / a plain Obliterate, consumed in
    // AfterCast. The marker rides the cast (crit through its SpellMod); the +20% is applied by the hit scripts.
    void ArmDeathchillForCast(Player* dk, Spell* spell, FrostCastState* state)
    {
        state->deathchill = false;
        if (!DeathKnight::DeathchillReady(dk))
            return;

        DeathKnight::ArmDeathchill(dk, spell);
        // the helper refuses a Killing Machine Obliterate: only a cast that really carries the marker spends the charge
        state->deathchill = dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_MARKER, dk->GetGUID());
    }

    void ConsumeDeathchillForCast(Player* dk, FrostCastState* state)
    {
        if (!state->deathchill)
            return;

        state->deathchill = false;
        DeathKnight::ConsumeDeathchill(dk);
    }

    // Killing Machine and Runic Attenuation: the data holds the two-hander chance; any other grip rolls half of it.
    // Only the owner's own auto attacks count (no ability, no Threat of Thassarian strike, no minion).
    bool CheckTwoHandAutoAttack(Unit* owner, ProcEventInfo& eventInfo)
    {
        Player* player = GetPlayerCaster(owner);
        if (!player || eventInfo.GetActor() != player || eventInfo.GetSpellInfo())
            return false;

        return player->IsTwoHandUsed() || roll_chance_i(ONE_HANDER_CHANCE_PCT);
    }

    bool KnowsDeathchill(Unit const* unit)
    {
        return unit->HasAura(DeathKnightData::SPELL_DEATHCHILL_203308) ||
            unit->HasAura(DeathKnightData::SPELL_DEATHCHILL_203309) ||
            unit->HasAura(DeathKnightData::SPELL_DEATHCHILL_203310);
    }

    // Deathchill's ready charge: granted unless the lockout is running or the charge is already up
    void GrantDeathchillCharge(Player* dk)
    {
        if (!dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_LOCKOUT) &&
            !dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_BUFF))
            dk->CastSpell(dk, DeathKnightData::SPELL_DEATHCHILL_BUFF, TRIGGERED_FULL_MASK);
    }

    bool IsLoadingIn(Player const* dk)
    {
        return !dk->IsInWorld() || (dk->GetSession() && dk->GetSession()->PlayerLoading());
    }

    // At login the talent passives apply before the saved auras load, so the lockout is not there yet: the grant waits
    // (a second at a time, re-resolving the player each time) until the player is in the world, then re-checks.
    void GrantDeathchillWhenLoaded(ObjectGuid guid, uint32 mapId, uint32 instanceId, int32 attempts)
    {
        Player* dk = ObjectAccessor::FindPlayer(guid);
        if (!dk || dk->GetMapId() != mapId || dk->GetInstanceId() != instanceId)
            return;

        if (IsLoadingIn(dk))
        {
            if (attempts > 0)
                dk->m_Events.AddEventAtOffset([guid, mapId, instanceId, attempts]()
                {
                    GrantDeathchillWhenLoaded(guid, mapId, instanceId, attempts - 1);
                }, 1s);

            return;
        }

        if (KnowsDeathchill(dk))
            GrantDeathchillCharge(dk);
    }

    // Engagement filter shared by Hungering Cold's tick and Glacial Advance's eruptions: only enemies already in combat
    // with the Death Knight or the group, so neither ever pulls an idle pack.
    void KeepEngagedEnemies(Player* dk, std::list<WorldObject*>& targets)
    {
        targets.remove_if([dk](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !unit->IsAlive() || !Engagement::IsEngagedWithOwnerOrGroup(unit, dk);
        });
    }
}

// 203054 - Obliterate. A Killing Machine stack turns the cast into Frost damage (school switched in OnCast, so the
// guaranteed crit, the armor skip and the Frost bonuses all follow); otherwise a ready Deathchill is armed for it.
// The Frost multipliers (Merciless, Tundra, the Obliteration capstone, Razorice, Deathchill) are applied in OnHit.
// AfterCast spends the stack (Enduring Strength extends Pillar inside ConsumeKillingMachine) and the Deathchill charge.
class spell_dk_obliterate_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_obliterate_rework);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        if (DeathKnight::HasKillingMachine(dk))
        {
            state->killingMachine = true;
            DeathKnight::SetCastSchool(GetSpell(), SPELL_SCHOOL_MASK_FROST);
        }
        else
            ArmDeathchillForCast(dk, GetSpell(), state);

        DeathKnight::SnapshotRuneCooldowns(dk);
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state || !target)
            return;

        uint32 flags = 0;
        if (state->killingMachine)
            flags |= DeathKnight::FROST_MULT_KM_OBLITERATE;
        if (DeathKnight::IsSchoolSwitchedCast(GetSpell()))
            flags |= DeathKnight::FROST_MULT_SCHOOL_SWITCHED;
        if (state->deathchill)
            flags |= DeathKnight::FROST_MULT_DEATHCHILL;

        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target, flags));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state)
            return;

        if (state->killingMachine)
            DeathKnight::ConsumeKillingMachine(dk);

        ConsumeDeathchillForCast(dk, state);
        state->Reset();
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_obliterate_rework::HandleCast);
        OnHit += SpellHitFn(spell_dk_obliterate_rework::HandleHit);
        AfterCast += SpellCastFn(spell_dk_obliterate_rework::HandleAfterCast);
    }
};

// 49143 - Frost Strike. Deathchill is armed and spent here; the Glacier Rot, Mastery and Merciless terms are applied
// in OnHit.
class spell_dk_frost_strike_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_frost_strike_rework);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        ArmDeathchillForCast(dk, GetSpell(), state);
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state || !target)
            return;

        uint32 const flags = state->deathchill ? uint32(DeathKnight::FROST_MULT_DEATHCHILL) : 0u;
        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target, flags));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state)
            return;

        ConsumeDeathchillForCast(dk, state);
        state->Reset();
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_frost_strike_rework::HandleCast);
        OnHit += SpellHitFn(spell_dk_frost_strike_rework::HandleHit);
        AfterCast += SpellCastFn(spell_dk_frost_strike_rework::HandleAfterCast);
    }
};

// 49184 - Howling Blast. OnCast notes whether Rime pays for it (the buff and its cost mod are gone by AfterCast) and
// whether the Avalanche capstone is known, and arms Deathchill. OnHit applies the Frost multiplier (Glacier Rot's base
// term) and Deathchill. AfterCast: Avalanche icicles on up to RIME_AVALANCHE_TARGETS enemies the blast hit (Rime +
// capstone), Rage of the Frozen Champion's Runic Power (Rime), Hungering Cold's storm, the Deathchill charge.
class spell_dk_howling_blast_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_howling_blast_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_FREEZING_FOG, DeathKnightData::SPELL_AVALANCHE,
            DeathKnightData::SPELL_RAGE_OF_THE_FROZEN_CHAMPION_ENERGIZE });
    }

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        state->rime = dk->HasAura(DeathKnightData::SPELL_FREEZING_FOG);
        state->avalanche = state->rime && dk->HasAura(DeathKnightData::SPELL_RIME_59057);
        ArmDeathchillForCast(dk, GetSpell(), state);
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state || !target)
            return;

        uint32 const flags = state->deathchill ? uint32(DeathKnight::FROST_MULT_DEATHCHILL) : 0u;
        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target, flags));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state)
            return;

        if (dk->IsAlive())
        {
            if (state->avalanche)
                CastAvalanche(dk);

            if (state->rime)
            {
                int32 const runicPower = GetRankAmount(dk, { DeathKnightData::SPELL_RAGE_OF_THE_FROZEN_CHAMPION_203295,
                    DeathKnightData::SPELL_RAGE_OF_THE_FROZEN_CHAMPION });
                // the rank value is whole Runic Power; power is stored x10
                if (runicPower > 0)
                    dk->CastCustomSpell(DeathKnightData::SPELL_RAGE_OF_THE_FROZEN_CHAMPION_ENERGIZE,
                        SPELLVALUE_BASE_POINT0, runicPower * 10, dk, TRIGGERED_FULL_MASK);
            }

            if (dk->HasAura(DeathKnightData::SPELL_HUNGERING_COLD_PASSIVE))
                DeathKnight::StartOrExtendHungeringCold(dk);
        }

        ConsumeDeathchillForCast(dk, state);
        state->Reset();
    }

    // At most one icicle per enemy the blast hit, at most RIME_AVALANCHE_TARGETS of them, chosen at random
    void CastAvalanche(Player* dk)
    {
        std::vector<ObjectGuid> hits;
        for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
            if (info.missCondition == SPELL_MISS_NONE)
                hits.push_back(info.targetGUID);

        Acore::Containers::RandomResize(hits, std::size_t(DeathKnightData::RIME_AVALANCHE_TARGETS));
        for (ObjectGuid const& guid : hits)
            if (Unit* enemy = ObjectAccessor::GetUnit(*dk, guid))
                if (enemy->IsAlive())
                    dk->CastSpell(enemy, DeathKnightData::SPELL_AVALANCHE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_howling_blast_rework::HandleCast);
        OnHit += SpellHitFn(spell_dk_howling_blast_rework::HandleHit);
        AfterCast += SpellCastFn(spell_dk_howling_blast_rework::HandleAfterCast);
    }
};

// 45477 - Icy Touch. Deathchill only: armed on the cast, +DEATHCHILL_DAMAGE_PCT% on the direct hit (Frost Fever is a
// separate spell and gets nothing), spent after the cast. Improved Icy Touch keeps its stock dummy.
class spell_dk_icy_touch_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_icy_touch_rework);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        ArmDeathchillForCast(dk, GetSpell(), state);
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state || !state->deathchill)
            return;

        SetHitDamage(ScaleDamage(GetHitDamage(), 1.0f + float(DeathKnightData::DEATHCHILL_DAMAGE_PCT) / 100.0f));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState* state = dk ? FindCastState(dk) : nullptr;
        if (!state)
            return;

        ConsumeDeathchillForCast(dk, state);
        state->Reset();
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_icy_touch_rework::HandleCast);
        OnHit += SpellHitFn(spell_dk_icy_touch_rework::HandleHit);
        AfterCast += SpellCastFn(spell_dk_icy_touch_rework::HandleAfterCast);
    }
};

// 55050 - Heart Strike. Gravefrost's capstone (rank 3) makes the cast Shadowfrost (both schools, armor skipped); the
// off-hand copy cast during the hit reads the same flag. A switched strike loses the physical total-percent modifiers,
// so Razorice's Frost vulnerability (aura 271 cannot tell) comes from the multiplier helper.
class spell_dk_heart_strike_frost : public SpellScript
{
    PrepareSpellScript(spell_dk_heart_strike_frost);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        if (dk->HasAura(DeathKnightData::SPELL_GRAVEFROST_203277))
        {
            state->gravefrost = true;
            DeathKnight::SetCastSchool(GetSpell(), SCHOOL_MASK_SHADOWFROST);
        }
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target || !DeathKnight::IsSchoolSwitchedCast(GetSpell()))
            return;

        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target,
            DeathKnight::FROST_MULT_SCHOOL_SWITCHED));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (FrostCastState* state = dk ? FindCastState(dk) : nullptr)
            state->Reset();
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_heart_strike_frost::HandleCast);
        OnHit += SpellHitFn(spell_dk_heart_strike_frost::HandleHit);
        AfterCast += SpellCastFn(spell_dk_heart_strike_frost::HandleAfterCast);
    }
};

// 45462 - Plague Strike. The Heart Strike rules (Gravefrost's capstone: Shadowfrost, Razorice term when switched).
class spell_dk_plague_strike_frost : public SpellScript
{
    PrepareSpellScript(spell_dk_plague_strike_frost);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        FrostCastState* state = GetCastState(dk);
        state->Reset();
        if (dk->HasAura(DeathKnightData::SPELL_GRAVEFROST_203277))
        {
            state->gravefrost = true;
            DeathKnight::SetCastSchool(GetSpell(), SCHOOL_MASK_SHADOWFROST);
        }
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target || !DeathKnight::IsSchoolSwitchedCast(GetSpell()))
            return;

        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target,
            DeathKnight::FROST_MULT_SCHOOL_SWITCHED));
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (FrostCastState* state = dk ? FindCastState(dk) : nullptr)
            state->Reset();
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_plague_strike_frost::HandleCast);
        OnHit += SpellHitFn(spell_dk_plague_strike_frost::HandleHit);
        AfterCast += SpellCastFn(spell_dk_plague_strike_frost::HandleAfterCast);
    }
};

// 66198 Obliterate, 66196 Frost Strike, 203322 Heart Strike, 66216 Plague Strike - the Threat of Thassarian off-hand
// copies (cast triggered during the main-hand hit, so they read the main hand's flags). A copy inherits the main
// hand's school switch (Killing Machine Obliterate: Frost; Gravefrost Heart / Plague Strike: Shadowfrost). A
// non-physical off-hand strike gets neither the engine's flat doubling nor its total-percent (0.5 and Nerves of Cold
// Steel), so OnHit rebuilds the physical result: (damage + the flat the physical copy stores halved) x 0.5 x
// (1 + Nerves%), the factor from FROST_MULT_OFFHAND (DeathKnightMechanics.h, "S2 helpers"). Frost Strike's copy is
// Frost in the data and stores its full flat.
class spell_dk_frost_offhand : public SpellScript
{
    PrepareSpellScript(spell_dk_frost_offhand);

    void HandleCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FrostCastState const* state = dk ? FindCastState(dk) : nullptr;
        if (!state)
            return;

        switch (GetSpellInfo()->Id)
        {
            case DeathKnightData::SPELL_OBLITERATE_66198:
                if (state->killingMachine)
                    DeathKnight::SetCastSchool(GetSpell(), SPELL_SCHOOL_MASK_FROST);
                break;
            case DeathKnightData::SPELL_HEART_STRIKE_OFFHAND:
            case DeathKnightData::SPELL_PLAGUE_STRIKE_66216:
                if (state->gravefrost)
                    DeathKnight::SetCastSchool(GetSpell(), SCHOOL_MASK_SHADOWFROST);
                break;
            default:
                break;
        }
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        FrostCastState const* state = FindCastState(dk);
        Spell* spell = GetSpell();
        SpellInfo const* spellInfo = GetSpellInfo();
        uint32 flags = 0;
        int32 damage = GetHitDamage();

        // A non-physical copy skips the engine's flat doubling and total-percent: rebuild the physical result
        // (GetOffhandFlatAddBack is 0 for 66196, which stores its full flat)
        if (!(spell->GetSpellSchoolMask() & SPELL_SCHOOL_MASK_NORMAL))
        {
            flags |= DeathKnight::FROST_MULT_OFFHAND;
            damage += DeathKnight::GetOffhandFlatAddBack(dk, spellInfo, target);
        }

        if (DeathKnight::IsSchoolSwitchedCast(spell))
            flags |= DeathKnight::FROST_MULT_SCHOOL_SWITCHED;
        if (state && state->deathchill)
            flags |= DeathKnight::FROST_MULT_DEATHCHILL;
        if (state && state->killingMachine && spellInfo->Id == DeathKnightData::SPELL_OBLITERATE_66198)
            flags |= DeathKnight::FROST_MULT_KM_OBLITERATE;

        SetHitDamage(ApplyFrostMultiplier(damage, dk, spellInfo, target, flags));
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dk_frost_offhand::HandleCast);
        OnHit += SpellHitFn(spell_dk_frost_offhand::HandleHit);
    }
};

// -65661 - Threat of Thassarian (replaces the stock spell_dk_threat_of_thassarian: its roll_chance_i ignores Proc
// Chance and it maps Blood Strike / Rune Strike). The owner's own strike, dual-wielding, once per cast (Heart Strike
// cleaves), rolls amount% x (1 + Proc Chance%) and casts the mapped off-hand copy triggered (it pays nothing and
// procs nothing).
class spell_dk_threat_of_thassarian_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_threat_of_thassarian_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_OBLITERATE_66198, DeathKnightData::SPELL_FROST_STRIKE_66196,
            DeathKnightData::SPELL_HEART_STRIKE_OFFHAND, DeathKnightData::SPELL_PLAGUE_STRIKE_66216,
            DeathKnightData::SPELL_DEATH_STRIKE_66188 });
    }

    static uint32 GetOffhandCopy(SpellInfo const* spellInfo)
    {
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_DEATHKNIGHT)
            return 0;

        if (spellInfo->SpellFamilyFlags[0] & TOT_HEART_STRIKE_D0)
            return DeathKnightData::SPELL_HEART_STRIKE_OFFHAND;
        if (spellInfo->SpellFamilyFlags[0] & TOT_PLAGUE_STRIKE_D0)
            return DeathKnightData::SPELL_PLAGUE_STRIKE_66216;
        if (spellInfo->SpellFamilyFlags[0] & TOT_DEATH_STRIKE_D0)
            return DeathKnightData::SPELL_DEATH_STRIKE_66188;
        if (spellInfo->SpellFamilyFlags[1] & TOT_FROST_STRIKE_D1)
            return DeathKnightData::SPELL_FROST_STRIKE_66196;
        if (spellInfo->SpellFamilyFlags[1] & TOT_OBLITERATE_D1)
            return DeathKnightData::SPELL_OBLITERATE_66198;

        return 0;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetTarget();
        Spell const* spell = eventInfo.GetProcSpell();
        if (!owner || !owner->IsPlayer() || !spell || spell->IsTriggered() || !owner->haveOffhandWeapon() ||
            (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC))
            return false;

        if (!GetOffhandCopy(eventInfo.GetSpellInfo()))
            return false;

        return _guard.OwnerFirst(owner, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* owner = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        uint32 const copy = GetOffhandCopy(eventInfo.GetSpellInfo());
        Player* player = GetPlayerCaster(owner);
        if (!player || !target || !copy)
            return;

        float const chance = float(aurEff->GetAmount()) * (1.0f + player->GetProcChancePercentage() / 100.0f);
        if (!roll_chance_f(chance))
            return;

        owner->CastSpell(target, copy, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_threat_of_thassarian_rework::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dk_threat_of_thassarian_rework::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    DeathKnight::OncePerCastGuard _guard;
};

// -51123 - Killing Machine (talent ranks; replaces spell_gen_no_offhand_proc here so the off hand rolls too). The
// proc row carries the two-hander chance; a one-hander rolls half of it. The trigger itself is the rank's own effect.
class spell_dk_killing_machine_talent : public AuraScript
{
    PrepareAuraScript(spell_dk_killing_machine_talent);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return CheckTwoHandAutoAttack(GetTarget(), eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_killing_machine_talent::CheckProc);
    }
};

// -203270 - Runic Attenuation: the Killing Machine auto-attack rule (two-hander value halved for any other grip).
class spell_dk_runic_attenuation : public AuraScript
{
    PrepareAuraScript(spell_dk_runic_attenuation);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return CheckTwoHandAutoAttack(GetTarget(), eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_runic_attenuation::CheckProc);
    }
};

// -203278 - Koltira's Favor. A cast-phase proc on Obliterate (after the cast paid its rune, before the hits): the
// Frost Rune the cast just spent comes back ready. The cooldown snapshot is taken in the Obliterate script's OnCast.
class spell_dk_koltiras_favor : public AuraScript
{
    PrepareAuraScript(spell_dk_koltiras_favor);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetTarget();
        return owner && owner->IsPlayer() && eventInfo.GetActor() == owner;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk)
            return;

        int8 const slot = DeathKnight::FindJustSpentFrostRune(dk);
        if (slot >= 0)
            DeathKnight::ActivateRune(dk, uint8(slot));
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_koltiras_favor::CheckProc);
        OnProc += AuraProcFn(spell_dk_koltiras_favor::HandleProc);
    }
};

// 203292 - Obliteration. A cast-phase proc on Frost Strike / Howling Blast / Glacial Advance while Pillar of Frost is
// up: always +1 Killing Machine, then OBLITERATION_RUNE_PCT% (times Proc Chance) to activate a depleted Frost Rune.
class spell_dk_obliteration : public AuraScript
{
    PrepareAuraScript(spell_dk_obliteration);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_PILLAR_OF_FROST,
            DeathKnightData::SPELL_OBLITERATION_FROST_RUNE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetTarget();
        return owner && owner->IsPlayer() && eventInfo.GetActor() == owner &&
            owner->HasAura(DeathKnightData::SPELL_PILLAR_OF_FROST);
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk)
            return;

        DeathKnight::GrantKillingMachine(dk);

        float const chance = float(DeathKnightData::OBLITERATION_RUNE_PCT) *
            (1.0f + dk->GetProcChancePercentage() / 100.0f);
        if (roll_chance_f(chance))
            dk->CastSpell(dk, DeathKnightData::SPELL_OBLITERATION_FROST_RUNE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dk_obliteration::CheckProc);
        OnProc += AuraProcFn(spell_dk_obliteration::HandleProc);
    }
};

// 203280 - Pillar of Frost. While Pillar is up the Death Knight carries Toravon's Whiteout's buff, at the highest rank
// known; the buff is permanent and is removed with Pillar, so Enduring Strength's extensions carry over.
class spell_dk_pillar_of_frost : public AuraScript
{
    PrepareAuraScript(spell_dk_pillar_of_frost);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_TORAVONS_WHITEOUT_BUFF });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk)
            return;

        int32 const percent = GetRankAmount(dk, { DeathKnightData::SPELL_TORAVONS_WHITEOUT_203287,
            DeathKnightData::SPELL_TORAVONS_WHITEOUT_203286, DeathKnightData::SPELL_TORAVONS_WHITEOUT });
        if (percent > 0)
            dk->CastCustomSpell(DeathKnightData::SPELL_TORAVONS_WHITEOUT_BUFF, SPELLVALUE_BASE_POINT0, percent, dk,
                TRIGGERED_FULL_MASK);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* dk = GetPlayerCaster(GetTarget()))
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_TORAVONS_WHITEOUT_BUFF);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_pillar_of_frost::HandleApply, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_pillar_of_frost::HandleRemove, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// -203308 - Deathchill (rank passives). Learning (or logging in with) a rank grants the visible charge 203311 unless
// the lockout is running, so it is ready at the start of a fight; losing every rank takes the charge away.
class spell_dk_deathchill : public AuraScript
{
    PrepareAuraScript(spell_dk_deathchill);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DEATHCHILL_BUFF, DeathKnightData::SPELL_DEATHCHILL_LOCKOUT });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk)
            return;

        if (IsLoadingIn(dk))
        {
            GrantDeathchillWhenLoaded(dk->GetGUID(), dk->GetMapId(), dk->GetInstanceId(), DEATHCHILL_LOAD_RETRIES);
            return;
        }

        GrantDeathchillCharge(dk);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (dk && !KnowsDeathchill(dk))
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_DEATHCHILL_BUFF);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_deathchill::HandleApply, EFFECT_FIRST_FOUND, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_deathchill::HandleRemove, EFFECT_FIRST_FOUND, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 203313 - Deathchill lockout (hidden, 60 / 45 / 30 s by rank). Running out gives the charge back, if a rank is still
// known.
class spell_dk_deathchill_lockout : public AuraScript
{
    PrepareAuraScript(spell_dk_deathchill_lockout);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DEATHCHILL_BUFF });
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* application = GetTargetApplication();
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk || !application || application->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        if (KnowsDeathchill(dk) && !dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_BUFF))
            dk->CastSpell(dk, DeathKnightData::SPELL_DEATHCHILL_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_deathchill_lockout::HandleRemove, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203315 - Hungering Cold storm (the self aura, 10 s). Every 2 s it casts the tick; the cadence is fixed, so haste
// never adds ticks, and a new Howling Blast only lengthens the aura (never re-casts it: that would reset the timer).
class spell_dk_hungering_cold_storm : public AuraScript
{
    PrepareAuraScript(spell_dk_hungering_cold_storm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_HUNGERING_COLD_TICK });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (dk && dk->IsAlive())
            dk->CastSpell(dk, DeathKnightData::SPELL_HUNGERING_COLD_TICK, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_hungering_cold_storm::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 203316 - Hungering Cold tick (8 yd around the Death Knight, Frost). Only enemies already in combat with the Death
// Knight or the group are hit (never pulls). Each hit adds a slow stack; a second stack freezes (OnHungeringColdHit
// owns the stun-immunity check and the per-enemy lockout).
class spell_dk_hungering_cold_tick : public SpellScript
{
    PrepareSpellScript(spell_dk_hungering_cold_tick);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (Player* dk = GetPlayerCaster(GetCaster()))
            KeepEngagedEnemies(dk, targets);
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (dk && target && target->IsAlive())
            DeathKnight::OnHungeringColdHit(dk, target);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_hungering_cold_tick::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_SRC_AREA_ENEMY);
        OnHit += SpellHitFn(spell_dk_hungering_cold_tick::HandleHit);
    }
};

// 203273 - Glacial Advance. After the cast: the enemy hit set is cleared, then GLACIAL_ADVANCE_ERUPTIONS spikes are
// laid out along the Death Knight's facing, GLACIAL_ADVANCE_STEP_YARDS apart. Each spike's height is found from the
// one before it (the stock caster-height placement sinks spikes into hills); the line ends at a cliff, a wall, or
// ground it cannot find. The eruptions are cast GLACIAL_ADVANCE_STEP_MS apart on the caster's event queue; each one
// re-resolves the caster by guid and checks map and instance first (a dest never carries the map id).
class spell_dk_glacial_advance : public SpellScript
{
    PrepareSpellScript(spell_dk_glacial_advance);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_GLACIAL_ERUPTION });
    }

    void HandleAfterCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Map* map = dk ? dk->GetMap() : nullptr;
        if (!dk || !map)
            return;

        dk->CustomData.GetDefault<GlacialAdvanceHits>(GLACIAL_HITS_KEY)->hit.clear();

        ObjectGuid const guid = dk->GetGUID();
        uint32 const mapId = dk->GetMapId();
        uint32 const instanceId = dk->GetInstanceId();
        uint32 const phaseMask = dk->GetPhaseMask();
        float const startX = dk->GetPositionX();
        float const startY = dk->GetPositionY();
        float const facing = dk->GetOrientation();

        float previousX = startX;
        float previousY = startY;
        float previousZ = dk->GetPositionZ();
        for (int32 i = 0; i < DeathKnightData::GLACIAL_ADVANCE_ERUPTIONS; ++i)
        {
            float const distance = float(DeathKnightData::GLACIAL_ADVANCE_STEP_YARDS) * float(i + 1);
            float const x = startX + distance * std::cos(facing);
            float const y = startY + distance * std::sin(facing);

            float z = map->GetHeight(phaseMask, x, y, previousZ + GLACIAL_PROBE_UP_YARDS, true,
                GLACIAL_PROBE_DISTANCE_YARDS);
            if (z <= INVALID_HEIGHT)
                z = map->GetGridHeight(x, y);

            if (z <= INVALID_HEIGHT || std::fabs(z - previousZ) > GLACIAL_MAX_STEP_Z_YARDS)
                break;

            if (!map->isInLineOfSight(previousX, previousY, previousZ + GLACIAL_LOS_HEIGHT_YARDS, x, y,
                z + GLACIAL_LOS_HEIGHT_YARDS, phaseMask, LINEOFSIGHT_ALL_CHECKS, VMAP::ModelIgnoreFlags::Nothing))
                break;

            dk->m_Events.AddEventAtOffset([guid, mapId, instanceId, x, y, z]()
            {
                Player* caster = ObjectAccessor::FindPlayer(guid);
                if (!caster || !caster->IsAlive() || caster->GetMapId() != mapId ||
                    caster->GetInstanceId() != instanceId)
                    return;

                caster->CastSpell(x, y, z + GLACIAL_CAST_LIFT_YARDS, DeathKnightData::SPELL_GLACIAL_ERUPTION, true);
            }, Milliseconds(DeathKnightData::GLACIAL_ADVANCE_STEP_MS * i));

            previousX = x;
            previousY = y;
            previousZ = z;
        }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dk_glacial_advance::HandleAfterCast);
    }
};

// 203274 - Glacial Eruption (3 yd around a spike). Only engaged enemies, and each enemy once per Glacial Advance cast
// (the hit set is on the Death Knight). The damage takes the Frost multiplier (Glacier Rot and its Mastery capstone).
class spell_dk_glacial_eruption : public SpellScript
{
    PrepareSpellScript(spell_dk_glacial_eruption);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        KeepEngagedEnemies(dk, targets);

        std::unordered_set<ObjectGuid>& hit = dk->CustomData.GetDefault<GlacialAdvanceHits>(GLACIAL_HITS_KEY)->hit;
        targets.remove_if([&hit](WorldObject* object)
        {
            return hit.count(object->GetGUID()) > 0;
        });

        for (WorldObject* object : targets)
            hit.insert(object->GetGUID());
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        SetHitDamage(ApplyFrostMultiplier(GetHitDamage(), dk, GetSpellInfo(), target, 0));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_glacial_eruption::FilterTargets, EFFECT_ALL,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnHit += SpellHitFn(spell_dk_glacial_eruption::HandleHit);
    }
};

// 203306 - Breath of Sindragosa (cast). The engine's own checks do not cover the Runic Power (the drain is the aura's);
// the cast needs BREATH_MIN_RP and is refused while a Breath is still running (Breath can outlast its 2 min cooldown).
// The cooldown is the plain DBC one (Cooldown Haste applies through the generic path), cancelling is right-clicking the
// buff.
class spell_dk_breath_of_sindragosa : public SpellScript
{
    PrepareSpellScript(spell_dk_breath_of_sindragosa);

    SpellCastResult CheckCast()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return SPELL_CAST_OK;

        if (dk->HasAura(DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA))
            return SPELL_FAILED_AURA_BOUNCED;

        // Runic Power is stored x10
        if (dk->GetPower(POWER_RUNIC_POWER) < uint32(DeathKnightData::BREATH_MIN_RP) * 10)
            return SPELL_FAILED_NO_POWER;

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dk_breath_of_sindragosa::CheckCast);
    }
};

// 203306 - Breath of Sindragosa (the aura, PERIODIC_DUMMY 1 s, permanent). Each tick: pay the drain (10 Runic Power,
// +1 every BREATH_DRAIN_STEP_TICKS ticks) or end; every FROSTWYRM_RAMP_TICKS ticks one ramp stack (capstone); cast the
// tick; roll Rage of the Frozen Champion's Rime (capstone). The end: the ramp goes, and Final Roar (capstone) fires
// only when Breath expired (it could not pay: the script ends it with AURA_REMOVE_BY_EXPIRE) or was cancelled; death,
// logout and other removals (DEFAULT) get none. The stored damage is always cleared.
class spell_dk_breath_of_sindragosa_aura : public AuraScript
{
    PrepareAuraScript(spell_dk_breath_of_sindragosa_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA_TICK,
            DeathKnightData::SPELL_FROSTWYRMS_WRATH_RAMP, DeathKnightData::SPELL_FINAL_ROAR_BURST });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* dk = GetPlayerCaster(GetTarget()))
            DeathKnight::TakeFinalRoarDamage(dk);
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk || !dk->IsAlive())
            return;

        uint32 const tick = aurEff->GetTickNumber();
        uint32 const drain = DeathKnight::GetBreathDrain(tick);
        if (dk->GetPower(POWER_RUNIC_POWER) < drain)
        {
            Remove(AURA_REMOVE_BY_EXPIRE);
            return;
        }

        dk->ModifyPower(POWER_RUNIC_POWER, -int32(drain));

        if (tick % uint32(DeathKnightData::FROSTWYRM_RAMP_TICKS) == 0 &&
            dk->HasAura(DeathKnightData::SPELL_FROSTWYRMS_WRATH_203303))
            dk->CastSpell(dk, DeathKnightData::SPELL_FROSTWYRMS_WRATH_RAMP, TRIGGERED_FULL_MASK);

        dk->CastSpell(dk, DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA_TICK, TRIGGERED_FULL_MASK, nullptr, aurEff);

        if (dk->IsAlive() && dk->HasAura(DeathKnightData::SPELL_RAGE_OF_THE_FROZEN_CHAMPION_203295))
        {
            float const chance = float(DeathKnightData::RAGE_FROZEN_CHAMPION_RIME_PCT) *
                (1.0f + dk->GetProcChancePercentage() / 100.0f);
            if (roll_chance_f(chance))
                DeathKnight::GrantRime(dk);
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* dk = GetPlayerCaster(GetTarget());
        if (!dk)
            return;

        dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_FROSTWYRMS_WRATH_RAMP);

        uint32 const stored = DeathKnight::TakeFinalRoarDamage(dk);
        AuraApplication const* application = GetTargetApplication();
        if (!stored || !application || !dk->IsAlive() || !dk->HasAura(DeathKnightData::SPELL_FINAL_ROAR_203290))
            return;

        AuraRemoveMode const mode = application->GetRemoveMode();
        if (mode != AURA_REMOVE_BY_EXPIRE && mode != AURA_REMOVE_BY_CANCEL)
            return;

        FinalRoarState* roar = dk->CustomData.GetDefault<FinalRoarState>(FINAL_ROAR_KEY);
        roar->stored = stored;
        roar->targets = 0;
        dk->CastSpell(dk, DeathKnightData::SPELL_FINAL_ROAR_BURST, TRIGGERED_FULL_MASK);
        roar->stored = 0;
        roar->targets = 0;
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_breath_of_sindragosa_aura::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_breath_of_sindragosa_aura::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_breath_of_sindragosa_aura::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203307 - Breath of Sindragosa tick (the cone in front of the Death Knight, once a second). The primary target is
// the Death Knight's victim, else the selected unit; every other target takes BREATH_SECONDARY_PCT%, and when the
// primary is not in the cone all of them do. The Frost multiplier (Merciless, Tundra, Mastery capstone, ramp) follows
// each hit. Every hit's final damage is stored for Final Roar (capstone).
class spell_dk_breath_of_sindragosa_tick : public SpellScript
{
    PrepareSpellScript(spell_dk_breath_of_sindragosa_tick);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        _primary = ObjectGuid::Empty;

        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk)
            return;

        Unit* primary = dk->GetVictim();
        if (!primary)
            primary = ObjectAccessor::GetUnit(*dk, dk->GetTarget());

        if (!primary)
            return;

        for (WorldObject* object : targets)
            if (object == primary)
            {
                _primary = primary->GetGUID();
                return;
            }
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* target = GetHitUnit();
        if (!dk || !target)
            return;

        int32 damage = GetHitDamage();
        if (target->GetGUID() != _primary)
            damage = int32(int64(damage) * DeathKnightData::BREATH_SECONDARY_PCT / 100);

        // the ramp and Mastery terms reach every target (the helper keys them on the tick's spell id)
        uint32 const flags = target->GetGUID() == _primary ? uint32(DeathKnight::FROST_MULT_BREATH_PRIMARY) : 0u;
        SetHitDamage(ApplyFrostMultiplier(damage, dk, GetSpellInfo(), target, flags));
    }

    void HandleAfterHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        if (!dk || !dk->HasAura(DeathKnightData::SPELL_FINAL_ROAR_203290))
            return;

        // after armor, crit and absorb (Spell.cpp: m_damage = the dealt damage)
        int32 const dealt = GetHitDamage();
        if (dealt > 0)
            DeathKnight::AddFinalRoarDamage(dk, uint32(dealt));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_breath_of_sindragosa_tick::FilterTargets,
            EFFECT_ALL, TARGET_UNIT_CONE_ENEMY_104);
        OnHit += SpellHitFn(spell_dk_breath_of_sindragosa_tick::HandleHit);
        AfterHit += SpellHitFn(spell_dk_breath_of_sindragosa_tick::HandleAfterHit);
    }

    ObjectGuid _primary;
};

// 203291 - Final Roar (Breath's capstone burst, a cone). The total is FINAL_ROAR_SHARE_PCT% of the damage Breath
// stored, split evenly over the enemies the cone caught; it takes no bonuses of its own.
class spell_dk_final_roar : public SpellScript
{
    PrepareSpellScript(spell_dk_final_roar);

    void CountTargets(std::list<WorldObject*>& targets)
    {
        if (Player* dk = GetPlayerCaster(GetCaster()))
            dk->CustomData.GetDefault<FinalRoarState>(FINAL_ROAR_KEY)->targets = uint32(targets.size());
    }

    void HandleHit()
    {
        Player* dk = GetPlayerCaster(GetCaster());
        FinalRoarState const* roar = dk ? dk->CustomData.Get<FinalRoarState>(FINAL_ROAR_KEY) : nullptr;
        if (!roar)
            return;

        uint64 const share = uint64(roar->stored) * uint64(DeathKnightData::FINAL_ROAR_SHARE_PCT) / 100;
        SetHitDamage(int32(std::min<uint64>(share / std::max<uint32>(1, roar->targets), uint64(INT32_MAX))));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_final_roar::CountTargets, EFFECT_ALL,
            TARGET_UNIT_CONE_ENEMY_104);
        OnHit += SpellHitFn(spell_dk_final_roar::HandleHit);
    }
};

// 55095 - Frost Fever (a second script beside the Dancing Rune Weapon guard). Chilblains: while the disease ticks, the
// Death Knight's own Icy Clutch on the victim is refreshed, so the slow lasts as long as the disease. A creature
// caster (Frost Fever is also a spawn aura on two creatures) is left alone.
class spell_dk_frost_fever_chilblains : public AuraScript
{
    PrepareAuraScript(spell_dk_frost_fever_chilblains);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* dk = GetPlayerCaster(GetCaster());
        Unit* victim = GetTarget();
        if (!dk || !victim || !victim->IsAlive())
            return;

        for (uint32 const clutch : { DeathKnightData::SPELL_ICY_CLUTCH, DeathKnightData::SPELL_ICY_CLUTCH_50435,
            DeathKnightData::SPELL_ICY_CLUTCH_50436 })
            if (Aura* aura = victim->GetAura(clutch, dk->GetGUID()))
                aura->RefreshDuration();
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_frost_fever_chilblains::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

void AddSC_deathknight_frost_spell_scripts()
{
    RegisterSpellScript(spell_dk_obliterate_rework);
    RegisterSpellScript(spell_dk_frost_strike_rework);
    RegisterSpellScript(spell_dk_howling_blast_rework);
    RegisterSpellScript(spell_dk_icy_touch_rework);
    RegisterSpellScript(spell_dk_heart_strike_frost);
    RegisterSpellScript(spell_dk_plague_strike_frost);
    RegisterSpellScript(spell_dk_frost_offhand);
    RegisterSpellScript(spell_dk_threat_of_thassarian_rework);
    RegisterSpellScript(spell_dk_killing_machine_talent);
    RegisterSpellScript(spell_dk_runic_attenuation);
    RegisterSpellScript(spell_dk_koltiras_favor);
    RegisterSpellScript(spell_dk_obliteration);
    RegisterSpellScript(spell_dk_pillar_of_frost);
    RegisterSpellScript(spell_dk_deathchill);
    RegisterSpellScript(spell_dk_deathchill_lockout);
    RegisterSpellScript(spell_dk_hungering_cold_storm);
    RegisterSpellScript(spell_dk_hungering_cold_tick);
    RegisterSpellScript(spell_dk_glacial_advance);
    RegisterSpellScript(spell_dk_glacial_eruption);
    RegisterSpellAndAuraScriptPair(spell_dk_breath_of_sindragosa, spell_dk_breath_of_sindragosa_aura);
    RegisterSpellScript(spell_dk_breath_of_sindragosa_tick);
    RegisterSpellScript(spell_dk_final_roar);
    RegisterSpellScript(spell_dk_frost_fever_chilblains);
}
