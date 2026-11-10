/*
 * mod-dungeon-bosses, Stratholme S13: Ramstein the Gorger (10439), "Feeding Time" and "Bursting at the Seams". Build
 * spec ST 3432-3483 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows RG and 3.5 row S13. Replaces stock
 * SmartAI 10439 (Knockout 17307, Trample 5568, Flurry 15088 at reset, the walk-in action list 1043900) and the Mindless
 * Undead's own SmartAI 11030: WP-S13's SQL rev drops those rows; bound by apps/dbc-tools
 * source/npcs/stratholme/ramstein_the_gorger.py. Pure rules: RamsteinLogic.h.
 *
 * The instance summons him in his pen (the slaughter event, once the 13 abominations are dead); this script walks him
 * in (the stock walk-in), and his death goes straight to the Black Guards (the instance skips the Mindless stage).
 *
 *   Walk-in     the pen door 175405 opens, he yells (line 0), walks to his stop (home), the door shuts behind him, and
 *               he goes after the nearest player within 70 yd
 *   RG1  Meat   at 5 s, then every 15 s: the Slaughter Square gate 175358 opens and 4 (heroic 5) Mindless Undead 11030
 *               shamble out of (3941.8, -3393.1), passive, straight at him at 3.5 yd/s (re-pathed once a second); 33 in
 *               all on normal, no cap on heroic
 *   RG2  Gorge  a walker within 3 yd of him (his reach, once he is big) is rooted and eaten in a 1.5 s bite (emote line
 *               1, 206685): 206686 heals him 3% / 4%, and a Gorged stack (206687: +15% size, +10% damage; 8, heroic
 *               10). He fights on through the bite. Heroic Cannibalize: a meat killed within 10 yd of him leaves a
 *               corpse he eats the same way for half the heal
 *   RG3  Tear   at 30 s, then every 30 s: emote line 2, 1 + stacks Half-Digested Corpses (300586) spill around him
 *               and go for a random nearby player, a 6 yd gut puddle under him (registry zone, 4% a second for 20 s,
 *               Weakened once per player), Exposed (206689: +50% damage taken, 8 s / 6 s), every Gorged stack gone.
 *               Heroic: a crawler alive 15 s after the tear walks back to him and is eaten (a stack, no heal)
 *   RG4  Trample at 8 s, then every 12 s: a 1.5 s rear-up (emote state), then a circle on him of 10 yd + 1 per stack,
 *               25% / 30% + 3% per stack, Weakened, never the tank (206692); the tank takes the weapon hit (206694)
 *   RG5  Knockout 206695, stock 17307 without its stun, on his victim: first 4-9 s, then every 10-15 s
 *   Flurry      stock 15088 on himself at the pull
 *   Arena       StratholmeRework::LeashOptions on RamsteinArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler. Every firing logs one INFO line
 * "strat ramstein <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "Map.h"
#include "MotionMaster.h"
#include "PassiveAI.h"
#include "Player.h"
#include "RamsteinLogic.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratRamstein;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "ramstein";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }
}

// Ramstein the Gorger 10439
struct boss_ramstein_the_gorger_rework : public BossAI
{
    explicit boss_ramstein_the_gorger_rework(Creature* creature)
        : BossAI(creature, BOSS_RAMSTEIN), _arena(RamsteinArena(), LeashOptions(kLogBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAMSTEIN;
        Mechanic::BeginEncounter(me, options);
        Describe();

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        DoCastSelf(SPELL_RG_FLURRY, true);
        _nextTearMs = kTearCadence.first;
        _nextTrampleMs = kTrampleCadence.first;
        _nextKnockoutMs = InRange(kKnockoutFirst, Rand01());
        bool const heroic = IsHeroicMap(me);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE (the instance goes on to the Black Guards), the summons despawn
        Cleanup();
        Talk(YELL_RAMSTEIN_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("meat={} killer={}", _meat.Summoned(), killer ? killer->GetName() : "none"));
    }

    // The meat, the crawlers and the puddle stalkers are his summons but never fight on their own account: not zoned
    // into combat (BossAI::JustSummoned would). SummonWave adds each one to `summons` through this.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        Forget(summon->GetGUID());
        BossAI::SummonedCreatureDespawn(summon);
    }

    // RG2 heroic Cannibalize: a meat killed within 10 yd of him leaves a corpse he eats.
    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        uint32 const entry = summon->GetEntry();
        if (entry != NPC_MINDLESS_UNDEAD && entry != NPC_ST_HALF_DIGESTED_CORPSE)
            return;
        if (_bites.Has(summon->GetGUID().GetRawValue()))
            return;     // dying in a bite's last moments: the bite finishes anyway
        Forget(summon->GetGUID());
        if (entry == NPC_MINDLESS_UNDEAD && me->IsAlive() && me->IsEngaged()
            && CorpseEdible(IsHeroicMap(me), me->GetExactDist2d(summon)))
        {
            BeginBite(summon, BiteKind::Corpse);
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "cannibalize",
                Acore::StringFormat("corpse at {:.1f} yd", me->GetExactDist2d(summon)));
        }
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_RG_WALK_IN && _walkIn == WalkIn::Walking)
            FinishWalkIn();
    }

    void UpdateAI(uint32 diff) override
    {
        if (_walkIn == WalkIn::Pending)
            StartWalkIn();
        if (_walkIn == WalkIn::Walking)
        {
            UpdateWalkIn(diff);
            return;
        }
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        bool const heroic = IsHeroicMap(me);
        FinishBites(heroic);
        UpdateMeat(heroic);
        UpdateWalkers();
        UpdateCrawlers(heroic);

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_clockMs >= _nextTearMs)
        {
            _nextTearMs = _clockMs + kTearCadence.every;
            Tear(heroic);
        }
        if (_clockMs >= _nextTrampleMs)
        {
            _nextTrampleMs = _clockMs + kTrampleCadence.every;
            StartTrample(heroic);
        }
        if (_clockMs >= _nextKnockoutMs)
            Knockout();

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The walk-in (stock action list 1043900)
    // ----------------------------------------------------------------------------------------------------------------

    enum class WalkIn : uint8
    {
        Pending,
        Walking,
        Done,
    };

    void StartWalkIn()
    {
        if (me->GetExactDist2d(kRamsteinSummon.x, kRamsteinSummon.y) > kWalkInSkipRadiusYd)
        {
            _walkIn = WalkIn::Done;     // a GM spawned him elsewhere: he is where he is
            return;
        }
        _walkIn = WalkIn::Walking;
        _walkInMs = 0;
        _walkInYelled = false;
        me->SetHomePosition(kRamsteinStop.x, kRamsteinStop.y, kRamsteinStop.z, kRamsteinSummon.o);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToAll(true);       // the stock list's "set unit flags 768" (immune to players and NPCs)
        SetPenDoor(GO_STATE_ACTIVE);
        me->GetMotionMaster()->MovePoint(POINT_RG_WALK_IN, kRamsteinStop.x, kRamsteinStop.y, kRamsteinStop.z);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "walk-in", "from his pen to his stop");
    }

    void UpdateWalkIn(uint32 diff)
    {
        _walkInMs += diff;
        if (!_walkInYelled && _walkInMs >= kWalkInYellMs)
        {
            _walkInYelled = true;
            Talk(YELL_RAMSTEIN_HUNGER);
        }
        if (_walkInMs >= kWalkInTimeoutMs)
            FinishWalkIn();     // a blocked walk ends where he stands
    }

    void FinishWalkIn()
    {
        if (_walkIn != WalkIn::Walking)
            return;
        _walkIn = WalkIn::Done;
        SetPenDoor(GO_STATE_READY);
        me->SetImmuneToAll(false);
        me->SetReactState(REACT_AGGRESSIVE);
        if (!_walkInYelled)
            Talk(YELL_RAMSTEIN_HUNGER);
        if (Player* target = me->SelectNearestPlayer(kWalkInAggroRangeYd))
        {
            // Unit::Attack adds no threat, and UpdateVictim ends a fight that has none: engage first.
            me->EngageWithTarget(target);
            AttackStart(target);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "walk-in-done",
            Acore::StringFormat("at=({:.1f}, {:.1f})", me->GetPositionX(), me->GetPositionY()));
    }

    void SetPenDoor(GOState state)
    {
        if (GameObject* door = me->FindNearestGameObject(GO_ZIGGURAT_DOORS4, kWalkInDoorRangeYd))
            door->SetGoState(state);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG1 The Meat
    // ----------------------------------------------------------------------------------------------------------------

    struct Walker
    {
        ObjectGuid guid;
        BiteKind kind = BiteKind::Meat;
        uint64 nextRepathMs = 0;
    };

    void UpdateMeat(bool heroic)
    {
        if (uint32 const count = _meat.Take(_clockMs, heroic))
            SummonMeatWave(count);
    }

    // `count` Mindless Undead out of the south gate passage, passive, walking to him.
    std::vector<Creature*> SummonMeatWave(uint32 count)
    {
        OpenSideGate();
        Vec2 const spawn = kMindlessUndeadSpawn.XY();
        float const facing = DungeonKit::BearingTo(spawn, kRamsteinStop.XY());
        std::vector<Position> at;
        for (Vec2 const& p : WavePoints(spawn, count))
            at.emplace_back(p.x, p.y, kMindlessUndeadSpawn.z, facing);

        DungeonKit::WaveSpec spec;
        spec.entry = NPC_MINDLESS_UNDEAD;
        spec.passive = true;
        spec.onSummon = [this](Creature* add)
        {
            _walkers.push_back({ add->GetGUID(), BiteKind::Meat, 0 });
        };
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, at, summons);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "meat",
            Acore::StringFormat("wave of {} (summoned {}, alive walkers {})", wave.size(), _meat.Summoned(),
                _walkers.size()));
        return wave;
    }

    // The meat's passage: the Slaughter Square gate opens at the first wave (the instance opens it again on his death).
    void OpenSideGate()
    {
        if (GameObject* gate = me->FindNearestGameObject(GO_SLAUGHTER_GATE_SIDE, kSideGateSearchYd))
            if (gate->GetGoState() != GO_STATE_ACTIVE)
            {
                gate->SetGoState(GO_STATE_ACTIVE);
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "side-gate", "opened for the meat");
            }
    }

    // Walkers (the meat, and on heroic the crawlers that came back) walk to him, re-pathed once a second, and are eaten
    // on reaching him. A rooted, stunned or knocked-about walker is left alone until it is free.
    void UpdateWalkers()
    {
        for (auto it = _walkers.begin(); it != _walkers.end();)
        {
            Creature* walker = me->GetMap()->GetCreature(it->guid);
            if (!walker || !walker->IsAlive() || _bites.Has(it->guid.GetRawValue()))
            {
                it = _walkers.erase(it);
                continue;
            }
            if (InGorgeReach(me->GetExactDist2d(walker), walker->GetPositionZ() - me->GetPositionZ(),
                me->GetCombatReach()))
            {
                BeginBite(walker, it->kind);
                it = _walkers.erase(it);
                continue;
            }
            if (_clockMs >= it->nextRepathMs && !walker->HasUnitState(UNIT_STATE_NOT_MOVE | UNIT_STATE_LOST_CONTROL))
            {
                it->nextRepathMs = _clockMs + kMeatRepathMs;
                // MovePoint treats a speed of 0 as "the creature's own": a walker slowed to a stop stays put instead.
                float const speed = SlowedSpeed(kMeatSpeedYdPerSec,
                    walker->GetMaxNegativeAuraModifier(SPELL_AURA_MOD_DECREASE_SPEED));
                if (speed > 0.f)
                    walker->GetMotionMaster()->MovePoint(POINT_RG_WALKER, me->GetPosition(), FORCED_MOVEMENT_WALK,
                        speed);
            }
            ++it;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG2 Gorge
    // ----------------------------------------------------------------------------------------------------------------

    // The bite begins: the walker (or its corpse) is held where it is for kBiteMs, the emote and the look go off; the
    // meal lands in FinishBites. He fights on meanwhile (it is not a cast).
    void BeginBite(Creature* eaten, BiteKind kind)
    {
        if (!_bites.Add(eaten->GetGUID().GetRawValue(), kind, _clockMs))
            return;
        if (eaten->IsAlive())
        {
            eaten->GetMotionMaster()->Clear();
            eaten->StopMoving();
            eaten->SetImmuneToAll(true);    // it is being eaten: nobody kills it twice
            eaten->SetControlled(true, UNIT_STATE_ROOT);
        }
        if (_clockMs >= _nextGorgeEmoteMs)
        {
            _nextGorgeEmoteMs = _clockMs + kEmoteGapMs;
            Talk(EMOTE_RAMSTEIN_GORGE);
            me->CastSpell(me, SPELL_RG_GORGE_LOOK, true);
        }
    }

    void FinishBites(bool heroic)
    {
        for (Bite const& bite : _bites.Take(_clockMs))
        {
            if (Creature* eaten = me->GetMap()->GetCreature(ObjectGuid(bite.id)))
                eaten->DespawnOrUnsummon();
            _crawlers.Forget(bite.id);
            if (!me->IsAlive())
                continue;
            uint32 const heal = PctOfMax(me->GetMaxHealth(), BiteHealPct(heroic, bite.kind));
            if (heal)
                me->CastCustomSpell(SPELL_RG_GORGE_HEAL, SPELLVALUE_BASE_POINT0, static_cast<int32>(heal), me, true);
            uint32 const before = DungeonKit::Stacks(me, SPELL_RG_GORGED);
            uint32 const after = StacksAfterBite(before, heroic);
            if (after != before)
                DungeonKit::AddStacks(me, SPELL_RG_GORGED, static_cast<int32>(after - before), me,
                    kGorgedMaxStacks(heroic));
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "gorge",
                Acore::StringFormat("kind={} heal={} stacks={}->{}", int(bite.kind), heal, before, after));
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG3 Bursting at the Seams
    // ----------------------------------------------------------------------------------------------------------------

    void Tear(bool heroic)
    {
        Talk(EMOTE_RAMSTEIN_STITCHES);
        me->CastSpell(me, SPELL_RG_SEAMS_LOOK, true);

        // 1 crawler + 1 per stack, on a ring around him: outside his body at the size he was, so read the reach before
        // he shrinks back.
        uint32 const stacks = DungeonKit::Stacks(me, SPELL_RG_GORGED);
        float const radius = SpillRadius(me->GetCombatReach());
        me->RemoveAurasDueToSpell(SPELL_RG_GORGED);
        std::vector<Position> at;
        for (float angle : SpillAngles(SpillCount(stacks), Rand01() * DungeonKit::kTwoPi))
            at.push_back(me->GetFirstCollisionPosition(radius, angle));   // stops short of a wall
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_ST_HALF_DIGESTED_CORPSE;
        spec.onSummon = [this](Creature* crawler)
        {
            SpawnedCrawler(crawler);
        };
        std::vector<Creature*> const spilled = DungeonKit::SummonWave(me, spec, at, summons);

        PlacePuddle();
        me->CastSpell(me, SPELL_RG_EXPOSED, true);
        if (heroic)
            DungeonKit::ShortenAura(me, SPELL_RG_EXPOSED, me->GetGUID(), Ms(kExposedMs(true)));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "tear",
            Acore::StringFormat("heroic={} stacks={} crawlers={}/{} puddle=({:.1f}, {:.1f})", heroic ? 1 : 0, stacks,
                spilled.size(), SpillCount(stacks), me->GetPositionX(), me->GetPositionY()));
    }

    // A crawler: melee on a random nearby player (any player, the tank included), threat on everyone so it can switch
    // when its first target dies.
    void SpawnedCrawler(Creature* crawler)
    {
        _crawlers.Add(crawler->GetGUID().GetRawValue(), _clockMs);
        DoZoneInCombat(crawler);
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kSpillNearPlayerYd;
        if (Player* target = DungeonKit::PickPlayer(me, rule))
        {
            crawler->EngageWithTarget(target);
            crawler->AI()->AttackStart(target);
        }
    }

    // The puddle under him: a registry zone (the damage, Weakened once per player, the bots avoid it) and a stalker
    // that carries its look. 6 yd, 20 s, 4% a second after a 1 s grace.
    void PlacePuddle()
    {
        Position const at = me->GetPosition();
        if (Creature* stalker = me->SummonCreature(NPC_ST_GUT_PUDDLE, at, TEMPSUMMON_TIMED_DESPAWN, kPuddleMs))
            stalker->CastSpell(stalker, SPELL_RG_GUT_PUDDLE_LOOK, true);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, kPuddleRadius), Ms(kPuddleTickMs));
        ref.Persistent(Ms(kPuddleMs), Ms(kPuddleTickMs)).Damage(kPuddlePct).Spell(SPELL_RG_GUT_PUDDLE)
            .WeakenedOncePerPlayer().NoFillTimer().Tag(TAG_GUT_PUDDLE);
        Track(ref.Handle());
    }

    // Heroic: a crawler alive 15 s after the tear stops fighting and walks back to him to be eaten.
    void UpdateCrawlers(bool heroic)
    {
        if (!heroic)
            return;
        for (uint64 const raw : _crawlers.TakeDue(_clockMs))
        {
            Creature* crawler = me->GetMap()->GetCreature(ObjectGuid(raw));
            if (!crawler || !crawler->IsAlive() || _bites.Has(raw))
                continue;
            crawler->AI()->DoAction(ACTION_RG_RETURN);
            _walkers.push_back({ crawler->GetGUID(), BiteKind::Crawler, 0 });
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "crawler-back", "walks back to be eaten");
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG4 Trample, RG5 Knockout
    // ----------------------------------------------------------------------------------------------------------------

    void StartTrample(bool heroic)
    {
        uint32 const stacks = DungeonKit::Stacks(me, SPELL_RG_GORGED);
        float const radius = TrampleRadius(stacks);
        float const pct = TramplePct(heroic, stacks);
        me->SetEmoteState(EMOTE_STATE_ROAR);        // the rear-up (not a cast: he keeps swinging)
        MechanicRef ref = Mechanic::Circle(me, me, radius, Ms(kTrampleWarnMs));
        ref.TankExempt().Damage(pct).Spell(SPELL_RG_TRAMPLE_HIT).Weakened().Tag(TAG_TRAMPLE);
        ref.OnResolve(OnRamstein([](boss_ramstein_the_gorger_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.TrampleLands(result.hits.size());
        }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "trample",
            Acore::StringFormat("heroic={} stacks={} radius={:.0f} pct={:.0f}", heroic ? 1 : 0, stacks, radius, pct));
    }

    void TrampleLands(std::size_t hits)
    {
        me->SetEmoteState(EMOTE_ONESHOT_NONE);
        me->CastSpell(me, SPELL_RG_TRAMPLE_LOOK, true);
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim))
            me->CastSpell(victim, SPELL_RG_TRAMPLE_TANK, true);     // the tank's share: the stock weapon hit
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "trample-lands",
            Acore::StringFormat("hits={} tank={}", hits, victim ? victim->GetName() : "none"));
    }

    void Knockout()
    {
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim))
        {
            me->CastSpell(victim, SPELL_RG_KNOCKOUT, true);
            _nextKnockoutMs = _clockMs + InRange(kKnockoutEvery, Rand01());
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "knockout", victim->GetName());
        }
        else
            _nextKnockoutMs = _clockMs + 1000;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST "Bots"): kill order the meat nearest to him first, then the crawlers, then him; no interrupts, no
    // dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        for (MeatTier const& tier : kMeatTiers)
        {
            BossMechanics::TargetEntry meat(NPC_MINDLESS_UNDEAD, tier.priority, Who::Dps,
                BossMechanics::Condition::NearUnit(NPC_RAMSTEIN, tier.withinYd));
            meat.AoeOk();
            d.targets.push_back(std::move(meat));
        }
        BossMechanics::TargetEntry crawler(NPC_ST_HALF_DIGESTED_CORPSE, kCrawlerPriority, Who::Dps);
        crawler.AoeOk();
        d.targets.push_back(std::move(crawler));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat ramstein` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Meat,
        Tear,
        Trample,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged() || _walkIn == WalkIn::Walking)
            return "Ramstein must be in combat (the meat walks, the tear spills and Trample rears only in the fight).";
        switch (mechanic)
        {
            case TestMechanic::Meat:
                SummonMeatWave(kMeatPerWave(heroic));
                break;
            case TestMechanic::Tear:
                Tear(heroic);
                break;
            case TestMechanic::Trample:
                StartTrample(heroic);
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    // Sets the Gorged stacks (0 removes them), capped at the difficulty's.
    uint32 TestStacks(uint32 stacks)
    {
        uint32 const capped = std::min(stacks, kGorgedMaxStacks(IsHeroicMap(me)));
        uint32 const before = DungeonKit::Stacks(me, SPELL_RG_GORGED);
        if (capped != before)
            DungeonKit::AddStacks(me, SPELL_RG_GORGED, static_cast<int32>(capped) - static_cast<int32>(before), me,
                kGorgedMaxStacks(IsHeroicMap(me)));
        return capped;
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s stacks={} meat={} walkers={} bites={} crawlers={} tear={}s trample={}s "
            "knockout={}s walkIn={} scale={:.2f} reach={:.1f}", _clockMs / 1000,
            DungeonKit::Stacks(me, SPELL_RG_GORGED), _meat.Summoned(), _walkers.size(), _bites.Size(),
            _crawlers.Size(), _nextTearMs / 1000, _nextTrampleMs / 1000, _nextKnockoutMs / 1000, int(_walkIn),
            me->GetObjectScale(), me->GetCombatReach());
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnRamstein(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_ramstein_the_gorger_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // A summon is gone (died, eaten, despawned): off every list.
    void Forget(ObjectGuid guid)
    {
        _walkers.erase(std::remove_if(_walkers.begin(), _walkers.end(), [guid](Walker const& w)
        {
            return w.guid == guid;
        }), _walkers.end());
        _crawlers.Forget(guid.GetRawValue());
    }

    // The pull's state: nothing pending, no walkers, no stacks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _walkers.clear();
        _bites.Clear();
        _crawlers.Clear();
        _meat.Reset();
        summons.DespawnAll();
        if (me->IsAlive())
        {
            me->RemoveAurasDueToSpell(SPELL_RG_GORGED);
            me->RemoveAurasDueToSpell(SPELL_RG_EXPOSED);
            me->RemoveAurasDueToSpell(SPELL_RG_FLURRY);
            me->SetEmoteState(EMOTE_ONESHOT_NONE);
        }
        _clockMs = 0;
        _nextTearMs = kTearCadence.first;
        _nextTrampleMs = kTrampleCadence.first;
        _nextKnockoutMs = 0;
        _nextGorgeEmoteMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    WalkIn _walkIn = WalkIn::Pending;
    uint32 _walkInMs = 0;
    bool _walkInYelled = false;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextTearMs = 0;
    uint64 _nextTrampleMs = 0;
    uint64 _nextKnockoutMs = 0;
    uint64 _nextGorgeEmoteMs = 0;
    MeatClock _meat;
    BiteQueue _bites;
    CrawlerBook _crawlers;
    std::vector<Walker> _walkers;
    std::vector<MechanicHandle> _live;
};

// The meat (11030): a prop the boss moves, eats and despawns. It never attacks (NullCreatureAI is passive); damage and
// crowd control still land on it (its fear immunity is the stock set -93).
struct npc_st_meat : public NullCreatureAI
{
    explicit npc_st_meat(Creature* creature) : NullCreatureAI(creature) { }
};

// The gut puddle's stalker (300587): it carries the look aura and nothing else; the boss despawns it.
struct npc_st_gut_puddle : public NullCreatureAI
{
    explicit npc_st_gut_puddle(Creature* creature) : NullCreatureAI(creature) { }
};

// A Half-Digested Corpse (300586): melee on the player the tear picked (the boss engages it). Heroic: after 15 s the
// boss tells it to stop and walk back to be eaten (ACTION_RG_RETURN); the boss moves it from then on.
struct npc_st_half_digested_corpse : public ScriptedAI
{
    explicit npc_st_half_digested_corpse(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _returning = false;
    }

    void DoAction(int32 action) override
    {
        if (action != ACTION_RG_RETURN || _returning || !me->IsAlive())
            return;
        _returning = true;
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->GetMotionMaster()->Clear();
        me->StopMoving();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (!_returning)
            ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (_returning || !UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    bool _returning = false;
};

namespace
{
    boss_ramstein_the_gorger_rework* FindRamsteinAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_RAMSTEIN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ramstein_the_gorger_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Ramstein is not running boss_ramstein_the_gorger_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_ramstein_the_gorger_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_ramstein_the_gorger_rework* ai = FindRamsteinAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Ramstein: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_RAMSTEIN, BOSS_RAMSTEIN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_ramstein_the_gorger_rework* ai = FindRamsteinAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ramstein: {}", ai->TestState());
        return true;
    }

    bool HandleMeat(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ramstein_the_gorger_rework::TestMechanic::Meat, heroic,
            "a meat wave (RG1; the gate opens, 4 walk in, heroic 5)");
    }

    bool HandleTear(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ramstein_the_gorger_rework::TestMechanic::Tear, heroic,
            "Bursting at the Seams (RG3: crawlers, the puddle, Exposed)");
    }

    bool HandleTrample(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ramstein_the_gorger_rework::TestMechanic::Trample, heroic,
            "Trample (RG4: a rear-up, then a circle on him)");
    }

    // `.dbtest strat ramstein stacks <n>`: sets his Gorged stacks (RG2; 0 removes them).
    bool HandleStacks(ChatHandler* handler, uint32 stacks)
    {
        boss_ramstein_the_gorger_rework* ai = FindRamsteinAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ramstein: Gorged set to {}.", ai->TestStacks(stacks));
        return true;
    }

    // `.dbtest strat ramstein <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& RamsteinTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "meat",    HandleMeat,    SEC_GAMEMASTER, Console::No },
            { "tear",    HandleTear,    SEC_GAMEMASTER, Console::No },
            { "trample", HandleTrample, SEC_GAMEMASTER, Console::No },
            { "stacks",  HandleStacks,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ramstein_the_gorger_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ramstein_the_gorger_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_meat, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_gut_puddle, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_half_digested_corpse, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("ramstein", RamsteinTestCommands());
}
