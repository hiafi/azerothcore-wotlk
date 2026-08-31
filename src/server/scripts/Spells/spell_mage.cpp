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

#include "Cell.h"
#include "CellImpl.h"
#include "Containers.h"
#include "CreatureAI.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "MageMechanics.h"
#include "Pet.h"
#include "Player.h"
#include "PlayerScript.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
/*
 * Scripts for spells with SPELLFAMILY_MAGE and SPELLFAMILY_GENERIC spells used by mage players.
 * Ordered alphabetically using scriptname.
 * Scriptnames of files in this file should be prefixed with "spell_mage_".
 */

enum MageSpells
{
    SPELL_MAGE_ARCANE_MISSILES_R1                = 5143,
    SPELL_MAGE_BLAZING_SPEED                     = 31643,
    SPELL_MAGE_MAGIC_ABSORPTION_MANA             = 29442,
    SPELL_MAGE_BURNOUT_TRIGGER                   = 44450,
    SPELL_MAGE_IMPROVED_BLIZZARD_CHILLED         = 12486,
    SPELL_MAGE_COMBUSTION                        = 11129,
    SPELL_MAGE_COMBUSTION_PROC                   = 28682,
    SPELL_MAGE_COLD_SNAP                         = 11958,
    SPELL_MAGE_FOCUS_MAGIC_PROC                  = 54648,
    SPELL_MAGE_FROST_WARDING_R1                  = 11189,
    SPELL_MAGE_FROST_WARDING_TRIGGERED           = 57776,
    SPELL_MAGE_INCANTERS_ABSORBTION_R1           = 44394,
    SPELL_MAGE_INCANTERS_ABSORBTION_TRIGGERED    = 44413,
    SPELL_MAGE_IGNITE                            = 12654,
    SPELL_MAGE_MASTER_OF_ELEMENTS_ENERGIZE       = 29077,
    SPELL_MAGE_PERMAFROST_AURA                   = 68391,
    SPELL_MAGE_SQUIRREL_FORM                     = 32813,
    SPELL_MAGE_GIRAFFE_FORM                      = 32816,
    SPELL_MAGE_SERPENT_FORM                      = 32817,
    SPELL_MAGE_DRAGONHAWK_FORM                   = 32818,
    SPELL_MAGE_WORGEN_FORM                       = 32819,
    SPELL_MAGE_SHEEP_FORM                        = 32820,
    SPELL_MAGE_GLYPH_OF_ETERNAL_WATER            = 70937,
    SPELL_MAGE_SUMMON_WATER_ELEMENTAL_PERMANENT  = 70908,
    SPELL_MAGE_SUMMON_WATER_ELEMENTAL_TEMPORARY  = 70907,
    SPELL_MAGE_GLYPH_OF_BLAST_WAVE               = 62126,
    SPELL_MAGE_FINGERS_OF_FROST                  = 44543,
    SPELL_MAGE_FINGERS_OF_FROST_AURASTATE_AURA   = 44544,
    SPELL_MAGE_ARCANE_POTENCY_RANK_1             = 57529,
    SPELL_MAGE_ARCANE_POTENCY_RANK_2             = 57531,
    SPELL_MAGE_EMPOWERED_FIRE_PROC               = 67545,
    SPELL_MAGE_T10_2P_BONUS                      = 70752,
    SPELL_MAGE_T10_2P_BONUS_EFFECT               = 70753,
    SPELL_MAGE_T8_4P_BONUS                       = 64869,
    SPELL_MAGE_HOT_STREAK_PROC                   = 48108,
    SPELL_MAGE_CHILLED_R1                        = 12484,
    SPELL_MAGE_CHILLED_R2                        = 12485,
    SPELL_MAGE_CHILLED_R3                        = 12486,
    SPELL_MAGE_MANA_SURGE                        = 37445,
    SPELL_MAGE_FROST_NOVA                        = 122,
    SPELL_MAGE_LIVING_BOMB_R1                    = 44457,
    SPELL_MAGE_MISSILE_BARRAGE_PROC              = 44401,

    // Frost Mage rework (docs/frost-mage-redesign.md) - new spells, reserved block 200000-209999
    // (apps/dbc-tools/source/ids.yaml). See docs/frost-mage-implementation-plan.md.
    SPELL_MAGE_ICICLES                           = 200001,
    SPELL_MAGE_GLACIAL_SPIKE                     = 200002,
    SPELL_MAGE_SHATTERING_COLD                   = 200003,
    SPELL_MAGE_FLURRY                            = 200004,
    SPELL_MAGE_REFRESHMENT                       = 200006,
    SPELL_MAGE_FROZEN_ORB                        = 200007,
    SPELL_MAGE_FROZEN_ORB_PULSE                  = 200008,
    SPELL_MAGE_FROZEN_ORB_PERIODIC               = 200009,
    SPELL_MAGE_BITING_COLD_R3                    = 200012,
    SPELL_MAGE_BITING_COLD_BITE                  = 200013,
    SPELL_MAGE_GLACIAL_SPIKE_SHATTER             = 200014,
    // Glacial Spike's 3-stage acceleration ramp (docs/frost-mage-handoff.md's art-pass
    // discussion) - two cosmetic wind-up hops, then the real damage-dealing impact. See
    // spell_mage_glacial_spike/spell_mage_glacial_spike_impact below.
    SPELL_MAGE_GLACIAL_SPIKE_WINDUP_1            = 200025,
    SPELL_MAGE_GLACIAL_SPIKE_WINDUP_2            = 200026,
    SPELL_MAGE_GLACIAL_SPIKE_IMPACT              = 200027,
    // Cluster C (docs/frost-mage-talent-tree-content-handoff.md) - Permafrost, Frozen Core,
    // Improved Cone of Cold, Shattered Barrier, Empowering Frostbolt capstones/support spells.
    SPELL_MAGE_PERMAFROST_STACK                  = 200015,
    SPELL_MAGE_FROZEN_CORE_BUFF_R1                = 200016,
    SPELL_MAGE_FROZEN_CORE_BUFF_R2                = 200017,
    SPELL_MAGE_FROZEN_CORE_BUFF_R3                = 200018,
    SPELL_MAGE_FROZEN_CORE_PIERCE                 = 200019,
    SPELL_MAGE_IMPROVED_CONE_OF_COLD_BUFF         = 200020,
    SPELL_MAGE_SHATTERED_BARRIER_SLOW             = 200021,
    SPELL_MAGE_SHATTERED_BARRIER_HASTE            = 200022,
    SPELL_MAGE_EMPOWERING_FROSTBOLT_R1             = 200023,
    SPELL_MAGE_EMPOWERING_FROSTBOLT_R2             = 200024,
    // Not new spells - naming existing stock IDs this pass's scripts need by name.
    SPELL_MAGE_ICE_LANCE                          = 30455,
    SPELL_MAGE_ICE_BARRIER                        = 11426,
    SPELL_MAGE_FROZEN_CORE_R3                     = 31669,
    SPELL_MAGE_WATER_ELEMENTAL_FREEZE             = 33395,
    // Not a new spell - naming the existing "Fingers of Frost" charge buff (already scripted
    // below as spell_mage_fingers_of_frost) for use by the frozen-state helpers.
    SPELL_MAGE_FINGERS_OF_FROST_CHARGES          = 74396
};

enum FrostMageReworkCreatures
{
    NPC_MAGE_FROZEN_ORB = 300001
};

enum MageSpellIcons
{
    MAGE_ICON_MAGIC_ABSORPTION                   = 459,
    MAGE_ICON_CLEARCASTING                       = 212,
    MAGE_ICON_PRESENCE_OF_MIND                   = 139,
    MAGE_ICON_LIVING_BOMB                        = 3000
};

/*
 * Frost Mage rework (docs/frost-mage-redesign.md, docs/frost-mage-implementation-plan.md).
 * Phase 1, first slice: the shared frozen-state check, Icicles, Glacial Spike, and Flurry.
 * Frozen Orb, Deep Freeze's conversion, the talent-row auras, and the rest of Phase 1 are not
 * part of this slice - see the implementation plan's "Suggested starting order".
 */

namespace FrostMageRework
{
    // A real freeze/root/stun Frost effect (Frost Nova, Deep Freeze's stun, Water Elemental's
    // Freeze) sets AURA_STATE_FROZEN globally: SharedDefines.h's PER_CASTER_AURA_STATE_MASK does
    // *not* include AURA_STATE_FROZEN (only AURA_STATE_CONFLAGRATE / AURA_STATE_DEADLY_POISON
    // are per-caster), so it benefits any caster once present - correct here, since anyone can
    // Shatter a target someone else froze.
    bool HasRealFreeze(Unit const* target)
    {
        return target && target->HasAuraState(AURA_STATE_FROZEN);
    }

    // Shattering Cold is caster-scoped by design ("Only the caster who applied it benefits"), so
    // - unlike the real-freeze case above - it's checked by caster GUID rather than the global
    // aura-state flag.
    bool HasShatteringCold(Unit const* target, ObjectGuid casterGuid)
    {
        return target && target->HasAura(SPELL_MAGE_SHATTERING_COLD, casterGuid);
    }

    // Fingers of Frost ("Your spells and abilities treat the target as if it were Frozen") is a
    // personal charge buff: it's the *caster* who needs the charge, not the target.
    bool HasFingersOfFrostCharge(Unit const* caster)
    {
        return caster && caster->HasAura(SPELL_MAGE_FINGERS_OF_FROST_CHARGES);
    }

    // The unified "frozen" check from the redesign's Interaction Rules section: a real freeze, a
    // Fingers of Frost charge, or Shattering Cold - the *only* thing "frozen" ever means in this
    // rework. Every frozen-state check in the codebase goes through this definition, either via
    // this wrapper or by calling Mage::IsFrozenTarget directly (Ice Lance's triple damage and
    // Permafrost in MageMechanics.cpp, Shatter's crit bonus in Unit.cpp, Frozen Core's capstone
    // below) - none of them fall back to the engine's native AURA_STATE_FROZEN alone. Delegates to
    // Mage::IsFrozenTarget (MageMechanics.h, core) rather than reimplementing - that's the
    // canonical copy now; kept as a thin wrapper
    // here (rather than switching every caller in this file to Mage::IsFrozenTarget directly) so
    // this namespace's existing call sites don't need to change.
    bool IsFrozenFor(Unit const* target, Unit const* caster)
    {
        return Mage::IsFrozenTarget(caster, target);
    }

    // Consumes one Fingers of Frost charge from `caster`, but only if Fingers of Frost was the
    // *sole* reason the target counted as frozen - docs/frost-mage-redesign.md: Glacial Spike
    // "Consumes a Fingers of Frost charge if one is available and the target is not otherwise
    // frozen"; Fingers of Frost's own entry has the same "Shattering Cold guard".
    void ConsumeFingersOfFrostIfSoleSource(Unit* caster, Unit const* target)
    {
        if (!caster || HasRealFreeze(target) || HasShatteringCold(target, caster->GetGUID()))
            return;

        if (Aura* fof = caster->GetAura(SPELL_MAGE_FINGERS_OF_FROST_CHARGES))
            fof->DropCharge();
    }
}

namespace
{
    // Shared by the three Icicle-granting scripts below (Frostbolt/Frostfire Bolt casts,
    // every 4th Blizzard pulse) - docs/frost-mage-redesign.md sec 1 (Icicles): "Generation is
    // enabled only when the Glacial Spike talent is learned."
    void GrantIcicleIfGlacialSpikeKnown(Unit* caster)
    {
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (player && player->HasSpell(SPELL_MAGE_GLACIAL_SPIKE))
            player->CastSpell(player, SPELL_MAGE_ICICLES, true);
    }
}

// 116 - Frostbolt
class spell_mage_frostbolt_icicles : public SpellScript
{
    PrepareSpellScript(spell_mage_frostbolt_icicles);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_ICICLES, SPELL_MAGE_GLACIAL_SPIKE });
    }

    void GrantIcicle()
    {
        GrantIcicleIfGlacialSpikeKnown(GetCaster());
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_mage_frostbolt_icicles::GrantIcicle);
    }
};

