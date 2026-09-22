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
 * Priest baseline rework (docs/reworks/priest-new-spells.md) - the 6 genuinely-new shared spells
 * from this pass (Angelic Feather, Power Word: Barrier, Divine Star, Halo, Leap of Faith, Void
 * Eruption). Kept in a separate file from the existing spell_priest.cpp (already 1400+ lines
 * before this) rather than growing that file further. Scriptnames prefixed "spell_pri_", same
 * convention as spell_priest.cpp. Power Word: Barrier needs no script at all (fully data-driven -
 * see its own spell() definition in apps/dbc-tools/source/classes/priest/priest_spells.py) so it
 * has no class here.
 *
 * Divine Star and Halo both use an explicit-single-unit-target "ally heals / enemy damages" pulse
 * spell (divine_star_pulse_200134 / halo_pulse_200136) cast individually at each newly-found
 * nearby unit, rather than a native AoE dest-area query - this sidesteps the "native AoE re-hits
 * everyone already inside the radius every tick" problem entirely, at the cost of doing the target
 * search by hand here instead of trusting SpellObjectAreaTargetSelect. See each class's own
 * comment for specifics.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Containers.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "EventMap.h"
#include "GameObject.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include <cmath>

enum PriestNewSpells
{
    SPELL_PRIEST_ANGELIC_FEATHER               = 200130,
    SPELL_PRIEST_ANGELIC_FEATHER_SPEED         = 200131,
    SPELL_PRIEST_DIVINE_STAR                   = 200133,
    SPELL_PRIEST_DIVINE_STAR_PULSE             = 200134,
    SPELL_PRIEST_HALO                          = 200135,
    SPELL_PRIEST_HALO_PULSE                    = 200136,
    SPELL_PRIEST_LEAP_OF_FAITH                 = 200137,
    SPELL_PRIEST_LEAP_OF_FAITH_JUMP            = 200138,
    SPELL_PRIEST_VOID_ERUPTION                 = 200139,
    SPELL_PRIEST_VOIDFORM                      = 200140,

    // Real stock spells this file's scripts need by number.
    SPELL_PRIEST_SHADOWFORM                    = 15473,
    SPELL_PRIEST_SHADOW_WORD_PAIN              = 589,

    // Discipline rework - Guiding Star (5,3) bolts an absorb onto Divine Star's healing
    // (.agents/plans/priest-rework/priest-rework.DISC.md). Rank *spell* ids, not talent_dbc ids.
    SPELL_PRIEST_GUIDING_STAR_R1               = 200156,
    SPELL_PRIEST_GUIDING_STAR_R2               = 200157,
    SPELL_PRIEST_GUIDING_STAR_ABSORB           = 200158
};

enum PriestNewCreatures
{
    // creature_template entry, hand-written pending SQL (see that migration's own comment).
    NPC_PRIEST_DIVINE_STAR = 300100
};

enum PriestNewGameObjects
{
    // gameobject_template entry, hand-written pending SQL (see that migration's own comment).
    GO_PRIEST_ANGELIC_FEATHER = 300101
};

/*
 * Angelic Feather (docs/reworks/priest-new-spells.md): "Places a feather at the target location,
 * granting the first ally to walk through it 40% increased movement speed for 5 sec. Only 3
 * feathers can be placed at one time." The feather itself is a native GAMEOBJECT_TYPE_TRAP GO
 * (gameobject_template.trap.spellId = SPELL_PRIEST_ANGELIC_FEATHER_SPEED, autoCloseTime=-1 so it
 * takes GameObject.cpp's "environmental trap" branch - fires for any nearby player, not just
 * hostile ones - and the buff spell's own TARGET_UNIT_TARGET_ALLY check is what actually restricts
 * the benefit to allies) - no C++ needed for the placement or the proximity trigger itself, both
 * are native engine behavior. This script only enforces "only 3 at once".
 */
class spell_pri_angelic_feather : public SpellScript
{
    PrepareSpellScript(spell_pri_angelic_feather);

    void DespawnOldestIfAtCap()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        std::list<GameObject*> feathers;
        caster->GetGameObjectListWithEntryInGrid(feathers, GO_PRIEST_ANGELIC_FEATHER, 100.0f);
        feathers.remove_if([caster](GameObject const* go) { return go->GetOwnerGUID() != caster->GetGUID(); });
        if (feathers.size() < 3)
            return;

