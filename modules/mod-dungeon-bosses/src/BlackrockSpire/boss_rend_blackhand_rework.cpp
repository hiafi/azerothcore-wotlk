/*
 * mod-dungeon-bosses, Blackrock Spire B12: Warchief Rend Blackhand (10429) and the arena show, normal and heroic. One
 * encounter with Gyth (boss_gyth_rework.cpp; RendGythFight.h is how the two AIs talk). Build spec SP "Warchief Rend
 * Blackhand and Gyth" (theme A "Let the Games Begin", rulings 59-61, the tank swap at 10, rulings 63-64), handoff
 * section 3.4 rows RG, section 3.5 row B12, section 3.8 (NM 11), section 10 (the rolling front ruling 3).
 * Replaces the stock boss_rend_blackhand (still registered, unbound by apps/dbc-tools
 * source/npcs/blackrock_spire/rend_gyth.py): the six summon groups and their wave timer, the 25% dismount and the dead
 * Frenzy / Knockdown are gone. Lord Victor Nefarius gets a Blackrock Spire copy (300732; spawn 137967 rebound by
 * the SQL rev, Blackwing Lair's 10162 untouched) with the small AI below (npc_brs_lord_victor_nefarius).
 *
 * The show (Rend's AI runs it on its own clock, out of combat until act 3; the stock area trigger 2026 starts it
 * through SetData(1, 2026), as stock):
 *   RG1  Act 1, the Beasts  Nefarius line 0 on the trigger; 3 s later line 1 and group 1 through the drake portcullis
 *                           (the 4 static adds behind it join; whatever is missing is summoned: 1 Dragonspawn, 1
 *                           Handler, 2 / 3 whelps), group 2 15 s later. Act 2 30 s after group 1, whatever is left.
 *   RG2  Act 2, the Drake   Nefarius line 8, Rend line 1; Gyth comes in with Rend in the saddle (Rend leaves the
 *                           balcony unseen: invisible and unattackable until act 3). Gyth is the fight.
 *   RG3  Act 3, the         on Gyth's death (Rend's emote 2) or 75 s / heroic 60 s into act 2 (Nefarius line 7; Gyth
 *        Warchief           stays, riderless: the failing path is harder): Rend leaps down beside Gyth at full health
 *                           and fights on the floor. His death: Nefarius line 10, the exit door opens (door data), the
 *                           copy leaves. A wipe: everything goes, the instance respawns him on the balcony (FAIL, as
 *                           stock) and Nefarius says line 11; the trigger can start the show again.
 *   RG4  The Rounds         10 s into act 2, then every 30 s (heroic 10 s; each round lasts 15 s): RG5, RG6, RG7 (and
 *                           RG8 on heroic) in that order, around again. The bored host in act 3: normal past 1:30 every
 *                           20 s (line 5), past 2:30 two rounds per call (line 4); heroic past 1:15 every 7 s,
 *                           past 2:00 every 5 s. Nefarius wears the step as an aura.
 *   RG5  Dress Hunt         line 2, boss emote 14 per target: 3 / 6 whelps (heroic 4 / 8) through the portcullis, each
 *                           running at a healer (split over the healers; none: the player with the least armor) at
 *                           8 yd/s, taunt immune, slowed / rooted / stunned as usual (the kit's Chaser), biting 3% (5%)
 *                           a second once there; gone when the round ends (15 s). Heroic while Gyth lives: a Handler
 *                           with them (Mend Dragon on Gyth, SmartAI).
 *   RG6  Freezing Sweep     line 6 (Gyth dead: Nefarius breathes it, line 12), boss emote 15: a wall of frost 4 yd
 *                           thick across the arena from the portcullis to the way-in door at 8 yd/s, 3 s after the
 *                           call, one 8 yd gap in the 40 yd main strip off the live pools (KT-B2's FrontDirector);
 *                           heroic a second wall 3 s later, its gap on the other side within 20 yd of the first
 *                           (ruling 3). 25%, Weakened, Frozen 2 s. Gyth hovers over the portcullis end meanwhile.
 *   RG7  Taste in my power  line 9, boss emote 16: a 6 yd circle under everyone (Spread) for 3 s, 30% and Weakened to
 *                           anyone in someone else's; a pool where each player stood (20 s, heroic 25 s): 30% on
 *                           entering and every 2 s inside (no Weakened; the kit's PuddleField).
 *   RG8  Thumbs Down (H)    line 13, boss emote 17: the non-victim with the lowest health (2 at 6 or more) gets a
 *                           skull; 5 s later a Shadow Crash: 150% of the reference row split evenly among everyone
 *                           within 8 yd of them (a registry Stack), the tank included; a lone player takes it all.
 *   RG9  Rend's Mark        act 2, 5 s after Gyth engages, every 15 s: Rend's emote 3 points at a non-tank; 4 s later
 *                           Gyth breathes a 60 degree, 20 yd cone at them (aimed live): the marked player is hit
 *                           unless 20 yd from Gyth (a RunOut from the owner), anyone else in the cone too. 40%,
 *                           Weakened. Ends when Rend leaves the saddle.
 *   RG11 Whirlwind          act 3, 15 s after landing, every 20 s: a 2 s wind-up, then 6 s of an 8 yd circle moving
 *                           with him, 10% a second to everyone inside, the tank too.
 *   RG12 Banner             act 3, 10 s after landing, every 30 s (at most 3 alive): he plants the Banner of the Dark
 *                           Horde at his feet (emote 4): +25% damage while he stands within 10 yd of a live one. Kill
 *                           priority; a tank-only 10 yd circle on it moves the bot tank (and him) off it.
 *   RG13 Handlers           act 1 groups; heroic, one with each Dress Hunt while Gyth lives.
 *   RG14 Tank kit           stock Mortal Strike 16856 and Cleave 15284.
 *   RG17 Mortal Wounds      10 players only: Mortal Strike every 8 s from 5 s after landing adds a stack (-10% healing
 *                           taken, 15 s); the bots' taunt swap at 3 (heroic: the tanks trade Gyth and Rend). His
 *                           target's stacks hold while he cannot strike it (a wind-up, the whirl, out of reach).
 *   Leash                   RendGythArena() with LeashOptions (no grips) once he is on the floor; before that a wipe is
 *                           nobody alive on the arena floor for 3 s, or Gyth evading.
 *
 * The descriptor (kill order, the taunt swaps at 10) lives on the Nefarius copy's encounter, the one unit present from
 * the trigger to the end; every add, Gyth and Rend are tracked into it. Mechanics are owned by a boss that fights the
 * group (BM keeps a shape's room bounds for a bot only while its owner fights that bot): the rounds by Gyth while he
 * fights, else by Rend on the floor (Nefarius only in the seconds when neither fights; he still speaks, breathes the
 * looks and burns the pools); the Mark and the riderless breath by Gyth; Whirlwind and the banner circles by Rend.
 * Nefarius never fights: his AI drops any combat his hits start (once a second) and never evades. Every firing logs one
 * INFO line "brs rend <mechanic> ..." (module.dungeonbosses); `.dbtest brs rend <mechanic>` fires one.
 *
 * B15 (Drakkisath's hard mode) reads the insult: a player targeting the copy and using /rude, /insult, /spit or
 * /chicken (TEXT_EMOTE 77, 113, 89, 22) within 40 yd while it is present: instance SetData(DATA_NEF_INSULTED, 1)
 * (saved; the instance refuses it while Drakkisath fights or is dead), Nefarius line 18; later insults line 19.
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
#include "DungeonKitFlex.h"
#include "DungeonKitFronts.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "RendGythFight.h"
#include "RendGythLogic.h"
#include "ScriptedCreature.h"
#include "SharedDefines.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <functional>
#include <list>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsRendGyth;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "rend";

    // Registry tags (bookkeeping, per encounter). 6 is the wall (RF's drill tag for a line front).
    enum RendTags : uint32
    {
        TAG_RG_MARK         = 1,
        TAG_RG_MARK_CONE    = 2,
        TAG_RG_SHADOWFLAME  = 3,
        TAG_RG_POOL         = 4,
        TAG_RG_THUMBS       = 5,
        TAG_RG_SWEEP        = 6,
        TAG_RG_WHIRL        = 7,
        TAG_RG_BANNER       = 8,
    };

    float constexpr kPortcullisSearchYd = 80.f;
    float constexpr kNefariusSearchYd = 15.f;
    uint32 constexpr kBannerZoneMs = 30 * 60 * 1000;    // a banner's tank-only circle: until it dies (cancelled then)
    uint32 constexpr kLeapEngageMs = 1500;              // the leap's flight before he takes a target
    uint32 constexpr kNefLeaveMs = 10000;               // Nefarius leaves this long after line 10
    uint32 constexpr kNefCombatPollMs = 1000;
    uint32 constexpr kTextEmotes[] = { TEXT_EMOTE_RUDE, TEXT_EMOTE_INSULT, TEXT_EMOTE_SPIT, TEXT_EMOTE_CHICKEN };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A living player of the map who is not a game master.
    bool FightCandidate(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    BossMechanics::SpotBounds RoomBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (auto const& box : { kWestBay, kMainStrip, kEastBay })
        {
            std::vector<Position> points;
            for (Vec2 const& p : box)
                points.emplace_back(p.x, p.y, kFloorZ, 0.f);
            bounds.Polygon(std::move(points), kRoomZMin, kRoomZMax);
        }
        return bounds;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Lord Victor Nefarius, Blackrock Spire copy (300732): the host on his balcony. Never fights; the insult for B15.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brs_lord_victor_nefarius : public ScriptedAI
{
    explicit npc_brs_lord_victor_nefarius(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // His hits (the rounds) put players in combat with him: he drops it and never evades (an evade would end the
    // encounter that holds the show's descriptor).
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->CombatStop(true);
    }

    // DR10 (B15's hard mode trigger, on this copy by SP): /rude, /insult, /spit, /chicken.
    void ReceiveEmote(Player* player, uint32 emote) override
    {
        if (std::find(std::begin(kTextEmotes), std::end(kTextEmotes), emote) == std::end(kTextEmotes))
            return;
        Insult(player);
    }

    void Insult(Player* player)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!player || !player->IsAlive() || !instance || _leaving || !me->IsAlive())
            return;
        if (player->GetDistance(me) > kInsultRangeYd)
            return;
        if (instance->GetData(DATA_NEF_INSULTED))
        {
            Talk(SAY_NEF_INSULTED_AGAIN, player);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "insult-again", player->GetName());
            return;
        }
        instance->SetData(DATA_NEF_INSULTED, 1);
        if (!instance->GetData(DATA_NEF_INSULTED))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "insult-refused", player->GetName());
            return;
        }
        Talk(YELL_NEF_INSULTED, player);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "insult", player->GetName());
    }

    // RG3: Rend is dead; the host leaves (the instance keeps him gone on a reload: OnCreatureCreate).
    void Leave()
    {
        if (_leaving)
            return;
        _leaving = true;
        me->DespawnOrUnsummon(Ms(kNefLeaveMs), Seconds(7 * DAY));
    }

    void UpdateAI(uint32 diff) override
    {
        _pollMs = _pollMs > diff ? _pollMs - diff : 0;
        if (_pollMs)
            return;
        _pollMs = kNefCombatPollMs;
        if (me->IsInCombat())
            me->CombatStop(true);
    }

private:
    uint32 _pollMs = 0;
    bool _leaving = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// RG5: a Dress Hunt whelp (10442, summoned for the round; its SmartAI is swapped for this one on summon: no bolts, it
// runs at its target and bites).
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brs_dress_hunt_whelp : public ScriptedAI
{
    explicit npc_brs_dress_hunt_whelp(Creature* creature) : ScriptedAI(creature) { }

    void Start(Unit* target, bool heroic)
    {
        _heroic = heroic;
        me->CastSpell(me, SPELL_RG_HUNTING, true);
        DungeonKit::ChaserSpec spec;
        spec.speed = kHuntSpeed;
        spec.reach = kHuntReach;
        spec.life = Ms(kRoundMs);
        spec.endOnArrive = false;
        spec.pick.nonTank = true;
        spec.pick.tankIfAlone = true;
        spec.onEnd = [](Creature* whelp, DungeonKit::ChaseEnd)
        {
            whelp->DespawnOrUnsummon();
        };
        _biteMs = kBiteEveryMs;
        if (!_chase.Start(me, target, spec))
            me->DespawnOrUnsummon();
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }

    void JustDied(Unit* /*killer*/) override
    {
        _chase.Stop(me);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_chase.Active())
            return;
        _chase.Update(me, diff);
        if (!_chase.Active() || !me->IsAlive())
            return;
        _biteMs = _biteMs > diff ? _biteMs - diff : 0;
        if (_biteMs)
            return;
        _biteMs = kBiteEveryMs;
        Unit* target = ObjectAccessor::GetUnit(*me, _chase.Target());
        if (!target || !target->IsAlive() || _chase.Holding() || me->HasUnitState(UNIT_STATE_STUNNED)
            || me->GetExactDist2d(target) > kHuntReach + me->GetCombatReach())
            return;
        me->SetFacingToObject(target);
        me->CastSpell(target, _heroic ? SPELL_RG_WHELP_BITE_H : SPELL_RG_WHELP_BITE, true);
    }

