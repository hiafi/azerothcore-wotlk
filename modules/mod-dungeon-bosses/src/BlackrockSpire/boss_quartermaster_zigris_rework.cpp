/*
 * mod-dungeon-bosses, Blackrock Spire B6: Quartermaster Zigris (9736), "a quartermaster who fights out of his own
 * stores". Build spec: docs/dungeons/blackrock-spire-rework.md "Quartermaster Zigris" (SP 1690-1903, ZG1-ZG8, rulings
 * 40-43), handoff section 3.4 rows ZG, 3.5 row B6, 3.6, 3.8 (the ledge and its three crate spots), the KT-B1 chaser
 * (the sheep). Replaces the stock boss_quartermaster_zigris (Stun Bomb, Hooked Net, the healing potion, which have no
 * rows to drop: the stock boss is C++ only); bound by apps/dbc-tools source/npcs/blackrock_spire/zigris.py. Pure rules:
 * ZigrisLogic.h.
 *
 *   ZG1 Net Traps    at 8 s, then every 15 s: a trap at the spot of each of 2 random non-tanks (4 at 6 or more), and
 *                    2 where he stands at every Fall Back. A registry Mine (3 yd, armed after 1 s, grace 0.5 s) with a
 *                    bear trap object on it: sprung it is 20% (heroic 25%) + Weakened + a 2 s root, and gone;
 *                    unsprung it lasts 60 s; at most 8 (12 at 6 or more), heroic 10 (14), the oldest snaps shut
 *   ZG2 Fall Back    at 20 s, then every 20 s (heroic 15 / 15): the smoke bomb at his feet, a leap to the next of his 3
 *                    supply crates in turn, 2 traps where he stood; he shoots from the crate until the tank arrives
 *   ZG3 Restock      each landing adds a gadget for the fight: crate 1 the Powder Keg (emote 2), crate 2 the Mortar
 *                    (emote 3), crate 3 the sheep on heroic (emote 4), later landings nothing
 *   ZG4 Powder Keg   from 4 s after the first restock, every 20 s: a lit keg at a random non-tank's spot, a 10 yd
 *                    blast after a 4 s fuse, 30% (heroic 40%) + Weakened + a 2 s stun. One keg at every size
 *   ZG5 Mortar       from 3 s after the second restock, every 7 s: 3 shells (6 at 6 or more), 1 s apart, each at one
 *                    of the farthest non-tanks, from the second crate: 5 yd, 2 s flight, 25% (heroic 30%) + Weakened
 *   ZG6 Explosive    heroic, from 3 s after the third restock, every 20 s: a clockwork sheep at a random non-tank (2 at
 *       Sheep        6 or more), chasing at 5 yd/s (the kit Chaser: stops 1 s on a toss or a stun, honors slows); it
 *                    explodes on reaching its target or after 10 s (8 yd, 35% + Weakened), and when it walks over a
 *                    Net Trap, which it springs; kill it (3,000 health) and it does not
 *   ZG7 Shoot        stock 16496 at his target every 2 s while it is out of melee and in sight; he does not chase
 *   ZG8 Reset        evade or wipe: traps, kegs, sheep and the stalkers go, the restocks reset
 *
 * Boss data: kill order the sheep (ranged first), then him; no interrupts, no dispels. Every timer runs on the AI's
 * own clock, never on BossAI's scheduler. Every firing logs one INFO line "brs zigris <mechanic> ..."
 * (module.dungeonbosses); `.dbtest brs zigris ...` fires one mechanic on demand.
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
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZigrisLogic.h"
#include <algorithm>
#include <functional>
#include <memory>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsZigris;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "zigris";

    // The trap object's animations (G_BearTrap: open 145, trigger 147, close 148; VISUALS report, unconfirmed in game).
    uint32 constexpr kTrapAnimOpen = 145;
    uint32 constexpr kTrapAnimTrigger = 147;
    uint32 constexpr kTrapAnimClose = 148;
    uint32 constexpr kTrapCloseLingerMs = 500;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    DungeonKit::Vec2 ToVec(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    // The generic stalker 300713 (the keg's fuse, the mortar's launch point) is the orchestrator's template: without it
    // those looks are skipped, never an error line per keg.
    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRS_STALKER) != nullptr;
    }

    // A script-placed object lives this long as its own backstop (the script deletes it earlier).
    uint32 BackstopSecs(uint32 lifeMs)
    {
        return lifeMs / 1000 + 2;
    }
}

// Quartermaster Zigris 9736
struct boss_quartermaster_zigris_rework : public BossAI
{
    explicit boss_quartermaster_zigris_rework(Creature* creature)
        : BossAI(creature, BOSS_ZIGRIS), _arena(ZigrisArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        me->SetCombatMovement(false);   // he stands and shoots (stock)
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ZIGRIS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        bool const heroic = IsHeroicMap(me);
        Talk(TEXT_PULL);
        _trapsClock.Start(_clockMs, kTrapsFirstMs);
        _fallBackClock.Start(_clockMs, kFallBackFirstMs(heroic));
        _shootClock.Start(_clockMs, 1000);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} at=({:.1f}, {:.1f}, {:.1f})", heroic ? 1 : 0, _players,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(TEXT_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("falls={} landings={} traps={} killer={}", _falls, _landings, _trapsPlaced,
                killer ? killer->GetName() : "none"));
        Cleanup();
    }

    // Stalkers and sheep are his summons (they go with his reset and death) but never zone into his fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // A sheep killed (or put down) before it blew up does nothing: its zone and the bots' keep-away go.
    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (summon->GetEntry() == NPC_BRS_CLOCKWORK_SHEEP)
            SheepGone(summon->GetGUID(), "killed");
        BossAI::SummonedCreatureDies(summon, killer);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_BRS_CLOCKWORK_SHEEP)
            SheepGone(summon->GetGUID(), nullptr);
        BossAI::SummonedCreatureDespawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        // The delayed looks and object closings run in or out of combat (a `.dbtest` mechanic out of combat too).
        _clockMs += diff;
        UpdateLater();
        if (!UpdateVictim())
            return;

        bool const heroic = IsHeroicMap(me);
        UpdateSheep(diff);

        // The leap's arc climbs past the arena's band: the guard waits for the landing.
        if (!_landing && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_landing && _clockMs >= _landAtMs)
            Land(heroic);
        if (!_landing)
            UpdateBeats(heroic);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats(bool heroic)
    {
        if (_trapsClock.Due(_clockMs))
        {
            _trapsClock.Fired(_clockMs, kTrapsEveryMs);
            NetTraps();
        }
        if (_fallBackClock.Due(_clockMs))
        {
            _fallBackClock.Fired(_clockMs, kFallBackEveryMs(heroic));
            FallBack();
            return;     // in the air: nothing else fires until he lands
        }
        if (_kegClock.Due(_clockMs))
        {
            _kegClock.Fired(_clockMs, kKegEveryMs);
            PowderKeg(nullptr);
        }
        if (_mortarClock.Due(_clockMs))
        {
            _mortarClock.Fired(_clockMs, kMortarEveryMs);
            Mortar();
        }
        if (_sheepClock.Due(_clockMs))
        {
            _sheepClock.Fired(_clockMs, kSheepEveryMs);
            ReleaseSheep(nullptr);
        }
        if (_shootClock.Due(_clockMs))
        {
            _shootClock.Fired(_clockMs, kShootEveryMs);
            Shoot();
        }
    }

    // ZG7 stock Shoot: at his target while it is out of melee and in sight; out of sight he walks after it until he
    // sees it again (the stock script's rule).
    void Shoot()
    {
        Unit* victim = me->GetVictim();
        if (!victim || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!me->IsWithinLOSInMap(victim))
        {
            me->SetCombatMovement(true);
            me->GetMotionMaster()->MoveChase(victim);
            return;
        }
        if (!me->IsWithinMeleeRange(victim))
        {
            DoCastVictim(SPELL_ZG_SHOOT);
            me->SetCombatMovement(false);
            me->GetMotionMaster()->Clear();
        }
        else if (me->IsCombatMovementAllowed())
        {
            // In sight again: the line-of-sight chase ends with the combat movement (R-1-B n2).
            me->SetCombatMovement(false);
            me->GetMotionMaster()->Clear();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZG1 Net Traps
    // ----------------------------------------------------------------------------------------------------------------

    // The toss: a trap at the spot of each picked non-tank (`forced` = that player only: the `.dbtest` entry).
    void NetTraps(Player* forced = nullptr)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            targets = DungeonKit::PickPlayers(me, rule, kTossTargets.At(_players));
        }
        std::string who;
        for (Player* player : targets)
        {
            PlaceTrap(player->GetPosition());
            who += (who.empty() ? "" : ",") + player->GetName();
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "traps",
            Acore::StringFormat("count={} live={} targets={}", targets.size(), _traps.size(), who));
    }

    // One trap at `at`: the object, and the registry's Mine (the hitbox, the arming, the hit, the cap).
    void PlaceTrap(Position const& at)
    {
        bool const heroic = IsHeroicMap(me);
        float const x = at.GetPositionX();
        float const y = at.GetPositionY();
        float const z = at.GetPositionZ();
        Position const pos(x, y, z, 0.f);

        Trap trap;
        trap.pos = pos;
        if (GameObject* go = me->SummonGameObject(GO_BRS_NET_TRAP, x, y, z, frand(0.f, DungeonKit::kTwoPi), 0.f, 0.f,
                0.f, 0.f, BackstopSecs(kTrapLifeMs)))
            trap.go = go->GetGUID();

        MechanicRef ref = Mechanic::Mine(me, pos, kTrapRadius, Ms(kTrapArmMs), Ms(kTrapGraceMs));
        ref.Lifetime(Ms(kTrapLifeMs)).Cap(kTrapCapGroup, TrapCap(heroic, _players)).Damage(kTrapPct(heroic))
            .Spell(SPELL_ZG_NET_TRAP).Weakened().Rider(SPELL_ZG_NETTED).Tag(TAG_TRAPS);
        ref.OnResolve(OnZigris([](boss_quartermaster_zigris_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.TrapDone(r);
        }));
        trap.id = ref.Handle().id;
        if (!trap.id)
        {
            DeleteObject(trap.go);
            return;
        }
        ++_trapsPlaced;
        // The trap opens as the Mine arms.
        ObjectGuid const goGuid = trap.go;
        _traps.push_back(trap);
        Later(kTrapArmMs, [this, goGuid]() { PlayObjectAnim(goGuid, kTrapAnimOpen); });
    }

    // A trap's Mine is done: sprung (the object closes on its prey), or snapped shut harmlessly (the cap, the 60 s).
    void TrapDone(BossMechanics::ResolveResult const& result)
    {
        auto it = std::find_if(_traps.begin(), _traps.end(),
            [&result](Trap const& t) { return t.id == result.mechanicId; });
        if (it == _traps.end())
            return;
        ObjectGuid const goGuid = it->go;
        Position const pos = it->pos;
        _traps.erase(it);
        if (result.fizzled)
        {
            PlayObjectAnim(goGuid, kTrapAnimClose);
            _closing.push_back(goGuid);
            Later(kTrapCloseLingerMs, [this, goGuid]() { DeleteGadget(goGuid); });
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "trap-snapped",
                Acore::StringFormat("at=({:.1f}, {:.1f}) live={}", pos.GetPositionX(), pos.GetPositionY(),
                    _traps.size()));
            return;
        }
        PlayObjectAnim(goGuid, kTrapAnimTrigger);
        _closing.push_back(goGuid);
        Later(kTrapSpringLingerMs, [this, goGuid]() { DeleteGadget(goGuid); });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "trap-sprung",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={} live={}", pos.GetPositionX(), pos.GetPositionY(),
                result.hits.size(), _traps.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZG2 Fall Back, ZG3 Restock
    // ----------------------------------------------------------------------------------------------------------------

    void FallBack()
    {
        Position const from = me->GetPosition();
        Point3 const spot = CrateSpot(CrateFor(_falls));
        float const facing = DungeonKit::BearingTo(ToVec(from), spot.XY());

        Talk(TEXT_FALL_BACK);
        me->CastSpell(me, SPELL_ZG_SMOKE_BOMB, true);
        for (DungeonKit::Vec2 const& p : FallBackTrapSpots(ToVec(from), facing))
            PlaceTrap(Position(p.x, p.y, from.GetPositionZ(), 0.f));
        me->CastSpell(me, SPELL_ZG_LEAP, true);

        float const dist = DungeonKit::Distance(ToVec(from), spot.XY());
        // A line-of-sight chase must not resume under the leap and walk him off his crate (R-1-B n2).
        me->SetCombatMovement(false);
        me->GetMotionMaster()->Clear();
        DungeonKit::JumpTo(me, Position(spot.x, spot.y, spot.z, facing), kLeapSpeedYdPerSec);
        _landing = true;
        _landAtMs = _clockMs + LeapMs(dist);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fall-back",
            Acore::StringFormat("fall={} crate={} to=({:.1f}, {:.1f}, {:.1f}) dist={:.1f} traps={}", _falls + 1,
                CrateFor(_falls) + 1, spot.x, spot.y, spot.z, dist, _traps.size()));
        ++_falls;
    }

    // He is on the crate: the restock adds this landing's gadget (ZG3), and he turns to his target.
    void Land(bool heroic)
    {
        _landing = false;
        ++_landings;
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
        Restock const restock = RestockFor(_landings, heroic);
        RunRestock(restock, heroic);
        if (restock.text >= 0)
            Talk(static_cast<uint8>(restock.text));
        _shootClock.Start(_clockMs, 500);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "restock",
            Acore::StringFormat("landing={} gadget={} at=({:.1f}, {:.1f})", _landings, GadgetName(restock.gadget),
                me->GetPositionX(), me->GetPositionY()));
    }

    void RunRestock(Restock const& restock, bool heroic)
    {
        switch (restock.gadget)
        {
            case Gadget::PowderKeg:
                _kegClock.Start(_clockMs, kKegFirstAfterMs);
                break;
            case Gadget::Mortar:
                _mortarClock.Start(_clockMs, kMortarFirstAfterMs);
                EnsureMortarStalker();
                break;
            case Gadget::Sheep:
                if (heroic)
                    _sheepClock.Start(_clockMs, kSheepFirstAfterMs);
                break;
            case Gadget::None:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZG4 Powder Keg
    // ----------------------------------------------------------------------------------------------------------------

    // A lit keg at a random non-tank's spot (`forced` = that player: the `.dbtest` entry): the keg object, the fuse's
    // stalker, and a 10 yd circle that resolves after the 4 s fuse.
    void PowderKeg(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return;
        bool const heroic = IsHeroicMap(me);
        Position const pos = target->GetPosition();
        float const x = pos.GetPositionX();
        float const y = pos.GetPositionY();
        float const z = pos.GetPositionZ();

        ObjectGuid keg;
        if (GameObject* go = me->SummonGameObject(GO_BRS_POWDER_KEG, x, y, z, frand(0.f, DungeonKit::kTwoPi), 0.f, 0.f,
                0.f, 0.f, kKegGoLifeSecs))
        {
            keg = go->GetGUID();
            _closing.push_back(keg);    // a keg mid-fuse when the encounter ends goes with Cleanup
        }
        ObjectGuid fuse;
        if (StalkerExists())
            if (TempSummon* stalker = me->SummonCreature(NPC_BRS_STALKER, x, y, z, 0.f, TEMPSUMMON_TIMED_DESPAWN,
                    kFuseStalkerLifeMs))
            {
                stalker->CastSpell(stalker, SPELL_ZG_FUSE, true);
                fuse = stalker->GetGUID();
            }

        MechanicRef ref = Mechanic::Circle(me, pos, kKegRadius, Ms(kKegFuseMs));
        ref.Damage(kKegPct(heroic)).Spell(SPELL_ZG_KEG_BLAST).Weakened().Rider(SPELL_ZG_KEG_STUN).Tag(TAG_KEG);
        ref.OnResolve(OnZigris([pos, keg, fuse](boss_quartermaster_zigris_rework& ai,
            BossMechanics::ResolveResult const& r)
        {
            ai.KegBlew(pos, keg, fuse, r.hits.size());
        }));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "keg",
            Acore::StringFormat("on={} at=({:.1f}, {:.1f}) r={:.0f} fuse={}s", target->GetName(), x, y, kKegRadius,
                kKegFuseMs / 1000));
    }

    void KegBlew(Position const& pos, ObjectGuid keg, ObjectGuid fuse, std::size_t hits)
    {
        me->CastSpell(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ(), SPELL_ZG_BLAST_LOOK, true);
        DeleteGadget(keg);
        if (Creature* stalker = fuse ? me->GetMap()->GetCreature(fuse) : nullptr)
            stalker->DespawnOrUnsummon();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "keg-blast",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={}", pos.GetPositionX(), pos.GetPositionY(), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZG5 Mortar
    // ----------------------------------------------------------------------------------------------------------------

    // The mortar stands on the second crate: a stalker there is where the shells leave from.
    void EnsureMortarStalker()
    {
        if ((_mortarStalker && me->GetMap()->GetCreature(_mortarStalker)) || !StalkerExists())
            return;
        Point3 const at = CrateSpot(kMortarCrate);
        if (TempSummon* stalker = me->SummonCreature(NPC_BRS_STALKER, at.x, at.y, at.z, 0.f, TEMPSUMMON_MANUAL_DESPAWN))
            _mortarStalker = stalker->GetGUID();
    }

    // A salvo: the farthest non-tanks from him, one shell each, 1 s apart.
    void Mortar()
    {
        uint32 const shells = kShells.At(_players);
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        rule.farthest = true;
        std::vector<ObjectGuid> picked;
        for (Player* player : DungeonKit::PickPlayers(me, rule, shells))
            picked.push_back(player->GetGUID());
        if (picked.empty())
            return;
        EnsureMortarStalker();
        for (uint32 i = 0; i < shells; ++i)
        {
            ObjectGuid const guid = picked[ShellTarget(i, static_cast<uint32>(picked.size()))];
            if (i == 0)
                FireShell(guid, 0);
            else
                Later(i * kShellGapMs, [this, guid, i]() { FireShell(guid, i); });
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mortar",
            Acore::StringFormat("shells={} players={}", shells, picked.size()));
    }

    // One shell at where the player stands now: the circle (2 s), and the missile look timed to land with it.
    void FireShell(ObjectGuid playerGuid, uint32 index)
    {
        Player* player = ObjectAccessor::GetPlayer(*me, playerGuid);
        if (!player || !player->IsAlive() || !player->IsInMap(me))
            return;
        Position const pos = player->GetPosition();
        MechanicRef ref = Mechanic::Circle(me, pos, kShellRadius, Ms(kShellFlightMs));
        ref.Damage(kMortarPct(IsHeroicMap(me))).Spell(SPELL_ZG_MORTAR_SHELL).Weakened().Tag(TAG_MORTAR);

        Point3 const mortar = CrateSpot(kMortarCrate);
        float const dist = DungeonKit::Distance(mortar.XY(), ToVec(pos));
        uint32 const wait = ShellLaunchDelayMs(dist);
        ObjectGuid const stalker = _mortarStalker;
        Later(wait, [this, stalker, pos]()
        {
            Unit* from = stalker ? static_cast<Unit*>(me->GetMap()->GetCreature(stalker)) : nullptr;
            (from ? from : static_cast<Unit*>(me))->CastSpell(pos.GetPositionX(), pos.GetPositionY(),
                pos.GetPositionZ(), SPELL_ZG_MORTAR_LOOK, true);
        });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shell",
            Acore::StringFormat("n={} on={} at=({:.1f}, {:.1f}) dist={:.1f} launch+{}ms", index + 1, player->GetName(),
                pos.GetPositionX(), pos.GetPositionY(), dist, wait));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZG6 Explosive Sheep (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    struct Sheep
    {
        ObjectGuid guid;
        DungeonKit::Chaser chase;
        MechanicHandle zone;        // the blast: a circle anchored on the sheep, resolved by Detonate
        MechanicHandle keepAway;    // the bots' RunOut from the group on the chased player (never resolves)
        bool done = false;          // blown up or put down: nothing more happens to it
    };

    // `forced` = that player only; else the picked non-tanks (1, or 2 at 6 or more).
    void ReleaseSheep(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            targets = DungeonKit::PickPlayers(me, rule, kSheepCount.At(_players));
        }
        if (targets.empty())
            return;
        uint32 released = 0;
        for (Player* target : targets)
            if (ReleaseOne(target))
                ++released;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep",
            Acore::StringFormat("released={} live={}", released, _sheep.size()));
    }

    bool ReleaseOne(Player* target)
    {
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_BRS_CLOCKWORK_SHEEP;
        spec.passive = true;
        spec.despawn = Ms(kSheepDespawnMs);
        // The release is next to him, towards the target.
        float const facing = me->GetAngle(target);
        Position const at(me->GetPositionX() + std::cos(facing) * 1.5f, me->GetPositionY() + std::sin(facing) * 1.5f,
            me->GetPositionZ(), facing);
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, { at }, summons);
        if (wave.empty())
            return false;
        Creature* sheep = wave.front();

        auto entry = std::make_unique<Sheep>();
        entry->guid = sheep->GetGUID();
        sheep->CastSpell(sheep, SPELL_ZG_SHEEP_WINDUP, true);
        sheep->CastSpell(sheep, SPELL_ZG_FUSE, true);

        // The blast: a circle on the sheep itself, outline only until it goes (it never draws a growing fill that
        // reads as an imminent hit from 10 s out), hitting everyone inside when it is detonated.
        MechanicRef zone = Mechanic::Circle(me, sheep, kSheepBlastRadius, Ms(kSheepLifeMs + 500));
        zone.Damage(kSheepBlastPct).Spell(SPELL_ZG_SHEEP_BLAST).Weakened().NoFillTimer().Tag(TAG_SHEEP);
        entry->zone = zone.Handle();

        ObjectGuid const guid = entry->guid;
        DungeonKit::ChaserSpec chase;
        chase.speed = kSheepSpeed;
        chase.honorSlows = true;
        chase.reach = kSheepReachYd;
        chase.pauseOnControl = Ms(1000);
        chase.life = Ms(kSheepLifeMs);
        chase.endOnArrive = true;
        chase.tauntImmune = false;
        chase.fixate = false;
        chase.pick.nonTank = true;
        chase.pick.tankIfAlone = true;
        chase.onArrive = [this, guid](Creature*, Unit*) { _explode.emplace_back(guid, "reached"); };
        chase.onEnd = [this, guid](Creature*, DungeonKit::ChaseEnd why)
        {
            _explode.emplace_back(guid, why == DungeonKit::ChaseEnd::Expired ? "fuse" : "no-target");
        };
        chase.onTarget = [this, guid](Creature*, Unit* newTarget) { KeepAway(guid, newTarget); };
        if (!entry->chase.Start(sheep, target, std::move(chase), me))
        {
            Mechanic::Cancel(me, entry->zone);
            sheep->DespawnOrUnsummon();
            return false;
        }
        Sheep* raw = entry.get();
        _sheep.push_back(std::move(entry));
        KeepAway(raw, target);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep-chase",
            Acore::StringFormat("target={} from=({:.1f}, {:.1f})", target->GetName(), at.GetPositionX(),
                at.GetPositionY()));
        return true;
    }

    void KeepAway(ObjectGuid guid, Unit* target)
    {
        if (Sheep* sheep = FindSheep(guid))
            KeepAway(sheep, target);
    }

    // The bots' view of the chase: the chased player keeps away from the group, so the blast hits only them. Replaced
    // when the sheep takes a new target; the warning outlives the sheep, so it never resolves.
    void KeepAway(Sheep* sheep, Unit* target)
    {
        if (sheep->keepAway)
            Mechanic::Cancel(me, sheep->keepAway);
        sheep->keepAway = {};
        if (!target)
            return;
        MechanicRef ref = Mechanic::RunOut(me, target, kSheepBlastRadius, Ms(kSheepRunOutWarnMs));
        ref.NoTelegraph().Tag(TAG_SHEEP_RUN);
        sheep->keepAway = ref.Handle();
    }

    Sheep* FindSheep(ObjectGuid guid)
    {
        for (auto const& s : _sheep)
            if (s->guid == guid)
                return s.get();
        return nullptr;
    }

    // Every tick: the chasers move, the explosions they asked for go off, and a sheep over a Net Trap springs it.
    void UpdateSheep(uint32 diff)
    {
        for (auto const& entry : _sheep)
        {
            if (entry->done)
                continue;
            Creature* sheep = me->GetMap()->GetCreature(entry->guid);
            if (!sheep || !sheep->IsAlive())
                continue;
            entry->chase.Update(sheep, diff);
            if (entry->done || !entry->chase.Active())
                continue;
            for (Trap const& trap : _traps)
                if (SheepSpringsTrap(ToVec(sheep->GetPosition()), ToVec(trap.pos)))
                {
                    Mechanic::Detonate(me, MechanicHandle{ trap.id });
                    DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep-trap",
                        Acore::StringFormat("at=({:.1f}, {:.1f})", trap.pos.GetPositionX(), trap.pos.GetPositionY()));
                    _explode.emplace_back(entry->guid, "trap");
                    break;
                }
        }
        std::vector<std::pair<ObjectGuid, char const*>> queue;
        queue.swap(_explode);
        for (auto const& [guid, why] : queue)
            ExplodeSheep(guid, why);
    }

    // The blast: the sheep stops, its zone resolves (everyone within 8 yd), the look plays, and it goes shortly after.
    void ExplodeSheep(ObjectGuid guid, char const* why)
    {
        Sheep* entry = FindSheep(guid);
        if (!entry || entry->done)
            return;
        entry->done = true;
        Creature* sheep = me->GetMap()->GetCreature(guid);
        std::string const reason = why;
        if (reason == "no-target")
        {
            ReleaseMechanics(*entry);
            if (sheep)
            {
                entry->chase.Stop(sheep);
                sheep->DespawnOrUnsummon();
            }
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep-gone", "no target");
            return;
        }
        Position at = sheep ? sheep->GetPosition() : me->GetPosition();
        if (sheep)
        {
            entry->chase.Stop(sheep);
            sheep->StopMoving();
            sheep->RemoveAurasDueToSpell(SPELL_ZG_FUSE);
        }
        Mechanic::Detonate(me, entry->zone);
        if (entry->keepAway)
            Mechanic::Cancel(me, entry->keepAway);
        entry->keepAway = {};
        me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_ZG_BLAST_LOOK, true);
        if (sheep)
            sheep->DespawnOrUnsummon(Ms(kSheepDespawnMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep-blast",
            Acore::StringFormat("why={} at=({:.1f}, {:.1f}) r={:.0f}", why, at.GetPositionX(), at.GetPositionY(),
                kSheepBlastRadius));
    }

    void ReleaseMechanics(Sheep& entry)
    {
        if (entry.zone)
            Mechanic::Cancel(me, entry.zone);
        if (entry.keepAway)
            Mechanic::Cancel(me, entry.keepAway);
        entry.zone = {};
        entry.keepAway = {};
    }

    // A sheep died or despawned: its entry goes, and unless it blew up its mechanics are cancelled.
    void SheepGone(ObjectGuid guid, char const* why)
    {
        auto it = std::find_if(_sheep.begin(), _sheep.end(), [guid](auto const& s) { return s->guid == guid; });
        if (it == _sheep.end())
            return;
        Sheep& entry = **it;
        if (!entry.done)
        {
            entry.done = true;
            ReleaseMechanics(entry);
            if (Creature* sheep = me->GetMap()->GetCreature(guid))
                entry.chase.Stop(sheep);
        }
        if (why)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sheep-gone", why);
            return;     // a killed sheep's entry goes when it despawns: its unit is still on the map for now
        }
        _sheep.erase(it);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP "Bots"): the sheep first for the ranged, then him; no interrupts, no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        BossMechanics::TargetEntry sheep(NPC_BRS_CLOCKWORK_SHEEP, 3, Who::Ranged);
        sheep.AoeOk();
        d.targets.push_back(std::move(sheep));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs zigris` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Traps,
        Trap,
        FallBack,
        Keg,
        Mortar,
        Sheep,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, Player* gm)
    {
        if (!me->IsEngaged())
            return "Zigris must be in combat (the traps, the keg, the Mortar and the sheep run only in the fight).";
        switch (mechanic)
        {
            case TestMechanic::Traps:
                NetTraps();
                break;
            case TestMechanic::Trap:
                if (!gm)
                    return "No player to put a trap under.";
                PlaceTrap(gm->GetPosition());
                break;
            case TestMechanic::FallBack:
                if (_landing)
                    return "He is already in the air.";
                FallBack();
                break;
            case TestMechanic::Keg:
                PowderKeg(nullptr);
                break;
            case TestMechanic::Mortar:
                Mortar();
                break;
            case TestMechanic::Sheep:
                ReleaseSheep(nullptr);
                break;
        }
        return {};
    }

    // `.dbtest brs zigris restock <n>`: runs landing n's restock now (no leap), from the clock's present.
    std::string TestRestock(uint32 landing, bool heroic)
    {
        if (!me->IsEngaged())
            return "Zigris must be in combat.";
        Restock const restock = RestockFor(landing, heroic);
        if (restock.gadget == Gadget::None)
            return Acore::StringFormat("Landing {} adds nothing ({}).", landing, heroic ? "heroic" : "normal");
        RunRestock(restock, heroic);
        if (restock.text >= 0)
            Talk(static_cast<uint8>(restock.text));
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s players={} falls={} landings={} landing={} traps={}/{} keg={} mortar={} "
            "sheep={} live={} later={}", _clockMs / 1000, _players, _falls, _landings, _landing ? 1 : 0, _traps.size(),
            TrapCap(HeroicMap(), _players), _kegClock.On() ? "on" : "off", _mortarClock.On() ? "on" : "off",
            _sheepClock.On() ? "on" : "off", _sheep.size(), _later.size());
    }

private:
    struct Trap
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

    static char const* GadgetName(Gadget gadget)
    {
        switch (gadget)
        {
            case Gadget::PowderKeg:
                return "powder-keg";
            case Gadget::Mortar:
                return "mortar";
            case Gadget::Sheep:
                return "sheep";
            case Gadget::None:
                break;
        }
        return "none";
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*). A fizzled result runs it too (a trap snapping shut).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnZigris(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_quartermaster_zigris_rework*>(boss->AI()))
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

    void PlayObjectAnim(ObjectGuid guid, uint32 anim)
    {
        if (!guid)
            return;
        if (GameObject* go = me->GetMap()->GetGameObject(guid))
            go->SendCustomAnim(anim);
    }

    void DeleteObject(ObjectGuid guid)
    {
        if (!guid)
            return;
        if (GameObject* go = me->GetMap()->GetGameObject(guid))
            go->Delete();
    }

    // A sprung or snapped trap, or a keg: deleted, and no longer Cleanup's to delete.
    void DeleteGadget(ObjectGuid guid)
    {
        DeleteObject(guid);
        std::erase(_closing, guid);
    }

    // The pull's state: nothing pending, no traps, no kegs, no sheep, no restocks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (auto const& entry : _sheep)
        {
            ReleaseMechanics(*entry);
            if (Creature* sheep = me->GetMap()->GetCreature(entry->guid))
                entry->chase.Stop(sheep);
        }
        _sheep.clear();
        _explode.clear();
        for (Trap const& trap : _traps)
        {
            Mechanic::Cancel(me, MechanicHandle{ trap.id });
            DeleteObject(trap.go);
        }
        _traps.clear();
        // Sprung / snapped traps whose delete waited in _later, and kegs mid-fuse (R-1-B m2).
        for (ObjectGuid const& guid : _closing)
            DeleteObject(guid);
        _closing.clear();
        _later.clear();
        summons.DespawnAll();
        _mortarStalker = ObjectGuid::Empty;
        _clockMs = 0;
        _landAtMs = 0;
        _landing = false;
        _falls = 0;
        _landings = 0;
        _trapsPlaced = 0;
        _trapsClock.Stop();
        _fallBackClock.Stop();
        _kegClock.Stop();
        _mortarClock.Stop();
        _sheepClock.Stop();
        _shootClock.Stop();
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    GadgetClock _trapsClock;
    GadgetClock _fallBackClock;
    GadgetClock _kegClock;
    GadgetClock _mortarClock;
    GadgetClock _sheepClock;
    GadgetClock _shootClock;
    std::vector<Trap> _traps;
    std::vector<ObjectGuid> _closing;   // sprung / snapped traps and kegs waiting for their delete
    std::vector<std::unique_ptr<Sheep>> _sheep;
    std::vector<std::pair<ObjectGuid, char const*>> _explode;   // sheep to blow up at the end of this tick
    std::vector<Pending> _later;
    ObjectGuid _mortarStalker;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _landAtMs = 0;
    uint32 _falls = 0;              // leaps made (the next crate is CrateFor(_falls))
    uint32 _landings = 0;           // landings made (the restock is RestockFor(_landings))
    uint32 _trapsPlaced = 0;
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    bool _landing = false;          // in the air: the arena guard and the beats wait for the landing
};

// A Clockwork Sheep (300707): Zigris drives it (the kit Chaser), it only has to stand in his summons, passive and
// harmless to touch.
struct npc_brs_clockwork_sheep : public NullCreatureAI
{
    explicit npc_brs_clockwork_sheep(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_quartermaster_zigris_rework* FindZigrisAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_ZIGRIS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_quartermaster_zigris_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Zigris is not running boss_quartermaster_zigris_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_quartermaster_zigris_rework::TestMechanic mechanic, char const* what)
    {
        boss_quartermaster_zigris_rework* ai = FindZigrisAI(handler);
        if (!ai)
            return false;
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        std::string const error = ai->TestFire(mechanic, gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Zigris: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_ZIGRIS, BOSS_ZIGRIS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_quartermaster_zigris_rework* ai = FindZigrisAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Zigris: {}", ai->TestState());
        return true;
    }

    bool HandleTraps(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::Traps,
            "a Net Trap toss (ZG1: a trap under each picked non-tank)");
    }

    bool HandleTrap(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::Trap,
            "a Net Trap under you (ZG1; `.gm off` to spring it)");
    }

    bool HandleFallBack(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::FallBack,
            "Fall Back (ZG2: the leap to the next crate, 2 traps, the restock)");
    }

    bool HandleKeg(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::Keg,
            "a Powder Keg (ZG4: a 4 s fuse, then 10 yd)");
    }

    bool HandleMortar(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::Mortar,
            "a Mortar salvo (ZG5: shells 1 s apart at the farthest non-tanks)");
    }

    bool HandleSheep(ChatHandler* handler)
    {
        return Fire(handler, boss_quartermaster_zigris_rework::TestMechanic::Sheep,
            "an Explosive Sheep (ZG6: 5 yd/s, 10 s, 8 yd)");
    }

    // `.dbtest brs zigris restock <1-3> [1]`: the landing's gadget and emote now (starts its clock).
    bool HandleRestock(ChatHandler* handler, uint32 landing, Optional<uint32> heroic)
    {
        boss_quartermaster_zigris_rework* ai = FindZigrisAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestRestock(landing, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Zigris: restock {} run ({}).", landing, isHeroic ? "heroic" : "normal");
        return true;
    }

    // `.dbtest brs zigris <sub>`: the numbers are the map's difficulty (`restock` takes an optional 1 / 0 to force it).
    ChatCommandTable const& ZigrisTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "traps",    HandleTraps,    SEC_GAMEMASTER, Console::No },
            { "trap",     HandleTrap,     SEC_GAMEMASTER, Console::No },
            { "fallback", HandleFallBack, SEC_GAMEMASTER, Console::No },
            { "keg",      HandleKeg,      SEC_GAMEMASTER, Console::No },
            { "mortar",   HandleMortar,   SEC_GAMEMASTER, Console::No },
            { "sheep",    HandleSheep,    SEC_GAMEMASTER, Console::No },
            { "restock",  HandleRestock,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_quartermaster_zigris_rework()
{
    RegisterDungeonReworkCreatureAI(boss_quartermaster_zigris_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_clockwork_sheep, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("zigris", ZigrisTestCommands());
}