        // Summoned (not DB-spawned) GOs have no meaningful SpawnId - GUID counters are assigned
        // sequentially at creation, so the lowest one here is simply whichever feather is oldest.
        feathers.sort([](GameObject const* a, GameObject const* b) { return a->GetGUID().GetCounter() < b->GetGUID().GetCounter(); });
        feathers.front()->Delete();
    }

    void Register() override
    {
        // No unit target at all (dest-only ground-target spell), so a per-target hook like
        // BeforeHit would never fire - this needs a cast-level hook instead, run before the
        // SUMMON_OBJECT_SLOT1 effect actually places the new feather.
        BeforeCast += SpellCastFn(spell_pri_angelic_feather::DespawnOldestIfAtCap);
    }
};

/*
 * Divine Star (docs/reworks/priest-new-spells.md): "Throw a Divine Star forward 27 yds, healing
 * allies in its path... and dealing... Holy damage to enemies. After reaching its destination, the
 * Divine Star returns to you, healing allies and damaging enemies in its path again. Healing
 * reduced beyond 6 targets." Modeled on Frost Mage's Frozen Orb (spell_mage.cpp's
 * npc_mage_frozen_orb/spell_mage_frozen_orb) - see that file's own header comment on the pattern.
 * Differs from Frozen Orb in needing two separate legs (out, then back), each hitting a target at
 * most once - tracked here via a per-leg GUID set, cleared when the return leg starts.
 */
namespace
{
    constexpr uint32 POINT_DIVINE_STAR_END = 1;
    constexpr uint32 POINT_DIVINE_STAR_RETURN = 2;
    constexpr uint32 EVENT_DIVINE_STAR_PULSE = 1;
    constexpr uint32 EVENT_DIVINE_STAR_RETURN = 2;
    constexpr uint32 EVENT_DIVINE_STAR_DESPAWN = 3;
    constexpr float DIVINE_STAR_TRAVEL_DISTANCE = 27.0f;
    constexpr float DIVINE_STAR_SPEED = 20.0f;          // yd/sec - ~1.35s to cover 27 yds each way
    constexpr float DIVINE_STAR_PULSE_RADIUS = 3.0f;    // how close a unit must be to the missile to be hit
    constexpr uint32 DIVINE_STAR_PULSE_INTERVAL_MS = 100;
    // Live-playtest bug (2026-09-20): the return leg relied solely on
    // PointMovementGenerator::MovementInform firing when the outbound MovePoint's spline finished
    // (DoFinalize -> MovementInform(POINT_MOTION_TYPE, POINT_DIVINE_STAR_END), see
    // PointMovementGenerator.cpp) - for a hovering/no-gravity trigger creature travelling at an
    // explicit non-zero MovePoint speed, this callback was found to be unreliable in practice (the
    // star flew out and then just sat at the far end until TEMPSUMMON_TIMED_DESPAWN silently
    // removed it - reads in-game as "never returns"). Fixed by no longer trusting that callback
    // alone: the analytic travel time (distance/speed, +buffer for spline/network jitter) is now
    // also scheduled on the same EventMap already used for pulses (a mechanism already proven
    // reliable in this class), so the return leg starts on a deterministic timer even if
    // MovementInform never fires. MovementInform is left wired too (harmless - both paths funnel
    // through the same idempotent StartReturnLeg()/DespawnStar() helpers, guarded by _returning/
    // _despawned so whichever fires first wins and the other becomes a no-op).
    constexpr uint32 DIVINE_STAR_TRAVEL_TIME_MS = uint32(DIVINE_STAR_TRAVEL_DISTANCE / DIVINE_STAR_SPEED * 1000.0f) + 500;
    // "Healing reduced beyond 6 targets" - retail's own curve (10% per target beyond 6,
    // compounding); the design doc gives no explicit number, flagged as playtest-tunable.
    constexpr uint32 DIVINE_STAR_HEAL_FALLOFF_THRESHOLD = 6;
    constexpr float DIVINE_STAR_HEAL_FALLOFF_PER_TARGET = 0.9f;
    // Matches divine_star_pulse_200134's own base_points (99, stored -1 convention -> live 100) -
    // the flat portion the falloff multiplier applies to; the spellpower coefficient on top of it
    // (coeff_weight=0.4) still applies at full value through the normal damage/heal pipeline, so
    // the falloff only approximates a full-total reduction rather than an exact one. Acceptable for
    // a first pass - see this constant's own use below.
    constexpr int32 DIVINE_STAR_PULSE_BASE_HEAL = 100;
}

