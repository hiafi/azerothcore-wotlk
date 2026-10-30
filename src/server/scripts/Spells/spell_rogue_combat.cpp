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
 * Rogue rework - Combat spell scripts (rogue-rework S3a; docs/reworks/rogue-combat-rework.md). The PlayerScript /
 * UnitScript hooks (dispatcher, Blade Flurry copies, Blade Twisting stacks, Prey on the Weak, Riposte's dodge) live in
 * rogue_hooks.cpp and RogueMechanics.cpp; this file holds the spell and aura scripts.
 */

#include "AreaDefines.h"
#include "Containers.h"
#include "LeapMechanics.h" // Custom: warrior-rework W0b
#include "MotionMaster.h"
#include "MovementTypedefs.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <list>

namespace
{
    // Killing Spree's teleport (stock, reused unedited: family 8, no bits, 100 yd range from SpellInfoCorrections).
    constexpr uint32 SPELL_KILLING_SPREE_TELEPORT = 57840;
    // Kologarn's arena (Ulduar): Killing Spree is refused there (stock rule, kept).
    constexpr float KOLOGARN_ARENA_X = 1766.936f;
    constexpr float KOLOGARN_ARENA_Y = -24.748f;
    constexpr float KOLOGARN_ARENA_RADIUS_YD = 50.0f;

    Player* GetRoguePlayer(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }

    // The caster of a spell script when it is a player and the cast is the player's own (not a script cast). Every
    // S3 hit hook below uses it: 1752 / 2098 / 1766 have NPC users and the strikes are also cast by scripts.
    Player* GetOwnCastRogue(SpellScript& script)
    {
        Unit* caster = script.GetCaster();
        if (!caster || !caster->IsPlayer() || script.GetSpell()->IsTriggered())
            return nullptr;

        return caster->ToPlayer();
    }
}

// 203958 - Pistol Shot. BeforeCast latches whether Opportunity was up (its companion makes the shot free and +50%, both
// read at prepare / damage time); the hit resolves Primed Powder, Quick Draw and Surprise Attacks' shots; the stack is
// spent in AfterCast, hit or not (R12): the cast was already free, and a dodged empowered shot must not leave a second
// free one.
class spell_rog_pistol_shot : public SpellScript
{
    PrepareSpellScript(spell_rog_pistol_shot);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_OPPORTUNITY_BUFF });
    }

    void HandleBeforeCast()
    {
        Unit* caster = GetCaster();
        if (caster && caster->IsPlayer() && caster->HasAura(RogueData::SPELL_OPPORTUNITY_BUFF))
            _empowered = true;
    }

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnPistolShotHit(rogue, target, _empowered);
    }

    void HandleAfterCast()
    {
        if (!_empowered)
            return;

        Player* rogue = GetOwnCastRogue(*this);
        if (!rogue)
            return;

        if (Aura* opportunity = rogue->GetAura(RogueData::SPELL_OPPORTUNITY_BUFF))
            opportunity->ModStackAmount(-1);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_rog_pistol_shot::HandleBeforeCast);
        AfterHit += SpellHitFn(spell_rog_pistol_shot::HandleAfterHit);
        AfterCast += SpellCastFn(spell_rog_pistol_shot::HandleAfterCast);
    }

    bool _empowered = false;
};

// 203988 - Surprise Attacks' extra shot: x (100 + Opportunity's percent) / 100 when the Pistol Shot that fired it was
// empowered (the stamp B1 sets when it schedules the shots).
class spell_rog_pistol_shot_extra : public SpellScript
{
    PrepareSpellScript(spell_rog_pistol_shot_extra);

    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue || !Rogue::IsSurpriseShotEmpowered(rogue))
            return;

        SetHitDamage(int32(int64(GetHitDamage()) * (100 + RogueData::OPPORTUNITY_EMPOWER_PCT) / 100));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_rog_pistol_shot_extra::HandleDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 203959 - Between the Eyes: the hit spends Primed Powder (its damage mod already applied) and Blade Rush's
// empowerment; Hair Trigger rolls in the dispatcher's spent-clause event.
class spell_rog_between_the_eyes : public SpellScript
{
    PrepareSpellScript(spell_rog_between_the_eyes);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_PRIMED_POWDER });
    }

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        if (!rogue)
            return;

        rogue->RemoveAurasDueToSpell(RogueData::SPELL_PRIMED_POWDER);
        Rogue::ConsumeBladeRush(rogue);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_between_the_eyes::HandleAfterHit);
    }
};

