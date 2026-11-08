/*
 * mod-dungeon-bosses, Shadowfang Keep: Rethilgore, the Cell Keeper (WP-S1). Build spec: SK 310-353 (normal and
 * heroic), SK 191-309 (design), RG1-RG6; handoff section 3.5 rows RG, section 3.6 row S1, section 3.8 (the cell block),
 * section 7 #6 (jailed players and doors).
 *
 * Replaces SmartAI 3914 (Soul Drain 7295 on a random player, the prisoners' data set on death: kept here).
 *
 *   RG1 Lock-Up        at 10 s, then every 25 s (waits while someone is jailed): emote + 1.5 s cast bar, he leaps onto
 *                      a random non-tank (healer included) and throws them into a random cell; its door slams shut.
 *                      A teleport, not crowd control. The jailed unit is confined to the cell and everyone else is kept
 *                      out of every closed cell (server movement ignores closed doors: DungeonKit::Confinement).
 *   RG2 Cell Door      an invisible stand-in on the door line (720 / 12,000), attackable from both sides; its death
 *                      opens the door. Bots: kill order (TargetEntry 300500, priority 2, BreakOut)
 *   RG3 Cell Key       one at 66% and one at 33%: a walk-over pickup (keyless players) along the corridor; the carrier
 *                      gets the Cell Key buff, and a carrier-only pickup at a closed occupied door opens it. A jailed
 *                      carrier opens their own door at once. A key may be banked for the next Lock-Up.
 *   RG4 Soul Drain     1 s after the throw he channels on the prisoner (SV 680, not interruptible, not dispellable,
 *                      he keeps meleeing); every 2 s 5% Shadow (RefFlat) on the prisoner and a Soul Fragment
 *   RG5 Soul Fragment  a 1-body pickup at a free fragment point of the cell for 6 s: caught, it heals the prisoner 5%
 *                      (RefFlat); missed, it streaks to him and heals him 5% of his max health
 *   RG6 Tainted (H)    the second fragment of every Lock-Up is tainted: a registry Mine (1.5 yd, 0.5 s arm, no grace,
 *                      40 s), 25% Shadow + 1 Weakened on touch; never in the corridor's narrow WNW third
 *
 * Doors: the instance opens all three on his death and locks the levers while he fights; this script opens every door
 * Lock-Up touched when he evades, and frees (opens) a cell whose prisoner dies or leaves. On his death he tells the
 * stock prisoners (SetData(1, 1) on Ashcrombe, SetData(1, 2) on Adamant), as SmartAI 3914 did.
 *
 * Every firing logs one "sfk rethilgore <mechanic>" line (module.dungeonbosses, INFO). `.sfktest rethilgore ...` fires
 * one mechanic on demand; `.sfktest cells los` (WP-K) checks line of sight through a closed door.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "RethilgoreLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SoulDrain.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <array>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

namespace
{
    char constexpr kBoss[] = "rethilgore";

    // GetGameObject ids of the cell doors, by CellId.
    std::array<uint32, kCellCount> constexpr kCellDoorData{ { DATA_CELL_DOOR_S_GUID, DATA_CELL_DOOR_M_GUID,
        DATA_CELL_DOOR_N_GUID } };
    std::array<char const*, kCellCount> constexpr kCellNames{ { "S", "M", "N" } };

    // The stock prisoners' SmartAI (3849 / 3850 event 38, "on data set 1 / x"): Rethilgore is dead.
    uint32 constexpr kPrisonerDataRethilgoreDead = 1;
    uint32 constexpr kPrisonerValueAshcrombe = 1;
    uint32 constexpr kPrisonerValueAdamant = 2;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogRg(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    Position CellFloor(Vec2 p, float orientation = 0.f)
    {
        return DungeonKit::ToPosition(p, kCellBlockFloorZ, orientation);
    }

    Position ToPos(Point3 const& p)
    {
        return Position(p.x, p.y, p.z, 0.f);
    }

    std::optional<CellId> ParseCell(Optional<std::string> const& arg)
    {
        if (!arg)
            return std::nullopt;
        if (*arg == "s" || *arg == "S")
            return CELL_S;
        if (*arg == "m" || *arg == "M")
            return CELL_M;
        if (*arg == "n" || *arg == "N")
            return CELL_N;
        return std::nullopt;
    }

    uint32 RandomBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // The arena guard (handoff section 3.2 #1, PT1 item 2): the corridor and the three cells; a unit gripped back lands
    // in the corridor in front of the M door.
    DungeonKit::ArenaGuardOptions RethilgoreGuardOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.logPrefix = "sfk rethilgore arena";
        o.landing = [](Creature const* /*boss*/, Unit const* /*unit*/)
        {
            return CellFloor(InFrontOfCell(CELL_M, 4.f));
        };
        return o;
    }

    DungeonKit::ConfineOptions CellConfineOptions()
    {
        DungeonKit::ConfineOptions o;
        // A player's near teleport lands on the client's ack, so the thrown player still stands outside the cell for
        // a moment: the grace covers it (a put-back jump racing the teleport would land the same spot, but glitches).
        o.graceMs = 1500;
        o.logPrefix = "sfk rethilgore cell";
        return o;
    }
}