private:
    DungeonKit::Chaser _chase;
    uint32 _biteMs = 0;
    bool _heroic = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// RG12: the Banner of the Dark Horde (300733): rooted, attackable, no attacks.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brs_banner_of_the_dark_horde : public ScriptedAI
{
    explicit npc_brs_banner_of_the_dark_horde(Creature* creature) : ScriptedAI(creature)
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void AttackStart(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// RG6: the frost wall carrier (300734): the ice wall's look, moved along the band by the kit's FrontDirector.
struct npc_brs_frost_wall : public NullCreatureAI
{
    explicit npc_brs_frost_wall(Creature* creature) : NullCreatureAI(creature) { }
};

// ---------------------------------------------------------------------------------------------------------------------
// Warchief Rend Blackhand (10429): the show's runner and, from act 3, the boss on the floor.
// ---------------------------------------------------------------------------------------------------------------------
struct boss_rend_blackhand_rework : public BossAI, public RendShow
{
    explicit boss_rend_blackhand_rework(Creature* creature)
        : BossAI(creature, BOSS_REND), _arena(RendGythArena(), LeashOptions(kBossLogName)),
          _pools(Milliseconds(DungeonKit::PuddleField::kPollMs)) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
        GoIdle();
    }

    // at_blackrock_stadium (stock, kept): SetData(1, 2026) starts the show while Rend waits.
    void SetData(uint32 type, uint32 data) override
    {
        if (type == DATA_AREATRIGGER && data == kAreaTriggerBlackrockStadium)
            StartShow("area trigger 2026");
    }

    void JustSummoned(Creature* summon) override
    {
        // The frost wall carriers of a Sweep he owns (R-2 M-2: the kit's FrontDirector summons them through the
        // owner): never tracked or put in combat; they despawn on their own timer.
        if (summon && summon->GetEntry() == NPC_BRS_FROST_WALL)
            return;
        summons.Summon(summon);
        // Into the show's encounter (the descriptor's units); Gyth once he engages (he walks in immune).
        if (Creature* nef = Nefarius())
            if (summon->GetEntry() != NPC_GYTH)
                Mechanic::TrackUnit(nef, summon);
        switch (summon->GetEntry())
        {
            case NPC_GYTH:
                if (auto* drake = DrakeOf(summon))
                    drake->JoinShow(me->GetGUID(), _players);
                break;
            case NPC_CHROMATIC_WHELP:
            case NPC_CHROMATIC_DRAGONSPAWN:
            case NPC_BLACKHAND_DRAGON_HANDLER:
                if (!_quietSummon)
                    DoZoneInCombat(summon, 150.f);
                break;
            case NPC_BRS_BANNER:
                DoZoneInCombat(summon, 150.f);
                break;
            default:
                break;
        }
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_REND;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _engaged = true;
        _now = 0;
        bool const swap = DungeonKit::Flex::TankSwapOn(_players);
        _nextWhirlAt = kWhirlFirstMs;
        _nextBannerAt = kBannerFirstMs;
        _nextCleaveAt = urand(kCleaveFirstMinMs, kCleaveFirstMaxMs);
        _nextStrikeAt = swap ? kWoundsFirstMs : urand(kStrikeFirstMinMs, kStrikeFirstMaxMs);
        Log("engage", Acore::StringFormat("players={} heroic={} tankswap={} gyth={}", _players, _heroic ? 1 : 0,
            swap ? 1 : 0, GythAlive() ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_act != Act::Idle && _act != Act::Over)
        {
            Wipe(Acore::StringFormat("rend evaded ({})", uint32(why)).c_str());
            return;     // the instance respawned him (FAIL): nothing of this attempt is left to reset
        }
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        if (Creature* nef = Nefarius())
        {
            nef->AI()->Talk(YELL_NEF_SHORT_LIVED);
            if (auto* host = dynamic_cast<npc_brs_lord_victor_nefarius*>(nef->AI()))
                host->Leave();
        }
        // Gyth on the failing path outlives him: he stays (his own slot, his loot) and takes his own descriptor (the
        // show's goes with Nefarius's encounter: R-2 m-1); every other summon goes. The entry door opens with the DONE
        // (the instance, R-2 B-1).
        if (Creature* gyth = Gyth())
            if (gyth->IsAlive())
            {
                summons.Despawn(gyth);
                if (GythDrake* drake = DrakeOf(gyth))
                    drake->RendFell();
            }
        Log("death", Acore::StringFormat("show={}ms gyth-alive={}", _showMs, GythAlive() ? 1 : 0));
        _act = Act::Over;
        Cleanup(true);
        BossAI::JustDied(killer);
    }

    // RG12: within 10 yd of a live banner his hits are 25% harder. His own kit is all Physical (melee, Mortal Strike,
    // Cleave, Whirlwind); the rounds he owns once Gyth is down (Frost, Shadow: R-2 M-2) are Nefarius's and never grow.
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask mask) override
    {
        if (!victim || !damage || !(mask & SPELL_SCHOOL_MASK_NORMAL))
            return;
        damage = BannerDamage(damage, _empowered);
    }

    void UpdateAI(uint32 diff) override
    {
        if (_act == Act::Idle || _act == Act::Over)
        {
            // Out of the show: a GM's banner test still ticks nothing; Rend just waits.
            return;
        }
        RunShow(diff);
        if (_act != Act::Warchief || !me->IsAlive())
            return;
        if (_engageAt && _showMs >= _engageAt)
        {
            _engageAt = 0;
            DoZoneInCombat();
        }
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;
        _now += diff;
        RendKit(diff);
    }

    // ---- RendShow (Gyth's view of the show, RendGythFight.h) --------------------------------------------------------

    void OnGythEngaged(Creature* gyth) override
    {
        if (_act != Act::Drake || !gyth)
            return;
        _nextMarkAt = _showMs + kMarkFirstMs;
        if (Creature* nef = Nefarius())
            Mechanic::TrackUnit(nef, gyth);
        Log("gyth-engaged");
    }

    void OnGythDied(Creature* gyth) override
    {
        _gythDied = true;
        if (gyth)
            _gythDiedAt = gyth->GetPosition();
    }

    void OnGythEvaded(Creature* /*gyth*/) override
    {
        _gythEvaded = true;
    }

    uint8 ShowPlayers() const override
    {
        return _players;
    }

    ObjectGuid RendGuid() const override
    {
        return me->GetGUID();
    }

    // ---- `.dbtest brs rend` entry points ----------------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    std::string TestStart()
    {
        if (_act != Act::Idle)
            return "the show is already running";
        StartShow("gm test");
        return _act == Act::Idle ? "refused (Rend's boss state is not NOT_STARTED, or no Nefarius copy)" : "";
    }

    std::string TestAct(Act act)
    {
        if (_act == Act::Idle || _act == Act::Over)
            return "start the show first (`.dbtest brs rend start`)";
        if (act == Act::Drake && _act == Act::Beasts)
            StartDrake();
        else if (act == Act::Warchief && _act == Act::Drake)
            StartWarchief(false);
        else
            return "not from this act";
        return "";
    }

    std::string TestRound(Round r)
    {
        if (_act == Act::Idle || _act == Act::Over)
            return "start the show first (`.dbtest brs rend start`): the rounds run on its clock";
        if (!Nefarius())
            return "no Nefarius copy (300732) near Rend";
        RunRound(r);
        return "";
    }

    std::string TestMark()
    {
        Creature* gyth = Gyth();
        if (!gyth || !gyth->IsAlive())
            return "no Gyth (act 2)";
        Mark();
        return "";
    }

    std::string TestRendKit(bool whirl)
    {
        if (_act != Act::Warchief || !_engaged)
            return "Rend is not on the floor (act 3)";
        if (whirl)
            Whirlwind();
        else
            PlantBanner();
        return "";
    }

    void TestWipe()
    {
        if (_act != Act::Idle && _act != Act::Over)
            Wipe("gm test");
    }

    std::string TestState()
    {
        Creature* gyth = Gyth();
        std::string out = Acore::StringFormat("act={} show={}ms heroic={} players={} tankswap={} rounds={} next call="
            "{}ms bored={} gyth={} nefarius={} pools={} banners={} fronts={} empowered={} "
            "next mark/whirl/banner/strike={}/{}/{}/{}", ActName(_act), _showMs, _heroic ? 1 : 0, _players,
            DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0, _roundIndex, _nextCallAt, _bored,
            gyth ? (gyth->IsAlive() ? "alive" : "dead") : "none", Nefarius() ? 1 : 0, _pools.Count(),
            LiveBanners().size(), _fronts.Active() ? 1 : 0, _empowered ? 1 : 0, _nextMarkAt, _nextWhirlAt,
            _nextBannerAt, _nextStrikeAt);
        if (Unit* victim = me->GetVictim())
            out += Acore::StringFormat("\n  victim {} mortal wounds {}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_RG_MORTAL_WOUNDS, me->GetGUID()));
        return out;
    }

private:
    // ---- lookups ----------------------------------------------------------------------------------------------------

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    Creature* Nefarius()
    {
        if (!_nef.IsEmpty())
            if (Creature* nef = ObjectAccessor::GetCreature(*me, _nef))
                if (nef->IsAlive())
                    return nef;
        Creature* nef = me->FindNearestCreature(NPC_BRS_NEFARIUS, kNefariusSearchYd, true);
        _nef = nef ? nef->GetGUID() : ObjectGuid::Empty;
        return nef;
    }

    Creature* Gyth() const
    {
        return _gyth.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _gyth);
    }

    bool GythAlive() const
    {
        Creature* gyth = Gyth();
        return gyth && gyth->IsAlive();
    }

    static GythDrake* DrakeOf(Creature* gyth)
    {
        return (gyth && gyth->IsAIEnabled) ? dynamic_cast<GythDrake*>(gyth->AI()) : nullptr;
    }

    // The rounds' registry owner (R-2 M-2, RendGythLogic.h RoundOwnerFor): a boss that fights the group, so BM keeps
    // the shapes' room bounds for the bots; Nefarius only in the few seconds when neither fights.
    Unit* RoundOwnerUnit(Creature* nef)
    {
        Creature* gyth = Gyth();
        GythDrake* drake = (gyth && gyth->IsAlive()) ? DrakeOf(gyth) : nullptr;
        bool const rendFighting = _act == Act::Warchief && _engaged && me->IsAlive() && me->IsInCombat();
        switch (RoundOwnerFor(drake && drake->Fighting(), rendFighting))
        {
            case RoundOwner::Gyth:
                return gyth;
            case RoundOwner::Rend:
                return me;
            default:
                return nef;
        }
    }

    // The players of the show: alive, not a GM, on the arena floor.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (FightCandidate(player) && _arena.Contains(player))
                out.push_back(player);
        }
        return out;
    }

    // The bosses' current victims (Gyth's and Rend's): the tanks of the moment.
    GuidSet Victims() const
    {
        GuidSet out;
        if (Creature* gyth = Gyth())
            if (gyth->IsAlive() && gyth->GetVictim())
                out.insert(gyth->GetVictim()->GetGUID());
        if (_engaged && me->GetVictim())
            out.insert(me->GetVictim()->GetGUID());
        return out;
    }

    // A resolve callback that finds his AI again (never a captured `this`: the registry may outlive it).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnRend(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* rend = map->GetCreature(guid);
            if (!rend || !rend->IsAlive() || !rend->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_rend_blackhand_rework*>(rend->AI()))
                fn(*ai, result);
        };
    }

    // ---- idle, start, the acts --------------------------------------------------------------------------------------

    // On his balcony between attempts: seen, not attackable (stock).
    void GoIdle()
    {
        _act = Act::Idle;
        me->SetVisible(true);
        me->SetImmuneToAll(true);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetReactState(REACT_PASSIVE);
        if (instance && instance->GetBossState(BOSS_REND) != DONE)
            instance->HandleGameObject(instance->GetGuidData(GO_GYTH_ENTRY_DOOR), true);
    }

    void StartShow(char const* why)
    {
        if (_act != Act::Idle || !me->IsAlive() || !instance || instance->GetBossState(BOSS_REND) != NOT_STARTED)
            return;
        Creature* nef = Nefarius();
        if (!nef)
        {
            LOG_ERROR("module", "brs rend: no Nefarius copy (300732) within {} yd: the show cannot start",
                kNefariusSearchYd);
            return;
        }
        Cleanup(false);
        _heroic = DungeonKit::IsHeroicMap(me);
        _players = DungeonKit::Flex::Count(me);     // a preview: Gyth and Rend hold their own at their pulls
        instance->SetBossState(BOSS_REND, IN_PROGRESS);
        instance->SetData(DATA_VAELASTRASZ, NOT_STARTED);
        if (instance->GetBossState(BOSS_GYTH) != NOT_STARTED)
            instance->SetBossState(BOSS_GYTH, NOT_STARTED);
        instance->HandleGameObject(instance->GetGuidData(GO_GYTH_ENTRY_DOOR), false);
        if (GameObject* portcullis = me->FindNearestGameObject(GO_GYTH_COMBAT_DOOR, kPortcullisSearchYd))
            _portcullis = portcullis->GetGUID();

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_REND;
        Mechanic::BeginEncounter(nef, options);
        Describe();

        _act = Act::Beasts;
        _showMs = 0;
        _actStartMs = 0;
        _groupOneAt = kGroupOneDelayMs;
        _groupTwoAt = kGroupOneDelayMs + kGroupTwoMs;
        _actTwoAt = kGroupOneDelayMs + kActTwoMs;
        _wipeMs = 0;
        _pollMs = 0;
        nef->AI()->Talk(YELL_NEF_WELCOME);
        Log("show-start", Acore::StringFormat("why={} heroic={} players={} tankswap={}", why, _heroic ? 1 : 0,
            _players, DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0));
    }

    // Boss data on the Nefarius copy's encounter (build spec "Boss data"): act 1 Handlers, whelps, Dragonspawn; act 2
    // the hunting whelps, then Handlers, then Gyth; act 3 the hunting whelps, banners, then Rend (Gyth by the group's
    // call). Nefarius is never a target. At 10: the taunt swaps at 3 Corrosive Acid (Gyth) and 3 Mortal Wounds (Rend);
    // heroic two at once, the tanks trade (the BM rules).
    void Describe()
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_CHROMATIC_WHELP, 6, BossMechanics::Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_RG_HUNTING)));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BLACKHAND_DRAGON_HANDLER, 5));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_BANNER, 4));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_CHROMATIC_WHELP, 3));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_CHROMATIC_DRAGONSPAWN, 2));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_GYTH, 1));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_REND, 1));
        d.ignores.emplace_back(NPC_BRS_NEFARIUS);
        d.ignores.emplace_back(NPC_LORD_VICTOR_NEFARIUS);
        if (DungeonKit::Flex::TankSwapOn(_players))
        {
            d.tauntSwaps.emplace_back(NPC_GYTH, SPELL_RG_CORROSIVE_ACID, kSwapAt);
            d.tauntSwaps.emplace_back(NPC_REND, SPELL_RG_MORTAL_WOUNDS, kSwapAt);
        }
        Mechanic::Describe(nef, std::move(d));
    }

    void OpenPortcullis()
    {
        if (GameObject* go = _portcullis.IsEmpty() ? nullptr : ObjectAccessor::GetGameObject(*me, _portcullis))
            go->UseDoorOrButton(kPortcullisOpenS);
    }

    Creature* SummonAdd(uint32 entry, std::size_t spot)
    {
        Vec2 const p = kWaveSpots[spot % kWaveSpots.size()];
        return me->SummonCreature(entry, p.x, p.y, kWaveZ, DungeonKit::kPi, TEMPSUMMON_MANUAL_DESPAWN);
    }

    // RG1: group 1 takes in the static adds behind the portcullis; whatever of 1 Dragonspawn and 2 / 3 whelps is
    // missing is summoned, and a Handler always.
    void Group(bool first)
    {
        uint32 dragonspawn = 1;
        uint32 whelps = kGroupWhelps.At(_players);
        if (first)
        {
            Creature* nef = Nefarius();
            for (uint32 const entry : { static_cast<uint32>(NPC_CHROMATIC_WHELP),
                static_cast<uint32>(NPC_CHROMATIC_DRAGONSPAWN) })
            {
                std::list<Creature*> found;
                me->GetCreatureListWithEntryInGrid(found, entry, 120.f);
                for (Creature* c : found)
                {
                    if (!c->IsAlive() || c->IsSummon()
                        || c->GetExactDist2d(kWaveSpots[0].x, kWaveSpots[0].y) > kStaticSearchYd)
                        continue;
                    uint32& left = entry == NPC_CHROMATIC_WHELP ? whelps : dragonspawn;
                    left = left ? left - 1 : 0;
                    if (nef)
                        Mechanic::TrackUnit(nef, c);
                    DoZoneInCombat(c, 150.f);
                }
            }
            if (Creature* nefarius = Nefarius())
                nefarius->AI()->Talk(YELL_NEF_FEAST);
        }
        std::size_t spot = first ? 0 : 4;
        SummonAdd(NPC_BLACKHAND_DRAGON_HANDLER, spot++);
        for (uint32 i = 0; i < dragonspawn; ++i)
            SummonAdd(NPC_CHROMATIC_DRAGONSPAWN, spot++);
        for (uint32 i = 0; i < whelps; ++i)
            SummonAdd(NPC_CHROMATIC_WHELP, spot++);
        OpenPortcullis();
        Log(first ? "group-1" : "group-2", Acore::StringFormat("dragonspawn={} whelps={}", dragonspawn, whelps));
    }

    // RG2: Gyth comes in with Rend in the saddle; Rend leaves the balcony unseen.
    void StartDrake()
    {
        _act = Act::Drake;
        _actStartMs = _showMs;
        _nextCallAt = _showMs + kRoundsFirstMs;
        _roundIndex = 0;
        _nextMarkAt = 0;
        if (Creature* nef = Nefarius())
            nef->AI()->Talk(YELL_NEF_WARCHIEF);
        Talk(YELL_REND_PLEASURE);
        Creature* gyth = me->SummonCreature(NPC_GYTH, kGythSummon.x, kGythSummon.y, kGythSummon.z, 4.747295f,
            TEMPSUMMON_MANUAL_DESPAWN);
        _gyth = gyth ? gyth->GetGUID() : ObjectGuid::Empty;
        OpenPortcullis();
        me->SetVisible(false);
        Log("act-2", Acore::StringFormat("gyth={}", gyth ? 1 : 0));
        if (!gyth)
            StartWarchief(false);
    }

    // RG3: Rend leaps down beside Gyth (or where he fell); on the timer Gyth stays, riderless.
    void StartWarchief(bool gythDied)
    {
        if (_act != Act::Drake)
            return;
        _act = Act::Warchief;
        _actStartMs = _showMs;
        _nextMarkAt = 0;
        Creature* gyth = Gyth();
        Position from = _gythDiedAt;
        if (gythDied)
            Talk(EMOTE_REND_KNOCKED_OFF);
        else
        {
            if (Creature* nef = Nefarius())
                nef->AI()->Talk(YELL_NEF_CANNOT_BE);
            if (gyth && gyth->IsAlive())
            {
                from = gyth->GetPosition();
                if (auto* drake = DrakeOf(gyth))
                    drake->Dismount();
            }
        }
        if (from.GetPositionX() == 0.f && from.GetPositionY() == 0.f)
            from = DungeonKit::ToPosition(kRendLanding, kFloorZ);
        // From the drake's back, 6 yd toward the arena's middle.
        Vec2 const at{ from.GetPositionX(), from.GetPositionY() };
        Vec2 const mid{ kRendLanding.x - 20.f, kRendLanding.y };
        Vec2 land = DungeonKit::Distance(at, mid) > kRendLeapYd
            ? Vec2{ at.x + (mid.x - at.x) * kRendLeapYd / DungeonKit::Distance(at, mid),
                at.y + (mid.y - at.y) * kRendLeapYd / DungeonKit::Distance(at, mid) }
            : mid;
        if (!InRoom(land))
            land = kRendLanding;
        me->NearTeleportTo(at.x, at.y, from.GetPositionZ() + 3.f, DungeonKit::BearingTo(at, land));
        me->SetVisible(true);
        me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetImmuneToAll(false);
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetHomePosition(DungeonKit::ToPosition(land, kFloorZ, DungeonKit::BearingTo(at, land)));
        DungeonKit::JumpTo(me, DungeonKit::ToPosition(land, kFloorZ), 15.f, 8.f);
        _engageAt = _showMs + kLeapEngageMs;
        if (Creature* nef = Nefarius())
            Mechanic::TrackUnit(nef, me);   // a unit of the show's encounter once he can be fought
        Log("act-3", Acore::StringFormat("why={} gyth-alive={} at=({:.1f},{:.1f})", gythDied ? "gyth-died" : "timer",
            GythAlive() ? 1 : 0, land.x, land.y));
    }

    // ---- the show's clock -------------------------------------------------------------------------------------------

    void RunShow(uint32 diff)
    {
        _showMs += diff;

        if (_gythEvaded)
        {
            _gythEvaded = false;
            Wipe("gyth evaded");
            return;
        }
        if (_gythDied)
        {
            _gythDied = false;
            Log("gyth-died", Acore::StringFormat("act={}", ActName(_act)));
            if (_act == Act::Drake)
                StartWarchief(true);
        }
        if (WipeWatch(diff))
            return;

        if (Creature* nef = Nefarius())
        {
            _pools.Update(nef, diff, [this](Player* player, uint32 msInside) { PoolTick(player, msInside); });
            if (Unit* owner = FrontOwner())
                _fronts.Update(owner, diff);
        }
        PruneBurns();

        switch (_act)
        {
            case Act::Beasts:
                if (_groupOneAt && _showMs >= _groupOneAt)
                {
                    _groupOneAt = 0;
                    Group(true);
                }
                if (_groupTwoAt && _showMs >= _groupTwoAt)
                {
                    _groupTwoAt = 0;
                    Group(false);
                }
                if (_showMs >= _actTwoAt)
                    StartDrake();
                return;
            case Act::Drake:
                if (_showMs >= _actStartMs + ActTwoLengthMs(_heroic))
                    StartWarchief(false);
                else if (_nextMarkAt && _showMs >= _nextMarkAt)
                    Mark();
                break;
            default:
                break;
        }
        if (_act != Act::Drake && _act != Act::Warchief)
            return;
        Bored();
        if (_nextCallAt && _showMs >= _nextCallAt)
        {
            uint32 const n = RoundsPerCall(_heroic, _bored);
            for (uint32 i = 0; i < n; ++i)
                RunRound(RoundAt(_roundIndex++, _heroic));
            _nextCallAt = _showMs + CallEveryMs(_heroic, _bored);
        }
    }

    // RG15: nobody alive on the arena floor for kWipeGraceMs.
    bool WipeWatch(uint32 diff)
    {
        _pollMs = _pollMs > diff ? _pollMs - diff : 0;
        if (_pollMs)
            return false;
        _pollMs = kWipePollMs;
        if (!FightPlayers().empty())
        {
            _wipeMs = 0;
            return false;
        }
        _wipeMs += kWipePollMs;
        if (_wipeMs < kWipeGraceMs)
            return false;
        Wipe("nobody on the arena floor");
        return true;
    }

    // RG4: the bored host (act 3 only).
    void Bored()
    {
        if (_act != Act::Warchief)
            return;
        uint8 const step = BoredStep(_heroic, static_cast<uint32>(_showMs - _actStartMs));
        if (step <= _bored)
            return;
        _bored = step;
        if (Creature* nef = Nefarius())
        {
            nef->AI()->Talk(step >= 2 ? YELL_NEF_FRUITLESS : YELL_NEF_FORCE_MY_HAND);
            nef->CastSpell(nef, step >= 2 ? SPELL_RG_BORED_HOST : SPELL_RG_IMPATIENT_HOST, true);
        }
        Log("bored", Acore::StringFormat("step={} every={}ms per-call={}", step, CallEveryMs(_heroic, step),
            RoundsPerCall(_heroic, step)));
        // The faster cadence starts now.
        _nextCallAt = std::min<uint64>(_nextCallAt, _showMs + CallEveryMs(_heroic, step));
    }

    void RunRound(Round r)
    {
        Log("round", RoundName(r));
        switch (r)
        {
            case Round::DressHunt:
                DressHunt();
                break;
            case Round::FreezingSweep:
                FreezingSweep();
                break;
            case Round::Shadowflame:
                Shadowflame();
                break;
            case Round::ThumbsDown:
                if (_heroic)
                    ThumbsDown();
                break;
        }
    }

    // ---- RG5 Dress Hunt ---------------------------------------------------------------------------------------------

    void DressHunt()
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        std::vector<Player*> const players = FightPlayers();
        std::vector<uint64> healers;
        Player* leastArmor = nullptr;
        GuidSet const victims = Victims();
        Unit* roleOwner = GythAlive() ? static_cast<Unit*>(Gyth()) : static_cast<Unit*>(me);
        for (Player* p : players)
        {
            if (BossMechanics::GetRoleProvider().Get(roleOwner, p) == BossMechanics::Role::Healer)
                healers.push_back(p->GetGUID().GetRawValue());
            if (!victims.count(p->GetGUID()) && (!leastArmor || p->GetArmor() < leastArmor->GetArmor()))
                leastArmor = p;
        }
        uint32 const count = HuntWhelps(_heroic, _players);
        std::vector<uint64> const targets = HuntTargets(count, healers,
            leastArmor ? leastArmor->GetGUID().GetRawValue() : 0);
        nef->AI()->Talk(YELL_NEF_DRESS);
        GuidSet named;
        uint32 started = 0;
        std::size_t spot = 0;
        _quietSummon = true;
        for (uint64 raw : targets)
        {
            Player* target = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw));
            if (!target)
                continue;
            Creature* whelp = SummonAdd(NPC_CHROMATIC_WHELP, spot++);
            if (!whelp)
                continue;
            auto* hunt = new npc_brs_dress_hunt_whelp(whelp);
            if (!whelp->AIM_Initialize(hunt))
            {
                delete hunt;    // refused (the whelp's AI is locked): never installed (R-2 n-1)
                whelp->DespawnOrUnsummon();
                continue;
            }
            hunt->Start(target, _heroic);
            ++started;
            if (named.insert(target->GetGUID()).second)
                nef->AI()->Talk(EMOTE_NEF_HUNT, target);
        }
        _quietSummon = false;
        // RG13 heroic: a Handler with them while Gyth lives (it mends him; SmartAI).
        if (_heroic && GythAlive())
            SummonAdd(NPC_BLACKHAND_DRAGON_HANDLER, spot++);
        OpenPortcullis();
        Log("dress-hunt", Acore::StringFormat("whelps={} targets={} healers={} handler={}", started, named.size(),
            healers.size(), (_heroic && GythAlive()) ? 1 : 0));
    }

    // ---- RG6 Freezing Sweep -----------------------------------------------------------------------------------------

    Unit* FrontOwner()
    {
        if (_frontOwner.IsEmpty())
            return nullptr;
        return ObjectAccessor::GetUnit(*me, _frontOwner);
    }

    void FreezingSweep()
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        Creature* gyth = Gyth();
        GythDrake* drake = (gyth && gyth->IsAlive()) ? DrakeOf(gyth) : nullptr;
        // The breath and its look: Gyth while he lives, else Nefarius. The walls' owner: whoever fights the group.
        Unit* breather = drake ? static_cast<Unit*>(gyth) : static_cast<Unit*>(nef);
        Unit* owner = RoundOwnerUnit(nef);
        if (_fronts.Active() && owner->GetGUID() != _frontOwner)
        {
            // A wall of the other owner still rolls (Gyth fell mid-sweep): it goes (one owner per director).
            Unit* old = FrontOwner();
            _fronts.Clear(old ? old : me);
        }
        _frontOwner = owner->GetGUID();
        nef->AI()->Talk(drake ? YELL_NEF_FREEZING : YELL_NEF_MYSELF);
        nef->AI()->Talk(EMOTE_NEF_SWEEP);
        if (drake)
            drake->Hover(HoverMs(_heroic));     // refused while he walks in: the walls roll without him

        DungeonKit::WallSequence ws;
        ws.facing = DungeonKit::kPi;
        ws.travelYd = kSweepTravelYd;
        ws.widthYd = kSweepWidthYd;
        ws.bandYd = kSweepBandYd;
        ws.speed = kSweepSpeed;
        ws.walls = SweepWalls(_heroic);
        ws.firstWarnMs = kSweepWarnMs;
        ws.spacingMs = kSweepSpacingMs;
        ws.gaps.gapYd = kSweepGapYd;
        ws.gaps.spanYd = kSweepSpanYd;
        ws.gaps.withinYd = kSweepWithinYd;
        Map* map = me->GetMap();
        ObjectGuid const rendGuid = me->GetGUID();
        ws.pools = [map, rendGuid]()
        {
            Creature* rend = map ? map->GetCreature(rendGuid) : nullptr;
            auto* ai = (rend && rend->IsAIEnabled) ? dynamic_cast<boss_rend_blackhand_rework*>(rend->AI()) : nullptr;
            return ai ? DungeonKit::PoolsOf(ai->_pools) : std::vector<DungeonKit::Fronts::PoolCircle>{};
        };
        ws.decorate = [](MechanicRef& ref, uint32)
        {
            ref.Damage(kSweepPct).TankDamage(kSweepPct).School(SPELL_SCHOOL_FROST).Spell(SPELL_RG_FREEZING_SWEEP)
                .Weakened().Rider(SPELL_RG_FROZEN).Tag(TAG_RG_SWEEP);
        };
        ws.within = RoomBounds();
        ws.carriers.entry = NPC_BRS_FROST_WALL;
        ws.carriers.spacingYd = kSweepCarrierSpacingYd;
        ws.carriers.maxCount = kSweepCarrierMax;
        ObjectGuid const breatherGuid = breather->GetGUID();
        ws.onLaunch = [map, breatherGuid](uint32 index, Position const&)
        {
            Creature* who = map ? map->GetCreature(breatherGuid) : nullptr;
            if (!who || !who->IsAlive())
                return;
            if (auto* drake = DrakeOf(who))
                drake->BreatheWall();
            else
                who->CastSpell(who, SPELL_RG_FREEZING_BREATH, true);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sweep-wall", Acore::StringFormat("wall={}", index));
        };
        ws.dungeon = kLogDungeon;
        ws.boss = kBossLogName;
        uint32 const id = _fronts.StartWalls(owner, Position(kSweepStartX, kSweepStartY, kSweepStartZ), std::move(ws));
        std::string gaps;
        for (DungeonKit::Fronts::GapPick const& g : _fronts.Gaps(id))
            gaps += Acore::StringFormat(" {:.1f}{}", g.centre, g.offPools ? "" : "(pool)");
        Log("freezing-sweep", Acore::StringFormat("owner={} breath={} walls={} gaps:{}", owner == gyth ? "gyth"
            : owner == me ? "rend" : "nefarius", drake ? "gyth" : "nefarius", SweepWalls(_heroic), gaps));
    }

    // ---- RG7 Taste in my power --------------------------------------------------------------------------------------

    void Shadowflame()
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        nef->AI()->Talk(YELL_NEF_TASTE);
        nef->AI()->Talk(EMOTE_NEF_SHADOWFLAME);
        MechanicRef ref = Mechanic::Spread(RoundOwnerUnit(nef), kShadowflameRadius, Ms(kShadowflameWarnMs));
        ref.Damage(kShadowflamePct).TankDamage(kShadowflamePct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_RG_SHADOWFLAME)
            .Weakened().Within(RoomBounds()).Tag(TAG_RG_SHADOWFLAME);
        ref.OnResolve(OnRend([](boss_rend_blackhand_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.ShadowflameLanded(r.hits.size());
        }));
        Log("shadowflame");
    }

    // A pool under every player of the show.
    void ShadowflameLanded(std::size_t hits)
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        DungeonKit::PuddleSpec spec;
        spec.radius = kShadowflameRadius;
        spec.armAfter = Ms(kPoolArmMs);
        spec.life = Ms(PoolMs(_heroic));
        spec.tag = TAG_RG_POOL;
        uint32 const look = _heroic ? SPELL_RG_SHADOWFLAME_POOL_H : SPELL_RG_SHADOWFLAME_POOL;
        uint32 n = 0;
        for (Player* p : FightPlayers())
        {
            Position const at = p->GetPosition();
            if (_pools.Add(nef, at, spec).id)
            {
                ++n;
                nef->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), look, true);
            }
        }
        Log("shadowflame-landed", Acore::StringFormat("hits={} pools={}", hits, n));
    }

    // RG7: a pool burns on entering and every 2 s inside.
    void PoolTick(Player* player, uint32 msInside)
    {
        Creature* nef = Nefarius();
        if (!nef || !player)
            return;
        auto it = _burns.find(player->GetGUID());
        bool const burned = it != _burns.end();
        uint64 const since = burned ? _showMs - it->second : 0;
        bool const entering = msInside <= DungeonKit::PuddleField::kPollMs;
        bool const due = entering ? (!burned || since >= DungeonKit::PuddleField::kPollMs) : PoolBurnDue(burned, since);
        if (!due)
            return;
        _burns[player->GetGUID()] = _showMs;
        nef->CastSpell(player, SPELL_RG_SHADOWFLAME_BURN, true);
    }

    // Players out of every pool start fresh.
    void PruneBurns()
    {
        if (_burns.empty())
            return;
        std::erase_if(_burns, [this](auto const& kv)
        {
            return _showMs - kv.second >= 2 * kPoolTickMs;
        });
    }

    // ---- RG8 Thumbs Down (heroic) -----------------------------------------------------------------------------------

    void ThumbsDown()
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        GuidSet const victims = Victims();
        std::vector<CondemnCandidate> candidates;
        for (Player* p : FightPlayers())
            candidates.push_back({ p->GetGUID().GetRawValue(), p->GetHealthPct(), p->GetHealth(),
                victims.count(p->GetGUID()) != 0, DungeonKit::PlaneOf(p) });
        std::vector<uint64> const condemned = PickCondemned(candidates, kCondemned.At(_players));
        if (condemned.empty())
            return;
        nef->AI()->Talk(YELL_NEF_BORES_ME);
        for (uint64 raw : condemned)
        {
            Player* target = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw));
            if (!target)
                continue;
            nef->AI()->Talk(EMOTE_NEF_THUMBS_DOWN, target);
            nef->CastSpell(target, SPELL_RG_THUMBS_DOWN, true);
            MechanicRef ref = Mechanic::Stack(RoundOwnerUnit(nef), target, kThumbsRadius, Ms(kThumbsWarnMs));
            ref.Within(RoomBounds()).Tag(TAG_RG_THUMBS);
            ObjectGuid const guid = target->GetGUID();
            ref.OnResolve(OnRend([guid](boss_rend_blackhand_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.ShadowCrash(guid, r.hits);
            }));
            Log("thumbs-down", target->GetName());
        }
    }

    // 150% of the reference row split evenly among everyone within 8 yd of the condemned (the registry's Stack hits).
    void ShadowCrash(ObjectGuid condemned, std::vector<ObjectGuid> const& inside)
    {
        Creature* nef = Nefarius();
        if (!nef)
            return;
        std::vector<Unit*> takers;
        for (ObjectGuid const& g : inside)
            if (Player* p = ObjectAccessor::GetPlayer(*me, g))
                if (p->IsAlive())
                    takers.push_back(p);
        if (takers.empty())
            if (Player* p = ObjectAccessor::GetPlayer(*me, condemned))
                if (p->IsAlive())
                    takers.push_back(p);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(nef, takers,
            kThumbsTotalPct);
        for (auto const& [guid, amount] : shares)
            if (Player* p = ObjectAccessor::GetPlayer(*me, guid))
                nef->CastCustomSpell(SPELL_RG_SHADOW_CRASH, SPELLVALUE_BASE_POINT0, static_cast<int32>(amount), p,
                    TRIGGERED_FULL_MASK);
        if (Player* p = ObjectAccessor::GetPlayer(*me, condemned))
            p->RemoveAurasDueToSpell(SPELL_RG_THUMBS_DOWN);
        Log("shadow-crash", Acore::StringFormat("inside={} share={:.1f}%", takers.size(),
            ThumbsSharePct(static_cast<uint32>(takers.size()))));
    }

    // ---- RG9 Rend's Mark --------------------------------------------------------------------------------------------

    void Mark()
    {
        _nextMarkAt = _showMs + kMarkEveryMs;
        Creature* gyth = Gyth();
        GythDrake* drake = (gyth && gyth->IsAlive()) ? DrakeOf(gyth) : nullptr;
        if (!drake || drake->Riderless() || !gyth->IsEngaged())
            return;
        if (drake->Hovering())
        {
            _nextMarkAt = _showMs + kRetryMs;
            return;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        Player* target = DungeonKit::PickPlayer(gyth, rule);
        if (!target)
            return;
        Talk(EMOTE_REND_MARK, target);
        gyth->CastSpell(target, SPELL_RG_MARK, true);
        // The marked player: hit unless 20 yd from Gyth when he breathes.
        MechanicRef run = Mechanic::RunOut(gyth, target, kMarkRunOutYd, Ms(kMarkWarnMs));
        run.From(BossMechanics::MeasuredFrom::Owner).Damage(kBreathPct).TankDamage(kBreathPct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_RG_FLAME_BREATH).Weakened().NoFillTimer().Within(RoomBounds())
            .Tag(TAG_RG_MARK);
        // Everyone else: the cone from Gyth aimed live at the marked player (the Balnazzar BZ1 shape).
        BossMechanics::Eligibility others;
        for (Player* p : FightPlayers())
            if (p != target)
                others.carriers.insert(p->GetGUID());
        if (others.carriers.empty())
            others.carriers.insert(ObjectGuid::Empty);
        BossMechanics::ZoneSpec zone = BossMechanics::Shapes::Cone(gyth, kBreathAngleDeg, kBreathLengthYd);
        zone.to = BossMechanics::Anchor(target);
        MechanicRef cone = Mechanic::Zone(gyth, zone, Ms(kMarkWarnMs));
        cone.Damage(kBreathPct).TankDamage(kBreathPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_RG_FLAME_BREATH)
            .Weakened().Eligible(others).Within(RoomBounds()).Tag(TAG_RG_MARK_CONE);
        Map* map = me->GetMap();
        ObjectGuid const gythGuid = gyth->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        cone.OnResolve([map, gythGuid, targetGuid](BossMechanics::ResolveResult const& r)
        {
            Creature* g = map ? map->GetCreature(gythGuid) : nullptr;
            if (r.fizzled || !g || !g->IsAlive())
                return;
            if (auto* d = DrakeOf(g))
                d->BreatheAt(ObjectAccessor::GetUnit(*g, targetGuid));
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mark-breath", Acore::StringFormat("cone-hits={}",
                r.hits.size()));
        });
        Log("mark", target->GetName());
    }

    // ---- act 3: Rend's own kit --------------------------------------------------------------------------------------

    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _now < _whirlUntil;
    }

    void RendKit(uint32 diff)
    {
        bool const swap = DungeonKit::Flex::TankSwapOn(_players);
        if (swap)
            HoldWounds(diff);
        Empowerment(diff);
        if (_whirlLookAt && _now >= _whirlLookAt)
        {
            _whirlLookAt = 0;
            me->CastSpell(me, SPELL_RG_WHIRLWIND_LOOK, true);
        }
        if (Busy())
            return;
        if (_now >= _nextWhirlAt)
        {
            Whirlwind();
            return;
        }
        if (_now >= _nextBannerAt)
            PlantBanner();
        Unit* victim = me->GetVictim();
        if (_now >= _nextStrikeAt)
        {
            if (victim && me->IsWithinMeleeRange(victim))
                MortalStrike(victim, swap);
            else if (!swap)
                _nextStrikeAt = _now + kRetryMs;
        }
        if (Busy())
            return;
        if (_now >= _nextCleaveAt)
        {
            _nextCleaveAt = _now + urand(kCleaveEveryMinMs, kCleaveEveryMaxMs);
            if (victim && me->IsWithinMeleeRange(victim))
                DoCastVictim(SPELL_RG_CLEAVE);
        }
        if (Busy())
            return;
        DoMeleeAttackIfReady();
    }

    // RG11: a 2 s wind-up, then 6 s of an 8 yd circle moving with him (everyone, the tank too).
    void Whirlwind()
    {
        _nextWhirlAt = _now + kWhirlEveryMs;
        DungeonKit::CastBar(me, SPELL_RG_WHIRLWIND_BAR);
        MechanicRef ref = Mechanic::Circle(me, me, kWhirlRadius, Ms(kWhirlWindupMs));
        ref.AnchorOn(me).Persistent(Ms(kWhirlMs), Ms(kWhirlTickMs)).Damage(kWhirlPct).TankDamage(kWhirlPct)
            .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_RG_WHIRLWIND).Within(RoomBounds()).Tag(TAG_RG_WHIRL);
        _live.push_back(ref.Handle());
        _whirlLookAt = _now + kWhirlWindupMs;
        _whirlUntil = _now + kWhirlWindupMs + kWhirlMs;
        Log("whirlwind");
    }

    // RG12: a banner at his feet (at most 3 alive), with a tank-only 10 yd circle on it for the bots' drag-out.
    void PlantBanner()
    {
        _nextBannerAt = _now + kBannerEveryMs;
        std::vector<Creature*> const alive = LiveBanners();
        if (alive.size() >= kBannerMax)
            return;
        Creature* banner = me->SummonCreature(NPC_BRS_BANNER, me->GetPositionX(), me->GetPositionY(),
            me->GetPositionZ(), me->GetOrientation(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!banner)
            return;
        Talk(EMOTE_REND_BANNER);
        BossMechanics::Eligibility tanks;
        tanks.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, banner, kBannerRadius, Ms(1000));
        ref.AnchorOn(banner).Persistent(Ms(kBannerZoneMs), Ms(0)).Eligible(tanks).NoFillTimer()
            .Color(BossMechanics::Color::Orange).Within(RoomBounds()).Tag(TAG_RG_BANNER);
        _banners.emplace_back(banner->GetGUID(), ref.Handle());
        Log("banner", Acore::StringFormat("alive={}", alive.size() + 1));
    }

    std::vector<Creature*> LiveBanners()
    {
        std::vector<Creature*> out;
        std::erase_if(_banners, [this, &out](std::pair<ObjectGuid, MechanicHandle> const& b)
        {
            Creature* banner = ObjectAccessor::GetCreature(*me, b.first);
            if (banner && banner->IsAlive())
            {
                out.push_back(banner);
                return false;
            }
            Mechanic::Cancel(me, b.second);
            return true;
        });
        return out;
    }

    // RG12: the buff while a live banner stands within 10 yd of him.
    void Empowerment(uint32 diff)
    {
        _bannerPollMs = _bannerPollMs > diff ? _bannerPollMs - diff : 0;
        if (_bannerPollMs)
            return;
        _bannerPollMs = kBannerPollMs;
        bool near = false;
        for (Creature* banner : LiveBanners())
            if (me->GetExactDist2d(banner) <= kBannerRadius)
                near = true;
        if (near == _empowered)
            return;
        _empowered = near;
        if (near)
            me->CastSpell(me, SPELL_RG_BANNER_EMPOWER, true);
        else
            me->RemoveAurasDueToSpell(SPELL_RG_BANNER_EMPOWER);
        Log("banner-empowered", Acore::StringFormat("on={}", near ? 1 : 0));
    }

    // RG14 / RG17: Mortal Strike; at 10 every 8 s with a Mortal Wounds stack.
    void MortalStrike(Unit* victim, bool swap)
    {
        DoCastVictim(SPELL_RG_MORTAL_STRIKE);
        if (!swap)
        {
            _nextStrikeAt = _now + urand(kStrikeEveryMinMs, kStrikeEveryMaxMs);
            return;
        }
        uint32 const stacks = DungeonKit::AddStacks(victim, SPELL_RG_MORTAL_WOUNDS, 1, me, kWoundsMax);
        DungeonKit::ShortenAura(victim, SPELL_RG_MORTAL_WOUNDS, me->GetGUID(), Ms(kWoundsMs));
        if (victim->GetGUID() == _woundsHeldOn)
            _woundsHeldMs = 0;
        _nextStrikeAt = _now + kWoundsEveryMs;
        Log("mortal-wounds", Acore::StringFormat("on={} stacks={}", victim->GetName(), stacks));
    }

    // His target's Mortal Wounds hold while he cannot strike it (B7 / B14's hold).
    void HoldWounds(uint32 diff)
    {
        Unit* victim = me->GetVictim();
        ObjectGuid const on = victim ? victim->GetGUID() : ObjectGuid::Empty;
        if (on != _woundsHeldOn)
        {
            _woundsHeldOn = on;
            _woundsHeldMs = 0;
        }
        if (!victim)
            return;
        bool const holding = Busy() || !me->IsWithinMeleeRange(victim);
        if (holding)
            _woundsHeldMs += diff;
        if (!_woundsHeldMs)
            return;
        Aura* aura = victim->GetAura(SPELL_RG_MORTAL_WOUNDS, me->GetGUID());
        if (!aura)
        {
            _woundsHeldMs = 0;
            return;
        }
        if (holding && !HoldDue(_woundsHeldMs, aura->GetDuration()))
            return;
        DungeonKit::ShortenAura(victim, SPELL_RG_MORTAL_WOUNDS, me->GetGUID(),
            Milliseconds(aura->GetDuration() + static_cast<int32>(_woundsHeldMs)));
        _woundsHeldMs = 0;
    }

    // ---- the end of an attempt --------------------------------------------------------------------------------------

    // RG15: everything goes; Gyth's slot is reset; the instance respawns Rend on his balcony (FAIL, as stock) and
    // Nefarius says line 11. Ends with the state write: the respawn resets this AI.
    void Wipe(char const* why)
    {
        Log("wipe", Acore::StringFormat("why={} act={} show={}ms", why, ActName(_act), _showMs));
        _act = Act::Over;
        Cleanup(false);
        if (instance)
        {
            if (instance->GetBossState(BOSS_GYTH) != NOT_STARTED)
                instance->SetBossState(BOSS_GYTH, NOT_STARTED);
            instance->HandleGameObject(instance->GetGuidData(GO_GYTH_ENTRY_DOOR), true);
            instance->SetBossState(BOSS_REND, FAIL);
        }
    }

    // The attempt's state, gone (wipe rule 4): every mechanic, front, pool and its look, banner, add and debuff.
    void Cleanup(bool died)
    {
        Creature* nef = _nef.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _nef);
        Unit* frontOwner = FrontOwner();
        _fronts.Clear(frontOwner ? frontOwner : me);     // an owner gone: its fronts went with its encounter
        _frontOwner.Clear();
        if (nef)
        {
            _pools.Clear(nef);
            while (nef->RemoveDynObject(SPELL_RG_SHADOWFLAME_POOL))
                ;
            while (nef->RemoveDynObject(SPELL_RG_SHADOWFLAME_POOL_H))
                ;
            nef->RemoveAurasDueToSpell(SPELL_RG_IMPATIENT_HOST);
            nef->RemoveAurasDueToSpell(SPELL_RG_BORED_HOST);
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (auto const& b : _banners)
            Mechanic::Cancel(me, b.second);
        _banners.clear();
        _burns.clear();
        if (!died)
            summons.DespawnAll();
        me->RemoveAurasDueToSpell(SPELL_RG_BANNER_EMPOWER);
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_MORTAL_WOUNDS);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_MARK);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_THUMBS_DOWN);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_FROZEN);
            // Gyth's armor loss too: a wipe despawns him without his own Cleanup (R-2 m-2). Not while he fights on
            // after Rend's death (his tank's stacks are his swap's).
            if (!died || !GythAlive())
                instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_CORROSIVE_ACID);
        }
        _arena.Reset();
        _engaged = false;
        _empowered = false;
        _gythDied = false;
        _gythEvaded = false;
        _gythDiedAt = Position();
        _gyth.Clear();
        _now = 0;
        _engageAt = 0;
        _nextCallAt = 0;
        _roundIndex = 0;
        _bored = 0;
        _nextMarkAt = 0;
        _nextWhirlAt = 0;
        _nextBannerAt = 0;
        _nextStrikeAt = 0;
        _nextCleaveAt = 0;
        _whirlUntil = 0;
        _whirlLookAt = 0;
        _woundsHeldOn.Clear();
        _woundsHeldMs = 0;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::PuddleField _pools;
    DungeonKit::FrontDirector _fronts;
    std::vector<MechanicHandle> _live;
    std::vector<std::pair<ObjectGuid, MechanicHandle>> _banners;
    std::unordered_map<ObjectGuid, uint64> _burns;     // a pool's last burn per player (show clock)
    ObjectGuid _nef;
    ObjectGuid _gyth;
    ObjectGuid _portcullis;
    ObjectGuid _frontOwner;
    ObjectGuid _woundsHeldOn;
    Position _gythDiedAt;
    Act _act = Act::Idle;
    uint64 _showMs = 0;             // the show's clock (from the trigger)
    uint64 _actStartMs = 0;
    uint64 _groupOneAt = 0;
    uint64 _groupTwoAt = 0;
    uint64 _actTwoAt = 0;
    uint64 _nextCallAt = 0;
    uint64 _nextMarkAt = 0;
    uint64 _engageAt = 0;
    uint64 _now = 0;                // ms since Rend's pull (act 3)
    uint64 _nextWhirlAt = 0;
    uint64 _nextBannerAt = 0;
    uint64 _nextStrikeAt = 0;
    uint64 _nextCleaveAt = 0;
    uint64 _whirlUntil = 0;
    uint64 _whirlLookAt = 0;
    uint32 _woundsHeldMs = 0;
    uint32 _wipeMs = 0;
    uint32 _pollMs = 0;
    uint32 _bannerPollMs = 0;
    uint32 _roundIndex = 0;
    uint8 _bored = 0;
    uint8 _players = 0;             // the show's count (a preview at the trigger; his own held at his pull)
    bool _heroic = false;
    bool _engaged = false;
    bool _empowered = false;
    bool _gythDied = false;
    bool _gythEvaded = false;
    bool _quietSummon = false;
};