// 44614 - Frostfire Bolt
class spell_mage_frostfire_bolt_icicles : public SpellScript
{
    PrepareSpellScript(spell_mage_frostfire_bolt_icicles);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_ICICLES, SPELL_MAGE_GLACIAL_SPIKE });
    }

    void GrantIcicle()
    {
        GrantIcicleIfGlacialSpikeKnown(GetCaster());
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_mage_frostfire_bolt_icicles::GrantIcicle);
    }
};

// 10 - Blizzard
class spell_mage_blizzard_icicles : public AuraScript
{
    PrepareAuraScript(spell_mage_blizzard_icicles);

    uint8 _pulseCount = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_ICICLES, SPELL_MAGE_GLACIAL_SPIKE });
    }

    void CountPulse(AuraEffect const* /*aurEff*/)
    {
        if (++_pulseCount < 4)
            return;

        _pulseCount = 0;
        GrantIcicleIfGlacialSpikeKnown(GetCaster());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_mage_blizzard_icicles::CountPulse, EFFECT_1, SPELL_AURA_PERIODIC_TRIGGER_SPELL);
    }
};

// 200002 - Glacial Spike
// Redesigned as a 3-stage "ramp-up" missile chain to fake mid-flight acceleration - Spell.dbc
// only exposes one constant Speed per spell and the engine has no acceleration field at all (see
// docs/frost-mage-handoff.md's art-pass discussion). This spell (200002, the real button/cast-bar
// spell) no longer deals damage or travels itself (effect1 is a no-op DUMMY, Speed removed - see
// its CSV row's notes) - it only gates the cast (CheckIcicles) and, on hit (instant, since it no
// longer travels), kicks off the chain via BeginRamp:
//   1. Two short, dest-targeted (TARGET_DEST_DEST) cosmetic hops toward the real target -
//      SPELL_MAGE_GLACIAL_SPIKE_WINDUP_1 (Speed 1, ~0.5yd, ~0.5s) then _WINDUP_2 (Speed 5, ~1.5yd,
//      ~0.3s), fired ~0ms and ~500ms after the cast completes. Each hop's destination is computed
//      fresh (caster may have turned/moved) via GetFirstCollisionPosition - these spells are
//      purely visual and don't themselves know the real target.
//   2. The real hit, SPELL_MAGE_GLACIAL_SPIKE_IMPACT (Speed 30), cast at the real target ~800ms
//      after the button-press completes - see spell_mage_glacial_spike_impact below for icicle/
//      Fingers-of-Frost consumption and the Arctic Winds shatter-cleave, both moved there since
//      that's the stage that now represents the spell actually landing.
//
// This deliberately does *not* use the engine's native SPELL_EFFECT_TRIGGER_MISSILE_SPELL DBC
// chaining: for a unit-targeted trigger effect, EffectTriggerMissileSpell (SpellEffects.cpp)
// always re-casts the triggered spell from the caster's *current* position to the *same real*
// unit target - i.e. every leg re-flies the entire real cast distance, not a fraction of it.
// There's no way to get a short, controlled hop distance while keeping a real enemy unit as the
// target through that mechanism, so the whole chain is driven by hand instead: the real target is
// carried across the ~800ms ramp by GUID + ObjectAccessor (re-resolved and alive-checked at each
// stage) rather than by DBC-level target propagation, since a raw Unit* pointer captured into a
// delayed event isn't safe to hold across that much real time (the target could die/despawn).
class spell_mage_glacial_spike : public SpellScript
{
    PrepareSpellScript(spell_mage_glacial_spike);

    static constexpr uint8 REQUIRED_ICICLES = 5;

    // Ramp timing/distances - see the class comment above for why the chain is hand-driven.
    static constexpr float WINDUP_1_DISTANCE = 0.5f;
    static constexpr float WINDUP_2_DISTANCE = 1.5f;
    static constexpr uint32 WINDUP_2_DELAY_MS = 500;
    static constexpr uint32 IMPACT_DELAY_MS = 800;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_ICICLES, SPELL_MAGE_GLACIAL_SPIKE_WINDUP_1, SPELL_MAGE_GLACIAL_SPIKE_WINDUP_2, SPELL_MAGE_GLACIAL_SPIKE_IMPACT });
    }

    SpellCastResult CheckIcicles()
    {
        Aura* icicles = GetCaster()->GetAura(SPELL_MAGE_ICICLES);
        if (!icicles || icicles->GetStackAmount() < REQUIRED_ICICLES)
            return SPELL_FAILED_NO_COMBO_POINTS;

        return SPELL_CAST_OK;
    }

    // Short, collision-safe hop toward (not all the way to) the real target, from the caster's
    // *current* position at fire time. angle is relative to the caster's own facing (matching
    // GetFirstCollisionPosition's convention), so this points at the target regardless of which
    // way the caster happens to be facing.
    static void FireCosmeticHop(Unit* caster, Unit* target, float distance, uint32 spellId)
    {
        float const relativeAngle = caster->GetAngle(target) - caster->GetOrientation();
        Position const hop = caster->GetFirstCollisionPosition(distance, relativeAngle);
        caster->CastSpell(hop.GetPositionX(), hop.GetPositionY(), hop.GetPositionZ(), spellId, true);
    }

    void BeginRamp()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        ObjectGuid const targetGuid = target->GetGUID();
        FireCosmeticHop(caster, target, WINDUP_1_DISTANCE, SPELL_MAGE_GLACIAL_SPIKE_WINDUP_1);

        caster->m_Events.AddEventAtOffset([caster, targetGuid]()
        {
            Unit* target = ObjectAccessor::GetUnit(*caster, targetGuid);
            if (target && target->IsAlive())
                FireCosmeticHop(caster, target, WINDUP_2_DISTANCE, SPELL_MAGE_GLACIAL_SPIKE_WINDUP_2);
        }, Milliseconds(WINDUP_2_DELAY_MS));

        caster->m_Events.AddEventAtOffset([caster, targetGuid]()
        {
            Unit* target = ObjectAccessor::GetUnit(*caster, targetGuid);
            if (target && target->IsAlive())
                caster->CastSpell(target, SPELL_MAGE_GLACIAL_SPIKE_IMPACT, true);
        }, Milliseconds(IMPACT_DELAY_MS));
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_mage_glacial_spike::CheckIcicles);
        OnHit += SpellHitFn(spell_mage_glacial_spike::BeginRamp);
    }
};

// 200027 - Glacial Spike (Impact)
// The real damage-dealing leg of the 3-stage ramp above - a plain single-target Frost nuke at the
// real target, the same shape 200002 itself used to have before the ramp redesign. Icicle/
// Fingers-of-Frost consumption and the Arctic Winds shatter-cleave both moved here, since this is
// the stage that represents the spell actually landing.
class spell_mage_glacial_spike_impact : public SpellScript
{
    PrepareSpellScript(spell_mage_glacial_spike_impact);

    static constexpr uint8 MAX_SHATTER_TARGETS = 5;
    static constexpr float SHATTER_RADIUS = 8.0f;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_ICICLES, SPELL_MAGE_SHATTERING_COLD, SPELL_MAGE_FINGERS_OF_FROST_CHARGES, SPELL_MAGE_GLACIAL_SPIKE_SHATTER });
    }

    void ConsumeIciclesAndFrostCharge()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target)
            return;

        caster->RemoveAurasDueToSpell(SPELL_MAGE_ICICLES);
        FrostMageRework::ConsumeFingersOfFrostIfSoleSource(caster, target);

        // Arctic Winds capstone (docs/frost-mage-redesign.md sec 4 Row 9 / sec 1 Glacial Spike,
        // rank 3 only) - "the spike shatters on impact, striking up to 5 additional enemies within
        // 8 yards." Icon 2131 is Arctic Winds' own (mage_talents.csv), EFFECT_2 only present on its
        // rank-3 spell - same "top-rank-only dummy marker" idiom as Frostbite/Ice Shards. The
        // shattered hit deals its own independent damage (SPELL_MAGE_GLACIAL_SPIKE_SHATTER, same
        // 1500 base + 1.2 SP coeff as Glacial Spike itself) rather than re-triggering Glacial Spike
        // proper, which would re-run icicle/Fingers-of-Frost consumption per additional target.
        if (!caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 2131, EFFECT_2))
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, caster, SHATTER_RADIUS);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, SHATTER_RADIUS);
        nearby.remove(target);
        if (nearby.empty())
            return;

        Acore::Containers::RandomResize(nearby, MAX_SHATTER_TARGETS);

        for (Unit* shatterTarget : nearby)
            caster->CastSpell(shatterTarget, SPELL_MAGE_GLACIAL_SPIKE_SHATTER, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_mage_glacial_spike_impact::ConsumeIciclesAndFrostCharge);
    }
};

// 200001 - Icicles
// No fixed duration (see the CSV row's notes) - cleared here on combat-leave; consumption on
// Glacial Spike impact is handled above in spell_mage_glacial_spike_impact.
class FrostMageIcicleCombatReset : public PlayerScript
{
public:
    FrostMageIcicleCombatReset() : PlayerScript("FrostMageIcicleCombatReset", { PLAYERHOOK_ON_PLAYER_LEAVE_COMBAT }) { }

    void OnPlayerLeaveCombat(Player* player) override
    {
        player->RemoveAurasDueToSpell(SPELL_MAGE_ICICLES);
    }
};

// 200004 - Flurry
class spell_mage_flurry : public SpellScript
{
    PrepareSpellScript(spell_mage_flurry);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_SHATTERING_COLD });
    }

    // Applied once here, after Flurry's own three SCHOOL_DAMAGE effects (the CSV row's
    // effect1-3) have already resolved for this hit - that ordering is what makes
    // "Flurry's own bolts do not benefit from Shattering Cold" true with no extra guard.
    void ApplyShatteringCold()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (caster && target)
            caster->CastSpell(target, SPELL_MAGE_SHATTERING_COLD, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_mage_flurry::ApplyShatteringCold);
    }
};

// 200012 - Biting Cold (rank 3 capstone only; ranks 1-2 are a plain SPELL_AURA_DUMMY read
// straight out of Unit::SpellDamageBonusDone, no script needed for those).
// docs/frost-mage-redesign.md sec 4 Row 2: "Dealing direct Frost damage to a chilled enemy has a
// 15% chance to bite into a nearby enemy within 8 yards, dealing Frost damage and chilling them.
// Cannot occur more than once every 6 sec."
class spell_mage_biting_cold : public AuraScript
{
    PrepareAuraScript(spell_mage_biting_cold);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_BITING_COLD_BITE });
    }

    // The native ProcChance/ProcTypeMask/AttributesEx3 (copied from Brain Freeze, see
    // mage_talents.csv notes on 200012) already gate this to direct Frost/spell damage the mage
    // deals; the only thing left to check here is "was the struck target already chilled".
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = eventInfo.GetProcTarget();
        return target && target->HasAuraWithMechanic(1ULL << MECHANIC_SNARE);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
        if (_cooldownEnd > now)
            return;

        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        // Search near the struck target (not the caster) for another enemy within 8 yards.
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, caster, 8.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, 8.0f);
        nearby.remove(target);
        if (nearby.empty())
            return;

        _cooldownEnd = now + std::chrono::seconds(6);

        Unit* biteTarget = Acore::Containers::SelectRandomContainerElement(nearby);
        caster->CastSpell(biteTarget, SPELL_MAGE_BITING_COLD_BITE, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_biting_cold::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_biting_cold::HandleProc, EFFECT_1, SPELL_AURA_PROC_TRIGGER_SPELL);
    }

private:
    std::chrono::steady_clock::time_point _cooldownEnd = std::chrono::steady_clock::time_point::min();
};