// Cell Door stand-in 300500 (RG2): invisible, attackable from both sides of the door line, never moves or attacks; its
// death opens the real door (DungeonKit::BreakableDoorAI). Rethilgore's script sees the open door and frees the cell.
struct npc_sfk_cell_door : public DungeonKit::BreakableDoorAI
{
    explicit npc_sfk_cell_door(Creature* creature) : DungeonKit::BreakableDoorAI(creature) { }

    void OnDoorOpened(GameObject* door) override
    {
        LogRg("door-broken", Acore::StringFormat("door {} stand-in {}", door->GetEntry(), me->GetGUID().ToString()));
    }
};

// Soul Fragment 300501 / Tainted Fragment 300502 (RG5 / RG6): the wisp looks. Passive, never move or attack; the
// registry pickup or Mine owns the hitbox and Rethilgore's script despawns them.
struct npc_sfk_soul_fragment : public ScriptedAI
{
    explicit npc_sfk_soul_fragment(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// Rethilgore 3914
struct boss_rethilgore_rework : public BossAI
{
    explicit boss_rethilgore_rework(Creature* creature) : BossAI(creature, BOSS_RETHILGORE),
        _confine(CellConfineOptions())
    {
        _arena.Configure(RethilgoreArena(), RethilgoreGuardOptions());
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Encounter
    // ---------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        BossAI::Reset();
        ClearMechanicState();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (me->IsInEvadeMode())
            return;
        Talk(YELL_RETHILGORE_AGGRO);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RETHILGORE;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        _lockUp.Start();
        _keysDropped = 0;
        FenceClosedCells();
        LogRg("engage", std::string("heroic=") + (Heroic() ? "1" : "0"));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        OpenTouchedDoors();
        ClearMechanicState();
        BossAI::EnterEvadeMode(why);
        LogRg("evade");
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // the instance opens all three cell doors (BOSS_RETHILGORE DONE)
        ClearMechanicState();
        TellPrisoners();
        LogRg("death");
    }

    // His looks and helpers never join the fight (BossAI's JustSummoned would zone them into combat).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (!me->IsInCombat() || !damage || me->GetMaxHealth() == 0)
            return;
        if (damage >= me->GetHealth())
            return;     // the killing blow drops no key
        uint32 const after = me->GetHealth() - damage;
        float const pct = 100.f * float(after) / float(me->GetMaxHealth());
        for (uint32 n = Rethilgore::NewKeys(pct, _keysDropped); n; --n)
            DropKey(_keysDropped);
    }

    void UpdateAI(uint32 diff) override
    {
        // The Lock-Up steps, the jail, the pickups and the tainted fragments run on every update, also while he
        // casts or channels (a cast bar never pauses them) and out of combat (for .sfktest).
        _sequence.Update(diff);
        _pickups.Update(me, diff);
        _confine.Update(me, diff);
        MaintainJail(diff);
        TrackTainted();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;

        if (!_lockUpPending && _lockUp.Update(diff, _jail.has_value()))
            StartLockUp();

        DoMeleeAttackIfReady();     // Soul Drain allows melee (ALLOW_ACTION_DURING_CHANNEL); the cast bar does not
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Mechanics (public: the .sfktest subcommands call them)
    // ---------------------------------------------------------------------------------------------------------------

    // RG1: pick a random non-tank in his arena and start the sequence on it. False when nobody qualifies.
    bool StartLockUp()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.maxRange = Rethilgore::kLockUpRange;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (!_arena.Contains(player))
                    rule.exclude.push_back(player->GetGUID().GetRawValue());
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            _lockUp.Retry();
            return false;
        }
        LockUp(target, std::nullopt);
        return true;
    }