class npc_pri_divine_star : public CreatureAI
{
public:
    explicit npc_pri_divine_star(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* owner = summoner->ToUnit();
        if (!owner)
            return;

        _ownerGUID = owner->GetGUID();
        _origin = owner->GetPosition();
        me->SetFaction(owner->GetFaction());
        // Same reasoning as npc_mage_frozen_orb::IsSummonedBy (spell_mage.cpp): a plain trigger
        // creature needs this to resolve attackability against both real hostiles and
        // faction-neutral training dummies the way the owning player would.
        me->SetUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED);
        me->SetLevel(owner->GetLevel(), false);
        me->SetDisableGravity(true);
        me->SetHover(true);

        Position dest = owner->GetFirstCollisionPosition(DIVINE_STAR_TRAVEL_DISTANCE, 0.0f);
        me->GetMotionMaster()->MovePoint(POINT_DIVINE_STAR_END, dest, FORCED_MOVEMENT_NONE, DIVINE_STAR_SPEED, false);

        _events.ScheduleEvent(EVENT_DIVINE_STAR_PULSE, std::chrono::milliseconds(DIVINE_STAR_PULSE_INTERVAL_MS));
        _events.ScheduleEvent(EVENT_DIVINE_STAR_RETURN, std::chrono::milliseconds(DIVINE_STAR_TRAVEL_TIME_MS));
    }

    // Root-caused (2026-09-20, via temp server-side tracing): this fires synchronously from deep
    // inside MotionMaster::DirectExpire's own cleanup cascade (Update -> MovementExpired ->
    // DirectExpire -> DirectDelete -> MovementGenerator::Finalize -> here). Calling MovePoint() from
    // in here to start the next leg re-enters MotionMaster::Mutate() while DirectExpire is still
    // unwinding - the new generator gets Initialize()'d immediately (real bug: this genuinely
    // launches a fresh spline), but DirectExpire then falls through to its own trailing
    // `top()->Reset(_owner)` call, which now targets the *new* generator we just Mutate()'d in
    // instead of the one DirectExpire actually meant to reset - PointMovementGenerator::DoReset
    // calls unit->StopMoving(), killing the just-launched return leg on the same tick it started,
    // before the star travels a single yard. The next tick then sees an already-stopped/finalized
    // spline and immediately reports "arrived" at the same spot it never left - exactly the
    // "instant no-travel return" observed live. Fix: never call StartReturnLeg()/DespawnStar() from
    // this reentrant callback - only from UpdateAI's own EventMap-timer tick below, which runs as a
    // separate top-level call from Creature::Update(), outside MotionMaster's callback stack
    // entirely. This override is now a no-op (kept only so a future readthrough finds this comment
    // instead of silently wondering why MovementInform isn't overridden at all for a class that
    // clearly cares about point-arrival).
    void MovementInform(uint32 /*type*/, uint32 /*id*/) override
    {
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            if (eventId == EVENT_DIVINE_STAR_PULSE)
            {
                DoPulse();
                _events.ScheduleEvent(EVENT_DIVINE_STAR_PULSE, std::chrono::milliseconds(DIVINE_STAR_PULSE_INTERVAL_MS));
            }
            else if (eventId == EVENT_DIVINE_STAR_RETURN)
                StartReturnLeg();
            else if (eventId == EVENT_DIVINE_STAR_DESPAWN)
                DespawnStar();
        }
    }

