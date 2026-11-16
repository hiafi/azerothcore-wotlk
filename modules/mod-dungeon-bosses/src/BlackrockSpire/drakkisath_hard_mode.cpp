/*
 * mod-dungeon-bosses, Blackrock Spire B15: General Drakkisath's hard mode, the General's Army (heroic only).
 * Build spec SP 3990-4082 rows DR10-DR19 (design SP 3828-3937, rulings 69-72); handoff section 3.7, section 3.5 row
 * B15, section 3.6, section 3.8 (NM 13). It fights on B14's AI (boss_drakkisath_rework) through DrakkisathFight.h: B14
 * makes one GeneralsArmy per heroic pull with DATA_GENERALS_ARMY lit and calls its hooks. Pure rules and numbers:
 * DrakkisathHardModeLogic.h.
 *
 *   DR10 The insult      B12's arena Nefarius copy saves DATA_NEF_INSULTED (its lines 18-19 are B12's rev); B15 only
 *                        reads it.
 *   DR11 The herald      300740 (npc_brs_generals_herald, a heroic-only spawn at the throne room's south entrance):
 *                        shown while the insult is saved and he waits (hidden otherwise); its gossip "Let them come"
 *                        (the option's `conditions` mirror the rule) lights DATA_GENERALS_ARMY (the instance refuses it
 *                        otherwise), the herald's line 0, his line 9, and the herald runs to the alcove. It comes back
 *                        to the entrance when the attempt ends (the instance clears the flag; DR19).
 *   DR12 The Muster      1:30 on a timer: he stays rooted in his alcove (240k x the ladder for the whole fight), his
 *                        brands as heroic and his blade on whoever reaches him; the Elite Guards (30k each) hold the
 *                        alcove's mouth and strike anyone within 8 yd; the side gates open and a squad marches in every
 *                        20 s (alternating gates): Vanguard, Fire Line, Shield Wall, then one soldier larger. Anyone
 *                        who hurts him from beyond 10 yd is answered with a Fire Blast circle (no free damage window).
 *   DR13 Vanguard        Dragonspawn (17k) fixate a random player (the kit's Chaser) and wind up Cleaving Charge (90
 *                        degrees, 8 yd, 35%, Weakened; the fixated player aims it and is spared); a Captain (23k):
 *                        +25% damage to soldiers within 10 yd (the aura on their melee and stock spells, the percent on
 *                        their registry hits), Arcing Smash and Mortal Strike.
 *   DR14 Fire Line       Fire Tongues (13k): Scattering Flame (2 / 4 marks, 6 yd, 3 s, 30%, Weakened to others inside)
 *                        and Fireball Volley (2 s, interruptible; landed 20% to everyone); a Dragon Guard.
 *   DR15 Shield Wall     Dragon Guards (21k): 50% less damage from the front; in turn, a Shield Charge every 10 s (2 s
 *                        wind-up, a 4 yd lane 25 yd at a random player, 30%, Weakened, 5 yd knockback aside); Shield
 *                        Slam.
 *   DR16 The field       at 1:30: line 3, he steps down (unrooted) with the living Guards (released), his whole kit
 *                        starts over (Seared Flesh at 10 too); a squad every 45 s, each with the Champion's Call.
 *   DR17 The Call        line 4, a 4 yd circle 8 yd in front of him for 5 s (a Soak: no bot may claim it for the first
 *                        2 s, then any player but his tank); the first player in it (not his tank) is the challenger.
 *                        Unanswered: a Trophy and line 5.
 *   DR18 The Challenge   on his cast queue (a 12 s hold): rooted, a 12 s Physical bar, the kit's lethal 12 yd ring
 *                        round him and the challenger (pushes everyone else out; pets spared, the challenger dies
 *                        stepping out: the defaults pending the user), six blows 2 s apart at the challenger only (1.5
 *                        s telegraphs, the bots kept inside the ring by RingInside); each avoided blow +1 Finesse;
 *                        18,000 damage by the challenger wins at once (Humbled 10 s, line 6); time up or a dead
 *                        challenger: a Trophy (+10% his damage; line 7). An early end interrupts the bar (B14 ends the
 *                        hold).
 *   DR19 Reset           OnEnd ends the Call and the Challenge, cancels every mechanic, removes the auras (Trophy,
 *                        Humbled, Finesse, the marks), closes the gates (the instance's door data closes them too),
 *                        puts his and the Guards' heroic health back; B14's cleanup despawns the squads and the ring's
 *                        carrier; the instance respawns the Guards and clears the flag; the insult stays saved.
 *   Loot                 B14's pull passes hardMode to OnBossPull (LootMode 8 at 10); the instance keeps LootMode 2
 *                        while the flag is lit and records BOSS_GENERALS_ARMY (27) on the kill.
 *
 * Every timer runs on the fight's clock (DrakkisathFight::FightMs) or the soldiers' own. Every firing logs one INFO
 * line "brs drakkisath army-<mechanic> ..." (module.dungeonbosses); `.dbtest brs army <...>` fires them.
 */

#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DrakkisathFight.h"
#include "DrakkisathHardModeLogic.h"
#include "DrakkisathLogic.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "DungeonKitFlex.h"
#include "DungeonKitRing.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <list>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsGeneralsArmy;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BrsDrakkisath::Ability;
using BrsDrakkisath::DrakkisathFight;
using BrsDrakkisath::DrakkisathHardMode;

static_assert(uint8(Ability::Brands) == uint8(Kit::Brands) && uint8(Ability::Thunderclap) == uint8(Kit::Thunderclap)
    && uint8(Ability::Flamestrike) == uint8(Kit::Flamestrike)
    && uint8(Ability::BlackbladeSweep) == uint8(Kit::BlackbladeSweep) && uint8(Ability::Rage) == uint8(Kit::Rage)
    && uint8(Ability::SearedFlesh) == uint8(Kit::SearedFlesh) && uint8(Ability::Melee) == uint8(Kit::Melee),
    "Kit mirrors BrsDrakkisath::Ability");

namespace
{
    char const* const kLogKey = "army";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    bool IsSoldier(uint32 entry)
    {
        return entry == NPC_BRS_SQUAD_DRAGONSPAWN || entry == NPC_BRS_SQUAD_CAPTAIN
            || entry == NPC_BRS_SQUAD_FIRE_TONGUE || entry == NPC_BRS_SQUAD_DRAGON_GUARD;
    }

    uint32 SoldierHealthAt5(uint32 entry)
    {
        switch (entry)
        {
            case NPC_BRS_SQUAD_DRAGONSPAWN:     return kDragonspawnHealthAt5;
            case NPC_BRS_SQUAD_CAPTAIN:         return kCaptainHealthAt5;
            case NPC_BRS_SQUAD_FIRE_TONGUE:     return kFireTongueHealthAt5;
            case NPC_BRS_SQUAD_DRAGON_GUARD:    return kDragonGuardHealthAt5;
            default:                            return 0;
        }
    }

    // The soldiers of a squad, in summon order (the Captain or Dragon Guard last: it stands behind the line).
    std::vector<uint32> SoldiersOf(SquadPlan const& p)
    {
        std::vector<uint32> out;
        out.insert(out.end(), p.dragonspawn, NPC_BRS_SQUAD_DRAGONSPAWN);
        out.insert(out.end(), p.fireTongues, NPC_BRS_SQUAD_FIRE_TONGUE);
        out.insert(out.end(), p.dragonGuards, NPC_BRS_SQUAD_DRAGON_GUARD);
        out.insert(out.end(), p.captains, NPC_BRS_SQUAD_CAPTAIN);
        return out;
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }

    Position ToPos(Vec2 p, float z, float o = 0.f)
    {
        return Position(p.x, p.y, z, o);
    }

    // The floor under a point (the squads' lower floor is a placeholder: never trust its z).
    float FloorZ(Map* map, float x, float y, float z)
    {
        float const h = map ? map->GetHeight(x, y, z + 3.f) : INVALID_HEIGHT;
        return (h > INVALID_HEIGHT && std::fabs(h - z) < 6.f) ? h : z;
    }

    GuidSet GuidsOf(std::vector<Player*> const& players)
    {
        GuidSet out;
        for (Player* p : players)
            if (p)
                out.insert(p->GetGUID());
        return out;
    }

    // The fight's view through his AI (nullptr when he is not running B14's AI).
    DrakkisathFight* FightOf(Creature* boss)
    {
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<DrakkisathFight*>(boss->AI());
    }

    Creature* DrakkisathOf(WorldObject const* any)
    {
        InstanceScript* instance = any ? any->GetInstanceScript() : nullptr;
        return instance ? instance->GetCreature(BOSS_DRAKKISATH) : nullptr;
    }