    // RG1 on `target`: the emote and the 1.5 s cast bar, then the leap, then the throw into `forced` (else a random
    // cell).
    void LockUp(Player* target, std::optional<CellId> forced)
    {
        if (!target || _jail || _lockUpPending)
            return;
        _lockUpPending = true;
        _lockUp.Fired();
        DungeonKit::CastBar(me, Rethilgore::SPELL_LOCK_UP_CAST, nullptr, EMOTE_RETHILGORE_LOCK_UP, target);
        ObjectGuid const guid = target->GetGUID();
        CellId const cell = forced ? *forced : Rethilgore::CellFromRoll(urand(0, kCellCount - 1));
        LogRg("lock-up", Acore::StringFormat("target={} cell={}", target->GetName(), kCellNames[cell]));
        _sequence.Schedule(Ms(Rethilgore::kLockUpWarnMs), [this, guid, cell](TaskContext /*ctx*/)
        {
            Player* victim = ObjectAccessor::GetPlayer(*me, guid);
            if (!ValidLockUpTarget(victim))
            {
                AbortLockUp("the target is gone");
                return;
            }
            me->CastSpell(victim, Rethilgore::SPELL_LOCK_UP_LEAP, true);
            float const dist = me->GetExactDist2d(victim);
            DungeonKit::JumpTo(me, victim->GetPosition(), Rethilgore::kLeapSpeedXY, Rethilgore::kLeapMinSpeedZ);
            _sequence.Schedule(Ms(Rethilgore::ThrowDelayMs(dist)), [this, guid, cell](TaskContext /*ctx*/)
            {
                Player* thrown = ObjectAccessor::GetPlayer(*me, guid);
                if (!ValidLockUpTarget(thrown))
                {
                    AbortLockUp("the target is gone");
                    return;
                }
                _lockUpPending = false;
                Throw(thrown, cell);
            });
        });
    }

    // RG1's throw: `player` lands in `cell` (a teleport with a flash at both ends) and is jailed there.
    void Throw(Player* player, CellId cell)
    {
        if (!player || _jail)
            return;
        player->CastSpell(player, Rethilgore::SPELL_CELL_THROW_FLASH, true);
        Point3 const& landing = kCellLandings[cell];
        player->NearTeleportTo(landing.x, landing.y, landing.z, player->GetOrientation());
        player->CastSpell(player, Rethilgore::SPELL_CELL_THROW_FLASH, true);
        Jail(player, cell);
    }

    // `player` is in `cell` now: the door slams shut, the stand-in rises, Soul Drain follows. A key carrier opens
    // the door at once.
    void Jail(Player* player, CellId cell)
    {
        GameObject* door = CellDoor(cell);
        if (!player || !door || _jail)
            return;
        _touchedCells |= uint8(1u << cell);

        if (player->HasAura(Rethilgore::SPELL_CELL_KEY))
        {
            player->RemoveAurasDueToSpell(Rethilgore::SPELL_CELL_KEY);
            SetDoor(door, true);
            LogRg("key-self", Acore::StringFormat("prisoner={} cell={}", player->GetName(), kCellNames[cell]));
            return;
        }

        SetDoor(door, false);
        JailState jail;
        jail.prisoner = player->GetGUID();
        jail.cell = cell;
        jail.drainMs = Rethilgore::kDrainStartMs;

        if (Creature* standIn = DungeonKit::SpawnBreakableDoor(door, NPC_SFK_CELL_DOOR,
                Rethilgore::kDoorHealth(Heroic())))
        {
            jail.standIn = standIn->GetGUID();
            Mechanic::TrackUnit(me, standIn);
            BossMechanics::Registry::GetOrCreate(me->GetMap()).NoteHeld(me->GetGUID(), standIn->GetGUID(),
                player->GetGUID(), 0);
        }

        _confine.ConfineIn(player, CellArena(cell), ToPos(kCellLandings[cell]));
        // The prisoner's pet goes in with it (put back beside its owner after the grace); left outside, the fence
        // would put it out each time its follow path walks through the closed door (R1 N-4).
        if (Pet* pet = player->GetPet())
        {
            jail.pet = pet->GetGUID();
            _confine.ConfineIn(pet, CellArena(cell), ToPos(kCellLandings[cell]));
        }
        if (!_fences[cell])
            _fences[cell] = _confine.KeepOut(CellArena(cell), CellFloor(InFrontOfCell(cell)));

        Rethilgore::Cellmate const mate = Rethilgore::CellmateOf(cell);
        if (Creature* occupant = CellOccupant(cell); occupant && occupant->IsAlive() && occupant->IsAIEnabled)
            occupant->AI()->Talk(mate.textGroup, player);

        _jail = jail;
        RefreshDelivery();
        LogRg("jailed", Acore::StringFormat("prisoner={} cell={} door={}", player->GetName(), kCellNames[cell],
            Rethilgore::kDoorHealth(Heroic())));
    }

    // The jailed cell opens (door broken, key, prisoner gone, .sfktest): Soul Drain ends, the fence and the
    // confinement go, the stand-in despawns. Live fragments stay until caught or missed.
    void Free(char const* why)
    {
        if (!_jail)
            return;
        JailState const jail = *_jail;
        _jail.reset();
        if (GameObject* door = CellDoor(jail.cell))
            SetDoor(door, true);
        if (Creature* standIn = jail.standIn ? me->GetMap()->GetCreature(jail.standIn) : nullptr)
            standIn->DespawnOrUnsummon();
        _confine.Release(jail.prisoner);
        if (jail.pet)
            _confine.Release(jail.pet);
        ReleaseFence(jail.cell);
        StopDrain();
        if (_deliveryId)
            _pickups.Cancel(me, _deliveryId);
        _deliveryId = 0;
        _deliveryCarriers.clear();
        LogRg("freed", Acore::StringFormat("cell={} why={} ticks={}", kCellNames[jail.cell], why, jail.ticks));
    }