// 11071, 12496, 12497 - Frostbite (docs/frost-mage-redesign.md sec 4 Row 1)
// "Dealing direct Frost damage has a 5/10/15% chance to freeze the target for 5 sec. The freeze
// breaks on damage." Freezing and breaking on damage both come for free from native data on the
// triggered spell (12494): its Frost-school MOD_ROOT effect already satisfies
// SpellInfo::GetAuraState's generic "Frost school + stun/root effect -> AURA_STATE_FROZEN" check
// (SpellInfo.cpp), the same mechanism Frost Nova's own root relies on, so Shatter/Ice Lance/Deep
// Freeze's usability gate all recognize it with no extra wiring; its AuraInterruptFlags now
// includes AURA_INTERRUPT_FLAG_TAKE_DAMAGE (same flag Polymorph uses), so it breaks on any damage
// natively too. The only thing left to check here is that the damage which procced this was
// actually Frost school - the pulled data's EffectSpellClassMask scoped the old ADD_TARGET_TRIGGER
// version to a handful of named "chill" spells (and, being a classmask, could never reach a
// no-SpellFamilyFlags scripted trigger spell like Frozen Orb - same reachability hole as Chilled to
// the Bone's), so the effect was converted to a plain SPELL_AURA_PROC_TRIGGER_SPELL (no classmask)
// and the school check moved here, matching Biting Cold/Brain Freeze's existing "school check in
// CheckProc" idiom instead.
class spell_mage_frostbite : public AuraScript
{
    PrepareAuraScript(spell_mage_frostbite);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && (spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST) != 0;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_frostbite::CheckProc);
    }
};

// 200006 - Refreshment (Conjure Refreshment's item, 43518 "Conjured Mana Pie")
// docs/frost-mage-redesign.md sec 2: "Restores 100% of max health and 100% of max mana over
// 30 sec." Built on the real native Food/Drink mechanism (SPELL_AURA_MOD_REGEN/MOD_POWER_REGEN,
// the same aura types the pulled 61829/61830 use) rather than a dedicated periodic heal/energize
// aura - this gets the real "eating/drinking" emote for free (Player.cpp's food-emote code
// specifically looks for these two aura types) at the cost of precision: MOD_REGEN's health
// contribution only applies on the player's global 2-sec regen tick, whose phase isn't reset on
// aura apply, so the number of ticks across a fixed 30s window isn't exactly 15 every time.
// Deliberately not chasing exactness here - CalcAmount below targets 105% instead of 100%, and
// both RegenerateHealth() and Regenerate(POWER_MANA) already clamp at max (see their `curValue ==
// maxValue` early-outs), so overshooting the math just means "reliably reaches full before the
// duration runs out" rather than any real overheal.
class spell_mage_refreshment : public AuraScript
{
    PrepareAuraScript(spell_mage_refreshment);

    // MOD_REGEN's own formula (Player::RegenerateHealth()) adds `modifier * 0.4` on each 2-sec
    // regen tick while out of combat - 15 nominal ticks over this aura's 30-sec duration, so
    // total = modifier * 6. Solving `modifier * 6 = maxStat * TARGET_PCT` gives the divisor below.
    // (MOD_POWER_REGEN's mana math works out to the same "* 6" shape - see
    // Player::UpdateManaRegen()/Regenerate(POWER_MANA) - and mana regen isn't tick-quantized the
    // way health is, so it's the more reliable of the two either way.)
    static constexpr float TARGET_PCT = 1.05f;
    static constexpr float NOMINAL_TICKS_TIMES_POINT_FOUR = 6.0f;

    void CalcHeal(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* target = GetUnitOwner())
            amount = int32(target->GetMaxHealth() * TARGET_PCT / NOMINAL_TICKS_TIMES_POINT_FOUR);
    }

    void CalcMana(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* target = GetUnitOwner())
            amount = int32(target->GetMaxPower(POWER_MANA) * TARGET_PCT / NOMINAL_TICKS_TIMES_POINT_FOUR);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_refreshment::CalcHeal, EFFECT_0, SPELL_AURA_MOD_REGEN);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_refreshment::CalcMana, EFFECT_1, SPELL_AURA_MOD_POWER_REGEN);
    }
};

/*
 * Frozen Orb (docs/frost-mage-redesign.md sec 1; full design/gotchas in
 * docs/frost-mage-implementation-plan.md's dedicated "Frozen Orb Implementation" section).
 * 200007 is a SPELL_EFFECT_SCRIPT_EFFECT that summons the trigger creature (npc_mage_frozen_orb,
 * NPC_MAGE_FROZEN_ORB) at the caster's position; the creature's own AI drives everything else -
 * movement, the self-cast periodic pulse (200009, triggering the actual damage/slow in 200008),
 * and the Fingers of Frost grant chain. No spell-row work ties these three together beyond
 * 200009's EffectTriggerSpell pointing at 200008 and the AI's own me->CastSpell(me, 200009, ...).
 */
namespace
{
    constexpr uint32 POINT_FROZEN_ORB_END = 1;
    constexpr uint32 EVENT_FROZEN_ORB_GRANT_FOF = 1;
    // Matches both the orb's TEMPSUMMON_TIMED_DESPAWN lifetime and 200009's own duration, so its
    // 10th and final pulse (one per second) lands right as it expires.
    constexpr uint32 FROZEN_ORB_DURATION = 10000;
    // Travel distance, yards - not yet modified by Arctic Reach (that talent isn't built; see the
    // Frost talent tree item in docs/frost-mage-handoff.md).
    constexpr float FROZEN_ORB_TRAVEL_DISTANCE = 30.0f;
    constexpr float FROZEN_ORB_SPEED_RATE = 0.55f;
}

// 300001 - Frozen Orb (the projectile itself). Display left as the stock invisible-stalker model
// (1126) pending an art pass - picking a real "glowing orb" model is an interactive, in-game task
// (.morph browsing a reference client) per the implementation plan's notes, not something to guess
// here; see any of this session's other "SpellVisualID unset" spells for the same deferral.
class npc_mage_frozen_orb : public CreatureAI
{
public:
    explicit npc_mage_frozen_orb(Creature* creature) : CreatureAI(creature) { }

    // Frozen Orb's damage/threat/combat-log attribution isn't actually routed through the caster
    // chain to the owning player (traced for Chilled to the Bone's capstone: the periodic aura
    // 200009's own EffectTriggerSpell dispatch to 200008, AuraEffect::HandlePeriodicTriggerSpellAuraTick
    // in SpellAuraEffects.cpp, re-derives its trigger caster from either the tick's caster or its
    // target depending on SpellInfo::NeedsToBeTriggeredByCaster - for a plain AoE-from-source spell
    // like 200008 that resolves false, so the trigger is always cast "as the orb" regardless of what
    // 200009 itself was cast with; a fix would mean rearchitecting away from the native periodic-aura
    // dispatch, out of scope here and risky to the already-working orb behavior). Flagged, not fixed -
    // see docs/frost-mage-talent-tree-content-handoff.md. This getter exists so scripts that only
    // need to *look up* the owning player (not fix that deeper routing) - like the pulse script's
    // Chilled to the Bone check - can do so the same way GrantFingersOfFrost() below already does.
    ObjectGuid GetOwnerGUID() const { return _ownerGUID; }

    // The faction-35 trap (implementation plan): a trigger left on its default friendly-to-
    // everyone faction finds zero targets for its own TARGET_UNIT_SRC_AREA_ENEMY pulse cast.
    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* owner = summoner->ToUnit();
        if (!owner)
            return;

        _ownerGUID = owner->GetGUID();
        me->SetFaction(owner->GetFaction());

        me->SetDisableGravity(true);
        me->SetHover(true);
        me->SetSpeedRate(MOVE_RUN, FROZEN_ORB_SPEED_RATE);

        // Walks the line from the owner's position along their facing, clamped at the first wall
        // or terrain collision - called on the owner (not `me`) because that's whose facing at
        // cast time determines the orb's direction.
        Position dest = owner->GetFirstCollisionPosition(FROZEN_ORB_TRAVEL_DISTANCE, 0.0f);
        // generatePath=false: with pathfinding on, the orb curves around obstacles like a mob
        // giving chase, which looks wrong for a projectile. Issued once - re-issuing every tick
        // would resend SMSG_MONSTER_MOVE every tick and make the client visibly stutter.
        me->GetMotionMaster()->MovePoint(POINT_FROZEN_ORB_END, dest, FORCED_MOVEMENT_NONE, 0.0f, false);

        me->CastSpell(me, SPELL_MAGE_FROZEN_ORB_PERIODIC, true);
    }

    // Called from spell_mage_frozen_orb_pulse::NotifyOrb (OnEffectHitTarget on 200008) whenever a
    // pulse actually connects with an enemy. Both the "slows down significantly after dealing
    // damage" travel change and the Fingers of Frost grant chain start here -
    // docs/frost-mage-redesign.md sec 1: "Grants 1 charge when the orb first strikes any enemy,
    // then 1 additional charge every 3 sec while active."
    void NotifyPulseHit()
    {
        if (_halted)
            return;
        _halted = true;

        // Not Kill() (fires death events/loot/combat log noise for a trigger) and not setting
        // speed to 0 (divide-by-zero paths in movement code, desyncs the client) - see the
        // implementation plan's notes.
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->StopMoving();

        GrantFingersOfFrost();
        _events.ScheduleEvent(EVENT_FROZEN_ORB_GRANT_FOF, 3s);
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            if (eventId == EVENT_FROZEN_ORB_GRANT_FOF)
            {
                GrantFingersOfFrost();
                _events.ScheduleEvent(EVENT_FROZEN_ORB_GRANT_FOF, 3s);
            }
        }
    }

private:
    void GrantFingersOfFrost()
    {
        if (Unit* owner = ObjectAccessor::GetUnit(*me, _ownerGUID))
            owner->CastSpell(owner, SPELL_MAGE_FINGERS_OF_FROST_CHARGES, true);
    }

    ObjectGuid _ownerGUID;
    EventMap _events;
    bool _halted = false;
};

// 200007 - Frozen Orb
class spell_mage_frozen_orb : public SpellScript
{
    PrepareSpellScript(spell_mage_frozen_orb);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FROZEN_ORB_PERIODIC });
    }

    void SummonOrb(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            caster->SummonCreature(NPC_MAGE_FROZEN_ORB, *caster, TEMPSUMMON_TIMED_DESPAWN, FROZEN_ORB_DURATION);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_mage_frozen_orb::SummonOrb, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// 200008 - Frozen Orb Pulse. Damage/slow is native DBC data (see mage.csv's notes on this ID) -
// this script only exists to tell the orb's AI a pulse actually landed.
class spell_mage_frozen_orb_pulse : public SpellScript
{
    PrepareSpellScript(spell_mage_frozen_orb_pulse);

    // The owning mage, not GetCaster() (the orb itself) - see npc_mage_frozen_orb::GetOwnerGUID's
    // comment for why GetOriginalCaster() can't be used here instead.
    Player* GetOwningMage()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return nullptr;

        Creature* orb = caster->ToCreature();
        if (!orb)
            return nullptr;

        npc_mage_frozen_orb* ai = dynamic_cast<npc_mage_frozen_orb*>(orb->AI());
        if (!ai)
            return nullptr;

        Unit* owner = ObjectAccessor::GetUnit(*orb, ai->GetOwnerGUID());
        return owner ? owner->ToPlayer() : nullptr;
    }

    void NotifyOrb(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        if (Creature* orb = caster->ToCreature())
            if (npc_mage_frozen_orb* ai = dynamic_cast<npc_mage_frozen_orb*>(orb->AI()))
                ai->NotifyPulseHit();
    }

    // Chilled to the Bone base effect (docs/frost-mage-redesign.md sec 4 Row 10) - "Reduces the
    // movement speed of targets affected by Frostbolt, Cone of Cold and Frozen Orb by an
    // additional 4/7/10%." The talent's own slow boost is a classmask-scoped SpellMod
    // (EffectSpellClassMaskA_2: 544 on 44566-44568) that can never reach this spell - 200008 has no
    // SpellFamilyFlags of its own to match against, same reachability hole flagged on the talent's
    // own CSV row. Applied by hand instead: read the owning mage's own copy of that effect (icon
    // 2965, EFFECT_1 - present on every rank) and fold its amount into this pulse's slow before it
    // applies, same "boost a live effect value" idiom as spell_warr_vigilance_redirect_threat.
    void BoostChillEffect(SpellEffIndex /*effIndex*/)
    {
        Player* mage = GetOwningMage();
        if (!mage)
            return;

        if (AuraEffect const* chilledToTheBone = mage->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_MAGE, 2965, EFFECT_1))
            SetEffectValue(GetEffectValue() + chilledToTheBone->GetAmount());
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_mage_frozen_orb_pulse::NotifyOrb, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        OnEffectLaunchTarget += SpellEffectFn(spell_mage_frozen_orb_pulse::BoostChillEffect, EFFECT_1, SPELL_EFFECT_APPLY_AURA);
    }
};