    // ---- DR11 the arming (the herald's gossip and `.dbtest brs army arm` share it) ----------------------------------

    HeraldRefusal RefusalAt(WorldObject const* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return HeraldRefusal::NotHeroic;
        return HeraldRefusalFor(where->GetMap()->IsHeroic(), instance->GetData(DATA_NEF_INSULTED) != 0,
            instance->GetBossState(BOSS_DRAKKISATH), instance->GetData(DATA_GENERALS_ARMY) != 0);
    }

    // Arms the General's Army for `player` at `where` (the herald, or the GM). Returns the refusal (None: armed).
    HeraldRefusal Arm(WorldObject* where, Player* player)
    {
        HeraldRefusal refusal = RefusalAt(where);
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (refusal == HeraldRefusal::None && instance)
        {
            instance->SetData(DATA_GENERALS_ARMY, 1);
            if (!instance->GetData(DATA_GENERALS_ARMY))
                refusal = HeraldRefusal::Fighting;      // the instance refused it (GeneralsArmyChangeAllowed)
        }
        if (refusal != HeraldRefusal::None)
        {
            if (player && player->GetSession())
                ChatHandler(player->GetSession()).SendNotification(HeraldRefusalText(refusal));
            DungeonKit::LogMechanic(kLogDungeon, "drakkisath", "army-arm-refused", Acore::StringFormat("by={} why={}",
                player ? player->GetName() : std::string("none"), uint32(refusal)));
            return refusal;
        }
        if (Creature* boss = instance->GetCreature(BOSS_DRAKKISATH))
            if (boss->IsAlive() && boss->IsAIEnabled)
                boss->AI()->Talk(BrsDrakkisath::YELL_DR_ARMY_ARMED, player);
        DungeonKit::LogMechanic(kLogDungeon, "drakkisath", "army-armed", Acore::StringFormat("by={}",
            player ? player->GetName() : std::string("none")));
        return HeraldRefusal::None;
    }

    // The side gates (door data on Drakkisath: closed while he fights, open on his death). The hard mode opens them
    // for the squads; DR19 closes them again (and the instance's door update does on the attempt's end).
    void SetGates(Creature* boss, bool open)
    {
        for (uint32 entry : { uint32(GO_DRAKKISATH_DOOR_1), uint32(GO_DRAKKISATH_DOOR_2) })
            if (GameObject* gate = boss->FindNearestGameObject(entry, 80.f))
                gate->SetGoState(open ? GO_STATE_ACTIVE : GO_STATE_READY);
    }
}

// The hard mode of one pull (B14 makes it at a heroic pull with the army armed and ends it with the pull).
class GeneralsArmy final : public DrakkisathHardMode
{
public:
    GeneralsArmy() : _serial(++NextSerial()) { }

    // The pull's hard mode, as a callback or a command finds it again: his AI's ActiveHardMode on the same pull
    // (`serial`, 0: any), or nullptr.
    static GeneralsArmy* Find(Map* map, ObjectGuid bossGuid, uint32 serial, DrakkisathFight** fightOut = nullptr)
    {
        if (!map)
            return nullptr;
        DrakkisathFight* fight = FightOf(map->GetCreature(bossGuid));
        auto* army = fight ? dynamic_cast<GeneralsArmy*>(fight->ActiveHardMode()) : nullptr;
        if (!army || (serial && army->_serial != serial))
            return nullptr;
        if (fightOut)
            *fightOut = fight;
        return army;
    }

    // The running hard mode from any unit of the map (a soldier, a spell's caster).
    static GeneralsArmy* FindFor(WorldObject const* any, DrakkisathFight** fightOut = nullptr)
    {
        DrakkisathFight* fight = FightOf(DrakkisathOf(any));
        auto* army = fight ? dynamic_cast<GeneralsArmy*>(fight->ActiveHardMode()) : nullptr;
        if (army && fightOut)
            *fightOut = fight;
        return army;
    }

    // ---- the pull ---------------------------------------------------------------------------------------------------

    void OnEngage(DrakkisathFight& fight) override
    {
        Creature* boss = fight.Boss();
        _map = boss->GetMap();
        _bossGuid = boss->GetGUID();
        _players = fight.Players();
        _baseHealth = BaseBeforeHardMode(boss->GetMaxHealth(), _players);
        boss->RemoveAurasDueToSpell(SPELL_GA_TROPHY);
        boss->RemoveAurasDueToSpell(SPELL_GA_HUMBLED);
        DungeonKit::Flex::SetHealth(boss, kBossHealthAt5, true);
        for (Creature* guard : fight.Guards())
            DungeonKit::Flex::SetHealth(guard, kEliteGuardHealthAt5, true);
        std::vector<Position> spots;
        for (Point3 const& s : kGuardHoldSpots)
            spots.emplace_back(s.x, s.y, s.z, kGuardHoldFacing);
        fight.HoldGuards(spots, kGuardHoldReachYd);
        fight.SetRooted(true);
        SetGates(boss, true);
        Describe(boss);
        fight.Log("army-engage", Acore::StringFormat("players={} health={} base-before={} guards={}", _players,
            boss->GetMaxHealth(), _baseHealth, fight.Guards().size()));
    }

    void OnUpdate(DrakkisathFight& fight, uint32 /*diff*/) override
    {
        uint64 const now = fight.FightMs();
        RunPending(fight, now);
        if (!_field && PhaseAt(now) == Phase::Field)
            StartField(fight);
        while (SquadArrivalMs(_nextSquad) <= now)
            MarchSquad(fight, _nextSquad++);
        UpdateSquads(fight, now);
        UpdateCall(fight, now);
        UpdateChallenge(fight, now);
        Creature* boss = fight.Boss();
        if (_rings.Count())
            _rings.Prune(boss);
    }

    void OnDamageTaken(DrakkisathFight& fight, Unit* attacker, uint32& damage) override
    {
        if (!attacker || !damage)
            return;
        if (_challenge.active && attacker->GetGUID() == _challenge.challenger)
            _challenge.damage += damage;
        Phase const phase = _field ? Phase::Field : Phase::Muster;
        Player* owner = attacker->GetCharmerOrOwnerPlayerOrPlayerItself();
        if (!owner || !AnswersAttacker(phase, fight.Boss()->GetExactDist2d(attacker)))
            return;
        uint64 const now = fight.FightMs();
        uint64& next = _answerAt[owner->GetGUID()];
        if (now < next)
            return;
        next = now + kAnswerEveryMs;
        Answer(fight, attacker);
    }

    // His Trophies raise his non-melee hits (B14's kit and the blows; the aura raises his melee): R-2.
    void OnDamageDealt(DrakkisathFight& /*fight*/, Unit* victim, uint32& damage, bool melee) override
    {
        if (victim && damage)
            damage = TrophyDamage(damage, _trophies, melee);
    }

    bool UsesAbility(DrakkisathFight const& /*fight*/, Ability a) const override
    {
        return UsesKit(_field ? Phase::Field : Phase::Muster, Calling(), _challenge.active, Kit(uint8(a)));
    }

    std::optional<uint32> OnCast(DrakkisathFight& fight, uint32 id) override
    {
        if (id != CAST_GA_CHALLENGE)
            return std::nullopt;
        if (!StartChallenge(fight))
            return std::nullopt;
        return kChallengeMs;
    }

    void OnSpellFailed(DrakkisathFight& fight, uint32 spellId) override
    {
        // His duel bar stopped by anything but this script (B14 has ended the hold already): the Challenge ends now.
        if (spellId == SPELL_GA_CHALLENGE_BAR && _challenge.active && !_ending)
        {
            std::optional<ChallengeEnd> const end = JudgeChallenge(_challenge.damage, _challenge.target,
                ChallengerAlive(fight), true);
            EndChallenge(fight, end ? *end : ChallengeEnd::Lost, false);
        }
    }

    void OnSummonDied(DrakkisathFight& fight, Creature* summon) override
    {
        if (!summon || !IsSoldier(summon->GetEntry()))
            return;
        fight.Log("army-soldier-died", Acore::StringFormat("entry={} alive={}", summon->GetEntry(),
            LiveSoldiers(fight)));
    }

    void OnGuardDied(DrakkisathFight& fight, Creature* /*guard*/) override
    {
        fight.Log("army-guard-died", Acore::StringFormat("phase={} left={}", _field ? 2 : 1, fight.Guards().size()));
    }

