/*
 * mod-dungeon-bosses, Shadowfang Keep: Fenrus the Devourer and Arugal's Voidwalker (WP-S7). Build spec: SK 1183-1234
 * (build spec), SK 1087-1182 (design), FN1-FN9; handoff section 3.5 rows FN, section 3.6 row S7, section 7 #15 (fake
 * death). Replaces the SmartAI of Fenrus 4274 and Arugal's Voidwalker 4627 (WP-S7's SQL rev drops both, and Arugal's
 * intro action list 427500); Archmage Arugal 4275 speaks from above through the instance (his ObjectData guid).
 *
 * Fenrus (normal and heroic):
 *   FN1 Arugal's Lightning  phase one, from 10 s every 20 s: Arugal's Focus flashes and a 2 s registry circle (3 yd,
 *                           20% Nature, Weakened) lands on a random room-edge point (never the last one); Arugal yells
 *                           "Release your rage!" on the first. As it lands a voidwalker steps out of the strike (FN2).
 *   FN2 Voidwalker          stock entry 4627, rebound to npc_sfk_voidwalker: attacks the nearest player, no cap
 *                           (Dungeon ruling 9). Kill order: voidwalkers, then Fenrus.
 *   FN4 Toxic Saliva        stock 7125 on a random player within 5 yd, 1-7 s, then every 22-45 s (kept, DD scales it).
 *   Arugal's pull line      "Who dares interfere with the Sons of Arugal?" on Fenrus's pull.
 * Heroic on top:
 *   FN5 Shadow Fenrus       a lethal hit leaves him at 1 health (DungeonKit::LethalGuard, handoff s7 #15: no kill, loot
 *                           or credit): he falls still for 1 s, then Arugal yells "You, too, shall serve!" and he rises
 *                           with 40% health, shadow-wrapped (206023), his melee Shadow. Strikes stop bringing
 *                           voidwalkers; those already up keep fighting. His second death is real: BOSS_FENRUS DONE
 *                           opens the Sorcerer's Gate (the instance's door data) and he drops his loot.
 *   FN6/FN7 Shadow Leap     from 5 s into phase two, every 10 s: a 2 s crouch (cast bar + emote), then a registry
 *                           Bait (fewest Shadow Scar stacks baits, the others within 12 yd of him): the farthest player
 *                           and everyone within 6 yd of them take 25% Shadow and a Shadow Scar (+200% Shadow Leap
 *                           damage taken per stack, spell_sfk_fenrus_shadow_leap); the target takes no Weakened, the
 *                           others caught do. He jumps to the landing.
 *   FN8 Shadow Lightning    from 2 s into phase two, every 3 s: a 1 s registry circle (3 yd, 15% Shadow, no Weakened,
 *                           Dungeon ruling 10) under a random player.
 * Arugal's Voidwalker (npc_sfk_voidwalker): FN3 Void Pulse, a real 1.5 s interruptible cast every 3 s (1.5 s cast,
 * 1.5 s pause), 4% Shadow to every player (spell_sfk_fenrus_void_pulse, RefFlat); heroic Rising Pulse +1% per landed
 * pulse up to 10%. Interrupt, stun or kill: any works, none is required. No Dark Offering; its death opens nothing.
 *
 * The boss cannot be kited out of his round room (DungeonKit::ArenaGuard on FenrusArena()). Every firing logs
 * "sfk fenrus <mechanic> ..." (module.dungeonbosses); `.sfktest fenrus <mechanic>` fires one on demand.
 *
 * Stock behavior mirrored from the AzerothCore world DB SmartAI 4274 (Toxic Saliva; the death's instance data is the
 * boss state now), 4627 and Arugal's action list 427500 (the pull line, the Focus animation).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureTextMgr.h"
#include "DungeonKit.h"
#include "FenrusLogic.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include <list>
#include <optional>
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Fenrus;

namespace
{
    char constexpr kBoss[] = "fenrus";

    enum FenrusTimerGroups : uint32
    {
        GROUP_PHASE_ONE = 1,
        GROUP_PHASE_TWO = 2,
    };

    std::string GuidText(ObjectGuid guid)
    {
        return guid.ToString();
    }

    // The floor under a measured point of his room (the navmesh points carry no height).
    Position FloorAt(WorldObject const* ref, Vec2 p)
    {
        float z = ref->GetMapHeight(p.x, p.y, kFenrusFloorZ + 2.f);
        if (z <= INVALID_HEIGHT)
            z = kFenrusFloorZ;
        return DungeonKit::ToPosition(p, z);
    }

    DungeonKit::ArenaGuardOptions FenrusArenaOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.logPrefix = "sfk fenrus arena";
        // A unit that ran out of a doorway lands just inside the room on its way back, not at the boss.
        o.landing = [](Creature const* /*boss*/, Unit const* unit)
        {
            return DungeonKit::ToPosition(GripLanding(kFenrusRoomCenter, DungeonKit::PlaneOf(unit), kGripLandRadius),
                kFenrusFloorZ);
        };
        return o;
    }
}