    // RG4: one tick on the prisoner (5% Shadow) and its fragment (RG5), or the tainted one (RG6, heroic).
    void DrainTick()
    {
        if (!_jail)
            return;
        Player* prisoner = ObjectAccessor::GetPlayer(*me, _jail->prisoner);
        if (!prisoner)
            return;
        ++_jail->ticks;
        SoulDrain::Tick(me, prisoner);
        if (Rethilgore::TaintedOnTick(Heroic(), _jail->ticks))
            SpawnTainted(_jail->cell);
        else
            SpawnFragment(_jail->cell, prisoner->GetGUID());
    }

    // RG5: a Soul Fragment at a free point of `cell`, owned by `owner` (who a catch heals).
    void SpawnFragment(CellId cell, ObjectGuid owner)
    {
        std::optional<std::size_t> const pick = Rethilgore::PickFreePoint(Rethilgore::FragmentPoints(cell),
            OccupiedPoints(), Rethilgore::kFragmentMinGap, RandomBelow);
        if (!pick)
        {
            LogRg("fragment-skipped", Acore::StringFormat("cell={}: every point is taken", kCellNames[cell]));
            return;
        }
        Vec2 const at = Rethilgore::FragmentPoints(cell)[*pick];
        uint32 const key = _nextFragmentKey++;

        DungeonKit::PickupSpec spec;
        spec.radius = Rethilgore::kFragmentRadius;
        spec.life = Ms(Rethilgore::kFragmentLifeMs);
        spec.who.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        spec.who.carriers = PlayersExcept(owner);
        spec.count = 1;
        spec.color = BossMechanics::Color::Blue;
        spec.visualEntry = NPC_SFK_SOUL_FRAGMENT;
        spec.tag = Rethilgore::kTagSoulFragment;
        spec.onPick = [this, key, at, owner](Player* taker) { FragmentCaught(key, at, owner, taker); };
        spec.onExpire = [this, key, at]() { FragmentMissed(key, at); };
        if (!_pickups.Add(me, CellFloor(at), std::move(spec)))
            return;
        _fragments.push_back({ key, at });
        LogRg("fragment", Acore::StringFormat("cell={} at=({:.1f}, {:.1f})", kCellNames[cell], at.x, at.y));
    }

