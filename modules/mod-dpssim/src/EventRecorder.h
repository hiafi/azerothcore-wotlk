/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_EVENTRECORDER_H
#define MODULE_DPSSIM_EVENTRECORDER_H

#include "ObjectGuid.h"
#include "ScriptMgr.h"
#include <vector>

// Minimal M1 combat-log capture: total damage dealt, cast count, and crit count for one sim
// actor's hits against one sim target. Full per-spell breakdown is M3 (see the plan doc's Phase 1
// task list) - this is deliberately just enough for a human to spot-check a DPS number rather
// than trust a single aggregate figure blindly (expected casts roughly equal fight duration /
// cast time, observed crit rate roughly equal the configured crit chance).
//
// Hooks a single point in the damage pipeline: OnSpellDamageTakenFinal
// (UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, fires from Unit::CalculateSpellDamageTaken once `damage`
// has its fully mitigated - armor, crit bonus, block/resilience all applied - value). Two
// properties of that hook make it sufficient on its own, which is why this class doesn't also need
// OnDamage:
//   - It fires upstream of Unit::DealDamage, so its `damage` is the real, un-zeroed hit - unlike
//     OnDamage, which fires *after* a target's own DamageTaken() AI hook has already run and, for
//     some target types (e.g. SimTarget's training dummy - see its class comment), already zeroed
//     `damage` by then.
//   - It structurally only fires for direct spell hits, never periodic DoT ticks (those route
//     through the separate ModifyPeriodicDamageAurasTick hook instead - confirmed by reading every
//     call site of both in Unit.cpp/SpellAuraEffects.cpp), so there's no need to separately check
//     damageType == DOT the way an OnDamage-based recorder would.
// `isCrit` comes from this same hook - Unit::CalculateSpellDamageTaken already has the caster's
// crit roll as its own `crit` parameter, computed upstream of this hook's call, so threading it
// through costs nothing extra.
//
// **Root-caused 2026-09-12**: this class originally hooked ModifySpellDamageTaken instead (still
// present in core, unmodified, still used by mythic_plus_damage_affix_unitscript) on the mistaken
// assumption that its `damage` was already crit-adjusted by the time the hook fires. It isn't -
// that hook fires from CalculateSpellDamageTaken *before* the per-class mitigation switch that
// actually applies the crit multiplier (see Unit.cpp), so every crit this class recorded was
// silently logged at its base, non-crit value while still being flagged `isCrit = true`. Every DPS
// report generated before this fix undercounts crit damage and should be treated as stale.
// OnSpellDamageTakenFinal was added as a new, purely additive hook (see its own doc comment in
// UnitScript.h) specifically to fix this without touching ModifySpellDamageTaken's call site or
// semantics for its existing consumer.
//
// Frostbolt-only for M1 (direct spell hits) - a rotation with melee damage would need
// ModifyMeleeDamage too, for the same "read before DamageTaken zeroes it" reason.
//
// Filters by GUID rather than storing the actor/target Unit* directly, per this repo's convention
// of never holding a raw Unit*/Player*/Creature* past the call that produced it.
//
// **Must be heap-allocated (`new`), never a local/stack object.** Like every ScriptObject
// subclass, its constructor self-registers a raw `this` into ScriptRegistry<UnitScript>'s global,
// process-lifetime static maps, and the only matching teardown is ScriptMgr::Unload() at actual
// process shutdown, which unconditionally `delete`s every registered script. SimDaemon.cpp does
// not delete its EventRecorder either, for the same reason - ownership passes to ScriptMgr at
// construction, same as any other UnitScript. Known M1 limitation worth flagging for whenever a
// later milestone runs multiple sim iterations in one process: each iteration's EventRecorder
// leaks into that registry for the process's remaining lifetime (harmless - a stale instance's
// hooks just no-op forever, since GUIDs never match after its run ends - but wasteful); a real fix
// needs a script-unregistration path this codebase doesn't have yet.
//
// Deliberately constructed at runtime from SimDaemon.cpp, well after server boot, rather than
// from an AddSC_* module loader - ScriptRegistry's own comment warns its containers "must not be
// modified after server startup" because they're normally read concurrently by every map-update
// thread. That doesn't apply in sim mode: DpsSim.Enabled forces MapUpdate.Threads to 0
// (World::LoadConfigSettings()), so the sim loop is the only code driving Map::Update() - and
// therefore the only code that can produce these hook calls - and it runs on the same thread that
// constructs this object.
class EventRecorder : public UnitScript
{
public:
    // rotationSpellId == 0 (the default) means "track every spell the actor lands on the target",
    // not just one - added for Phase 2 (M2a), where a real mod-playerbots Engine/Strategy casts a
    // whole rotation of different spells rather than Phase 1's single hardcoded Frostbolt. Phase
    // 1's tests still pass a real id and get the original single-spell-filtered behavior.
    explicit EventRecorder(ObjectGuid actorGuid, ObjectGuid targetGuid, uint32 rotationSpellId = 0);

    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo, bool isCrit) override;

    // Aura tracking - added 2026-09-11 to directly observe whether talent-gated procs (Fingers of
    // Frost, Brain Freeze, Arcane Blast stacks, ...) actually fire, rather than inferring it from
    // which spells get cast. Both hooks already exist, unmodified, in core (UnitScript.h) and are
    // already wired up from Unit.cpp - no core widening needed, unlike ModifySpellDamageTaken back
    // in Phase 1. OnAuraApply only gets a bare Aura* (not a per-target AuraApplication*), so
    // positivity here comes from SpellInfo::IsPositive() (a spell-level classification) rather than
    // AuraApplication::IsPositive() (a per-application one) - fine for this sim's single-actor,
    // single-target scope, where the two should never disagree.
    void OnAuraApply(Unit* unit, Aura* aura) override;
    void OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode mode) override;

    // Clears every accumulated counter/vector back to a freshly-constructed instance's state,
    // without re-registering with ScriptRegistry<UnitScript> or changing actorGuid/targetGuid/
    // rotationSpellId. Added 2026-09-13 for SimDaemon::RunPlayerbotBatch() - running many
    // iterations in one process reuses the same actor/target Player/Creature (see that function's
    // own doc comment for why), so this recorder has to be explicitly rewound between iterations
    // instead of one fresh instance per run like RunPlayerbotOnce() still does. Never call this
    // mid-run - only between one iteration's result collection and the next iteration's first tick.
    void Reset();

    [[nodiscard]] uint64 GetTotalDamage() const { return _totalDamage; }
    [[nodiscard]] uint32 GetCastCount() const { return _castCount; }
    [[nodiscard]] uint32 GetCritCount() const { return _critCount; }

    // Per-hit damage values, in landing order. Needed for tests that check individual hits
    // against a hand-computed bound, not just the aggregate total (a compensating pair of bugs
    // can land on the right total by accident - see the plan doc's known-value test task).
    [[nodiscard]] std::vector<uint32> const& GetHitDamages() const { return _hitDamages; }

    // Per-hit crit flags, in landing order - GetHitCrits()[i] describes the same hit as
    // GetHitDamages()[i], both pushed together from the same OnSpellDamageTakenFinal call, so
    // there's no cross-hook correlation assumption here.
    [[nodiscard]] std::vector<bool> const& GetHitCrits() const { return _hitCrits; }

    // Per-hit spell ids, in landing order, parallel to GetHitDamages()/GetHitCrits() - lets a
    // human (or a future test) sanity-check that a real rotation actually cast a variety of
    // spells rather than falling back to nothing. Not a substitute for M3's real per-spell
    // breakdown (which would aggregate by spell rather than just list them per hit).
    [[nodiscard]] std::vector<uint32> const& GetHitSpellIds() const { return _hitSpellIds; }

    // Per-hit sim-clock timestamps (getMSTime() at the moment OnSpellDamageTakenFinal fired),
    // parallel to GetHitDamages()/GetHitCrits()/GetHitSpellIds() - safe to use directly as a
    // timeline value under the sim clock override (Timer.h), same as every other timestamp this
    // module logs. Added alongside aura tracking for the same reason: M3's timeline report needs
    // "when", not just "what".
    [[nodiscard]] std::vector<uint32> const& GetHitTimestamps() const { return _hitTimestamps; }

    // One entry per aura gained or lost by the actor or the target while this recorder is alive.
    // `Applied == false` is a removal (SpellId/Positive/StackAmount describe the aura that was
    // removed, not a new one). Not filtered to any particular spell - unlike the rotationSpellId
    // filter on damage hits, there's no equivalent "aura I care about" concept yet; a human (or the
    // eventual M3 report) filters by SpellId/UnitGuid themselves. `IsActor` is a convenience
    // (UnitGuid == _actorGuid) computed at capture time, since this recorder already knows both
    // GUIDs and every caller so far only ever wants "was this on the actor or the target".
    struct AuraEvent
    {
        uint32 TimestampMs;
        ObjectGuid UnitGuid;
        bool IsActor;
        uint32 SpellId;
        uint8 StackAmount;
        bool Positive;
        bool Applied;
    };
    [[nodiscard]] std::vector<AuraEvent> const& GetAuraEvents() const { return _auraEvents; }

private:
    ObjectGuid _actorGuid;
    ObjectGuid _targetGuid;
    uint32 _rotationSpellId;

    uint64 _totalDamage = 0;
    uint32 _castCount = 0;
    uint32 _critCount = 0;
    std::vector<uint32> _hitDamages;
    std::vector<bool> _hitCrits;
    std::vector<uint32> _hitSpellIds;
    std::vector<uint32> _hitTimestamps;
    std::vector<AuraEvent> _auraEvents;
};

#endif