// Fenrus the Devourer 4274
struct boss_fenrus_the_devourer_rework : public BossAI
{
    explicit boss_fenrus_the_devourer_rework(Creature* creature) : BossAI(creature, BOSS_FENRUS),
        _arena(FenrusArena(), FenrusArenaOptions())
    {
    }

    void Reset() override
    {
        BossAI::Reset();
        _timers.CancelAll();
        _arena.Reset();
        _lethal.Reset();
        _phase = Phase::One;
        _strikes = 0;
        _lastStrike.reset();
        RestoreLook();
        ClearScars();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_FENRUS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Mechanic::SetPhase(me, kDescriptorPhaseOne);
        _arena.Engage(me);
        ArugalSays(YELL_ARUGAL_FENRUS_PULL);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }

    void ScheduleTasks() override
    {
        // FN4 on the BossAI scheduler (it waits out his own casts).
        scheduler.Schedule(kSalivaFirstMin, kSalivaFirstMax, [this](TaskContext ctx)
        {
            if (!MayAct(_phase) || !ToxicSaliva(nullptr))
            {
                ctx.Repeat(kSalivaRetry);
                return;
            }
            ctx.Repeat(kSalivaEveryMin, kSalivaEveryMax);
        });

        // FN1 on _timers: never paused by a cast bar (the Pilot's lesson R1 S-2).
        _timers.Schedule(kLightningFirst, GROUP_PHASE_ONE, [this](TaskContext ctx)
        {
            if (!me->IsInCombat())
                return;
            ArugalsLightning(nullptr);
            ctx.Repeat(kLightningEvery);
        });
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _timers.CancelAll();
        _arena.Reset();
        ClearScars();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "evade", "phase=" + std::to_string(uint32(_phase)));
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _timers.CancelAll();
        _arena.Reset();
        ClearScars();
        BossAI::JustDied(killer);   // BOSS_FENRUS DONE: the Sorcerer's Gate opens (door data); voidwalkers despawn
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "died", "phase=" + std::to_string(uint32(_phase)));
    }

    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        // Only the voidwalkers join the fight; the strike stalker is a look (a helper in combat stalls the evade).
        if (summon->GetEntry() == NPC_ARUGALS_VOIDWALKER && me->IsEngaged())
            DoZoneInCombat(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (!InterceptsLethal(DungeonKit::IsHeroicMap(me), _phase))
            return;
        _lethal.Intercept(me, damage, [this]()
        {
            BeginRising();
        });
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.sfktest` mechanic's follow-ups.
        _timers.Update(diff);

        if (!UpdateVictim())
            return;

        scheduler.Update(diff);

        if (!_arena.Update(me, diff))
            return;     // he left his room: evading

        if (!MayAct(_phase) || me->IsActionPreventedByCasting())
            return;

        DoMeleeAttackIfReady();
    }

    // ---- mechanics (also called by `.sfktest`) ---------------------------------------------------------------------

    // FN1: a strike at a random edge point (`forced`: the point nearest that player, a `.sfktest`).
    void ArugalsLightning(Player* forced)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        std::size_t const index = forced ? NearestStrikeIndex(DungeonKit::PlaneOf(forced))
            : PickStrikeIndex(kFenrusStrikePoints.size(), _lastStrike, [](uint32 n) { return urand(0, n - 1); });
        _lastStrike = index;
        Position const at = FloorAt(me, kFenrusStrikePoints[index]);

        if (!_strikes++)
            ArugalSays(YELL_ARUGAL_RELEASE_YOUR_RAGE);
        FocusFlash();

        Mechanic::Circle(me, at, kLightningRadius, kLightningWarn).Damage(kLightningPct(heroic))
            .Spell(SPELL_FENRUS_ARUGALS_LIGHTNING).Weakened().Tag(TAG_ARUGALS_LIGHTNING)
            .OnResolve(OnFenrus([at](boss_fenrus_the_devourer_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.LightningLands(at, r.hits.size());
            }));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "lightning", Acore::StringFormat("point={} x={:.1f} y={:.1f} "
            "strike={} heroic={}", index, at.GetPositionX(), at.GetPositionY(), _strikes, heroic));
    }

    // FN2: a voidwalker steps out of the strike (phase one only).
    void LightningLands(Position const& at, std::size_t hits)
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "lightning-landed", Acore::StringFormat("hits={} phase={}", hits,
            uint32(_phase)));
        if (StrikeSummons(_phase))
            SummonVoidwalker(at);
    }

    Creature* SummonVoidwalker(Position const& at)
    {
        Creature* walker = me->SummonCreature(NPC_ARUGALS_VOIDWALKER, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
            uint32(kVoidwalkerCorpse.count()));
        if (!walker)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "voidwalker", "summon failed");
            return nullptr;
        }
        walker->CastSpell(walker, SPELL_FENRUS_LIGHTNING_ARRIVAL, true);
        Mechanic::TrackUnit(me, walker);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "voidwalker", Acore::StringFormat("guid={} alive={}",
            GuidText(walker->GetGUID()), AliveVoidwalkers()));
        return walker;
    }

    // FN4: stock Toxic Saliva on a random player within 5 yd (`forced`: that player).
    bool ToxicSaliva(Player* forced)
    {
        Unit* target = forced ? forced : SelectTarget(SelectTargetMethod::Random, 0, kSalivaRange, true);
        if (!target || me->CastSpell(target, SPELL_TOXIC_SALIVA, false) != SPELL_CAST_OK)
            return false;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "saliva", "target=" + GuidText(target->GetGUID()));
        return true;
    }

    // FN5 (heroic): the fake death. He falls still at 1 health; the rise follows on m_Events (not paused by casts and
    // outside the _timers dispatch, so it may schedule there).
    void BeginRising()
    {
        if (_phase != Phase::One)
            return;
        _phase = Phase::Rising;
        _timers.CancelGroup(GROUP_PHASE_ONE);
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->StopMoving();
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetStandState(UNIT_STAND_STATE_DEAD);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "fake-death", Acore::StringFormat("health={} voidwalkers={}",
            me->GetHealth(), AliveVoidwalkers()));

        me->m_Events.AddEventAtOffset([this]()
        {
            if (me->IsAlive() && _phase == Phase::Rising)
                RiseAsShadow();
        }, kStillness);
    }

    void RiseAsShadow()
    {
        _phase = Phase::Two;
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetHealth(PhaseTwoHealth(me->GetMaxHealth()));
        _lethal.Disarm();       // the second death is real
        me->CastSpell(me, SPELL_FENRUS_SHADOW_FENRUS, true);
        me->SetMeleeDamageSchool(SPELL_SCHOOL_SHADOW);
        ArugalSays(YELL_ARUGAL_AGGRO);
        Mechanic::SetPhase(me, kDescriptorPhaseTwo);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "rise", Acore::StringFormat("health={} max={}", me->GetHealth(),
            me->GetMaxHealth()));

        if (!me->IsInCombat())
            return;     // a `.sfktest` rise out of combat: no timers
        _timers.Schedule(kShadowLightningFirst, GROUP_PHASE_TWO, [this](TaskContext ctx)
        {
            if (!me->IsInCombat())
                return;
            ShadowLightning(nullptr);
            ctx.Repeat(kShadowLightningEvery);
        });
        _timers.Schedule(kLeapFirst, GROUP_PHASE_TWO, [this](TaskContext ctx)
        {
            if (!me->IsInCombat())
                return;
            ShadowLeap();
            ctx.Repeat(kLeapEvery);
        });
    }

    // FN6 (+ FN7): the crouch now, the Bait's landing 2 s later; spell_sfk_fenrus_shadow_leap multiplies the hit by the
    // target's Shadow Scars, the rider adds one.
    void ShadowLeap()
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        DungeonKit::CastBar(me, SPELL_FENRUS_SHADOW_LEAP_CAST, nullptr, EMOTE_FENRUS_SHADOW_LEAP);
        Mechanic::Bait(me, BossMechanics::BaitRule::FewestStacks(SPELL_FENRUS_SHADOW_SCAR), kLeapOthersRange,
            kLeapWarn).Radius(kLeapRadius).Damage(kLeapPct(heroic)).Spell(SPELL_FENRUS_SHADOW_LEAP).Weakened()
            .Rider(SPELL_FENRUS_SHADOW_SCAR).Tag(TAG_SHADOW_LEAP)
            .OnResolve(OnFenrus([](boss_fenrus_the_devourer_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.LeapLands(r);
            }));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "leap", Acore::StringFormat("heroic={}", heroic));
    }

    void LeapLands(BossMechanics::ResolveResult const& r)
    {
        Player* target = r.picked.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, r.picked);
        if (target)
            DungeonKit::JumpTo(me, target->GetPosition(), kLeapJumpSpeedXY, kLeapJumpMinSpeedZ);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "leap-landed", Acore::StringFormat("target={} hits={} scars={}",
            r.picked.IsEmpty() ? std::string("none") : GuidText(r.picked), r.hits.size(),
            target ? DungeonKit::Stacks(target, SPELL_FENRUS_SHADOW_SCAR) : 0u));
    }

    // FN8: a 1 s strike under a random player (`forced`: that player).
    void ShadowLightning(Player* forced)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // "under a random player": the tank too (he moves Fenrus off it)
            rule.maxRange = kShadowLightningRange;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return;
        Position const at = target->GetPosition();
        Mechanic::Circle(me, at, kShadowLightningRadius, kShadowLightningWarn).Damage(kShadowLightningPct(heroic))
            .Spell(SPELL_FENRUS_SHADOW_LIGHTNING).Tag(TAG_SHADOW_LIGHTNING)
            .OnResolve(OnFenrus([at](boss_fenrus_the_devourer_rework& ai, BossMechanics::ResolveResult const&)
            {
                ai.StrikeLook(at);
            }));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "shadow-lightning", "target=" + GuidText(target->GetGUID()));
    }

    // FN8's bolt at the point, hit or miss: on the strike / visual stalker 300516 when its template is declared (the
    // resolve copy carries the same look onto every player it hits).
    void StrikeLook(Position const& at)
    {
        if (!sObjectMgr->GetCreatureTemplate(NPC_SFK_STRIKE_STALKER))
            return;
        if (Creature* stalker = me->SummonCreature(NPC_SFK_STRIKE_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
            uint32(kStrikeLookLife.count())))
            stalker->CastSpell(stalker, SPELL_FENRUS_SHADOW_LIGHTNING_LOOK, true);
    }

    Phase CurrentPhase() const { return _phase; }

private:
    // Kill order voidwalkers, then Fenrus; interrupts Void Pulse before Toxic Saliva; dispel Toxic Saliva (Poison).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ARUGALS_VOIDWALKER, 1).AoeOk());
        d.interrupts.emplace_back(NPC_ARUGALS_VOIDWALKER, SPELL_FENRUS_VOID_PULSE, 2, kVoidPulseEvery);
        d.interrupts.emplace_back(NPC_FENRUS, SPELL_TOXIC_SALIVA, 1);
        d.dispels.emplace_back(SPELL_TOXIC_SALIVA, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // Archmage Arugal speaks from his ledge above (stock texts 0-2, yells).
    void ArugalSays(uint8 group)
    {
        Creature* arugal = instance ? instance->GetCreature(DATA_ARUGAL_GUID) : nullptr;
        if (!arugal || !arugal->IsAlive())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "arugal-line", Acore::StringFormat("group={} skipped (no "
                "Arugal)", group));
            return;
        }
        sCreatureTextMgr->SendChat(arugal, group);
    }

    // The lightning plays on Arugal's Focus (stock action list 427500: a custom animation).
    void FocusFlash()
    {
        if (GameObject* focus = instance ? instance->GetGameObject(DATA_ARUGALS_FOCUS_GUID) : nullptr)
            focus->SendCustomAnim(0);
    }

    void RestoreLook()
    {
        me->RemoveAurasDueToSpell(SPELL_FENRUS_SHADOW_FENRUS);
        me->SetMeleeDamageSchool(SpellSchools(me->GetCreatureTemplate()->dmgschool));
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // FN7 lasts for the fight: gone on a wipe and on his death.
    void ClearScars()
    {
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_FENRUS_SHADOW_SCAR);
    }

    uint32 AliveVoidwalkers() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->GetEntry() == NPC_ARUGALS_VOIDWALKER && c->IsAlive())
                    ++n;
        return n;
    }

    // A registry callback that reaches this AI through the map (guids only in the lambda).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnFenrus(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* fenrus = map->GetCreature(guid);
            if (!fenrus || !fenrus->IsAlive() || !fenrus->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_fenrus_the_devourer_rework*>(fenrus->AI()))
                fn(*ai, result);
        };
    }

    // Mechanic timers that a cast bar must not pause (FN1, FN6, FN8). Never scheduled into from inside one of its own
    // tasks except through the TaskContext.
    TaskScheduler _timers;
    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalGuard _lethal;
    Phase _phase = Phase::One;
    uint32 _strikes = 0;
    std::optional<std::size_t> _lastStrike;
};

// Arugal's Voidwalker 4627 (boss kit, FN2 / FN3).
struct npc_sfk_voidwalker : public ScriptedAI
{
    explicit npc_sfk_voidwalker(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _clock = Ms(0);
        _pulse.Start(_clock);
    }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _clock = Ms(0);
        _pulse.Start(_clock);
        // FN2: the nearest player first, so they come to the group and can be cleaved.
        if (Player* nearest = me->SelectNearestPlayer(kVoidwalkerAggroRange))
        {
            me->AddThreat(nearest, 1.f);
            AttackStart(nearest);
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_FENRUS_VOID_PULSE)
            return;
        bool const heroic = DungeonKit::IsHeroicMap(me);
        float const pct = _pulse.Pct(heroic);   // the pulse that just hit (the count goes up below)
        _pulse.Landed(_clock);
        Mechanic::NoteNextCastIn(me, SPELL_FENRUS_VOID_PULSE, kVoidPulsePause);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "pulse", Acore::StringFormat("walker={} pct={} landed={}",
            GuidText(me->GetGUID()), pct, _pulse.LandedCount()));
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_FENRUS_VOID_PULSE)
            return;
        _pulse.Interrupted(_clock);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "pulse-interrupted", "walker=" + GuidText(me->GetGUID()));
    }

    void JustDied(Unit* /*killer*/) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "voidwalker-died", Acore::StringFormat("walker={} landed={}",
            GuidText(me->GetGUID()), _pulse.LandedCount()));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        _clock += Ms(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_pulse.Due(_clock) && !Pulse())
            _pulse.Blocked(_clock);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // FN3: the 1.5 s cast (also `.sfktest fenrus pulse`). False when it could not start (stunned, silenced, locked).
    bool Pulse()
    {
        return me->CastSpell(me, SPELL_FENRUS_VOID_PULSE, false) == SPELL_CAST_OK;
    }

    // Read by spell_sfk_fenrus_void_pulse: this pulse's percent (Rising Pulse counts the landed ones before it).
    float PulsePct() const
    {
        return _pulse.Pct(DungeonKit::IsHeroicMap(me));
    }

private:
    Ms _clock{ 0 };
    PulseClock _pulse;
};

// FN3 Void Pulse 206022: players only; the damage is the voidwalker's current percent of the reference row
// (RefFlat at launch, so the target's defensives count; the spell ignores caster modifiers).
class spell_sfk_fenrus_void_pulse : public SpellScript
{
    PrepareSpellScript(spell_sfk_fenrus_void_pulse);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject const* target) { return !target->IsPlayer(); });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float pct = VoidPulsePct(DungeonKit::IsHeroicMap(caster), 0);
        if (Creature* walker = caster->ToCreature(); walker && walker->IsAIEnabled)
            if (auto* ai = dynamic_cast<npc_sfk_voidwalker*>(walker->AI()))
                pct = ai->PulsePct();
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));   // R2 N-1: per target
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_sfk_fenrus_void_pulse::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_fenrus_void_pulse::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// FN6 / FN7 Shadow Leap 206025 (beside spell_boss_mechanics_resolve, which sets the 25%): each Shadow Scar the player
// already carries adds +200% (the rider adds this landing's stack after the hit).
class spell_sfk_fenrus_shadow_leap : public SpellScript
{
    PrepareSpellScript(spell_sfk_fenrus_shadow_leap);

    void ApplyScars()
    {
        Unit* target = GetHitUnit();
        int32 const damage = GetHitDamage();
        if (!target || damage <= 0)
            return;
        uint32 const stacks = DungeonKit::Stacks(target, SPELL_FENRUS_SHADOW_SCAR);
        if (stacks)
            SetHitDamage(static_cast<int32>(ScarredDamage(static_cast<uint32>(damage), stacks)));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_sfk_fenrus_shadow_leap::ApplyScars);
    }
};

namespace
{
    template <class AI>
    AI* FindAI(ChatHandler* handler, uint32 entry, Creature*& creature)
    {
        creature = SfkTest::FindBoss(handler, entry);
        if (!creature)
            return nullptr;
        AI* ai = creature->IsAIEnabled ? dynamic_cast<AI*>(creature->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Creature {} does not run the Shadowfang Keep rework script.", entry);
        return ai;
    }

    boss_fenrus_the_devourer_rework* FindFenrus(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        return FindAI<boss_fenrus_the_devourer_rework>(handler, NPC_FENRUS, boss);
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_FENRUS, BOSS_FENRUS);
    }

    bool HandleLightning(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        ai->ArugalsLightning(handler->GetPlayer());
        handler->SendSysMessage("Arugal's Lightning: a 3 yd strike at the edge point nearest you in 2 s (20%, "
            "Weakened); a voidwalker steps out of it in phase one.");
        return true;
    }

    bool HandleVoidwalker(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        Player* gm = handler->GetPlayer();
        if (!ai->SummonVoidwalker(gm->GetPosition()))
        {
            handler->SendErrorMessage("The voidwalker could not be summoned.");
            return false;
        }
        handler->SendSysMessage("A voidwalker stepped out at your feet (Void Pulse every 3 s, 1.5 s cast).");
        return true;
    }

    bool HandlePulse(ChatHandler* handler)
    {
        Creature* walker = nullptr;
        npc_sfk_voidwalker* ai = FindAI<npc_sfk_voidwalker>(handler, NPC_ARUGALS_VOIDWALKER, walker);
        if (!ai)
            return false;
        if (!ai->Pulse())
        {
            handler->SendErrorMessage("Void Pulse did not start (casting, stunned, silenced or locked out).");
            return false;
        }
        handler->PSendSysMessage("Void Pulse: 1.5 s cast, then {}% to every player.", ai->PulsePct());
        return true;
    }

    bool HandleSaliva(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        if (!ai->ToxicSaliva(handler->GetPlayer()))
        {
            handler->SendErrorMessage("Toxic Saliva did not cast (stand within 5 yd, .gm off).");
            return false;
        }
        return true;
    }

    bool HandlePhaseTwo(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        if (ai->CurrentPhase() != Phase::One)
        {
            handler->SendErrorMessage("Fenrus is already past phase one.");
            return false;
        }
        ai->BeginRising();
        handler->SendSysMessage("Shadow Fenrus: he falls still for 1 s, then rises with 40% health (timers only in "
            "combat).");
        return true;
    }

    bool HandleLeap(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        ai->ShadowLeap();
        handler->SendSysMessage("Shadow Leap: 2 s crouch, then the farthest player and everyone within 6 yd of them "
            "(25%, x Shadow Scars).");
        return true;
    }

    bool HandleShadowLightning(ChatHandler* handler)
    {
        boss_fenrus_the_devourer_rework* ai = FindFenrus(handler);
        if (!ai)
            return false;
        ai->ShadowLightning(handler->GetPlayer());
        handler->SendSysMessage("Shadow Lightning: a 3 yd strike under you in 1 s (15%, no Weakened).");
        return true;
    }

    bool HandleScar(ChatHandler* handler, Optional<uint32> stacks)
    {
        Player* gm = handler->GetPlayer();
        if (!SfkTest::RequireShadowfangKeep(handler))
            return false;
        uint32 const want = std::min(stacks.value_or(1), kScarMaxStacks);
        int32 const delta = int32(want) - int32(DungeonKit::Stacks(gm, SPELL_FENRUS_SHADOW_SCAR));
        uint32 const now = DungeonKit::AddStacks(gm, SPELL_FENRUS_SHADOW_SCAR, delta, nullptr, kScarMaxStacks);
        handler->PSendSysMessage("Shadow Scar: {} stacks (your next Shadow Leap hit x{}).", now, ScarFactor(now));
        return true;
    }

    ChatCommandTable const& FenrusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",            HandleInfo,            SEC_GAMEMASTER, Console::No },
            { "lightning",       HandleLightning,       SEC_GAMEMASTER, Console::No },
            { "voidwalker",      HandleVoidwalker,      SEC_GAMEMASTER, Console::No },
            { "pulse",           HandlePulse,           SEC_GAMEMASTER, Console::No },
            { "saliva",          HandleSaliva,          SEC_GAMEMASTER, Console::No },
            { "phase2",          HandlePhaseTwo,        SEC_GAMEMASTER, Console::No },
            { "leap",            HandleLeap,            SEC_GAMEMASTER, Console::No },
            { "shadowlightning", HandleShadowLightning, SEC_GAMEMASTER, Console::No },
            { "scar",            HandleScar,            SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_fenrus_the_devourer_rework()
{
    RegisterDungeonReworkCreatureAI(boss_fenrus_the_devourer_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_voidwalker, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_fenrus_void_pulse);
    RegisterSpellScript(spell_sfk_fenrus_shadow_leap);
    SfkTest::RegisterBoss("fenrus", FenrusTestCommands());
}