private:
    // Only ever called from UpdateAI's EventMap tick (see MovementInform's own comment above for
    // why it must never be called from there) - the _returning guard is cheap insurance, not load-
    // bearing dedup, since there's now only one caller.
    void StartReturnLeg()
    {
        if (_returning)
            return;
        _returning = true;

        // Fresh per-leg hit set, the cast-wide heal-falloff counter (_alliesHealed) carries over.
        _hitThisLeg.clear();
        me->GetMotionMaster()->MovePoint(POINT_DIVINE_STAR_RETURN, _origin, FORCED_MOVEMENT_NONE, DIVINE_STAR_SPEED, false);
        _events.ScheduleEvent(EVENT_DIVINE_STAR_DESPAWN, std::chrono::milliseconds(DIVINE_STAR_TRAVEL_TIME_MS));
    }

    void DespawnStar()
    {
        if (_despawned)
            return;
        _despawned = true;
        me->DespawnOrUnsummon();
    }

    void DoPulse()
    {
        Unit* owner = ObjectAccessor::GetUnit(*me, _ownerGUID);
        if (!owner)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnitInObjectRangeCheck check(me, DIVINE_STAR_PULSE_RADIUS);
        Acore::UnitListSearcher<Acore::AnyUnitInObjectRangeCheck> searcher(me, nearby, check);
        Cell::VisitObjects(me, searcher, DIVINE_STAR_PULSE_RADIUS);

        for (Unit* unit : nearby)
        {
            // Only the orb itself is excluded here. The owner IS a legitimate target - the design
            // doc's "healing allies in its path" doesn't carve out the caster, and since the star
            // launches from and returns to the owner's own position, they're trivially in its path
            // on both legs (live-playtest bug 2026-09-20: originally skipped unit == owner too,
            // which meant Divine Star could never heal the priest who cast it).
            if (unit == me)
                continue;
            if (!_hitThisLeg.insert(unit->GetGUID()).second)
                continue; // already hit this leg

            if (owner->IsValidAssistTarget(unit))
            {
                ++_alliesHealed;
                if (_alliesHealed > DIVINE_STAR_HEAL_FALLOFF_THRESHOLD)
                {
                    float mult = std::pow(DIVINE_STAR_HEAL_FALLOFF_PER_TARGET, float(_alliesHealed - DIVINE_STAR_HEAL_FALLOFF_THRESHOLD));
                    int32 amount = int32(float(DIVINE_STAR_PULSE_BASE_HEAL) * mult);
                    owner->CastCustomSpell(SPELL_PRIEST_DIVINE_STAR_PULSE, SPELLVALUE_BASE_POINT0, amount, unit, true);
                    continue;
                }
            }

            owner->CastSpell(unit, SPELL_PRIEST_DIVINE_STAR_PULSE, true);
        }
    }

    ObjectGuid _ownerGUID;
    Position _origin;
    EventMap _events;
    std::set<ObjectGuid> _hitThisLeg;
    uint32 _alliesHealed = 0;
    bool _returning = false;
    bool _despawned = false;
};