// 44566, 44567, 44568 - Chilled to the Bone capstone (rank 3 only, EFFECT_2)
// docs/frost-mage-redesign.md sec 4 Row 10: "Your Frostbolt and Ice Lance casts versus monsters
// reduce the cooldown of your Frozen Orb by 1 sec, and your Blizzard reduces it by 1 sec every 3
// ticks." Frostbolt/Ice Lance are identified by their own SpellFamilyFlags bits (32 | 131072 -
// matches Improved Frostbolt's own classmask this session), Blizzard by its (524416 - matches
// Improved Blizzard's own classmask). "Versus monsters" excludes players and player-controlled
// pets/guardians (PvP), not just non-hostile targets. Frozen Orb has no cooldown of its own to
// reduce until it's actually been cast, so Player::ModifySpellCooldown's no-op-if-not-cooling-down
// behavior is exactly right here - nothing to guard for.
class spell_mage_chilled_to_the_bone : public AuraScript
{
    PrepareAuraScript(spell_mage_chilled_to_the_bone);

    static constexpr uint32 FROSTBOLT_ICE_LANCE_MASK = 131104; // Frostbolt (32) | Ice Lance (131072)
    static constexpr uint32 BLIZZARD_MASK = 524416;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FROZEN_ORB });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = eventInfo.GetProcTarget();
        if (!target || !target->IsCreature() || target->IsControlledByPlayer())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_MAGE
            && (spellInfo->SpellFamilyFlags[0] & (FROSTBOLT_ICE_LANCE_MASK | BLIZZARD_MASK)) != 0;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        Player* caster = GetTarget()->ToPlayer();
        if (!caster)
            return;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        bool reduce;
        if (spellInfo->SpellFamilyFlags[0] & FROSTBOLT_ICE_LANCE_MASK)
            reduce = true;
        else // Blizzard - only every 3rd tick
            reduce = (++_blizzardTicks % 3) == 0;

        if (reduce)
            caster->ModifySpellCooldown(SPELL_MAGE_FROZEN_ORB, -1000);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_chilled_to_the_bone::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_chilled_to_the_bone::HandleProc, EFFECT_2, SPELL_AURA_DUMMY);
    }

private:
    uint32 _blizzardTicks = 0;
};

/*
 * Talent Tree Step 3, Cluster C (docs/frost-mage-talent-tree-content-handoff.md) - Permafrost,
 * Frozen Core, Enduring Winter's capstone. Improved Cone of Cold's capstone (200020) and
 * Empowering Frostbolt's buff (200023/200024) are pure native data (ProcCharges/proc-trigger,
 * no script) and Shattered Barrier's capstone lives on the existing spell_mage_ice_barrier_aura
 * class below rather than a new one, since it needs that class's own AfterEffectAbsorb hook.
 */

// 12571 - Permafrost (rank 3 capstone only; ranks 1-2's duration+slow bonus on Frostbolt/Cone of
// Cold are pure classmask SpellMods, no script - see mage_talents.csv's notes on this row).
// docs/frost-mage-redesign.md sec 4 Row 2: "Each 1 sec you spend moving grants Permafrost,
// increasing the damage of your next Ice Lance by 20%. Stacks up to 5 times." Ticks every 1 sec
// (EFFECT_2, SPELL_AURA_PERIODIC_DUMMY) and only grants a stack on a tick where the caster was
// actually moving - not a stock aura shape, so tracked here instead of as a plain periodic proc.
class spell_mage_permafrost : public AuraScript
{
    PrepareAuraScript(spell_mage_permafrost);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_PERMAFROST_STACK });
    }

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetTarget();
        if (caster && caster->isMoving())
            caster->CastSpell(caster, SPELL_MAGE_PERMAFROST_STACK, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_mage_permafrost::OnPeriodic, EFFECT_2, SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 30455 - Ice Lance. Consumes the *entire* Permafrost buff (200015) in one cast, however many
// stacks are banked - the damage bonus itself is read in Mage::ApplyDoneDamagePctMods
// (MageMechanics.cpp) *before* this fires (damage calc happens ahead of OnHit's post-processing,
// same relative ordering Biting Cold and Flurry already rely on), so reading-then-consuming here
// is safe. Playtest bugfix (2026-08-26, user call): originally consumed 1 stack per cast for a
// flat +20% regardless of banked count - changed to clear-all-at-once so banking up multiple
// stacks before casting is actually worth doing (the damage bonus now scales with stack count to
// match, see MageMechanics.cpp).
class spell_mage_ice_lance : public SpellScript
{
    PrepareSpellScript(spell_mage_ice_lance);

    void ConsumePermafrost()
    {
        if (Unit* caster = GetCaster())
            caster->RemoveAurasDueToSpell(SPELL_MAGE_PERMAFROST_STACK);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_mage_ice_lance::ConsumePermafrost);
    }
};

// 6136 (Frost Armor) / 7321 (Ice Armor) - "Chilled", the melee-reactive slow both armors proc
// onto whoever hits the mage. Permafrost's duration+slow bonus (talent 65, 11175/12569/12571)
// can't reach these via classmask - like Frozen Orb before it, they're npc.csv trigger-only
// spells with no SpellFamilyFlags of their own to match against. Boosted by hand instead: read
// the mage's own Permafrost SpellMod amounts (icon 143) live and fold them into this cast before
// it applies - same "boost a live effect value" idiom as spell_mage_frozen_orb_pulse's Chilled to
// the Bone fix. GetCaster() here is the mage (the defender self-casts this reactive proc onto the
// attacker), not the attacker.
class spell_mage_chilled : public SpellScript
{
    PrepareSpellScript(spell_mage_chilled);

    void BoostSlow(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        if (AuraEffect const* slowMod = caster->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_MAGE, 143, EFFECT_1))
            SetEffectValue(GetEffectValue() + slowMod->GetAmount());
    }

    void ExtendDuration()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        AuraEffect const* durationMod = caster->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_MAGE, 143, EFFECT_0);
        if (!durationMod)
            return;

        if (Aura* hitAura = GetHitAura())
            hitAura->SetDuration(hitAura->GetDuration() + durationMod->GetAmount());
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_mage_chilled::BoostSlow, EFFECT_0, SPELL_EFFECT_APPLY_AURA);
        OnHit += SpellHitFn(spell_mage_chilled::ExtendDuration);
    }
};

// 31667/31668/31669 - Frozen Core (docs/frost-mage-redesign.md sec 4 Row 5). effect1 (magic
// damage taken -2/4/6%) and effect2 (taking magic damage grants a Frost-damage buff, all 3 ranks)
// are both pure native data, no script. This class exists only for rank 3's capstone (effect3):
// "Your Ice Lance critical strikes against frozen targets pierce to the target's core, dealing
// Frost damage over 8 sec." effect2 and effect3 share this spell's one spell-wide ProcFlags
// (confirmed by reading Aura::GetProcEffectMask/AuraEffect::CheckEffectProc/
// SpellMgr::CanSpellTriggerProcOnEvent directly - native PROC_TRIGGER_SPELL effects on the same
// entry can't have independently-scoped ProcTypeMask/HitMask/SpellFamilyMask), so both handlers
// discriminate their own event manually instead of relying on the native default action for
// either.
class spell_mage_frozen_core : public AuraScript
{
    PrepareAuraScript(spell_mage_frozen_core);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FROZEN_CORE_PIERCE });
    }

    // effect2 (buff grant) - this spell's shared ProcFlags also admits DONE-direction events
    // (needed for effect3 below), so a plain Ice Lance cast would otherwise also fire this
    // effect's native default action. Gate it here instead.
    void HandleBuffProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        if (!(eventInfo.GetTypeMask() & (PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG | PROC_FLAG_TAKEN_PERIODIC)))
            PreventDefaultAction();
    }

    void HandleCapstoneProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_MAGE
            || !(spellInfo->SpellFamilyFlags[0] & 0x20000)) // Ice Lance
            return;

        if (!(eventInfo.GetHitMask() & PROC_HIT_CRITICAL))
            return;

        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target || !Mage::IsFrozenTarget(caster, target))
            return;

        caster->CastSpell(target, SPELL_MAGE_FROZEN_CORE_PIERCE, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_frozen_core::HandleBuffProc, EFFECT_1, SPELL_AURA_PROC_TRIGGER_SPELL);
        OnEffectProc += AuraEffectProcFn(spell_mage_frozen_core::HandleCapstoneProc, EFFECT_2, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 44561 - Enduring Winter (rank 3 capstone only; effect1's duration bonus and effect2's
// Replenishment proc, all 3 ranks, are unchanged native data). docs/frost-mage-redesign.md sec 4
// Row 9: "While your Water Elemental is active, each Frostbolt you cast extends its duration by
// 2 sec." effect3 is a plain SPELL_AURA_DUMMY sharing effect2's existing scope (this spell's base
// spell_proc row, -44557, already Frostbolt-only - confirmed in data/sql/base/db_world/
// spell_proc.sql, not something this migration touches), so no new spell_proc row is needed.
// Pet inherits TempSummon's timer API directly (Pet -> Guardian -> Minion -> TempSummon); no-ops
// for the permanent (Glyph of Eternal Water) variant, which has nothing to extend.
class spell_mage_enduring_winter : public AuraScript
{
    PrepareAuraScript(spell_mage_enduring_winter);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        Player* caster = GetTarget()->ToPlayer();
        if (!caster)
            return;

        Pet* pet = caster->GetPet();
        if (!pet || pet->GetEntry() != NPC_WATER_ELEMENTAL_TEMP)
            return;

        pet->SetTimer(pet->GetTimer() + 2000);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_enduring_winter::HandleProc, EFFECT_2, SPELL_AURA_DUMMY);
    }
};

class spell_mage_arcane_blast : public SpellScript
{
    PrepareSpellScript(spell_mage_arcane_blast);

    bool Load() override { _triggerSpellId = 0; return true; }

    void HandleTriggerSpell(SpellEffIndex effIndex)
    {
        _triggerSpellId = GetSpellInfo()->Effects[effIndex].TriggerSpell;
        PreventHitDefaultEffect(effIndex);
    }

    void HandleAfterCast()
    {
        GetCaster()->CastSpell(GetCaster(), _triggerSpellId, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectLaunch += SpellEffectFn(spell_mage_arcane_blast::HandleTriggerSpell, EFFECT_1, SPELL_EFFECT_TRIGGER_SPELL);
        OnEffectLaunchTarget += SpellEffectFn(spell_mage_arcane_blast::HandleTriggerSpell, EFFECT_1, SPELL_EFFECT_TRIGGER_SPELL);
        AfterCast += SpellCastFn(spell_mage_arcane_blast::HandleAfterCast);
    }

private:
    uint32 _triggerSpellId;
};

class spell_mage_burning_determination : public AuraScript
{
    PrepareAuraScript(spell_mage_burning_determination);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!eventInfo.GetSpellInfo() || !eventInfo.GetActionTarget())
            return false;

        // Need Interrupt or Silenced mechanic
        if (!(eventInfo.GetSpellInfo()->GetAllEffectsMechanicMask() & ((1ULL << MECHANIC_INTERRUPT) | (1ULL << MECHANIC_SILENCE))))
            return false;

        Unit* target = eventInfo.GetActionTarget();