// 1752 - Sinister Strike (Combat half; S1's Blindside script is the other binding): second strike, Opportunity,
// Surprise Attacks' roll.
class spell_rog_sinister_strike_combat : public SpellScript
{
    PrepareSpellScript(spell_rog_sinister_strike_combat);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnSinisterStrikeHit(rogue, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_sinister_strike_combat::HandleAfterHit);
    }
};

// 2098 - Eviscerate (Combat half; S2's script is the other binding): Opportunity with the marker, Blade Rush's
// empowerment spent. Effect 1 targets the rogue, so AfterHit also runs for the caster: only the enemy hit counts.
class spell_rog_eviscerate_combat : public SpellScript
{
    PrepareSpellScript(spell_rog_eviscerate_combat);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target || target == rogue)
            return;

        Rogue::OnEviscerateCombatHit(rogue);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_eviscerate_combat::HandleAfterHit);
    }
};

// 14251 - Riposte: Opportunity on every hit, Improved Riposte's capstone cleave.
class spell_rog_riposte : public SpellScript
{
    PrepareSpellScript(spell_rog_riposte);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnRiposteHit(rogue, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_riposte::HandleAfterHit);
    }
};

// 13877 - Blade Flurry (rework). The copies live in the damage hooks (RogueUnitScript); the cast only resolves Deft
// Maneuvers. The NPC ids 33735 / 51211 / 65956 keep the stock spell_rog_blade_flurry.
class spell_rog_blade_flurry_rework : public SpellScript
{
    PrepareSpellScript(spell_rog_blade_flurry_rework);

    void HandleAfterCast()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue)
            return;

        Rogue::OnBladeFlurryCast(rogue);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_rog_blade_flurry_rework::HandleAfterCast);
    }
};

// 203992 - Deft Maneuvers' strike, centred on the rogue: every enemy already fighting the rogue takes it (R13: no
// target cap), never a totem. The weapon percent is the cast's base points (Rogue::OnBladeFlurryCast).
class spell_rog_deft_maneuvers_strike : public SpellScript
{
    PrepareSpellScript(spell_rog_deft_maneuvers_strike);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        targets.remove_if([caster](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || unit->IsTotem() || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(
            spell_rog_deft_maneuvers_strike::FilterTargets, EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// 203980 - Blade Rush: the charge is skipped when the target is already in melee range (the strike still lands at
// cast); the area strike takes the target and the enemies already fighting the rogue; the empowerment buff follows
// the cast.
class spell_rog_blade_rush : public SpellScript
{
    PrepareSpellScript(spell_rog_blade_rush);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_BLADE_RUSH_BUFF });
    }

    void HandleCharge(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !caster->IsPlayer() || !target)
            return;

        if (caster->IsWithinMeleeRange(target))
            PreventHitDefaultEffect(effIndex);
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        Unit* primary = GetExplTargetUnit();
        targets.remove_if([caster, primary](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || (unit != primary && !unit->IsInCombatWith(caster));
        });
    }

    void HandleAfterCast()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue)
            return;

        rogue->CastSpell(rogue, RogueData::SPELL_BLADE_RUSH_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rog_blade_rush::HandleCharge, EFFECT_0, SPELL_EFFECT_CHARGE);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_rog_blade_rush::FilterTargets, EFFECT_1,
            TARGET_UNIT_DEST_AREA_ENEMY);
        AfterCast += SpellCastFn(spell_rog_blade_rush::HandleAfterCast);
    }
};