    // RG6 (heroic): a Tainted Fragment, a registry Mine with the green wisp on it.
    void SpawnTainted(CellId cell)
    {
        std::optional<std::size_t> const pick = Rethilgore::PickFreePoint(Rethilgore::TaintedPoints(cell),
            OccupiedPoints(), Rethilgore::kFragmentMinGap, RandomBelow);
        if (!pick)
        {
            LogRg("tainted-skipped", Acore::StringFormat("cell={}: every point is taken", kCellNames[cell]));
            return;
        }
        Vec2 const at = Rethilgore::TaintedPoints(cell)[*pick];
        Position const pos = CellFloor(at);
        TempSummon* look = me->SummonCreature(NPC_SFK_TAINTED_FRAGMENT, pos, TEMPSUMMON_MANUAL_DESPAWN);

        // The lambda keeps the map and the look's guid only (a registry callback never holds a Unit*).
        Map* map = me->GetMap();
        ObjectGuid const lookGuid = look ? look->GetGUID() : ObjectGuid::Empty;
        BossMechanics::MechanicHandle const handle = Mechanic::Mine(me, pos, Rethilgore::kTaintedRadius,
            Ms(Rethilgore::kTaintedArmMs), Ms(Rethilgore::kTaintedGraceMs))
            .Lifetime(Ms(Rethilgore::kTaintedLifeMs)).Damage(Rethilgore::kTaintedPct).School(SPELL_SCHOOL_SHADOW)
            .Spell(Rethilgore::SPELL_TAINTED_FRAGMENT).Weakened().Color(BossMechanics::Color::Green)
            .Tag(Rethilgore::kTagTaintedFragment)
            .OnResolve([map, lookGuid](BossMechanics::ResolveResult const& result)
            {
                if (result.fizzled)
                    return;
                if (Creature* unit = map && lookGuid ? map->GetCreature(lookGuid) : nullptr)
                    unit->DespawnOrUnsummon();
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "tainted-popped",
                    Acore::StringFormat("{} player(s) hit", result.hits.size()));
            });
        if (!handle)
        {
            if (look)
                look->DespawnOrUnsummon();
            return;
        }
        _tainted.push_back({ lookGuid, handle, at });
        LogRg("tainted", Acore::StringFormat("cell={} at=({:.1f}, {:.1f})", kCellNames[cell], at.x, at.y));
    }

    // RG3: key `index` (0 = the 66% key) clatters to its landing along the corridor.
    void DropKey(uint32 index)
    {
        ++_keysDropped;
        Point3 const landing = Rethilgore::KeyLanding(index);
        Talk(EMOTE_RETHILGORE_KEYS);

        DungeonKit::PickupSpec spec;
        spec.radius = Rethilgore::kKeyRadius;
        spec.life = Ms(Rethilgore::kKeyLifeMs);
        spec.who.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        spec.who.auraSpell = Rethilgore::SPELL_CELL_KEY;   // keyless players only: one key at most
        spec.who.minStacks = 0;
        spec.who.maxStacks = 0;
        spec.count = 1;
        spec.color = BossMechanics::Color::Yellow;
        spec.goEntry = GO_SFK_CELL_KEY;
        spec.tag = Rethilgore::kTagCellKey;
        spec.onPick = [this](Player* taker) { KeyPicked(taker); };
        _pickups.Add(me, ToPos(landing), std::move(spec));
        LogRg("key-drop", Acore::StringFormat("key={} at=({:.1f}, {:.1f})", index + 1, landing.x, landing.y));
    }

    std::string StateText() const
    {
        std::string out = Acore::StringFormat(
            "lock-up in {} ms{}, keys dropped {}, pickups {}, fragments {}, tainted {}",
            _lockUp.UntilDueMs(), _lockUpPending ? " (in progress)" : "", _keysDropped, _pickups.Count(),
            _fragments.size(), _tainted.size());
        if (_jail)
        {
            Player const* prisoner = ObjectAccessor::FindPlayer(_jail->prisoner);
            out += Acore::StringFormat("; jailed {} in cell {}, ticks {}, key carriers at the door {}",
                prisoner ? prisoner->GetName() : _jail->prisoner.ToString(), kCellNames[_jail->cell], _jail->ticks,
                _deliveryCarriers.size());
        }
        else
            out += "; nobody jailed";
        return out;
    }

    bool HasJail() const { return _jail.has_value(); }
    CellId JailCell() const { return _jail ? _jail->cell : CELL_M; }
    ObjectGuid Prisoner() const { return _jail ? _jail->prisoner : ObjectGuid::Empty; }