    void OnEnd(DrakkisathFight& fight, bool died) override
    {
        Creature* boss = fight.Boss();
        EndCall(fight);
        EndChallenge(fight, ChallengeEnd::Aborted, true);
        _rings.Clear(boss);
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(boss, handle);
        _live.clear();
        _pending.clear();
        boss->RemoveAurasDueToSpell(SPELL_GA_TROPHY);
        boss->RemoveAurasDueToSpell(SPELL_GA_HUMBLED);
        if (InstanceScript* instance = boss->GetInstanceScript())
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_GA_CHALLENGER);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_GA_FINESSE);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_GA_SCATTERING_MARK);
        }
        if (!died)
        {
            SetGates(boss, false);
            // Heroic health back (DD restores the base a script set: put the heroic one back before the evade).
            for (Creature* guard : fight.Guards())
                DungeonKit::Flex::SetHealth(guard, kEliteGuardHeroicHealthAt5, true);
            if (_baseHealth)
                DungeonKit::Flex::SetHealth(boss, _baseHealth, true);
        }
        fight.Log("army-end", Acore::StringFormat("died={} phase={} squads={} trophies={} challenges={}/{}",
            died ? 1 : 0, _field ? 2 : 1, _nextSquad, _trophies, _won, _challenges));
    }

    // ---- the soldiers call back (npc_brs_army_soldier) --------------------------------------------------------------

    // DR13 Cleaving Charge: the Dragonspawn's 1.5 s wind-up and the 90 degree cone in front of it (anchored on it,
    // turning with it; its fixated victim aims it and is spared). False: not started.
    bool CleavingCharge(DrakkisathFight& fight, Creature* dragonspawn)
    {
        if (!dragonspawn || !dragonspawn->GetVictim())
            return false;
        float const pct = kCleavingChargePct * CommandScale(Commanded(dragonspawn));
        DungeonKit::CastBar(dragonspawn, SPELL_GA_CLEAVING_CHARGE_BAR);
        // The soldier owns its hit (R-2 m-7: never his Seared Flesh or Trophy, credited to the soldier; it fights the
        // group, so BM keeps the room bounds for the bots).
        MechanicRef ref = Mechanic::Cone(dragonspawn, dragonspawn, kCleavingChargeAngleDeg, kCleavingChargeLength,
            Ms(kCleavingChargeCastMs), BossMechanics::TankExempt::Yes);
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_GA_CLEAVING_CHARGE).Weakened()
            .Within(fight.RoomBounds()).Tag(TAG_GA_CLEAVING_CHARGE);
        Map* map = _map;
        ObjectGuid const guid = dragonspawn->GetGUID();
        ref.OnResolve([map, guid](BossMechanics::ResolveResult const&)
        {
            if (Creature* ds = map ? map->GetCreature(guid) : nullptr)
                if (ds->IsAlive())
                    ds->CastSpell(ds, SPELL_GA_CLEAVING_CHARGE_LOOK, true);
        });
        Keep(fight, ref.Handle());
        fight.Log("army-cleaving-charge", Acore::StringFormat("on={} pct={:.1f}",
            dragonspawn->GetVictim()->GetName(), pct));
        return true;
    }

    // DR14 Scattering Flame: 2 / 4 marked players, a 6 yd circle on each for 3 s, then each bursts on everyone else
    // inside it.
    bool ScatteringFlame(DrakkisathFight& fight, Creature* tongue)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;               // "mechanics include the tank" (designer rule)
        rule.exclude = DuelExcluded();      // never the challenger inside the ring (R-2 M-3)
        std::vector<Player*> const marked = DungeonKit::PickPlayers(tongue, rule, kScatteringTargets.At(_players));
        if (marked.empty())
            return false;
        float const pct = kScatteringPct * CommandScale(Commanded(tongue));
        for (Player* p : marked)
            tongue->CastSpell(p, SPELL_GA_SCATTERING_MARK, true);
        MechanicRef ref = Mechanic::Spread(tongue, kScatteringRadius, Ms(kScatteringWarnMs));    // its own (m-7)
        ref.Targets(GuidsOf(marked)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_GA_SCATTERING_FLAME).Weakened().Within(fight.RoomBounds()).Tag(TAG_GA_SCATTERING_FLAME);
        ExcludeChallenger(fight, ref);
        Keep(fight, ref.Handle());
        fight.Log("army-scattering-flame", Acore::StringFormat("marked={} pct={:.1f}", marked.size(), pct));
        return true;
    }

    // DR14 Fireball Volley landed (spell_brs_army_fireball_volley, AfterCast; a kicked volley never gets here): 20% to
    // everyone, no Weakened.
    void VolleyLanded(DrakkisathFight& fight, Creature* tongue)
    {
        GuidSet const targets = GuidsOf(fight.FightPlayers());
        DungeonKit::RegistryHitSpec spec;
        spec.pct = kVolleyPct * CommandScale(Commanded(tongue));
        spec.tankPct = spec.pct;
        spec.school = SPELL_SCHOOL_FIRE;
        spec.spellId = SPELL_GA_VOLLEY_HIT;
        spec.weakened = false;
        spec.tag = TAG_GA_VOLLEY;
        Keep(fight, DungeonKit::RegistryHit(tongue, targets, spec));     // the Fire Tongue's own hit (m-7)
        fight.Log("army-volley-landed", Acore::StringFormat("players={} pct={:.1f}", targets.size(), spec.pct));
    }

    // ---- `.dbtest brs army` entry points ----------------------------------------------------------------------------

    void TestSquad(DrakkisathFight& fight, uint32 index)
    {
        MarchSquad(fight, index);
    }

    void TestField(DrakkisathFight& fight)
    {
        if (!_field)
            StartField(fight);
    }

    void TestCall(DrakkisathFight& fight)
    {
        StartCall(fight);
    }

    bool TestChallenge(DrakkisathFight& fight, Player* challenger)
    {
        if (!challenger || _challenge.active)
            return false;
        EndCall(fight);
        _pendingChallenger = challenger->GetGUID();
        fight.ScheduleCast(CAST_GA_CHALLENGE, 0, kChallengePriority);
        return true;
    }

    std::string TestState(DrakkisathFight& fight)
    {
        uint64 const now = fight.FightMs();
        std::string out = Acore::StringFormat("serial={} players={} t={}ms phase={} next-squad={} at {}ms soldiers={} "
            "guards={} trophies={} challenges={} won={} calling={} rings={}", _serial, _players, now, _field ? 2 : 1,
            _nextSquad + 1, SquadArrivalMs(_nextSquad), LiveSoldiers(fight), fight.Guards().size(), _trophies,
            _challenges, _won, Calling() ? 1 : 0, _rings.Count());
        if (_challenge.active)
        {
            Player* ch = ObjectAccessor::GetPlayer(*fight.Boss(), _challenge.challenger);
            out += Acore::StringFormat("\n  challenge: {} damage {}/{} t={}ms finesse {}", ch ? ch->GetName() : "?",
                _challenge.damage, _challenge.target, now - _challenge.startMs,
                ch ? DungeonKit::Stacks(ch, SPELL_GA_FINESSE) : 0);
        }
        return out;
    }