// 203963 - Grappling Hook: a DUMMY on the ground point and a flat MoveJump (P0c shape). The core refuses a rooted
// caster only for CHARGE / JUMP effects, so the refusal is ours.
class spell_rog_grappling_hook : public SpellScript
{
    PrepareSpellScript(spell_rog_grappling_hook);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster && caster->IsPlayer() && caster->HasUnitState(UNIT_STATE_ROOT))
            return SPELL_FAILED_ROOTED;

        // Custom: warrior-rework W0b (D10) - the Heroic Leap rule: a point with no ground to stand on (a wall face,
        // open air, a too-steep slope) refuses. No destination keeps the old behaviour.
        WorldLocation const* dest = GetExplTargetDest();
        if (dest && !Leap::IsLandablePoint(caster, dest->GetPositionX(), dest->GetPositionY(), dest->GetPositionZ()))
            return SPELL_FAILED_NOPATH;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        WorldLocation const* dest = GetHitDest();
        if (!rogue || !dest)
            return;

        float const speedZ = float(std::sqrt(2.0 * Movement::gravity * double(RogueData::GRAPPLE_APEX_YD)));

        rogue->SetCanTeleport(true);
        sScriptMgr->AnticheatSetUnderACKmount(rogue);
        rogue->GetMotionMaster()->MoveJump(dest->GetPositionX(), dest->GetPositionY(), dest->GetPositionZ(),
            RogueData::GRAPPLE_SPEED_XY, speedZ);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_rog_grappling_hook::CheckCast);
        OnEffectHit += SpellEffectFn(spell_rog_grappling_hook::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 203969 - En Garde's aura: the damage-taken reduction is -4% per combo point spent (the row's per-point amount, read
// here already included); Coup de Grace's capstone multiplies it by 1 + Mastery. Fixed at cast: a recalculation
// (stack change) would drop the per-point part, which is not recomputed.
class spell_rog_en_garde : public AuraScript
{
    PrepareAuraScript(spell_rog_en_garde);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue || !rogue->HasAura(RogueData::SPELL_COUP_DE_GRACE_203972))
            return;

        float const mastery = std::max(0.0f, rogue->GetMasteryPercentage());
        amount = int32(std::lround(float(amount) * (1.0f + mastery / 100.0f)));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_en_garde::CalculateAmount, EFFECT_1,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// 203972 - Coup de Grace rank 3: Mastery adds into the damage bonus. Mastery is not an aura amount, so a 1 s poll
// moves effect 0 when it changes (the Vile Poisons precedent); the modifier is only rewritten when its value moved.
class spell_rog_coup_de_grace_mastery : public AuraScript
{
    PrepareAuraScript(spell_rog_coup_de_grace_mastery);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Player* rogue = GetRoguePlayer(GetTarget());
        if (!rogue)
            return;

        AuraEffect* bonus = aurEff->GetBase()->GetEffect(EFFECT_0);
        if (!bonus)
            return;

        int32 const mastery = int32(std::lround(std::max(0.0f, rogue->GetMasteryPercentage())));
        int32 const wanted = bonus->GetSpellInfo()->Effects[EFFECT_0].CalcValue() + mastery;
        if (bonus->GetAmount() != wanted)
            bonus->ChangeAmount(wanted);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_coup_de_grace_mastery::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 51690 - Killing Spree (rework, a fork of the stock pair): a finisher. The strikes are 1 + points: the aura runs
// points x 500 ms (set when it applies, the points still held) and ticks at apply. It hops between the enemies
// already fighting the rogue within the hop range (a lone enemy every time), no +20% damage aura any more, and Blade
// Rush's empowerment ends with the spree.
class spell_rog_killing_spree_rework_aura : public AuraScript
{
    PrepareAuraScript(spell_rog_killing_spree_rework_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_KILLING_SPREE_TELEPORT, RogueData::SPELL_KILLING_SPREE_MAIN });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* rogue = GetRoguePlayer(GetTarget());
        if (!rogue)
            return;

        int32 const points = int32(rogue->GetComboPoints());
        if (points <= 0)
            return;

        int32 const duration = points * RogueData::KILLING_SPREE_STRIKE_INTERVAL_MS;
        GetAura()->SetMaxDuration(duration);
        GetAura()->SetDuration(duration);
    }

    void HandleEffectPeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* rogue = GetRoguePlayer(GetTarget());
        if (!rogue)
            return;

        while (!_targets.empty())
        {
            ObjectGuid const guid = Acore::Containers::SelectRandomContainerElement(_targets);
            Unit* target = ObjectAccessor::GetUnit(*rogue, guid);
            // The unit may be gone, dead, or have gone stealthed / invisible since the cast.
            if (!target || !rogue->IsValidAttackTarget(target) || target->HasStealthAura() ||
                target->HasInvisibilityAura())
            {
                _targets.remove(guid);
                continue;
            }

            rogue->CastSpell(target, SPELL_KILLING_SPREE_TELEPORT, true);

            // Ensure the fast coordinate switch: do not wait for the client's teleport-ack opcode.
            WorldLocation const& dest = rogue->GetTeleportDest();
            rogue->UpdatePosition(dest, true);

            rogue->CastSpell(target, RogueData::SPELL_KILLING_SPREE_MAIN,
                TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_DONT_REPORT_CAST_ERROR));
            break;
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* rogue = GetRoguePlayer(GetTarget()))
            Rogue::ConsumeBladeRush(rogue);
    }

public:
    void AddTarget(Unit* target)
    {
        _targets.push_back(target->GetGUID());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_rog_killing_spree_rework_aura::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_killing_spree_rework_aura::HandleEffectPeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_rog_killing_spree_rework_aura::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

private:
    GuidList _targets;
};