        // This hook runs while the proc engine iterates the target's aura map; removing an
        // aura inline would invalidate the live iterator (aura containers are flat_multimaps).
        // Defer removals to the target's event queue so they run outside the proc walk.
        // Xinef: immuned effect should just eat charge
        if (eventInfo.GetHitMask() & PROC_EX_IMMUNE)
        {
            target->m_Events.AddEventAtOffset([target]() { target->RemoveAurasDueToSpell(54748); }, 1ms);
            return false;
        }
        if (Aura* aura = target->GetAura(54748))
        {
            if (aura->GetDuration() < aura->GetMaxDuration())
                target->m_Events.AddEventAtOffset([target]() { target->RemoveAurasDueToSpell(54748); }, 1ms);
            return false;
        }

        return true;
    }

    void HandleProc(ProcEventInfo&  /*eventInfo*/)
    {
        PreventDefaultAction();
        GetUnitOwner()->CastSpell(GetUnitOwner(), 54748, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_burning_determination::CheckProc);
        OnProc += AuraProcFn(spell_mage_burning_determination::HandleProc);
    }
};

class spell_mage_molten_armor : public AuraScript
{
    PrepareAuraScript(spell_mage_molten_armor);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || (eventInfo.GetTypeMask() & PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK))
            return true;

        if (!eventInfo.GetActionTarget())
        {
            return false;
        }

        // Xinef: Molten Shields talent
        if (AuraEffect* aurEff = eventInfo.GetActionTarget()->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_MAGE, 16, EFFECT_0))
            return roll_chance_i(aurEff->GetSpellInfo()->GetRank() * 50);

        return false;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_molten_armor::CheckProc);
    }
};

class spell_mage_mirror_image : public AuraScript
{
    PrepareAuraScript(spell_mage_mirror_image)

    void HandleEffectApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->CastSpell((Unit*)nullptr, GetSpellInfo()->Effects[aurEff->GetEffIndex()].TriggerSpell, true);
    }

    void CalcPeriodic(AuraEffect const* /*effect*/, bool& isPeriodic, int32&  /*amplitude*/)
    {
        isPeriodic = false;
    }

    void Register() override
    {
        OnEffectApply += AuraEffectApplyFn(spell_mage_mirror_image::HandleEffectApply, EFFECT_2, SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(spell_mage_mirror_image::CalcPeriodic, EFFECT_2, SPELL_AURA_PERIODIC_DUMMY);
    }
};

class spell_mage_burnout : public AuraScript
{
    PrepareAuraScript(spell_mage_burnout);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_BURNOUT_TRIGGER });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return eventInfo.GetSpellInfo() != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        int32 mana = int32(eventInfo.GetSpellInfo()->CalcPowerCost(GetTarget(), eventInfo.GetSchoolMask()));
        mana = CalculatePct(mana, aurEff->GetAmount());

        GetTarget()->CastCustomSpell(SPELL_MAGE_BURNOUT_TRIGGER, SPELLVALUE_BASE_POINT0, mana, GetTarget(), true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_burnout::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_burnout::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

class spell_mage_burnout_trigger : public SpellScript
{
    PrepareSpellScript(spell_mage_burnout_trigger);

    void HandleDummy(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);
        if (Unit* target = GetHitUnit())
        {
            int32 newDamage = -(target->ModifyPower(POWER_MANA, -GetEffectValue()));
            GetSpell()->ExecuteLogEffectTakeTargetPower(effIndex, target, POWER_MANA, newDamage, 0.0f);
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_mage_burnout_trigger::HandleDummy, EFFECT_0, SPELL_EFFECT_POWER_BURN);
    }
};

class spell_mage_pet_scaling : public AuraScript
{
    PrepareAuraScript(spell_mage_pet_scaling);

    void CalculateResistanceAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: mage pet inherits 40% of resistance from owner and 35% of armor (guessed)
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            SpellSchoolMask schoolMask = SpellSchoolMask(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            int32 modifier = schoolMask == SPELL_SCHOOL_MASK_NORMAL ? 35 : 40;
            amount = CalculatePct(std::max<int32>(0, owner->GetResistance(schoolMask)), modifier);
        }
    }

    void CalculateStatAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: mage pet inherits 30% of intellect / stamina
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            Stats stat = Stats(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            amount = CalculatePct(std::max<int32>(0, owner->GetStat(stat)), 30);
        }
    }

    void CalculateAPAmount(AuraEffect const*  /*aurEff*/, int32&   /*amount*/, bool& /*canBeRecalculated*/)
    {
        // xinef: mage pet inherits 0% AP
    }

    void CalculateSPAmount(AuraEffect const*  /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: mage pet inherits 33% of SP
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            int32 frost = owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_FROST);
            amount = CalculatePct(std::max<int32>(0, frost), 33);

            // xinef: Update appropriate player field
            if (owner->IsPlayer())
                owner->SetUInt32Value(PLAYER_PET_SPELL_POWER, (uint32)amount);
        }
    }

    void HandleEffectApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (GetUnitOwner()->IsPet())
            return;

        GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, aurEff->GetAuraType(), true, SPELL_BLOCK_TYPE_POSITIVE);
        if (aurEff->GetAuraType() == SPELL_AURA_MOD_ATTACK_POWER)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_ATTACK_POWER_PCT, true, SPELL_BLOCK_TYPE_POSITIVE);
        else if (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE, true, SPELL_BLOCK_TYPE_POSITIVE);
    }

    void CalcPeriodic(AuraEffect const* /*aurEff*/, bool& isPeriodic, int32& amplitude)
    {
        if (!GetUnitOwner()->IsPet())
            return;

        isPeriodic = true;
        amplitude = 2 * IN_MILLISECONDS;
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();
        if (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT && (aurEff->GetMiscValue() == STAT_STAMINA || aurEff->GetMiscValue() == STAT_INTELLECT))
        {
            int32 currentAmount = aurEff->GetAmount();
            int32 newAmount = GetEffect(aurEff->GetEffIndex())->CalculateAmount(GetCaster());
            if (newAmount != currentAmount)
            {
                if (aurEff->GetMiscValue() == STAT_STAMINA)
                {
                    uint32 actStat = GetUnitOwner()->GetHealth();
                    GetEffect(aurEff->GetEffIndex())->ChangeAmount(newAmount, false);
                    GetUnitOwner()->SetHealth(std::min<uint32>(GetUnitOwner()->GetMaxHealth(), actStat));
                }
                else
                {
                    uint32 actStat = GetUnitOwner()->GetPower(POWER_MANA);
                    GetEffect(aurEff->GetEffIndex())->ChangeAmount(newAmount, false);
                    GetUnitOwner()->SetPower(POWER_MANA, std::min<uint32>(GetUnitOwner()->GetMaxPower(POWER_MANA), actStat));
                }
            }
        }
        else
            GetEffect(aurEff->GetEffIndex())->RecalculateAmount();
    }

    void Register() override
    {
        if (m_scriptSpellId != 35657)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_pet_scaling::CalculateResistanceAmount, EFFECT_ALL, SPELL_AURA_MOD_RESISTANCE);

        if (m_scriptSpellId == 35657 || m_scriptSpellId == 35658)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_pet_scaling::CalculateStatAmount, EFFECT_ALL, SPELL_AURA_MOD_STAT);

        if (m_scriptSpellId == 35657)
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_pet_scaling::CalculateAPAmount, EFFECT_ALL, SPELL_AURA_MOD_ATTACK_POWER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_pet_scaling::CalculateSPAmount, EFFECT_ALL, SPELL_AURA_MOD_DAMAGE_DONE);
        }

        OnEffectApply += AuraEffectApplyFn(spell_mage_pet_scaling::HandleEffectApply, EFFECT_ALL, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(spell_mage_pet_scaling::CalcPeriodic, EFFECT_ALL, SPELL_AURA_ANY);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_mage_pet_scaling::HandlePeriodic, EFFECT_ALL, SPELL_AURA_ANY);
    }
};

class spell_mage_brain_freeze : public AuraScript
{
    PrepareAuraScript(spell_mage_brain_freeze);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // xinef: Improved Blizzard, generic chilled check
        if (spellInfo->SpellFamilyFlags[0] & 0x100000)
            return spellInfo->Id == SPELL_MAGE_IMPROVED_BLIZZARD_CHILLED;

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_brain_freeze::CheckProc);
    }
};

class spell_mage_glyph_of_eternal_water : public AuraScript
{
    PrepareAuraScript(spell_mage_glyph_of_eternal_water);

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* target = GetTarget())
            if (Player* player = target->ToPlayer())
                if (Pet* pet = player->GetPet())
                    if (pet->GetEntry() == NPC_WATER_ELEMENTAL_PERM)
                        pet->Remove(PET_SAVE_NOT_IN_SLOT);
    }

    void Register() override
    {
        OnEffectRemove += AuraEffectRemoveFn(spell_mage_glyph_of_eternal_water::OnRemove, EFFECT_0, SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

    class spell_mage_combustion_proc : public AuraScript
    {
        PrepareAuraScript(spell_mage_combustion_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_COMBUSTION });
    }

        void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
        {
            GetTarget()->RemoveAurasDueToSpell(SPELL_MAGE_COMBUSTION);
        }

        void Register() override
        {
            AfterEffectRemove += AuraEffectRemoveFn(spell_mage_combustion_proc::OnRemove, EFFECT_0, SPELL_AURA_ADD_FLAT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
        }
    };

// Incanter's Absorbtion
class spell_mage_incanters_absorbtion_base_AuraScript : public AuraScript
{
public:
    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_INCANTERS_ABSORBTION_TRIGGERED, SPELL_MAGE_INCANTERS_ABSORBTION_R1 });
    }

    void Trigger(AuraEffect* aurEff, DamageInfo& /*dmgInfo*/, uint32& absorbAmount)
    {
        Unit* target = GetTarget();

        if (AuraEffect* talentAurEff = target->GetAuraEffectOfRankedSpell(SPELL_MAGE_INCANTERS_ABSORBTION_R1, EFFECT_0))
        {
            int32 bp = CalculatePct(absorbAmount, talentAurEff->GetAmount());
            if (AuraEffect* currentAura = target->GetAuraEffect(SPELL_AURA_MOD_DAMAGE_DONE, SPELLFAMILY_MAGE, 2941, EFFECT_0))
            {
                bp += int32(currentAura->GetAmount() * (currentAura->GetBase()->GetDuration() / (float)currentAura->GetBase()->GetMaxDuration()));
                currentAura->ChangeAmount(bp);
                currentAura->GetBase()->RefreshDuration();
            }
            else
                target->CastCustomSpell(target, SPELL_MAGE_INCANTERS_ABSORBTION_TRIGGERED, &bp, nullptr, nullptr, true, nullptr, aurEff);
        }
    }
};

// -11113 - Blast Wave
class spell_mage_blast_wave : public SpellScript
{
    PrepareSpellScript(spell_mage_blast_wave);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_GLYPH_OF_BLAST_WAVE });
    }

    void HandleKnockBack(SpellEffIndex effIndex)
    {
        if (GetCaster()->HasAura(SPELL_MAGE_GLYPH_OF_BLAST_WAVE))
            PreventHitDefaultEffect(effIndex);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_mage_blast_wave::HandleKnockBack, EFFECT_2, SPELL_EFFECT_KNOCK_BACK);
    }
};

// 11958 - Cold Snap
class spell_mage_cold_snap : public SpellScript
{
    PrepareSpellScript(spell_mage_cold_snap);

