/*
 * mod-dungeon-bosses, Blackrock Spire B14: General Drakkisath (10363), normal and heroic, the Upper Spire's final boss.
 * Build spec SP 3990-4082 (design SP 3699-3989: theme A "Only the Branded May Pass", rulings 68-71, 73; the tank swap
 * at 10, rulings 63, 70, 71); handoff section 3.4 rows DR, section 3.5 row B14, section 3.6, section 3.8 (NM 13).
 * Replaces the stock boss_drakkisath (still registered, unbound by apps/dbc-tools
 * source/npcs/blackrock_spire/drakkisath.py): Conflagration (its threat wipe and 10 s disorient), Pierce Armor and the
 * plain Cleave are retired; Flamestrike and Thunderclap are reworked; Rage stays. The Chromatic Elite Guards (10814)
 * leave SmartAI for npc_brs_chromatic_elite_guard below (Knockdown removed; Mortal Strike and Strike kept).
 *
 *   DR1 The opening        he and both Guards engage together; the Guards are the first kill (boss data). At 10 the
 *                          second tank holds the Guards.
 *   DR2 Searing Brand      15 s, then every 20 s (one brand cast: normal, one kind at random on 1 / 2 non-tanks;
 *                          heroic, 1 / 2 of each kind): 12 s, nothing for 2 s, then each second 2% to the bearer and
 *                          6% to every other player within 4 yd (a held RunOut from the bearer). Emote line 1.
 *   DR3 Collapsing Brand   the same cast: each second 8% to the bearer, 1.6% while another player is within 4 yd (a
 *                          held Stack on a partner the script picks: another Collapsing bearer first, else the nearest
 *                          player with no brand, a non-tank first). Emote line 2.
 *   DR5 Thunderclap        8 s, then every 15 s: a 2 s wind-up, a 10 yd ring on him, everyone (the tank too): 25%,
 *                          Weakened, a 3 s slow.
 *   DR6 Flamestrike        6 s, then every 15 s: a 2.5 s cast, 5 yd circles at 2 / 4 random non-tanks' spots: 30%,
 *                          Weakened, then a burning patch 15 s (5% a second). Heroic: the cast is an expected
 *                          interrupt; uninterrupted, a circle lands under every player; kicked, none lands.
 *   DR7 Blackblade Sweep   5 s, then every 12 s: a 1.5 s wind-up, his facing locked at its start (toward his target),
 *                          a 180 degree, 10 yd sweep in front: 35%, Weakened, the tank too.
 *   DR8 Tank kit           stock Rage 16789 (1 s, every 35 s); the Guards' Mortal Strike and Strike.
 *   DR9 Seared Flesh       10 players only: 8 s, then every 8 s his blade adds a stack to his target (+10% damage taken
 *                          from him per stack, 15 s, refreshed, no cap); the bots' taunt swap at 3 (the user ruling:
 *                          a tank taunts once its own stacks are gone). The stacks of his target hold while he cannot
 *                          strike it (a wind-up, a hard mode hold, out of reach): DrakkisathLogic.h.
 *   Leash                  DrakkisathArena() with LeashOptions (no grips).
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler that a cast bar pauses. The hard mode (WP-B15,
 * the General's Army) fights on this AI through DrakkisathFight.h (DrakkisathHardMode hooks; this class is its
 * DrakkisathFight). Every firing logs one INFO line "brs drakkisath <mechanic> ..." (module.dungeonbosses);
 * `.dbtest brs drakkisath <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DrakkisathFight.h"
#include "DrakkisathLogic.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "DungeonKitFlow.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <list>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsDrakkisath;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "drakkisath";

    // Registry tags (bookkeeping; per encounter).
    enum DrakkisathTags : uint32
    {
        TAG_DR_SEARING      = 1,
        TAG_DR_COLLAPSING   = 2,
        TAG_DR_THUNDERCLAP  = 3,
        TAG_DR_FLAMESTRIKE  = 4,
        TAG_DR_PATCH        = 5,
        TAG_DR_SWEEP        = 6,
    };

    enum GuardPoints : uint32
    {
        POINT_GUARD_HOLD    = 1,
    };

    float constexpr kGuardSearchYd = 80.f;      // his two Guards stand 9 yd from him

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    DrakkisathHardModeFactory& HardModeFactory()
    {
        static DrakkisathHardModeFactory factory;
        return factory;
    }

    // A living, attackable player of the map who is not a game master.
    bool FightCandidate(Player const* player)
    {
        return player && player->IsAlive() && !player->IsGameMaster() && player->IsInWorld();
    }
}

void BrsDrakkisath::RegisterDrakkisathHardMode(DrakkisathHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

std::unique_ptr<DrakkisathHardMode> BrsDrakkisath::CreateDrakkisathHardMode(Creature* boss)
{
    DrakkisathHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// The Chromatic Elite Guards 10814 (DR1, DR8): melee with the stock Mortal Strike and Strike (Knockdown removed). The
// hard mode (B15, DR12) can hold one at a spot: it walks there, stays rooted and strikes only the nearest player within
// reach of the spot; Release sends it back to its threat.
struct npc_brs_chromatic_elite_guard : public ScriptedAI
{
    explicit npc_brs_chromatic_elite_guard(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _events.Reset();
        EndHold();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _events.ScheduleEvent(EVENT_MORTAL_STRIKE, Ms(urand(kGuardMortalFirstMinMs, kGuardMortalFirstMaxMs)));
        _events.ScheduleEvent(EVENT_STRIKE, Ms(urand(kGuardStrikeFirstMinMs, kGuardStrikeFirstMaxMs)));
    }

    void JustDied(Unit* killer) override;

    void EnterEvadeMode(EvadeReason why) override
    {
        EndHold();
        ScriptedAI::EnterEvadeMode(why);
    }

    // Held: swing at the picked target from the spot, never chase.
    void AttackStart(Unit* who) override
    {
        if (!_hold)
        {
            ScriptedAI::AttackStart(who);
            return;
        }
        if (who && _arrived)
            me->Attack(who, true);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (!_hold || type != POINT_MOTION_TYPE || id != POINT_GUARD_HOLD)
            return;
        _arrived = true;
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetFacingTo(_spot.GetOrientation());
    }

    void Hold(Position const& spot, float reachYd)
    {
        if (!me->IsAlive())
            return;
        EndHold();
        _hold = true;
        _spot = spot;
        _reachYd = reachYd;
        _pickMs = 0;
        me->AttackStop();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_GUARD_HOLD, spot.GetPositionX(), spot.GetPositionY(),
            spot.GetPositionZ());
    }

    void Release()
    {
        if (!_hold)
            return;
        EndHold();
        me->AttackStop();
        me->GetMotionMaster()->Clear();
        // The next UpdateVictim picks the threat leader and chases it.
    }

    bool Held() const
    {
        return _hold;
    }

    void UpdateAI(uint32 diff) override
    {
        if (_hold)
        {
            UpdateHold(diff);
            return;
        }
        if (!UpdateVictim())
            return;
        RunEvents(diff);
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

private:
    enum GuardEvents : uint32
    {
        EVENT_MORTAL_STRIKE = 1,
        EVENT_STRIKE        = 2,
    };

    void RunEvents(uint32 diff)
    {
        _events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        while (uint32 const id = _events.ExecuteEvent())
        {
            Unit* victim = me->GetVictim();
            switch (id)
            {
                case EVENT_MORTAL_STRIKE:
                    if (victim && me->IsWithinMeleeRange(victim))
                        DoCastVictim(SPELL_DR_GUARD_MORTAL_STRIKE);
                    _events.ScheduleEvent(EVENT_MORTAL_STRIKE, Ms(kGuardMortalEveryMs));
                    break;
                case EVENT_STRIKE:
                    if (victim && me->IsWithinMeleeRange(victim))
                        DoCastVictim(SPELL_DR_GUARD_STRIKE);
                    _events.ScheduleEvent(EVENT_STRIKE, Ms(kGuardStrikeEveryMs));
                    break;
                default:
                    break;
            }
        }
    }

    // Held at the spot: every kGuardHoldPickMs the nearest living player within reach of the spot is its target (none:
    // it stands idle, still in combat); it swings only at a target in its melee range.
    void UpdateHold(uint32 diff)
    {
        if (!me->IsInCombat() || !_arrived)
            return;
        _pickMs = _pickMs > diff ? _pickMs - diff : 0;
        if (!_pickMs)
        {
            _pickMs = kGuardHoldPickMs;
            Player* best = nullptr;
            float bestDist = 0.f;
            for (auto const& ref : me->GetMap()->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!FightCandidate(player) || !me->IsValidAttackTarget(player))
                    continue;
                float const d = player->GetExactDist2d(&_spot);
                if (d > _reachYd || (best && d >= bestDist))
                    continue;
                best = player;
                bestDist = d;
            }
            if (best && me->GetVictim() != best)
            {
                me->AddThreat(best, 0.f);
                me->Attack(best, true);
            }
            else if (!best && me->GetVictim())
                me->AttackStop();
        }
        if (!me->GetVictim())
            return;
        RunEvents(diff);
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    void EndHold()
    {
        if (_hold && _arrived)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _hold = false;
        _arrived = false;
    }

    EventMap _events;
    Position _spot;
    float _reachYd = 0.f;
    uint32 _pickMs = 0;
    bool _hold = false;
    bool _arrived = false;
};

// General Drakkisath 10363
struct boss_drakkisath_rework : public BossAI, public DrakkisathFight
{
    explicit boss_drakkisath_rework(Creature* creature)
        : BossAI(creature, BOSS_DRAKKISATH), _arena(DrakkisathArena(), LeashOptions(kBossLogName)),
          _queue(kCastSpacingMs) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(false);     // a `.dbtest brs drakkisath` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        bool hardMode = _heroic && instance && instance->GetData(DATA_GENERALS_ARMY) != 0;
        if (hardMode)
        {
            // The handler first: a lit flag with no handler registered runs the plain heroic, without the hard mode's
            // loot bits (the B8 rule, R-1-B n6).
            _hardMode = CreateDrakkisathHardMode(me);
            if (!_hardMode)
            {
                LOG_WARN("module", "brs drakkisath: the General's Army is armed but no hard mode handler is "
                    "registered; the pull runs as a plain heroic");
                hardMode = false;
            }
        }
        _players = OnBossPull(me, kBossLogName, hardMode);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_DRAKKISATH;
        Mechanic::BeginEncounter(me, options);
        FindGuards();
        Describe();
        _arena.Engage(me);
        StartTimers(0);
        Talk(YELL_DR_AGGRO);

        Log("engage", Acore::StringFormat("players={} heroic={} hardmode={} handler={} tankswap={} guards={}",
            _players, _heroic ? 1 : 0, hardMode ? 1 : 0, _hardMode ? 1 : 0,
            DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0, _guards.size()));
        if (_hardMode)
        {
            _hardMode->OnEngage(*this);
            // The kit's `pull` line above logs his health before the hard mode sets it.
            Log("pull-health", Acore::StringFormat("health={} hardmode=1", me->GetMaxHealth()));
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_DR_DEATH);
        Cleanup(true);
        BossAI::JustDied(killer);
        Log("death");
    }

    // Everything he summons is his fight's (despawned with it).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (summon && _hardMode && _engaged)
            _hardMode->OnSummonDied(*this, summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    // DR9: every hit of his on a player carrying his Seared Flesh is 10% harder per stack. The hard mode's Trophy
    // raises his non-melee hits after it (DrakkisathFight.h OnDamageDealt). B15's squads own their own hits (R-2 m-7).
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType type, SpellSchoolMask /*mask*/) override
    {
        if (!victim || !damage)
            return;
        if (uint32 const stacks = DungeonKit::Stacks(victim, SPELL_DR_SEARED_FLESH, me->GetGUID()))
            damage = SearedFleshDamage(damage, stacks);
        if (_hardMode && _engaged)
            _hardMode->OnDamageDealt(*this, victim, damage, type == DIRECT_DAMAGE);
    }

    // A cast bar of his kicked or cancelled: the heroic Flamestrike lands nothing (DR6); a hold a hard mode cast set
    // ends with it (lesson 6, B8's EndHoldEarly).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        uint32 const id = spell ? spell->Id : 0;
        if (id == SPELL_DR_FLAMESTRIKE_CAST_H)
            FlamestrikeStopped("kicked");
        if (!_engaged)
            return;
        if (_now < _holdUntil)
        {
            _holdUntil = EndHoldEarly(_queue, _holdUntil, _now);
            Log("hold-ended", Acore::StringFormat("spell={}", id));
        }
        else if (id == SPELL_DR_FLAMESTRIKE_CAST_H)
            _queue.Interrupted(_now);
        if (_hardMode)
            _hardMode->OnSpellFailed(*this, id);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dbtest` brand still ticks and ends.
        _clockMs += diff;
        UpdateBrands();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _now += diff;
        if (_hardMode)
        {
            _hardMode->OnUpdate(*this, diff);
            if (!_engaged || !me->IsAlive())
                return;     // the hook ended the fight
        }

        if (DungeonKit::Flex::TankSwapOn(_players))
        {
            SearedFlesh();
            HoldSearedFlesh(diff);
        }
        if (_now >= _nextBrandAt)
            BrandTimer();

        if (Busy())
            return;
        RunQueue();
        if (Busy())
            return;
        Rage();
        if (Uses(Ability::Melee))
            DoMeleeAttackIfReady();
    }

    // ---- DrakkisathFight (the hard mode's view of the pull, DrakkisathFight.h) --------------------------------------

    Creature* Boss() override
    {
        return me;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    uint8 Players() const override
    {
        return _players;
    }

    DrakkisathHardMode* ActiveHardMode() override
    {
        return _hardMode.get();
    }

    uint64 FightMs() const override
    {
        return _now;
    }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!FightCandidate(player))
                continue;
            if (!me->IsInCombatWith(player) && !_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    std::vector<Creature*> Guards() override
    {
        std::vector<Creature*> out;
        for (ObjectGuid const& guid : _guards)
            if (Creature* guard = ObjectAccessor::GetCreature(*me, guid))
                if (guard->IsAlive())
                    out.push_back(guard);
        return out;
    }

    void HoldGuards(std::vector<Position> const& spots, float reachYd) override
    {
        if (spots.empty())
            return;
        std::size_t i = 0;
        for (Creature* guard : Guards())
        {
            Position const& spot = spots[std::min(i, spots.size() - 1)];
            ++i;
            if (auto* ai = GuardAI(guard))
                ai->Hold(spot, reachYd);
        }
        Log("guards-hold", Acore::StringFormat("guards={} reach={:.0f}", i, reachYd));
    }

    void ReleaseGuards() override
    {
        uint32 released = 0;
        for (Creature* guard : Guards())
            if (auto* ai = GuardAI(guard))
                if (ai->Held())
                {
                    ai->Release();
                    ++released;
                }
        Log("guards-release", Acore::StringFormat("guards={}", released));
    }

    void SetRooted(bool rooted) override
    {
        if (rooted == _rooted)
            return;
        _rooted = rooted;
        me->SetControlled(rooted, UNIT_STATE_ROOT);
        Log("rooted", Acore::StringFormat("on={}", rooted ? 1 : 0));
    }

    void RestartKit(uint32 delayMs = 0) override
    {
        StartTimers(delayMs);
        Log("kit-restart", Acore::StringFormat("delay={}ms", delayMs));
    }

    GuidSet Brands(uint8 searing, uint8 collapsing) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        GuidSet busy;
        for (BrandState const& b : _brands)
            busy.insert(b.bearer);
        DungeonKit::ExcludeGuids(rule, busy);
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, rule, uint32(searing) + collapsing);
        std::vector<Player*> searingBearers;
        std::vector<Player*> collapsingBearers;
        for (std::size_t i = 0; i < picks.size(); ++i)
            (i < searing ? searingBearers : collapsingBearers).push_back(picks[i]);
        return BrandOn(searingBearers, collapsingBearers);
    }

    BossMechanics::SpotBounds RoomBounds() const override
    {
        BossMechanics::SpotBounds bounds;
        for (auto const& box : { kHallBox, kAlcoveBox })
        {
            std::vector<Position> points;
            for (Vec2 const& p : box)
                points.emplace_back(p.x, p.y, kRoomZ, 0.f);
            bounds.Polygon(std::move(points), kRoomZMin, kRoomZMax);
        }
        return bounds;
    }

    void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) override
    {
        if (id < kHardModeCastBase)
            return;
        _queue.Schedule(id, _now + inMs, priority);
    }

    void CancelCast(uint32 id) override
    {
        _queue.Cancel(id);
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _live.push_back(handle);
    }

    void TrackSummon(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
        Mechanic::TrackUnit(me, summon);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ---- his Guards call back ---------------------------------------------------------------------------------------

    void GuardDied(Creature* guard)
    {
        if (!_engaged || !guard)
            return;
        Log("guard-died", Acore::StringFormat("guid={} left={}", guard->GetSpawnId(), Guards().size()));
        if (_hardMode)
            _hardMode->OnGuardDied(*this, guard);
    }

    // ---- `.dbtest brs drakkisath` entry points ----------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    void TestBrand(Player* target, Brand kind)
    {
        if (kind == Brand::Searing)
            BrandOn({ target }, {});
        else
            BrandOn({}, { target });
    }

    void TestThunderclap()
    {
        StartThunderclap();
    }

    void TestFlamestrike(Player* target, bool heroicForm)
    {
        StartFlamestrike(heroicForm, { target });
    }

    void TestSweep()
    {
        StartSweep();
    }

    void TestSearedFlesh(Player* target)
    {
        Strike(target);
    }

    std::string TestState()
    {
        auto due = [this](uint32 id) -> std::string
        {
            std::optional<uint64> const at = _queue.DueAt(id);
            return at ? Acore::StringFormat("{}ms", *at) : std::string("-");
        };
        std::string out = Acore::StringFormat("engaged={} heroic={} hardmode={} players={} tankswap={} t={}ms "
            "hold={}ms rooted={} next sweep/clap/flamestrike={}/{}/{} brand={}ms rage={}ms seared={}ms brands={} "
            "guards={}", _engaged ? 1 : 0, _heroic ? 1 : 0, _hardMode ? 1 : 0, _players,
            DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0, _now, _holdUntil, _rooted ? 1 : 0, due(CAST_SWEEP),
            due(CAST_THUNDERCLAP), due(CAST_FLAMESTRIKE), _nextBrandAt, _nextRageAt, _nextSearedAt, _brands.size(),
            Guards().size());
        for (BrandState const& b : _brands)
        {
            Player* bearer = ObjectAccessor::GetPlayer(*me, b.bearer);
            out += Acore::StringFormat("\n  {} on {} ticks={} partner={}", BrandName(b.kind),
                bearer ? bearer->GetName() : std::string("?"), b.ticks, b.partner.IsEmpty() ? 0 : 1);
        }
        if (Unit* victim = me->GetVictim())
            out += Acore::StringFormat("\n  victim {} seared flesh {}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_DR_SEARED_FLESH, me->GetGUID()));
        return out;
    }

private:
    struct BrandState
    {
        ObjectGuid bearer;
        ObjectGuid partner;                                 // Collapsing: the partner the bots stack on
        Brand kind = Brand::Searing;
        uint64 bornMs = 0;                                  // _clockMs
        uint32 ticks = 0;
        uint32 othersHit = 0;                               // Searing: flares on others
        uint32 pairedTicks = 0;                             // Collapsing: ticks with someone within 4 yd
        MechanicHandle handle;
    };

    // A resolve callback that finds his AI again (never a captured `this`: the registry may outlive it).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBoss(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_drakkisath_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    static npc_brs_chromatic_elite_guard* GuardAI(Creature* guard)
    {
        return (guard && guard->IsAIEnabled) ? dynamic_cast<npc_brs_chromatic_elite_guard*>(guard->AI()) : nullptr;
    }

    void FindGuards()
    {
        _guards.clear();
        std::list<Creature*> found;
        me->GetCreatureListWithEntryInGrid(found, NPC_CHROMATIC_ELITE_GUARD, kGuardSearchYd);
        for (Creature* guard : found)
        {
            if (!guard->IsAlive())
                continue;
            _guards.push_back(guard->GetGUID());
            Mechanic::TrackUnit(me, guard);     // the descriptor's assist-tank entry sees them (TS report)
        }
    }

    void Describe()
    {
        // Boss data (build spec): the Guards first, then him. Heroic: Flamestrike on the interrupt list (expected). At
        // 10 the taunt swap at 3 Seared Flesh and the assist tank holds the Guards. B15 edits it for the hard mode
        // (Mechanic::EditDescriptor).
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_CHROMATIC_ELITE_GUARD, 1));
        if (_heroic)
            d.interrupts.emplace_back(NPC_DRAKKISATH, SPELL_DR_FLAMESTRIKE_CAST_H, kFlamestrikeKickPriority,
                Ms(kFlamestrikeEveryMs));
        if (DungeonKit::Flex::TankSwapOn(_players))
        {
            d.tauntSwaps.push_back(BossMechanics::TauntSwapEntry(NPC_DRAKKISATH, SPELL_DR_SEARED_FLESH,
                kSearedFleshSwapAt));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_CHROMATIC_ELITE_GUARD, 1,
                BossMechanics::Who::AssistTank));
        }
        Mechanic::Describe(me, std::move(d));
    }

    bool Uses(Ability a) const
    {
        return !_hardMode || _hardMode->UsesAbility(*this, a);
    }

    // A cast bar of his, or a hard mode cast holding him.
    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _now < _holdUntil;
    }

    // Every ability from now: its first timer plus `delayMs` (the pull; B15's phase 2).
    void StartTimers(uint32 delayMs)
    {
        uint64 const base = _now + delayMs;
        _queue.Schedule(CAST_SWEEP, base + kSweepFirstMs, kSweepPriority);
        _queue.Schedule(CAST_THUNDERCLAP, base + kThunderclapFirstMs, kThunderclapPriority);
        _queue.Schedule(CAST_FLAMESTRIKE, base + kFlamestrikeFirstMs, kFlamestrikePriority);
        _nextBrandAt = base + kBrandFirstMs;
        _nextRageAt = base + kRageFirstMs;
        _nextSearedAt = base + kSearedFleshFirstMs;
    }

    // The cast queue: his three wind-ups and B15's casts, one at a time.
    void RunQueue()
    {
        std::optional<uint32> const next = _queue.Next(_now);
        if (!next)
            return;
        switch (*next)
        {
            case CAST_SWEEP:
                RunOwnCast(CAST_SWEEP, Ability::BlackbladeSweep, kSweepCastMs, kSweepEveryMs, kSweepPriority,
                    [this]() { StartSweep(); });
                return;
            case CAST_THUNDERCLAP:
                RunOwnCast(CAST_THUNDERCLAP, Ability::Thunderclap, kThunderclapCastMs, kThunderclapEveryMs,
                    kThunderclapPriority, [this]() { StartThunderclap(); });
                return;
            case CAST_FLAMESTRIKE:
                RunOwnCast(CAST_FLAMESTRIKE, Ability::Flamestrike, kFlamestrikeCastMs, kFlamestrikeEveryMs,
                    kFlamestrikePriority, [this]() { StartFlamestrike(_heroic, {}); });
                return;
            default:
                break;
        }
        // The entry is consumed before OnCast: a next cast the hook schedules for the same id stays queued.
        uint32 const id = *next;
        std::optional<uint32> const holdMs = StartHardModeCast(_queue, id, _now, [this, id]()
        {
            return _hardMode ? _hardMode->OnCast(*this, id) : std::nullopt;
        });
        if (holdMs)
            _holdUntil = _now + *holdMs;
    }

    // One of his wind-ups came up: off by the hard mode's gate, or no target, it re-arms at its cadence (a retry for a
    // missing target); else it holds the queue for its bar and the next one is due a cadence from now.
    template <class Start>
    void RunOwnCast(uint32 id, Ability ability, uint32 castMs, uint32 everyMs, uint8 priority, Start start)
    {
        if (!Uses(ability))
        {
            _queue.Schedule(id, _now + everyMs, priority);
            return;
        }
        if (!me->GetVictim())
        {
            _queue.Schedule(id, _now + kRetryMs, priority);
            return;
        }
        _queue.Started(id, _now, castMs);
        _queue.Schedule(id, _now + everyMs, priority);
        start();
    }

    // ---- DR8 Rage ---------------------------------------------------------------------------------------------------

    void Rage()
    {
        if (_now < _nextRageAt)
            return;
        _nextRageAt = _now + kRageEveryMs;
        if (!Uses(Ability::Rage))
            return;
        me->CastSpell(me, SPELL_DR_RAGE, true);
        Log("rage");
    }

    // ---- DR2 / DR3 the brands ---------------------------------------------------------------------------------------

    void BrandTimer()
    {
        _nextBrandAt = _now + kBrandEveryMs;
        if (!Uses(Ability::Brands))
            return;
        BrandCounts const counts = BrandsPerCast(_heroic, _players, urand(0, 1) == 0);
        Brands(counts.searing, counts.collapsing);
    }

    GuidSet BrandOn(std::vector<Player*> const& searingBearers, std::vector<Player*> const& collapsingBearers)
    {
        GuidSet searing;
        GuidSet collapsing;
        std::vector<uint64> searingIds;
        std::vector<uint64> collapsingIds;
        for (Player* bearer : searingBearers)
        {
            if (!bearer)
                continue;
            searing.insert(bearer->GetGUID());
            searingIds.push_back(bearer->GetGUID().GetRawValue());
            me->CastSpell(bearer, SPELL_DR_SEARING_BRAND, true);
            Talk(EMOTE_DR_SEARING_BRAND, bearer);
            // Telegraph only (the script ticks): everyone else keeps 4 yd from the bearer for the whole brand.
            MechanicRef ref = Mechanic::RunOut(me, bearer, kBrandRadius, Ms(kBrandMs));
            ref.Within(RoomBounds()).Tag(TAG_DR_SEARING);
            MechanicHandle const handle = ref.Handle();
            Track(handle);
            _brands.push_back({ bearer->GetGUID(), ObjectGuid::Empty, Brand::Searing, _clockMs, 0, 0, 0, handle });
        }
        for (Player* bearer : collapsingBearers)
        {
            if (!bearer)
                continue;
            collapsing.insert(bearer->GetGUID());
            collapsingIds.push_back(bearer->GetGUID().GetRawValue());
            me->CastSpell(bearer, SPELL_DR_COLLAPSING_BRAND, true);
            Talk(EMOTE_DR_COLLAPSING, bearer);
            _brands.push_back({ bearer->GetGUID(), ObjectGuid::Empty, Brand::Collapsing, _clockMs, 0, 0, 0, {} });
        }
        if (!collapsingIds.empty())
            PairUp(collapsingIds, searingIds);
        Log("brands", Acore::StringFormat("searing={} collapsing={} heroic={}", searing.size(), collapsing.size(),
            _heroic ? 1 : 0));
        if (_hardMode && _engaged)
            _hardMode->OnBrands(*this, searing, collapsing);
        GuidSet all = searing;
        all.insert(collapsing.begin(), collapsing.end());
        return all;
    }

    // DR3: each Collapsing bearer's partner (DrakkisathLogic.h PairCollapsing), a held Stack on the partner that only
    // the bearer must reach (telegraph only: the script ticks).
    void PairUp(std::vector<uint64> const& collapsingIds, std::vector<uint64> const& searingIds)
    {
        std::vector<BrandPlayer> players;
        Unit const* victim = me->GetVictim();
        for (Player* player : FightPlayers())   // the fight's players only, never one outside the hall (R-2 n-2)
        {
            players.push_back({ player->GetGUID().GetRawValue(), DungeonKit::PlaneOf(player), player == victim });
        }
        for (auto const& [bearerId, partnerId] : PairCollapsing(collapsingIds, searingIds, players))
        {
            ObjectGuid const bearerGuid(bearerId);
            ObjectGuid const partnerGuid(partnerId);
            Player* partner = ObjectAccessor::GetPlayer(*me, partnerGuid);
            if (!partner)
                continue;
            BossMechanics::Eligibility who;
            who.carriers.insert(bearerGuid);
            MechanicRef ref = Mechanic::Stack(me, partner, kBrandRadius, Ms(kBrandMs));
            ref.Eligible(who).Within(RoomBounds()).Tag(TAG_DR_COLLAPSING);
            MechanicHandle const handle = ref.Handle();
            Track(handle);
            for (BrandState& b : _brands)
                if (b.bearer == bearerGuid && b.kind == Brand::Collapsing && b.bornMs == _clockMs)
                {
                    b.partner = partnerGuid;
                    b.handle = handle;
                }
            Log("brand-partner", Acore::StringFormat("bearer={} partner={}", bearerGuid.GetCounter(),
                partner->GetName()));
        }
    }

    // The brands tick on the AI's own clock: nothing for kBrandMercyMs, then every second until kBrandMs.
    void UpdateBrands()
    {
        if (_brands.empty())
            return;
        for (BrandState& b : _brands)
        {
            Player* bearer = ObjectAccessor::GetPlayer(*me, b.bearer);
            if (!bearer || !bearer->IsAlive() || bearer->GetMap() != me->GetMap())
            {
                b.ticks = kBrandTicks + 1;      // gone: ends below
                continue;
            }
            while (b.ticks < kBrandTicks && _clockMs >= b.bornMs + BrandTickAtMs(b.ticks + 1))
            {
                ++b.ticks;
                BrandTick(b, bearer);
            }
        }
        std::erase_if(_brands, [this](BrandState const& b)
        {
            if (b.ticks < kBrandTicks)
                return false;
            EndBrand(b);
            return true;
        });
    }

    void BrandTick(BrandState& b, Player* bearer)
    {
        std::vector<Player*> near;
        for (Player* player : FightPlayers())   // R-2 n-2: the fight's players only
        {
            if (player == bearer)
                continue;
            if (player->GetExactDist2d(bearer) > kBrandRadius
                || std::fabs(player->GetPositionZ() - bearer->GetPositionZ()) > kBrandZBand)
                continue;
            near.push_back(player);
        }
        if (b.kind == Brand::Searing)
        {
            me->CastSpell(bearer, SPELL_DR_SEARING_BURN, true);
            for (Player* other : near)
                me->CastSpell(other, SPELL_DR_SEARING_FLARE, true);
            b.othersHit += near.size();
            return;
        }
        me->CastSpell(bearer, near.empty() ? SPELL_DR_COLLAPSING_BURN : SPELL_DR_COLLAPSING_SHARED, true);
        if (!near.empty())
            ++b.pairedTicks;
    }

    void EndBrand(BrandState const& b)
    {
        if (b.handle)
            Mechanic::Cancel(me, b.handle);
        uint32 const aura = b.kind == Brand::Searing ? SPELL_DR_SEARING_BRAND : SPELL_DR_COLLAPSING_BRAND;
        Player* bearer = ObjectAccessor::GetPlayer(*me, b.bearer);
        if (bearer)
            bearer->RemoveAurasDueToSpell(aura, me->GetGUID());
        uint32 const ticks = std::min(b.ticks, kBrandTicks);
        Log("brand-end", Acore::StringFormat("kind={} bearer={} ticks={} others={} paired={}", BrandName(b.kind),
            bearer ? bearer->GetName() : std::string("gone"), ticks, b.othersHit, b.pairedTicks));
    }

    // ---- DR5 Thunderclap --------------------------------------------------------------------------------------------

    void StartThunderclap()
    {
        DungeonKit::CastBar(me, SPELL_DR_THUNDERCLAP_CAST);
        MechanicRef ref = Mechanic::Circle(me, me, kThunderclapRadius, Ms(kThunderclapCastMs));
        ref.Damage(kThunderclapPct).TankDamage(kThunderclapPct).School(SPELL_SCHOOL_NORMAL)
            .Spell(SPELL_DR_THUNDERCLAP).Weakened().Rider(SPELL_DR_THUNDERCLAP_SLOW).Within(RoomBounds())
            .Tag(TAG_DR_THUNDERCLAP);
        ref.OnResolve(OnBoss([](boss_drakkisath_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.me->CastSpell(ai.me, SPELL_DR_THUNDERCLAP_LOOK, true);
            ai.Log("thunderclap-landed", Acore::StringFormat("hits={}", r.hits.size()));
        }));
        Track(ref.Handle());
        Log("thunderclap");
    }

    // ---- DR6 Flamestrike --------------------------------------------------------------------------------------------

    // `targets` empty: the fight's pick (normal 2 / 4 random non-tanks; heroic every player).
    void StartFlamestrike(bool heroicForm, std::vector<Player*> targets)
    {
        if (targets.empty())
        {
            if (heroicForm)
                targets = FightPlayers();
            else
            {
                DungeonKit::PickRule rule;
                rule.nonTank = true;
                targets = DungeonKit::PickPlayers(me, rule, kFlamestrikeTargets.At(_players));
            }
        }
        FlamestrikeStopped("replaced");     // never two sets waiting on one bar
        uint32 const bar = heroicForm ? SPELL_DR_FLAMESTRIKE_CAST_H : SPELL_DR_FLAMESTRIKE_CAST;
        DungeonKit::CastBar(me, bar);
        for (Player* target : targets)
        {
            if (!target)
                continue;
            Position const at = target->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, at, kFlamestrikeRadius, Ms(kFlamestrikeCastMs));
            ref.Damage(kFlamestrikePct).TankDamage(kFlamestrikePct).School(SPELL_SCHOOL_FIRE)
                .Spell(SPELL_DR_FLAMESTRIKE).Weakened().Within(RoomBounds()).Tag(TAG_DR_FLAMESTRIKE);
            ref.OnResolve(OnBoss([at](boss_drakkisath_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.FlamestrikeLanded(at, r.hits.size());
            }));
            MechanicHandle const handle = ref.Handle();
            if (!handle)
                continue;
            Track(handle);
            _flamestrikes.push_back(handle);
        }
        Log("flamestrike", Acore::StringFormat("circles={} heroic={}", _flamestrikes.size(), heroicForm ? 1 : 0));
        // Heroic: a bar that could not start (a silence) stops the circles as a kick does.
        if (heroicForm && !me->HasUnitState(UNIT_STATE_CASTING))
            FlamestrikeStopped("no-cast");
    }

    // The heroic bar was kicked (or could not start): its circles never land.
    void FlamestrikeStopped(char const* why)
    {
        if (_flamestrikes.empty())
            return;
        for (MechanicHandle const& handle : _flamestrikes)
            Mechanic::Cancel(me, handle);
        Log("flamestrike-stopped", Acore::StringFormat("why={} circles={}", why, _flamestrikes.size()));
        _flamestrikes.clear();
    }

    // A circle landed: its burning patch for 15 s (the look a 5 yd dynamic object).
    void FlamestrikeLanded(Position const& at, std::size_t hits)
    {
        _flamestrikes.clear();      // the set resolves together: none left to stop
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kFlamestrikePatchMs - kFlamestrikePatchTickMs);
        linger.tick = Ms(kFlamestrikePatchTickMs);
        linger.pct = kFlamestrikePatchPct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_DR_FLAMESTRIKE_BURN;
        linger.slow = false;
        linger.tag = TAG_DR_PATCH;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(at, kFlamestrikeRadius), linger);
        ref.TankDamage(kFlamestrikePatchPct).Within(RoomBounds());
        Track(ref.Handle());
        me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_DR_FLAMESTRIKE_PATCH, true);
        Log("flamestrike-landed", Acore::StringFormat("at=({:.1f},{:.1f}) hits={}", at.GetPositionX(),
            at.GetPositionY(), hits));
    }

    // ---- DR7 Blackblade Sweep ---------------------------------------------------------------------------------------

    // His facing locks at the wind-up's start, toward his target: the cone is pinned to that spot and facing, so the
    // tank steps to his flank to leave it.
    void StartSweep()
    {
        Unit* victim = me->GetVictim();
        float const facing = victim ? me->GetAbsoluteAngle(victim) : me->GetOrientation();
        me->SetFacingTo(facing);
        Position const at(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        DungeonKit::CastBar(me, SPELL_DR_SWEEP_CAST);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(at, kSweepAngleDeg, kSweepLength),
            Ms(kSweepCastMs));
        ref.Damage(kSweepPct).TankDamage(kSweepPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_DR_BLACKBLADE_SWEEP)
            .Weakened().Within(RoomBounds()).Tag(TAG_DR_SWEEP);
        ref.OnResolve(OnBoss([](boss_drakkisath_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.me->CastSpell(ai.me, SPELL_DR_SWEEP_LOOK, true);
            ai.Log("sweep-landed", Acore::StringFormat("hits={}", r.hits.size()));
        }));
        Track(ref.Handle());
        Log("sweep", Acore::StringFormat("o={:.2f}", facing));
    }

    // ---- DR9 Seared Flesh (10 players) ------------------------------------------------------------------------------

    // His blade needs him free (no wind-up, no hard mode hold, his melee on) and his target in reach.
    bool CanStrike(Unit* victim) const
    {
        return victim && !Busy() && Uses(Ability::Melee) && me->IsWithinMeleeRange(victim);
    }

    void SearedFlesh()
    {
        if (_now < _nextSearedAt || !Uses(Ability::SearedFlesh))
            return;
        Unit* victim = me->GetVictim();
        if (!CanStrike(victim))
            return;     // every tick until he can (the stacks hold meanwhile)
        Strike(victim);
    }

    void Strike(Unit* victim)
    {
        if (!victim || !victim->IsAlive())
            return;
        uint32 const stacks = DungeonKit::AddStacks(victim, SPELL_DR_SEARED_FLESH, 1, me, kSearedFleshMax);
        DungeonKit::ShortenAura(victim, SPELL_DR_SEARED_FLESH, me->GetGUID(), Ms(kSearedFleshMs));
        if (victim->GetGUID() == _searedHeldOn)
            _searedHeldMs = 0;      // the strike sets the duration afresh
        _nextSearedAt = _now + kSearedFleshEveryMs;
        Log("seared-flesh", Acore::StringFormat("on={} stacks={}", victim->GetName(), stacks));
    }

    // His target's Seared Flesh holds while he cannot strike it (DrakkisathLogic.h): applied a second at a time; a new
    // target drops what the old one had banked.
    void HoldSearedFlesh(uint32 diff)
    {
        Unit* victim = me->GetVictim();
        ObjectGuid const on = victim ? victim->GetGUID() : ObjectGuid::Empty;
        if (on != _searedHeldOn)
        {
            _searedHeldOn = on;
            _searedHeldMs = 0;
        }
        if (!victim || !Uses(Ability::SearedFlesh))
            return;
        bool const holding = !CanStrike(victim);
        if (holding)
            _searedHeldMs += diff;
        if (!_searedHeldMs)
            return;
        Aura* aura = victim->GetAura(SPELL_DR_SEARED_FLESH, me->GetGUID());
        if (!aura)
        {
            _searedHeldMs = 0;
            return;
        }
        if (holding && !SearedFleshHoldDue(_searedHeldMs, aura->GetDuration()))
            return;
        DungeonKit::ShortenAura(victim, SPELL_DR_SEARED_FLESH, me->GetGUID(),
            Milliseconds(aura->GetDuration() + static_cast<int32>(_searedHeldMs)));
        _searedHeldMs = 0;
    }

    // ---- cleanup ----------------------------------------------------------------------------------------------------

    // The pull's state, gone: the hard mode's own end first, every mechanic, the brands, the patches, every summon, the
    // Guards' holds, his root.
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _flamestrikes.clear();
        for (BrandState const& b : _brands)
            EndBrand(b);
        _brands.clear();
        while (me->RemoveDynObject(SPELL_DR_FLAMESTRIKE_PATCH))
            ;
        summons.DespawnAll();
        for (Creature* guard : Guards())
            if (auto* ai = GuardAI(guard))
                ai->Release();
        _guards.clear();
        if (_rooted)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _rooted = false;
        _queue.Reset();
        _now = 0;
        _holdUntil = 0;
        _nextBrandAt = 0;
        _nextRageAt = 0;
        _nextSearedAt = 0;
        _searedHeldOn.Clear();
        _searedHeldMs = 0;
        _players = 0;
        _engaged = false;
        _arena.Reset();
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DR_SEARED_FLESH);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DR_SEARING_BRAND);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DR_COLLAPSING_BRAND);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DR_THUNDERCLAP_SLOW);
        }
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    std::unique_ptr<DrakkisathHardMode> _hardMode;
    std::vector<MechanicHandle> _live;
    std::vector<MechanicHandle> _flamestrikes;      // the circles waiting on the current Flamestrike bar
    std::vector<BrandState> _brands;
    GuidVector _guards;
    ObjectGuid _searedHeldOn;
    uint32 _searedHeldMs = 0;
    uint64 _clockMs = 0;            // ms the AI has run (the brands' clock; never held)
    uint64 _now = 0;                // ms since the pull
    uint64 _holdUntil = 0;          // _now: a hard mode cast holds him until then
    uint64 _nextBrandAt = 0;
    uint64 _nextRageAt = 0;
    uint64 _nextSearedAt = 0;
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    bool _heroic = false;
    bool _engaged = false;
    bool _rooted = false;
};

void npc_brs_chromatic_elite_guard::JustDied(Unit* /*killer*/)
{
    EndHold();
    InstanceScript* instance = me->GetInstanceScript();
    Creature* boss = instance ? instance->GetCreature(BOSS_DRAKKISATH) : nullptr;
    if (boss && boss->IsAlive() && boss->IsAIEnabled)
        if (auto* ai = dynamic_cast<boss_drakkisath_rework*>(boss->AI()))
            ai->GuardDied(me);
}

namespace
{
    boss_drakkisath_rework* FindDrakkisathAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_DRAKKISATH);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_drakkisath_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Drakkisath is not running boss_drakkisath_rework (check the ScriptName).");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_DRAKKISATH, BOSS_DRAKKISATH);
    }

    // `.dbtest brs drakkisath state`: the clock, the queue, the brands, the Guards, the stacks.
    bool HandleState(ChatHandler* handler)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Drakkisath: {}", ai->TestState());
        return true;
    }

    bool Brand(ChatHandler* handler, BrsDrakkisath::Brand kind)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestBrand(target, kind);
        handler->PSendSysMessage("Drakkisath: a {} Brand on {} ({}).", BrandName(kind), target->GetName(),
            kind == BrsDrakkisath::Brand::Searing ? "DR2" : "DR3");
        return true;
    }

    // `.dbtest brs drakkisath searing`: a Searing Brand on the selected player (or you) (DR2).
    bool HandleSearing(ChatHandler* handler)
    {
        return Brand(handler, BrsDrakkisath::Brand::Searing);
    }

    // `.dbtest brs drakkisath collapsing`: a Collapsing Brand on the selected player (or you) and its partner (DR3).
    bool HandleCollapsing(ChatHandler* handler)
    {
        return Brand(handler, BrsDrakkisath::Brand::Collapsing);
    }

    // `.dbtest brs drakkisath thunderclap`: Thunderclap now (DR5).
    bool HandleThunderclap(ChatHandler* handler)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        if (!ai)
            return false;
        ai->TestThunderclap();
        handler->PSendSysMessage("{}", "Drakkisath: Thunderclap (DR5).");
        return true;
    }

    // `.dbtest brs drakkisath flamestrike [0|1]`: a Flamestrike circle at the selected player's (or your) spot (DR6);
    // 1 = the heroic bar (interruptible).
    bool HandleFlamestrike(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestFlamestrike(target, isHeroic);
        handler->PSendSysMessage("Drakkisath: Flamestrike at {}'s spot ({} bar) (DR6).", target->GetName(),
            isHeroic ? "heroic, interruptible" : "normal");
        return true;
    }

    // `.dbtest brs drakkisath sweep`: Blackblade Sweep now, toward his target (DR7).
    bool HandleSweep(ChatHandler* handler)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        if (!ai)
            return false;
        ai->TestSweep();
        handler->PSendSysMessage("{}", "Drakkisath: Blackblade Sweep (DR7).");
        return true;
    }

    // `.dbtest brs drakkisath seared`: a Seared Flesh stack on the selected player (or you) (DR9; in the fight it runs
    // at 10 players only).
    bool HandleSeared(ChatHandler* handler)
    {
        boss_drakkisath_rework* ai = FindDrakkisathAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestSearedFlesh(target);
        handler->PSendSysMessage("Drakkisath: a Seared Flesh stack on {} (DR9).", target->GetName());
        return true;
    }

    ChatCommandTable const& DrakkisathTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "state",       HandleState,       SEC_GAMEMASTER, Console::No },
            { "searing",     HandleSearing,     SEC_GAMEMASTER, Console::No },
            { "collapsing",  HandleCollapsing,  SEC_GAMEMASTER, Console::No },
            { "thunderclap", HandleThunderclap, SEC_GAMEMASTER, Console::No },
            { "flamestrike", HandleFlamestrike, SEC_GAMEMASTER, Console::No },
            { "sweep",       HandleSweep,       SEC_GAMEMASTER, Console::No },
            { "seared",      HandleSeared,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_drakkisath_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_drakkisath_rework, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_chromatic_elite_guard, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("drakkisath", DrakkisathTestCommands());
}