class spell_rog_killing_spree_rework : public SpellScript
{
    PrepareSpellScript(spell_rog_killing_spree_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_KILLING_SPREE });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        // Kologarn's arena: Killing Spree should not work there.
        if (caster && caster->IsPlayer() && caster->GetMapId() == MAP_ULDUAR &&
            caster->GetDistance2d(KOLOGARN_ARENA_X, KOLOGARN_ARENA_Y) < KOLOGARN_ARENA_RADIUS_YD)
            return SPELL_FAILED_CANT_DO_THAT_RIGHT_NOW;

        return SPELL_CAST_OK;
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        // Only enemies already fighting the rogue within the hop range, awake and visible. The range counts both
        // object sizes (combat reach), so large bosses stay valid while the rogue stands in their melee range.
        targets.remove_if([caster](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !unit->IsAlive() || !unit->IsInCombatWith(caster) ||
                !caster->IsValidAttackTarget(unit) || unit->HasStealthAura() || unit->HasInvisibilityAura() ||
                !caster->IsWithinDistInMap(unit, RogueData::KILLING_SPREE_HOP_RANGE_YD);
        });

        if (targets.empty() || caster->GetVehicleBase() || caster->HasUnitState(UNIT_STATE_ROOT))
            FinishCast(SPELL_FAILED_OUT_OF_RANGE);
        else
        {
            // Added attribute not breaking stealth, removes auras here
            caster->RemoveAurasWithInterruptFlags(AURA_INTERRUPT_FLAG_CAST);
            caster->RemoveAurasWithInterruptFlags(AURA_INTERRUPT_FLAG_SPELL_ATTACK);
        }
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !caster->IsPlayer() || !target)
            return;

        if (Aura* aura = caster->GetAura(RogueData::SPELL_KILLING_SPREE))
            if (auto* script = dynamic_cast<spell_rog_killing_spree_rework_aura*>(
                aura->GetScriptByName("spell_rog_killing_spree_rework")))
                script->AddTarget(target);

        // Doc section 5: the cast rolls poisons once, as any finisher cast does, against the first enemy it chose.
        // Its own procs are suppressed (stock AttributesEx3 0x10000), so the roll is made here; the strikes are
        // triggered hits and roll nothing.
        if (!_poisonsRolled)
        {
            _poisonsRolled = true;
            Rogue::RollCastPoisons(caster->ToPlayer(), target, GetSpell());
        }
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_rog_killing_spree_rework::CheckCast);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_rog_killing_spree_rework::FilterTargets,
            EFFECT_1, TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_rog_killing_spree_rework::HandleDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
    }

private:
    bool _poisonsRolled = false;
};

// -13960 - Hack and Slash: the proc row's check rolls the chance (C++: Proc Chance, weapon speed on autos, once per
// cast on abilities) and the proc casts the strikes.
class spell_rog_hack_and_slash : public AuraScript
{
    PrepareAuraScript(spell_rog_hack_and_slash);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetRoguePlayer(GetTarget());
        return owner && Rogue::RollHackAndSlash(owner, eventInfo);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* owner = GetRoguePlayer(GetTarget());
        Unit* target = eventInfo.GetActionTarget();
        if (!owner || !target)
            return;