namespace
{
    boss_rend_blackhand_rework* FindRendAI(ChatHandler* handler)
    {
        Creature* rend = BrsTest::FindBoss(handler, NPC_REND);
        if (!rend)
            return nullptr;
        auto* ai = rend->IsAIEnabled ? dynamic_cast<boss_rend_blackhand_rework*>(rend->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Rend is not running boss_rend_blackhand_rework (check the ScriptName).");
        return ai;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("Rend: {}", error);
            return false;
        }
        handler->PSendSysMessage("Rend: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_REND, BOSS_REND);
    }

    // `.dbtest brs rend state`: the act, the show's clock, the rounds, the pools and banners.
    bool HandleState(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Rend: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs rend start`: the show as the area trigger starts it (RG1; `.gm off`: a GM is no player of it).
    bool HandleStart(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestStart(), "the show starts (RG1)");
    }

    bool HandleAct2(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestAct(Act::Drake), "act 2, Gyth comes in (RG2)");
    }

    bool HandleAct3(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestAct(Act::Warchief), "act 3 on the timer, Rend leaps down (RG3)");
    }

    bool Round(ChatHandler* handler, BrsRendGyth::Round r, char const* what)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestRound(r), what);
    }

    bool HandleDress(ChatHandler* handler)
    {
        return Round(handler, BrsRendGyth::Round::DressHunt, "Kill the one in the dress (RG5)");
    }

    bool HandleSweep(ChatHandler* handler)
    {
        return Round(handler, BrsRendGyth::Round::FreezingSweep, "Freezing Sweep (RG6)");
    }

    bool HandleShadowflame(ChatHandler* handler)
    {
        return Round(handler, BrsRendGyth::Round::Shadowflame, "Taste in my power (RG7)");
    }

    bool HandleThumbs(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        if (ai && !ai->HeroicMap())
            return Done(handler, "Thumbs Down is heroic only (RG8)", "");
        return Round(handler, BrsRendGyth::Round::ThumbsDown, "Thumbs Down (RG8)");
    }

    bool HandleMark(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestMark(), "Rend's Mark (RG9)");
    }

    bool HandleWhirlwind(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestRendKit(true), "Whirlwind (RG11)");
    }

    bool HandleBanner(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        return ai && Done(handler, ai->TestRendKit(false), "a Banner of the Dark Horde (RG12)");
    }

    // `.dbtest brs rend insult`: the insult as the selected player (or you) gives it (DR10, for B15).
    bool HandleInsult(ChatHandler* handler)
    {
        Creature* nef = BrsTest::FindBoss(handler, NPC_BRS_NEFARIUS);
        Player* player = handler->getSelectedPlayer();
        if (!player && handler->GetSession())
            player = handler->GetSession()->GetPlayer();
        auto* ai = (nef && nef->IsAIEnabled) ? dynamic_cast<npc_brs_lord_victor_nefarius*>(nef->AI()) : nullptr;
        if (!ai || !player)
        {
            handler->SendErrorMessage("{}", "Rend: no Nefarius copy (300732) running npc_brs_lord_victor_nefarius.");
            return false;
        }
        ai->Insult(player);
        InstanceScript* instance = nef->GetInstanceScript();
        handler->PSendSysMessage("Rend: insult given; the instance's insult flag is {}.",
            instance ? instance->GetData(DATA_NEF_INSULTED) : 0);
        return true;
    }

    // `.dbtest brs rend wipe`: the attempt ends (RG15).
    bool HandleWipe(ChatHandler* handler)
    {
        boss_rend_blackhand_rework* ai = FindRendAI(handler);
        if (!ai)
            return false;
        ai->TestWipe();
        handler->PSendSysMessage("{}", "Rend: the attempt is reset (RG15).");
        return true;
    }

    ChatCommandTable const& RendTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "state",       HandleState,       SEC_GAMEMASTER, Console::No },
            { "start",       HandleStart,       SEC_GAMEMASTER, Console::No },
            { "act2",        HandleAct2,        SEC_GAMEMASTER, Console::No },
            { "act3",        HandleAct3,        SEC_GAMEMASTER, Console::No },
            { "dress",       HandleDress,       SEC_GAMEMASTER, Console::No },
            { "sweep",       HandleSweep,       SEC_GAMEMASTER, Console::No },
            { "shadowflame", HandleShadowflame, SEC_GAMEMASTER, Console::No },
            { "thumbs",      HandleThumbs,      SEC_GAMEMASTER, Console::No },
            { "mark",        HandleMark,        SEC_GAMEMASTER, Console::No },
            { "whirlwind",   HandleWhirlwind,   SEC_GAMEMASTER, Console::No },
            { "banner",      HandleBanner,      SEC_GAMEMASTER, Console::No },
            { "insult",      HandleInsult,      SEC_GAMEMASTER, Console::No },
            { "wipe",        HandleWipe,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rend_blackhand_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_rend_blackhand_rework, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_lord_victor_nefarius, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_banner_of_the_dark_horde, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_frost_wall, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("rend", RendTestCommands());
}
