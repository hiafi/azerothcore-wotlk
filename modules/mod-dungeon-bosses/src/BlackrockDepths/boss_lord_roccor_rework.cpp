/*
 * mod-dungeon-bosses, Blackrock Depths D2: Lord Roccor (9025), "the mountain is restless" (ruling 13). Build spec S1
 * 362-410 (docs/dungeons/blackrock-depths-1-detention-block.md, the whole "Lord Roccor" section), handoff sections 3.4
 * rows D2, 3.5 row D2, 3.6, 3.8 (the road), 3.9 (G1's `walk` drill row), 3.10. Replaces his SmartAI (Flame Shock
 * 13729, Earth Shock 13728, Ground Tremor 6524: the S0 SQL rev drops it); bound by apps/dbc-tools
 * source/npcs/blackrock_depths/roccor.py; his road (waypoint path 473040) and texts are
 * data/sql/updates/pending_db_world/rev_roccor_blackrock_depths.sql. Pure rules: RoccorLogic.h.
 *
 *   RO1 Restless March   he walks his road (RoccorLogic.h kRoadWest to kRoadEast, 61.8 yd through his spawn) out and
 *                        back at 1.5 yd/s, out of combat on the waypoint path, in combat by script (combat movement
 *                        off: he never chases; he swings at his victim when it is in reach). He stops only for
 *                        Rampage and Ground Tremor. The leash judge of G1's walk row runs once a second: the tank more
 *                        than 8 yd from him posts a Zone OffSpot failure tag 2, anyone more than 40 yd tag 3 (nothing
 *                        is registered: the bots keep up on their own, gap 10). After a surge the tank's judge waits
 *                        4 s. He evades when nobody in combat with him has been within 40 yd of the road for 10 s
 *   RO2 Underfoot        every second a Dark Iron (8891, 8892, 8909, 8921) within 6 yd of him takes 10% of its health
 *                        (no threat, no combat: Unit::DealDamage with skipCombat); the crush and crack looks play at
 *                        most every 3 s
 *   RO3 Rampage          12 s, then every 20 s (heroic 15 s): he stops and rears up for 2.5 s (emote 1) while a 20 x
 *                        8 yd lane shows ahead along the road (clipped at the road's end; turned round with under
 *                        10 yd left, section 8 #3); 40% / 60% Physical, the tank too. Dark Irons in the lane die; on
 *                        heroic a Loosed Earth in it merges back into him for 3% of his health. Then he surges to the
 *                        lane's end and walks on from there
 *   RO4 Loosed Earth     18 s, then every 25 s (heroic 20 s): a 2 s Ground Tremor (emote 2), then 2 (heroic 3)
 *                        Loosed Earth 300780 at his feet, each opening on a random non-tank (100 threat; everyone in
 *                        the fight at 0 so it never evades). They crumble after 45 s. At most two waves alive
 *   RO5 Flung Boulders   heroic, 10 s, then every 5 s: 3 circles of 3 yd on floor within 8 yd of him, 2 s, then 25%
 *                        Physical + Weakened; the boulder's look is thrown 0.4 s before the hit
 *   RO6 Flame Shock      his victim, 8 s, then 8-18 s: 6% + 2% every 3 s for 12 s (heroic 8% + 3%), Magic (the
 *                        dispel is a reward: descriptor)
 *   RO7 Earth Shock      a random player in 20 yd (the tank too), 7 s, then every 12 s: 10% / 15% Nature and the
 *                        stock 2 s school lockout
 *   Rule 10              with his victim out of reach for 3 s he hurls a stone at it every 2 s (15% / 20%)
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd roccor <mechanic> ..."
 * (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameTime.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "RoccorLogic.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <list>
#include <optional>
#include <string>
#include <unordered_set>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdRoccor;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "roccor";

    uint32 constexpr POINT_ROCCOR_LEG = 1;
    uint32 constexpr POINT_ROCCOR_SURGE = 2;

    enum RoccorCasts : uint32
    {
        CAST_RAMPAGE    = 1,
        CAST_TREMOR     = 2,
    };

    uint8 constexpr kPriorityRampage = 2;
    uint8 constexpr kPriorityTremor = 1;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    // The leash: the kit's leash on the road's 40 yd frame. He never chases, so the hold rule has nothing to do.
    DungeonKit::ArenaGuardOptions GuardOptions()
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(kBossLogName);
        o.holdWhileVictimOff = false;
        return o;
    }

    std::vector<uint32> DarkIronEntries()
    {
        return std::vector<uint32>(kDarkIronEntries.begin(), kDarkIronEntries.end());
    }
}

// Loosed Earth 300780 (RO4): a small earth elemental risen by Ground Tremor. It opens on the non-tank Roccor picked,
// melees (DamageModifier: about 8% of the reference row a swing), and returns to stone after 45 s or, on heroic, when
// his Rampage lane catches it (the merge). Stunnable (section 8 #4).
struct npc_brd_loosed_earth : public ScriptedAI
{
    explicit npc_brd_loosed_earth(Creature* creature) : ScriptedAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _lifeMs = 0;
        me->CastSpell(me, SPELL_RO_LOOSED_EARTH_RISE, true);
    }

    // Nobody left to fight (the boss's wipe despawns it anyway): back to stone, never a reset at a spawn point.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        if (!_returning)
            me->DespawnOrUnsummon();
    }

    // Crumble (45 s) or merge (heroic Rampage): the look, then gone. False when it is already going.
    bool ReturnToStone()
    {
        if (_returning || !me->IsAlive())
            return false;
        _returning = true;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->GetMotionMaster()->Clear(false);
        me->StopMoving();
        me->CastSpell(me, SPELL_RO_RETURN_TO_STONE, true);
        me->DespawnOrUnsummon(Ms(kLoosedFadeMs));
        return true;
    }

    bool Returning() const { return _returning; }

    void UpdateAI(uint32 diff) override
    {
        if (_returning)
            return;
        _lifeMs += diff;
        if (_lifeMs >= kLoosedLifeMs)
        {
            ReturnToStone();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "loosed-earth-crumbles");
            return;
        }
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    uint32 _lifeMs = 0;
    bool _returning = false;
};

// Lord Roccor 9025
struct boss_lord_roccor_rework : public BossAI
{
    explicit boss_lord_roccor_rework(Creature* creature)
        : BossAI(creature, BOSS_ROCCOR), _arena(RoadArena(), GuardOptions())
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        _Reset();
        Cleanup();
        me->SetCombatMovement(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ROCCOR;
        Mechanic::BeginEncounter(me, options);
        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        Describe();
        _arena.Engage(me);

        _queue.Schedule(CAST_RAMPAGE, kRampageFirstMs, kPriorityRampage);
        _queue.Schedule(CAST_TREMOR, kLoosedFirstMs, kPriorityTremor);
        _nextFlameShockMs = kFlameShockFirstMs;
        _nextEarthShockMs = kEarthShockFirstMs;
        _nextBouldersMs = kBouldersFirstMs;

        // RO1: on, the way he was walking; the script walks him now (the out-of-combat path leaves the idle slot,
        // so a pause stands still instead of taking the path up again).
        _dir = DirectionOf(me->GetOrientation());
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MoveIdle();
        StartLeg();
        Talk(EMOTE_ROCCOR_PULL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) s={:.1f} dir={}", _heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), RoadS(DungeonKit::PlaneOf(me)), _dir));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    // Back where the pull found him: the road's waypoint path again (the evade's home walk replaced it).
    void JustReachedHome() override
    {
        BossAI::JustReachedHome();
        me->GetMotionMaster()->Initialize();
    }

    void JustDied(Unit* killer) override
    {
        Talk(EMOTE_ROCCOR_DEATH);
        BossAI::JustDied(killer);   // DONE; the Loosed Earth despawn with the summons
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={} clock={}s", killer ? killer->GetName() : "none", _deathClockMs / 1000));
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == POINT_ROCCOR_LEG && _march == March::Walking)
            _legDone = true;
        else if (id == POINT_ROCCOR_SURGE && _march == March::Surging)
            _surgeDone = true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        _deathClockMs = _clockMs;
        if (!_arena.Update(me, diff))
            return;     // nobody within 40 yd of the road for 10 s: evading

        UpdateLeash(diff);
        UpdateUnderfoot(diff);
        UpdateRampage();
        UpdateTremor();
        UpdateBoulders();
        UpdateMarch();
        StartQueuedCast();
        UpdateShocks();
        UpdateHurl(diff);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO1 Restless March
    // ----------------------------------------------------------------------------------------------------------------

    enum class March : uint8
    {
        Walking,
        Paused,     // a rear-up or a Ground Tremor
        Surging,
    };

    // Walks to the road's end `_dir` points to (turning round when he stands at it).
    void StartLeg()
    {
        float const s = RoadS(DungeonKit::PlaneOf(me));
        if (RoadAhead(s, _dir) < 0.5f)
            _dir = -_dir;
        Point3 const end = LegEnd(_dir);
        me->GetMotionMaster()->MovePoint(POINT_ROCCOR_LEG, end.x, end.y, end.z, FORCED_MOVEMENT_WALK, kWalkYdS);
        me->SetHomePosition(me->GetPosition());     // an evade walks home a short way, then takes up the path
        _march = March::Walking;
        _legDone = false;
    }

    void PauseMarch()
    {
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MoveIdle();
        me->StopMoving();
        _march = March::Paused;
        _legDone = false;
    }

    void UpdateMarch()
    {
        if (_march == March::Walking && _legDone)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "march-turn",
                Acore::StringFormat("at=({:.1f}, {:.1f})", me->GetPositionX(), me->GetPositionY()));
            StartLeg();
        }
        else if (_march == March::Surging && (_surgeDone || _clockMs >= _surgeGiveUpAt))
            EndSurge();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cast queue: Rampage and Ground Tremor never overlap
    // ----------------------------------------------------------------------------------------------------------------

    void StartQueuedCast()
    {
        if (_march != March::Walking || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        std::optional<uint32> const next = _queue.Next(_clockMs);
        if (!next)
            return;
        switch (*next)
        {
            case CAST_RAMPAGE:
                _queue.Started(CAST_RAMPAGE, _clockMs, kRampageWarnMs);
                _queue.Schedule(CAST_RAMPAGE, _clockMs + kRampageEveryMs(_heroic), kPriorityRampage);
                StartRampage();
                break;
            case CAST_TREMOR:
                _queue.Started(CAST_TREMOR, _clockMs, kTremorCastMs);
                _queue.Schedule(CAST_TREMOR, _clockMs + kLoosedEveryMs(_heroic), kPriorityTremor);
                StartTremor();
                break;
            default:
                _queue.Cancel(*next);
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO3 Rampage
    // ----------------------------------------------------------------------------------------------------------------

    struct Rampage
    {
        RampagePlan plan;
        Position origin;
        float facing = 0.f;
        uint64 resolveAt = 0;
        MechanicHandle lane;
    };

    void StartRampage()
    {
        PauseMarch();
        RampagePlan const plan = PlanRampage(RoadS(DungeonKit::PlaneOf(me)), _dir);
        float const facing = RoadFacing(plan.dir);
        Position const origin(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        me->SetFacingTo(facing);
        DungeonKit::CastBar(me, SPELL_RO_RAMPAGE_CAST, nullptr, EMOTE_ROCCOR_RAMPAGE);
        float const pct = kRampagePct(_heroic);
        MechanicRef ref = Mechanic::Line(me, origin, facing, plan.length, kRampageWidthYd, Ms(kRampageWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_RO_RAMPAGE).Tag(TAG_RAMPAGE);
        _rampage = Rampage{ plan, origin, facing, _clockMs + kRampageWarnMs, ref.Handle() };
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rampage",
            Acore::StringFormat("heroic={} pct={:.0f} from=({:.1f}, {:.1f}) s={:.1f}->{:.1f} length={:.1f} turned={} "
                "ok={}", _heroic ? 1 : 0, pct, origin.GetPositionX(), origin.GetPositionY(), plan.fromS, plan.toS,
                plan.length, plan.turned ? 1 : 0, ref.IsValid() ? 1 : 0));
    }

    // The lane resolves (the registry hits the players): the Dark Irons in it die, a Loosed Earth in it merges
    // (heroic), then the surge.
    void UpdateRampage()
    {
        if (!_rampage || _clockMs < _rampage->resolveAt)
            return;
        Rampage const r = *_rampage;
        _rampage.reset();

        Vec2 const origin{ r.origin.GetPositionX(), r.origin.GetPositionY() };
        uint32 crushed = 0;
        std::list<Creature*> trash;
        me->GetCreatureListWithEntryInGrid(trash, DarkIronEntries(), r.plan.length + 10.f);
        for (Creature* c : trash)
        {
            if (!c->IsAlive() || std::fabs(c->GetPositionZ() - r.origin.GetPositionZ()) > kUnderfootZYd)
                continue;
            if (!InLane(origin, r.facing, r.plan.length, kRampageWidthYd, DungeonKit::PlaneOf(c),
                c->GetCombatReach()))
                continue;
            c->CastSpell(c, SPELL_RO_UNDERFOOT_CRACK, true);
            Unit::DealDamage(me, c, c->GetHealth(), nullptr, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL, nullptr, false,
                false, nullptr, true);
            ++crushed;
        }

        uint32 merged = 0;
        if (_heroic)
            for (ObjectGuid const& guid : summons)
            {
                Creature* add = ObjectAccessor::GetCreature(*me, guid);
                if (!add || add->GetEntry() != NPC_BRD_LOOSED_EARTH || !add->IsAlive())
                    continue;
                if (!InLane(origin, r.facing, r.plan.length, kRampageWidthYd, DungeonKit::PlaneOf(add),
                    add->GetCombatReach()))
                    continue;
                if (Merge(add))
                    ++merged;
            }

        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rampage-lands",
            Acore::StringFormat("crushed={} merged={}", crushed, merged));
        StartSurge(r);
    }

    // Heroic: the add returns to stone and he heals 3% of his health.
    bool Merge(Creature* add)
    {
        auto* ai = add->IsAIEnabled ? dynamic_cast<npc_brd_loosed_earth*>(add->AI()) : nullptr;
        if (!ai || !ai->ReturnToStone())
            return false;
        int32 const heal = static_cast<int32>(MergeHeal(me->GetMaxHealth()));
        me->CastCustomSpell(me, SPELL_RO_EARTHEN_MERGE, &heal, nullptr, nullptr, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "merge",
            Acore::StringFormat("heal={} health={}/{}", heal, me->GetHealth(), me->GetMaxHealth()));
        return true;
    }

    void StartSurge(Rampage const& r)
    {
        _dir = r.plan.dir;
        float const z = RoadPoint(r.plan.toS).z;
        float const x = r.origin.GetPositionX() + std::cos(r.facing) * r.plan.length;
        float const y = r.origin.GetPositionY() + std::sin(r.facing) * r.plan.length;
        me->CastSpell(me, SPELL_RO_RAMPAGE_SURGE, true);
        me->GetMotionMaster()->MovePoint(POINT_ROCCOR_SURGE, x, y, z, FORCED_MOVEMENT_RUN, kSurgeYdS);
        _march = March::Surging;
        _surgeDone = false;
        _surgeGiveUpAt = _clockMs + kSurgeGiveUpMs;
        _queue.SetBusy(true);
    }

    void EndSurge()
    {
        bool const arrived = _surgeDone;
        _queue.SetBusy(false);
        _tankGraceUntil = _clockMs + kSurgeLeashGraceMs;
        StartLeg();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "surge-ends",
            Acore::StringFormat("arrived={} at=({:.1f}, {:.1f}) s={:.1f} dir={}", arrived ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), RoadS(DungeonKit::PlaneOf(me)), _dir));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO4 Loosed Earth
    // ----------------------------------------------------------------------------------------------------------------

    void StartTremor()
    {
        PauseMarch();
        DungeonKit::CastBar(me, SPELL_RO_GROUND_TREMOR, nullptr, EMOTE_ROCCOR_LOOSED);
        _tremorAt = _clockMs + kTremorCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "ground-tremor",
            Acore::StringFormat("heroic={} alive={}", _heroic ? 1 : 0, AliveLoosed()));
    }

    void UpdateTremor()
    {
        if (!_tremorAt || _clockMs < *_tremorAt)
            return;
        _tremorAt.reset();
        RaiseLoosedEarth();
        if (_march == March::Paused)
            StartLeg();
    }

    uint32 AliveLoosed() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
        {
            Creature* add = ObjectAccessor::GetCreature(*me, guid);
            if (!add || add->GetEntry() != NPC_BRD_LOOSED_EARTH || !add->IsAlive())
                continue;
            auto* ai = add->IsAIEnabled ? dynamic_cast<npc_brd_loosed_earth*>(add->AI()) : nullptr;
            if (ai && ai->Returning())
                continue;
            ++n;
        }
        return n;
    }

    // Each opens on a random non-tank (a lone tank when nobody else is there). Returns how many rose.
    uint32 RaiseLoosedEarth()
    {
        uint32 const alive = AliveLoosed();
        uint32 const count = LoosedToRaise(_heroic, alive);
        uint32 raised = 0;
        std::string picks;
        for (uint32 i = 0; i < count; ++i)
        {
            Position const at = me->GetRandomNearPosition(kLoosedSpawnYd);
            TempSummon* add = me->SummonCreature(NPC_BRD_LOOSED_EARTH, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 5000);
            if (!add)
                continue;
            ++raised;
            Mechanic::TrackUnit(me, add);
            // Everyone in the fight at 0 (a one-entry threat list evades), then its pick.
            for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
                if (Unit* u = ref->GetVictim())
                    add->GetThreatMgr().AddThreat(u, 0.f, nullptr, true, true);
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            Player* target = DungeonKit::PickPlayer(me, rule);
            if (target && add->IsAIEnabled)
            {
                add->AddThreat(target, kLoosedOpeningThreat);
                add->AI()->AttackStart(target);
                picks += picks.empty() ? target->GetName() : "," + target->GetName();
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "loosed-earth",
            Acore::StringFormat("heroic={} raised={} alive-before={} cap={} targets={}", _heroic ? 1 : 0, raised,
                alive, kLoosedCap(_heroic), picks.empty() ? "none" : picks));
        return raised;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO2 Underfoot
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateUnderfoot(uint32 diff)
    {
        _underfootMs += diff;
        if (_underfootMs < kUnderfootTickMs)
            return;
        _underfootMs = 0;
        Underfoot();
    }

    uint32 Underfoot()
    {
        std::list<Creature*> trash;
        me->GetCreatureListWithEntryInGrid(trash, DarkIronEntries(), kUnderfootYd + 4.f);
        bool const look = _clockMs >= _nextUnderfootLookMs;
        Vec2 const at = DungeonKit::PlaneOf(me);
        uint32 hit = 0;
        uint32 killed = 0;
        for (Creature* c : trash)
        {
            if (!c->IsAlive() || !InUnderfoot(at, me->GetPositionZ(), DungeonKit::PlaneOf(c), c->GetPositionZ()))
                continue;
            if (look)
                c->CastSpell(c, SPELL_RO_UNDERFOOT_CRACK, true);
            uint32 const damage = UnderfootDamage(c->GetMaxHealth());
            if (damage >= c->GetHealth())
                ++killed;
            Unit::DealDamage(me, c, damage, nullptr, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL, nullptr, false, false,
                nullptr, true);
            ++hit;
        }
        if (!hit)
            return 0;
        if (look)
        {
            me->CastSpell(me, SPELL_RO_UNDERFOOT, true);
            _nextUnderfootLookMs = _clockMs + kUnderfootLookEveryMs;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "underfoot",
            Acore::StringFormat("hit={} killed={}", hit, killed));
        return hit;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO5 Flung Boulders (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    struct BoulderLook
    {
        Position at;
        uint64 throwAt = 0;
    };

    struct Boulder
    {
        MechanicHandle handle;
        uint64 resolveAt = 0;
    };

    void UpdateBoulders()
    {
        for (auto it = _looks.begin(); it != _looks.end();)
        {
            if (_clockMs < it->throwAt)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->at.GetPositionX(), it->at.GetPositionY(), it->at.GetPositionZ(),
                SPELL_RO_FLUNG_BOULDER_LOOK, true);
            it = _looks.erase(it);
        }
        std::erase_if(_boulders, [this](Boulder const& b) { return _clockMs > b.resolveAt + 1000; });
        if (!_heroic || _clockMs < _nextBouldersMs)
            return;
        _nextBouldersMs = _clockMs + kBouldersEveryMs;
        FlingBoulders();
    }

    uint32 FlingBoulders()
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(me);
        rules.minRange = 0.f;
        rules.maxRange = kBoulderSpreadYd;
        rules.minFromAway = kBoulderApartYd;
        rules.tries = 24;
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.reachable = true;
        Arena const floor = BoulderFloor();
        uint32 placed = 0;
        for (uint32 i = 0; i < kBouldersCount; ++i)
        {
            std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &floor, rules, probe);
            if (!spot)
                continue;
            rules.awayFrom.push_back({ spot->GetPositionX(), spot->GetPositionY() });
            MechanicRef ref = Mechanic::Circle(me, *spot, kBoulderRadiusYd, Ms(kBoulderWarnMs));
            ref.Damage(kBoulderPct).TankDamage(kBoulderPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_RO_FLUNG_BOULDERS)
                .Weakened().Tag(TAG_BOULDERS);
            if (!ref.IsValid())
                continue;
            _boulders.push_back({ ref.Handle(), _clockMs + kBoulderWarnMs });
            _looks.push_back({ *spot, _clockMs + kBoulderWarnMs - kBoulderLookLeadMs });
            ++placed;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flung-boulders",
            Acore::StringFormat("placed={} at=({:.1f}, {:.1f})", placed, me->GetPositionX(), me->GetPositionY()));
        return placed;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO6 Flame Shock, RO7 Earth Shock, rule 10's stone
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateShocks()
    {
        if (_march != March::Walking || me->IsActionPreventedByCasting())
            return;
        if (_clockMs >= _nextFlameShockMs)
            _nextFlameShockMs = _clockMs + (FlameShock() ? FlameShockDelay(frand(0.f, 1.f)) : kShockRetryMs);
        if (_clockMs >= _nextEarthShockMs)
            _nextEarthShockMs = _clockMs + (EarthShock(false) ? kEarthShockEveryMs : kShockRetryMs);
    }

    bool FlameShock()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinDistInMap(victim, kShockRangeYd) || !me->IsWithinLOSInMap(victim))
            return false;
        me->CastSpell(victim, SPELL_RO_FLAME_SHOCK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flame-shock",
            Acore::StringFormat("heroic={} target={}", _heroic ? 1 : 0, victim->GetName()));
        return true;
    }

    bool EarthShock(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // a random player, the tank too (ruling 88)
        rule.tankIfAlone = test;
        rule.maxRange = kShockRangeYd;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_RO_EARTH_SHOCK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "earth-shock",
            Acore::StringFormat("heroic={} target={}", _heroic ? 1 : 0, target->GetName()));
        return true;
    }

    // Rule 10: his victim out of reach for 3 s (a tank who stopped walking with him): a stone every 2 s. Never while
    // the tank is still catching up after a surge (kSurgeLeashGraceMs).
    void UpdateHurl(uint32 diff)
    {
        Unit* victim = me->GetVictim();
        if (_march != March::Walking || !victim || me->IsWithinMeleeRange(victim))
        {
            _outOfReachMs = 0;
            return;
        }
        _outOfReachMs += diff;
        if (!HurlReady(_outOfReachMs, _clockMs, _nextHurlMs, _tankGraceUntil) || me->IsActionPreventedByCasting())
            return;
        if (HurlStone(victim))
            _nextHurlMs = _clockMs + kHurlEveryMs;
    }

    bool HurlStone(Unit* victim)
    {
        if (!victim || !me->IsWithinDistInMap(victim, kHurlRangeYd) || !me->IsWithinLOSInMap(victim))
            return false;
        me->CastSpell(victim, SPELL_RO_HURL_STONE, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hurl-stone",
            Acore::StringFormat("target={} dist={:.1f} out-of-reach={}ms", victim->GetName(),
                me->GetExactDist2d(victim), _outOfReachMs));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO1's leash judge (G1's walk row: the tank 8 yd tag 2, everyone 40 yd tag 3, once a second)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateLeash(uint32 diff)
    {
        _leashMs += diff;
        if (_leashMs < kLeashTickMs)
            return;
        _leashMs = 0;
        bool const grace = _march == March::Surging || _clockMs < _tankGraceUntil;
        BossMechanics::Registry& reg = BossMechanics::Registry::GetOrCreate(me->GetMap());
        BossMechanics::RoleProvider const& roles = BossMechanics::GetRoleProvider();
        std::unordered_set<uint64> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Player* p = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
            if (!CountsAsPlayer(p))
                continue;
            bool const tank = roles.Get(me, p) == BossMechanics::Role::Tank;
            float const dist = me->GetExactDist2d(p);
            uint32 const tag = LeashTag(dist, tank, grace);
            if (!tag)
                continue;
            out.insert(p->GetGUID().GetRawValue());
            BossMechanics::FailureEvent e;
            e.encounter = me->GetGUID();
            e.tag = tag;
            e.kind = BossMechanics::Kind::Zone;
            e.player = p->GetGUID();
            e.type = BossMechanics::FailureEvent::Type::OffSpot;
            e.at = GameTime::GetGameTimeMS();
            reg.PostFailure(e);
            if (!_outOfLeash.count(p->GetGUID().GetRawValue()))
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "leash",
                    Acore::StringFormat("player={} tank={} dist={:.1f} tag={}", p->GetName(), tank ? 1 : 0, dist,
                        tag));
        }
        _outOfLeash = std::move(out);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (S1): kill order none, interrupts none, dispel Flame Shock (a reward)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.dispels.emplace_back(SPELL_RO_FLAME_SHOCK, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd roccor` entry points (`heroic` forces the heroic form until the next pull)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Rampage,
        Tremor,
        Boulders,
        Underfoot,
        FlameShock,
        EarthShock,
        Hurl,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Lord Roccor must be in combat (the road, the timers and the registry run only in the fight).";
        _heroic = heroic;
        switch (mechanic)
        {
            case TestMechanic::Rampage:
            case TestMechanic::Tremor:
                if (_march != March::Walking || me->HasUnitState(UNIT_STATE_CASTING))
                    return "Lord Roccor is busy (a rear-up, a Ground Tremor or a surge); try again in a moment.";
                if (mechanic == TestMechanic::Rampage)
                {
                    _queue.Started(CAST_RAMPAGE, _clockMs, kRampageWarnMs, false);
                    StartRampage();
                }
                else
                {
                    _queue.Started(CAST_TREMOR, _clockMs, kTremorCastMs, false);
                    StartTremor();
                }
                return {};
            case TestMechanic::Boulders:
                return FlingBoulders() ? std::string() : "No floor spot for a boulder.";
            case TestMechanic::Underfoot:
                Underfoot();
                return {};
            case TestMechanic::FlameShock:
                return FlameShock() ? std::string() : "No victim within 20 yd in line of sight.";
            case TestMechanic::EarthShock:
                return EarthShock(true) ? std::string() : "No player within 20 yd in line of sight.";
            case TestMechanic::Hurl:
                return HurlStone(me->GetVictim()) ? std::string() : "No victim within 40 yd in line of sight.";
        }
        return {};
    }

    uint32 TestRaise(bool heroic)
    {
        _heroic = heroic;
        return RaiseLoosedEarth();
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        auto at = [this](uint32 id)
        {
            std::optional<uint64> const due = _queue.DueAt(id);
            return due ? Acore::StringFormat("{}s", int64(*due / 1000)) : std::string("-");
        };
        char const* march = _march == March::Walking ? "walking" : _march == March::Paused ? "paused" : "surging";
        return Acore::StringFormat("clock={}s heroic={} march={} dir={} s={:.1f}/{:.1f} rampage@{} tremor@{} "
            "flameshock@{}s earthshock@{}s boulders@{}s loosed={} boulders-live={} out-of-reach={}ms out-of-leash={}",
            _clockMs / 1000, _heroic ? 1 : 0, march, _dir, RoadS(DungeonKit::PlaneOf(me)), RoadLength(),
            at(CAST_RAMPAGE), at(CAST_TREMOR), _nextFlameShockMs / 1000, _nextEarthShockMs / 1000,
            _nextBouldersMs / 1000, AliveLoosed(), _boulders.size(), _outOfReachMs, _outOfLeash.size());
    }

private:
    // The pull's state: no lane, boulders, looks or adds; the timers and the march from the start; Flame Shock off
    // everyone (Reset, evade, death, a new pull).
    void Cleanup()
    {
        if (_rampage)
            Mechanic::Cancel(me, _rampage->lane);
        _rampage.reset();
        for (Boulder const& b : _boulders)
            Mechanic::Cancel(me, b.handle);
        _boulders.clear();
        _looks.clear();
        _tremorAt.reset();
        summons.DespawnEntry(NPC_BRD_LOOSED_EARTH);
        me->RemoveAurasDueToSpell(SPELL_RO_RAMPAGE_SURGE);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                    p->RemoveAurasDueToSpell(SPELL_RO_FLAME_SHOCK, me->GetGUID());
        _queue.Reset();
        _clockMs = 0;
        _nextFlameShockMs = kFlameShockFirstMs;
        _nextEarthShockMs = kEarthShockFirstMs;
        _nextBouldersMs = kBouldersFirstMs;
        _nextHurlMs = 0;
        _nextUnderfootLookMs = 0;
        _surgeGiveUpAt = 0;
        _tankGraceUntil = 0;
        _underfootMs = 0;
        _leashMs = 0;
        _outOfReachMs = 0;
        _march = March::Walking;
        _legDone = false;
        _surgeDone = false;
        _outOfLeash.clear();
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _deathClockMs = 0;
    uint64 _nextFlameShockMs = kFlameShockFirstMs;
    uint64 _nextEarthShockMs = kEarthShockFirstMs;
    uint64 _nextBouldersMs = kBouldersFirstMs;
    uint64 _nextHurlMs = 0;
    uint64 _nextUnderfootLookMs = 0;
    uint64 _surgeGiveUpAt = 0;
    uint64 _tankGraceUntil = 0;
    uint32 _underfootMs = 0;
    uint32 _leashMs = 0;
    uint32 _outOfReachMs = 0;
    int _dir = 1;
    March _march = March::Walking;
    bool _legDone = false;
    bool _surgeDone = false;
    bool _heroic = false;
    std::optional<Rampage> _rampage;
    std::optional<uint64> _tremorAt;
    std::vector<Boulder> _boulders;
    std::vector<BoulderLook> _looks;
    std::unordered_set<uint64> _outOfLeash;
};

namespace
{
    boss_lord_roccor_rework* FindRoccorAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_ROCCOR);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_lord_roccor_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Lord Roccor is not running boss_lord_roccor_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_lord_roccor_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_lord_roccor_rework* ai = FindRoccorAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Lord Roccor: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_ROCCOR, BOSS_ROCCOR);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_lord_roccor_rework* ai = FindRoccorAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Lord Roccor: {}", ai->TestState());
        return true;
    }

    bool HandleRampage(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::Rampage, heroic,
            "Rampage (RO3: the rear-up, the lane, the surge; heroic merges)");
    }

    bool HandleTremor(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::Tremor, heroic,
            "Ground Tremor (RO4: the cast, then the Loosed Earth)");
    }

    // `.dbtest brd roccor loosed [1]`: a wave at once, no cast (the cap still counts).
    bool HandleLoosed(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_lord_roccor_rework* ai = FindRoccorAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        uint32 const raised = ai->TestRaise(isHeroic);
        handler->PSendSysMessage("Lord Roccor: {} Loosed Earth rose ({}).", raised, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleBoulders(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::Boulders, heroic,
            "Flung Boulders (RO5: three 3 yd circles within 8 yd)");
    }

    bool HandleUnderfoot(ChatHandler* handler)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::Underfoot, Optional<uint32>(),
            "an Underfoot tick (RO2: 10% to each Dark Iron within 6 yd)");
    }

    bool HandleFlameShock(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::FlameShock, heroic,
            "Flame Shock (RO6, on his victim)");
    }

    bool HandleEarthShock(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::EarthShock, heroic,
            "Earth Shock (RO7, on a random player in 20 yd)");
    }

    bool HandleHurl(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_lord_roccor_rework::TestMechanic::Hurl, heroic,
            "Hurl Stone (rule 10, at his victim)");
    }

    // `.dbtest brd roccor <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& BossLordRoccorTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "rampage",    HandleRampage,    SEC_GAMEMASTER, Console::No },
            { "tremor",     HandleTremor,     SEC_GAMEMASTER, Console::No },
            { "loosed",     HandleLoosed,     SEC_GAMEMASTER, Console::No },
            { "boulders",   HandleBoulders,   SEC_GAMEMASTER, Console::No },
            { "underfoot",  HandleUnderfoot,  SEC_GAMEMASTER, Console::No },
            { "flameshock", HandleFlameShock, SEC_GAMEMASTER, Console::No },
            { "earthshock", HandleEarthShock, SEC_GAMEMASTER, Console::No },
            { "hurl",       HandleHurl,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lord_roccor_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lord_roccor_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_loosed_earth, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("roccor", BossLordRoccorTestCommands());
}