        Rogue::CastHackAndSlash(owner, target);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_hack_and_slash::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_rog_hack_and_slash::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 1766 - Kick: Improved Kick's capstone needs to know whether the kick really interrupted a cast. The interrupt effect
// runs in the launch phase, before any hit hook, so the effect hook (which runs ahead of the default handler) records
// the target's interruptible spells with the core's own conditions, and AfterHit checks which are gone (R5).
class spell_rog_kick_combat : public SpellScript
{
    PrepareSpellScript(spell_rog_kick_combat);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_IMPROVED_KICK_13867 });
    }

    void RecordInterruptible(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target || !target->IsAlive() || !rogue->HasAura(RogueData::SPELL_IMPROVED_KICK_13867))
            return;

        // The conditions of Spell::EffectInterruptCast.
        for (uint32 type : { uint32(CURRENT_GENERIC_SPELL), uint32(CURRENT_CHANNELED_SPELL) })
        {
            Spell* spell = target->GetCurrentSpell(type);
            if (!spell)
                continue;

            SpellInfo const* current = spell->GetSpellInfo();
            bool const running = spell->getState() == SPELL_STATE_CASTING ||
                (spell->getState() == SPELL_STATE_PREPARING && spell->GetCastTime() > 0);
            bool const interruptible = type == CURRENT_GENERIC_SPELL ?
                (current->InterruptFlags & SPELL_INTERRUPT_FLAG_INTERRUPT) != 0 :
                (current->ChannelInterruptFlags & CHANNEL_INTERRUPT_FLAG_INTERRUPT) != 0;
            if (running && interruptible && current->PreventionType == SPELL_PREVENTION_TYPE_SILENCE)
                _recorded[type == CURRENT_GENERIC_SPELL ? 0 : 1] = current->Id;
        }
    }

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target || (!_recorded[0] && !_recorded[1]) ||
            !rogue->HasAura(RogueData::SPELL_IMPROVED_KICK_13867))
            return;

        bool interrupted = false;
        for (uint32 index : { 0u, 1u })
        {
            if (!_recorded[index])
                continue;

            Spell* spell = target->GetCurrentSpell(index == 0 ? uint32(CURRENT_GENERIC_SPELL) :
                uint32(CURRENT_CHANNELED_SPELL));
            if (!spell || spell->GetSpellInfo()->Id != _recorded[index])
                interrupted = true;
        }

        if (interrupted)
            Rogue::OnKickInterrupt(rogue);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rog_kick_combat::RecordInterruptible, EFFECT_0,
            SPELL_EFFECT_INTERRUPT_CAST);
        AfterHit += SpellHitFn(spell_rog_kick_combat::HandleAfterHit);
    }

    uint32 _recorded[2] = { 0, 0 };
};

// 204000 - Improved Sprint's helper (linked to Sprint): the root-duration cut and the speed floor exist only with the
// capstone.
class spell_rog_improved_sprint_helper : public AuraScript
{
    PrepareAuraScript(spell_rog_improved_sprint_helper);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* rogue = GetRoguePlayer(GetUnitOwner());
        if (!rogue || !rogue->HasAura(RogueData::SPELL_IMPROVED_SPRINT_13875))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_improved_sprint_helper::CalculateAmount, EFFECT_0,
            SPELL_AURA_MECHANIC_DURATION_MOD);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_improved_sprint_helper::CalculateAmount, EFFECT_1,
            SPELL_AURA_MOD_MINIMUM_SPEED);
    }
};

// 204001 - Endurance's helper (linked to Evasion): Evasion's magic damage taken reduction by the talent's rank.
class spell_rog_endurance_helper : public AuraScript
{
    PrepareAuraScript(spell_rog_endurance_helper);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* rogue = GetRoguePlayer(GetUnitOwner());
        amount = rogue ? -Rogue::GetRankAmount(rogue, { RogueData::SPELL_ENDURANCE, RogueData::SPELL_ENDURANCE_13872 },
            EFFECT_2) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_endurance_helper::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// 204002 - Improved Feint's helper (linked to Feint): the extra damage taken reduction only when Enforcer Stance is
// up as Feint is cast. Fixed at apply.
class spell_rog_improved_feint_helper : public AuraScript
{
    PrepareAuraScript(spell_rog_improved_feint_helper);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Player* rogue = GetRoguePlayer(GetUnitOwner());
        amount = rogue && rogue->HasAura(RogueData::SPELL_ENFORCER_STANCE) ?
            -Rogue::GetRankAmount(rogue, { RogueData::SPELL_IMPROVED_FEINT }, EFFECT_0) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_improved_feint_helper::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

void AddSC_rogue_combat_spell_scripts()
{
    RegisterSpellScript(spell_rog_pistol_shot);
    RegisterSpellScript(spell_rog_pistol_shot_extra);
    RegisterSpellScript(spell_rog_between_the_eyes);
    RegisterSpellScript(spell_rog_sinister_strike_combat);
    RegisterSpellScript(spell_rog_eviscerate_combat);
    RegisterSpellScript(spell_rog_riposte);
    RegisterSpellScript(spell_rog_blade_flurry_rework);
    RegisterSpellScript(spell_rog_deft_maneuvers_strike);
    RegisterSpellScript(spell_rog_blade_rush);
    RegisterSpellScript(spell_rog_grappling_hook);
    RegisterSpellScript(spell_rog_en_garde);
    RegisterSpellScript(spell_rog_coup_de_grace_mastery);
    RegisterSpellAndAuraScriptPair(spell_rog_killing_spree_rework, spell_rog_killing_spree_rework_aura);
    RegisterSpellScript(spell_rog_hack_and_slash);
    RegisterSpellScript(spell_rog_kick_combat);
    RegisterSpellScript(spell_rog_improved_sprint_helper);
    RegisterSpellScript(spell_rog_endurance_helper);
    RegisterSpellScript(spell_rog_improved_feint_helper);
}
