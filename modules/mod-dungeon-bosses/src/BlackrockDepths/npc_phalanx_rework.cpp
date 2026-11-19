/*
 * mod-dungeon-bosses, Blackrock Depths D19: Phalanx (9502), the Grim Guzzler's bouncer, and the heroic Rowdy Patrons
 * (300841). Build spec S4 "Phalanx" (docs/dungeons/blackrock-depths-4-imperial-seat.md, PH1-PH6; rulings 63-66),
 * handoff sections 3.4 (row D19: KT-D2's DamageLedger), 3.5, 3.8 (NM: the bar's upper floor, the seven tables, the
 * tank's Spot), 3.10 and section 7 #12 (a section 4 Finder group opens the Bar Door by any of the four ways; the new
 * gossip makes it always possible). Replaces stock `npc_phalanx` (blackrock_depths.cpp 405-598): its DORMANT /
 * MOVING_TO_DOOR / ACTIVE machine is re-implemented here as it was (Cala's CMaNGOS Grim Guzzler staging, the stock
 * file's own credit: cmangos/mangos-wotlk 563770518af7) and its combat rewritten. He has no SmartAI (verified live).
 * Bound by apps/dbc-tools source/npcs/blackrock_depths/phalanx.py. Pure rules: PhalanxLogic.h.
 *
 *   The state machine (stock, plus the gossip start)
 *     DORMANT        faction 35 in his corner, gossip menu 2283. Three wake-ups, once: Rocknot's ale run
 *                    (DoAction ACTION_PHALANX_START_ACTIVATION), Plugger's death (his SmartAI sets faction 14 on him:
 *                    seen here, D17 section 0) and, new (ruling 66), the gossip option "start a fight"
 *     MOVING_TO_DOOR DATA_PHALANX_ACTIVATED saved at once; passive, he runs path 95020 to the door node, yells line 0
 *                    200 ms later; a 15 s watchdog activates him where he stands. Damage on the walk wakes him at once
 *                    (rule 10)
 *     ACTIVE         faction 54, aggressive, home = the door node. A reload with the flag saved starts here
 *   His death writes slot 12 DONE: the instance opens the Bar Door (GO_STATE_ACTIVE, also on every load: S0).
 *
 *   PH1 Mighty Blow      stock 14099 copy: 15 s, then every 10 s, on his victim: 25% / 30% of the tank row and the
 *                        stock knockback (heroic: the tank knocked into a table smashes it, PH6)
 *   PH2 Thunderclap      stock 15588 copy: 12 s, then every 10 s: 10 yd, 10% / 12% and a 10 s Magic slow (-40%
 *                        movement, -34% attack speed): the dispel list (a reward on normal, expected on heroic)
 *   PH3 Fireball Volley  stock 15285 copy: from 50% health, at once then every 10 s: 20 yd, 12% / 15%
 *   PH4 Throw Out        10 s, then every 20 s (heroic 15 s): the top damage dealer of the last 10 s (KT-D2's ledger,
 *                        on him and his Rowdy Patrons; never his victim, never the last one thrown) is held 1 s (emote
 *                        line 1) and thrown 15-25 yd onto open floor (never onto a table); the 6 yd landing circle
 *                        shows at the grab: anyone else in it 30% / 45% + Weakened, the thrown player 15% / 25%
 *   PH5 Last Call        20 s, then every 30 s (heroic 25 s): yell line 2, a 3 s cast while he stands still, then a
 *                        pulse knocking back everyone within 10 yd (heroic 12 yd), the tank too: 25% / 40% + Weakened
 *   PH6 Property Damage  heroic: a player knocked by Last Call or Mighty Blow to within about 2 yd of a table smashes
 *                        it: 25% + Weakened, yell line 3, an Outrage stack on him (+15% damage, 5 at most), two Rowdy
 *                        Patrons at the table, its chairs gone and its wood chips flying. Each table breaks once
 *
 *   A throw and Last Call never run at once; the stock casts wait for Last Call's bar (PhalanxLogic.h Timeline). The
 *   tank holds him at the open Spot by the door (bots: a hidden tank-only Park circle). Boss data: kill order Rowdy
 *   Patron, then Phalanx; dispel list Thunderclap; no interrupt list.
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd phalanx <mechanic> ..."
 * (module.dungeonbosses). Lambdas the registry keeps capture guids and values only. Every end of the fight (reset,
 * evade, death) releases a held player, removes his auras and the players', despawns the patrons and the stalkers and
 * brings the smashed tables' chairs back.
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
#include "DungeonKitLedger.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PhalanxLogic.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <functional>
#include <list>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdPhalanx;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "phalanx";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogPh(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    char const* RequestName(PhalanxRequest request)
    {
        switch (request)
        {
            case PhalanxRequest::AleRun:        return "ale-run";
            case PhalanxRequest::PluggerDeath:  return "plugger-death";
            case PhalanxRequest::Gossip:        return "gossip";
        }
        return "?";
    }

    // A player who may take part: alive, in the world, not a game master.
    bool FightCandidate(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The bots' hard bounds while a mechanic of the fight is in view (Last Call, the Throw Out landing, the tank's
    // Park): PhalanxLogic.h BotFloor, the throw floor and the door alcove on the bar floor's height. An escape never
    // plans onto the stairs or the lower level, out of the healer's range and sight of the tank (PHALANX-DIAG).
    std::vector<Position> AtBarFloor(Vec2 const* first, Vec2 const* last)
    {
        std::vector<Position> out;
        out.reserve(std::size_t(last - first));
        for (Vec2 const* p = first; p != last; ++p)
            out.emplace_back(p->x, p->y, kBarFloorZ, 0.f);
        return out;
    }

    BossMechanics::SpotBounds BarFloorBounds()
    {
        return BossMechanics::SpotBounds()
            .Polygon(AtBarFloor(kThrowFloorPolygon.data(), kThrowFloorPolygon.data() + kThrowFloorPolygon.size()),
                kBarFloorZMin, kBarFloorZMax)
            .Polygon(AtBarFloor(kDoorAlcovePolygon.data(), kDoorAlcovePolygon.data() + kDoorAlcovePolygon.size()),
                kBarFloorZMin, kBarFloorZMax);
    }

    // The test commands' forced mechanics (`.dbtest brd phalanx ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Throw,
        LastCall,
        Clap,
        Blow,
        Volley,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Phalanx 9502
// ---------------------------------------------------------------------------------------------------------------------
struct npc_phalanx_rework : public BossAI
{
private:
    // PH4: one throw from the grab to the landing.
    struct Throw
    {
        enum class Step : uint8
        {
            None,
            Held,       // the 1 s hold
            Flying,     // the 1 s flight
        };

        Step step = Step::None;
        ObjectGuid target;
        Position landing;
        uint64 throwAtMs = 0;       // the hold ends, the flight starts
        uint64 landAtMs = 0;        // the flight ends (the circle resolves)
        float thrownPct = 0.f;
        char const* pick = "";
    };

    // PH6: a player knocked back (Last Call, Mighty Blow), watched for a table on the way.
    struct Knock
    {
        ObjectGuid guid;
        uint64 atMs = 0;
        char const* source = "";
    };

public:
    explicit npc_phalanx_rework(Creature* creature)
        : BossAI(creature, BOSS_PHALANX), _arena(BarUpperArena(), LeashOptions(kBoss)), _floor(ThrowFloor()),
        _ledger(Milliseconds(kLedgerWindowMs)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks: the state machine (stock), the pull, the ends
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the summon list (the patrons, the stalkers)
        Cleanup();
        // Stock Reset: a woken Phalanx stays awake (an evade); a reload with the saved flag starts awake at the door.
        bool const restoring = _state == PhalanxState::Dormant && instance
            && instance->GetData(DATA_PHALANX_ACTIVATED) == DONE;
        if (_state != PhalanxState::Dormant || restoring)
        {
            Activate();
            // An evade already walks home; a fresh spawn must walk to the door, without the yell.
            if (restoring)
            {
                me->GetMotionMaster()->MoveTargetedHome();
                LogPh("restored", "awake at the door (DATA_PHALANX_ACTIVATED saved)");
            }
        }
        else
        {
            me->RestoreFaction();
            me->SetReactState(REACT_AGGRESSIVE);
            me->SetNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        }
    }

    void JustEngagedWith(Unit* who) override
    {
        // Engaged on the walk (the Plugger route leaves him faction 14 and passive) or by a GM: he fights at once.
        if (_state != PhalanxState::Active)
            Activate();
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogPh("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        // Waypoint movement updates home at each node: an evade on the walk still returns to the door (stock).
        if (_state != PhalanxState::Dormant)
            SetDoorHome();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_PH_DEATH);
        _state = PhalanxState::Dead;
        Cleanup();
        BossAI::JustDied(killer);       // slot 12 DONE: the instance opens the Bar Door (ruling 66)
        LogPh("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    // The ledger (PH4): every hit on him, pets for their owner. A hit on the walk wakes him (rule 10).
    void DamageTaken(Unit* who, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (who && damage)
            _ledger.Record(who, damage);
        if (WakesOnDamage(_state) && who && who->IsControlledByPlayer())
        {
            LogPh("woken", Acore::StringFormat("by={} (hit on the walk)", who->GetName()));
            Activate();
        }
    }

    // A Rowdy Patron's hits count for the ledger too ("the most trouble" in the bar).
    void RecordTrouble(Unit* who, uint32 damage)
    {
        if (who && damage)
            _ledger.Record(who, damage);
    }

    void DoAction(int32 action) override
    {
        if (action == ACTION_PHALANX_START_ACTIVATION)
            StartActivation(PhalanxRequest::AleRun);
    }

    // Ruling 66: the new gossip option on the dormant Phalanx (menu 2283 option 0, the SQL rev).
    void sGossipSelect(Player* player, uint32 menuId, uint32 gossipListId) override
    {
        if (menuId != kGossipMenu || gossipListId != kGossipOption)
            return;
        CloseGossipMenuFor(player);
        if (_state != PhalanxState::Dormant)
            return;
        LogPh("gossip-start", Acore::StringFormat("player={}", player->GetName()));
        StartActivation(PhalanxRequest::Gossip);
    }

    void PathEndReached(uint32 pathId) override
    {
        if (pathId != kPathDoor || _state != PhalanxState::MovingToDoor)
            return;
        Activate();
        // Zero-delay waypoints do not apply their facing; the sniff turns him after arrival (stock).
        me->SetFacingTo(kDoorNode.o);
        LogPh("at-door");
    }

    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
        if (summon->GetEntry() != NPC_BRD_ROWDY_PATRON)
        {
            summon->SetReactState(REACT_PASSIVE);       // a stalker: a look only
            return;
        }
        Mechanic::TrackUnit(me, summon);
        if (me->IsEngaged())
            DoZoneInCombat(summon);
    }

    // PH5: Last Call's bar never fails while he is stun immune and the bar is not kickable; if it ever does, the pulse
    // goes with it (rule 13).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || spell->Id != SPELL_PH_LAST_CALL_CAST || !_lastCall)
            return;
        Mechanic::Cancel(me, _lastCall);
        _lastCall = MechanicHandle{};
        LogPh("last-call-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (PluggerDeathSeen(_state, me->GetFaction()))
            StartActivation(PhalanxRequest::PluggerDeath);
        UpdateStaging();
        UpdateThrow();      // a throw and the knocks run to their end out of combat too (`.dbtest`)
        WatchKnocks();

        if (_state != PhalanxState::Active || !UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (_fighting)
            RunTimers();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // The state machine
    // ----------------------------------------------------------------------------------------------------------------

    void SetDoorHome()
    {
        me->SetHomePosition(kDoorNode.x, kDoorNode.y, kDoorNode.z, kDoorNode.o);
    }

    // Once, from DORMANT: the saved flag, passive, the run to the door, the yell, the watchdog.
    void StartActivation(PhalanxRequest why)
    {
        if (_state != PhalanxState::Dormant)
            return;
        _state = PhalanxState::MovingToDoor;
        SetDoorHome();
        if (instance)
            instance->SetData(DATA_PHALANX_ACTIVATED, DONE);    // the instance saves it
        me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        // The sniff keeps him interactive on the run, changes the faction on arrival and yells shortly after starting.
        me->SetReactState(REACT_PASSIVE);
        me->SetWalk(false);
        me->GetMotionMaster()->MoveWaypoint(kPathDoor, false);
        _yellAtMs = _clockMs + kYellDelayMs;
        _watchdogAtMs = _clockMs + kWalkWatchdogMs;
        LogPh("activation", Acore::StringFormat("source={}", RequestName(why)));
    }

    void UpdateStaging()
    {
        if (_yellAtMs && _clockMs >= _yellAtMs)
        {
            _yellAtMs = 0;
            Talk(SAY_PH_DOOR);
        }
        if (_watchdogAtMs && _clockMs >= _watchdogAtMs)
        {
            _watchdogAtMs = 0;
            if (_state == PhalanxState::MovingToDoor)
            {
                // A blocked route must not leave him passive for good, nor teleport him (stock).
                LogPh("watchdog", "the walk stalled: awake where he stands");
                Activate();
            }
        }
    }

    void Activate()
    {
        _state = PhalanxState::Active;
        _watchdogAtMs = 0;
        SetDoorHome();
        me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        me->SetFaction(kFactionAwake);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull, the clocks
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PHALANX;
        Mechanic::BeginEncounter(me, options);
        _registered = true;
        _arena.Engage(me);
        _fighting = true;
        _timeline.Start(_heroic, _clockMs);
        Describe();
        PostPark();
        LogPh("engage", Acore::StringFormat("heroic={} throw={}s last-call={}s clap={}s blow={}s", _heroic ? 1 : 0,
            kThrowFirstMs / 1000, kLastCallFirstMs / 1000, kThunderclapFirstMs / 1000, kMightyBlowFirstMs / 1000));
    }

    // Boss data (S4 "Boss data"): kill order Rowdy Patron, then Phalanx; dispel list Thunderclap (a reward on normal,
    // expected on heroic: the higher priority there); no interrupt list.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_BRD_ROWDY_PATRON, 2, BossMechanics::Who::Dps);
        d.targets.emplace_back(NPC_PHALANX, 1, BossMechanics::Who::Any);
        d.dispels.emplace_back(SPELL_PH_THUNDERCLAP, _heroic ? 2 : 1);
        Mechanic::Describe(me, std::move(d));
    }

    // The tank's open Spot by the door (bots only: a hidden tank-only Park circle), renewed while the fight lasts.
    void PostPark()
    {
        if (_park)
            Mechanic::Cancel(me, _park);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, Position(kTankSpot.x, kTankSpot.y, kTankSpot.z, kDoorNode.o),
            kParkRadiusYd, Ms(kParkRenewMs + 5000));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Within(BarFloorBounds()).Tag(TAG_PH_PARK);
        _park = ref.Handle();
        Track(_park);
        _parkAtMs = _clockMs + kParkRenewMs;
    }

    void RunTimers()
    {
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        bool const throwing = _throw.step != Throw::Step::None;

        if (!_volleyArmed && me->HealthBelowPct(int32(kVolleyHealthPct)))
        {
            _volleyArmed = true;
            _timeline.ArmVolley(_clockMs);
            LogPh("volley-armed", Acore::StringFormat("health={:.0f}%", me->GetHealthPct()));
        }
        if (_clockMs >= _parkAtMs)
            PostPark();

        if (_timeline.Due(Beat::ThrowOut, _clockMs))
        {
            if (!MayStart(Beat::ThrowOut, throwing, casting))
                _timeline.Retry(Beat::ThrowOut, _clockMs);
            else
            {
                // No one to throw (a solo tank) or no floor: the beat passes, the next one comes on time.
                if (!StartThrow(nullptr))
                    LogPh("throw-out-skipped", "nobody to throw or no landing");
                _timeline.Fired(Beat::ThrowOut, _clockMs);
            }
        }
        if (_timeline.Due(Beat::LastCall, _clockMs))
        {
            if (MayStart(Beat::LastCall, _throw.step != Throw::Step::None, me->HasUnitState(UNIT_STATE_CASTING))
                && StartLastCall())
                _timeline.Fired(Beat::LastCall, _clockMs);
            else
                _timeline.Retry(Beat::LastCall, _clockMs);
        }
        if (_timeline.Due(Beat::Thunderclap, _clockMs))
        {
            if (MayStart(Beat::Thunderclap, false, me->HasUnitState(UNIT_STATE_CASTING)) && CastThunderclap())
                _timeline.Fired(Beat::Thunderclap, _clockMs);
            else
                _timeline.Retry(Beat::Thunderclap, _clockMs);
        }
        if (_timeline.Due(Beat::MightyBlow, _clockMs))
        {
            if (MayStart(Beat::MightyBlow, false, me->HasUnitState(UNIT_STATE_CASTING)) && CastMightyBlow())
                _timeline.Fired(Beat::MightyBlow, _clockMs);
            else
                _timeline.Retry(Beat::MightyBlow, _clockMs);
        }
        if (_timeline.Due(Beat::Volley, _clockMs))
        {
            if (MayStart(Beat::Volley, false, me->HasUnitState(UNIT_STATE_CASTING)) && CastVolley())
                _timeline.Fired(Beat::Volley, _clockMs);
            else
                _timeline.Retry(Beat::Volley, _clockMs);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PH1-PH3: the kept stock casts (copies in the slice; the percents ride in the spells, the kit's refflat script)
    // ----------------------------------------------------------------------------------------------------------------

    bool CastMightyBlow()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return false;
        me->CastSpell(victim, SPELL_PH_MIGHTY_BLOW, true);
        if (victim->IsPlayer())
            WatchKnock(victim, "mighty-blow");
        LogPh("mighty-blow", Acore::StringFormat("target={} pct={:.0f}", victim->GetName(), kMightyBlowPct(_heroic)));
        return true;
    }

    bool CastThunderclap()
    {
        me->CastSpell(me, SPELL_PH_THUNDERCLAP, true);
        LogPh("thunderclap", Acore::StringFormat("pct={:.0f} r={:.0f}", kThunderclapPct(_heroic),
            kThunderclapRadiusYd));
        return true;
    }

    bool CastVolley()
    {
        me->CastSpell(me, SPELL_PH_FIREBALL_VOLLEY, true);
        LogPh("fireball-volley", Acore::StringFormat("pct={:.0f} r={:.0f}", kVolleyPct(_heroic), kVolleyRadiusYd));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PH4 Throw Out
    // ----------------------------------------------------------------------------------------------------------------

    std::vector<Player*> FightPlayers()
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

    bool OnBarFloor(Player const* player) const
    {
        return player && _arena.Contains(player);
    }

    // The ledger's top damage dealer of the last 10 s (never the victim, never the last one thrown, on the floor);
    // with nobody in the ledger, a random player by the same rule (KT-D2 question 4's default). Null: nobody.
    Player* PickThrowTarget(char const*& how)
    {
        Unit const* victim = me->GetVictim();
        ObjectGuid const victimGuid = victim ? victim->GetGUID() : ObjectGuid::Empty;
        Player* top = _ledger.Top(me, { victimGuid, _lastThrown }, [this](Player* p)
        {
            return FightCandidate(p) && OnBarFloor(p);
        });
        if (top)
        {
            how = "ledger";
            return top;
        }
        std::vector<Player*> pool;
        for (Player* p : FightPlayers())
            if (ThrowEligible(p->GetGUID() == victimGuid, p->GetGUID() == _lastThrown, OnBarFloor(p)))
                pool.push_back(p);
        if (pool.empty())
            return nullptr;
        how = "random";
        return pool[urand(0, uint32(pool.size() - 1))];
    }

    // Open floor 15-25 yd from the thrown player: on the throw floor, reachable from them, clear of the tables and the
    // pillar; the measured spots as the fallback.
    std::optional<Position> PickLanding(Player* target)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(target);
        rules.minRange = kThrowMinYd;
        rules.maxRange = kThrowMaxYd;
        for (Vec2 const& t : kTables)
            rules.avoid.push_back({ t, kTableAvoidYd });
        rules.avoid.push_back({ kPillar, kPillarRadiusYd });
        rules.tries = 32;
        rules.bestEffort = true;
        DungeonKit::FloorProbe probe;
        probe.z = kBarFloorZ;
        probe.zBand = kFloorZBandYd;
        probe.reachable = true;
        std::vector<Vec2> const fixed(kFixedLandings.begin(), kFixedLandings.end());
        return DungeonKit::PickFloorSpot(target, &_floor, rules, probe, fixed);
    }

    // The grab: the 6 yd landing circle (everyone else; the thrown player has their own hit), the hold, the emote.
    // `forced` (a test) skips the pick. False: nobody to throw, or no landing.
    bool StartThrow(Player* forced)
    {
        char const* how = "forced";
        Player* target = forced ? forced : PickThrowTarget(how);
        if (!target)
            return false;
        std::optional<Position> const landing = PickLanding(target);
        if (!landing)
            return false;

        float const scale = OutrageScale(OutrageStacks());
        float const othersPct = kLandingPct(_heroic) * scale;
        // Everyone in the fight but the thrown player (and his own guid, so the set is never empty: empty = everyone).
        BossMechanics::Eligibility others;
        others.carriers.insert(me->GetGUID());
        for (Player* p : FightPlayers())
            if (p != target)
                others.carriers.insert(p->GetGUID());
        MechanicRef ref = Mechanic::Circle(me, *landing, kLandingRadiusYd, Ms(kThrowWarnMs));
        ref.Damage(othersPct).TankDamage(othersPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_PH_THROW_OUT).Weakened()
            .Eligible(others).Within(BarFloorBounds()).Tag(TAG_PH_THROW_OUT);
        if (!ref.IsValid())
        {
            LogPh("throw-out-refused", target->GetName());
            return false;
        }
        Track(ref.Handle());

        me->CastSpell(target, SPELL_PH_GRAB, true);
        Talk(EMOTE_PH_GRAB, target);
        _throw = Throw{};
        _throw.step = Throw::Step::Held;
        _throw.target = target->GetGUID();
        _throw.landing = *landing;
        _throw.throwAtMs = _clockMs + kGrabMs;
        _throw.landAtMs = _clockMs + kThrowWarnMs;
        _throw.thrownPct = kThrownPct(_heroic) * scale;
        _throw.pick = how;
        _lastThrown = target->GetGUID();
        LogPh("throw-out", Acore::StringFormat("heroic={} target={} pick={} total={} to=({:.1f}, {:.1f}) yd={:.1f} "
            "thrown={:.0f}% others={:.0f}% outrage={}", _heroic ? 1 : 0, target->GetName(), how,
            _ledger.Total(target->GetGUID()), landing->GetPositionX(), landing->GetPositionY(),
            target->GetExactDist2d(landing->GetPositionX(), landing->GetPositionY()), _throw.thrownPct, othersPct,
            OutrageStacks()));
        return true;
    }

    Player* ThrownPlayer() const
    {
        if (_throw.target.IsEmpty())
            return nullptr;
        Player* p = ObjectAccessor::GetPlayer(*me, _throw.target);
        return p && p->IsInWorld() && p->IsAlive() && p->GetMap() == me->GetMap() ? p : nullptr;
    }

    // The hold's end (the throw) and the flight's end (the landing). A thrown player who died or left is let go; the
    // circle still lands for the others.
    void UpdateThrow()
    {
        if (_throw.step == Throw::Step::Held && _clockMs >= _throw.throwAtMs)
        {
            Player* p = ThrownPlayer();
            if (!p)
            {
                LogPh("throw-out-dropped", "the held player is gone");
                _throw = Throw{};
                return;
            }
            p->RemoveAurasDueToSpell(SPELL_PH_GRAB, me->GetGUID());
            float const yd = p->GetExactDist2d(_throw.landing.GetPositionX(), _throw.landing.GetPositionY());
            DungeonKit::JumpTo(p, _throw.landing, ThrowSpeedXY(yd), 0.f, SPELL_PH_THROW_LOOK, me);
            _throw.step = Throw::Step::Flying;
            LogPh("throw-out-flight", Acore::StringFormat("target={} yd={:.1f}", p->GetName(), yd));
        }
        else if (_throw.step == Throw::Step::Flying && _clockMs >= _throw.landAtMs)
        {
            me->CastSpell(_throw.landing.GetPositionX(), _throw.landing.GetPositionY(), _throw.landing.GetPositionZ(),
                SPELL_PH_SLAM_LOOK, true);
            if (Player* p = ThrownPlayer())
            {
                DungeonKit::RegistryHitSpec spec;
                spec.pct = _throw.thrownPct;
                spec.tankPct = _throw.thrownPct;
                spec.school = SPELL_SCHOOL_NORMAL;
                spec.spellId = SPELL_PH_THROWN;
                spec.weakened = false;      // not a failure (S4)
                spec.tag = TAG_PH_THROWN;
                Track(DungeonKit::RegistryHit(me, GuidSet{ p->GetGUID() }, spec));
                LogPh("throw-out-landed", Acore::StringFormat("target={} pct={:.0f}", p->GetName(), spec.pct));
            }
            _throw = Throw{};
        }
    }

    // Lets the held player go (a reset, an evade, his death).
    void ReleaseThrow()
    {
        if (!_throw.target.IsEmpty())
            if (Player* p = ObjectAccessor::GetPlayer(*me, _throw.target))
                p->RemoveAurasDueToSpell(SPELL_PH_GRAB, me->GetGUID());
        _throw = Throw{};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PH5 Last Call
    // ----------------------------------------------------------------------------------------------------------------

    bool StartLastCall()
    {
        float const r = kLastCallRadiusYd(_heroic);
        float const pct = kLastCallPct(_heroic) * OutrageScale(OutrageStacks());
        float const x = me->GetPositionX();
        float const y = me->GetPositionY();
        bool const heroic = _heroic;
        MechanicRef ref = Mechanic::Circle(me, me, r, Ms(kLastCallCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_PH_LAST_CALL).Weakened()
            .Within(BarFloorBounds()).Tag(TAG_PH_LAST_CALL)
            .OnHit(OnPhalanxHit([x, y, heroic](npc_phalanx_rework& ai, Unit* hit)
            {
                ai.LastCallHit(hit, x, y, heroic);
            }))
            .OnResolve(OnPhalanx([](npc_phalanx_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.LastCallLands(r);
            }));
        if (!ref.IsValid())
        {
            LogPh("last-call-refused", "the registry refused the pulse");
            return false;
        }
        _lastCall = ref.Handle();
        Track(_lastCall);
        DungeonKit::CastBar(me, SPELL_PH_LAST_CALL_CAST);     // he stands still for the bar
        Talk(YELL_PH_LAST_CALL);
        LogPh("last-call", Acore::StringFormat("heroic={} r={:.0f} pct={:.0f} outrage={}", _heroic ? 1 : 0, r, pct,
            OutrageStacks()));
        return true;
    }

    // Each unit the pulse hits is knocked back from where he stood; on heroic a player is watched for a table.
    void LastCallHit(Unit* hit, float x, float y, bool heroic)
    {
        if (!hit || !hit->IsAlive())
            return;
        hit->KnockbackFrom(x, y, kLastCallKnockSpeedXY, kLastCallKnockSpeedZ);
        if (heroic && hit->IsPlayer())
            WatchKnock(hit, "last-call");
    }

    void LastCallLands(BossMechanics::ResolveResult const& r)
    {
        _lastCall = MechanicHandle{};
        me->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), SPELL_PH_SLAM_LOOK, true);
        LogPh("last-call-pulse", Acore::StringFormat("hits={}", r.hits.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PH6 Property Damage (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 OutrageStacks() const
    {
        return DungeonKit::Stacks(me, SPELL_PH_OUTRAGE);
    }

    void WatchKnock(Unit* who, char const* source)
    {
        if (!_heroic || !who)
            return;
        for (Knock& k : _knocks)
            if (k.guid == who->GetGUID())
            {
                k.atMs = _clockMs;
                k.source = source;
                return;
            }
        _knocks.push_back({ who->GetGUID(), _clockMs, source });
    }

    void WatchKnocks()
    {
        for (auto it = _knocks.begin(); it != _knocks.end();)
        {
            if (KnockExpired(_clockMs, it->atMs))
            {
                it = _knocks.erase(it);
                continue;
            }
            if (!KnockWatched(_clockMs, it->atMs))
            {
                ++it;
                continue;
            }
            Player* p = ObjectAccessor::GetPlayer(*me, it->guid);
            if (!p || !p->IsAlive() || p->GetMap() != me->GetMap())
            {
                it = _knocks.erase(it);
                continue;
            }
            std::optional<std::size_t> const table = SmashedTable(DungeonKit::PlaneOf(p), p->GetPositionZ(), _tables);
            if (!table)
            {
                ++it;
                continue;
            }
            char const* source = it->source;
            it = _knocks.erase(it);
            Smash(*table, p, source);
        }
    }

    // A table breaks: the smasher's hit, Outrage, the yell, the wood chips, the chairs, two Rowdy Patrons.
    void Smash(std::size_t table, Player* smasher, char const* source)
    {
        _tables.Break(table);
        if (smasher)
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kSmashPct;
            spec.tankPct = kSmashPct;
            spec.school = SPELL_SCHOOL_NORMAL;
            spec.spellId = SPELL_PH_TABLE_SMASH;
            spec.weakened = true;
            spec.tag = TAG_PH_SMASH;
            Track(DungeonKit::RegistryHit(me, GuidSet{ smasher->GetGUID() }, spec));
        }
        me->CastSpell(me, SPELL_PH_OUTRAGE, true);     // a stack (5 at most), the roar
        Talk(YELL_PH_PROPERTY_DAMAGE);

        Vec2 const at = kTables[table];
        Position const spot(at.x, at.y, kBarFloorZ, 0.f);
        if (Creature* stalker = me->SummonCreature(NPC_BRD_STALKER_WAVE_2, spot, TEMPSUMMON_TIMED_DESPAWN,
            kSplintersLookMs))
            stalker->CastSpell(stalker, SPELL_PH_TABLE_SPLINTERS, true);     // the chips at the table, not on him
        DespawnChairs(table);
        uint32 patrons = 0;
        for (Vec2 const& p : PatronSpots(table))
            if (me->SummonCreature(NPC_BRD_ROWDY_PATRON, Position(p.x, p.y, kBarFloorZ, 0.f),
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, kPatronDespawnMs))
                ++patrons;
        LogPh("property-damage", Acore::StringFormat("table=T{} by={} source={} outrage={} patrons={} broken={}",
            table + 1, smasher ? smasher->GetName() : std::string("none"), source, OutrageStacks(), patrons,
            _tables.Count()));
    }

    void DespawnChairs(std::size_t table)
    {
        std::list<GameObject*> chairs;
        me->GetGameObjectListWithEntryInGrid(chairs, ChairEntriesOf(table), kChairSearchYd);
        for (GameObject* chair : chairs)
            if (chair && chair->isSpawned())
                chair->DespawnOrUnsummon();
    }

    // Every chair of the floor back (each end of the fight; a reload too: the chairs' respawn times are saved).
    void RespawnChairs()
    {
        std::list<GameObject*> chairs;
        me->GetGameObjectListWithEntryInGrid(chairs, AllChairEntries(), kChairSearchYd);
        for (GameObject* chair : chairs)
            if (chair && !chair->isSpawned())
                chair->Respawn();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there (captures the map and guid).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnPhalanx(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (npc_phalanx_rework* ai = Find(map, guid))
                fn(*ai, result);
        };
    }

    template <typename Fn>
    std::function<void(Unit*)> OnPhalanxHit(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](Unit* hit)
        {
            if (npc_phalanx_rework* ai = Find(map, guid))
                fn(*ai, hit);
        };
    }

public:
    static npc_phalanx_rework* Find(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_phalanx_rework*>(boss->AI());
    }

private:
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _registered = true;     // a registry encounter of ours exists now (a `.dbtest` one included)
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state, cleared (Reset, evade, death, a new pull): nothing pending, nobody held, no aura of the fight
    // left on anyone, no patron or stalker, every chair back. The registry's encounter ends too.
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_registered)
        {
            Mechanic::EndEncounter(me);
            _registered = false;
        }
        if (_lastCall && me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(false);
        _lastCall = MechanicHandle{};
        _park = MechanicHandle{};
        ReleaseThrow();
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_PH_GRAB);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_PH_THUNDERCLAP);
        }
        me->RemoveAurasDueToSpell(SPELL_PH_OUTRAGE);
        summons.DespawnAll();
        RespawnChairs();
        _ledger.Clear();
        _knocks.clear();
        _tables = TableState{};
        _lastThrown.Clear();
        _timeline = Timeline{};
        _volleyArmed = false;
        _fighting = false;
        _parkAtMs = 0;
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd phalanx` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `who` (the GM's selected player, or the GM) stands in for the
    // group out of combat.
    std::string TestFire(TestKind kind, Player* who)
    {
        switch (kind)
        {
            case TestKind::Throw:
                if (_throw.step != Throw::Step::None)
                    return "A throw is already going on.";
                if (!StartThrow(who))
                    return "No throw: no player, or no open floor 15-25 yd from them on the bar floor.";
                break;
            case TestKind::LastCall:
                if (me->HasUnitState(UNIT_STATE_CASTING) || !StartLastCall())
                    return "No Last Call: a cast is going on, or the registry refused it.";
                break;
            case TestKind::Clap:
                CastThunderclap();
                break;
            case TestKind::Blow:
                if (!CastMightyBlow())
                    return "No Mighty Blow: he has no victim in melee reach.";
                break;
            case TestKind::Volley:
                CastVolley();
                break;
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd phalanx smash <1-7>`: PH6 now at that table, `who` the smasher (any difficulty).
    std::string TestSmash(uint32 table, Player* who)
    {
        if (table < 1 || table > kTableCount)
            return "Tables are 1-7 (T1-T7, PhalanxLogic.h kTables).";
        if (_tables.Broken(table - 1))
            return "That table is already broken this fight.";
        Smash(table - 1, who, "test");
        return {};
    }

    // `.dbtest brd phalanx wake`: the gossip start (DC-2 and the playtest; the other two sources are the stock ones).
    std::string TestWake()
    {
        if (_state != PhalanxState::Dormant)
            return "He is not dormant.";
        StartActivation(PhalanxRequest::Gossip);
        return {};
    }

    // `.dbtest brd phalanx heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (_fighting)
            _timeline.heroic = heroic;
    }

    std::string TestState()
    {
        auto left = [this](Beat beat) -> std::string
        {
            uint64 const at = _timeline.At(beat);
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        char const* state = "?";
        switch (_state)
        {
            case PhalanxState::Dormant:      state = "dormant"; break;
            case PhalanxState::MovingToDoor: state = "moving-to-door"; break;
            case PhalanxState::Active:       state = "active"; break;
            case PhalanxState::Dead:         state = "dead"; break;
        }
        std::string ranking;
        for (auto const& [guid, total] : _ledger.Ranking())
        {
            Player* p = ObjectAccessor::GetPlayer(*me, guid);
            ranking += Acore::StringFormat(" {}={}", p ? p->GetName() : guid.ToString(), total);
        }
        return Acore::StringFormat("phalanx state={} faction={} heroic={} fighting={} throw={} last-call={} clap={} "
            "blow={} volley={} outrage={} broken={} throwing={} ledger:{}", state, me->GetFaction(), _heroic ? 1 : 0,
            _fighting ? 1 : 0, left(Beat::ThrowOut), left(Beat::LastCall), left(Beat::Thunderclap),
            left(Beat::MightyBlow), left(Beat::Volley), OutrageStacks(), _tables.Count(),
            _throw.step != Throw::Step::None ? 1 : 0, ranking.empty() ? std::string(" none") : ranking);
    }

private:
    DungeonKit::ArenaGuard _arena;
    DungeonKit::Arena const _floor;         // the throw floor (PhalanxLogic.h ThrowFloor)
    DungeonKit::DamageLedger _ledger;       // PH4, 10 s
    PhalanxState _state = PhalanxState::Dormant;
    bool _heroic = false;
    bool _heroicForced = false;             // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _registered = false;               // a registry encounter of ours exists
    bool _volleyArmed = false;
    uint64 _clockMs = 0;                    // the AI's own clock
    uint64 _yellAtMs = 0;                   // the wake-up yell (0: none pending)
    uint64 _watchdogAtMs = 0;               // the walk's watchdog (0: none)
    uint64 _parkAtMs = 0;
    Timeline _timeline;
    Throw _throw;
    ObjectGuid _lastThrown;
    std::vector<Knock> _knocks;
    TableState _tables;
    MechanicHandle _lastCall;
    MechanicHandle _park;
    std::vector<MechanicHandle> _live;
};

// ---------------------------------------------------------------------------------------------------------------------
// Rowdy Patron 300841 (heroic, PH6): two per smashed table, melee only. Its hits count for Phalanx's ledger.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_rowdy_patron : public ScriptedAI
{
    explicit npc_brd_rowdy_patron(Creature* creature) : ScriptedAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        if (summoner)
            _phalanx = summoner->GetGUID();
        DoZoneInCombat();
    }

    void DamageTaken(Unit* who, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (npc_phalanx_rework* ai = npc_phalanx_rework::Find(me->GetMap(), _phalanx))
            ai->RecordTrouble(who, damage);
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    ObjectGuid _phalanx;
};

namespace
{
    npc_phalanx_rework* PhalanxAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_PHALANX);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<npc_phalanx_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    Player* Selected(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* ok)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        npc_phalanx_rework* ai = PhalanxAI(handler);
        return ai && Done(handler, ai->TestFire(kind, Selected(handler)), ok);
    }

    // `.dbtest brd phalanx info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_PHALANX, BOSS_PHALANX);
    }

    // `.dbtest brd phalanx state`: his state, clocks, Outrage, the broken tables and the ledger.
    bool HandleState(ChatHandler* handler)
    {
        npc_phalanx_rework* ai = PhalanxAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd phalanx wake`: the gossip start while he is dormant.
    bool HandleWake(ChatHandler* handler)
    {
        npc_phalanx_rework* ai = PhalanxAI(handler);
        return ai && Done(handler, ai->TestWake(), "Phalanx wakes and walks to the Bar Door.");
    }

    // `.dbtest brd phalanx throw`: PH4 now on the selected player (or you).
    bool HandleThrow(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Throw, "Throw Out: a 1 s hold, a 1 s flight, the 6 yd circle where they land.");
    }

    // `.dbtest brd phalanx lastcall`: PH5 now.
    bool HandleLastCall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::LastCall, "Last Call: a 3 s bar, then the pulse and the knockback.");
    }

    bool HandleClap(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clap, "Thunderclap: 10 yd, the Magic slow.");
    }

    bool HandleBlow(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Blow, "Mighty Blow on his victim.");
    }

    bool HandleVolley(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Volley, "Fireball Volley: 20 yd.");
    }

    // `.dbtest brd phalanx smash <1-7>`: PH6 at that table, the selected player (or you) the smasher.
    bool HandleSmash(ChatHandler* handler, Optional<uint32> table)
    {
        npc_phalanx_rework* ai = PhalanxAI(handler);
        return ai && Done(handler, ai->TestSmash(table.value_or(2), Selected(handler)),
            "Property damage: the hit, an Outrage stack, two Rowdy Patrons, the chairs gone.");
    }

    // `.dbtest brd phalanx clear`: every mechanic, patron and stalker goes, the chairs come back.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd phalanx heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        npc_phalanx_rework* ai = PhalanxAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& NpcPhalanxTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "wake",     HandleWake,     SEC_GAMEMASTER, Console::No },
            { "throw",    HandleThrow,    SEC_GAMEMASTER, Console::No },
            { "lastcall", HandleLastCall, SEC_GAMEMASTER, Console::No },
            { "clap",     HandleClap,     SEC_GAMEMASTER, Console::No },
            { "blow",     HandleBlow,     SEC_GAMEMASTER, Console::No },
            { "volley",   HandleVolley,   SEC_GAMEMASTER, Console::No },
            { "smash",    HandleSmash,    SEC_GAMEMASTER, Console::No },
            { "clear",    HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic",   HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_npc_phalanx_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_phalanx_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_rowdy_patron, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("phalanx", NpcPhalanxTestCommands());
}
