/*
 * mod-dungeon-bosses, Blackrock Spire B4: Mother Smolderweb (10596), "The Clutch, with Mother's Milk". Build spec:
 * docs/dungeons/blackrock-spire-rework.md "Mother Smolderweb" (SP 1231-1469, SW1-SW10, rulings 33-36 and 63-64),
 * handoff section 3.4 rows SW, 3.5 row B4, 3.6, 3.8 (her cave and its eight egg spots). Replaces her SmartAI (the S0
 * SQL rev dropped the rows); bound by apps/dbc-tools source/npcs/blackrock_spire/smolderweb.py. Pure rules:
 * SmolderwebLogic.h.
 *
 *   SW1 The Clutch   on the pull 8 eggs (gameobject 301251, display 364) at the fixed spots of the cave, each a
 *                    registry Mine (4 yd, 0.5 s grace): a player who stays in one hatches it: 20% (heroic 25%) Nature +
 *                    Weakened + 3 Broodlings on them. Eggs stay: no cap, no timer, only a step hatches one
 *   SW2 Lay Egg      at 10 s, then every 20 s (emote 0): a 4 yd marker follows each of 2 random non-tanks (4 at 6 or
 *                    more) for 2 s (heroic 3 s) and lands where they stand: an egg of SW1's kind drops there. Heroic:
 *                    the marked player also carries a bots-only RunOut measured from her, 16 yd
 *   SW3 Hatch        the hatched egg despawns, the burst plays, 3 Broodlings (2,000 health, heroic 3,000) ring the
 *                    hatcher and go for the player with the most Venom, else the hatcher
 *   SW4 Mother's     at 5 s, then every 10 s: a 6 yd splash at the spot of a random non-tank (2 at 6 or more), 2 s
 *       Milk         flight: 15% (heroic 20%) Nature + Weakened + a stack of Venom
 *   SW5 Venom        Poison, 1% of the reference row a second per stack, 30 s (refreshed by each stack), up to 5
 *                    stacks (heroic 8: a second spell); a Poison dispel clears every stack
 *   SW6 Crystal      at 12 s, then every 15 s she rears up for 2 s (cast bar) and a 60 degree cone 20 yd in front of
 *       Spray        her hits the non-tanks: 25% (heroic 30%) Frost + Weakened + 2 s encased; both tanks exempt at 10
 *   SW7 Brood Call   heroic, at 25 s, then every 30 s (emote 1): 3 s cast bar, not interruptible; at its end every
 *                    egg within 15 yd of her hatches: 3 Broodlings each onto the player nearest it, no damage. For the
 *                    bots a tank-only Park circle holds her where no egg is within the call's reach
 *   SW8 Last Milk    on her death every living player in the cave with quest 4866 incomplete and no Mother's Milk
 *                    16468 gets the stock aura (emote 2); the stock death spiderlings (16103) stay
 *   SW9 Reset        evade, wipe or death: eggs, markers, Broodlings and the Park circle go; the clutch comes back at
 *                    the next pull
 *   SW10 Widow's     10 players only, from 6 s, every 6 s: a stack of Widow's Bite on her target (Poison, 1% a second
 *       Bite         per stack, 15 s, each stack refreshing it, no cap); the taunt swap entry at 3 stacks
 *
 * Boss data: kill order the Broodlings (area damage ok), then her; no interrupts; dispel list Venom and Widow's Bite
 * (rewards); the taunt swap only at 10 players. Every timer runs on the AI's own clock, never on BossAI's scheduler.
 * Every firing logs one INFO line "brs smolderweb <mechanic> ..." (module.dungeonbosses); `.dbtest brs smolderweb ...`
 * fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SmolderwebLogic.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <functional>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsSmolderweb;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "smolderweb";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Vec2 ToVec(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    // Players of the cave the AI may act on: alive, in the world, not game masters, within `range` of `ref`.
    std::vector<Player*> PlayersNear(WorldObject const* ref, float range)
    {
        std::vector<Player*> out;
        Map* map = ref->GetMap();
        if (!map)
            return out;
        for (auto const& entry : map->GetPlayers())
        {
            Player* player = entry.GetSource();
            if (!player || !player->IsAlive() || !player->IsInWorld() || player->IsGameMaster())
                continue;
            if (ref->GetExactDist2d(player) > range)
                continue;
            out.push_back(player);
        }
        return out;
    }
}

// ====================================================================================================================
// Smolderweb Broodling 300705 (SW3): a Spire spiderling that bursts out of a hatched egg. Weak bite, 2,000 health. It
// goes for the player with the most Venom ("the young smell it"), else the player who hatched the egg.
// ====================================================================================================================
struct npc_brs_broodling : public ScriptedAI
{
    explicit npc_brs_broodling(Creature* creature) : ScriptedAI(creature) { }

    void SetHatcher(ObjectGuid hatcher)
    {
        _hatcher = hatcher;
        _retargetMs = 0;
    }

    void Reset() override
    {
        _retargetMs = 0;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (_retargetMs <= diff)
        {
            _retargetMs = kBroodlingRetargetMs;
            Retarget();
        }
        else
            _retargetMs -= diff;
        DoMeleeAttackIfReady();
    }

private:
    void Retarget()
    {
        std::vector<BroodlingCandidate> candidates;
        for (Player* player : PlayersNear(me, kBroodlingSeekYd))
        {
            uint32 const venom = DungeonKit::Stacks(player, SPELL_SW_VENOM) + DungeonKit::Stacks(player,
                SPELL_SW_VENOM_HEROIC);
            candidates.push_back({ player->GetGUID().GetRawValue(), venom, me->GetExactDist2d(player) });
        }
        std::optional<uint64> const pick = PickBroodlingTarget(candidates, _hatcher.GetRawValue());
        if (!pick)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, ObjectGuid(*pick));
        if (!target || me->GetVictim() == target)
            return;
        me->GetThreatMgr().ResetAllThreat();
        DoAddThreat(target, 1000.f);
        AttackStart(target);
    }

    ObjectGuid _hatcher;
    uint32 _retargetMs = 0;
};

// Mother Smolderweb 10596
struct boss_mother_smolderweb_rework : public BossAI
{
    explicit boss_mother_smolderweb_rework(Creature* creature)
        : BossAI(creature, BOSS_SMOLDERWEB), _arena(SmolderwebArena(), LeashOptions(kBossLogName)) { }

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

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _players = OnBossPull(me, kBossLogName);
        _heroic = IsHeroicMap(me);
        _tankSwap = DungeonKit::Flex::TankSwapOn(_players);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SMOLDERWEB;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        _layClock.Start(_clockMs, kLayBeat.firstMs);
        _milkClock.Start(_clockMs, kMilkBeat.firstMs);
        _sprayClock.Start(_clockMs, kSprayBeat.firstMs);
        if (_heroic)
        {
            _broodCallClock.Start(_clockMs, kBroodCallBeat.firstMs);
            _parkClock.Start(_clockMs, 1000);
        }
        if (_tankSwap)
            _biteClock.Start(_clockMs, kBiteBeat.firstMs);
        PlaceClutch();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} swap={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, _players,
                _tankSwap ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("eggs={} laid={} hatched={} killer={}", _eggs.size(), _eggsLaid, _eggsHatched,
                killer ? killer->GetName() : "none"));
        Cleanup();      // eggs, markers and Broodlings go (SummonList, DespawnAll) before the stock death spiderlings
        LastMilk();
        me->CastSpell(me, SPELL_SW_DEATH_SPIDERLINGS, true);
    }

    void UpdateAI(uint32 diff) override
    {
        // The delayed looks run in or out of combat (a `.dbtest` mechanic out of combat too).
        _clockMs += diff;
        UpdateLater();
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        UpdateBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        if (_layClock.Due(_clockMs))
        {
            _layClock.Fired(_clockMs, kLayBeat.everyMs);
            LayEggs(nullptr);
        }
        if (_milkClock.Due(_clockMs))
        {
            _milkClock.Fired(_clockMs, kMilkBeat.everyMs);
            SpitMilk(nullptr);
        }
        if (_biteClock.Due(_clockMs))
        {
            // A bite needs her target in reach (a tank taunting from range, or the next target after a tank died):
            // else it is tried again shortly (R-1-B n1).
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinDist(victim, kBiteReachYd))
            {
                _biteClock.Fired(_clockMs, kBiteBeat.everyMs);
                WidowsBite();
            }
            else
                _biteClock.Start(_clockMs, kBiteRetryMs);
        }
        if (_parkClock.Due(_clockMs))
        {
            _parkClock.Fired(_clockMs, kParkRenewMs);
            RenewPark();
        }
        // The two casts wait for each other (and for any cast in progress): they stay due until she is free.
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_sprayClock.Due(_clockMs))
        {
            _sprayClock.Fired(_clockMs, kSprayBeat.everyMs);
            StartSpray();
        }
        else if (_broodCallClock.Due(_clockMs))
        {
            _broodCallClock.Fired(_clockMs, kBroodCallBeat.everyMs);
            StartBroodCall();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW1 The Clutch, SW2 Lay Egg, SW3 Hatch
    // ----------------------------------------------------------------------------------------------------------------

    // The eight starting eggs, at the cave's fixed spots (floor height from the map when it is near the measured one).
    void PlaceClutch()
    {
        uint32 placed = 0;
        for (std::size_t i = 0; i < kClutchCount; ++i)
        {
            Point3 const spot = ClutchSpot(i);
            float const mapZ = me->GetMapHeight(spot.x, spot.y, spot.z + 3.f);
            bool const valid = mapZ > INVALID_HEIGHT + 1.f;
            float const z = EggZ(spot.z, mapZ, valid);
            if (PlaceEgg(Position(spot.x, spot.y, z, 0.f)))
                ++placed;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "clutch", Acore::StringFormat("eggs={}", placed));
    }

    // The lay: a marker follows each picked non-tank (`forced` = that player: the `.dbtest` entry) and lands where they
    // stand: the egg drops there. Heroic: the marked player also carries a bots-only RunOut measured from her.
    void LayEggs(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            targets = DungeonKit::PickPlayers(me, rule, kLayTargets.At(_players));
        }
        if (targets.empty())
            return;
        Talk(TEXT_LAY_EGG);
        uint32 const warn = kLayWarnMs(_heroic);
        std::string who;
        for (Player* player : targets)
        {
            DungeonKit::ImpactSpec impact;
            impact.pct = 0.f;
            impact.weakened = false;
            impact.tag = TAG_SW_LAY;
            Map* map = me->GetMap();
            ObjectGuid const bossGuid = me->GetGUID();
            MechanicRef marker = DungeonKit::FollowThenLand(me, player, kEggRadius, Ms(warn), impact,
                [map, bossGuid](Creature* /*owner*/, Position const& spot, BossMechanics::ResolveResult const&)
                {
                    Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
                    if (!boss || !boss->IsAIEnabled)
                        return;
                    if (auto* ai = dynamic_cast<boss_mother_smolderweb_rework*>(boss->AI()))
                        ai->EggLanded(spot);
                });
            Track(marker.Handle());
            if (_heroic)
            {
                MechanicRef carry = Mechanic::RunOut(me, player, kCarryClearYd, Ms(warn));
                carry.From(BossMechanics::MeasuredFrom::Owner).NoTelegraph().Tag(TAG_SW_CARRY);
                Track(carry.Handle());
            }
            who += (who.empty() ? "" : ",") + player->GetName();
        }
        ++_layRounds;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lay",
            Acore::StringFormat("round={} count={} warn={}s live={} targets={}", _layRounds, targets.size(),
                warn / 1000, _eggs.size(), who));
    }

    void EggLanded(Position const& spot)
    {
        if (PlaceEgg(spot))
            ++_eggsLaid;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "egg-laid",
            Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) live={}", spot.GetPositionX(), spot.GetPositionY(),
                spot.GetPositionZ(), _eggs.size()));
    }

    // One egg at `at`: the object, and the registry's Mine (the hitbox, the arming, the hit). False when it is not
    // placed (the safety cap, or the registry refused it).
    bool PlaceEgg(Position const& at)
    {
        if (_eggs.size() >= kEggSafetyCap)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "egg-refused",
                Acore::StringFormat("safety cap {} reached", kEggSafetyCap));
            return false;
        }
        float const x = at.GetPositionX();
        float const y = at.GetPositionY();
        float const z = at.GetPositionZ();
        Egg egg;
        egg.pos = Position(x, y, z, 0.f);
        if (GameObject* go = me->SummonGameObject(GO_BRS_SMOLDERWEB_EGG, x, y, z, frand(0.f, DungeonKit::kTwoPi), 0.f,
                0.f, 0.f, 0.f, kEggLifeSecs))
            egg.go = go->GetGUID();

        // A player's pet or guardian walking over an egg does not hatch it: players only (SP: "a player who steps in").
        BossMechanics::Eligibility playersOnly;
        playersOnly.playersOnly = true;
        MechanicRef ref = Mechanic::Mine(me, egg.pos, kEggRadius, Ms(kEggArmMs), Ms(kEggGraceMs));
        ref.Damage(kEggPct(_heroic)).Spell(SPELL_SW_EGG_HATCH).Weakened().Tag(TAG_SW_EGG).Eligible(playersOnly);
        ref.OnResolve(OnSmolderweb([](boss_mother_smolderweb_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.EggDone(r);
        }));
        egg.id = ref.Handle().id;
        if (!egg.id)
        {
            DeleteObject(egg.go);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "egg-refused", "the registry refused the mine");
            return false;
        }
        _eggs.push_back(egg);
        return true;
    }

    // An egg's Mine is done: a player stayed in it (it hatches), or it fizzled (the encounter ended).
    void EggDone(BossMechanics::ResolveResult const& result)
    {
        auto it = std::find_if(_eggs.begin(), _eggs.end(),
            [&result](Egg const& e) { return e.id == result.mechanicId; });
        if (it == _eggs.end())
            return;
        Egg const egg = *it;
        _eggs.erase(it);
        DeleteObject(egg.go);
        if (result.fizzled)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "egg-gone",
                Acore::StringFormat("live={}", _eggs.size()));
            return;
        }
        Player* hatcher = nullptr;
        for (ObjectGuid const& guid : result.hits)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
            {
                hatcher = player;
                break;
            }
        Position const burst = hatcher ? hatcher->GetPosition() : egg.pos;
        Hatch(egg.pos, burst, hatcher ? hatcher->GetGUID() : ObjectGuid::Empty);
        ++_eggsHatched;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hatch",
            Acore::StringFormat("by={} hits={} egg=({:.1f}, {:.1f}) live={}", hatcher ? hatcher->GetName() : "none",
                result.hits.size(), egg.pos.GetPositionX(), egg.pos.GetPositionY(), _eggs.size()));
    }

    // The burst at the egg and the three Broodlings in a ring around `burst` (the hatcher's spot).
    void Hatch(Position const& eggPos, Position const& burst, ObjectGuid hatcher)
    {
        me->CastSpell(eggPos.GetPositionX(), eggPos.GetPositionY(), eggPos.GetPositionZ(), SPELL_SW_HATCH_LOOK, true);
        SpawnBroodlings(burst, hatcher);
    }

    void SpawnBroodlings(Position const& at, ObjectGuid hatcher)
    {
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_BRS_BROODLING;
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = Ms(kBroodlingDespawnMs);
        spec.onSummon = [hatcher](Creature* add)
        {
            if (add->IsAIEnabled)
                if (auto* ai = dynamic_cast<npc_brs_broodling*>(add->AI()))
                    ai->SetHatcher(hatcher);
        };
        std::vector<Position> spots;
        float const start = frand(0.f, DungeonKit::kTwoPi);
        for (Vec2 const& p : BroodlingSpots(ToVec(at), start))
            spots.emplace_back(p.x, p.y, at.GetPositionZ(), DungeonKit::BearingTo(p, ToVec(at)));
        DungeonKit::SummonWave(me, spec, spots, summons);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW4 Mother's Milk, SW5 Venom
    // ----------------------------------------------------------------------------------------------------------------

    // `forced` = that player only (the `.dbtest` entry); else the picked non-tanks (1, or 2 at 6 or more). The splash
    // is where they stand now: a 2 s flight to a fixed spot, so a player who moves is out of it.
    void SpitMilk(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            targets = DungeonKit::PickPlayers(me, rule, kMilkTargets.At(_players));
        }
        std::string who;
        for (Player* player : targets)
        {
            Position const pos = player->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, pos, kMilkRadius, Ms(kMilkFlightMs));
            ref.Damage(kMilkPct(_heroic)).Spell(SPELL_SW_MILK).Weakened().Rider(VenomSpell(_heroic)).Tag(TAG_SW_MILK);
            Track(ref.Handle());
            LaunchMilkLook(pos);
            who += (who.empty() ? "" : ",") + player->GetName();
        }
        if (!targets.empty())
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "milk",
                Acore::StringFormat("count={} targets={}", targets.size(), who));
    }

    // The spat missile leaves her so it lands as the splash resolves.
    void LaunchMilkLook(Position const& pos)
    {
        float const dist = me->GetExactDist2d(pos.GetPositionX(), pos.GetPositionY());
        Later(MilkLaunchDelayMs(dist), [this, pos]()
        {
            me->CastSpell(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ(), SPELL_SW_MILK_LOOK, true);
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW6 Crystal Spray
    // ----------------------------------------------------------------------------------------------------------------

    void StartSpray()
    {
        DungeonKit::CastBar(me, SPELL_SW_SPRAY_CAST);
        MechanicRef ref = Mechanic::Cone(me, me, kSprayAngleDeg, kSprayLengthYd, Ms(kSprayCastMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kSprayPct(_heroic)).Spell(SPELL_SW_SPRAY).Weakened().Rider(SPELL_SW_ENCASED).Tag(TAG_SW_SPRAY);
        if (_tankSwap)
        {
            // At 10 players both tanks are exempt (the waiting one too): only healers and damage dealers are hit.
            BossMechanics::Eligibility nonTank;
            nonTank.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
            ref.Eligible(nonTank);
        }
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spray",
            Acore::StringFormat("pct={:.0f} angle={:.0f} length={:.0f}", kSprayPct(_heroic), kSprayAngleDeg,
                kSprayLengthYd));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW7 Brood Call (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void StartBroodCall()
    {
        DungeonKit::CastBar(me, SPELL_SW_BROOD_CALL, nullptr, TEXT_BROOD_CALL);
        Later(kBroodCallCastMs, [this]() { BroodCallHatch(); });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "brood-call",
            Acore::StringFormat("eggs={} in-reach={}", _eggs.size(), EggsInReach().size()));
    }

    std::vector<std::size_t> EggsInReach() const
    {
        std::vector<Vec2> points;
        points.reserve(_eggs.size());
        for (Egg const& egg : _eggs)
            points.push_back(ToVec(egg.pos));
        return EggsInBroodRange(points, ToVec(me->GetPosition()));
    }

    // The call lands: every egg within 15 yd of her hatches at once, 3 Broodlings each onto the player nearest it. No
    // damage: the Mine is cancelled (it never goes off), the object goes, the burst plays.
    void BroodCallHatch()
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        std::vector<Player*> const players = PlayersNear(me, kBroodlingSeekYd);
        std::vector<std::size_t> const reach = EggsInReach();
        std::vector<Vec2> where;
        where.reserve(players.size());
        for (Player* player : players)
            where.push_back(ToVec(player->GetPosition()));
        std::vector<Egg> gone;
        for (std::size_t index : reach)
        {
            Egg const& egg = _eggs[index];
            std::optional<std::size_t> const near = NearestTo(where, ToVec(egg.pos));
            Mechanic::Cancel(me, MechanicHandle{ egg.id });
            DeleteObject(egg.go);
            me->CastSpell(egg.pos.GetPositionX(), egg.pos.GetPositionY(), egg.pos.GetPositionZ(), SPELL_SW_HATCH_LOOK,
                true);
            Player* target = near ? players[*near] : nullptr;
            if (target)
                SpawnBroodlings(target->GetPosition(), target->GetGUID());
            gone.push_back(egg);
        }
        for (Egg const& egg : gone)
            _eggs.erase(std::remove_if(_eggs.begin(), _eggs.end(), [&egg](Egg const& e) { return e.id == egg.id; }),
                _eggs.end());
        _eggsHatched += static_cast<uint32>(gone.size());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "brood-hatch",
            Acore::StringFormat("eggs={} broodlings={} live={}", gone.size(), gone.size() * kBroodlingsPerEgg,
                _eggs.size()));
    }

    // For the bots: a hidden tank-only Park circle at a spot where she is held clear of every egg (the call's reach,
    // the circle, a margin). Where she stands when that holds; else the best floor point within kParkMaxMoveYd; else
    // where she stands. Renewed every kParkRenewMs, so it follows the floor as it fills.
    void RenewPark()
    {
        if (_park.IsValid())
            Mechanic::Cancel(me, _park);
        _park = MechanicHandle();
        std::vector<Vec2> eggs;
        eggs.reserve(_eggs.size());
        for (Egg const& egg : _eggs)
            eggs.push_back(ToVec(egg.pos));
        Position spot = me->GetPosition();
        bool moved = false;
        if (!ParkSpotClean(ToVec(spot), eggs))
        {
            DungeonKit::FloorSpotRules rules;
            rules.near = DungeonKit::PlaneOf(me);
            rules.minRange = 0.f;
            rules.maxRange = kParkMaxMoveYd;
            for (Vec2 const& egg : eggs)
                rules.avoid.push_back({ egg, ParkAvoidRadiusYd() });
            DungeonKit::FloorProbe probe;
            probe.z = me->GetPositionZ();
            probe.reachable = true;
            DungeonKit::Arena const arena = SmolderwebArena();
            if (std::optional<Position> const pick = DungeonKit::PickFloorSpot(me, &arena, rules, probe))
                if (ParkViolations(ToVec(*pick), eggs) < ParkViolations(ToVec(spot), eggs))
                {
                    spot = *pick;
                    moved = true;
                }
        }
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, spot, kParkRadiusYd, Ms(kParkHoldMs));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Tag(TAG_SW_PARK);
        _park = ref.Handle();
        if (moved)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "park",
                Acore::StringFormat("to=({:.1f}, {:.1f}) eggs={}", spot.GetPositionX(), spot.GetPositionY(),
                    eggs.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW8 Last Milk
    // ----------------------------------------------------------------------------------------------------------------

    // She spits her last milk across the cave: the stock Mother's Milk 16468 on every living quest 4866 holder in the
    // cave who lacks it (the gossip's two conditions), after the fight so no in-fight dispel or death strips it. The
    // stock spell is a dummy aura on every enemy within 10 yd of its caster, so it is put on each holder directly
    // (Unit::AddAura, the boss as caster) and the spat missile plays to their feet.
    uint32 LastMilk()
    {
        Talk(TEXT_LAST_MILK);
        uint32 given = 0;
        uint32 holders = 0;
        for (auto const& entry : me->GetMap()->GetPlayers())
        {
            Player* player = entry.GetSource();
            if (!player)
                continue;
            bool const questIncomplete = player->GetQuestStatus(kQuestRaggedJohn) == QUEST_STATUS_INCOMPLETE;
            if (questIncomplete)
                ++holders;
            if (!LastMilkWanted(player->IsAlive(), player->IsGameMaster(), questIncomplete,
                    player->HasAura(SPELL_SW_QUEST_MILK), me->GetExactDist2d(player),
                    player->GetPositionZ() - me->GetPositionZ()))
                continue;
            me->CastSpell(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(),
                SPELL_SW_MILK_LOOK, true);
            if (me->AddAura(SPELL_SW_QUEST_MILK, player))
                ++given;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "last-milk",
            Acore::StringFormat("holders={} given={}", holders, given));
        return given;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SW10 Widow's Bite (10 players)
    // ----------------------------------------------------------------------------------------------------------------

    // Her bite on her target adds a stack (the boss is the caster, which the taunt swap entry counts); each stack
    // refreshes the 15 s, so the debuff falls off the old tank 3 s before the new one is wanted again.
    void WidowsBite()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !victim->IsPlayer())
            return;
        uint32 const stacks = DungeonKit::AddStacks(victim, SPELL_SW_WIDOWS_BITE, 1, me);
        ++_bites;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bite",
            Acore::StringFormat("on={} stacks={}", victim->GetName(), stacks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP "Bots")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order the Broodlings (area damage ok), then her; no interrupts; Venom and Widow's Bite are rewards; at 10
    // players the second tank takes her at 3 stacks of Widow's Bite.
    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        BossMechanics::TargetEntry broodlings(NPC_BRS_BROODLING, 2, Who::Dps);
        broodlings.AoeOk();
        d.targets.push_back(std::move(broodlings));
        d.dispels.emplace_back(VenomSpell(_heroic), 2);
        if (_tankSwap)
        {
            d.dispels.emplace_back(SPELL_SW_WIDOWS_BITE, 1);
            d.tauntSwaps.emplace_back(NPC_SMOLDERWEB, SPELL_SW_WIDOWS_BITE, kBiteSwapAtStacks);
        }
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs smolderweb` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Clutch,
        Lay,
        Egg,
        Milk,
        Spray,
        Call,
        Bite,
        LastMilk,
        Clear,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, Player* gm)
    {
        if (!me->IsEngaged())
            return "Mother Smolderweb must be in combat (the picks read her threat list, the mechanics her encounter).";
        switch (mechanic)
        {
            case TestMechanic::Clutch:
                PlaceClutch();
                break;
            case TestMechanic::Lay:
                LayEggs(nullptr);
                break;
            case TestMechanic::Egg:
                if (!gm)
                    return "No player to put an egg under.";
                if (!PlaceEgg(gm->GetPosition()))
                    return "The egg was not placed (see the log).";
                break;
            case TestMechanic::Milk:
                SpitMilk(nullptr);
                break;
            case TestMechanic::Spray:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "She is casting already.";
                StartSpray();
                break;
            case TestMechanic::Call:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "She is casting already.";
                StartBroodCall();
                break;
            case TestMechanic::Bite:
                WidowsBite();
                break;
            case TestMechanic::LastMilk:
                LastMilk();
                break;
            case TestMechanic::Clear:
                ClearEggs();
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s players={} heroic={} swap={} eggs={}/{} laid={} hatched={} rounds={} "
            "bites={} summons={} later={} live={}", _clockMs / 1000, _players, _heroic ? 1 : 0, _tankSwap ? 1 : 0,
            _eggs.size(), kEggSafetyCap, _eggsLaid, _eggsHatched, _layRounds, _bites, summons.size(), _later.size(),
            _live.size());
    }

private:
    struct Egg
    {
        uint32 id = 0;          // the registry Mine
        ObjectGuid go;          // the object (may be empty: the summon failed)
        Position pos;
    };

    struct Pending
    {
        uint64 dueMs = 0;
        std::function<void()> fn;
    };

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if she is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnSmolderweb(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (!map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_mother_smolderweb_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    // `fn` after `delayMs` on the AI's own clock (in or out of combat); a Cleanup drops what is pending.
    void Later(uint32 delayMs, std::function<void()> fn)
    {
        _later.push_back({ _clockMs + delayMs, std::move(fn) });
    }

    void UpdateLater()
    {
        if (_later.empty())
            return;
        std::vector<Pending> due;
        for (auto it = _later.begin(); it != _later.end();)
        {
            if (_clockMs >= it->dueMs)
            {
                due.push_back(std::move(*it));
                it = _later.erase(it);
            }
            else
                ++it;
        }
        for (Pending& p : due)
            p.fn();
    }

    // A mechanic of the fight (a marker, a splash, the cone, a carry hint): kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    void DeleteObject(ObjectGuid guid)
    {
        if (!guid)
            return;
        if (GameObject* go = me->GetMap()->GetGameObject(guid))
            go->Delete();
    }

    // Every egg off the floor with its Mine (a test, a reset, her death): nobody is hit.
    void ClearEggs()
    {
        for (Egg const& egg : _eggs)
        {
            Mechanic::Cancel(me, MechanicHandle{ egg.id });
            DeleteObject(egg.go);
        }
        _eggs.clear();
    }

    // The pull's state: no egg, no marker, no Broodling, no park circle, nothing pending (Reset, evade, death, a new
    // pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_park.IsValid())
            Mechanic::Cancel(me, _park);
        _park = MechanicHandle();
        ClearEggs();
        _later.clear();
        summons.DespawnAll();
        _clockMs = 0;
        _layClock.Stop();
        _milkClock.Stop();
        _sprayClock.Stop();
        _broodCallClock.Stop();
        _biteClock.Stop();
        _parkClock.Stop();
        _layRounds = 0;
        _eggsLaid = 0;
        _eggsHatched = 0;
        _bites = 0;
        _arena.Reset();
        // Her Venom and Widow's Bite end with the attempt (a wipe or the kill): no Poison ticks past the fight
        // (R-1-B m1; B7 and B9 do the same for theirs).
        if (instance)
            for (uint32 const spell : { uint32(SPELL_SW_VENOM), uint32(SPELL_SW_VENOM_HEROIC),
                uint32(SPELL_SW_WIDOWS_BITE) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    BeatClock _layClock;
    BeatClock _milkClock;
    BeatClock _sprayClock;
    BeatClock _broodCallClock;
    BeatClock _biteClock;
    BeatClock _parkClock;
    std::vector<Egg> _eggs;
    std::vector<MechanicHandle> _live;
    std::vector<Pending> _later;
    MechanicHandle _park;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint32 _layRounds = 0;
    uint32 _eggsLaid = 0;
    uint32 _eggsHatched = 0;
    uint32 _bites = 0;
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    bool _heroic = false;
    bool _tankSwap = false;         // 10 players: Widow's Bite and the taunt swap
};

namespace
{
    boss_mother_smolderweb_rework* FindSmolderwebAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_SMOLDERWEB);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_mother_smolderweb_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Mother Smolderweb is not running boss_mother_smolderweb_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_mother_smolderweb_rework::TestMechanic mechanic, char const* what)
    {
        boss_mother_smolderweb_rework* ai = FindSmolderwebAI(handler);
        if (!ai)
            return false;
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        std::string const error = ai->TestFire(mechanic, gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Smolderweb: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_SMOLDERWEB, BOSS_SMOLDERWEB);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_mother_smolderweb_rework* ai = FindSmolderwebAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Smolderweb: {}", ai->TestState());
        return true;
    }

    bool HandleClutch(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Clutch,
            "the starting clutch (SW1: the eight eggs at the cave's spots)");
    }

    bool HandleLay(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Lay,
            "Lay Egg (SW2: a marker on each picked non-tank, an egg where it lands)");
    }

    bool HandleEgg(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Egg,
            "an egg under you (SW1; it arms in 1.5 s, `.gm off` to hatch it)");
    }

    bool HandleMilk(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Milk,
            "Mother's Milk (SW4: a 6 yd splash after 2 s, a stack of Venom)");
    }

    bool HandleSpray(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Spray,
            "Crystal Spray (SW6: 2 s rear-up, then the cone)");
    }

    bool HandleCall(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Call,
            "Brood Call (SW7: 3 s, then every egg within 15 yd of her hatches)");
    }

    bool HandleBite(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Bite,
            "Widow's Bite (SW10: a stack on her target)");
    }

    bool HandleLastMilk(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::LastMilk,
            "Last Milk (SW8: the quest aura on every quest 4866 holder in the cave)");
    }

    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, boss_mother_smolderweb_rework::TestMechanic::Clear, "every egg cleared");
    }

    // `.dbtest brs smolderweb <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& SmolderwebTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "clutch",   HandleClutch,   SEC_GAMEMASTER, Console::No },
            { "lay",      HandleLay,      SEC_GAMEMASTER, Console::No },
            { "egg",      HandleEgg,      SEC_GAMEMASTER, Console::No },
            { "milk",     HandleMilk,     SEC_GAMEMASTER, Console::No },
            { "spray",    HandleSpray,    SEC_GAMEMASTER, Console::No },
            { "call",     HandleCall,     SEC_GAMEMASTER, Console::No },
            { "bite",     HandleBite,     SEC_GAMEMASTER, Console::No },
            { "lastmilk", HandleLastMilk, SEC_GAMEMASTER, Console::No },
            { "clear",    HandleClear,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Venom (SW5): the stock periodic-damage script (1% of the reference row a second per stack) is bound by the kit's
// spell_dungeon_refflat_periodic; this one adds the dispel rule: a Poison dispel clears every stack, not one.
class spell_brs_smolderweb_venom : public AuraScript
{
    PrepareAuraScript(spell_brs_smolderweb_venom);

    void ClearAllStacks(DispelInfo* dispelInfo)
    {
        dispelInfo->SetRemovedCharges(std::max<uint8>(1, GetStackAmount()));
    }

    void Register() override
    {
        OnDispel += AuraDispelFn(spell_brs_smolderweb_venom::ClearAllStacks);
    }
};

void AddSC_boss_mother_smolderweb_rework()
{
    RegisterDungeonReworkCreatureAI(boss_mother_smolderweb_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_broodling, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_smolderweb_venom);
    BrsTest::RegisterBoss("smolderweb", SmolderwebTestCommands());
}