private:
    struct Pending
    {
        uint64 atMs = 0;
        std::function<void(GeneralsArmy&, DrakkisathFight&)> fn;
    };

    struct SquadRec
    {
        uint32 index = 0;
        SquadKind kind = SquadKind::Vanguard;
        std::vector<ObjectGuid> soldiers;
        uint64 arrivedMs = 0;           // 0: not in the hall yet
        uint64 nextChargeMs = 0;        // Shield Wall
        uint32 chargeTurn = 0;
    };

    struct CallState
    {
        bool active = false;
        bool botsMayClaim = false;
        uint64 startMs = 0;
        Position spot;
        MechanicHandle soak;
    };

    struct ChallengeState
    {
        bool active = false;
        uint32 id = 0;
        ObjectGuid challenger;
        uint64 startMs = 0;
        uint32 damage = 0;
        uint32 target = 0;
        DungeonKit::LethalRingSpec ring;
        std::array<Blow, kBlows> blows{};
        std::array<bool, kBlows> hit{};
        std::vector<MechanicHandle> handles;
    };

    static uint32& NextSerial()
    {
        static uint32 serial = 0;
        return serial;
    }

    // A registry callback that finds this pull's hard mode again (never a captured `this`).
    template <class Fn>
    std::function<void(Unit*)> OnArmy(Fn fn) const
    {
        Map* map = _map;
        ObjectGuid const boss = _bossGuid;
        uint32 const serial = _serial;
        return [map, boss, serial, fn](Unit* hit)
        {
            DrakkisathFight* fight = nullptr;
            if (GeneralsArmy* army = Find(map, boss, serial, &fight))
                if (hit)
                    fn(*army, *fight, hit);
        };
    }

    void Later(DrakkisathFight& fight, uint32 inMs, std::function<void(GeneralsArmy&, DrakkisathFight&)> fn)
    {
        _pending.push_back({ fight.FightMs() + inMs, std::move(fn) });
    }

    void RunPending(DrakkisathFight& fight, uint64 now)
    {
        if (_pending.empty())
            return;
        std::vector<Pending> due;
        std::vector<Pending> later;
        for (Pending& p : _pending)
            (p.atMs <= now ? due : later).push_back(std::move(p));
        _pending = std::move(later);
        for (Pending& p : due)
            p.fn(*this, fight);
    }

    void Keep(DrakkisathFight& fight, MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        fight.Track(handle);
    }

    // R-2 M-3: the challenger (in the ring, or stepping in) is no squad's pick, and no squad shape asks them to move or
    // knocks them: the ring kills only a challenger who steps out (wave 2 ruling).
    ObjectGuid DuelChallenger() const
    {
        return ObjectGuid(DuelChallengerOf(_challenge.active, _challenge.challenger.GetRawValue(),
            _pendingChallenger.GetRawValue()));
    }

    bool InDuel(Unit const* who) const
    {
        ObjectGuid const challenger = DuelChallenger();
        return who && !challenger.IsEmpty() && who->GetGUID() == challenger;
    }

    std::vector<uint64> DuelExcluded() const
    {
        ObjectGuid const challenger = DuelChallenger();
        if (challenger.IsEmpty())
            return {};
        return { challenger.GetRawValue() };
    }

    // A squad shape registered while a duel runs: every fight player but the challenger is eligible.
    void ExcludeChallenger(DrakkisathFight& fight, MechanicRef& ref) const
    {
        ObjectGuid const challenger = DuelChallenger();
        if (challenger.IsEmpty())
            return;
        BossMechanics::Eligibility others;
        for (Player* p : fight.FightPlayers())
            if (p->GetGUID() != challenger)
                others.carriers.insert(p->GetGUID());
        if (others.carriers.empty())
            others.carriers.insert(ObjectGuid::Empty);
        ref.Eligible(others);
    }

    bool Calling() const
    {
        return _call.active || !_pendingChallenger.IsEmpty();
    }

    static bool Commanded(Unit const* soldier)
    {
        return soldier && soldier->HasAura(SPELL_GA_COMMAND);
    }

    uint32 LiveSoldiers(DrakkisathFight& fight) const
    {
        uint32 n = 0;
        for (SquadRec const& squad : _squads)
            for (ObjectGuid const& guid : squad.soldiers)
                if (Creature* c = ObjectAccessor::GetCreature(*fight.Boss(), guid))
                    if (c->IsAlive())
                        ++n;
        return n;
    }

    // Boss data (SP): kill order Captain, Fire Tongues, Dragonspawn, Dragon Guards, then the Elite Guards (B14's
    // priority 1), then him; Fireball Volley on the interrupt list (expected), below his Flamestrike. At 10 the second
    // tank holds the Captains and Dragon Guards too (SP "Tank swap at 10"; B14 gave it the Elite Guards).
    void Describe(Creature* boss)
    {
        bool const assist = DungeonKit::Flex::TankSwapOn(_players);
        Mechanic::EditDescriptor(boss, [assist](BossMechanics::Descriptor& d)
        {
            if (assist)
            {
                d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_CAPTAIN, 1,
                    BossMechanics::Who::AssistTank));
                d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_DRAGON_GUARD, 1,
                    BossMechanics::Who::AssistTank));
            }
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_CAPTAIN, 5));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_FIRE_TONGUE, 4));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_DRAGONSPAWN, 3));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_SQUAD_DRAGON_GUARD, 2));
            d.interrupts.emplace_back(NPC_BRS_SQUAD_FIRE_TONGUE, SPELL_GA_FIREBALL_VOLLEY, kVolleyKickPriority,
                Ms(kVolleyEveryMs));
        });
    }

    // ---- DR12 / DR16 the Muster and the field -----------------------------------------------------------------------

    void StartField(DrakkisathFight& fight)
    {
        _field = true;
        Creature* boss = fight.Boss();
        boss->AI()->Talk(BrsDrakkisath::YELL_DR_PHASE_TWO);
        fight.SetRooted(false);
        fight.ReleaseGuards();
        fight.RestartKit(0);
        fight.Log("army-field", Acore::StringFormat("guards={} soldiers={}", fight.Guards().size(),
            LiveSoldiers(fight)));
    }

    void MarchSquad(DrakkisathFight& fight, uint32 index)
    {
        Creature* boss = fight.Boss();
        SquadPlan const plan = PlanSquad(index);
        uint32 const gate = SquadGate(index);
        std::vector<uint32> const entries = SoldiersOf(plan);
        std::vector<Player*> const players = fight.FightPlayers();
        SquadRec rec;
        rec.index = index;
        rec.kind = plan.kind;
        uint32 slot = 0;
        for (uint32 entry : entries)
        {
            Vec2 const at = SquadSpot(gate, slot++, uint32(entries.size()));
            float const z = FloorZ(_map, at.x, at.y, kSquadSpawn[gate].z);
            Creature* soldier = boss->SummonCreature(entry, at.x, at.y, z, kSquadSpawnFacing,
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, 15000);
            if (!soldier)
                continue;
            Mechanic::TrackUnit(boss, soldier);
            DungeonKit::Flex::SetHealth(soldier, SoldierHealthAt5(entry), true);
            if (entry == NPC_BRS_SQUAD_DRAGON_GUARD)
                soldier->AddAura(SPELL_GA_SHIELD_FRONT, soldier);
            rec.soldiers.push_back(soldier->GetGUID());
            MusterSoldier(soldier, players);
        }
        fight.Log("army-squad", Acore::StringFormat("n={} kind={} soldiers={} gate={} health={}", index + 1,
            SquadName(plan.kind), rec.soldiers.size(), uint32(gate ? GO_DRAKKISATH_DOOR_2 : GO_DRAKKISATH_DOOR_1),
            plan.HealthAt5()));
        _squads.push_back(std::move(rec));
        if (SquadCallsChallenge(index))
            StartCall(fight);
    }

    void MusterSoldier(Creature* soldier, std::vector<Player*> const& players);

    // A squad reaches the hall with its first soldier; Shield Wall squads charge in turn from then on.
    void UpdateSquads(DrakkisathFight& fight, uint64 now)
    {
        Creature* boss = fight.Boss();
        for (SquadRec& squad : _squads)
        {
            std::vector<Creature*> alive;
            for (ObjectGuid const& guid : squad.soldiers)
                if (Creature* c = ObjectAccessor::GetCreature(*boss, guid))
                    if (c->IsAlive())
                        alive.push_back(c);
            if (alive.empty())
                continue;
            if (!squad.arrivedMs)
            {
                for (Creature* c : alive)
                    if (InRoom(PlaneOf(c), c->GetPositionZ()))
                    {
                        squad.arrivedMs = std::max<uint64>(now, 1);
                        squad.nextChargeMs = now + kShieldChargeFirstMs;
                        fight.Log("army-squad-arrived", Acore::StringFormat("n={} kind={}", squad.index + 1,
                            SquadName(squad.kind)));
                        break;
                    }
                continue;
            }
            if (squad.kind != SquadKind::ShieldWall || now < squad.nextChargeMs)
                continue;
            // The next living Guard in turn that is free (not mid-cast).
            Creature* charger = nullptr;
            for (std::size_t i = 0; i < alive.size() && !charger; ++i)
            {
                Creature* c = alive[(squad.chargeTurn + i) % alive.size()];
                if (!c->HasUnitState(UNIT_STATE_CASTING) && c->GetVictim())
                    charger = c;
            }
            if (!charger || !ShieldCharge(fight, charger))
            {
                squad.nextChargeMs = now + 1000;    // retry
                continue;
            }
            ++squad.chargeTurn;
            squad.nextChargeMs = now + kShieldChargeEveryMs;
        }
    }

    // DR15 Shield Charge: a 2 s wind-up toward a random player, a 4 yd lane 25 yd long, then the run; everyone hit is
    // knocked 5 yd aside.
    bool ShieldCharge(DrakkisathFight& fight, Creature* guard)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.exclude = DuelExcluded();      // never aimed at the challenger inside the ring (R-2 M-3)
        Player* target = DungeonKit::PickPlayer(guard, rule);
        if (!target)
            return false;
        float const facing = guard->GetAbsoluteAngle(target);
        Position const start(guard->GetPositionX(), guard->GetPositionY(), guard->GetPositionZ(), facing);
        guard->SetFacingTo(facing);
        DungeonKit::CastBar(guard, SPELL_GA_SHIELD_CHARGE_BAR);
        float const pct = kShieldChargePct * CommandScale(Commanded(guard));
        MechanicRef ref = Mechanic::Line(guard, BossMechanics::Anchor(start), facing, kShieldChargeLength,
            kShieldChargeWidth, Ms(kShieldChargeCastMs));
        Vec2 const from = PlaneOf(guard);
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_GA_SHIELD_CHARGE).Weakened()
            .Within(fight.RoomBounds()).Tag(TAG_GA_SHIELD_CHARGE);
        ExcludeChallenger(fight, ref);
        // The 5 yd knock aside never throws the challenger (a duel that starts during the wind-up included) across
        // the lethal ring: only stepping out kills them (wave 2 ruling; R-2 M-3).
        ref.OnHit(OnArmy([from, facing](GeneralsArmy& army, DrakkisathFight&, Unit* hit)
        {
            if (!hit->IsAlive() || army.InDuel(hit))
                return;
            Vec2 const src = KnockSource(from, facing, PlaneOf(hit));
            hit->KnockbackFrom(src.x, src.y, DungeonKit::PushSpeedXY(kShieldChargeKnockYd, kShieldChargeKnockSpeedZ),
                kShieldChargeKnockSpeedZ);
        }));
        Map* map = _map;
        ObjectGuid const guid = guard->GetGUID();
        ref.OnResolve([map, guid, from, facing](BossMechanics::ResolveResult const&)
        {
            Creature* g = map ? map->GetCreature(guid) : nullptr;
            if (!g || !g->IsAlive())
                return;
            // The run: the lane's length, short of the hall's wall when the lane leaves it.
            float length = kShieldChargeLength;
            if (DungeonKit::PointInPolygon(BrsDrakkisath::kHallBox, from))
                if (std::optional<float> wall = DungeonKit::RayToPolygonEdge(BrsDrakkisath::kHallBox, from, facing))
                    length = std::max(0.f, std::min(length, *wall - 1.f));
            Vec2 const end = DungeonKit::Advance(from, facing, length);
            g->InterruptNonMeleeSpells(false);      // the bar is over: nothing may hold the run
            g->GetMotionMaster()->MoveCharge(end.x, end.y, g->GetPositionZ(), kShieldChargeSpeed);
        });
        Keep(fight, ref.Handle());
        fight.Log("army-shield-charge", Acore::StringFormat("at={} pct={:.1f}", target->GetName(), pct));
        return true;
    }

    // ---- phase 1: no free damage window -----------------------------------------------------------------------------

    void Answer(DrakkisathFight& fight, Unit* attacker)
    {
        Creature* boss = fight.Boss();
        Position const at = attacker->GetPosition();
        MechanicRef ref = Mechanic::Circle(boss, at, kAnswerRadius, Ms(kAnswerWarnMs));
        ref.Damage(kAnswerPct).TankDamage(kAnswerPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_GA_FIRE_BLAST).Weakened()
            .Within(fight.RoomBounds()).Tag(TAG_GA_ANSWER);
        Keep(fight, ref.Handle());
        Later(fight, kAnswerWarnMs, [](GeneralsArmy&, DrakkisathFight& f)
        {
            f.Boss()->CastSpell(f.Boss(), SPELL_GA_FIRE_BLAST_LOOK, true);
        });
        fight.Log("army-answer", Acore::StringFormat("at={} dist={:.1f}", attacker->GetName(),
            boss->GetExactDist2d(attacker)));
    }

    // ---- DR17 the Champion's Call -----------------------------------------------------------------------------------

    void StartCall(DrakkisathFight& fight)
    {
        if (_call.active || _challenge.active || !_pendingChallenger.IsEmpty())
            return;
        Creature* boss = fight.Boss();
        float const facing = boss->GetVictim() ? boss->GetAbsoluteAngle(boss->GetVictim()) : boss->GetOrientation();
        Vec2 const spot = CallSpot(PlaneOf(boss), facing);
        _call = CallState();
        _call.active = true;
        _call.startMs = fight.FightMs();
        _call.spot = Position(spot.x, spot.y, FloorZ(_map, spot.x, spot.y, boss->GetPositionZ()), facing);
        boss->AI()->Talk(BrsDrakkisath::YELL_DR_CHALLENGE);
        // Humans first: for 2 s no bot may claim it (no player is eligible: the Soak's carriers name only him).
        BossMechanics::Eligibility nobody;
        nobody.carriers.insert(boss->GetGUID());
        nobody.playersOnly = true;
        _call.soak = RegisterCallSoak(fight, nobody, kCallMs);
        fight.Log("army-call", Acore::StringFormat("at=({:.1f},{:.1f}) soak={}", spot.x, spot.y, _call.soak ? 1 : 0));
    }

    MechanicHandle RegisterCallSoak(DrakkisathFight& fight, BossMechanics::Eligibility const& who, uint32 warnMs)
    {
        MechanicRef ref = Mechanic::Soak(fight.Boss(), BossMechanics::Anchor(_call.spot), kCallRadius, 1, Ms(warnMs));
        ref.Eligible(who).OneClaimPerBot().MissedSoak(BossMechanics::MissedSoakMode::Never).Within(fight.RoomBounds())
            .Tag(TAG_GA_CALL);
        MechanicHandle const handle = ref.Handle();
        Keep(fight, handle);
        return handle;
    }

    void UpdateCall(DrakkisathFight& fight, uint64 now)
    {
        if (!_call.active)
            return;
        Creature* boss = fight.Boss();
        Unit const* tank = boss->GetVictim();
        for (Player* p : fight.FightPlayers())
        {
            if (p == tank || !p->IsAlive())
                continue;
            if (p->GetExactDist2d(&_call.spot) > kCallRadius
                || std::fabs(p->GetPositionZ() - _call.spot.GetPositionZ()) > kCallZBand)
                continue;
            EndCall(fight);
            _pendingChallenger = p->GetGUID();
            fight.ScheduleCast(CAST_GA_CHALLENGE, 0, kChallengePriority);
            fight.Log("army-call-answered", Acore::StringFormat("by={} after={}ms", p->GetName(), now - _call.startMs));
            return;
        }
        if (!_call.botsMayClaim && now >= _call.startMs + kCallBotDelayMs)
        {
            // Nobody yet: the bots may claim it, any player but his tank.
            _call.botsMayClaim = true;
            Mechanic::Cancel(boss, _call.soak);
            BossMechanics::Eligibility who;
            who.playersOnly = true;
            for (Player* p : fight.FightPlayers())
                if (p != tank)
                    who.carriers.insert(p->GetGUID());
            if (who.carriers.empty())
                who.carriers.insert(boss->GetGUID());
            uint64 const left = _call.startMs + kCallMs > now ? _call.startMs + kCallMs - now : 1;
            _call.soak = RegisterCallSoak(fight, who, uint32(left));
            fight.Log("army-call-bots", Acore::StringFormat("eligible={}", who.carriers.size()));
        }
        if (now >= _call.startMs + kCallMs)
        {
            EndCall(fight);
            Reward(fight, ChallengeEnd::Unanswered);
        }
    }

    void EndCall(DrakkisathFight& fight)
    {
        if (!_call.active)
            return;
        if (_call.soak)
            Mechanic::Cancel(fight.Boss(), _call.soak);
        _call = CallState();
    }

    // ---- DR18 the Challenge -----------------------------------------------------------------------------------------

    bool ChallengerAlive(DrakkisathFight& fight) const
    {
        Player* ch = ObjectAccessor::GetPlayer(*fight.Boss(), _challenge.challenger);
        return ch && ch->IsAlive() && ch->GetMap() == fight.Boss()->GetMap();
    }

    bool StartChallenge(DrakkisathFight& fight)
    {
        Creature* boss = fight.Boss();
        ObjectGuid const guid = _pendingChallenger;
        _pendingChallenger.Clear();
        Player* challenger = ObjectAccessor::GetPlayer(*boss, guid);
        if (!challenger || !challenger->IsAlive() || challenger->GetMap() != boss->GetMap()
            || boss->GetExactDist2d(challenger) > kCallAheadYd + kCallRadius + 6.f)
        {
            fight.Log("army-challenge-refused", "the challenger is gone");
            Reward(fight, ChallengeEnd::ChallengerDied);
            return false;
        }
        ++_challenges;
        _challenge = ChallengeState();
        _challenge.active = true;
        _challenge.id = _challenges;
        _challenge.challenger = guid;
        _challenge.startMs = fight.FightMs();
        _challenge.target = WinDamage();
        _challenge.blows = PlanBlows([](uint32 n) { return n ? urand(0, n - 1) : 0u; });

        fight.SetRooted(true);
        boss->SetFacingToObject(challenger);
        DungeonKit::CastBar(boss, SPELL_GA_CHALLENGE_BAR);
        boss->CastSpell(challenger, SPELL_GA_CHALLENGER, true);

        Vec2 const centre = RingCentre(PlaneOf(boss), PlaneOf(challenger));
        DungeonKit::LethalRingSpec& ring = _challenge.ring;
        ring.center = Position(centre.x, centre.y, boss->GetPositionZ());
        ring.radius = kRingRadius;
        ring.width = kRingWidth;
        ring.killSpell = SPELL_GA_RING_STRIKE;
        ring.armAfter = Ms(kRingArmMs);
        ring.lifetime = Ms(kRingLifeMs);
        ring.pets = kRingStrikesPets;
        ring.keepIn = { guid };
        ring.spareKeepIn = kRingSparesChallenger;
        ring.tag = TAG_GA_RING;
        ring.carrierEntry = NPC_BRS_CHALLENGE_RING;
        ring.carrierAura = kRingLookSpell;
        ring.dungeon = kLogDungeon;
        ring.boss = "drakkisath";
        MechanicHandle const ringHandle = _rings.Add(boss, ring);
        fight.Track(ringHandle);

        for (uint32 k = 0; k < kBlows; ++k)
        {
            uint32 const id = _challenge.id;
            Later(fight, BlowStartMs(k), [id, k](GeneralsArmy& army, DrakkisathFight& f)
            {
                if (army._challenge.active && army._challenge.id == id)
                    army.Strike(f, k);
            });
        }
        fight.Log("army-challenge", Acore::StringFormat("challenger={} target={} centre=({:.1f},{:.1f}) ring={} "
            "blows={},{},{},{},{},{}", challenger->GetName(), _challenge.target, centre.x, centre.y, ringHandle ? 1 : 0,
            BlowName(_challenge.blows[0]), BlowName(_challenge.blows[1]), BlowName(_challenge.blows[2]),
            BlowName(_challenge.blows[3]), BlowName(_challenge.blows[4]), BlowName(_challenge.blows[5])));
        return true;
    }

    // Blow k: its telegraph now, aimed at the challenger where they stand; it lands kBlowWarnMs later.
    void Strike(DrakkisathFight& fight, uint32 k)
    {
        Creature* boss = fight.Boss();
        Player* challenger = ObjectAccessor::GetPlayer(*boss, _challenge.challenger);
        if (!challenger || !challenger->IsAlive())
            return;
        Blow const blow = _challenge.blows[k];
        BlowNumbers const n = NumbersOf(blow);
        float const pct = n.pct;    // his Trophies raise the hit itself (OnDamageDealt), as they do his own kit's
        boss->SetFacingToObject(challenger);
        float const facing = boss->GetAbsoluteAngle(challenger);
        Position const bossAt(boss->GetPositionX(), boss->GetPositionY(), boss->GetPositionZ(), facing);
        BossMechanics::Eligibility onlyChallenger;
        onlyChallenger.carriers.insert(_challenge.challenger);
        onlyChallenger.playersOnly = true;
        BossMechanics::SpotBounds const inside = DungeonKit::RingInside(_challenge.ring);
        uint32 const id = _challenge.id;
        auto decorate = [&](MechanicRef& ref)
        {
            ref.Damage(pct).TankDamage(pct).School(blow == Blow::FireBlast || blow == Blow::RingOfFlame
                ? SPELL_SCHOOL_FIRE : SPELL_SCHOOL_NORMAL).Spell(n.spell).Eligible(onlyChallenger).Within(inside)
                .Tag(TAG_GA_BLOW);
            if (n.weakened)
                ref.Weakened();
            ref.OnHit(OnArmy([id, k](GeneralsArmy& army, DrakkisathFight&, Unit* hit)
            {
                if (army._challenge.id == id && hit->GetGUID() == army._challenge.challenger)
                    army._challenge.hit[k] = true;
            }));
            _challenge.handles.push_back(ref.Handle());
            Keep(fight, ref.Handle());
        };
        switch (blow)
        {
            case Blow::Sweep:
            {
                MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Cone(bossAt, kSweepAngleDeg,
                    kSweepLength), Ms(kBlowWarnMs));
                decorate(ref);
                break;
            }
            case Blow::OverheadCleave:
            {
                MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Cone(bossAt, kCleaveAngleDeg,
                    kCleaveLength), Ms(kBlowWarnMs));
                decorate(ref);
                break;
            }
            case Blow::FireBlast:
            {
                Vec2 const centre{ _challenge.ring.center.GetPositionX(), _challenge.ring.center.GetPositionY() };
                for (Vec2 const& s : FireBlastSpots(PlaneOf(challenger), frand(0.f, 2.f * kPi), centre))
                {
                    MechanicRef ref = Mechanic::Circle(boss, ToPos(s, challenger->GetPositionZ()), kFireBlastRadius,
                        Ms(kBlowWarnMs));
                    decorate(ref);
                }
                break;
            }
            case Blow::RingOfFlame:
            {
                MechanicRef ref = Mechanic::Donut(boss, bossAt, kRingOfFlameInner, kRingOfFlameOuter,
                    Ms(kBlowWarnMs));
                decorate(ref);
                break;
            }
            case Blow::Thunderclap:
            {
                MechanicRef ref = Mechanic::Circle(boss, bossAt, kThunderclapRadius, Ms(kBlowWarnMs));
                decorate(ref);
                break;
            }
        }
        Later(fight, kBlowWarnMs, [id, blow](GeneralsArmy& army, DrakkisathFight& f)
        {
            if (!army._challenge.active || army._challenge.id != id)
                return;
            Creature* b = f.Boss();
            switch (blow)
            {
                case Blow::Sweep:
                case Blow::OverheadCleave:  b->CastSpell(b, BrsDrakkisath::SPELL_DR_SWEEP_LOOK, true); break;
                case Blow::Thunderclap:     b->CastSpell(b, BrsDrakkisath::SPELL_DR_THUNDERCLAP_LOOK, true); break;
                case Blow::FireBlast:       b->CastSpell(b, SPELL_GA_FIRE_BLAST_LOOK, true); break;
                case Blow::RingOfFlame:     b->CastSpell(b, SPELL_GA_RING_OF_FLAME_LOOK, true); break;
            }
        });
        Later(fight, kBlowWarnMs + kBlowJudgeMs, [id, k](GeneralsArmy& army, DrakkisathFight& f)
        {
            army.JudgeBlow(f, id, k);
        });
        fight.Log("army-blow", Acore::StringFormat("n={} kind={} pct={:.1f}", k + 1, BlowName(blow), pct));
    }

    // A blow has landed: avoided, +1 Finesse (up to 6).
    void JudgeBlow(DrakkisathFight& fight, uint32 id, uint32 k)
    {
        if (!_challenge.active || _challenge.id != id)
            return;
        Player* challenger = ObjectAccessor::GetPlayer(*fight.Boss(), _challenge.challenger);
        if (!challenger || !challenger->IsAlive())
            return;
        if (_challenge.hit[k])
        {
            fight.Log("army-blow-hit", Acore::StringFormat("n={} kind={}", k + 1, BlowName(_challenge.blows[k])));
            return;
        }
        uint32 const stacks = DungeonKit::AddStacks(challenger, SPELL_GA_FINESSE, 1, fight.Boss(), kFinesseMax);
        fight.Log("army-finesse", Acore::StringFormat("n={} kind={} stacks={}", k + 1, BlowName(_challenge.blows[k]),
            stacks));
    }

    void UpdateChallenge(DrakkisathFight& fight, uint64 now)
    {
        if (!_challenge.active)
            return;
        bool const timeUp = now >= _challenge.startMs + kChallengeMs;
        if (std::optional<ChallengeEnd> const end = JudgeChallenge(_challenge.damage, _challenge.target,
            ChallengerAlive(fight), timeUp))
            EndChallenge(fight, *end, false);
    }

    // The Challenge ends: the ring and the blows go, the challenger's marks go, he is unrooted; an early end stops his
    // bar (B14 ends the hold with it); then the reward (not on Aborted). `fightEnding`: from OnEnd (no interrupt).
    void EndChallenge(DrakkisathFight& fight, ChallengeEnd end, bool fightEnding)
    {
        if (!_challenge.active)
            return;
        Creature* boss = fight.Boss();
        _challenge.active = false;
        for (MechanicHandle const& handle : _challenge.handles)
            Mechanic::Cancel(boss, handle);
        _challenge.handles.clear();
        _rings.Clear(boss);
        if (Player* ch = ObjectAccessor::GetPlayer(*boss, _challenge.challenger))
        {
            ch->RemoveAurasDueToSpell(SPELL_GA_CHALLENGER);
            ch->RemoveAurasDueToSpell(SPELL_GA_FINESSE);
        }
        if (!fightEnding)
        {
            if (boss->HasUnitState(UNIT_STATE_CASTING))
            {
                _ending = true;
                boss->InterruptNonMeleeSpells(false);
                _ending = false;
            }
            fight.SetRooted(!_field);       // phase 1 (a GM test) keeps him in his alcove
        }
        fight.Log("army-challenge-end", Acore::StringFormat("end={} damage={}/{} after={}ms", ChallengeEndName(end),
            _challenge.damage, _challenge.target, fight.FightMs() - _challenge.startMs));
        Reward(fight, end);
    }

    void Reward(DrakkisathFight& fight, ChallengeEnd end)
    {
        Creature* boss = fight.Boss();
        if (end == ChallengeEnd::Won)
        {
            ++_won;
            boss->CastSpell(boss, SPELL_GA_HUMBLED, true);
            boss->AI()->Talk(BrsDrakkisath::YELL_DR_CHALLENGE_WON);
            fight.Log("army-humbled");
            return;
        }
        if (!GivesTrophy(end))
            return;
        _trophies = DungeonKit::AddStacks(boss, SPELL_GA_TROPHY, 1, boss, kTrophyMax);
        boss->AI()->Talk(end == ChallengeEnd::Unanswered ? BrsDrakkisath::YELL_DR_COWARDS
            : BrsDrakkisath::YELL_DR_CHALLENGE_LOST);
        fight.Log("army-trophy", Acore::StringFormat("why={} trophies={}", ChallengeEndName(end), _trophies));
    }

    uint32 const _serial;
    Map* _map = nullptr;
    ObjectGuid _bossGuid;
    uint8 _players = 0;
    uint32 _baseHealth = 0;
    bool _field = false;
    bool _ending = false;
    uint32 _nextSquad = 0;
    std::vector<SquadRec> _squads;
    CallState _call;
    ObjectGuid _pendingChallenger;
    ChallengeState _challenge;
    DungeonKit::LethalRings _rings;
    uint32 _challenges = 0;
    uint32 _won = 0;
    uint32 _trophies = 0;
    std::map<ObjectGuid, uint64> _answerAt;
    std::vector<MechanicHandle> _live;
    std::vector<Pending> _pending;
};

