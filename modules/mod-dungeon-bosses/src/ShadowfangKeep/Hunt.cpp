/*
 * mod-dungeon-bosses, Shadowfang Keep: the Hunt (Hunt.h), shared by Odo the Blindwatcher (WP-S5) and Baron
 * Silverlaine's Echo of Odo (WP-S3). Modeled on mod-boss-mechanics' `sfk-hunt` drill (MechanicCommand.cpp
 * RegisterHunt, EndHunt).
 */

#include "Hunt.h"
#include "BossMechanics.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>

namespace SfkHunt
{
    // The circle's resolve callback and the Hunt share this; the callback holds it weakly, so a hunt that ended (or a
    // chaser AI that is gone) is never touched from a late pass.
    struct Hunt::State
    {
        Map* map = nullptr;
        ObjectGuid owner;
        ObjectGuid chaser;
        ObjectGuid target;
        uint32 zone = 0;
        bool live = true;               // cleared by a catch, a lost target or the end
        bool caught = false;
        bool lost = false;
        bool prevCombatMovement = true;
    };

    namespace
    {
        uint32 constexpr kHuntPointId = 0x48554E54;    // "HUNT": the re-aimed MovePoint

        void CancelZone(Map* map, uint32 zone)
        {
            if (!map || !zone)
                return;
            if (BossMechanics::Registry* reg = BossMechanics::Registry::Get(map))
                reg->Cancel(zone);
        }

        // One resolve pass of the circle (the drill's: a hit is the catch, else re-aim at the player).
        void OnPass(std::weak_ptr<Hunt::State> const& weak, BossMechanics::ResolveResult const& r)
        {
            std::shared_ptr<Hunt::State> const s = weak.lock();
            if (!s || !s->live || r.fizzled)
                return;
            Creature* chaser = s->map->GetCreature(s->chaser);
            if (!r.hits.empty())
            {
                // The catch: the resolve copy and the Maul rider have landed on the player this pass. No later pass.
                s->caught = true;
                s->live = false;
                CancelZone(s->map, s->zone);
                if (chaser)
                {
                    chaser->GetMotionMaster()->Clear(false);
                    chaser->StopMoving();
                }
                return;
            }
            Player* target = chaser ? ObjectAccessor::GetPlayer(*chaser, s->target) : nullptr;
            if (!chaser || !chaser->IsAlive() || !target || !target->IsAlive() || target->GetMap() != s->map)
            {
                s->lost = true;
                s->live = false;
                CancelZone(s->map, s->zone);
                return;
            }
            // The chaser's own run speed (the hunt rate, slows included): what the bots read for the circle's drift.
            chaser->GetMotionMaster()->MovePoint(kHuntPointId, target->GetPosition());
        }
    }

    bool Hunt::Start(Unit* owner, Creature* chaser, Player* target, HuntTuning const& tuning, HuntSpells const& spells,
        uint32 tag)
    {
        if (!owner || !chaser || !target || !owner->IsInWorld() || !chaser->IsInWorld() || !chaser->IsAlive()
            || !target->IsInWorld() || !target->IsAlive() || target->GetMap() != chaser->GetMap()
            || owner->GetMap() != chaser->GetMap())
            return false;
        if (Active())
            Stop(chaser, false);

        std::shared_ptr<State> const state = std::make_shared<State>();
        state->map = chaser->GetMap();
        state->owner = owner->GetGUID();
        state->chaser = chaser->GetGUID();
        state->target = target->GetGUID();

        // The catch circle (drill: `hunt <radius> <warn> persist=<chase> tick=<tick>`, eligible = the hunted only).
        BossMechanics::Eligibility eligibility;
        eligibility.carriers = { target->GetGUID() };
        {
            BossMechanics::MechanicRef ref = Mechanic::Circle(owner, chaser, tuning.radius,
                Milliseconds(tuning.warnMs));
            ref.Persistent(Milliseconds(tuning.chaseMs), Milliseconds(tuning.tickMs)).Eligible(eligibility);
            if (spells.catchHit)
                ref.Spell(spells.catchHit);
            if (spells.maul)
                ref.Rider(spells.maul);
            if (tag)
                ref.Tag(tag);
            std::weak_ptr<State> const weak = state;
            ref.OnResolve([weak](BossMechanics::ResolveResult const& r) { OnPass(weak, r); });
            state->zone = ref.Handle().id;
        }   // the ref commits here
        if (!state->zone)
            return false;

        _state = state;
        _tuning = tuning;
        _spells = spells;
        _elapsedMs = 0;

        // He drops the tank: no chase of the victim while hunting (a victim change attacks without moving).
        state->prevCombatMovement = chaser->IsCombatMovementAllowed();
        chaser->SetCombatMovement(false);
        chaser->GetMotionMaster()->Clear(false);
        chaser->StopMoving();
        chaser->SetWalk(false);
        chaser->SetFacingToObject(target);
        // The hunt rate from the start, as the drill's chaser (the bots read it during the howl too).
        DungeonKit::SetRunSpeedPct(chaser, tuning.ratePct);
        if (spells.hunted)
            chaser->CastSpell(target, spells.hunted, true);
        if (spells.howl)
            DungeonKit::CastBar(chaser, spells.howl);     // on himself (a self-only bar), facing the target
        return true;
    }