// 200133 - Divine Star
class spell_pri_divine_star : public SpellScript
{
    PrepareSpellScript(spell_pri_divine_star);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_DIVINE_STAR_PULSE });
    }

    void SummonStar(SpellEffIndex /*effIndex*/)
    {
        // 15s outer backstop - well past the ~2.6s actual round trip (2 * DIVINE_STAR_TRAVEL_TIME_MS)
        // the AI's own EventMap-driven despawn now handles; this is just a safety net so a stray orb
        // can never linger indefinitely if something upstream goes wrong.
        if (Unit* caster = GetCaster())
            caster->SummonCreature(NPC_PRIEST_DIVINE_STAR, *caster, TEMPSUMMON_TIMED_DESPAWN, 15000);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_pri_divine_star::SummonStar, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

/*
 * 200134 - Divine Star Pulse. Live-playtest bugfix (2026-09-20, "not sure if Divine Star is
 * healing, is it being attributed correctly"): this spell relies on an explicit single-unit target
 * (npc_pri_divine_star::DoPulse casts it directly at whichever unit it finds, not a native AoE
 * search), and for that target-selection path (TARGET_REFERENCE_TYPE_TARGET / DEFAULT category)
 * Spell::SelectImplicitTargetObjectTargets never consults each effect's own TARGET_UNIT_TARGET_ALLY
 * (21, EFFECT_0/HEAL) vs TARGET_UNIT_TARGET_ENEMY (6, EFFECT_1/SCHOOL_DAMAGE) check - that's only
 * honored by the AoE/nearby/chain/trajectory search paths (SelectImplicitAreaTargets etc), never by
 * this one. Left alone, BOTH effects apply to every unit hit, ally or enemy - a priest healing
 * themself also silently self-damages for the same amount, and any enemy hit also gets healed
 * alongside the damage. Fixed here by nulling out whichever effect's target doesn't match the
 * caster's real IsValidAssistTarget/IsValidAttackTarget read on that unit - same idiom
 * spell_mage_arcane_blast::ClearSelfTarget (spell_mage.cpp) uses to drop a single effect's target
 * without touching the other effect's own independent resolution.
 */
class spell_pri_divine_star_pulse : public SpellScript
{
    PrepareSpellScript(spell_pri_divine_star_pulse);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GUIDING_STAR_ABSORB });
    }

    void FilterAllyTarget(WorldObject*& target)
    {
        Unit* caster = GetCaster();
        Unit* unitTarget = target ? target->ToUnit() : nullptr;
        if (caster && unitTarget && !caster->IsValidAssistTarget(unitTarget))
            target = nullptr;
    }

    void FilterEnemyTarget(WorldObject*& target)
    {
        Unit* caster = GetCaster();
        Unit* unitTarget = target ? target->ToUnit() : nullptr;
        if (caster && unitTarget && !caster->IsValidAttackTarget(unitTarget))
            target = nullptr;
    }

    /*
     * Guiding Star (Discipline 5,3, docs/reworks/priest-disc-rework.md): "causes its healing to
     * apply an absorb shield equal to 15/30% of the amount healed. Applies once per pass, so a
     * full out-and-back cast shields twice." Each pass is a separate pulse cast, so hooking the
     * pulse gives the "once per pass" rule for free. Self-contained: it does not require, and does
     * not consume, the Divine Aegis talent (PLAN sec 2: a second pass adds to the first, same
     * shape as Divine Aegis).
     *
     * The talent's two ranks are read by explicit rank spell id rather than the dummy-by-icon
     * idiom - this talent is brand new, so its SpellIconID is assigned on the data side and there
     * is no stock icon to key on, while both rank ids are fixed by DISC.md's ID map.
     */
    void HandleGuidingStar()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 healed = GetHitHeal();
        if (healed <= 0)
            return;

        AuraEffect const* guidingStar = caster->GetAuraEffect(SPELL_PRIEST_GUIDING_STAR_R2, EFFECT_2);
        if (!guidingStar)
            guidingStar = caster->GetAuraEffect(SPELL_PRIEST_GUIDING_STAR_R1, EFFECT_2);

        if (!guidingStar)
            return;

        int32 absorb = int32(CalculatePct(float(healed), float(guidingStar->GetAmount())));
        if (absorb <= 0)
            return;

        if (AuraEffect const* existing = target->GetAuraEffect(SPELL_PRIEST_GUIDING_STAR_ABSORB, EFFECT_0, caster->GetGUID()))
            absorb += existing->GetAmount();

        caster->CastCustomSpell(SPELL_PRIEST_GUIDING_STAR_ABSORB, SPELLVALUE_BASE_POINT0, absorb, target, true);
    }

    void Register() override
    {
        OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_pri_divine_star_pulse::FilterAllyTarget, EFFECT_0, TARGET_UNIT_TARGET_ALLY);
        OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_pri_divine_star_pulse::FilterEnemyTarget, EFFECT_1, TARGET_UNIT_TARGET_ENEMY);
        AfterHit += SpellHitFn(spell_pri_divine_star_pulse::HandleGuidingStar);
    }
};

/*
 * Halo (docs/reworks/priest-new-spells.md): "Creates a ring of Holy energy around you that quickly
 * expands to a 40 yd radius, healing allies for... and dealing... Holy damage to enemies." Self-buff
 * aura ticking every 100ms, computing the ring's current radius from elapsed/max duration each
 * tick and casting halo_pulse_200136 at whichever units are newly within that radius - same
 * explicit-single-unit-target idiom as Divine Star's pulse, and the same "search the whole growing
 * disc each tick, dedup by GUID" trick (a naive re-query at a fixed final radius would re-hit
 * everyone already inside on every tick; the dedup set makes this cheap and simple without needing
 * true annulus-band radius math).
 */
