/*
 * mod-dungeon-bosses, Deadmines: Rhahk'Zor, the Watchman and the Evoker (WP-B1). Build spec: DM 'Rhahk'Zor' Build spec
 * RZ1-RZ10; handoff section 3.4 rows RZ and section 3.5 row B1. Replaces Rhahk'Zor's SmartAI (644) and, on the two
 * spawns beside him (79165 Watchman, 79167 Evoker), the stock 1725 / 1729 SmartAI (WP-B1's SQL rev repoints them).
 *
 * Rhahk'Zor (normal and heroic):
 *   RZ1 Cave In       every 15 s from 8 s: a 2 s registry circle (5 yd, 20%, Weakened) under one random non-tank;
 *                     heroic: under every player plus 5 random spots >= 6 yd from every player, each leaving
 *                     RZ3 Rubble (DeadminesKit::ImpactThenLinger: 10 s, 1 s ticks, 5%, the "Standing in It" slow).
 *                     A player is hit once per wave (WaveLedger + spell_dm_rhahkzor_cave_in).
 *   RZ2 Tremor        as a wave lands: 5% Physical to every player (205211, RefFlat).
 *   RZ4 Whirlwind     every 40 s from 20 s: 2 s cast bar, then a 4 s spin (rooted, no swings); a registry circle
 *                     (8 yd) on him, 1 s ticks of 15%, Weakened on a player's first tick; heroic ticks knock back.
 *   RZ5 Slam          every 50 s from 10 s: stock 6304 on the tank, its stun cut to 1.5 s (handoff section 7 #3).
 *   RZ10 Lookout      heroic, while the Watchman lives: as the first wave lands, the Watchman calls a second wave
 *                     under every player (1.5 s, 20%, Weakened, no rubble) and marks them (Spotted).
 * The Evoker: RZ7 Fireball filler from 2 s, RZ6 Flamestrike every 12 s from 5 s on a random player (its stock
 * burning ground registered as a bot-only persistent zone), heroic RZ8 Fireball Volley every 14 s from 8 s (40%, the
 * expected interrupt), Quick Flame Ward on the stock timing, Frost Armor out of combat; no flee.
 * The Watchman: Shoot at 5 to 30 yd every 2 s (stock).
 * Descriptor: kill order Evoker, Watchman, Rhahk'Zor; interrupts Fireball Volley > Fireball; purge Quick Flame Ward.
 *
 * Every mechanic firing logs one INFO line, "dm-pilot rhahkzor <mechanic> ...", in category module.dungeonbosses.
 * `.dmtest rhahkzor <mechanic>` fires one on demand (see RhahkZorTestCommands below).
 *
 * The stock behavior kept: the patrol (creature_addon path 791680), the aggro yell, the Factory Door and the boss
 * state on death (the instance's door data opens the door on DONE). Stock SmartAI rows mirrored here (AzerothCore
 * world DB): 644 (yell, Slam, door, instance data), 1725 (Shoot), 1729 (Frost Armor, Flamestrike, Quick Flame Ward).
 */

#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "RhahkZorLogic.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <list>
#include <optional>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace RhahkZor;

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";
    float constexpr kAddSearchRange = 60.f;
    float constexpr kEvokerCastRange = 40.f;

    Vec2 ToVec2(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    // Every player of the fight: alive, in the world, not a GM, within kRoomRange of `center`; plus `forced` (a
    // `.dmtest` caller) when given.
    std::vector<Player*> RoomPlayers(Creature* center, Player* forced = nullptr)
    {
        std::vector<Player*> out;
        for (auto const& ref : center->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsInWorld() || !p->IsAlive() || p->IsGameMaster() || p->GetDistance(center) > kRoomRange)
                continue;
            out.push_back(p);
        }
        if (forced && forced->IsAlive() && std::find(out.begin(), out.end(), forced) == out.end())
            out.push_back(forced);
        return out;
    }

    Ms RandomMs(Ms min, Ms max)
    {
        return Ms(urand(static_cast<uint32>(min.count()), static_cast<uint32>(max.count())));
    }

    Creature* FindRhahkZor(Creature* add)
    {
        InstanceScript* instance = add->GetInstanceScript();
        return instance ? instance->GetCreature(DATA_RHAHKZOR_GUID) : nullptr;
    }

    // The registry encounter's owner for an add's own zone: the boss while he is alive, else the add itself.
    Unit* EncounterOwner(Creature* add)
    {
        if (Creature* boss = FindRhahkZor(add); boss && boss->IsAlive())
            return boss;
        return add;
    }

    // An add pulled on its own pulls Rhahk'Zor (who pulls the other add).
    void PullBoss(Creature* add, Unit* who)
    {
        Creature* boss = FindRhahkZor(add);
        if (boss && boss->IsAlive() && !boss->IsInCombat() && who && boss->IsAIEnabled)
            boss->AI()->AttackStart(who);
    }
}