// The squad soldiers 300736-300739 (Rage Talon copies): melee, their stock strikes on their own clock from the moment
// they reach the hall, and the hard mode's moves through GeneralsArmy. Every fight player sits on their threat list (at
// 0), so a fixated or kept soldier never evades when its target dies, feigns or vanishes (wave 2 lesson 5).
struct npc_brs_army_soldier : public ScriptedAI
{
    explicit npc_brs_army_soldier(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _clockMs = 0;
        _arrived = false;
    }

    // From GeneralsArmy::MarchSquad, right after the summon.
    void Muster(std::vector<Player*> const& players)
    {
        for (Player* p : players)
            if (p && p->IsAlive())
                me->GetThreatMgr().AddThreat(p, 0.f, nullptr, true, true);
        if (players.empty())
            return;
        Player* first = players[urand(0, uint32(players.size()) - 1)];
        if (me->GetEntry() == NPC_BRS_SQUAD_DRAGONSPAWN)
        {
            // DR13: fixated on a random player (a new one when it dies), its own run speed.
            DungeonKit::ChaserSpec spec;
            spec.speed = 0.f;
            spec.endOnArrive = false;
            spec.fixate = true;
            spec.tauntImmune = true;
            spec.pick.nonTank = false;
            if (_chase.Start(me, first, std::move(spec), me))
                return;
        }
        me->AddThreat(first, 1.f);
        AttackStart(first);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _chase.Stop(me);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _chase.Stop(me);
        ScriptedAI::EnterEvadeMode(why);
        me->DespawnOrUnsummon(1s);      // a soldier is the fight's: it never walks back to a spawn point
    }

