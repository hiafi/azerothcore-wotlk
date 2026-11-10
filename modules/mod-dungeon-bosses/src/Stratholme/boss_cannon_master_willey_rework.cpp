/*
 * mod-dungeon-bosses, Stratholme S5: Cannon Master Willey (10997), "a firing range, and you're the targets". Build spec
 * ST 1444-1502 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows WY, 3.5 row S5, 3.6, 3.8 (the hall
 * frame kWilleyHall). Replaces stock SmartAI 10997 (Knock Away, Pummel, Summon Crimson Rifleman 17279 in threes and
 * its death burst) and the Crimson Rifleman's 11054 (Shoot, the out-of-combat attack and despawn, death by the click
 * Cannon Fire 17278): WP-S5's SQL rev drops those rows, turns the stock cannons' spawns into Mercy and Zeal and
 * removes the Cannonball Stacks; bound by apps/dbc-tools source/npcs/stratholme/cannon_master_willey.py. Pure rules:
 * WilleyLogic.h.
 *
 *   WY1 The Drill   at 6 s, then every 20 s ("Ready!", yell line 1): a rank of 3 (heroic 4) Crimson Riflemen marches
 *                   in from the yard opening and forms across the hall's far end (X 52); at most 6 (heroic 8) alive:
 *                   a due rank waits until it fits. No riflemen on his death
 *   WY2 Aim         6 s (heroic 4 s) after a rank forms ("Aim!", line 2): each rifleman marks a random player (a red
 *                   arrow, 206500; distinct players while there are enough) and carries Taking Aim (206501, the bots'
 *                   first kill target)
 *   WY3 Fire        3 s (heroic 2 s) later ("Fire!", line 3): each aiming rifleman still standing and in control
 *                   shoots its mark, 15% / 20% Physical, not avoidable (206502); the rank aims again 8 s later.
 *                   Between volleys the riflemen shoot their stock Shoot 17353 every 2 s
 *   WY4 Cannonball  the last rifleman of a rank to die drops a Scarlet Cannonball (301202) for 20 s: a walk-over
 *                   pickup for a player without one (never the tank)
 *   WY5 Holding     Holding Cannonball (206503): -30% speed, 30 s, then the ball is lost
 *   WY6 Load        a carrier 2 s in a gun's load spot (behind its breech) loads it: the gun fires point-blank at him,
 *                   5% of his maximum health (206504, never the killing blow), line 6 on the first load
 *   WY7 Shaken      +10% damage taken a stack (206505), up to 3, 15 s, refreshed by each load
 *   WY8 Cannon Fire normal, at 10 s then every 12 s: he calls Mercy or Zeal (line 4 / 5) and the gun fires down its
 *                   half of the hall, the full length: a 2.5 s line marker, 40% Fire, tank included, no Weakened
 *   WY9 The Barrage heroic, replaces Cannon Fire, at 12 s then every 20 s: the whole order of 5 blasts (3 on one half,
 *                   2 on the other) as a center-screen boss emote, 3 s before the first blast, then one every 1.5 s;
 *                   30% Fire + Weakened each; no marker (NoTelegraph, ruling 23): bots read the hidden lines
 *   WY10            melee, Knock Away 10101 on his victim, Pummel 15615 on a caster within 5 yd (stock, DD-scaled)
 *   Guns            a glow ring under each gun for the fight (stalker 300610: Mercy gold 206509, Zeal orange
 *                   206510)
 *   Arena           StratholmeRework::LeashOptions on WilleyArena() (the hall frame; no grips; holds at the edge);
 *                   the lanes' spot bounds keep the bots' dodges in the hall, never the yard (HallBounds)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler. Every firing logs one INFO line
 * "strat willey <mechanic> ..." (module.dungeonbosses).
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
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WilleyLogic.h"
#include <algorithm>
#include <array>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratWilley;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "willey";

    // The Barrage's call reaches the whole hall (58 yd) and the yard beside it; a plain text emote stops at 25 yd.
    float constexpr kCallRangeYd = 150.f;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    // A frame point on the hall floor (the hall is flat, z 125.1..126.5).
    Position HallPos(Vec2 p, float orientation = 0.f)
    {
        return DungeonKit::ToPosition(p, kWilleySpawn.z, orientation);
    }

    // Where a bot may plan to stand for his lanes: the hall, never the yard its far end opens into (F-2).
    BossMechanics::SpotBounds HallBounds()
    {
        std::vector<Position> corners;
        for (Vec2 const& p : HallSpotCorners())
            corners.push_back(HallPos(p));
        BossMechanics::SpotBounds b;
        b.Polygon(std::move(corners), kSpotZMin, kSpotZMax);
        return b;
    }

    BossMechanics::ZoneSpec LaneShape(Gun gun)
    {
        return BossMechanics::Shapes::LineFacing(HallPos(LaneStart(gun)), kWilleyHall.angle, kHallLength, kHalfWidth);
    }

    // A rifleman (or a player) that cannot act on its own now: a stunned, feared, charmed or polymorphed rifleman
    // misses its volley (crowd control is an answer to the Drill, like the kill).
    bool OutOfControl(Unit const* unit)
    {
        return unit->HasUnitState(UNIT_STATE_LOST_CONTROL);
    }
}

// Cannon Master Willey 10997
struct boss_cannon_master_willey_rework : public BossAI
{
    explicit boss_cannon_master_willey_rework(Creature* creature)
        : BossAI(creature, BOSS_WILLEY), _arena(WilleyArena(), LeashOptions(kLogBoss)) { }

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
        options.bossStateId = BOSS_WILLEY;
        Mechanic::BeginEncounter(me, options);
        Describe();

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        SpawnGlows();
        Talk(YELL_WILLEY_AGGRO);
        bool const heroic = IsHeroicMap(me);
        _nextGunsMs = heroic ? kBarrageCadence.first : kCannonFireCadence.first;
        _nextKnockAwayMs = PickInRange(kKnockAwayFirst, Rand01());
        _nextPummelMs = 0;
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
        BossAI::JustDied(killer);   // DONE; his riflemen despawn with his summons (no death burst)
        Cleanup();
        Talk(YELL_WILLEY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("ranks={} loads={} killer={}", _ranksFormed, _loads,
                killer ? killer->GetName() : "none"));
    }

    // The glow stalkers are his summons (they go with his reset and death) but never fight: not zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == kNpcGunGlow)
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    // WY6 never the killing blow (F-2): the cannon shot is the only damage he deals himself; after every damage-taken
    // modifier (ShotDamage divides out Shaken only, not a player's curse or debuff) it leaves him at 1 health.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (attacker == me)
            damage = SelfDamageCap(me->GetHealth(), damage);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (summon->GetEntry() == NPC_CRIMSON_RIFLEMAN)
            RiflemanGone(summon, true);
        BossAI::SummonedCreatureDies(summon, killer);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_CRIMSON_RIFLEMAN)
            RiflemanGone(summon, false);
        BossAI::SummonedCreatureDespawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        // The pickups poll in or out of combat (a `.dbtest` ball out of combat too); Cleanup clears them on a reset.
        _pickups.Update(me, diff);
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        bool const heroic = IsHeroicMap(me);
        UpdateCarriers(diff);
        UpdateRanks();

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateDrill(heroic);
        if (_clockMs >= _nextGunsMs)
        {
            if (heroic)
            {
                _nextGunsMs = _clockMs + kBarrageCadence.every;
                Barrage();
            }
            else
            {
                _nextGunsMs = _clockMs + kCannonFireCadence.every;
                CannonFire(GunFromRoll(urand(0, 1)));
            }
        }
        if (_clockMs >= _nextKnockAwayMs)
            KnockAway();
        if (_clockMs >= _nextPummelMs)
            Pummel();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY1 The Drill, WY2 Aim, WY3 Fire
    // ----------------------------------------------------------------------------------------------------------------

    struct Rank
    {
        uint32 id = 0;
        std::vector<ObjectGuid> members;
        std::vector<std::pair<ObjectGuid, ObjectGuid>> aims;    // rifleman -> its mark, while aiming
        RankCycle cycle;
    };

    uint32 AliveRiflemen() const
    {
        uint32 alive = 0;
        for (Rank const& rank : _ranks)
            for (ObjectGuid const& guid : rank.members)
                if (Creature* rifleman = me->GetMap()->GetCreature(guid))
                    if (rifleman->IsAlive())
                        ++alive;
        return alive;
    }

    void UpdateDrill(bool heroic)
    {
        if (!_drill.Due(_clockMs))
            return;
        if (!CanForm(AliveRiflemen(), kRankSize(heroic), kRiflemanCap(heroic)))
            return;     // held: it comes as soon as it fits
        if (FormRank(heroic))
            _drill.Formed(_clockMs);
        else
            _drill.RetryIn(_clockMs, 1000);     // the summon failed: try again in 1 s
    }

    // A rank appears at the yard opening and marches to its spots at the hall's far end. False: nobody summoned.
    bool FormRank(bool heroic)
    {
        std::size_t const size = RankSpotCount(heroic);
        std::vector<Position> at;
        for (std::size_t i = 0; i < size; ++i)
        {
            Vec2 const start = MarchStart(i, size);
            Point3 const spot = RankSpot(heroic, i);
            at.emplace_back(start.x, start.y, kRankZ, DungeonKit::BearingTo(start, spot.XY()));
        }

        Rank rank;
        rank.id = ++_ranksFormed;
        std::size_t index = 0;
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_CRIMSON_RIFLEMAN;
        spec.onSummon = [&rank, &index, heroic](Creature* rifleman)
        {
            rank.members.push_back(rifleman->GetGUID());
            Point3 const spot = RankSpot(heroic, index++);
            rifleman->GetMotionMaster()->MovePoint(POINT_WY_RANK, spot.x, spot.y, spot.z);
        };
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, at, summons);
        if (wave.empty())
            return false;
        rank.cycle.Summoned(_clockMs, heroic);
        _ranks.push_back(std::move(rank));
        Yell(YELL_WILLEY_READY, _lastReadyYellMs);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "drill",
            Acore::StringFormat("rank={} size={} alive={}", _ranks.back().id, wave.size(), AliveRiflemen()));
        return true;
    }

    void UpdateRanks()
    {
        for (Rank& rank : _ranks)
            switch (rank.cycle.Update(_clockMs))
            {
                case RankStep::Aim:
                    Aim(rank);
                    break;
                case RankStep::Fire:
                    Fire(rank);
                    break;
                default:
                    break;
            }
    }

    // WY2: each rifleman still standing marks a random player, a different one while there are enough.
    void Aim(Rank& rank)
    {
        rank.aims.clear();
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        uint32 marked = 0;
        for (ObjectGuid const& guid : rank.members)
        {
            Creature* rifleman = me->GetMap()->GetCreature(guid);
            if (!rifleman || !rifleman->IsAlive())
                continue;
            Player* target = DungeonKit::PickPlayer(me, rule);
            if (!target)
            {
                DungeonKit::PickRule any;
                any.nonTank = false;
                target = DungeonKit::PickPlayer(me, any);   // fewer players than riflemen: marks repeat
            }
            if (!target)
                continue;
            rule.exclude.push_back(target->GetGUID().GetRawValue());
            rifleman->CastStop();
            rifleman->SetFacingToObject(target);
            rifleman->CastSpell(target, SPELL_WY_AIM, true);
            rifleman->CastSpell(rifleman, SPELL_WY_TAKING_AIM, true);
            rank.aims.emplace_back(guid, target->GetGUID());
            ++marked;
        }
        if (!marked)
            return;
        Yell(YELL_WILLEY_AIM, _lastAimYellMs);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "aim",
            Acore::StringFormat("rank={} marked={} heroic={}", rank.id, marked, IsHeroicMap(me) ? 1 : 0));
    }

    // WY3: every aiming rifleman still standing and in control shoots its mark.
    void Fire(Rank& rank)
    {
        if (rank.aims.empty())
            return;
        uint32 shots = 0;
        uint32 jammed = 0;
        for (auto const& [riflemanGuid, targetGuid] : rank.aims)
        {
            Creature* rifleman = me->GetMap()->GetCreature(riflemanGuid);
            Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
            if (target)
                target->RemoveAurasDueToSpell(SPELL_WY_AIM, riflemanGuid);
            if (!rifleman || !rifleman->IsAlive())
                continue;
            rifleman->RemoveAurasDueToSpell(SPELL_WY_TAKING_AIM);
            if (!target || !target->IsAlive() || !target->IsInMap(rifleman))
                continue;
            if (OutOfControl(rifleman))
            {
                ++jammed;
                continue;
            }
            rifleman->CastSpell(target, SPELL_WY_FIRE, true);
            ++shots;
        }
        rank.aims.clear();
        Yell(YELL_WILLEY_FIRE, _lastFireYellMs);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "fire",
            Acore::StringFormat("rank={} shots={} jammed={}", rank.id, shots, jammed));
    }

    // A rifleman died (or despawned): its mark loses the arrow; the last of a rank to die drops the rank's ball.
    void RiflemanGone(Creature* rifleman, bool died)
    {
        ObjectGuid const guid = rifleman->GetGUID();
        for (auto rankIt = _ranks.begin(); rankIt != _ranks.end(); ++rankIt)
        {
            Rank& rank = *rankIt;
            if (std::find(rank.members.begin(), rank.members.end(), guid) == rank.members.end())
                continue;
            for (auto it = rank.aims.begin(); it != rank.aims.end(); ++it)
                if (it->first == guid)
                {
                    if (Player* target = ObjectAccessor::GetPlayer(*me, it->second))
                        target->RemoveAurasDueToSpell(SPELL_WY_AIM, guid);
                    rank.aims.erase(it);
                    break;
                }
            rank.members.erase(std::remove(rank.members.begin(), rank.members.end(), guid), rank.members.end());
            bool anyAlive = false;
            for (ObjectGuid const& other : rank.members)
                if (Creature* c = me->GetMap()->GetCreature(other))
                    if (c->IsAlive())
                        anyAlive = true;
            if (anyAlive)
                return;
            uint32 const rankId = rank.id;
            _ranks.erase(rankIt);
            if (died && me->IsAlive() && me->IsEngaged())
                DropBall(rifleman->GetPosition(), rankId);
            return;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY4 Cannonball, WY5 Holding, WY6 Load, WY7 Shaken
    // ----------------------------------------------------------------------------------------------------------------

    void DropBall(Position const& at, uint32 rankId)
    {
        DungeonKit::PickupSpec spec;
        spec.radius = kBallRadius;
        spec.life = Ms(kBallLifeMs);
        spec.who.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        spec.who.auraSpell = SPELL_WY_HOLDING_CANNONBALL;    // one ball a player
        spec.who.minStacks = 0;
        spec.who.maxStacks = 0;
        spec.count = 1;
        spec.color = BossMechanics::Color::Yellow;
        spec.goEntry = GO_ST_CANNONBALL;
        spec.tag = TAG_CANNONBALL;
        spec.onPick = [this](Player* taker) { BallPicked(taker); };
        spec.onExpire = [rankId]()
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "ball-lost", Acore::StringFormat("rank={} (20 s)", rankId));
        };
        uint32 const id = _pickups.Add(me, at, std::move(spec));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "ball-drop",
            Acore::StringFormat("rank={} at=({:.1f}, {:.1f}) id={}", rankId, at.GetPositionX(), at.GetPositionY(), id));
    }

    void BallPicked(Player* taker)
    {
        if (!taker)
            return;
        taker->CastSpell(taker, SPELL_WY_HOLDING_CANNONBALL, true);
        _carrierPollMs = kCarrierPollMs;    // the load spots appear on the next update
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "ball-picked", taker->GetName());
    }

    bool AnyCarrier() const
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && player->HasAura(SPELL_WY_HOLDING_CANNONBALL))
                    return true;
        return false;
    }

    // The two load spots exist while someone carries a ball (carrier-only Soaks: the bots' delivery job).
    void UpdateCarriers(uint32 diff)
    {
        _carrierPollMs += diff;
        if (_carrierPollMs < kCarrierPollMs)
            return;
        _carrierPollMs = 0;
        bool const carrying = AnyCarrier();
        for (Gun gun : { Gun::Mercy, Gun::Zeal })
        {
            uint32& id = _loadIds[static_cast<std::size_t>(gun)];
            if (carrying && !id)
                id = AddLoadSpot(gun);
            else if (!carrying && id)
            {
                _pickups.Cancel(me, id);
                id = 0;
            }
        }
    }

    uint32 AddLoadSpot(Gun gun)
    {
        DungeonKit::PickupSpec spec;
        spec.radius = kLoadRadius;
        spec.life = Ms(kLoadSpotLifeMs);
        spec.dwell = Ms(kLoadDwellMs);
        spec.who.auraSpell = SPELL_WY_HOLDING_CANNONBALL;    // carriers only
        spec.who.minStacks = 1;
        spec.count = 1;
        spec.color = BossMechanics::Color::Yellow;
        spec.tag = TAG_LOAD;
        spec.onPick = [this, gun](Player* taker) { GunLoaded(gun, taker); };
        Vec2 const at = LoadSpot(gun);
        return _pickups.Add(me, HallPos(at), std::move(spec));
    }

    // The guns' names on the floor: a gold ring under Mercy, an orange one under Zeal, for the fight (the stalker
    // carries the glow aura; his reset and death despawn it with his summons).
    void SpawnGlows()
    {
        for (Gun gun : { Gun::Mercy, Gun::Zeal })
        {
            Point3 const at = GunAt(gun);
            if (Creature* glow = me->SummonCreature(kNpcGunGlow, at.x, at.y, at.z, 0.f, TEMPSUMMON_MANUAL_DESPAWN))
                glow->CastSpell(glow, GlowSpell(gun), true);
        }
    }

    GameObject* FindGun(Gun gun) const
    {
        return me->FindNearestGameObject(gun == Gun::Mercy ? GO_ST_MERCY : GO_ST_ZEAL, kGunSearchYd);
    }

    // WY6: the carrier loads the gun; it swings round and fires point-blank at him. WY7: a Shaken stack.
    void GunLoaded(Gun gun, Player* taker)
    {
        _loadIds[static_cast<std::size_t>(gun)] = 0;      // taken: re-added on the next poll while carriers remain
        _carrierPollMs = kCarrierPollMs;
        if (!taker || !taker->HasAura(SPELL_WY_HOLDING_CANNONBALL))
            return;
        taker->RemoveAurasDueToSpell(SPELL_WY_HOLDING_CANNONBALL);
        ShootWilley(gun, taker->GetName());
    }

    void ShootWilley(Gun gun, std::string const& by)
    {
        if (GameObject* go = FindGun(gun))
            go->SendCustomAnim(0);
        uint32 const stacks = DungeonKit::Stacks(me, SPELL_WY_SHAKEN);
        uint32 const damage = ShotDamage(me->GetMaxHealth(), me->GetHealth(), stacks);
        if (damage)
            me->CastCustomSpell(SPELL_WY_CANNON_SHOT, SPELLVALUE_BASE_POINT0, static_cast<int32>(damage), me, true);
        uint32 const after = DungeonKit::AddStacks(me, SPELL_WY_SHAKEN, 1, me, kShakenMaxStacks);
        if (!_loads++)
            Talk(YELL_WILLEY_MY_GUNS);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "load",
            Acore::StringFormat("gun={} by={} shot={} shaken={}->{}", GunName(gun), by, damage, stacks, after));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY8 Cannon Fire (normal), WY9 the Barrage (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void CannonFire(Gun gun)
    {
        Talk(gun == Gun::Mercy ? YELL_WILLEY_MERCY_FIRE : YELL_WILLEY_ZEAL_FIRE);
        MechanicRef ref = Mechanic::Zone(me, LaneShape(gun), Ms(kCannonFireWarnMs));
        ref.Damage(kCannonFirePct).Spell(SPELL_WY_CANNON_FIRE).Within(HallBounds()).Tag(TAG_CANNON_FIRE);
        ref.OnResolve(OnWilley([gun](boss_cannon_master_willey_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.GunFired(gun, r.hits.size(), "cannon-fire-lands");
        }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "cannon-fire", GunName(gun));
    }

    // Five hidden lines, all registered at the call (the stratholme-followups drill's shape): the emote names the
    // order, nothing is drawn, each blast lands 3 s + 1.5 s x its place after the call.
    void Barrage()
    {
        BarrageOrder const order = MakeBarrageOrder(urand(0, kBarrageOrders - 1));
        std::string const call = BarrageCall(order);
        me->Talk(call, CHAT_MSG_RAID_BOSS_EMOTE, LANG_UNIVERSAL, kCallRangeYd, nullptr);
        for (uint32 i = 0; i < kBarrageBlasts; ++i)
        {
            Gun const gun = order[i];
            MechanicRef ref = Mechanic::Zone(me, LaneShape(gun), Ms(BlastDelayMs(i)));
            ref.NoTelegraph().Damage(kBarragePct).Spell(SPELL_WY_BARRAGE).Weakened().Within(HallBounds())
                .Tag(TAG_BARRAGE);
            ref.OnResolve(OnWilley([gun](boss_cannon_master_willey_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.GunFired(gun, r.hits.size(), "barrage-blast");
            }));
            Track(ref.Handle());
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "barrage", call.substr(call.find(':') + 2));
    }

    // A lane fired: the gun's firing animation and bursts down its half (the impact; the registry dealt the damage).
    void GunFired(Gun gun, std::size_t hits, char const* what)
    {
        if (GameObject* go = FindGun(gun))
            go->SendCustomAnim(0);
        for (float x : kBurstX)
        {
            Vec2 const p = LanePoint(gun, x);
            me->CastSpell(p.x, p.y, kWilleySpawn.z, SPELL_WY_BLAST_LOOK, true);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, what, Acore::StringFormat("gun={} hits={}", GunName(gun), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY10 the stock kit
    // ----------------------------------------------------------------------------------------------------------------

    void KnockAway()
    {
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            DoCastVictim(SPELL_WY_KNOCK_AWAY);
            _nextKnockAwayMs = _clockMs + PickInRange(kKnockAwayEvery, Rand01());
        }
        else
            _nextKnockAwayMs = _clockMs + 1000;
    }

    void Pummel()
    {
        _nextPummelMs = _clockMs + 500;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsNonMeleeSpellCast(false)
                || me->GetDistance(player) > kPummelRange || !me->IsValidAttackTarget(player))
                continue;
            DoCast(player, SPELL_WY_PUMMEL);
            _nextPummelMs = _clockMs + PickInRange(kPummelEvery, Rand01());
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "pummel", player->GetName());
            return;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST "Bots"): kill order the aiming riflemen, then the others, then him; no interrupts, no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        BossMechanics::TargetEntry aiming(NPC_CRIMSON_RIFLEMAN, 3, Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_WY_TAKING_AIM));
        aiming.AoeOk();
        d.targets.push_back(std::move(aiming));
        BossMechanics::TargetEntry rifleman(NPC_CRIMSON_RIFLEMAN, 2, Who::Dps);
        rifleman.AoeOk();
        d.targets.push_back(std::move(rifleman));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat willey` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Rank,
        Aim,
        Mercy,
        Zeal,
        Barrage,
        Load,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic, Player* gm)
    {
        if (!me->IsEngaged())
            return "Willey must be in combat (the ranks, the guns and the Barrage run only in the fight).";
        switch (mechanic)
        {
            case TestMechanic::Rank:
                if (!FormRank(heroic))
                    return "No rifleman could be summoned.";
                break;
            case TestMechanic::Aim:
                if (_ranks.empty())
                    return "No rank stands (`.dbtest strat willey rank` first).";
                for (Rank& rank : _ranks)
                    rank.cycle.AimNow(_clockMs);
                break;
            case TestMechanic::Mercy:
                CannonFire(Gun::Mercy);
                break;
            case TestMechanic::Zeal:
                CannonFire(Gun::Zeal);
                break;
            case TestMechanic::Barrage:
                Barrage();
                break;
            case TestMechanic::Load:
                ShootWilley(gm && gm->GetExactDist2d(GunAt(Gun::Zeal).x, GunAt(Gun::Zeal).y)
                    < gm->GetExactDist2d(GunAt(Gun::Mercy).x, GunAt(Gun::Mercy).y) ? Gun::Zeal : Gun::Mercy,
                    gm ? gm->GetName() : "test");
                break;
        }
        return {};
    }

    // A ball at the GM's feet (out of combat too). A game master never picks it up (the pickups skip GMs): `.gm off`.
    void TestBall(Position const& at)
    {
        DropBall(at, 0);
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s ranks={} riflemen={} nextRank={}s guns={}s shaken={} loads={} "
            "pickups={} loadSpots={}/{}", _clockMs / 1000, _ranks.size(), AliveRiflemen(), _drill.DueMs() / 1000,
            _nextGunsMs / 1000, DungeonKit::Stacks(me, SPELL_WY_SHAKEN), _loads, _pickups.Count(), _loadIds[0],
            _loadIds[1]);
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnWilley(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_cannon_master_willey_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // One yell line, never twice within kYellGapMs (two ranks on one beat).
    void Yell(uint8 group, uint64& last)
    {
        if (last && _clockMs < last + kYellGapMs)
            return;
        last = _clockMs ? _clockMs : 1;
        Talk(group);
    }

    // The pull's state: nothing pending, no ranks, no balls, no carriers, no Shaken (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _pickups.Clear(me);
        _loadIds = { 0, 0 };
        // Marks and balls are this fight's: every player loses them when it ends.
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
            {
                player->RemoveAurasDueToSpell(SPELL_WY_HOLDING_CANNONBALL);
                player->RemoveAurasDueToSpell(SPELL_WY_AIM);
            }
        _ranks.clear();
        summons.DespawnAll();
        if (me->IsAlive())
            me->RemoveAurasDueToSpell(SPELL_WY_SHAKEN);
        _clockMs = 0;
        _drill.Reset();
        _nextGunsMs = kCannonFireCadence.first;
        _nextKnockAwayMs = 0;
        _nextPummelMs = 0;
        _carrierPollMs = 0;
        _lastReadyYellMs = 0;
        _lastAimYellMs = 0;
        _lastFireYellMs = 0;
        _loads = 0;
        _ranksFormed = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::Pickups _pickups;
    DrillClock _drill;
    std::vector<Rank> _ranks;
    std::vector<MechanicHandle> _live;
    std::array<uint32, 2> _loadIds{ { 0, 0 } };   // Mercy, Zeal: the live load spot (0: none)
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextGunsMs = 0;
    uint64 _nextKnockAwayMs = 0;
    uint64 _nextPummelMs = 0;
    uint64 _lastReadyYellMs = 0;
    uint64 _lastAimYellMs = 0;
    uint64 _lastFireYellMs = 0;
    uint32 _carrierPollMs = 0;
    uint32 _loads = 0;
    uint32 _ranksFormed = 0;
};

// A Crimson Rifleman (11054): stands where its rank formed (no chasing), shoots its stock Shoot 17353 at a random
// player every 2 s, never while aiming (Willey drives Aim and Fire), and swings at anyone in melee range.
struct npc_st_crimson_rifleman : public ScriptedAI
{
    // No combat movement from the start: the summon is put into combat before its first update (Creature.h: changing
    // it in combat only affects the next AttackStart), so the march's MovePoint is never replaced by a chase.
    explicit npc_st_crimson_rifleman(Creature* creature) : ScriptedAI(creature)
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        me->SetCombatMovement(false);
        _shootMs = urand(500, kShootEveryMs);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim))
        {
            DoMeleeAttackIfReady();
            return;
        }
        _shootMs = diff >= _shootMs ? 0 : _shootMs - diff;
        if (_shootMs || me->HasAura(SPELL_WY_TAKING_AIM) || me->isMoving())
            return;
        _shootMs = kShootEveryMs;
        if (Unit* target = SelectTarget(SelectTargetMethod::Random, 0, 100.f, true))
            DoCast(target, SPELL_WY_SHOOT);
    }

private:
    uint32 _shootMs = 0;
};

namespace
{
    boss_cannon_master_willey_rework* FindWilleyAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_WILLEY);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_cannon_master_willey_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Willey is not running boss_cannon_master_willey_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_cannon_master_willey_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_cannon_master_willey_rework* ai = FindWilleyAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        std::string const error = ai->TestFire(mechanic, isHeroic, gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Willey: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_WILLEY, BOSS_WILLEY);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_cannon_master_willey_rework* ai = FindWilleyAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Willey: {}", ai->TestState());
        return true;
    }

    bool HandleRank(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Rank, heroic,
            "a rank (WY1; 3 riflemen, heroic 4, past the cap too)");
    }

    bool HandleAim(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Aim, heroic,
            "Aim on every rank (WY2; Fire follows 3 s later, heroic 2 s)");
    }

    bool HandleMercy(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Mercy, heroic,
            "Cannon Fire down Mercy's half (WY8, the east half)");
    }

    bool HandleZeal(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Zeal, heroic,
            "Cannon Fire down Zeal's half (WY8, the west half)");
    }

    bool HandleBarrage(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Barrage, heroic,
            "the Barrage (WY9: the call, then five hidden blasts)");
    }

    bool HandleLoad(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_cannon_master_willey_rework::TestMechanic::Load, heroic,
            "a loaded gun's shot at him (WY6 / WY7: the gun nearer to you)");
    }

    // `.dbtest strat willey ball`: a Scarlet Cannonball at your feet (WY4; `.gm off` to pick it up).
    bool HandleBall(ChatHandler* handler)
    {
        boss_cannon_master_willey_rework* ai = FindWilleyAI(handler);
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!ai || !gm)
            return false;
        ai->TestBall(gm->GetPosition());
        handler->PSendSysMessage("Willey: a Scarlet Cannonball lies at your feet for 20 s (WY4; `.gm off` to take "
            "it).");
        return true;
    }

    // `.dbtest strat willey <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& WilleyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "rank",    HandleRank,    SEC_GAMEMASTER, Console::No },
            { "aim",     HandleAim,     SEC_GAMEMASTER, Console::No },
            { "mercy",   HandleMercy,   SEC_GAMEMASTER, Console::No },
            { "zeal",    HandleZeal,    SEC_GAMEMASTER, Console::No },
            { "barrage", HandleBarrage, SEC_GAMEMASTER, Console::No },
            { "load",    HandleLoad,    SEC_GAMEMASTER, Console::No },
            { "ball",    HandleBall,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// The glow stalker (300610) under each gun: carries the glow aura and nothing else; Willey despawns it.
struct npc_st_willey_glow : public NullCreatureAI
{
    explicit npc_st_willey_glow(Creature* creature) : NullCreatureAI(creature) { }
};

void AddSC_boss_cannon_master_willey_rework()
{
    RegisterDungeonReworkCreatureAI(boss_cannon_master_willey_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_crimson_rifleman, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_willey_glow, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("willey", WilleyTestCommands());
}