    bool Load() override
    {
        return GetCaster()->IsPlayer();
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetCaster()->ToPlayer();
        // immediately finishes the cooldown on Frost spells

        PlayerSpellMap const& spellMap = caster->GetSpellMap();
        for (PlayerSpellMap::const_iterator itr = spellMap.begin(); itr != spellMap.end(); ++itr)
        {
            SpellInfo const* spellInfo = sSpellMgr->AssertSpellInfo(itr->first);
            if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE && (spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST) && spellInfo->Id != SPELL_MAGE_COLD_SNAP && spellInfo->GetRecoveryTime() > 0)
            {
                SpellCooldowns::iterator citr = caster->GetSpellCooldownMap().find(spellInfo->Id);
                if (citr != caster->GetSpellCooldownMap().end() && citr->second.needSendToClient)
                    caster->RemoveSpellCooldown(spellInfo->Id, true);
                else
                    caster->RemoveSpellCooldown(spellInfo->Id, false);
            }
        }
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_mage_cold_snap::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -543  - Fire Ward
// -6143 - Frost Ward
class spell_mage_fire_frost_ward : public spell_mage_incanters_absorbtion_base_AuraScript
{
    PrepareAuraScript(spell_mage_fire_frost_ward);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FROST_WARDING_TRIGGERED, SPELL_MAGE_FROST_WARDING_R1 });
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
        if (Unit* caster = GetCaster())
        {
            // +80.68% from sp bonus
            float bonus = 0.8068f;

            bonus *= caster->SpellBaseDamageBonusDone(GetSpellInfo()->GetSchoolMask());
            bonus *= caster->CalculateLevelPenalty(GetSpellInfo());

            amount += int32(bonus);
        }
    }

    void Absorb(AuraEffect* aurEff, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Unit* target = GetTarget();
        if (AuraEffect* talentAurEff = target->GetAuraEffectOfRankedSpell(SPELL_MAGE_FROST_WARDING_R1, EFFECT_0))
        {
            int32 chance = talentAurEff->GetSpellInfo()->Effects[EFFECT_1].CalcValue(); // SPELL_EFFECT_DUMMY with NO_TARGET

            if (roll_chance_i(chance))
            {
                int32 bp = dmgInfo.GetDamage();
                target->CastCustomSpell(target, SPELL_MAGE_FROST_WARDING_TRIGGERED, &bp, nullptr, nullptr, true, nullptr, aurEff);
                absorbAmount = 0;

                // Xinef: trigger Incanters Absorbtion
                uint32 damage = dmgInfo.GetDamage();
                Trigger(aurEff, dmgInfo, damage);

                // Xinef: hack for chaos bolt
                if (!dmgInfo.GetSpellInfo() || dmgInfo.GetSpellInfo()->SpellIconID != 3178)
                    dmgInfo.AbsorbDamage(bp);

                PreventDefaultAction();
            }
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_fire_frost_ward::CalculateAmount, EFFECT_0, SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_mage_fire_frost_ward::Absorb, EFFECT_0);
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_mage_fire_frost_ward::Trigger, EFFECT_0);
    }
};

// 54646 - Focus Magic
class spell_mage_focus_magic : public AuraScript
{
    PrepareAuraScript(spell_mage_focus_magic);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FOCUS_MAGIC_PROC });
    }

    bool Load() override
    {
        _procTarget = nullptr;
        return true;
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        _procTarget = GetCaster();
        return _procTarget && _procTarget->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->CastSpell(_procTarget, SPELL_MAGE_FOCUS_MAGIC_PROC, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_focus_magic::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_focus_magic::HandleProc, EFFECT_0, SPELL_AURA_MOD_SPELL_CRIT_CHANCE);
    }

private:
    Unit* _procTarget;
};

namespace
{
    // Frost Mage rework (docs/frost-mage-redesign.md sec 2, Ice Barrier): "Flat absorb value
    // replaced with a scaling formula: 2000 base plus 1.0 spell power coefficient." Used to carry
    // a separate hand-rolled 0.8068 coefficient (a pre-rework, pre-single-rank-spell-system relic
    // - SCHOOL_ABSORB auras get no automatic spell_bonus_data/SpellDamageBonusDone scaling
    // anywhere in this engine, confirmed by reading AuraEffect::CalculateAmount's SCHOOL_ABSORB
    // case and every SpellBonusEntry consumer in Unit.cpp, so a manual bonus here has always been
    // the *only* source of Ice Barrier's spell power scaling, not a second one stacked on top of
    // spell_bonus_data as the last handoff worried - that entry is simply inert for this aura
    // type). Retuned to the spec's plain 1.0 coefficient and factored out of its two previously
    // duplicated copies (spell_mage_ice_barrier_aura and spell_mage_ice_barrier both had their own
    // identical copy) into this one shared helper.
    int32 ApplyIceBarrierSpellPowerBonus(Unit* caster, int32 amount, SpellInfo const* spellInfo, AuraEffect const* aurEff)
    {
        float bonus = 1.0f * caster->SpellBaseDamageBonusDone(spellInfo->GetSchoolMask());

        // Glyph of Ice Barrier: its weird having a SPELLMOD_ALL_EFFECTS here but its blizzards doing :)
        // Glyph of Ice Barrier is only applied at the spell damage bonus because it was already applied to the base value in CalculateSpellDamage
        bonus = caster->ApplyEffectModifiers(spellInfo, aurEff->GetEffIndex(), bonus);

        bonus *= caster->CalculateLevelPenalty(spellInfo);

        amount += int32(bonus);
        return amount;
    }
}

// -11426 - Ice Barrier
class spell_mage_ice_barrier_aura : public spell_mage_incanters_absorbtion_base_AuraScript
{
    PrepareAuraScript(spell_mage_ice_barrier_aura);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
        if (Unit* caster = GetCaster())
            amount = ApplyIceBarrierSpellPowerBonus(caster, amount, GetSpellInfo(), aurEff);
    }

    // Shattered Barrier capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 7,
    // rank 2) - "Your Ice Barrier shatters when destroyed, slowing all enemies within 10 yards by
    // 70% for 4 sec and granting you 8% haste for 8 sec." Fires only when this hit's absorb
    // (absorbAmount, already clamped/finalized by the caller - Unit::CalcAbsorbResist) consumes
    // the shield's entire remaining amount, not when the shield simply expires on its own -
    // gated on a rank-2-only dummy marker (talent 2214's own icon 2945, EFFECT_1).
    void HandleShatter(AuraEffect* aurEff, DamageInfo& /*dmgInfo*/, uint32& absorbAmount)
    {
        if (absorbAmount < aurEff->GetAmount())
            return; // shield still has amount left - not actually destroyed by this hit

        Unit* caster = GetTarget();
        if (!caster)
            return;

        if (!caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 2945, EFFECT_1))
            return;

        caster->CastSpell(caster, SPELL_MAGE_SHATTERED_BARRIER_SLOW, true);
        caster->CastSpell(caster, SPELL_MAGE_SHATTERED_BARRIER_HASTE, true);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_ice_barrier_aura::CalculateAmount, EFFECT_0, SPELL_AURA_SCHOOL_ABSORB);
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_mage_ice_barrier_aura::Trigger, EFFECT_0);
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_mage_ice_barrier_aura::HandleShatter, EFFECT_0);
    }
};

class spell_mage_ice_barrier : public SpellScript
{
    PrepareSpellScript(spell_mage_ice_barrier);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();

        if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_SCHOOL_ABSORB, (SpellFamilyNames)GetSpellInfo()->SpellFamilyName, GetSpellInfo()->SpellIconID, EFFECT_0))
        {
            int32 newAmount = GetSpellInfo()->Effects[EFFECT_0].CalcValue(caster, nullptr, nullptr);
            newAmount = ApplyIceBarrierSpellPowerBonus(caster, newAmount, GetSpellInfo(), aurEff);

            if (aurEff->GetAmount() > newAmount)
                return SPELL_FAILED_AURA_BOUNCED;
        }

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_mage_ice_barrier::CheckCast);
    }
};

// -11119 - Ignite
class spell_mage_ignite : public AuraScript
{
    PrepareAuraScript(spell_mage_ignite);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_IGNITE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!eventInfo.GetActor() || !eventInfo.GetProcTarget())
            return false;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();

        if (!damageInfo || !damageInfo->GetSpellInfo())
        {
            return false;
        }

        // Molten Armor
        if (SpellInfo const* spellInfo = eventInfo.GetSpellInfo())
        {
            if (spellInfo->SpellFamilyFlags[1] & 0x8)
            {
                return false;
            }
        }

        return true;
    }

    void HandleProc(AuraEffect const*  /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* igniteDot = sSpellMgr->AssertSpellInfo(SPELL_MAGE_IGNITE);
        int32 pct = 8 * GetSpellInfo()->GetRank();

        int32 amount = int32(CalculatePct(eventInfo.GetDamageInfo()->GetDamage(), pct) / igniteDot->GetMaxTicks());

        // Xinef: implement ignite bug
        eventInfo.GetProcTarget()->CastDelayedSpellWithPeriodicAmount(eventInfo.GetActor(), SPELL_MAGE_IGNITE, SPELL_AURA_PERIODIC_DAMAGE, amount);
        //GetTarget()->CastCustomSpell(SPELL_MAGE_IGNITE, SPELLVALUE_BASE_POINT0, amount, eventInfo.GetProcTarget(), true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_ignite::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_ignite::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -44457 - Living Bomb
class spell_mage_living_bomb : public AuraScript
{
    PrepareAuraScript(spell_mage_living_bomb);

    bool Validate(SpellInfo const* spell) override
    {
        if (!sSpellMgr->GetSpellInfo(uint32(spell->Effects[EFFECT_1].CalcValue())))
            return false;
        return true;
    }

    void AfterRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        AuraRemoveMode removeMode = GetTargetApplication()->GetRemoveMode();
        if (removeMode != AURA_REMOVE_BY_ENEMY_SPELL && removeMode != AURA_REMOVE_BY_EXPIRE)
            return;

        if (Unit* caster = GetCaster())
            caster->CastSpell(GetTarget(), uint32(aurEff->GetAmount()), true, nullptr, aurEff);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_mage_living_bomb::AfterRemove, EFFECT_1, SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// -1463 - Mana Shield
class spell_mage_mana_shield : public spell_mage_incanters_absorbtion_base_AuraScript
{
    PrepareAuraScript(spell_mage_mana_shield);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
        if (Unit* caster = GetCaster())
        {
            // +80.53% from sp bonus
            float bonus = 0.8053f;

            bonus *= caster->SpellBaseDamageBonusDone(GetSpellInfo()->GetSchoolMask());
            bonus *= caster->CalculateLevelPenalty(GetSpellInfo());

            amount += int32(bonus);
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_mage_mana_shield::CalculateAmount, EFFECT_0, SPELL_AURA_MANA_SHIELD);
        AfterEffectManaShield += AuraEffectManaShieldFn(spell_mage_mana_shield::Trigger, EFFECT_0);
    }
};

// -29074 - Master of Elements
class spell_mage_master_of_elements : public AuraScript
{
    PrepareAuraScript(spell_mage_master_of_elements);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_MASTER_OF_ELEMENTS_ENERGIZE, SPELL_MAGE_LIVING_BOMB_R1 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || !damageInfo->GetSpellInfo())
            return false;

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* spellInfo = eventInfo.GetDamageInfo()->GetSpellInfo();

        // Living Bomb explosion has no mana cost, use the aura spell's cost instead
        if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE
            && spellInfo->SpellIconID == MAGE_ICON_LIVING_BOMB
            && !spellInfo->ManaCost && !spellInfo->ManaCostPercentage)
        {
            uint8 rank = sSpellMgr->GetSpellRank(spellInfo->Id);
            spellInfo = sSpellMgr->GetSpellInfo(
                sSpellMgr->GetSpellWithRank(SPELL_MAGE_LIVING_BOMB_R1, rank));
            if (!spellInfo)
                return;
        }

        // Use base mana cost (ManaCost + ManaCostPercentage) without spell mods,
        // as the talent refunds based on "base mana cost"
        int32 mana = spellInfo->ManaCost + int32(CalculatePct(GetTarget()->GetCreateMana(), spellInfo->ManaCostPercentage));
        mana = CalculatePct(mana, aurEff->GetAmount());

        if (mana > 0)
        {
            GetTarget()->CastCustomSpell(SPELL_MAGE_MASTER_OF_ELEMENTS_ENERGIZE, SPELLVALUE_BASE_POINT0, mana, GetTarget(), true, nullptr, aurEff);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_master_of_elements::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_master_of_elements::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

enum SilvermoonPolymorph
{
    NPC_AUROSALIA   = 18744,
};

/// @todo move out of here and rename - not a mage spell
// 32826 - Polymorph (Visual)
class spell_mage_polymorph_cast_visual : public SpellScript
{
    PrepareSpellScript(spell_mage_polymorph_cast_visual);

    static const uint32 PolymorhForms[6];

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        // check if spell ids exist in dbc
        for (uint32 i = 0; i < 6; ++i)
            if (!sSpellMgr->GetSpellInfo(PolymorhForms[i]))
                return false;
        return true;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (Unit* target = GetCaster()->FindNearestCreature(NPC_AUROSALIA, 30.0f))
            if (target->IsCreature())
                target->CastSpell(target, PolymorhForms[urand(0, 5)], true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_mage_polymorph_cast_visual::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

const uint32 spell_mage_polymorph_cast_visual::spell_mage_polymorph_cast_visual::PolymorhForms[6] =
{
    SPELL_MAGE_SQUIRREL_FORM,
    SPELL_MAGE_GIRAFFE_FORM,
    SPELL_MAGE_SERPENT_FORM,
    SPELL_MAGE_DRAGONHAWK_FORM,
    SPELL_MAGE_WORGEN_FORM,
    SPELL_MAGE_SHEEP_FORM
};

// 31687 - Summon Water Elemental
class spell_mage_summon_water_elemental : public SpellScript
{
    PrepareSpellScript(spell_mage_summon_water_elemental)
    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_MAGE_GLYPH_OF_ETERNAL_WATER,
                SPELL_MAGE_SUMMON_WATER_ELEMENTAL_TEMPORARY,
                SPELL_MAGE_SUMMON_WATER_ELEMENTAL_PERMANENT
            });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();

        if (Creature* pet = ObjectAccessor::GetCreature(*caster, caster->GetPetGUID()))
            if (!pet->IsAlive())
                pet->ToTempSummon()->UnSummon();

        // Glyph of Eternal Water
        if (caster->HasAura(SPELL_MAGE_GLYPH_OF_ETERNAL_WATER))
            caster->CastSpell(caster, SPELL_MAGE_SUMMON_WATER_ELEMENTAL_PERMANENT, true);
        else
            caster->CastSpell(caster, SPELL_MAGE_SUMMON_WATER_ELEMENTAL_TEMPORARY, true);

        if (Creature* pet = ObjectAccessor::GetCreature(*caster, caster->GetPetGUID()))
            if (pet->GetCharmInfo() && caster->ToPlayer())
            {
                pet->m_CreatureSpellCooldowns.clear();
                SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(31707);
                pet->GetCharmInfo()->ToggleCreatureAutocast(spellInfo, true);
                pet->GetCharmInfo()->SetSpellAutocast(spellInfo, true);
                caster->ToPlayer()->CharmSpellInitialize();
            }
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_mage_summon_water_elemental::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 33395 - Water Elemental: Freeze
// docs/frost-mage-redesign.md sec 2 ("Water Elemental: Freeze"): "Against targets immune to
// freeze effects, grants the owner 1 Fingers of Frost charge instead of applying the freeze."
// "Autocast: Removed" needed no code or data change here - 33395's pulled AttributesEx (see
// npc.csv's raw_overrides on this row) already carries SPELL_ATTR1_NO_AUTOCAST_AI, so
// SpellInfo::IsAutocastable() is already false and CharmInfo::InitCharmCreateSpells never calls
// ToggleCreatureAutocast for this spell - the pet already can't self-cast it. This script is only
// the immune-target half of the item.
class spell_mage_water_elemental_freeze : public SpellScript
{
    PrepareSpellScript(spell_mage_water_elemental_freeze);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FINGERS_OF_FROST_CHARGES });
    }

    void GrantFingersOfFrostOnImmune()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Effect 1 is the SPELL_AURA_MOD_ROOT ("frozen in place") effect - Effect 0's damage
        // always lands regardless of freeze immunity, matching the live spell description ("Damage
        // caused may interrupt the effect").
        if (!target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_1, caster))
            return;

        Unit* owner = caster->GetOwner();
        if (!owner)
            return;

        owner->CastSpell(owner, SPELL_MAGE_FINGERS_OF_FROST_CHARGES, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_mage_water_elemental_freeze::GrantFingersOfFrostOnImmune);
    }
};