    // DR15: the Dragon Guard's shield takes half from the front.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (attacker && damage && me->GetEntry() == NPC_BRS_SQUAD_DRAGON_GUARD)
            damage = ShieldFrontDamage(damage, me->GetOrientation(), me->GetAbsoluteAngle(attacker));
    }

    void UpdateAI(uint32 diff) override
    {
        if (_chase.Active())
            _chase.Update(me, diff);
        if (!UpdateVictim())
            return;
        if (!_arrived)
        {
            if (InRoom(PlaneOf(me), me->GetPositionZ()))
                Arrive();
        }
        else
        {
            _clockMs += diff;
            RunMoves();
        }
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

private:
    void Arrive()
    {
        _arrived = true;
        _clockMs = 0;
        switch (me->GetEntry())
        {
            case NPC_BRS_SQUAD_DRAGONSPAWN:
                _nextA = kCleavingChargeFirstMs;
                break;
            case NPC_BRS_SQUAD_CAPTAIN:
                _nextA = kArcingSmashFirstMs;
                _nextB = kMortalStrikeFirstMs;
                _nextC = 0;             // the command at once
                _nextD = 0;
                break;
            case NPC_BRS_SQUAD_FIRE_TONGUE:
                _nextA = kScatteringFirstMs;
                _nextB = kVolleyFirstMs;
                break;
            case NPC_BRS_SQUAD_DRAGON_GUARD:
                _nextA = kShieldSlamFirstMs;
                break;
            default:
                break;
        }
    }

    void RunMoves()
    {
        if (me->GetEntry() == NPC_BRS_SQUAD_CAPTAIN)
            Command();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Unit* victim = me->GetVictim();
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = GeneralsArmy::FindFor(me, &fight);
        switch (me->GetEntry())
        {
            case NPC_BRS_SQUAD_DRAGONSPAWN:
                if (_clockMs >= _nextA && army && army->CleavingCharge(*fight, me))
                    _nextA = _clockMs + kCleavingChargeEveryMs;
                break;
            case NPC_BRS_SQUAD_CAPTAIN:
                if (_clockMs >= _nextA && victim && me->IsWithinMeleeRange(victim))
                {
                    DoCastVictim(SPELL_GA_ARCING_SMASH);
                    _nextA = _clockMs + kArcingSmashEveryMs;
                }
                else if (_clockMs >= _nextB && victim && me->IsWithinMeleeRange(victim))
                {
                    DoCastVictim(SPELL_GA_MORTAL_STRIKE);
                    _nextB = _clockMs + kMortalStrikeEveryMs;
                }
                break;
            case NPC_BRS_SQUAD_FIRE_TONGUE:
                if (_clockMs >= _nextA && army && army->ScatteringFlame(*fight, me))
                    _nextA = _clockMs + kScatteringEveryMs;
                else if (_clockMs >= _nextB && me->CastSpell(me, SPELL_GA_FIREBALL_VOLLEY, false) == SPELL_CAST_OK)
                {
                    _nextB = _clockMs + kVolleyEveryMs;
                    Mechanic::NoteNextCastIn(me, SPELL_GA_FIREBALL_VOLLEY, Ms(kVolleyEveryMs));
                }
                break;
            case NPC_BRS_SQUAD_DRAGON_GUARD:
                if (_clockMs >= _nextA && victim && me->IsWithinMeleeRange(victim))
                {
                    DoCastVictim(SPELL_GA_SHIELD_SLAM);
                    _nextA = _clockMs + kShieldSlamEveryMs;
                }
                break;
            default:
                break;
        }
    }

    // DR13: every second, the command on every other living soldier within 10 yd (a 2 s aura); its look every 5 s.
    void Command()
    {
        if (_clockMs < _nextC)
            return;
        _nextC = _clockMs + kCommandRefreshMs;
        std::list<Creature*> near;
        for (uint32 entry : { uint32(NPC_BRS_SQUAD_DRAGONSPAWN), uint32(NPC_BRS_SQUAD_CAPTAIN),
            uint32(NPC_BRS_SQUAD_FIRE_TONGUE), uint32(NPC_BRS_SQUAD_DRAGON_GUARD) })
            me->GetCreatureListWithEntryInGrid(near, entry, kCommandRadius);
        for (Creature* soldier : near)
            if (soldier != me && soldier->IsAlive())
                me->CastSpell(soldier, SPELL_GA_COMMAND, true);
        if (_clockMs >= _nextD)
        {
            _nextD = _clockMs + kCommandLookEveryMs;
            me->CastSpell(me, SPELL_GA_COMMAND_LOOK, true);
        }
    }

    DungeonKit::Chaser _chase;
    uint64 _clockMs = 0;            // ms since it reached the hall
    uint64 _nextA = 0;
    uint64 _nextB = 0;
    uint64 _nextC = 0;
    uint64 _nextD = 0;
    bool _arrived = false;
};