class spell_pri_halo : public AuraScript
{
    PrepareAuraScript(spell_pri_halo);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_HALO_PULSE });
    }

    void OnPeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetTarget();
        if (!caster)
            return;

        Aura const* base = aurEff->GetBase();
        int32 maxDuration = base->GetMaxDuration();
        if (maxDuration <= 0)
            return;

        float elapsedFraction = float(maxDuration - base->GetDuration()) / float(maxDuration);
        elapsedFraction = std::min(elapsedFraction, 1.0f);
        float radius = 40.0f * elapsedFraction;
        if (radius <= 0.0f)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnitInObjectRangeCheck check(caster, radius);
        Acore::UnitListSearcher<Acore::AnyUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, radius);

        for (Unit* unit : nearby)
        {
            // Live-playtest bug (2026-09-20): explicitly excluding the caster here meant Halo could
            // never heal the priest who cast it, even though they're standing at the ring's own
            // center the whole time - same class of bug Divine Star had (see
            // npc_pri_divine_star::DoPulse's own comment) and the design doc's "healing allies"
            // doesn't carve the caster out either. Removed.
            if (!_hit.insert(unit->GetGUID()).second)
                continue;

            caster->CastSpell(unit, SPELL_PRIEST_HALO_PULSE, true);
        }
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_halo::OnPeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY);
    }

private:
    std::set<ObjectGuid> _hit;
};

/*
 * 200136 - Halo Pulse. Live-playtest bugfix (2026-09-20, "Halo is also not healing either or its
 * not being attributed correctly"): same underlying gap as Divine Star Pulse
 * (spell_pri_divine_star_pulse above, see its own notes for the full mechanism writeup) - this
 * spell also relies on an explicit single-unit target (spell_pri_halo::OnPeriodic casts it
 * directly at whichever unit the expanding ring newly finds, not a native AoE search), and
 * Spell::SelectImplicitTargetObjectTargets never consults TARGET_UNIT_TARGET_ALLY (21,
 * EFFECT_0/HEAL) vs TARGET_UNIT_TARGET_ENEMY (6, EFFECT_1/SCHOOL_DAMAGE) for that target-reference
 * path. Left alone, both effects landed on every unit the ring touched regardless of reaction.
 * Same OnObjectTargetSelect-nulling fix as Divine Star's pulse.
 */
class spell_pri_halo_pulse : public SpellScript
{
    PrepareSpellScript(spell_pri_halo_pulse);

    void FilterAllyTarget(WorldObject*& target)
    {
        Unit* caster = GetCaster();
        Unit* unitTarget = target ? target->ToUnit() : nullptr;
        if (caster && unitTarget && !caster->IsValidAssistTarget(unitTarget))
            target = nullptr;
    }

    void FilterEnemyTarget(WorldObject*& target)
    {
        Unit* caster = GetCaster();
        Unit* unitTarget = target ? target->ToUnit() : nullptr;
        if (caster && unitTarget && !caster->IsValidAttackTarget(unitTarget))
            target = nullptr;
    }

    void Register() override
    {
        OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_pri_halo_pulse::FilterAllyTarget, EFFECT_0, TARGET_UNIT_TARGET_ALLY);
        OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_pri_halo_pulse::FilterEnemyTarget, EFFECT_1, TARGET_UNIT_TARGET_ENEMY);
    }
};

/*
 * Leap of Faith (docs/reworks/priest-new-spells.md): "Pulls the spirit of a party or raid member,
 * instantly moving them directly in front of you." Modeled directly on DK Death Grip
 * (spell_dk.cpp's spell_dk_death_grip::HandleDummy), direction reversed: the destination is near
 * the *caster*, not the target's own explicit dest, since this pulls a friendly ally to the priest
 * rather than yanking an enemy to the DK.
 */