// Rhahk'Zor 644
struct boss_rhahk_zor_rework : public BossAI
{
    explicit boss_rhahk_zor_rework(Creature* creature) : BossAI(creature, BOSS_RHAHKZOR) { }

    void Reset() override
    {
        _Reset();
        _followups.CancelAll();
        EndSpin();
        _ledger.Clear();
        RespawnAdds();
    }

    void JustEngagedWith(Unit* who) override
    {
        _JustEngagedWith();
        Talk(SAY_RHAHKZOR_AGGRO);

        BossMechanics::EncounterOptions opt;
        opt.bossStateId = BOSS_RHAHKZOR;
        Mechanic::BeginEncounter(me, opt);
        PullAdds(who);
        DescribeEncounter();
        LOG_INFO(kLog, "dm-pilot rhahkzor engage heroic={} players={}", DeadminesKit::IsHeroicMap(me),
            RoomPlayers(me).size());
    }

    void ScheduleTasks() override
    {
        scheduler.Schedule(kCaveInFirst, [this](TaskContext ctx)
        {
            CaveIn();
            ctx.Repeat(kCaveInEvery);
        });
        scheduler.Schedule(kWhirlwindFirst, [this](TaskContext ctx)
        {
            if (Busy())
            {
                ctx.Repeat(kBusyRetry);
                return;
            }
            Whirlwind();
            ctx.Repeat(kWhirlwindEvery);
        });
        scheduler.Schedule(kSlamFirst, [this](TaskContext ctx)
        {
            if (Busy() || !Slam(me->GetVictim()))
            {
                ctx.Repeat(kBusyRetry);
                return;
            }
            ctx.Repeat(kSlamEvery);
        });
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        scheduler.CancelAll();
        _followups.CancelAll();     // runs out of combat too (UpdateAI): nothing may fire while evading
        EndSpin();
        EvadeAdds();
        _EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _followups.CancelAll();
        EndSpin();
        _JustDied();
        LOG_INFO(kLog, "dm-pilot rhahkzor died");
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (target && spell->Id == SPELL_RHAHKZOR_SLAM)
            DeadminesKit::ShortenAura(target, SPELL_RHAHKZOR_SLAM, me->GetGUID(), kSlamStun);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dmtest` mechanic's follow-ups (the landing, the spin) and its Lookout's rocks.
        _followups.Update(diff);
        scheduler.Update(diff);

        if (!UpdateVictim())
            return;

        if (me->IsActionPreventedByCasting() || _spinning)
            return;

        DoMeleeAttackIfReady();
    }

    // ---- mechanics (also called by `.dmtest`) ---------------------------------------------------------------------

    // RZ1 (+ RZ3 heroic): one wave. `forced` (a `.dmtest` caller) is the normal target and joins the heroic list.
    void CaveIn(Player* forced = nullptr)
    {
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        std::vector<Player*> const players = RoomPlayers(me, forced);

        std::vector<Position> spots;
        if (heroic)
        {
            for (Player* p : players)
                spots.push_back(p->GetPosition());
        }
        else if (Unit* target = NormalTarget(forced, players))
            spots.push_back(target->GetPosition());

        std::size_t const playerCircles = spots.size();
        std::vector<Position> const random = RandomSpots(kRandomCircles(heroic), players);
        spots.insert(spots.end(), random.begin(), random.end());
        if (spots.empty())
        {
            LOG_INFO(kLog, "dm-pilot rhahkzor cavein skipped (no player)");
            return;
        }

        Talk(EMOTE_RHAHKZOR_CAVE_IN);
        std::uint32_t const wave = _ledger.BeginWave();
        for (Position const& at : spots)
            _ledger.Assign(CaveInCircle(at, heroic).id, wave);

        std::size_t const rubble = RubbleCount(heroic, playerCircles, random.size(), false);
        LOG_INFO(kLog, "dm-pilot rhahkzor cavein wave={} heroic={} players={} circles={} random={} rubble={}", wave,
            heroic, players.size(), spots.size(), random.size(), rubble);

        ObjectGuid const forcedGuid = forced ? forced->GetGUID() : ObjectGuid::Empty;
        _followups.Schedule(kCaveInWarn, [this, spots, heroic, rubble, forcedGuid](TaskContext)
        {
            CaveInLands(spots, heroic, rubble, forcedGuid);
        });
    }

    // RZ10: the Watchman's second wave under every player where they stand now. `watchman` may be null (`.dmtest`
    // without a Watchman: no emote and no marks).
    void Lookout(Creature* watchman, Player* forced = nullptr)
    {
        std::vector<Player*> const players = RoomPlayers(me, forced);
        if (players.empty())
            return;

        if (watchman && watchman->IsAIEnabled)
            watchman->AI()->Talk(EMOTE_WATCHMAN_LOOKOUT);

        bool const heroic = DeadminesKit::IsHeroicMap(me);
        std::uint32_t const wave = _ledger.BeginWave();
        std::vector<Position> spots;
        for (Player* p : players)
        {
            spots.push_back(p->GetPosition());
            BossMechanics::MechanicHandle const h = Mechanic::Circle(me, p->GetPosition(), kCaveInRadius,
                kLookoutWarn).Damage(kCaveInPct(heroic)).Spell(SPELL_RZ_CAVE_IN).Weakened().Tag(TAG_LOOKOUT);
            _ledger.Assign(h.id, wave);
            if (watchman)
                watchman->CastSpell(p, SPELL_RZ_SPOTTED, true);
        }
        LOG_INFO(kLog, "dm-pilot rhahkzor lookout wave={} circles={} watchman={}", wave, spots.size(),
            watchman != nullptr);

        // Lookout runs from a _followups task (CaveInLands) or `.dmtest`, so the rocks go on m_Events: the BossAI
        // scheduler pauses while Rhahk'Zor holds a cast bar, which would show them up to 2 s after the circles land.
        me->m_Events.AddEventAtOffset([this, spots]()
        {
            if (me->IsAlive())
                Rocks(spots);
        }, kLookoutWarn);
    }

    // RZ4: the cast bar now, the spin as it ends; the registry circle on him owns the ticks.
    void Whirlwind()
    {
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        DeadminesKit::CastBar(me, SPELL_RZ_WHIRLWIND_CAST, nullptr, EMOTE_RHAHKZOR_WHIRLWIND);
        {
            BossMechanics::MechanicRef ref = Mechanic::Circle(me, me, kWhirlwindRadius, kWhirlwindCast);
            ref.Persistent(kWhirlwindSpin, kWhirlwindTick).Damage(kWhirlwindPct(heroic)).Spell(SPELL_RZ_WHIRLWIND)
                .WeakenedOncePerPlayer().Tag(TAG_WHIRLWIND);
            if (heroic)
                ref.Rider(SPELL_RZ_WHIRLWIND_KNOCKBACK);
        }   // the ref commits here
        LOG_INFO(kLog, "dm-pilot rhahkzor whirlwind heroic={} knockback={}", heroic, heroic);

        _followups.Schedule(kWhirlwindCast, [this](TaskContext)
        {
            StartSpin();
        });
        _followups.Schedule(kWhirlwindCast + kWhirlwindSpin, [this](TaskContext)
        {
            EndSpin();
        });
    }

    // RZ5: stock 6304 on `target`; SpellHitTarget cuts the stun to 1.5 s.
    bool Slam(Unit* target)
    {
        if (!target || me->CastSpell(target, SPELL_RHAHKZOR_SLAM, false) != SPELL_CAST_OK)
            return false;
        LOG_INFO(kLog, "dm-pilot rhahkzor slam target={} stun_ms={}", target->GetGUID().ToString(),
            kSlamStun.count());
        return true;
    }

    // RZ2: the room shake.
    void Tremor()
    {
        me->CastSpell(me, SPELL_RZ_CAVE_IN_TREMOR, true);
        LOG_INFO(kLog, "dm-pilot rhahkzor tremor pct={}", kTremorPct(DeadminesKit::IsHeroicMap(me)));
    }

    // spell_dm_rhahkzor_cave_in reads and writes it.
    WaveLedger& Ledger() { return _ledger; }

private:
    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _spinning;
    }

    // One RZ1 circle: normal, the plain impact; heroic, the impact plus its rubble (RZ3).
    BossMechanics::MechanicHandle CaveInCircle(Position const& at, bool heroic)
    {
        if (!heroic)
            return Mechanic::Circle(me, at, kCaveInRadius, kCaveInWarn).Damage(kCaveInPct(heroic))
                .Spell(SPELL_RZ_CAVE_IN).Weakened().Tag(TAG_CAVE_IN);

        DeadminesKit::ImpactSpec impact;
        impact.shape = BossMechanics::Shapes::Circle(at, kCaveInRadius);
        impact.warn = kCaveInWarn;
        impact.pct = kCaveInPct(heroic);
        impact.spellId = SPELL_RZ_CAVE_IN;
        impact.weakened = true;
        impact.tag = TAG_CAVE_IN;
        DeadminesKit::LingerSpec linger;
        linger.duration = kRubbleDuration;
        linger.tick = kRubbleTick;
        linger.pct = kRubblePct(heroic);
        linger.spellId = SPELL_RZ_RUBBLE;
        linger.tag = TAG_RUBBLE;
        return DeadminesKit::ImpactThenLinger(me, impact, linger);
    }

    // Normal: one random non-tank player (`forced` wins); the tank only when nobody else is there.
    Unit* NormalTarget(Player* forced, std::vector<Player*> const& players)
    {
        if (forced)
            return forced;
        if (Unit* target = SelectTarget(SelectTargetMethod::Random, 0, kRoomRange, true, false))
            return target;
        if (Unit* victim = me->GetVictim(); victim && victim->IsPlayer())
            return victim;
        return players.empty() ? nullptr : Acore::Containers::SelectRandomContainerElement(players);
    }

    // Heroic random circles: a random bearing and distance from the boss, cut at the first collision, kept >= 6 yd
    // from every player and 4 yd from each other (RhahkZor::PickRandomSpots).
    std::vector<Position> RandomSpots(std::size_t count, std::vector<Player*> const& players)
    {
        std::vector<Position> out;
        if (!count)
            return out;
        std::vector<Vec2> playerSpots;
        for (Player* p : players)
            playerSpots.push_back(ToVec2(*p));

        std::vector<Position> samples;
        auto sampler = [this, &samples]() -> std::optional<Vec2>
        {
            Position p = me->GetPosition();
            me->MovePositionToFirstCollision(p, frand(kRandomRingMin, kRandomRingMax), frand(0.f, 2.f * float(M_PI)));
            if (me->GetExactDist2d(p) < kRandomRingMin)
                return std::nullopt;    // blocked right away
            samples.push_back(p);
            return ToVec2(p);
        };
        std::vector<Vec2> const picked = PickRandomSpots(count, kRandomTries, sampler, playerSpots,
            kRandomMinFromPlayer, kRandomMinApart);
        for (Vec2 const& v : picked)
            for (Position const& s : samples)
                if (s.GetPositionX() == v.x && s.GetPositionY() == v.y)
                {
                    out.push_back(s);
                    break;
                }
        return out;
    }

    void CaveInLands(std::vector<Position> const& spots, bool heroic, std::size_t rubble, ObjectGuid forcedGuid)
    {
        Rocks(spots);
        Tremor();
        if (rubble)
            LOG_INFO(kLog, "dm-pilot rhahkzor rubble patches={} duration_ms={}", rubble, kRubbleDuration.count());

        Creature* watchman = Watchman();
        if (LookoutFollows(heroic, watchman != nullptr))
            Lookout(watchman, forcedGuid.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, forcedGuid));
    }

    // The falling rocks look at every landed circle (205212, a 2 s dynamic object).
    void Rocks(std::vector<Position> const& spots)
    {
        for (Position const& at : spots)
            me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_RZ_CAVE_IN_ROCKS, true);
    }

    void StartSpin()
    {
        if (!me->IsAlive())
            return;
        me->CastSpell(me, SPELL_RZ_WHIRLWIND_SPIN, true);
        me->SetControlled(true, UNIT_STATE_ROOT);
        _spinning = true;
        LOG_INFO(kLog, "dm-pilot rhahkzor whirlwind-spin duration_ms={}", kWhirlwindSpin.count());
    }

    void EndSpin()
    {
        if (!_spinning)
            return;
        _spinning = false;
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->RemoveAurasDueToSpell(SPELL_RZ_WHIRLWIND_SPIN);
    }

    // ---- the boss-kit adds ----------------------------------------------------------------------------------------

    std::list<Creature*> Adds() const
    {
        std::list<Creature*> adds;
        me->GetCreatureListWithEntryInGrid(adds, std::vector<uint32>{ NPC_DM_WATCHMAN, NPC_DM_EVOKER },
            kAddSearchRange);
        return adds;
    }

    Creature* Watchman() const
    {
        Creature* watchman = _watchmanGuid ? ObjectAccessor::GetCreature(*me, _watchmanGuid) : nullptr;
        if (!watchman)
            for (Creature* add : Adds())
                if (add->GetEntry() == NPC_DM_WATCHMAN && add->IsAlive())
                {
                    watchman = add;
                    break;
                }
        return watchman && watchman->IsAlive() && watchman->IsInWorld() ? watchman : nullptr;
    }

    void PullAdds(Unit* who)
    {
        Unit* target = who ? who : me->GetVictim();
        for (Creature* add : Adds())
        {
            if (!add->IsAlive())
                continue;
            if (add->GetEntry() == NPC_DM_WATCHMAN)
                _watchmanGuid = add->GetGUID();
            Mechanic::TrackUnit(me, add);
            if (target && !add->IsInCombat() && add->IsAIEnabled)
                add->AI()->AttackStart(target);
        }
    }

    void EvadeAdds()
    {
        for (Creature* add : Adds())
            if (add->IsAlive() && add->IsInCombat() && add->IsAIEnabled)
                add->AI()->EnterEvadeMode();
    }

    // A wipe brings back the adds the group killed (until Rhahk'Zor is DONE).
    void RespawnAdds()
    {
        if (instance && instance->GetBossState(BOSS_RHAHKZOR) == DONE)
            return;
        for (Creature* add : Adds())
            if (!add->IsAlive())
                add->Respawn(true);
    }

    // Kill order Evoker, Watchman, Rhahk'Zor (DM, approved); interrupts Fireball Volley before Fireball; purge Quick
    // Flame Ward (handoff section 3.4).
    void DescribeEncounter()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_DM_EVOKER, 2);
        d.targets.emplace_back(NPC_DM_WATCHMAN, 1);
        d.interrupts.emplace_back(NPC_DM_EVOKER, SPELL_RZ_FIREBALL_VOLLEY, 2, kVolleyEvery);
        d.interrupts.emplace_back(NPC_DM_EVOKER, SPELL_FIREBALL, 1);
        d.purges.emplace_back(NPC_DM_EVOKER, SPELL_QUICK_FLAME_WARD, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // Follow-ups of a mechanic (a wave landing, the spin). A TaskScheduler must not be scheduled into from inside its
    // own task (TaskScheduler.h): CaveIn and Whirlwind run from `scheduler` tasks and schedule here; Lookout runs from
    // a task here (CaveInLands) and schedules into `scheduler`.
    TaskScheduler _followups;
    WaveLedger _ledger;
    ObjectGuid _watchmanGuid;
    bool _spinning = false;
};

// boss-kit Watchman 300420 (replaces spawn 79165): stock 1725's Shoot; Lookout is the boss's (RZ10).
struct npc_dm_watchman : public ScriptedAI
{
    explicit npc_dm_watchman(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        scheduler.CancelAll();
    }

    void JustEngagedWith(Unit* who) override
    {
        PullBoss(me, who);
        scheduler.Schedule(kShootEvery, [this](TaskContext ctx)
        {
            Unit* victim = me->GetVictim();
            if (victim && !me->HasUnitState(UNIT_STATE_CASTING) && ShootInRange(me->GetDistance(victim)))
                DoCastVictim(SPELL_SHOOT);
            ctx.Repeat(kShootEvery);
        });
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        scheduler.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;
        DoMeleeAttackIfReady();
    }
};

// boss-kit Evoker 300421 (replaces spawn 79167): RZ6 Flamestrike, RZ7 Fireball, RZ8 Fireball Volley (heroic), Quick
// Flame Ward, Frost Armor; no flee.
struct npc_dm_evoker : public ScriptedAI
{
    explicit npc_dm_evoker(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        scheduler.CancelAll();
        _clock = Ms(0);
        _pendingFlame.reset();
        if (me->IsAlive() && !me->HasAura(SPELL_FROST_ARMOR))
            me->CastSpell(me, SPELL_FROST_ARMOR, true);     // stock: out of combat, kept as a visual
    }

    void JustEngagedWith(Unit* who) override
    {
        PullBoss(me, who);
        _clock = Ms(0);
        _nextFireball = kFireballFirst;
        _nextFlamestrike = kFlamestrikeFirst;
        _nextVolley = kVolleyFirst;
        if (DeadminesKit::IsHeroicMap(me))
            Mechanic::NoteNextCastIn(me, SPELL_RZ_FIREBALL_VOLLEY, kVolleyFirst);
        scheduler.Schedule(RandomMs(kWardFirstMin, kWardFirstMax), [this](TaskContext ctx)
        {
            if (me->HasUnitState(UNIT_STATE_CASTING))
            {
                ctx.Repeat(kBusyRetry);
                return;
            }
            QuickFlameWard();
            ctx.Repeat(RandomMs(kWardEveryMin, kWardEveryMax));
        });
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_FLAMESTRIKE && _pendingFlame)
        {
            // The stock dynamic object burns; this zone is for the bots only (no damage, no marker).
            Mechanic::Circle(EncounterOwner(me), *_pendingFlame, kFlamestrikeRadius, Ms(0))
                .Persistent(kFlamestrikeGround, Ms(1000)).NoTelegraph().Tag(TAG_FLAMESTRIKE);
            LOG_INFO(kLog, "dm-pilot rhahkzor flamestrike-ground x={:.1f} y={:.1f} duration_ms={}",
                _pendingFlame->GetPositionX(), _pendingFlame->GetPositionY(), kFlamestrikeGround.count());
            _pendingFlame.reset();
        }
        else if (spell->Id == SPELL_RZ_FIREBALL_VOLLEY)
            LOG_INFO(kLog, "dm-pilot rhahkzor volley-landed pct={}", kVolleyPct(DeadminesKit::IsHeroicMap(me)));
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_FLAMESTRIKE)
            _pendingFlame.reset();
        else if (spell->Id == SPELL_RZ_FIREBALL_VOLLEY)
            LOG_INFO(kLog, "dm-pilot rhahkzor volley-interrupted");
        else if (spell->Id == SPELL_FIREBALL)
            LOG_INFO(kLog, "dm-pilot rhahkzor fireball-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        scheduler.Update(diff);
        _clock += Ms(diff);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        bool const heroic = DeadminesKit::IsHeroicMap(me);
        switch (NextEvokerCast(heroic && _clock >= _nextVolley, _clock >= _nextFlamestrike, _clock >= _nextFireball))
        {
            case EvokerCast::Volley:
                Volley();
                _nextVolley = _clock + kVolleyEvery;
                Mechanic::NoteNextCastIn(me, SPELL_RZ_FIREBALL_VOLLEY, kVolleyEvery);
                return;
            case EvokerCast::Flamestrike:
                _nextFlamestrike = _clock + (Flamestrike(nullptr) ? kFlamestrikeEvery : kBusyRetry);
                break;
            case EvokerCast::Fireball:
                // The filler: the next one as soon as this cast ends (the cast itself holds the loop); a failed
                // cast (range, line of sight) waits a second and he swings meanwhile.
                _nextFireball = _clock + (Fireball(nullptr) ? kBusyRetry : Ms(1000));
                break;
            case EvokerCast::None:
                break;
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- casts (also called by `.dmtest`; `forced` is the GM) -------------------------------------------------------

    // RZ8 (heroic in the fight; `.dmtest` fires it on any difficulty).
    void Volley()
    {
        RefillMana();
        DeadminesKit::CastBar(me, SPELL_RZ_FIREBALL_VOLLEY, nullptr, EMOTE_EVOKER_VOLLEY);
        LOG_INFO(kLog, "dm-pilot rhahkzor volley cast_ms=3000 pct={}", kVolleyPct(DeadminesKit::IsHeroicMap(me)));
    }

    // RZ6: stock 11829 at a random player's spot; OnSpellCast registers its burning ground.
    bool Flamestrike(Player* forced)
    {
        Unit* target = forced ? forced : SelectTarget(SelectTargetMethod::Random, 0, kEvokerCastRange, true);
        if (!target)
            return false;
        RefillMana();
        Position const at = target->GetPosition();
        if (me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_FLAMESTRIKE, false)
            != SPELL_CAST_OK)
            return false;
        _pendingFlame = at;
        LOG_INFO(kLog, "dm-pilot rhahkzor flamestrike target={}", target->GetGUID().ToString());
        return true;
    }

    // RZ7: stock 11839 on a random player.
    bool Fireball(Player* forced)
    {
        Unit* target = forced ? forced : SelectTarget(SelectTargetMethod::Random, 0, kEvokerCastRange, true);
        if (!target)
            target = me->GetVictim();
        if (!target)
            return false;
        RefillMana();
        if (me->CastSpell(target, SPELL_FIREBALL, false) != SPELL_CAST_OK)
            return false;
        LOG_INFO(kLog, "dm-pilot rhahkzor fireball target={}", target->GetGUID().ToString());
        return true;
    }

    void QuickFlameWard()
    {
        RefillMana();
        if (me->CastSpell(me, SPELL_QUICK_FLAME_WARD, false) == SPELL_CAST_OK)
            LOG_INFO(kLog, "dm-pilot rhahkzor quickflameward");
    }

private:
    // The Evoker casts back to back for the whole fight; a level 19 mage's mana would run dry in about 25 s, so every
    // cast starts full (the stock casts keep their ids and costs).
    void RefillMana()
    {
        me->SetPower(POWER_MANA, me->GetMaxPower(POWER_MANA));
    }

    Ms _clock{ 0 };
    Ms _nextFireball{ 0 };
    Ms _nextFlamestrike{ 0 };
    Ms _nextVolley{ 0 };
    std::optional<Position> _pendingFlame;
};

// RZ1 / RZ10 (205210, beside spell_boss_mechanics_resolve): a player is hit once per wave, however many circles of
// that wave they stand in (DM RZ1). The two scripts only ever remove targets, so their order does not matter; every
// circle of a wave resolves in the same registry tick and an instant triggered resolve lands at once, so the ledger
// knows the earlier circles' hits when the next one filters.
class spell_dm_rhahkzor_cave_in : public SpellScript
{
    PrepareSpellScript(spell_dm_rhahkzor_cave_in);

    boss_rhahk_zor_rework* Boss()
    {
        Unit* owner = GetOriginalCaster();
        Creature* creature = owner ? owner->ToCreature() : nullptr;
        return creature && creature->IsAIEnabled ? dynamic_cast<boss_rhahk_zor_rework*>(creature->AI()) : nullptr;
    }

    uint32 MechanicId()
    {
        SpellValue const* value = GetSpellValue();
        return value ? value->MiscVal[0] : 0;
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        boss_rhahk_zor_rework* boss = Boss();
        uint32 const id = MechanicId();
        if (!boss || !id)
            return;
        WaveLedger const& ledger = boss->Ledger();
        targets.remove_if([&ledger, id](WorldObject const* target)
        {
            return !ledger.MayHit(id, target->GetGUID().GetRawValue());
        });
    }

    void NoteHit()
    {
        boss_rhahk_zor_rework* boss = Boss();
        Unit* target = GetHitUnit();
        if (boss && target)
            boss->Ledger().NoteHit(MechanicId(), target->GetGUID().GetRawValue());
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dm_rhahkzor_cave_in::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        AfterHit += SpellHitFn(spell_dm_rhahkzor_cave_in::NoteHit);
    }
};

// RZ2 Cave In Tremor 205211 and RZ8 Fireball Volley 205219: players only, the damage is a percent of the reference row
// (DeadminesKit::RefFlat; both spells ignore caster modifiers, so the number is exact before mitigation).
class spell_dm_rhahkzor_ref_flat : public SpellScript
{
    PrepareSpellScript(spell_dm_rhahkzor_ref_flat);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject const* target) { return !target->IsPlayer(); });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        bool const heroic = DeadminesKit::IsHeroicMap(caster);
        float const pct = GetSpellInfo()->Id == SPELL_RZ_FIREBALL_VOLLEY ? kVolleyPct(heroic) : kTremorPct(heroic);
        SetEffectValue(static_cast<int32>(DeadminesKit::RefFlat(caster, pct)));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dm_rhahkzor_ref_flat::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_dm_rhahkzor_ref_flat::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    // `.dmtest rhahkzor <mechanic>`: the GM (`.gm off` to be hit) is the target or the forced player; Rhahk'Zor, the
    // Evoker or the Watchman is the selected creature of that entry, else the nearest within 200 yd.
    template <class AI>
    AI* FindAI(ChatHandler* handler, uint32 entry, Creature*& creature)
    {
        creature = DeadminesTest::FindBoss(handler, entry);
        if (!creature)
            return nullptr;
        AI* ai = creature->IsAIEnabled ? dynamic_cast<AI*>(creature->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Creature {} does not run the Deadmines rework script.", entry);
        return ai;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_RHAHKZOR, BOSS_RHAHKZOR);
    }

    bool HandleCaveIn(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_rhahk_zor_rework* ai = FindAI<boss_rhahk_zor_rework>(handler, NPC_RHAHKZOR, boss);
        if (!ai)
            return false;
        ai->CaveIn(handler->GetPlayer());
        handler->SendSysMessage("Cave In: one wave (normal: on you; heroic: every player and 5 random spots), "
            "landing in 2 s (tremor, rubble on heroic, Lookout when a Watchman lives).");
        return true;
    }

    bool HandleLookout(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_rhahk_zor_rework* ai = FindAI<boss_rhahk_zor_rework>(handler, NPC_RHAHKZOR, boss);
        if (!ai)
            return false;
        Creature* watchman = boss->FindNearestCreature(NPC_DM_WATCHMAN, 100.f, true);
        ai->Lookout(watchman, handler->GetPlayer());
        handler->PSendSysMessage("Lookout: a 1.5 s circle under every player{}.", watchman ? ", Spotted marks" :
            " (no Watchman alive: no emote, no marks)");
        return true;
    }

    bool HandleRubble(ChatHandler* handler)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_RHAHKZOR);
        if (!boss)
            return false;
        DeadminesKit::LingerSpec linger;
        linger.duration = kRubbleDuration;
        linger.tick = kRubbleTick;
        linger.pct = kRubblePct(DeadminesKit::IsHeroicMap(boss));
        linger.spellId = SPELL_RZ_RUBBLE;
        linger.tag = TAG_RUBBLE;
        DeadminesKit::Linger(boss, BossMechanics::Shapes::Circle(handler->GetPlayer()->GetPosition(), kCaveInRadius),
            linger);
        LOG_INFO(kLog, "dm-pilot rhahkzor rubble patches=1 duration_ms={} (dmtest)", kRubbleDuration.count());
        handler->SendSysMessage("Rubble: one 5 yd patch at your feet for 10 s.");
        return true;
    }

    bool HandleTremor(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_rhahk_zor_rework* ai = FindAI<boss_rhahk_zor_rework>(handler, NPC_RHAHKZOR, boss);
        if (!ai)
            return false;
        ai->Tremor();
        return true;
    }

    bool HandleWhirlwind(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_rhahk_zor_rework* ai = FindAI<boss_rhahk_zor_rework>(handler, NPC_RHAHKZOR, boss);
        if (!ai)
            return false;
        ai->Whirlwind();
        handler->SendSysMessage("Whirlwind: 2 s cast, then a 4 s spin; 8 yd circle on him (heroic: knockback).");
        return true;
    }

    bool HandleSlam(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_rhahk_zor_rework* ai = FindAI<boss_rhahk_zor_rework>(handler, NPC_RHAHKZOR, boss);
        if (!ai)
            return false;
        if (!ai->Slam(handler->GetPlayer()))
        {
            handler->SendErrorMessage("Slam did not cast (stand in melee range, .gm off).");
            return false;
        }
        return true;
    }

    bool HandleVolley(ChatHandler* handler)
    {
        Creature* evoker = nullptr;
        npc_dm_evoker* ai = FindAI<npc_dm_evoker>(handler, NPC_DM_EVOKER, evoker);
        if (!ai)
            return false;
        ai->Volley();
        return true;
    }

    bool HandleFlamestrike(ChatHandler* handler)
    {
        Creature* evoker = nullptr;
        npc_dm_evoker* ai = FindAI<npc_dm_evoker>(handler, NPC_DM_EVOKER, evoker);
        if (!ai)
            return false;
        if (!ai->Flamestrike(handler->GetPlayer()))
        {
            handler->SendErrorMessage("Flamestrike did not cast.");
            return false;
        }
        return true;
    }

    bool HandleFireball(ChatHandler* handler)
    {
        Creature* evoker = nullptr;
        npc_dm_evoker* ai = FindAI<npc_dm_evoker>(handler, NPC_DM_EVOKER, evoker);
        if (!ai)
            return false;
        if (!ai->Fireball(handler->GetPlayer()))
        {
            handler->SendErrorMessage("Fireball did not cast.");
            return false;
        }
        return true;
    }

    bool HandleWard(ChatHandler* handler)
    {
        Creature* evoker = nullptr;
        npc_dm_evoker* ai = FindAI<npc_dm_evoker>(handler, NPC_DM_EVOKER, evoker);
        if (!ai)
            return false;
        ai->QuickFlameWard();
        return true;
    }

    ChatCommandTable const& RhahkZorTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "cavein",      HandleCaveIn,      SEC_GAMEMASTER, Console::No },
            { "lookout",     HandleLookout,     SEC_GAMEMASTER, Console::No },
            { "rubble",      HandleRubble,      SEC_GAMEMASTER, Console::No },
            { "tremor",      HandleTremor,      SEC_GAMEMASTER, Console::No },
            { "whirlwind",   HandleWhirlwind,   SEC_GAMEMASTER, Console::No },
            { "slam",        HandleSlam,        SEC_GAMEMASTER, Console::No },
            { "volley",      HandleVolley,      SEC_GAMEMASTER, Console::No },
            { "flamestrike", HandleFlamestrike, SEC_GAMEMASTER, Console::No },
            { "fireball",    HandleFireball,    SEC_GAMEMASTER, Console::No },
            { "ward",        HandleWard,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rhahk_zor_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_rhahk_zor_rework);
    RegisterDeadminesReworkCreatureAI(npc_dm_watchman);
    RegisterDeadminesReworkCreatureAI(npc_dm_evoker);
    RegisterSpellScript(spell_dm_rhahkzor_cave_in);
    RegisterSpellScript(spell_dm_rhahkzor_ref_flat);
    DeadminesTest::RegisterBoss("rhahkzor", RhahkZorTestCommands());
}
