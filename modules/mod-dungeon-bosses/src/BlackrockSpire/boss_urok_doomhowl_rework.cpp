/*
 * mod-dungeon-bosses, Blackrock Spire B5: Urok Doomhowl (10584), "Stolen Magic". Build spec SP 1630-1688
 * (docs/dungeons/blackrock-spire-rework.md, rulings 37-39), handoff section 3.4 rows UR and 3.5 row B5. Replaces the
 * stock boss_urok_doomhowl (AzerothCore's src/server/scripts/.../BlackrockSpire/boss_urok_doomhowl.cpp: its Rend and
 * Strike timers, the arrival look and yell are kept) and the challenge's gameobject SmartAI (175621, 175584 and the
 * action list 17558400: WP-B5's SQL rev drops them, with the fail and pike rows of the ogres 10601 / 10602). Bound by
 * apps/dbc-tools source/npcs/blackrock_spire/urok.py. Pure rules: UrokLogic.h; the shard helpers B8 / B9 reuse:
 * UrokShards.h.
 *
 *   UR1  The Challenge   the tribute pile 175621 (go_brs_urok_pile) works once Omokk is dead, and again after a wipe
 *                        (the instance's DATA_UROK_PILE, ruling 39; no item). Using it summons Urok hidden at his stock
 *                        spot: he owns the prelude. 3 rounds at 2.5 / 12.5 / 22.5 s of 1 Enforcer 10601 + 1 Magus
 *                        10602 from the stock circles; he arrives (stock look, yell line 0, pulls everyone within 100
 *                        yd) 5 s after the sixth ogre dies, at most at 50 s. An ogre out of combat 30 s (stock) or no
 *                        living player on the plateau for 15 s fails it
 *   UR2  Magus shard     a Magus drops a shard where it dies; a prelude shard that reaches the pile is a Stolen Power
 *                        stack when he arrives
 *   UR3  Stolen Magic    shards (300706, the kit's CrawlPickups: a T-only Soak anchored on the shard, MissedSoak Never)
 *                        are taken on touch (2 yd); left 10 s (heroic 7 s) they crawl to him at 3 yd/s
 *   UR4  Warosh's Power  a grab: +5% damage and healing done a stack, 3, 20 s, refreshed
 *   UR5  Stolen Power    a shard reaching him: +5% damage done a stack, 8 (heroic 5), emote line 3
 *   UR6  Wild Bolt       first 6 s, every 10 s: a 6 yd circle within 8 yd of 1 / 2 random non-tanks, 2 s (a missile
 *                        timed to land with it), 25% / 30%, Weakened; a shard at its center
 *   UR7  Doomhowl        first 15 s, every 20 s: 2.5 s cast (emote line 2), 12 yd on him, tank exempt, 20% / 30%,
 *                        Weakened, 2 s fear
 *   UR8  Rend, Strike    stock 16509 / 15580 on his victim (stock timers)
 *   UR9  Overcharge (H)  at 5 Stolen Power: 3 s cast (emote line 4), 40% to every player, the stacks reset
 *   UR10 Unstable (H)    every grab adds a stack; 6 s after the first the carrier bursts (10% a stack to the carrier,
 *                        30% + Weakened to everyone within 8 yd + 2 a stack past the first); shards eligible below 2
 *   UR11 Reset           an evade or a failed prelude: Urok, the ogres and the shards go, the pile is usable again
 *   Arena                BlackrockSpireRework::LeashOptions on UrokArena() (no grips)
 *
 * Every fight timer runs on the AI's own clock, never on BossAI's scheduler. Every firing logs one INFO line
 * "brs urok <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "UrokLogic.h"
#include "UrokShards.h"
#include <algorithm>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsUrok;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "urok";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    Position ToPos(Point4 const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    // Why the pile refuses (nullptr: it is ready).
    char const* PileRefusal(uint32 pile)
    {
        switch (pile)
        {
            case PILE_READY:    return nullptr;
            case PILE_LOCKED:   return "Highlord Omokk still rules the Spirestones. The skulls do not answer you.";
            case PILE_IN_USE:   return "The challenge is already under way.";
            case PILE_SPENT:    return "Urok Doomhowl is dead. The skulls are silent.";
            default:            return "The skulls do not answer you.";
        }
    }

    // UR1: `by` uses the pile. Summons Urok hidden at his spot and hands him the challenge. False (and a notification
    // to `by`) when the pile is not ready or the summon failed (the pile is ready again then).
    bool StartChallenge(GameObject* pile, Player* by)
    {
        InstanceScript* instance = pile ? pile->GetInstanceScript() : nullptr;
        if (!instance)
            return false;
        uint32 const state = instance->GetData(DATA_UROK_PILE);
        if (char const* why = PileRefusal(state))
        {
            if (by)
                ChatHandler(by->GetSession()).SendNotification(why);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pile-refused",
                Acore::StringFormat("by={} pile={}", by ? by->GetName() : "none", UrokPileName(state)));
            return false;
        }
        instance->SetData(DATA_UROK_PILE, PILE_IN_USE);
        if (instance->GetData(DATA_UROK_PILE) != PILE_IN_USE)
            return false;
        Creature* urok = pile->SummonCreature(NPC_UROK, ToPos(kUrokSummon), TEMPSUMMON_MANUAL_DESPAWN);
        if (!urok || !urok->IsAIEnabled || !urok->AI())
        {
            if (urok)
                urok->DespawnOrUnsummon();
            instance->SetData(DATA_UROK_PILE, PILE_READY);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pile-failed", "Urok was not summoned");
            return false;
        }
        pile->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "challenge",
            Acore::StringFormat("by={} heroic={}", by ? by->GetName() : "gm", IsHeroicMap(pile) ? 1 : 0));
        urok->AI()->DoAction(ACTION_UR_CHALLENGE);
        return true;
    }
}

// Urok Doomhowl 10584
struct boss_urok_doomhowl_rework : public BossAI
{
    explicit boss_urok_doomhowl_rework(Creature* creature)
        : BossAI(creature, BOSS_UROK), _arena(UrokArena(), LeashOptions(kBossLogName)) { }

    enum class Stage : uint8
    {
        Standing,   // placed by hand (a GM): a plain boss
        Prelude,    // the challenge runs; he is hidden
        Fight,      // out and fighting (or about to be)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        _players = 0;
    }

    void DoAction(int32 action) override
    {
        if (action == ACTION_UR_CHALLENGE && _stage == Stage::Standing && !me->IsEngaged())
            BeginChallenge();
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_stage == Stage::Prelude)
            Reveal("engaged early");    // something reached him before his time: he is out now
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _stage = Stage::Fight;
        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_UROK;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_UR_AGGRO);

        bool const heroic = IsHeroicMap(me);
        _fightStartMs = _nowMs;
        _nextWildBoltMs = _nowMs + kWildBoltCadence.first;
        _nextDoomhowlMs = _nowMs + kDoomhowlCadence.first;
        _nextRendMs = _nowMs + InRange(kRendFirst, Rand01());
        _nextStrikeMs = _nowMs + InRange(kStrikeFirst, Rand01());
        _overchargeAtMs = 0;
        _shards.SetGoal({ me->GetGUID(), std::nullopt });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} stolen={} shards={} challenge={}", heroic ? 1 : 0, _players,
                DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER), _shards.Count(), _fromChallenge ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_stage == Stage::Prelude)
            return;     // hidden and passive: nothing to evade from
        CleanupFight();
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
        if (_fromChallenge)
            EndChallenge("wipe");       // UR11: he goes, the pile is ready again
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);       // DONE: the instance spends the pile; the summons (ogres, shards) despawn
        me->setActive(false);           // the challenge's grid hold ends with him (his corpse stays: MANUAL_DESPAWN)
        CleanupFight();
        DeleteChallengeObjects();
        _arena.Reset();
        Talk(SAY_UR_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("fight={}s killer={}", (_nowMs - _fightStartMs) / 1000,
                killer ? killer->GetName() : "none"));
    }

    // The ogres, the shards and the markers are his summons; none is zoned into combat by him (BossAI would): the
    // ogres are sent at the players one by one, the shards never fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        uint32 const entry = summon->GetEntry();
        if (entry != NPC_UROK_ENFORCER && entry != NPC_UROK_MAGUS)
            return;
        ForgetOgre(summon->GetGUID());
        if (_stage == Stage::Prelude)
            _prelude.OgreDied();
        if (entry == NPC_UROK_MAGUS)
            DropShard(summon->GetPosition(), "magus");     // UR2
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "ogre-died",
            Acore::StringFormat("entry={} dead={}/{} at={}s", entry, _prelude.OgresDead(), kPreludeOgres,
                _prelude.Now() / 1000));
    }

    void UpdateAI(uint32 diff) override
    {
        _nowMs += diff;
        if (_stage == Stage::Prelude)
        {
            UpdatePrelude(diff);
            return;
        }
        if (!UpdateVictim())
            return;

        bool const heroic = IsHeroicMap(me);
        _shards.Update(me, diff);
        UpdateLaunches();
        UpdateUnstable();

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_overchargeAtMs && _nowMs >= _overchargeAtMs)
            OverchargeLands();

        if (!me->HasUnitState(UNIT_STATE_CASTING))
        {
            uint32 const stacks = DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER);
            if (OverchargeDue(stacks, heroic, _overchargeAtMs != 0))
                StartOvercharge(stacks);
            else if (_nowMs >= _nextDoomhowlMs)
            {
                _nextDoomhowlMs = _nowMs + kDoomhowlCadence.every;
                StartDoomhowl(heroic);
            }
            else if (_nowMs >= _nextWildBoltMs)
            {
                _nextWildBoltMs = _nowMs + kWildBoltCadence.every;
                WildBolt(heroic);
            }
            else
                TankHits();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR1 The Challenge
    // ----------------------------------------------------------------------------------------------------------------

    struct Ogre
    {
        ObjectGuid guid;
        uint32 outOfCombatMs = 0;
    };

    void BeginChallenge()
    {
        _stage = Stage::Prelude;
        _fromChallenge = true;
        me->setActive(true);        // his grid stays loaded through the prelude (he is not engaged yet)
        Hide();
        _prelude.Start();
        _pileStacks = 0;
        _nobodyMs = 0;
        _ogres.clear();
        SpawnChallengeObjects();
        Describe();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "prelude",
            Acore::StringFormat("rounds={} ogres={} cap={}s heroic={}", kRounds.size(), kPreludeOgres,
                kArrivalCapMs / 1000, IsHeroicMap(me) ? 1 : 0));
    }

    void UpdatePrelude(uint32 diff)
    {
        for (std::size_t const round : _prelude.Update(diff))
            SummonRound(round);
        _shards.Update(me, diff);
        UpdateUnstable();

        // Stock: an ogre left out of combat for 30 s fails the challenge.
        for (Ogre& ogre : _ogres)
        {
            Creature* c = me->GetMap()->GetCreature(ogre.guid);
            if (!c || !c->IsAlive())
                continue;
            if (c->IsInCombat())
                ogre.outOfCombatMs = 0;
            else if ((ogre.outOfCombatMs += diff) >= kOgreOutOfCombatFailMs)
            {
                EndChallenge("an ogre out of combat for 30 s");
                return;
            }
        }
        // Nobody alive on the plateau (a wipe between rounds, or the group left): it fails too.
        if (AnyPlayerOnPlateau())
            _nobodyMs = 0;
        else if ((_nobodyMs += diff) >= kNobodyFailMs)
        {
            EndChallenge("nobody on the plateau for 15 s");
            return;
        }

        if (_prelude.ArrivalDue())
            Arrive("on time");
    }

    bool AnyPlayerOnPlateau() const
    {
        Arena const arena = UrokArena();
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster()
                && arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                return true;
        }
        return false;
    }

    void SummonRound(std::size_t index)
    {
        OgreRound const& round = kRounds[index];
        SummonOgre(NPC_UROK_ENFORCER, kCircles[round.enforcerCircle]);
        SummonOgre(NPC_UROK_MAGUS, kCircles[round.magusCircle]);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "round",
            Acore::StringFormat("{}/{} at={}s", index + 1, kRounds.size(), _prelude.Now() / 1000));
    }

    // An ogre steps out of its circle (the stock teleport look) and goes for the nearest player. It keeps its stock
    // SmartAI combat rows (Strike; Arcane Bolt, Slow, Bloodlust); the flex scaler sizes it at its own pull.
    void SummonOgre(uint32 entry, Point4 const& at)
    {
        DungeonKit::WaveSpec spec;
        spec.entry = entry;
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = Milliseconds(60000);
        spec.onSummon = [this](Creature* ogre)
        {
            ogre->CastSpell(ogre, SPELL_UR_OGRE_TELEPORT, true);
            _ogres.push_back({ ogre->GetGUID(), 0 });
            if (Player* target = BrsStolenMagic::NearestPlayer(ogre, kOgreAggroRangeYd))
            {
                ogre->EngageWithTarget(target);
                if (ogre->IsAIEnabled && ogre->AI())
                    ogre->AI()->AttackStart(target);
            }
        };
        DungeonKit::SummonWave(me, spec, { ToPos(at) }, summons);
    }

    void ForgetOgre(ObjectGuid guid)
    {
        _ogres.erase(std::remove_if(_ogres.begin(), _ogres.end(), [guid](Ogre const& o)
        {
            return o.guid == guid;
        }), _ogres.end());
    }

    // The stock look of the challenge: Omokk's head on its pike in the pile and the six summoning circles. Props only
    // (not selectable); the instance tracks them and deletes them on a reset.
    void SpawnChallengeObjects()
    {
        auto spawn = [this](uint32 entry, float x, float y, float z, float o)
        {
            if (GameObject* go = me->SummonGameObject(entry, x, y, z, o, 0.f, 0.f, 0.f, 0.f, 0, true,
                GO_SUMMON_TIMED_DESPAWN))
            {
                go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                _objects.push_back(go->GetGUID());
            }
        };
        spawn(GO_UROK_CHALLENGE, kUrokPile.x, kUrokPile.y, kUrokPile.z, 0.f);
        for (Point4 const& c : kCircles)
            spawn(GO_UROK_CIRCLE, c.x, c.y, c.z, c.o);
    }

    void DeleteChallengeObjects()
    {
        for (ObjectGuid const& guid : _objects)
            if (GameObject* go = me->GetMap()->GetGameObject(guid))
                go->Delete();
        _objects.clear();
    }

    // Hidden while he owns the prelude: invisible, not selectable, not attackable, passive and kept out of combat.
    // Not IMMUNE_TO_PC: the prelude's hits he owns (heroic Unstable, the carrier's burst) must still land on the
    // players (Unit::_IsValidAttackTarget refuses an immune-to-PC attacker), and the combat lock keeps those hits
    // from pulling him into the fight early (R-1-A m4).
    void Hide()
    {
        me->SetVisible(false);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToNPC(true);
        me->SetIsCombatDisallowed(true);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
    }

    // He is out: visible, attackable, the prelude's pile stacks on him, the shards crawl to him now.
    void Reveal(char const* why)
    {
        _prelude.Stop();
        _stage = Stage::Fight;
        me->SetVisible(true);
        me->SetIsCombatDisallowed(false);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
        me->SetImmuneToAll(false);
        me->SetReactState(REACT_AGGRESSIVE);
        me->CastSpell(me, SPELL_UR_ARRIVAL, true);
        Talk(SAY_UR_SUMMON);
        bool const heroic = IsHeroicMap(me);
        uint32 const stacks = StacksAtArrival(_pileStacks, heroic);
        if (stacks)
            DungeonKit::AddStacks(me, SPELL_UR_STOLEN_POWER, static_cast<int32>(stacks), me,
                kStolenPowerCap(heroic));
        _shards.SetGoal({ me->GetGUID(), std::nullopt });
        DeleteChallengeObjects();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "arrive",
            Acore::StringFormat("why={} at={}s ogres-dead={}/{} pile-stacks={} stolen={} shards={}", why,
                _prelude.Now() / 1000, _prelude.OgresDead(), kPreludeOgres, _pileStacks, stacks, _shards.Count()));
    }

    // Stock: he arrives and pulls everyone within 100 yd.
    void Arrive(char const* why)
    {
        Reveal(why);
        Player* target = BrsStolenMagic::NearestPlayer(me, kArrivalPullRangeYd);
        if (!target)
        {
            EndChallenge("nobody to fight at his arrival");
            return;
        }
        me->EngageWithTarget(target);
        AttackStart(target);
        DoZoneInCombat(me, kArrivalPullRangeYd);
    }

    // UR11: the challenge failed or the group wiped. Everything of it goes, the instance resets the pile (stock
    // SetData(4, FAIL): the challenge objects, the ogres, the pile READY again) and he despawns.
    void EndChallenge(char const* why)
    {
        _prelude.Stop();
        _stage = Stage::Standing;
        _fromChallenge = false;
        CleanupFight();
        summons.DespawnAll();
        DeleteChallengeObjects();
        _ogres.clear();
        me->setActive(false);
        if (instance)
            instance->SetData(DATA_UROK_EVENT, FAIL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "reset", why);
        me->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR3 Stolen Magic, UR4 Warosh's Power, UR5 Stolen Power
    // ----------------------------------------------------------------------------------------------------------------

    uint32 DropShard(Position const& at, char const* source)
    {
        bool const heroic = IsHeroicMap(me);
        DungeonKit::CrawlPickupSpec spec = BrsStolenMagic::ShardSpec(Ms(kShardWaitMs(heroic)), TAG_UR_SHARD);
        if (heroic)
        {
            // UR10: anyone may take a shard at 0 to 2 Unstable stacks (the touch: CrawlPickups holds everyone to
            // `who`); the bots' claim order stops them at 2 (SP: "Bots grab only at 0 or 1 stack").
            spec.who.auraSpell = SPELL_UR_UNSTABLE;
            spec.who.maxStacks = kUnstableGrabMaxStacks;
            spec.order = BossMechanics::Ordering{ SPELL_UR_UNSTABLE, true, kUnstableBotCapStacks };
        }
        // The pickups live in this AI and their callbacks run from its UpdateAI: `this` is safe here.
        spec.onPick = [this](Player* taker, Position const& p) { ShardTaken(taker, p); };
        spec.onReach = [this](ObjectGuid, Position const& p) { ShardReached(p); };
        DungeonKit::CrawlGoal goal;
        if (_stage == Stage::Prelude)
            goal.point = Position(kUrokPile.x, kUrokPile.y, kUrokPile.z, 0.f);
        else
            goal.unit = me->GetGUID();
        uint32 const id = _shards.Add(me, at, std::move(spec), goal);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shard",
            Acore::StringFormat("source={} id={} at=({:.1f}, {:.1f}) live={}", source, id, at.GetPositionX(),
                at.GetPositionY(), _shards.Count()));
        return id;
    }

    void ShardTaken(Player* taker, Position const& at)
    {
        bool const heroic = IsHeroicMap(me);
        uint32 const power = DungeonKit::AddStacks(taker, SPELL_UR_WAROSHS_POWER, 1, nullptr, kWaroshMaxStacks);
        uint32 unstable = 0;
        if (heroic)
            unstable = UnstableGrab(taker);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shard-taken",
            Acore::StringFormat("by={} power={} unstable={} at=({:.1f}, {:.1f})", taker->GetName(), power, unstable,
                at.GetPositionX(), at.GetPositionY()));
    }

    void ShardReached(Position const& at)
    {
        if (_stage == Stage::Prelude)
        {
            ++_pileStacks;      // UR2: a stack waiting for him in the pile
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shard-pile",
                Acore::StringFormat("pile-stacks={}", _pileStacks));
            return;
        }
        bool const heroic = IsHeroicMap(me);
        uint32 const before = DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER);
        uint32 const after = BrsStolenMagic::AddStolenPower(me, kStolenPowerCap(heroic));
        Talk(EMOTE_UR_RECLAIM);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "stolen-power",
            Acore::StringFormat("stacks={}->{} at=({:.1f}, {:.1f})", before, after, at.GetPositionX(),
                at.GetPositionY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR6 Wild Bolt
    // ----------------------------------------------------------------------------------------------------------------

    struct Launch
    {
        Position at;
        uint64 dueMs = 0;
    };

    void WildBolt(bool heroic)
    {
        uint8 const count = kWildBoltTargets.At(_players);
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        rule.maxRange = kWildBoltTargetRangeYd;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, count);
        for (Player* target : targets)
        {
            Position const spot = BoltSpot(target);
            MechanicRef ref = Mechanic::Circle(me, spot, kWildBoltRadiusYd, Ms(kWildBoltWarnMs));
            ref.Damage(kWildBoltPct(heroic)).Spell(SPELL_UR_WILD_BOLT).Weakened().Tag(TAG_UR_WILD_BOLT);
            ref.OnResolve(OnUrok([spot, gen = _generation](boss_urok_doomhowl_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                if (gen == ai._generation)
                    ai.WildBoltLanded(spot, result.hits.size());
            }));
            Track(ref.Handle());
            float const dist = me->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY());
            _launches.push_back({ spot, _nowMs + LaunchDelayMs(kWildBoltWarnMs, dist, kWildBoltMissileSpeed) });
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wild-bolt",
            Acore::StringFormat("heroic={} count={}/{} pct={:.0f}", heroic ? 1 : 0, targets.size(), count,
                kWildBoltPct(heroic)));
    }

    // A floor point within 8 yd of the target, on the plateau (it slopes about 4 degrees: the probe follows it).
    Position BoltSpot(Player* target)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(target);
        rules.minRange = 0.f;
        rules.maxRange = kWildBoltScatterYd;
        DungeonKit::FloorProbe probe;
        probe.z = target->GetPositionZ();
        Arena const arena = UrokArena();
        if (std::optional<Position> spot = DungeonKit::PickFloorSpot(me, &arena, rules, probe))
            return *spot;
        return target->GetPosition();
    }

    // The missile, launched so it lands as the circle resolves (the look only; the registry owns the hit). It keeps
    // flying through a Doomhowl cast: this runs off the casting check.
    void UpdateLaunches()
    {
        for (auto it = _launches.begin(); it != _launches.end();)
        {
            if (_nowMs < it->dueMs)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->at.GetPositionX(), it->at.GetPositionY(), it->at.GetPositionZ(),
                SPELL_UR_WILD_BOLT_MISSILE, true);
            it = _launches.erase(it);
        }
    }

    void WildBoltLanded(Position const& at, std::size_t hits)
    {
        // The landing look on the new shard (it stands at the center).
        uint32 const id = DropShard(at, "wild-bolt");
        if (Creature* shard = id ? me->GetMap()->GetCreature(_shards.UnitOf(id)) : nullptr)
            shard->CastSpell(shard, SPELL_UR_WILD_BOLT_LANDING, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wild-bolt-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={}", at.GetPositionX(), at.GetPositionY(), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR7 Doomhowl, UR8 Rend and Strike
    // ----------------------------------------------------------------------------------------------------------------

    void StartDoomhowl(bool heroic)
    {
        DungeonKit::CastBar(me, SPELL_UR_DOOMHOWL_CAST, nullptr, uint8(EMOTE_UR_DOOMHOWL));
        MechanicRef ref = Mechanic::Circle(me, me, kDoomhowlRadiusYd, Ms(kDoomhowlCastMs));
        ref.TankExempt().Damage(kDoomhowlPct(heroic)).Spell(SPELL_UR_DOOMHOWL).Weakened()
            .Rider(SPELL_UR_DOOMHOWL_FEAR).Tag(TAG_UR_DOOMHOWL);
        ref.OnResolve(OnUrok([gen = _generation](boss_urok_doomhowl_rework& ai,
            BossMechanics::ResolveResult const& result)
        {
            if (gen == ai._generation)
                ai.DoomhowlLands(result.hits.size());
        }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "doomhowl",
            Acore::StringFormat("heroic={} pct={:.0f} radius={:.0f}", heroic ? 1 : 0, kDoomhowlPct(heroic),
                kDoomhowlRadiusYd));
    }

    void DoomhowlLands(std::size_t hits)
    {
        me->CastSpell(me, SPELL_UR_DOOMHOWL_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "doomhowl-lands", Acore::StringFormat("hits={}", hits));
    }

    void TankHits()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;
        if (_nowMs >= _nextRendMs)
        {
            DoCast(victim, SPELL_UR_REND);
            _nextRendMs = _nowMs + InRange(kTankHitEvery, Rand01());
        }
        else if (_nowMs >= _nextStrikeMs)
        {
            DoCast(victim, SPELL_UR_STRIKE);
            _nextStrikeMs = _nowMs + InRange(kTankHitEvery, Rand01());
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR9 Overcharge (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void StartOvercharge(uint32 stacks)
    {
        DungeonKit::CastBar(me, SPELL_UR_OVERCHARGE_CAST, nullptr, uint8(EMOTE_UR_OVERCHARGE));
        _overchargeAtMs = _nowMs + kOverchargeCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "overcharge", Acore::StringFormat("stacks={}", stacks));
    }

    void OverchargeLands()
    {
        _overchargeAtMs = 0;
        GuidSet const players = BrsStolenMagic::PlayersNear(me, kOverchargeRangeYd);
        BrsStolenMagic::Overcharge(me, kOverchargePct, kOverchargeRangeYd, TAG_UR_OVERCHARGE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "overcharge-lands",
            Acore::StringFormat("hits={} pct={:.0f}", players.size(), kOverchargePct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR10 Unstable (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A heroic grab: one more Unstable stack; the fuse runs from the first. The RunOut for everyone else is placed
    // again with the radius of the new count and the time left. Returns the carrier's stacks.
    uint32 UnstableGrab(Player* carrier)
    {
        uint64 const key = carrier->GetGUID().GetRawValue();
        bool const first = _unstable.Stacks(key) == 0;
        UnstableFuse const fuse = _unstable.Grab(key, _nowMs);
        uint64 const left = std::max<uint64>(100, _unstable.Remaining(key, _nowMs));
        DungeonKit::AddStacks(carrier, SPELL_UR_UNSTABLE, 1, me);
        if (Aura* aura = carrier->GetAura(SPELL_UR_UNSTABLE, me->GetGUID()))
        {
            // AddStacks refreshes the duration: the fuse does not reset, so the clock shows the time left.
            aura->SetMaxDuration(static_cast<int32>(kUnstableFuseMs));
            aura->SetDuration(static_cast<int32>(left));
        }
        auto it = _unstableRunOuts.find(key);
        if (it != _unstableRunOuts.end())
            Mechanic::Cancel(me, it->second);
        MechanicRef ref = Mechanic::RunOut(me, carrier, UnstableRadius(fuse.stacks), Ms(left));
        ref.Damage(kUnstableOthersPct).Spell(SPELL_UR_UNSTABLE_BURST).Weakened().Tag(TAG_UR_UNSTABLE);
        _unstableRunOuts[key] = ref.Handle();
        if (first)
            carrier->CastSpell(carrier, SPELL_UR_UNSTABLE_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "unstable",
            Acore::StringFormat("carrier={} stacks={} radius={:.0f} left={}ms", carrier->GetName(), fuse.stacks,
                UnstableRadius(fuse.stacks), left));
        return fuse.stacks;
    }

    // The fuses: the carrier's own hit at the burst (10% a stack, no Weakened; the RunOut hits the others at the same
    // moment), and the rune look again every 2.5 s while a fuse burns.
    void UpdateUnstable()
    {
        if (_unstable.Size() == 0)
            return;
        for (UnstableFuse const& fuse : _unstable.TakeDue(_nowMs))
        {
            ObjectGuid const guid(fuse.carrier);
            _unstableRunOuts.erase(fuse.carrier);
            Player* carrier = ObjectAccessor::GetPlayer(me->GetMap(), guid);
            if (!carrier || !carrier->IsAlive())
                continue;
            carrier->RemoveAurasDueToSpell(SPELL_UR_UNSTABLE);
            carrier->CastSpell(carrier, SPELL_UR_WILD_BOLT_LANDING, true);     // the burst's look (Arcane Explosion)
            DungeonKit::RegistryHitSpec spec;
            spec.pct = UnstableCarrierPct(fuse.stacks);
            spec.school = SPELL_SCHOOL_ARCANE;
            spec.spellId = SPELL_UR_UNSTABLE_BURST;
            spec.weakened = false;
            spec.tag = TAG_UR_UNSTABLE;
            DungeonKit::RegistryHit(me, GuidSet{ guid }, spec);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "unstable-burst",
                Acore::StringFormat("carrier={} stacks={} self={:.0f}% radius={:.0f}", carrier->GetName(),
                    fuse.stacks, UnstableCarrierPct(fuse.stacks), UnstableRadius(fuse.stacks)));
        }
        if (_nowMs >= _nextUnstableLookMs)
        {
            _nextUnstableLookMs = _nowMs + kUnstableLookEveryMs;
            for (UnstableFuse const& fuse : _unstable.All())
                if (Player* carrier = ObjectAccessor::GetPlayer(me->GetMap(), ObjectGuid(fuse.carrier)))
                    if (carrier->IsAlive())
                        carrier->CastSpell(carrier, SPELL_UR_UNSTABLE_LOOK, true);
        }
    }

    void ClearUnstable()
    {
        for (UnstableFuse const& fuse : _unstable.All())
            if (Player* carrier = ObjectAccessor::GetPlayer(me->GetMap(), ObjectGuid(fuse.carrier)))
                carrier->RemoveAurasDueToSpell(SPELL_UR_UNSTABLE);
        _unstable.Clear();
        _unstableRunOuts.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP "Boss data"): kill order the Magi, then the Enforcers; dispel the Magi's Slow (a reward)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_UROK_MAGUS, kMagusPriority, Who::Dps));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_UROK_ENFORCER, kEnforcerPriority, Who::Dps));
        d.dispels.push_back(BossMechanics::DispelEntry(SPELL_UR_MAGUS_SLOW, kSlowDispelPriority));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs urok` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        WildBolt,
        Doomhowl,
        Overcharge,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (_stage == Stage::Prelude || !me->IsEngaged())
            return "Urok must be out and in combat (use `.dbtest brs urok arrive` during the challenge).";
        switch (mechanic)
        {
            case TestMechanic::WildBolt:
                WildBolt(heroic);
                break;
            case TestMechanic::Doomhowl:
                StartDoomhowl(heroic);
                break;
            case TestMechanic::Overcharge:
                StartOvercharge(DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER));
                break;
        }
        return {};
    }

    std::string TestArrive()
    {
        if (_stage != Stage::Prelude)
            return "The challenge is not running (use the pile, or `.dbtest brs urok challenge`).";
        Arrive("gm");
        return {};
    }

    // A shard at `at` (the GM's spot): it crawls to the pile during the challenge, to him after.
    void TestShard(Position const& at)
    {
        DropShard(at, "gm");
    }

    uint32 TestStacks(uint32 stacks)
    {
        bool const heroic = IsHeroicMap(me);
        uint32 const capped = std::min(stacks, kStolenPowerCap(heroic));
        uint32 const before = DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER);
        if (capped != before)
            DungeonKit::AddStacks(me, SPELL_UR_STOLEN_POWER, static_cast<int32>(capped) - static_cast<int32>(before),
                me, kStolenPowerCap(heroic));
        return capped;
    }

    // A heroic grab by `player` without a shard (UR10's stack and fuse), on any map.
    uint32 TestUnstable(Player* player)
    {
        return UnstableGrab(player);
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("stage={} challenge={} prelude={}s rounds={} ogres-dead={} ogres-live={} "
            "pile-stacks={} shards={} stolen={} unstable-carriers={} fight={}s bolt={}s howl={}s overcharge={} "
            "players={} visible={}", int(_stage), _fromChallenge ? 1 : 0, _prelude.Now() / 1000, _prelude.RoundsOut(),
            _prelude.OgresDead(), _ogres.size(), _pileStacks, _shards.Count(),
            DungeonKit::Stacks(me, SPELL_UR_STOLEN_POWER), _unstable.Size(),
            _stage == Stage::Fight ? (_nowMs - _fightStartMs) / 1000 : 0,
            _nextWildBoltMs > _nowMs ? (_nextWildBoltMs - _nowMs) / 1000 : 0,
            _nextDoomhowlMs > _nowMs ? (_nextDoomhowlMs - _nowMs) / 1000 : 0, _overchargeAtMs ? 1 : 0, _players,
            me->IsVisible() ? 1 : 0);
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnUrok(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_urok_doomhowl_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // The fight's state goes (reset, evade, death, a failed challenge): the shards, the fuses, the pending hits.
    void CleanupFight()
    {
        ++_generation;
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (auto const& [key, handle] : _unstableRunOuts)
            Mechanic::Cancel(me, handle);
        ClearUnstable();
        _shards.Clear(me);
        _launches.clear();
        _overchargeAtMs = 0;
        if (me->IsAlive())
            me->RemoveAurasDueToSpell(SPELL_UR_STOLEN_POWER);
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CrawlPickups _shards;
    PreludeClock _prelude;
    UnstableBook _unstable;
    std::unordered_map<uint64, MechanicHandle> _unstableRunOuts;
    std::vector<Ogre> _ogres;
    std::vector<ObjectGuid> _objects;
    std::vector<Launch> _launches;
    std::vector<MechanicHandle> _live;
    Stage _stage = Stage::Standing;
    bool _fromChallenge = false;
    uint8 _players = 0;                 // the flex count held at the pull (5..10)
    uint32 _pileStacks = 0;             // UR2: prelude shards that reached the pile
    uint32 _nobodyMs = 0;
    uint32 _generation = 0;             // bumped on cleanup: a resolve from an earlier pull does nothing
    uint64 _nowMs = 0;                  // ms since he was summoned: every timer of the challenge and the fight
    uint64 _fightStartMs = 0;
    uint64 _nextWildBoltMs = 0;
    uint64 _nextDoomhowlMs = 0;
    uint64 _nextRendMs = 0;
    uint64 _nextStrikeMs = 0;
    uint64 _overchargeAtMs = 0;         // heroic: the cast lands then (0: none)
    uint64 _nextUnstableLookMs = 0;
};

// The Stolen Magic shard (300706): a passive prop its owner moves (the kit's CrawlPickups) and despawns. Shared with
// Wyrmthalak's hard mode (B9, WT10).
struct npc_brs_stolen_magic_shard : public NullCreatureAI
{
    explicit npc_brs_stolen_magic_shard(Creature* creature) : NullCreatureAI(creature) { }
};

// Urok's Tribute Pile (175621, a goober now): usable once Omokk is dead, again after a wipe, never after Urok's death
// (the instance's DATA_UROK_PILE; ruling 39, no item). Not selectable while it cannot be used.
struct go_brs_urok_pile : public GameObjectAI
{
    explicit go_brs_urok_pile(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kPileSelectPollMs;
        InstanceScript* instance = me->GetInstanceScript();
        bool const usable = instance && UrokPileUsable(instance->GetData(DATA_UROK_PILE));
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (usable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!usable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        StartChallenge(me, player);
        return true;
    }

private:
    uint32 _pollMs = 0;
};

namespace
{
    boss_urok_doomhowl_rework* FindUrokAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_UROK);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_urok_doomhowl_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Urok is not running boss_urok_doomhowl_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_urok_doomhowl_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Urok: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_UROK, BOSS_UROK);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Urok: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs urok challenge`: uses the nearest tribute pile as the GM (the pile must be ready: Omokk dead).
    bool HandleChallenge(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        Player* gm = handler->GetPlayer();
        GameObject* pile = gm ? gm->FindNearestGameObject(GO_UROK_PILE, 200.f) : nullptr;
        if (!pile)
        {
            handler->SendErrorMessage("{}", "No Urok's Tribute Pile within 200 yd.");
            return false;
        }
        InstanceScript* instance = pile->GetInstanceScript();
        uint32 const state = instance ? instance->GetData(DATA_UROK_PILE) : uint32(PILE_LOCKED);
        if (!StartChallenge(pile, nullptr))
        {
            handler->SendErrorMessage("The pile refused ({}).", UrokPileName(state));
            return false;
        }
        handler->PSendSysMessage("Urok: the challenge runs (UR1: rounds at 2.5 / 12.5 / 22.5 s, he arrives by 50 s).");
        return true;
    }

    bool HandleArrive(ChatHandler* handler)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestArrive();
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Urok: he arrives now.");
        return true;
    }

    bool HandleShard(ChatHandler* handler)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        ai->TestShard(gm->GetPosition());
        handler->PSendSysMessage("Urok: a shard at your feet (UR3; game masters cannot take it).");
        return true;
    }

    bool HandleBolt(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_urok_doomhowl_rework::TestMechanic::WildBolt, heroic,
            "Wild Bolt (UR6: 1 / 2 circles near non-tanks, 2 s, a shard each)");
    }

    bool HandleHowl(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_urok_doomhowl_rework::TestMechanic::Doomhowl, heroic,
            "Doomhowl (UR7: 2.5 s cast, 12 yd, tank exempt, 2 s fear)");
    }

    bool HandleOvercharge(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_urok_doomhowl_rework::TestMechanic::Overcharge, heroic,
            "Overcharge (UR9: 3 s cast, then 40% to everyone, the stacks reset)");
    }

    // `.dbtest brs urok stacks <n>`: sets his Stolen Power (UR5; 0 removes it), capped at the difficulty's.
    bool HandleStacks(ChatHandler* handler, uint32 stacks)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Urok: Stolen Power set to {}.", ai->TestStacks(stacks));
        return true;
    }

    // `.dbtest brs urok unstable`: a heroic grab on the selected player (else the GM): one Unstable stack and the fuse.
    bool HandleUnstable(ChatHandler* handler)
    {
        boss_urok_doomhowl_rework* ai = FindUrokAI(handler);
        if (!ai)
            return false;
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!target)
            return false;
        handler->PSendSysMessage("Urok: {} carries {} Unstable (UR10).", target->GetName(), ai->TestUnstable(target));
        return true;
    }

    // `.dbtest brs urok <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& UrokTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "challenge",  HandleChallenge,  SEC_GAMEMASTER, Console::No },
            { "arrive",     HandleArrive,     SEC_GAMEMASTER, Console::No },
            { "shard",      HandleShard,      SEC_GAMEMASTER, Console::No },
            { "bolt",       HandleBolt,       SEC_GAMEMASTER, Console::No },
            { "howl",       HandleHowl,       SEC_GAMEMASTER, Console::No },
            { "overcharge", HandleOvercharge, SEC_GAMEMASTER, Console::No },
            { "stacks",     HandleStacks,     SEC_GAMEMASTER, Console::No },
            { "unstable",   HandleUnstable,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_urok_doomhowl_rework()
{
    RegisterDungeonReworkCreatureAI(boss_urok_doomhowl_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_stolen_magic_shard, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_brs_urok_pile, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("urok", UrokTestCommands());
}