// 74396 - Fingers of Frost
class spell_mage_fingers_of_frost : public AuraScript
{
    PrepareAuraScript(spell_mage_fingers_of_frost);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FINGERS_OF_FROST_AURASTATE_AURA });
    }

    void PrepareProc(ProcEventInfo& eventInfo)
    {
        if (Spell const* spell = eventInfo.GetProcSpell())
        {
            bool isTriggered = spell->IsTriggered();
            bool isCastPhase = (eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST) != 0;
            bool isChanneled = spell->GetSpellInfo()->IsChanneled();
            bool prevent = false;

            if (isTriggered)
                prevent = false;
            else if (isChanneled)
                prevent = true;
            else if (!isCastPhase)
                prevent = true;

            if (prevent)
                PreventDefaultAction();
        }
    }

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_MAGE_FINGERS_OF_FROST_AURASTATE_AURA);
    }

    void Register() override
    {
        DoPrepareProc += AuraProcFn(spell_mage_fingers_of_frost::PrepareProc);
        AfterEffectRemove += AuraEffectRemoveFn(spell_mage_fingers_of_frost::OnRemove, EFFECT_0, SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// -31571 - Arcane Potency
class spell_mage_arcane_potency : public AuraScript
{
    PrepareAuraScript(spell_mage_arcane_potency);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_MAGE_ARCANE_POTENCY_RANK_1,
                SPELL_MAGE_ARCANE_POTENCY_RANK_2
            });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Only proc on Clearcasting or Presence of Mind
        if (spellInfo->SpellIconID != MAGE_ICON_CLEARCASTING && spellInfo->SpellIconID != MAGE_ICON_PRESENCE_OF_MIND)
            return false;

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        uint32 spellId = GetSpellInfo()->GetRank() == 1 ? SPELL_MAGE_ARCANE_POTENCY_RANK_1 : SPELL_MAGE_ARCANE_POTENCY_RANK_2;
        GetTarget()->CastSpell(GetTarget(), spellId, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_arcane_potency::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_arcane_potency::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 11129 - Combustion
class spell_mage_combustion : public AuraScript
{
    PrepareAuraScript(spell_mage_combustion);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_COMBUSTION_PROC });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Do not take charges, add a stack of crit buff
        if (!(eventInfo.GetHitMask() & PROC_HIT_CRITICAL))
        {
            // Applying the stack mutates the actor's aura map while the proc engine iterates
            // it (this hook runs from Aura::GetProcEffectMask); defer it so the insert can't
            // invalidate the live iterator (aura containers are flat_multimaps).
            Unit* actor = eventInfo.GetActor();
            actor->m_Events.AddEventAtOffset([actor]()
            {
                actor->CastSpell(static_cast<Unit*>(nullptr), SPELL_MAGE_COMBUSTION_PROC, true);
            }, 1ms);
            return false;
        }

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_combustion::CheckProc);
    }
};

// -31656 - Empowered Fire
class spell_mage_empowered_fire : public AuraScript
{
    PrepareAuraScript(spell_mage_empowered_fire);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_EMPOWERED_FIRE_PROC });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Only proc on Ignite
        return spellInfo->Id == SPELL_MAGE_IGNITE;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        // Calculate mana restored: 2% of base mana (percent value comes from spell 67545 effect 0)
        uint32 percent = sSpellMgr->GetSpellInfo(SPELL_MAGE_EMPOWERED_FIRE_PROC)->Effects[EFFECT_0].CalcValue();
        int32 mana = int32(CalculatePct(target->GetCreateMana(), percent));
        target->CastCustomSpell(SPELL_MAGE_EMPOWERED_FIRE_PROC, SPELLVALUE_BASE_POINT0, mana, target, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_empowered_fire::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_empowered_fire::HandleProc, EFFECT_0, SPELL_AURA_ADD_FLAT_MODIFIER);
    }
};

// 48108 - Hot Streak, 57761 - Fireball!
class spell_mage_gen_extra_effects : public AuraScript
{
    PrepareAuraScript(spell_mage_gen_extra_effects);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_MAGE_T8_4P_BONUS,
                SPELL_MAGE_T10_2P_BONUS,
                SPELL_MAGE_T10_2P_BONUS_EFFECT
            });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = eventInfo.GetActor();
        // T8 4P bonus: prevent double proc on Arcane Missiles
        if (GetSpellInfo()->Id == SPELL_MAGE_HOT_STREAK_PROC && caster->HasAura(SPELL_MAGE_T8_4P_BONUS))
        {
            SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
            if (spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_MAGE &&
                (spellInfo->SpellFamilyFlags[0] & 0x00000800)) // Arcane Missiles
                return false;
        }
        return true;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = eventInfo.GetActor();
        // T10 2P bonus: apply pushing the limit on proc consumption
        if (caster->HasAura(SPELL_MAGE_T10_2P_BONUS))
            caster->CastSpell(caster, SPELL_MAGE_T10_2P_BONUS_EFFECT, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_gen_extra_effects::CheckProc);
        OnProc += AuraProcFn(spell_mage_gen_extra_effects::HandleProc);
    }
};

// 56372 - Glyph of Ice Block
class spell_mage_glyph_of_ice_block : public AuraScript
{
    PrepareAuraScript(spell_mage_glyph_of_ice_block);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_FROST_NOVA });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        // Reset cooldowns on Frost Nova and all its ranks
        SpellInfo const* frostNovaInfo = sSpellMgr->GetSpellInfo(SPELL_MAGE_FROST_NOVA);
        if (!frostNovaInfo)
            return;

        PlayerSpellMap const& spellMap = player->GetSpellMap();
        for (auto const& itr : spellMap)
        {
            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(itr.first);
            if (!spellInfo)
                continue;

            // Frost Nova spell family flags: 0x00000040
            if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE &&
                (spellInfo->SpellFamilyFlags[0] & 0x00000040))
            {
                player->RemoveSpellCooldown(spellInfo->Id, true);
            }
        }
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_glyph_of_ice_block::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 56374 - Glyph of Icy Veins
class spell_mage_glyph_of_icy_veins : public AuraScript
{
    PrepareAuraScript(spell_mage_glyph_of_icy_veins);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* target = GetTarget();

        // Remove attack speed slows and haste reducting auras
        target->RemoveAurasByType(SPELL_AURA_HASTE_SPELLS);
        target->RemoveAurasByType(SPELL_AURA_MOD_DECREASE_SPEED);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_glyph_of_icy_veins::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 56375 - Glyph of Polymorph
class spell_mage_glyph_of_polymorph : public AuraScript
{
    PrepareAuraScript(spell_mage_glyph_of_polymorph);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* target = eventInfo.GetProcTarget();
        if (!target)
            return;

        // Remove DoTs from target
        target->RemoveAurasByType(SPELL_AURA_PERIODIC_DAMAGE, ObjectGuid::Empty, target->GetAura(32409), true); // SW:D shall not be removed.
        target->RemoveAurasByType(SPELL_AURA_PERIODIC_DAMAGE_PERCENT, ObjectGuid::Empty, nullptr, true);
        target->RemoveAurasByType(SPELL_AURA_PERIODIC_LEECH, ObjectGuid::Empty, nullptr, true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_glyph_of_polymorph::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -44445 - Hot Streak
class spell_mage_hot_streak : public AuraScript
{
    PrepareAuraScript(spell_mage_hot_streak);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_HOT_STREAK_PROC });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        // Non-crit - reset counter
        if (!(eventInfo.GetHitMask() & PROC_EX_CRITICAL_HIT))
        {
            _critStreak = 0;
            return;
        }

        // Crit - increment counter
        ++_critStreak;