private:
    struct JailState
    {
        ObjectGuid prisoner;
        ObjectGuid pet;         // the prisoner's pet, confined with it
        CellId cell = CELL_M;
        ObjectGuid standIn;
        uint32 drainMs = 0;     // until the channel (then the next tick)
        uint32 ticks = 0;
        bool draining = false;
    };

    struct FragmentEntry
    {
        uint32 key = 0;
        Vec2 at;
    };

    struct TaintedEntry
    {
        ObjectGuid look;
        BossMechanics::MechanicHandle handle;
        Vec2 at;
    };

    bool Heroic() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    void Describe()
    {
        BossMechanics::Descriptor d;
        // The stand-in while someone is jailed (it exists only then), before Rethilgore; BreakOut orders two prisons by
        // the held player's role (only one at a time here).
        d.targets.push_back(BossMechanics::TargetEntry(NPC_SFK_CELL_DOOR, 2, BossMechanics::Who::Dps).BreakOut());
        d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_SFK_SOUL_FRAGMENT));
        d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_SFK_TAINTED_FRAGMENT));
        Mechanic::Describe(me, std::move(d));
    }

    bool ValidLockUpTarget(Player const* p) const
    {
        return p && p->IsInWorld() && p->IsAlive() && p->IsInMap(me) && !p->IsGameMaster() && me->IsAlive()
            && !_jail;
    }

    void AbortLockUp(char const* why)
    {
        _lockUpPending = false;
        _lockUp.Retry();
        LogRg("lock-up-aborted", why);
    }

    GameObject* CellDoor(CellId cell) const
    {
        return instance ? instance->GetGameObject(kCellDoorData[cell]) : nullptr;
    }

    Creature* CellOccupant(CellId cell) const
    {
        if (!instance)
            return nullptr;
        switch (cell)
        {
            case CELL_S:
                return instance->GetCreature(DATA_ADAMANT_GUID);
            case CELL_M:
                return instance->GetCreature(DATA_ASHCROMBE_GUID);
            default:
                return instance->GetCreature(DATA_LANDEN_GUID);
        }
    }

    void SetDoor(GameObject* door, bool open)
    {
        if (!door)
            return;
        if (instance)
            instance->HandleGameObject(ObjectGuid::Empty, open, door);
        else
            door->SetGoState(open ? GO_STATE_ACTIVE : GO_STATE_READY);
    }

    // Everyone stays out of a closed cell (server movement walks bots through closed doors); one fence per cell.
    void FenceClosedCells()
    {
        for (std::size_t i = 0; i < kCellCount; ++i)
        {
            CellId const cell = CellId(i);
            GameObject const* door = CellDoor(cell);
            if (door && door->GetGoState() != GO_STATE_ACTIVE && !_fences[cell])
                _fences[cell] = _confine.KeepOut(CellArena(cell), CellFloor(InFrontOfCell(cell)));
        }
    }

    void ReleaseFence(CellId cell)
    {
        if (_fences[cell])
            _confine.ReleaseKeepOut(_fences[cell]);
        _fences[cell] = 0;
    }

    // Evade: every door Lock-Up touched opens, so nobody is left locked in after a wipe (SK "Implementation").
    void OpenTouchedDoors()
    {
        for (std::size_t i = 0; i < kCellCount; ++i)
            if (_touchedCells & (1u << i))
                SetDoor(CellDoor(CellId(i)), true);
        if (_jail)
            SetDoor(CellDoor(_jail->cell), true);
        _touchedCells = 0;
    }

    void ClearMechanicState()
    {
        _sequence.CancelAll();
        _pickups.Clear(me);
        _confine.Clear();
        _fences.fill(0);
        if (_jail)
            if (Creature* standIn = _jail->standIn ? me->GetMap()->GetCreature(_jail->standIn) : nullptr)
                standIn->DespawnOrUnsummon();
        StopDrain();
        _jail.reset();
        _deliveryId = 0;
        _deliveryCarriers.clear();
        _fragments.clear();
        for (TaintedEntry const& t : _tainted)
            if (Creature* look = t.look ? me->GetMap()->GetCreature(t.look) : nullptr)
                look->DespawnOrUnsummon();
        _tainted.clear();
        _lockUpPending = false;
        _lockUp.Start();
        RemoveKeys();
    }

    // Keys are this fight's: every carrier loses its key when the fight ends.
    void RemoveKeys()
    {
        if (!me->IsInWorld())
            return;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                player->RemoveAurasDueToSpell(Rethilgore::SPELL_CELL_KEY);
    }

    // The stock SmartAI 3914 rows 1-2: Ashcrombe and Adamant hear he is dead (their escort to the Courtyard Door).
    void TellPrisoners()
    {
        if (!instance)
            return;
        if (Creature* ashcrombe = instance->GetCreature(DATA_ASHCROMBE_GUID))
            if (ashcrombe->IsAIEnabled)
                ashcrombe->AI()->SetData(kPrisonerDataRethilgoreDead, kPrisonerValueAshcrombe);
        if (Creature* adamant = instance->GetCreature(DATA_ADAMANT_GUID))
            if (adamant->IsAIEnabled)
                adamant->AI()->SetData(kPrisonerDataRethilgoreDead, kPrisonerValueAdamant);
    }

    // The jail's upkeep, every update: the prisoner gone or the door open frees the cell; the channel, the ticks and
    // the carrier-only delivery follow the jail.
    void MaintainJail(uint32 diff)
    {
        if (!_jail)
            return;
        Player* prisoner = ObjectAccessor::GetPlayer(*me, _jail->prisoner);
        if (!prisoner || !prisoner->IsAlive() || !prisoner->IsInMap(me))
        {
            Free("prisoner-gone");
            return;
        }
        GameObject const* door = CellDoor(_jail->cell);
        if (!door || door->GetGoState() == GO_STATE_ACTIVE)
        {
            Free("door-open");
            return;
        }

        if (_jail->drainMs > diff)
            _jail->drainMs -= diff;
        else
        {
            _jail->drainMs = Rethilgore::kDrainTickMs;
            if (_jail->draining)
                DrainTick();
            else
            {
                _jail->draining = true;
                LogRg("soul-drain", Acore::StringFormat("prisoner={}", prisoner->GetName()));
            }
        }
        if (_jail && _jail->draining)
            SoulDrain::StartChannel(me, prisoner);

        _deliveryCheckMs += diff;
        if (_deliveryCheckMs >= 1000)
        {
            _deliveryCheckMs = 0;
            RefreshDelivery();
        }
    }

    void StopDrain()
    {
        SoulDrain::StopChannel(me);
    }

    // The players alive in the map other than `except` (a fragment's carriers: the prisoner cannot reach it).
    GuidSet PlayersExcept(ObjectGuid except) const
    {
        GuidSet out;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && !player->IsGameMaster() && player->GetGUID() != except)
                    out.insert(player->GetGUID());
        return out;
    }

    // RG3 delivery: a carrier-only pickup at the closed occupied door, for the key carriers outside the cell. Rebuilt
    // when the carriers change.
    void RefreshDelivery()
    {
        GuidSet carriers;
        if (_jail)
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (player->IsAlive() && player->GetGUID() != _jail->prisoner
                        && player->HasAura(Rethilgore::SPELL_CELL_KEY))
                        carriers.insert(player->GetGUID());
        if (carriers == _deliveryCarriers && (_deliveryId != 0) == !carriers.empty())
            return;
        if (_deliveryId)
            _pickups.Cancel(me, _deliveryId);
        _deliveryId = 0;
        _deliveryCarriers = carriers;
        if (carriers.empty() || !_jail)
            return;

        DungeonKit::PickupSpec spec;
        spec.radius = Rethilgore::kDeliveryRadius;
        spec.life = Ms(Rethilgore::kKeyLifeMs);
        spec.who.carriers = carriers;
        spec.count = 1;
        spec.color = BossMechanics::Color::Yellow;
        spec.tag = Rethilgore::kTagCellKey;
        spec.onPick = [this](Player* taker) { KeyDelivered(taker); };
        _deliveryId = _pickups.Add(me, CellFloor(kCellDoors[_jail->cell].XY()), std::move(spec));
    }

    void KeyPicked(Player* taker)
    {
        if (!taker)
            return;
        taker->CastSpell(taker, Rethilgore::SPELL_CELL_KEY, true);
        LogRg("key-picked", Acore::StringFormat("carrier={}", taker->GetName()));
        RefreshDelivery();
    }

    void KeyDelivered(Player* taker)
    {
        _deliveryId = 0;
        _deliveryCarriers.clear();
        if (!taker || !_jail || !taker->HasAura(Rethilgore::SPELL_CELL_KEY))
        {
            RefreshDelivery();
            return;
        }
        taker->RemoveAurasDueToSpell(Rethilgore::SPELL_CELL_KEY);
        LogRg("key-delivered", Acore::StringFormat("carrier={} cell={}", taker->GetName(), kCellNames[_jail->cell]));
        Free("key");
    }

    // RG5 caught: the soul returns to its owner (the streak and 5% of the reference row as a heal).
    void FragmentCaught(uint32 key, Vec2 at, ObjectGuid owner, Player* taker)
    {
        ForgetFragment(key);
        Player* soulOwner = ObjectAccessor::GetPlayer(*me, owner);
        int32 const amount = SoulDrain::ReturnSoul(me, CellFloor(at), soulOwner);
        if (!amount)
            return;
        LogRg("fragment-caught", Acore::StringFormat("catcher={} owner={} heal={}", taker ? taker->GetName() : "?",
            soulOwner->GetName(), amount));
    }

    // RG5 missed: it streaks to him and heals him 5% of his max health.
    void FragmentMissed(uint32 key, Vec2 at)
    {
        ForgetFragment(key);
        if (!me->IsInCombat())
            return;
        int32 const amount = SoulDrain::Feast(me, CellFloor(at));
        LogRg("fragment-missed", Acore::StringFormat("heal={}", amount));
    }

    void ForgetFragment(uint32 key)
    {
        std::erase_if(_fragments, [key](FragmentEntry const& f) { return f.key == key; });
    }

    std::vector<Vec2> OccupiedPoints() const
    {
        std::vector<Vec2> out;
        for (FragmentEntry const& f : _fragments)
            out.push_back(f.at);
        for (TaintedEntry const& t : _tainted)
            out.push_back(t.at);
        return out;
    }

    // Tainted fragments the registry is done with (popped, faded, or ended with the encounter) leave the list; their
    // look goes too.
    void TrackTainted()
    {
        if (_tainted.empty())
            return;
        BossMechanics::Registry const* registry = Mechanic::Read(me->GetMap());
        std::erase_if(_tainted, [this, registry](TaintedEntry const& t)
        {
            BossMechanics::ActiveMechanic const* m = registry ? registry->Find(t.handle.id) : nullptr;
            if (m && !m->finished && !m->cancelled)
                return false;
            if (Creature* look = t.look ? me->GetMap()->GetCreature(t.look) : nullptr)
                look->DespawnOrUnsummon();
            return true;
        });
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::Confinement _confine;
    DungeonKit::Pickups _pickups;
    TaskScheduler _sequence;
    Rethilgore::LockUpClock _lockUp;
    std::optional<JailState> _jail;
    std::array<uint32, kCellCount> _fences{};
    std::vector<FragmentEntry> _fragments;
    std::vector<TaintedEntry> _tainted;
    GuidSet _deliveryCarriers;
    uint32 _deliveryId = 0;
    uint32 _deliveryCheckMs = 0;
    uint32 _keysDropped = 0;
    uint32 _nextFragmentKey = 1;
    uint8 _touchedCells = 0;
    bool _lockUpPending = false;
};

