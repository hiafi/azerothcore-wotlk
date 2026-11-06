/*
 * mod-dungeon-bosses, Deadmines: Edwin VanCleef, the Blackguards and the shadow image (WP-B8). Build spec: DM 'Edwin
 * VanCleef' Build spec VC1-VC9 (docs/dungeons/deadmines-rework.md); handoff .agents/plans/deadmines-pilot/
 * deadmines-pilot.HANDOFF.md sections 3.4 (VC rows), 3.5 (B8), 7 #12 (DI-8: he is untargetable for the 2 s of an
 * Ambush, a ruling). The hard mode (VC10-VC13) is WP-B9's (vancleef_hard_mode.cpp); its hooks here are marked "B9".
 *
 * Replaces SmartAI 639 (stock: Dual Wield out of combat, lines 0-5, VanCleef's Allies 5200 at 50%). The instance keeps
 * him hidden until Greenskin is DONE (ruling 26; instance_deadmines_rework), and this script never un-hides him: the
 * only visibility it changes is its own vanish, undone when it ends.
 *
 *   VC1 Ambush from the Rigging  emote 6; he vanishes (not selectable, not attackable, unseen; threat kept) and a 5 yd
 *                                registry circle falls under a random non-tank (2 s, 40% Physical + Weakened); he
 *                                drops onto it and goes back to the tank. 12 s, then every 20 s (15 s below 33%).
 *   VC2 Shadow image             from 33% (heroic 50%): two circles under two different non-tanks; he drops on one,
 *                                his image (300427) on the other, same 40% + Weakened at each.
 *   VC3 The guns                 from 66% (line 1): at once, then every 25 s; Greenskin's lanes on the same deck
 *                                frame (GreenskinLanes::Fire): normal 3 lanes rail to rail, 2 s; heroic Greenskin's
 *                                Crossfire grid (4 + 2 lanes, 2.5 s) with burning crossings. Greenskin's cast bars.
 *   VC4 The Brotherhood          at 50% (emote 2): two boss-kit Blackguards (300426) for 300 s, kill order.
 *   VC5 Cheap Shot               a Blackguard's opener on its first target in melee: stock 1833, stun cut to 2 s.
 *   VC6 Rupture                  stock 14903 on the Blackguard's victim (stock targeted itself), stock timers.
 *   VC7 Fire Bomb (H)            a Blackguard's death leaves a 6 yd burning patch, 15 s, 5% Fire per second.
 *   VC8 Thrash                   stock aura 3417 (creature_template_addon) procs 3391.
 *   VC9 Expose Armor (H)         each Thrash proc stacks -6% armor on his victim, 5 stacks, 20 s.
 *   Lines 0 aggro, 4 kill, 5 death (stock), 1 / 2 / 3 at 66 / 50 / 33%; 10 (arrival) is the instance's.
 *
 * Every mechanic firing logs one INFO line, "dm-pilot vancleef <mechanic> ...", in module.dungeonbosses.
 * `.dmtest vancleef <mechanic>` fires one on demand (VanCleefTestCommands below).
 */

#include "Chat.h"
#include "Creature.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "GreenskinLanes.h"
#include "HardModeLogic.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "TemporarySummon.h"
#include "VanCleefLogic.h"
#include <optional>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace VanCleef;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    enum VanCleefEvents : uint32
    {
        EVENT_AMBUSH    = 1,
        EVENT_GUNS      = 2,
    };

    enum BlackguardEvents : uint32
    {
        EVENT_CHEAP_SHOT    = 1,
        EVENT_RUPTURE       = 2,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The encounter owner for a Blackguard's Fire Bomb: VanCleef while he is alive.
    Creature* FindVanCleef(WorldObject* from)
    {
        InstanceScript* instance = from->GetInstanceScript();
        Creature* boss = instance ? instance->GetCreature(DATA_VANCLEEF_GUID) : nullptr;
        return boss && boss->IsAlive() ? boss : nullptr;
    }
}

// Edwin VanCleef 639 (hidden by the instance until Greenskin is DONE)
struct boss_edwin_vancleef_rework : public BossAI
{
    explicit boss_edwin_vancleef_rework(Creature* creature) : BossAI(creature, BOSS_EDWIN_VANCLEEF) { }