void GeneralsArmy::MusterSoldier(Creature* soldier, std::vector<Player*> const& players)
{
    if (soldier && soldier->IsAIEnabled)
        if (auto* ai = dynamic_cast<npc_brs_army_soldier*>(soldier->AI()))
            ai->Muster(players);
}

// The black dragonkin herald 300740 (DR11; a heroic-only spawn at the throne room's south entrance). Neutral, never in
// combat; shown, placed and given its gossip by the instance's state every second (DrakkisathHardModeLogic.h
// HeraldPlaceFor): the entrance while the insult is saved and he waits, the alcove once armed, hidden otherwise.
struct npc_brs_generals_herald : public ScriptedAI
{
    explicit npc_brs_generals_herald(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        _pollMs = 0;
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kHeraldPollMs;
        InstanceScript* instance = me->GetInstanceScript();
        HeraldPlace const place = instance ? HeraldPlaceFor(me->GetMap()->IsHeroic(),
            instance->GetData(DATA_NEF_INSULTED) != 0, instance->GetBossState(BOSS_DRAKKISATH),
            instance->GetData(DATA_GENERALS_ARMY) != 0) : HeraldPlace::Hidden;
        Show(place);
    }

    void sGossipSelect(Player* player, uint32 menuId, uint32 gossipListId) override
    {
        if (menuId != kHeraldGossipMenu || gossipListId != kHeraldGossipOption)
            return;
        CloseGossipMenuFor(player);
        if (Arm(me, player) != HeraldRefusal::None)
            return;
        Talk(SAY_HERALD_ARMED, player);
        _pollMs = 0;    // run to the alcove now
    }

private:
    void Show(HeraldPlace place)
    {
        bool const hidden = place == HeraldPlace::Hidden;
        // Placed first (a hidden herald coming back appears at its spot): the run to the alcove when armed in sight,
        // else a step to the spot.
        if (!hidden && place != _place)
        {
            Point3 const& to = place == HeraldPlace::Alcove ? kHeraldAlcove : kHeraldEntrance;
            float const facing = place == HeraldPlace::Alcove ? kHeraldAlcoveFacing : kHeraldEntranceFacing;
            if (!_hidden && _place == HeraldPlace::Entrance && place == HeraldPlace::Alcove)
                me->GetMotionMaster()->MovePoint(1, to.x, to.y, to.z, FORCED_MOVEMENT_RUN, 0.f, facing);
            else
                me->NearTeleportTo(to.x, to.y, to.z, facing);
            _place = place;
        }
        if (hidden != _hidden)
        {
            _hidden = hidden;
            me->SetVisible(!hidden);
            if (hidden)
                me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            else
                me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }
        // The gossip only at the entrance (the option's conditions agree).
        if (place == HeraldPlace::Entrance)
            me->SetNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        else
            me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
    }