    HuntEnd Hunt::Update(Creature* chaser, uint32 diff)
    {
        if (!_state)
            return HuntEnd::None;
        _elapsedMs += diff;

        HuntEnd end = HuntEnd::None;
        if (_state->caught)
            end = HuntEnd::Caught;
        else if (_state->lost)
            end = HuntEnd::TargetLost;
        else
        {
            Player* target = chaser ? ObjectAccessor::GetPlayer(*chaser, _state->target) : nullptr;
            if (!chaser || !target || !target->IsAlive() || target->GetMap() != chaser->GetMap())
                end = HuntEnd::TargetLost;
            // One tick of grace past the end, so the circle's last pass (at warn + chase) runs first.
            else if (_elapsedMs >= TotalMs(_tuning) + _tuning.tickMs)
                end = HuntEnd::Escaped;
        }
        if (end == HuntEnd::None)
            return end;
        Finish(chaser, true);
        return end;
    }

    void Hunt::Stop(Creature* chaser, bool resumeChase)
    {
        if (_state)
            Finish(chaser, resumeChase);
    }

    bool Hunt::Chasing() const
    {
        return _state && _elapsedMs >= _tuning.warnMs;
    }

    ObjectGuid Hunt::Target() const
    {
        return _state ? _state->target : ObjectGuid::Empty;
    }

    void Hunt::Finish(Creature* chaser, bool resumeChase)
    {
        std::shared_ptr<State> const s = std::move(_state);
        _state.reset();
        _elapsedMs = 0;
        if (!s)
            return;
        s->live = false;
        CancelZone(s->map, s->zone);

        if (!chaser || !chaser->IsInWorld())
            return;
        if (_spells.hunted)
            if (Player* target = ObjectAccessor::GetPlayer(*chaser, s->target))
                target->RemoveAurasDueToSpell(_spells.hunted, chaser->GetGUID());
        if (!chaser->IsAlive())
            return;
        // A hunt stopped during the howl (a bell rung at once) drops the cast bar.
        if (_spells.howl && chaser->FindCurrentSpellBySpellId(_spells.howl))
            chaser->InterruptNonMeleeSpells(false, _spells.howl);
        if (CreatureTemplate const* t = chaser->GetCreatureTemplate())
            chaser->SetSpeed(MOVE_RUN, t->speed_run);
        chaser->SetCombatMovement(s->prevCombatMovement);
        if (chaser->GetMotionMaster()->GetCurrentMovementGeneratorType() == POINT_MOTION_TYPE)
        {
            chaser->GetMotionMaster()->Clear(false);
            chaser->StopMoving();
        }
        if (resumeChase && chaser->IsCombatMovementAllowed())
            if (Unit* victim = chaser->GetVictim())
                chaser->GetMotionMaster()->MoveChase(victim);
    }
}

// The Maul's stun and bleed (Odo's, the echo's): the bleed effect's calculated value is the total percent of reference
// health; each tick deals RefFlat(caster, total / ticks) (HuntLogic.h MaulTickPct). The caster is the registry rider's
// original caster, the encounter owner. SPELL_ATTR3_IGNORE_CASTER_MODIFIERS on the spell keeps Blood Frenzy and
// Howling Rage out of it.
class spell_sfk_hunt_maul : public AuraScript
{
    PrepareAuraScript(spell_sfk_hunt_maul);

    void CalcAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        SpellInfo const* info = GetSpellInfo();
        uint32 const duration = static_cast<uint32>(std::max(0, info->GetMaxDuration()));
        float const tickPct = SfkHunt::MaulTickPct(static_cast<float>(amount), duration,
            static_cast<uint32>(std::max(0, aurEff->GetAmplitude())));
        amount = static_cast<int32>(DungeonKit::RefFlat(GetCaster(), tickPct));
        canBeRecalculated = false;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sfk_hunt_maul::CalcAmount, EFFECT_ALL,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

namespace SfkHunt
{
    void AddSC_sfk_hunt()
    {
        RegisterSpellScript(spell_sfk_hunt_maul);
    }
}