// 205914 Soul Drain (RG4 tick): 5% of the reference non-tank row, Shadow (the target's defensives count; the spell
// ignores caster modifiers).
class spell_sfk_rethilgore_soul_drain : public SpellScript
{
    PrepareSpellScript(spell_sfk_rethilgore_soul_drain);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlat(GetCaster(), Rethilgore::kDrainPct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_rethilgore_soul_drain::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_rethilgore_rework* RethilgoreAI(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_RETHILGORE);
        if (!boss)
            return nullptr;
        boss_rethilgore_rework* ai = CAST_AI(boss_rethilgore_rework, boss->AI());
        if (!ai)
            handler->SendErrorMessage("Rethilgore does not run boss_rethilgore_rework (is the instance bound to {}?).",
                kInstanceScriptName);
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        return handler->getSelectedPlayerOrSelf();
    }

    // `.sfktest rethilgore info`
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_RETHILGORE, BOSS_RETHILGORE);
    }

    // `.sfktest rethilgore state`: the Lock-Up clock, the jail, keys and fragments.
    bool HandleState(ChatHandler* handler)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("{}", ai->StateText());
        return true;
    }

    // `.sfktest rethilgore lockup [s|m|n]`: the whole Lock-Up (emote, cast bar, leap, throw) on the selected player
    // or the GM, into the given cell (else a random one).
    bool HandleLockUp(ChatHandler* handler, Optional<std::string> cell)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        if (ai->HasJail())
        {
            handler->SendErrorMessage("Someone is jailed already (.sfktest rethilgore free).");
            return false;
        }
        ai->LockUp(TestTarget(handler), ParseCell(cell));
        return true;
    }

    // `.sfktest rethilgore jail [s|m|n]`: the throw alone (no leap), now.
    bool HandleJail(ChatHandler* handler, Optional<std::string> cell)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        if (ai->HasJail())
        {
            handler->SendErrorMessage("Someone is jailed already (.sfktest rethilgore free).");
            return false;
        }
        std::optional<CellId> const which = ParseCell(cell);
        ai->Throw(TestTarget(handler), which ? *which : Rethilgore::CellFromRoll(urand(0, kCellCount - 1)));
        return true;
    }

    // `.sfktest rethilgore free`: open the jailed cell now.
    bool HandleFree(ChatHandler* handler)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        ai->Free("test");
        return true;
    }

    // `.sfktest rethilgore key [1|2]`: drop a key now (default: the next one).
    bool HandleKey(ChatHandler* handler, Optional<uint32> which)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        ai->DropKey(which && *which ? *which - 1 : 0);
        return true;
    }

    // `.sfktest rethilgore tick`: one Soul Drain tick (someone must be jailed).
    bool HandleTick(ChatHandler* handler)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        if (!ai->HasJail())
        {
            handler->SendErrorMessage("Nobody is jailed (.sfktest rethilgore jail).");
            return false;
        }
        ai->DrainTick();
        return true;
    }

    // `.sfktest rethilgore fragment [s|m|n]`: a Soul Fragment at a free point of the cell (default: the jailed cell,
    // else M), owned by the prisoner, else the GM.
    bool HandleFragment(ChatHandler* handler, Optional<std::string> cell)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        std::optional<CellId> const which = ParseCell(cell);
        ObjectGuid const owner = ai->HasJail() ? ai->Prisoner() : handler->GetPlayer()->GetGUID();
        ai->SpawnFragment(which ? *which : ai->JailCell(), owner);
        return true;
    }

    // `.sfktest rethilgore tainted [s|m|n]`: a Tainted Fragment (any difficulty) at a free tainted point of the cell.
    bool HandleTainted(ChatHandler* handler, Optional<std::string> cell)
    {
        boss_rethilgore_rework* ai = RethilgoreAI(handler);
        if (!ai)
            return false;
        std::optional<CellId> const which = ParseCell(cell);
        ai->SpawnTainted(which ? *which : ai->JailCell());
        return true;
    }

    ChatCommandTable const& RethilgoreTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "lockup",   HandleLockUp,   SEC_GAMEMASTER, Console::No },
            { "jail",     HandleJail,     SEC_GAMEMASTER, Console::No },
            { "free",     HandleFree,     SEC_GAMEMASTER, Console::No },
            { "key",      HandleKey,      SEC_GAMEMASTER, Console::No },
            { "tick",     HandleTick,     SEC_GAMEMASTER, Console::No },
            { "fragment", HandleFragment, SEC_GAMEMASTER, Console::No },
            { "tainted",  HandleTainted,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rethilgore_rework()
{
    RegisterDungeonReworkCreatureAI(boss_rethilgore_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_cell_door, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_soul_fragment, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_rethilgore_soul_drain);
    SfkTest::RegisterBoss("rethilgore", RethilgoreTestCommands());
}