    uint32 _pollMs = 0;
    bool _hidden = false;
    HeraldPlace _place = HeraldPlace::Entrance;
};

// The Champion's Challenge ring's carrier 300741 (the kit's LethalRing summons it and casts the look on it): passive.
struct npc_brs_challenge_ring : public ScriptedAI
{
    explicit npc_brs_challenge_ring(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// DR14 Fireball Volley 210582: the cast landed (an interrupted cast never reaches AfterCast).
class spell_brs_army_fireball_volley : public SpellScript
{
    PrepareSpellScript(spell_brs_army_fireball_volley);

    void Landed()
    {
        Creature* tongue = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!tongue || !tongue->IsAlive())
            return;
        DrakkisathFight* fight = nullptr;
        if (GeneralsArmy* army = GeneralsArmy::FindFor(tongue, &fight))
            army->VolleyLanded(*fight, tongue);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_brs_army_fireball_volley::Landed);
    }
};

namespace
{
    // The running pull's hard mode (an error and nullptr when there is none).
    GeneralsArmy* FindArmy(ChatHandler* handler, DrakkisathFight*& fight)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_DRAKKISATH);
        if (!boss)
            return nullptr;
        fight = FightOf(boss);
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Drakkisath is not running boss_drakkisath_rework.");
            return nullptr;
        }
        auto* army = dynamic_cast<GeneralsArmy*>(fight->ActiveHardMode());
        if (!army)
            handler->SendErrorMessage("{}", "No hard mode pull is running (insult Nefarius, answer the herald on "
                "heroic, then pull him).");
        return army;
    }

    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        bool const heroic = handler->GetPlayer()->GetMap()->IsHeroic();
        HeraldPlace const place = HeraldPlaceFor(heroic, instance->GetData(DATA_NEF_INSULTED) != 0,
            instance->GetBossState(BOSS_DRAKKISATH), instance->GetData(DATA_GENERALS_ARMY) != 0);
        handler->PSendSysMessage("army: flag {}, insult {}, kill {}, boss {}, heroic {}, herald {}",
            instance->GetData(DATA_GENERALS_ARMY), instance->GetData(DATA_NEF_INSULTED),
            DungeonTest::StateName(instance->GetBossState(BOSS_GENERALS_ARMY)),
            DungeonTest::StateName(instance->GetBossState(BOSS_DRAKKISATH)), heroic ? 1 : 0,
            place == HeraldPlace::Hidden ? "hidden" : place == HeraldPlace::Entrance ? "entrance" : "alcove");
        return true;
    }

    // `.dbtest brs army arm`: "Let them come" as a player answers it (the same refusals), from the GM.
    bool HandleArm(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        Player* gm = Gm(handler);
        HeraldRefusal const r = Arm(gm, gm);
        if (r != HeraldRefusal::None)
        {
            handler->SendErrorMessage("{}", HeraldRefusalText(r));
            return false;
        }
        handler->PSendSysMessage("{}", "The general's legions answer: the next pull is the hard mode (DR11).");
        return true;
    }

    // `.dbtest brs army clear`: puts the flag out (refused while he fights).
    bool HandleClear(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        instance->SetData(DATA_GENERALS_ARMY, 0);
        handler->PSendSysMessage("army: flag {}", instance->GetData(DATA_GENERALS_ARMY));
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = FindArmy(handler, fight);
        if (!army)
            return false;
        handler->PSendSysMessage("army: {}", army->TestState(*fight));
        return true;
    }

    // `.dbtest brs army squad <n>`: squad n (1-based, the drill's order) marches in now.
    bool HandleSquad(ChatHandler* handler, uint32 n)
    {
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = FindArmy(handler, fight);
        if (!army || !n)
            return false;
        army->TestSquad(*fight, n - 1);
        handler->PSendSysMessage("army: squad {} ({}) marches in.", n, SquadName(PlanSquad(n - 1).kind));
        return true;
    }

    // `.dbtest brs army field`: phase 2 now (DR16).
    bool HandleField(ChatHandler* handler)
    {
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = FindArmy(handler, fight);
        if (!army)
            return false;
        army->TestField(*fight);
        handler->PSendSysMessage("{}", "army: the general takes the field (DR16).");
        return true;
    }

    // `.dbtest brs army call`: the Champion's Call now (DR17).
    bool HandleCall(ChatHandler* handler)
    {
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = FindArmy(handler, fight);
        if (!army)
            return false;
        army->TestCall(*fight);
        handler->PSendSysMessage("{}", "army: the Champion's Call (DR17).");
        return true;
    }

    // `.dbtest brs army challenge`: the selected player (or you) is the challenger now (DR18).
    bool HandleChallenge(ChatHandler* handler)
    {
        DrakkisathFight* fight = nullptr;
        GeneralsArmy* army = FindArmy(handler, fight);
        Player* target = handler->getSelectedPlayer() ? handler->getSelectedPlayer() : Gm(handler);
        if (!army || !target)
            return false;
        bool const ok = army->TestChallenge(*fight, target);
        handler->PSendSysMessage("army: {} {}.", target->GetName(), ok ? "is challenged (queued, DR18)"
            : "cannot be challenged now (a Challenge runs)");
        return ok;
    }

    ChatCommandTable const& GeneralsArmyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "arm",       HandleArm,       SEC_GAMEMASTER, Console::No },
            { "clear",     HandleClear,     SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "squad",     HandleSquad,     SEC_GAMEMASTER, Console::No },
            { "field",     HandleField,     SEC_GAMEMASTER, Console::No },
            { "call",      HandleCall,      SEC_GAMEMASTER, Console::No },
            { "challenge", HandleChallenge, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brs_drakkisath_hard_mode()
{
    BrsDrakkisath::RegisterDrakkisathHardMode([](Creature*) { return std::make_unique<GeneralsArmy>(); });
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_army_soldier, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_generals_herald, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brs_challenge_ring, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_army_fireball_volley);
    BrsTest::RegisterBoss(kLogKey, GeneralsArmyTestCommands());
}