        // Two crits in a row - proc Hot Streak if chance succeeds
        if (_critStreak >= 2)
        {
            _critStreak = 0;
            if (roll_chance_i(aurEff->GetAmount()))
                GetTarget()->CastSpell(GetTarget(), SPELL_MAGE_HOT_STREAK_PROC, true, nullptr, aurEff);
        }
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_hot_streak::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

private:
    uint8 _critStreak = 0;
};

// -11185 - Improved Blizzard
class spell_mage_imp_blizzard : public AuraScript
{
    PrepareAuraScript(spell_mage_imp_blizzard);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_MAGE_CHILLED_R1,
                SPELL_MAGE_CHILLED_R2,
                SPELL_MAGE_CHILLED_R3,
                SPELL_MAGE_FINGERS_OF_FROST_AURASTATE_AURA
            });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        uint32 spellId;
        switch (GetSpellInfo()->GetRank())
        {
            case 1: spellId = SPELL_MAGE_CHILLED_R1; break;
            case 2: spellId = SPELL_MAGE_CHILLED_R2; break;
            case 3: spellId = SPELL_MAGE_CHILLED_R3; break;
            default: return;
        }

        Unit* caster = GetTarget();
        if (Unit* target = eventInfo.GetProcTarget())
            caster->CastSpell(target, spellId, true, nullptr, aurEff);

        // Fingers of Frost: Blizzard chill effects can trigger FoF
        if (AuraEffect const* fofTalent = caster->GetAuraEffectOfRankedSpell(SPELL_MAGE_FINGERS_OF_FROST, EFFECT_0))
            if (roll_chance_i(fofTalent->GetAmount()))
                caster->CastSpell(caster, SPELL_MAGE_FINGERS_OF_FROST_AURASTATE_AURA, true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_imp_blizzard::HandleProc, EFFECT_0, SPELL_AURA_OVERRIDE_CLASS_SCRIPTS);
    }
};

// 61062, 37447 - Improved Mana Gems
class spell_mage_imp_mana_gems : public AuraScript
{
    PrepareAuraScript(spell_mage_imp_mana_gems);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_MANA_SURGE });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->CastSpell(GetTarget(), SPELL_MAGE_MANA_SURGE, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_imp_mana_gems::HandleProc, EFFECT_1, SPELL_AURA_OVERRIDE_CLASS_SCRIPTS);
    }
};

// -44404 - Missile Barrage
class spell_mage_missile_barrage : public AuraScript
{
    PrepareAuraScript(spell_mage_missile_barrage);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Arcane Blast - full proc chance (100%)
        // Arcane Blast spell family flags: 0x20000000
        if (spellInfo->SpellFamilyFlags[0] & 0x20000000)
            return true;

        // Other spells - 50% proc chance
        return roll_chance_i(50);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_missile_barrage::CheckProc);
    }
};

// -29441 - Magic Absorption
class spell_mage_magic_absorption : public AuraScript
{
    PrepareAuraScript(spell_mage_magic_absorption);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_MAGIC_ABSORPTION_MANA });
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        return GetTarget()->HasActivePowerType(POWER_MANA);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* target = GetTarget();
        int32 bp = CalculatePct(int32(target->GetMaxPower(POWER_MANA)), aurEff->GetAmount());
        target->CastCustomSpell(SPELL_MAGE_MAGIC_ABSORPTION_MANA, SPELLVALUE_BASE_POINT0, bp, target, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_magic_absorption::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_mage_magic_absorption::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -31641 - Blazing Speed
class spell_mage_blazing_speed : public AuraScript
{
    PrepareAuraScript(spell_mage_blazing_speed);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_BLAZING_SPEED });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        if (Unit* target = eventInfo.GetActionTarget())
            target->CastSpell(target, SPELL_MAGE_BLAZING_SPEED, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_mage_blazing_speed::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// -5143 - Arcane Missiles
class spell_mage_arcane_missiles : public AuraScript
{
    PrepareAuraScript(spell_mage_arcane_missiles);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_T10_2P_BONUS, SPELL_MAGE_T10_2P_BONUS_EFFECT });
    }

    void OnRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (target->HasAura(SPELL_MAGE_T10_2P_BONUS) && _canProcT10)
            target->CastSpell(target, SPELL_MAGE_T10_2P_BONUS_EFFECT, true, nullptr, aurEff);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_mage_arcane_missiles::OnRemove, EFFECT_1, SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }

public:
    void AllowT10Proc() { _canProcT10 = true; }

private:
    bool _canProcT10 = false;
};

// -31661 - Dragon's Breath
class spell_mage_dragon_breath : public AuraScript
{
    PrepareAuraScript(spell_mage_dragon_breath);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Don't proc with Living Bomb explosion
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (spellInfo && spellInfo->SpellIconID == MAGE_ICON_LIVING_BOMB && spellInfo->SpellFamilyName == SPELLFAMILY_MAGE)
            return false;

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_dragon_breath::CheckProc);
    }
};

// -44614 - Frostfire Bolt
class spell_mage_frostfire_bolt : public AuraScript
{
    PrepareAuraScript(spell_mage_frostfire_bolt);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_PERMAFROST_AURA });
    }

    void ApplyPermafrost(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->CastSpell(GetTarget(), SPELL_MAGE_PERMAFROST_AURA, true, nullptr, aurEff);
    }

    void RemovePermafrost(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_MAGE_PERMAFROST_AURA);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_mage_frostfire_bolt::ApplyPermafrost, EFFECT_0, SPELL_AURA_MOD_DECREASE_SPEED, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        AfterEffectRemove += AuraEffectRemoveFn(spell_mage_frostfire_bolt::RemovePermafrost, EFFECT_0, SPELL_AURA_MOD_DECREASE_SPEED, AURA_EFFECT_HANDLE_REAL);
    }
};

// 45438 - Ice Block
class spell_mage_ice_block : public SpellScript
{
    PrepareSpellScript(spell_mage_ice_block);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return spellInfo->ExcludeCasterAuraSpell && ValidateSpellInfo({ static_cast<uint32>(spellInfo->ExcludeCasterAuraSpell) });
    }

    void TriggerHypothermia()
    {
        GetCaster()->CastSpell(GetCaster(), GetSpellInfo()->ExcludeCasterAuraSpell, true);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_mage_ice_block::TriggerHypothermia);
    }
};

// 12536 - Clearcasting
class spell_mage_clearcasting : public AuraScript
{
    PrepareAuraScript(spell_mage_clearcasting);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return true;

        // Missile Barrage has priority over Clearcasting for Arcane Missiles
        if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE && (spellInfo->SpellFamilyFlags[0] & 0x800))
            if (GetTarget()->HasAura(SPELL_MAGE_MISSILE_BARRAGE_PROC))
                return false;

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_clearcasting::CheckProc);
    }
};

// 44401 - Missile Barrage (proc buff)
class spell_mage_missile_barrage_proc : public AuraScript
{
    PrepareAuraScript(spell_mage_missile_barrage_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MAGE_T10_2P_BONUS, SPELL_MAGE_T8_4P_BONUS, SPELL_MAGE_ARCANE_MISSILES_R1 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = eventInfo.GetActor();

        // Prevent double proc for Arcane Missiles
        if (caster == eventInfo.GetActionTarget())
            return false;

        // T8 4P bonus: chance to not consume the proc
        if (AuraEffect const* aurEff = caster->GetAuraEffect(SPELL_MAGE_T8_4P_BONUS, EFFECT_0))
            if (roll_chance_i(aurEff->GetAmount()))
                return false;

        return true;
    }

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetTarget();
        // T10 2P bonus: signal Arcane Missiles to proc the bonus when it ends
        if (caster->HasAura(SPELL_MAGE_T10_2P_BONUS))
        {
            if (Aura* aura = caster->GetAuraOfRankedSpell(SPELL_MAGE_ARCANE_MISSILES_R1))
            {
                if (spell_mage_arcane_missiles* script = dynamic_cast<spell_mage_arcane_missiles*>(aura->GetScriptByName("spell_mage_arcane_missiles")))
                    script->AllowT10Proc();
            }
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_mage_missile_barrage_proc::CheckProc);
        AfterEffectRemove += AuraEffectRemoveFn(spell_mage_missile_barrage_proc::OnRemove, EFFECT_0, SPELL_AURA_ADD_FLAT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_mage_spell_scripts()
{
    RegisterSpellScript(spell_mage_arcane_blast);
    RegisterSpellScript(spell_mage_arcane_missiles);
    RegisterSpellScript(spell_mage_arcane_potency);
    RegisterSpellScript(spell_mage_blazing_speed);
    RegisterSpellScript(spell_mage_burning_determination);
    RegisterSpellScript(spell_mage_molten_armor);
    RegisterSpellScript(spell_mage_mirror_image);
    RegisterSpellScript(spell_mage_burnout);
    RegisterSpellScript(spell_mage_burnout_trigger);
    RegisterSpellScript(spell_mage_pet_scaling);
    RegisterSpellScript(spell_mage_brain_freeze);
    RegisterSpellScript(spell_mage_combustion);
    RegisterSpellScript(spell_mage_glyph_of_eternal_water);
    RegisterSpellScript(spell_mage_combustion_proc);
    RegisterSpellScript(spell_mage_dragon_breath);
    RegisterSpellScript(spell_mage_empowered_fire);
    RegisterSpellScript(spell_mage_gen_extra_effects);
    RegisterSpellScript(spell_mage_frostfire_bolt);
    RegisterSpellScript(spell_mage_glyph_of_ice_block);
    RegisterSpellScript(spell_mage_glyph_of_icy_veins);
    RegisterSpellScript(spell_mage_glyph_of_polymorph);
    RegisterSpellScript(spell_mage_hot_streak);
    RegisterSpellScript(spell_mage_ice_barrier);
    RegisterSpellScript(spell_mage_ice_barrier_aura);
    RegisterSpellScript(spell_mage_ice_block);
    RegisterSpellScript(spell_mage_imp_blizzard);
    RegisterSpellScript(spell_mage_imp_mana_gems);
    RegisterSpellScript(spell_mage_clearcasting);
    RegisterSpellScript(spell_mage_missile_barrage);
    RegisterSpellScript(spell_mage_missile_barrage_proc);
    RegisterSpellScript(spell_mage_blast_wave);
    RegisterSpellScript(spell_mage_cold_snap);
    RegisterSpellScript(spell_mage_fire_frost_ward);
    RegisterSpellScript(spell_mage_focus_magic);
    RegisterSpellScript(spell_mage_ignite);
    RegisterSpellScript(spell_mage_living_bomb);
    RegisterSpellScript(spell_mage_mana_shield);
    RegisterSpellScript(spell_mage_master_of_elements);
    RegisterSpellScript(spell_mage_polymorph_cast_visual);
    RegisterSpellScript(spell_mage_summon_water_elemental);
    RegisterSpellScript(spell_mage_water_elemental_freeze);
    RegisterSpellScript(spell_mage_fingers_of_frost);
    RegisterSpellScript(spell_mage_magic_absorption);

    // Frost Mage rework (docs/frost-mage-redesign.md) - see the block above spell_mage_arcane_blast.
    RegisterSpellScript(spell_mage_frostbolt_icicles);
    RegisterSpellScript(spell_mage_frostfire_bolt_icicles);
    RegisterSpellScript(spell_mage_blizzard_icicles);
    RegisterSpellScript(spell_mage_glacial_spike);
    RegisterSpellScript(spell_mage_glacial_spike_impact);
    RegisterSpellScript(spell_mage_flurry);
    RegisterSpellScript(spell_mage_biting_cold);
    RegisterSpellScript(spell_mage_frostbite);
    RegisterSpellScript(spell_mage_refreshment);
    RegisterSpellScript(spell_mage_frozen_orb);
    RegisterSpellScript(spell_mage_frozen_orb_pulse);
    RegisterSpellScript(spell_mage_chilled_to_the_bone);
    RegisterSpellScript(spell_mage_permafrost);
    RegisterSpellScript(spell_mage_ice_lance);
    RegisterSpellScript(spell_mage_chilled);
    RegisterSpellScript(spell_mage_frozen_core);
    RegisterSpellScript(spell_mage_enduring_winter);
    RegisterCreatureAI(npc_mage_frozen_orb);
    new FrostMageIcicleCombatReset();
}