    void Reset() override
    {
        EndVanish(false);
        _Reset();
        GreenskinLanes::ForgetOwner(me);
        _stagesDone = 0;
        _plan = PlanFor(DeadminesKit::IsHeroicMap(me), false);
        OnEncounterReset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        Talk(YELL_VANCLEEF_AGGRO);

        bool const heroic = DeadminesKit::IsHeroicMap(me);
        _plan = PlanFor(heroic, instance && instance->GetData(DATA_HARD_MODE));
        _stagesDone = 0;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_EDWIN_VANCLEEF;
        Mechanic::BeginEncounter(me, options);
        Describe();

        // VC8: the stock Thrash aura comes from creature_template_addon (both difficulties); an evade can strip it.
        if (!me->HasAura(SPELL_THRASH_AURA))
            DoCastSelf(SPELL_THRASH_AURA, true);

        if (_plan.ambush)
            events.ScheduleEvent(EVENT_AMBUSH, Ms(kAmbushFirstMs));
        LOG_INFO(kLog, "dm-pilot vancleef engage heroic={} hardmode={} guns={}", heroic,
            instance ? instance->GetData(DATA_HARD_MODE) : 0, _plan.guns);
    }

    void KilledUnit(Unit* victim) override
    {
        if (victim && victim->IsPlayer())
            Talk(YELL_VANCLEEF_KILL);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        EndVanish(false);
        GreenskinLanes::ForgetOwner(me);
        LOG_INFO(kLog, "dm-pilot vancleef evade stages={}", _stagesDone);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        EndVanish(false);
        GreenskinLanes::ForgetOwner(me);
        Talk(YELL_VANCLEEF_DEATH);
        HardMode::Script::OnDied(me, _hardMode);    // B9: the instance marks the hard mode kill itself
        BossAI::JustDied(killer);
        LOG_INFO(kLog, "dm-pilot vancleef died");
    }

    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_DM_SHADOW_IMAGE)
        {
            // A look, not a combatant: never zoned into combat.
            summons.Summon(summon);
            summon->SetReactState(REACT_PASSIVE);
            return;
        }
        BossAI::JustSummoned(summon);
        if (summon->GetEntry() == NPC_DM_BLACKGUARD)
            Mechanic::TrackUnit(me, summon);
    }

    // VC9 (heroic): every Thrash proc (3391, cast on himself) stacks Expose Armor on his victim.
    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_THRASH || caster != me || !_plan.exposeArmor)
            return;
        Unit* victim = me->GetVictim();
        if (!victim)
            return;
        me->CastSpell(victim, SPELL_EXPOSE_ARMOR, true);
        Aura const* aura = victim->GetAura(SPELL_EXPOSE_ARMOR, me->GetGUID());
        LOG_INFO(kLog, "dm-pilot vancleef expose-armor target={} stacks={}", victim->GetName(),
            aura ? aura->GetStackAmount() : 0);
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_HARD_MODE_LIT:
                // B9: the keg set DATA_HARD_MODE before this; the crews abandon the guns.
                _plan = PlanFor(DeadminesKit::IsHeroicMap(me), true);
                events.CancelEvent(EVENT_GUNS);
                OnHardModeLit();
                LOG_INFO(kLog, "dm-pilot vancleef hardmode-lit guns={}", _plan.guns);
                break;
            case ACTION_HARD_MODE_RESET:
                _plan = PlanFor(DeadminesKit::IsHeroicMap(me), false);
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        // B9: the hard mode clock runs first, in the rigging too; true = the ship blew and he evaded.
        if (_hardMode.lit && HardMode::Script::Update(me, _hardMode, diff))
            return;

        // Out of combat: stock Dual Wield (SmartAI 639 cast it once out of combat).
        if (!_dualWield && me->IsInWorld())
        {
            DoCastSelf(SPELL_DUAL_WIELD, true);
            _dualWield = true;
        }

        // The Ambush drop runs out of combat too (`.dmtest vancleef ambush` on an idle VanCleef). The timers keep
        // running in the rigging, so Ambush keeps its 20 / 15 s cadence and the guns theirs; an event due meanwhile
        // waits for the loop below (it returns while he is vanished).
        bool eventsUpdated = false;
        if (_vanished)
        {
            events.Update(diff);
            eventsUpdated = true;
            if (_vanishMs > diff)
            {
                _vanishMs -= diff;
                return;
            }
            Drop();
        }

        if (!UpdateVictim())
            return;

        RunStages();

        if (!eventsUpdated)
            events.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            ExecuteEvent(eventId);
            if (_vanished || me->IsActionPreventedByCasting())
                return;
        }

        DoMeleeAttackIfReady();
    }

    void ExecuteEvent(uint32 eventId) override
    {
        switch (eventId)
        {
            case EVENT_AMBUSH:
                events.ScheduleEvent(EVENT_AMBUSH, Ms(Ambush() ? AmbushCooldownMs(_stagesDone) : kAmbushRetryMs));
                break;
            case EVENT_GUNS:
                if (_plan.guns)
                {
                    FireGuns(DeadminesKit::IsHeroicMap(me));
                    events.ScheduleEvent(EVENT_GUNS, Ms(kGunsEveryMs));
                }
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC1 / VC2 Ambush from the Rigging (public for `.dmtest vancleef`)
    // ----------------------------------------------------------------------------------------------------------------

    // One Ambush: `forced` circles at given spots (a `.dmtest` call), else 1 or 2 picked non-tanks. False when there is
    // nobody to ambush or he is already in the rigging.
    bool Ambush(std::vector<Position> const* forced = nullptr)
    {
        if (_vanished || !me->IsAlive())
            return false;
        bool const heroic = DeadminesKit::IsHeroicMap(me);

        std::vector<Position> spots;
        std::vector<ObjectGuid> marked;
        if (forced)
            spots = *forced;
        else
        {
            Unit const* tank = me->GetVictim();
            std::vector<Player*> players;
            std::vector<AmbushCandidate> candidates;
            for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            {
                Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
                if (!player || !player->IsAlive() || !player->IsInWorld() || player->IsGameMaster())
                    continue;
                candidates.push_back({ players.size(), player == tank });
                players.push_back(player);
            }
            std::vector<std::size_t> const picks = PickAmbushTargets(candidates, AmbushCircles(_stagesDone),
                [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
            for (std::size_t index : picks)
            {
                spots.push_back(players[index]->GetPosition());
                marked.push_back(players[index]->GetGUID());
            }
        }
        if (spots.empty())
        {
            LOG_INFO(kLog, "dm-pilot vancleef ambush no-target");
            return false;
        }

        Talk(EMOTE_VANCLEEF_AMBUSH);
        DoCastSelf(SPELL_AMBUSH_VANISH, true);
        Vanish();

        Milliseconds const warn = Ms(kAmbushWarnMs(heroic));
        uint32 registered = 0;
        for (std::size_t i = 0; i < spots.size(); ++i)
        {
            bool const image = i > 0;
            BossMechanics::MechanicHandle const h = Mechanic::Circle(me, spots[i], kAmbushRadius, warn)
                .Damage(kAmbushPct(heroic)).Weakened().Spell(SPELL_AMBUSH_HIT)
                .Tag(image ? TAG_SHADOW_IMAGE : TAG_AMBUSH);
            registered += h.IsValid() ? 1 : 0;
        }
        _dropAt = spots.front();
        _imagesAt.assign(spots.begin() + 1, spots.end());
        _vanishMs = kAmbushWarnMs(heroic);

        LOG_INFO(kLog, "dm-pilot vancleef ambush circles={} registered={} warn={}ms forced={}", spots.size(),
            registered, _vanishMs, forced != nullptr);
        if (spots.size() > 1)
            LOG_INFO(kLog, "dm-pilot vancleef shadow-image circles={}", spots.size() - 1);
        for (ObjectGuid const& guid : marked)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                LOG_DEBUG(kLog, "dm-pilot vancleef ambush target={}", player->GetName());
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC3 The guns
    // ----------------------------------------------------------------------------------------------------------------
    void FireGuns(bool heroic)
    {
        Greenskin::LaneVolley const spec = GunsVolley(heroic);
        // Greenskin's cast bars name the volley ("Fire on My Mark" / "Crossfire"); the lanes own the hit.
        DeadminesKit::CastBar(me, heroic ? Greenskin::SPELL_CROSSFIRE_CAST : Greenskin::SPELL_FIRE_ON_MY_MARK_CAST);
        GreenskinLanes::Volley const volley = GreenskinLanes::Fire(me, spec);
        LOG_INFO(kLog, "dm-pilot vancleef the-guns heroic={} lanes={} across={} along={} cells={} warn={}ms", heroic,
            volley.Lanes(), volley.across.size(), volley.along.size(), volley.cells.size(), spec.warnMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC4 The Brotherhood
    // ----------------------------------------------------------------------------------------------------------------
    void Brotherhood()
    {
        Talk(EMOTE_VANCLEEF_ALLIES);
        uint32 summoned = 0;
        for (Vec2 const& spot : BlackguardSpots({ me->GetPositionX(), me->GetPositionY() }, me->GetOrientation()))
        {
            float z = me->GetPositionZ();
            me->UpdateAllowedPositionZ(spot.x, spot.y, z);
            if (me->SummonCreature(NPC_DM_BLACKGUARD, spot.x, spot.y, z, me->GetOrientation(),
                TEMPSUMMON_TIMED_DESPAWN, kBlackguardLifeMs))
                ++summoned;
        }
        LOG_INFO(kLog, "dm-pilot vancleef brotherhood blackguards={}", summoned);
    }

    // VC7 (heroic): a Blackguard died at `at` (npc_dm_blackguard::JustDied).
    void FireBomb(Position const& at)
    {
        DeadminesKit::LingerSpec linger;
        linger.duration = Ms(kFireBombMs);
        linger.tick = Ms(kFireBombTickMs);
        linger.pct = kFireBombPct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_FIRE_BOMB_TICK;
        linger.slow = false;                    // DM: "no slow"
        linger.tag = TAG_FIRE_BOMB;
        BossMechanics::MechanicHandle const h =
            DeadminesKit::Linger(me, BossMechanics::Shapes::Circle(at, kFireBombRadius), linger);
        LOG_INFO(kLog, "dm-pilot vancleef fire-bomb at={:.1f},{:.1f} registered={}", at.GetPositionX(),
            at.GetPositionY(), h.IsValid());
    }

    Plan const& CurrentPlan() const { return _plan; }
    HardMode::State& HardModeState() { return _hardMode; }

private:
    // Kill order: the Blackguards first while they live, then VanCleef (the boss rule). No interrupts, dispels or
    // purges (DM "Boss data").
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_DM_BLACKGUARD, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // The yard answers (stages reached and not done, in order).
    void RunStages()
    {
        if (_vanished)
            return;
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        for (Stage stage : NewStages(_stagesDone, me->GetHealthPct(), heroic))
        {
            _stagesDone |= stage;
            switch (stage)
            {
                case STAGE_GUNS:
                    Talk(YELL_VANCLEEF_GUNS);
                    LOG_INFO(kLog, "dm-pilot vancleef stage guns pct={:.0f} plan={}", me->GetHealthPct(), _plan.guns);
                    if (_plan.guns)
                        events.ScheduleEvent(EVENT_GUNS, Ms(0));
                    break;
                case STAGE_BROTHERHOOD:
                    if (_plan.brotherhood)
                        Brotherhood();
                    break;
                case STAGE_IMAGE:
                    LOG_INFO(kLog, "dm-pilot vancleef stage shadow-image pct={:.0f}", me->GetHealthPct());
                    break;
                case STAGE_RIGHTEOUS:
                    Talk(YELL_VANCLEEF_IMAGE);
                    LOG_INFO(kLog, "dm-pilot vancleef stage righteous pct={:.0f} ambush-every={}ms",
                        me->GetHealthPct(), AmbushCooldownMs(_stagesDone));
                    break;
                default:
                    break;
            }
        }
    }

    // DI-8 (section 7 #12, a ruling): untargetable for the 2 s, threat kept.
    void Vanish()
    {
        me->InterruptNonMeleeSpells(false);     // a gun cast bar (`.dmtest`): its lanes are registered already
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
        me->SetVisible(false);
        _vanished = true;
    }

    // Undo the vanish (only what Vanish did). `dropped`: he lands at _dropAt.
    void EndVanish(bool dropped)
    {
        if (!_vanished)
            return;
        _vanished = false;
        _vanishMs = 0;
        if (dropped)
        {
            Unit* victim = me->GetVictim() ? me->GetVictim() : me->SelectVictim();
            float const facing = victim ? _dropAt.GetAbsoluteAngle(victim) : me->GetOrientation();
            me->NearTeleportTo(_dropAt.GetPositionX(), _dropAt.GetPositionY(), _dropAt.GetPositionZ(), facing);
        }
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
        me->SetVisible(true);
    }

    // The 2 s are up: he lands on the first circle, his image on the others; back to the tank.
    void Drop()
    {
        EndVanish(true);
        DoCastSelf(SPELL_AMBUSH_STRIKE, true);
        uint32 images = 0;
        for (Position const& at : _imagesAt)
        {
            if (TempSummon* image = me->SummonCreature(NPC_DM_SHADOW_IMAGE, at, TEMPSUMMON_TIMED_DESPAWN,
                kShadowImageLifeMs))
            {
                image->CastSpell(image, SPELL_SHADOW_IMAGE_VISUAL, true);
                image->CastSpell(image, SPELL_AMBUSH_STRIKE, true);
                ++images;
            }
        }
        _imagesAt.clear();
        LOG_INFO(kLog, "dm-pilot vancleef ambush drop at={:.1f},{:.1f} images={}", _dropAt.GetPositionX(),
            _dropAt.GetPositionY(), images);

        if (me->IsEngaged())
        {
            if (Unit* victim = me->SelectVictim())
                AttackStart(victim);
        }
        else
            me->GetMotionMaster()->MoveTargetedHome();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Hard mode hooks (B9: vancleef_hard_mode.cpp, HardMode::Script in HardModeLogic.h). The keg (go_dm_powder_keg)
    // calls HardMode::Script::Light: instance->SetData(DATA_HARD_MODE, 1), engage the user (JustEngagedWith reads the
    // flag: PlanFor(heroic, true), no gun lanes), then DoAction(ACTION_HARD_MODE_LIT):
    //   OnHardModeLit()     500k, yell 7, the clock aura, the 3:00 clock (_hardMode; ticked first thing in UpdateAI:
    //                       fire front, powder, mast, yell 9, the explosion, which evades him).
    //   OnEncounterReset()  (Reset: evade, wipe, the explosion) his health back (340k), DATA_HARD_MODE 0, the keg
    //                       re-armed, the burning looks and the mast gone.
    //   JustDied            HardMode::Script::OnDied: the looks and the clock auras go (the kill flag is the
    //                       instance's).
    // ----------------------------------------------------------------------------------------------------------------
    void OnHardModeLit() { HardMode::Script::OnLit(me, _hardMode); }
    void OnEncounterReset() { HardMode::Script::OnReset(me, _hardMode); }

    HardMode::State _hardMode;

    Plan _plan;
    uint32 _stagesDone = 0;
    bool _vanished = false;
    uint32 _vanishMs = 0;
    bool _dualWield = false;
    Position _dropAt;
    std::vector<Position> _imagesAt;
};

// B9 (HardModeLogic.h): the hard mode run of a VanCleef running this AI.
HardMode::State* HardMode::Script::StateOf(Creature* vanCleef)
{
    auto* ai = vanCleef && vanCleef->IsAIEnabled ? dynamic_cast<boss_edwin_vancleef_rework*>(vanCleef->AI()) : nullptr;
    return ai ? &ai->HardModeState() : nullptr;
}

// boss-kit Blackguard 300426 (summoned at 50%): Cheap Shot opener (2 s), Rupture on the victim, Fire Bomb on death
// (heroic). Stock SmartAI 636 mirrored (Cheap Shot on aggro, Rupture 3-10 s then 10-15 s); no stealth (summoned in the
// open), so Cheap Shot (stock: stealth only) is cast triggered.
struct npc_dm_blackguard : public ScriptedAI
{
    explicit npc_dm_blackguard(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _events.Reset();
        _openerMs = 0;
        _opened = false;
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _events.ScheduleEvent(EVENT_CHEAP_SHOT, Ms(0));
        _events.ScheduleEvent(EVENT_RUPTURE, Ms(kRuptureFirstMinMs), Ms(kRuptureFirstMaxMs));
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_CHEAP_SHOT && target)
            DeadminesKit::ShortenAura(target, SPELL_CHEAP_SHOT, me->GetGUID(), Ms(kCheapShotMs));
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (!DeadminesKit::IsHeroicMap(me))
            return;
        Creature* boss = FindVanCleef(me);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_edwin_vancleef_rework*>(boss->AI()) : nullptr;
        if (!ai || !ai->CurrentPlan().fireBomb)
            return;
        // The patch's look from the corpse (triggered: a dead caster may cast it), the registry patch on VanCleef's
        // encounter.
        me->CastSpell(me, SPELL_FIRE_BOMB_GROUND, true);
        ai->FireBomb(me->GetPosition());
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        _events.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;

        while (uint32 const eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_CHEAP_SHOT:
                    CheapShot();
                    break;
                case EVENT_RUPTURE:
                    if (Unit* victim = me->GetVictim())
                    {
                        DoCast(victim, SPELL_RUPTURE);
                        LOG_INFO(kLog, "dm-pilot vancleef rupture target={}", victim->GetName());
                    }
                    _events.ScheduleEvent(EVENT_RUPTURE, Ms(kRuptureMinMs), Ms(kRuptureMaxMs));
                    break;
                default:
                    break;
            }
            if (me->IsActionPreventedByCasting())
                return;
        }

        DoMeleeAttackIfReady();
    }

    // VC5: once, on the first target, as soon as it is in melee range (given up after 10 s).
    void CheapShot()
    {
        if (_opened)
            return;
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim))
        {
            _opened = true;
            me->CastSpell(victim, SPELL_CHEAP_SHOT, true);
            LOG_INFO(kLog, "dm-pilot vancleef cheap-shot target={} stun={}ms", victim->GetName(), kCheapShotMs);
            return;
        }
        _openerMs += kCheapShotPollMs;
        if (_openerMs < kCheapShotGiveUpMs)
            _events.ScheduleEvent(EVENT_CHEAP_SHOT, Ms(kCheapShotPollMs));
    }

    void ForceCheapShot(Unit* target)
    {
        if (!target)
            return;
        me->CastSpell(target, SPELL_CHEAP_SHOT, true);
        LOG_INFO(kLog, "dm-pilot vancleef cheap-shot target={} stun={}ms (dmtest)", target->GetName(), kCheapShotMs);
    }

private:
    EventMap _events;
    uint32 _openerMs = 0;
    bool _opened = false;
};

// shadow image 300427 (VC2): summoned at the landing, shows the image look and strike, fades (timed despawn). The
// registry circle owns the hit; the image never fights.
struct npc_dm_shadow_image : public ScriptedAI
{
    explicit npc_dm_shadow_image(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void UpdateAI(uint32 /*diff*/) override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
};

namespace
{
    // `.dmtest vancleef <mechanic>`: the GM (`.gm off` to be hit) is the target; VanCleef is the selected one, else
    // the nearest within 200 yd. A hidden VanCleef (Greenskin alive) is found too: hand-testing is a GM's call.
    boss_edwin_vancleef_rework* FindVanCleefAI(ChatHandler* handler)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_EDWIN_VANCLEEF);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_edwin_vancleef_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Edwin VanCleef does not run boss_edwin_vancleef_rework.");
        return ai;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_EDWIN_VANCLEEF, BOSS_EDWIN_VANCLEEF);
    }

    bool HandleAmbush(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        std::vector<Position> const spots{ handler->GetPlayer()->GetPosition() };
        if (!ai->Ambush(&spots))
        {
            handler->SendErrorMessage("Ambush did not start (he is already in the rigging).");
            return false;
        }
        handler->SendSysMessage("Ambush: a 5 yd circle at your feet, 2 s; he drops onto it.");
        return true;
    }

    bool HandleImage(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        Player* gm = handler->GetPlayer();
        std::vector<Position> const spots{ gm->GetPosition(), gm->GetNearPosition(8.f, 0.f) };
        if (!ai->Ambush(&spots))
        {
            handler->SendErrorMessage("Ambush did not start (he is already in the rigging).");
            return false;
        }
        handler->SendSysMessage("Shadow image: circles at your feet (VanCleef) and 8 yd ahead (the image), 2 s.");
        return true;
    }

    bool HandleGuns(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        ai->FireGuns(false);
        handler->SendSysMessage("The guns (normal): 3 lanes rail to rail on the deck frame, 2 s.");
        return true;
    }

    bool HandleCrossfire(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        ai->FireGuns(true);
        handler->SendSysMessage("The guns (heroic): 4 lanes across + 2 along, 2.5 s, 8 burning crossings for 20 s.");
        return true;
    }

    bool HandleBrotherhood(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        ai->Brotherhood();
        handler->SendSysMessage("The Brotherhood: two Blackguards beside him (300 s).");
        return true;
    }

    bool HandleFireBomb(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        ai->FireBomb(handler->GetPlayer()->GetPosition());
        handler->SendSysMessage("Fire Bomb: a 6 yd burning patch at your feet, 15 s (the registry patch only).");
        return true;
    }

    bool HandleExposeArmor(ChatHandler* handler)
    {
        boss_edwin_vancleef_rework* ai = FindVanCleefAI(handler);
        if (!ai)
            return false;
        Player* gm = handler->GetPlayer();
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_EDWIN_VANCLEEF);
        if (!boss)
            return false;
        boss->CastSpell(gm, SPELL_EXPOSE_ARMOR, true);
        Aura const* aura = gm->GetAura(SPELL_EXPOSE_ARMOR, boss->GetGUID());
        LOG_INFO(kLog, "dm-pilot vancleef expose-armor target={} stacks={} (dmtest)", gm->GetName(),
            aura ? aura->GetStackAmount() : 0);
        handler->PSendSysMessage("Expose Armor: {} stack(s) on you.", aura ? aura->GetStackAmount() : 0);
        return true;
    }

    bool HandleCheapShot(ChatHandler* handler)
    {
        Creature* blackguard = DeadminesTest::FindBoss(handler, NPC_DM_BLACKGUARD);
        if (!blackguard)
            return false;
        auto* ai = blackguard->IsAIEnabled ? dynamic_cast<npc_dm_blackguard*>(blackguard->AI()) : nullptr;
        if (!ai)
        {
            handler->SendErrorMessage("The Blackguard does not run npc_dm_blackguard.");
            return false;
        }
        ai->ForceCheapShot(handler->GetPlayer());
        handler->SendSysMessage("Cheap Shot: stock 1833 on you, stun cut to 2 s (stand within 5 yd, .gm off).");
        return true;
    }

    ChatCommandTable const& VanCleefTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "ambush",      HandleAmbush,      SEC_GAMEMASTER, Console::No },
            { "image",       HandleImage,       SEC_GAMEMASTER, Console::No },
            { "guns",        HandleGuns,        SEC_GAMEMASTER, Console::No },
            { "crossfire",   HandleCrossfire,   SEC_GAMEMASTER, Console::No },
            { "brotherhood", HandleBrotherhood, SEC_GAMEMASTER, Console::No },
            { "firebomb",    HandleFireBomb,    SEC_GAMEMASTER, Console::No },
            { "exposearmor", HandleExposeArmor, SEC_GAMEMASTER, Console::No },
            { "cheapshot",   HandleCheapShot,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_edwin_vancleef_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_edwin_vancleef_rework);
    RegisterDeadminesReworkCreatureAI(npc_dm_blackguard);
    RegisterDeadminesReworkCreatureAI(npc_dm_shadow_image);
    DeadminesTest::RegisterBoss("vancleef", VanCleefTestCommands());
}