class spell_pri_leap_of_faith : public SpellScript
{
    PrepareSpellScript(spell_pri_leap_of_faith);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_LEAP_OF_FAITH_JUMP });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster)
            return;

        Position dest = caster->GetFirstCollisionPosition(2.0f, 0.0f);
        target->CastSpell(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), SPELL_PRIEST_LEAP_OF_FAITH_JUMP, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pri_leap_of_faith::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

/*
 * Void Eruption (docs/reworks/priest-new-spells.md): "Releases an explosive blast of pure void
 * energy, causing Shadow damage to up to 10 enemies within 10 yards of your target. The power
 * drawn from the Void increases your periodic Shadow damage by 10% for 10 sec, with the duration
 * increased by 0.5 sec for each enemy hit. While in Shadowform this spell also applies Shadow
 * Word: Pain to all enemies hit." Baseline behavior only this pass - Shadow spec's "Generates 25
 * Madness" (priest-shadow-rework.md) is deferred to whenever the Shadow resource system itself
 * gets built. The periodic-Shadow-damage %-boost itself is read live from Voidform's marker aura
 * by Priest::ApplyDoneDamagePctMods (PriestMechanics.h/.cpp), wired into
 * Unit::SpellPctDamageModsDone next to Mage's own equivalent hook.
 */
namespace
{
    constexpr uint32 VOID_ERUPTION_MAX_TARGETS = 10;
    constexpr int32 VOID_ERUPTION_VOIDFORM_BASE_DURATION_MS = 10000;
    constexpr int32 VOID_ERUPTION_VOIDFORM_DURATION_PER_HIT_MS = 500;
}

class spell_pri_void_eruption : public SpellScript
{
    PrepareSpellScript(spell_pri_void_eruption);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_VOIDFORM, SPELL_PRIEST_SHADOW_WORD_PAIN, SPELL_PRIEST_SHADOWFORM });
    }

    // "up to 10 enemies" - trimmed here rather than in DBC data (no MaxAffectedTargets field
    // exposed by this pipeline's DSL for a plain dest-area effect). RandomResize is a no-op when
    // the list is already at or under the requested size.
    void TrimTargets(std::list<WorldObject*>& targets)
    {
        Acore::Containers::RandomResize(targets, VOID_ERUPTION_MAX_TARGETS);
    }

    void CountHit(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        ++_hitCount;

        // Shadow Word: Pain application while in Shadowform - "may not tag enemies not already in
        // combat with the caster's party" (design doc).
        if (!caster->HasAura(SPELL_PRIEST_SHADOWFORM))
            return;

        bool alreadyEngaged = caster->IsInCombatWith(target);
        if (!alreadyEngaged)
        {
            if (Group* group = caster->ToPlayer() ? caster->ToPlayer()->GetGroup() : nullptr)
            {
                for (GroupReference* ref = group->GetFirstMember(); ref && !alreadyEngaged; ref = ref->next())
                    if (Player* member = ref->GetSource())
                        if (member != caster && member->IsInCombatWith(target))
                            alreadyEngaged = true;
            }
        }

        if (alreadyEngaged)
            caster->CastSpell(target, SPELL_PRIEST_SHADOW_WORD_PAIN, true);
    }

    void ApplyVoidform()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        int32 duration = VOID_ERUPTION_VOIDFORM_BASE_DURATION_MS + int32(_hitCount) * VOID_ERUPTION_VOIDFORM_DURATION_PER_HIT_MS;
        caster->CastCustomSpell(SPELL_PRIEST_VOIDFORM, SPELLVALUE_AURA_DURATION, duration, caster, true);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_void_eruption::TrimTargets, EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_pri_void_eruption::CountHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterCast += SpellCastFn(spell_pri_void_eruption::ApplyVoidform);
    }

private:
    uint32 _hitCount = 0;
};

void AddSC_priest_new_spell_scripts()
{
    RegisterSpellScript(spell_pri_angelic_feather);
    RegisterCreatureAI(npc_pri_divine_star);
    RegisterSpellScript(spell_pri_divine_star);
    RegisterSpellScript(spell_pri_divine_star_pulse);
    RegisterSpellScript(spell_pri_halo);
    RegisterSpellScript(spell_pri_halo_pulse);
    RegisterSpellScript(spell_pri_leap_of_faith);
    RegisterSpellScript(spell_pri_void_eruption);
}
