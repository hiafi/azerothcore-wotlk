/*
 * mod-dungeon-bosses, Blackrock Depths D11: Lord Incendius (9017), "the flame that will not die, on an island that is
 * a death trap" (rulings 47, 48, 88). Build spec: docs/dungeons/blackrock-depths-2-shadowforge-city.md "Lord
 * Incendius" (IN1-IN8), handoff sections 3.4 / 3.5 row D11, 3.6, 3.8, 3.10, 7 #14 A. Replaces his SmartAI (rows 0-4,
 * dropped by rev_blackrock_depths_skeleton.sql); bound by apps/dbc-tools source/npcs/blackrock_depths/incendius.py. His
 * patrol (path 477330) is the creature's own movement out of combat. Pure rules and the causeway's geometry:
 * IncendiusLogic.h. The hard mode (D12, Lord of the Lake) fights on this AI through IncendiusFight.h.
 *
 * The "island" is the Anvil bulge on the z -72 causeway (NAVMESH 2.5): the arena is s -24 to +24 along it (section 7
 * #14 A, the same frame D12 uses); the lava is 38 yd below both long sides and a fall is death (ruling 48: the kit's
 * FallWatch kills anyone caught 20 yd under the causeway over the lake).
 *
 *   IN1 Curse        at 16 s, then every 22 s: +10% Fire damage taken on everyone within 45 yd for 60 s (a Curse;
 *                    removing it is a reward, the descriptor's dispel list)
 *   IN2 Fiery Burst  at 9 s, then every 9-13 s: a 1.5 s cast on his victim, everyone within 10 yd of it, 12% / 15%;
 *                    interruptible (a reward on normal, expected on heroic: the descriptor's interrupt list)
 *   IN3 Fire Storm   at 6 s, then every 10 s (heroic 8 s): a 2 s marker at a random player's spot (the tank too), then
 *                    a 5 yd patch for 30 s, 4% / 6% a second (and the kit's Standing in It slow)
 *   IN4 Magma Fist   at 12 s, then every 20 s: a 2 s line from him through a random player (the tank too), then the
 *                    fist: 25% / 40% + Weakened, and a 10 yd throw along the line (the kit's PushAlong: it lands on the
 *                    floor, or past the edge, never on the rim)
 *   IN5 Lava Surge   at 15 s, then every 25 s (heroic 20 s): a 3 s marker, a 6 yd strip along the long edge where more
 *                    players stand: 30% / 45% + Weakened
 *   IN6 Shatter      a lethal hit while a rebirth is left: he yells and breaks (gone, not immune: the Embers are the
 *                    targets); 4 (heroic 5) Embers of Incendius 300794 appear at the edges and roll to The Black Anvil
 *                    over about 10 s
 *   IN7 Reborn       12 s after the shatter he reforms by the Anvil with 40% of his health + 10% per Ember that arrived
 *                    (an Ember still alive then joins him too). Once on normal, twice on heroic; the last death is real
 *                    (the encounter credit)
 *   IN8 The trap     at each rebirth, 5 s before he stands up, the edge marker (emote line 5): the first rebirth seals
 *       closes       both necks (4 yd bands across the causeway at the arena's ends) and every rebirth eats the next
 *                    2 yd of both long edges (the kit's LethalBands: anyone inside is thrown over the real edge, pets
 *                    too); the crumble says emote line 2 and leaves the cracks for the rest of the fight
 *
 * Every timer runs on the AI's own clock (the beats pause while he is shattered). Every firing logs one INFO line
 * "brd incendius <mechanic> ..." (module.dungeonbosses); `.dbtest brd incendius <mechanic>` fires one on demand.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitEdges.h"
#include "IncendiusFight.h"
#include "IncendiusLogic.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdIncendius;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "incendius";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    IncendiusHardModeFactory& HardModeFactory()
    {
        static IncendiusHardModeFactory factory;
        return factory;
    }

    IncendiusIdleHook& IdleHook()
    {
        static IncendiusIdleHook hook;
        return hook;
    }

    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRD_STALKER) != nullptr;
    }

    // The causeway's floor under (x, y) near its height; the causeway's height when the probe finds nothing close.
    float FloorZ(WorldObject const* ref, float x, float y)
    {
        float const z = ref->GetMap()->GetHeight(ref->GetPhaseMask(), x, y, kFloorZ + 3.f, true, 10.f);
        return (z > INVALID_HEIGHT && std::fabs(z - kFloorZ) <= 4.f) ? z : kFloorZ;
    }

    Position OnFloor(WorldObject const* ref, Vec2 p, float o = 0.f)
    {
        return Position(p.x, p.y, FloorZ(ref, p.x, p.y), o);
    }

    // The ground under a player (a player in the air gets the floor within 10 yd below, else his own height).
    Position GroundUnder(Player const* player)
    {
        float const x = player->GetPositionX();
        float const y = player->GetPositionY();
        float const z = player->GetPositionZ();
        float const floor = player->GetMap()->GetHeight(player->GetPhaseMask(), x, y, z + 2.f, true, 12.f);
        return Position(x, y, (floor > INVALID_HEIGHT && std::fabs(floor - z) <= 10.f) ? floor : z, 0.f);
    }

    // The leash: the arena's real floor at the causeway's height.
    DungeonKit::Arena FightArena()
    {
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Polygon(ArenaFloor(), kFloorZ - 4.f, kFloorZ + 8.f));
    }

    // The lake the FallWatch covers: a box in the causeway frame round the arena, from the catch height down to the
    // lava's surface (the Fireguard Destroyers' floor at z -116 is below it).
    DungeonKit::Arena LakeRegion()
    {
        float const mid = MidlineAt(0.f);
        std::vector<Vec2> box{ ToWorld(kLakeSMin, mid - kLakeHalfWidthYd), ToWorld(kLakeSMax, mid - kLakeHalfWidthYd),
            ToWorld(kLakeSMax, mid + kLakeHalfWidthYd), ToWorld(kLakeSMin, mid + kLakeHalfWidthYd) };
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Polygon(std::move(box), kLakeZMin,
            kFloorZ - kFallCatchBelowYd + 0.5f));
    }

    std::vector<Position> ToPositions(std::vector<Vec2> const& poly, float z)
    {
        std::vector<Position> out;
        out.reserve(poly.size());
        for (Vec2 const& p : poly)
            out.emplace_back(p.x, p.y, z, 0.f);
        return out;
    }
}

void BrdIncendius::RegisterIncendiusHardMode(IncendiusHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

void BrdIncendius::RegisterIncendiusIdleHook(IncendiusIdleHook hook)
{
    IdleHook() = std::move(hook);
}

std::unique_ptr<IncendiusHardMode> BrdIncendius::CreateIncendiusHardMode(Creature* boss)
{
    IncendiusHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// -------------------------------------------------------------------------------------------------------------------
// Ember of Incendius 300794 (IN6): rolls to The Black Anvil and never fights. The boss reads where it is (arrived,
// dead) and counts it; the Ember only moves, re-aimed every second so a slow, a root or a stun holds it back.
// -------------------------------------------------------------------------------------------------------------------

struct npc_brd_ember_of_incendius : public ScriptedAI
{
    explicit npc_brd_ember_of_incendius(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Nobody left to fight (the boss's wipe despawns it anyway): gone, never a walk home.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    // The boss starts the roll: `speed` yd/s toward the Anvil.
    void Roll(float speed)
    {
        _speed = speed;
        _rolling = true;
        _aimMs = 0;
        Aim();
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim() || !_rolling)
            return;
        _aimMs += diff;
        if (_aimMs < kEmberReaimMs)
            return;
        _aimMs = 0;
        Aim();
    }

private:
    void Aim()
    {
        if (!me->IsAlive() || me->HasUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED |
            UNIT_STATE_FLEEING | UNIT_STATE_DISTRACTED))
            return;
        // A slow on the Ember cuts its roll (its run speed rate against the template's).
        float rate = 1.f;
        if (CreatureTemplate const* t = me->GetCreatureTemplate())
            if (t->speed_run > 0.f)
                rate = std::clamp(me->GetSpeedRate(MOVE_RUN) / t->speed_run, 0.1f, 1.5f);
        me->GetMotionMaster()->MovePoint(1, kAnvil.x, kAnvil.y, kAnvil.z, FORCED_MOVEMENT_RUN, _speed * rate);
    }

    float _speed = 1.f;
    uint32 _aimMs = 0;
    bool _rolling = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Lord Incendius 9017
// -------------------------------------------------------------------------------------------------------------------

struct boss_lord_incendius_rework : public BossAI, public IncendiusFight
{
    explicit boss_lord_incendius_rework(Creature* creature)
        : BossAI(creature, BOSS_INCENDIUS), _arena(FightArena(), LeashOptions(kBossLogName)),
          _floor(CausewayFloor()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

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

        Cleanup(false);     // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        bool hardMode = _heroic && instance && instance->GetData(DATA_CINDER_USED) != 0;
        if (hardMode)
        {
            // The handler first: a lit Cinder with no handler registered runs the normal heroic.
            _hardMode = CreateIncendiusHardMode(me);
            if (!_hardMode)
            {
                LOG_WARN("module", "brd incendius: the Cinder is lit but no hard mode handler is registered; the pull "
                    "runs as a normal heroic");
                hardMode = false;
            }
        }
        OnBossPull(me, kBossLogName, hardMode);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_INCENDIUS;
        Mechanic::BeginEncounter(me, options);
        Describe();

        DungeonKit::Arena arena = FightArena();
        DungeonKit::ArenaGuardOptions guard = LeashOptions(kBossLogName);
        if (_hardMode)
            _hardMode->ConfigureArena(*this, arena, guard);
        _arena.Configure(std::move(arena), std::move(guard));
        _arena.Engage(me);

        _rebirthsLeft = RebirthsFor(_heroic);
        if (_hardMode)
            _rebirthsLeft = _hardMode->Rebirths(*this, _rebirthsLeft);
        if (_rebirthsLeft)
            _lethal.Reset();
        else
            _lethal.Disarm();
        ArmFallWatch();

        _curse.Start(_beatMs, kCurseFirstMs);
        _burst.Start(_beatMs, kBurstFirstMs);
        _storm.Start(_beatMs, kFireStormFirstMs);
        _fist.Start(_beatMs, kFistFirstMs);
        if (LavaSurgeOn())
            _surge.Start(_beatMs, kSurgeFirstMs);

        Log("engage", Acore::StringFormat("heroic={} hardmode={} handler={} rebirths={} health={} at=({:.1f}, {:.1f})",
            _heroic ? 1 : 0, hardMode ? 1 : 0, _hardMode ? 1 : 0, _rebirthsLeft, me->GetMaxHealth(),
            me->GetPositionX(), me->GetPositionY()));
        if (_hardMode)
        {
            _hardMode->OnEngage(*this);
            // The kit's `pull` line above logs his health before the hard mode changes it.
            Log("pull-health", Acore::StringFormat("health={} hardmode=1", me->GetMaxHealth()));
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    // The final death (each shatter before it held him at 1 health): the credit and the loot (filled by Unit::Kill
    // before this runs; the hard mode bit is the instance's, set at the trigger and the pull).
    void JustDied(Unit* killer) override
    {
        Talk(YELL_IN_DEATH);
        BossAI::JustDied(killer);
        Log("death", Acore::StringFormat("rebirths={} embers-arrived={} embers-killed={} steps={} hardmode={} "
            "killer={}", _rebirthsDone, _embersArrived, _embersKilled, _crumbleSteps, _hardMode ? 1 : 0,
            killer ? killer->GetName() : "none"));
        Cleanup(true);
    }

    // The Embers and the looks are props of the fight: never zoned into it here (an Ember gets its threat list by
    // hand).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        if (_shattered)
        {
            damage = 0;     // gone: nothing lands on him until he reforms
            return;
        }
        if (_engaged && _rebirthsLeft > 0)
            _lethal.Intercept(me, damage, [this]()
            {
                _shatterPending = true;     // the shatter runs at the next AI tick, outside the damage path
            });
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id == SPELL_IN_FIERY_BURST)
            Log("fiery-burst-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsEngaged() && me->IsAlive() && IdleHook())
            IdleHook()(me, diff);
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        _fall.Update(me, diff);
        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);

        if (_shatterPending)
            Shatter();
        if (_shattered)
        {
            UpdateShatter();
            return;
        }

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        UpdateNeckGrip(diff);

        _beatMs += diff;
        UpdateBeats();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!_hardMode || _hardMode->Melee(*this))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        if (_curse.Due(_beatMs))
        {
            _curse.Fired(_beatMs, kCurseEveryMs);
            Curse();
        }
        if (_storm.Due(_beatMs))
        {
            _storm.Fired(_beatMs, FireStormEveryMs());
            FireStorm(nullptr);
        }
        if (_fist.Due(_beatMs))
        {
            _fist.Fired(_beatMs, kFistEveryMs);
            MagmaFist(nullptr);
        }
        if (_surge.Due(_beatMs))
        {
            _surge.Fired(_beatMs, kSurgeEveryMs(_heroic));
            if (LavaSurgeOn())
                LavaSurge();
        }
        if (_burst.Due(_beatMs) && !me->HasUnitState(UNIT_STATE_CASTING))
            _burst.Start(_beatMs, FieryBurst() ? urand(kBurstMinMs, kBurstMaxMs) : 1000u);
    }

    // The hard mode's multiplier on his own reference hits (Firelord's Will); 1 on any other pull.
    float HardModeScale()
    {
        return _hardMode ? _hardMode->DamageScale(*this) : 1.f;
    }

    // R-1-B m4 (orchestrator default): once the necks are sealed, a player of the fight standing on the causeway past
    // one is put back onto the arena (a near teleport: a jump would cross the lethal seal) after kNeckGripGraceMs.
    void UpdateNeckGrip(uint32 diff)
    {
        if (!_necksSealed)
            return;
        _neckCheckMs += diff;
        if (_neckCheckMs < kNeckGripCheckMs)
            return;
        uint32 const step = _neckCheckMs;
        _neckCheckMs = 0;
        for (Player* player : FightPlayers())
        {
            if (player->IsFalling() || player->IsInFlight() || player->IsBeingTeleported())
                continue;
            int const side = PastSealedNeck(DungeonKit::PlaneOf(player), player->GetPositionZ());
            if (!_neckGrip.Update(player->GetGUID().GetRawValue(), side == 0, step))
                continue;
            Vec2 const land = NeckGripLanding(side);
            float const z = FloorZ(me, land.x, land.y);
            player->NearTeleportTo(land.x, land.y, z + 0.5f, DungeonKit::BearingTo(land, kAnvil.XY()));
            _neckGrip.Gripped(player->GetGUID().GetRawValue());
            Log("neck-grip", Acore::StringFormat("player={} side={} to=({:.1f}, {:.1f})", player->GetName(),
                side > 0 ? "east" : "west", land.x, land.y));
        }
    }

    // IN1: the copy of Curse of the Elemental Lord on everyone within 45 yd (triggered: never waits on a cast bar).
    void Curse()
    {
        me->CastSpell(me, SPELL_IN_CURSE, true);
        Log("curse", Acore::StringFormat("radius={:.0f} fire={:.0f}%", kCurseRadiusYd, kCurseFirePct));
    }

    // IN2: the 1.5 s cast on his victim; its 10 yd burst hits everyone round it (the kit's refflat script).
    bool FieryBurst()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        bool const cast = me->CastSpell(victim, SPELL_IN_FIERY_BURST, false) == SPELL_CAST_OK;
        if (cast)
            Log("fiery-burst", Acore::StringFormat("on={} pct={:.0f}", victim->GetName(), kBurstPct(_heroic)));
        return cast;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IN3 Fire Storm
    // ----------------------------------------------------------------------------------------------------------------

    MechanicHandle FireStorm(Player* forced) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank too (ruling 88)
        Player* target = forced ? forced : DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            Log("fire-storm", "no target");
            return {};
        }
        Position const at = GroundUnder(target);
        uint32 const life = FireStormLifeMs();
        float const pct = kFireStormPct(_heroic) * HardModeScale();
        MechanicRef ref = Mechanic::Circle(me, at, kFireStormRadiusYd, Ms(kFireStormWarnMs));
        ref.Persistent(Ms(life), Ms(kFireStormTickMs)).Damage(pct).TankDamage(pct).Spell(SPELL_IN_FIRE_STORM)
            .Rider(DungeonKit::SPELL_KIT_STANDING_IN_IT).Within(Bounds()).Tag(TAG_IN_FIRE_STORM);
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return {};
        Track(handle);
        DoCastSelf(SPELL_IN_FIRE_STORM_CAST, true);
        // The lava pool appears with the patch (after the marker), on a stalker for the patch's life.
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        me->m_Events.AddEventAtOffset([map, guid, at, life]()
        {
            if (boss_lord_incendius_rework* ai = AIOf(map, guid))
                if (ai->_engaged)
                    ai->LookAt(at, SPELL_IN_FIRE_STORM_PATCH, life);
        }, Ms(kFireStormWarnMs));
        Log("fire-storm", Acore::StringFormat("on={} at=({:.1f}, {:.1f}, {:.1f}) r={:.0f} life={}s pct={:.0f}",
            target->GetName(), at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), kFireStormRadiusYd,
            life / 1000, pct));
        return handle;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IN4 Magma Fist
    // ----------------------------------------------------------------------------------------------------------------

    MechanicHandle MagmaFist(Player* forced) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = _hardMode && !_hardMode->MagmaFistOnTank(*this);   // ruling 88; the hard mode: ruling 90
        Player* target = forced ? forced : DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            Log("magma-fist", "no target");
            return {};
        }
        Vec2 const boss = DungeonKit::PlaneOf(me);
        Vec2 const to = DungeonKit::PlaneOf(target);
        float const facing = DungeonKit::BearingTo(boss, to);
        float const distance = DungeonKit::Distance(boss, to);
        // The hard mode's giant stands far out over the lava: the line starts where it still reaches past a far
        // target (R-1-B m3). It still crosses the reach band: a tank standing in its path is hit (ruling 88).
        float const offset = _hardMode && _hardMode->FistFromNearEnd(*this) ? FistStartOffset(distance) : 0.f;
        Vec2 const from{ boss.x + std::cos(facing) * offset, boss.y + std::sin(facing) * offset };
        float const length = FistLength(distance - offset);
        float const pct = kFistPct(_heroic) * HardModeScale();
        Position const start(from.x, from.y, FloorZ(me, from.x, from.y), facing);
        MechanicRef ref = Mechanic::Line(me, start, facing, length, kFistWidthYd, Ms(kFistWarnMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_IN_MAGMA_FIST).Weakened().Within(Bounds())
            .Tag(TAG_IN_MAGMA_FIST);
        ref.OnHit(OnIncendiusUnit([facing](boss_lord_incendius_rework& ai, Unit* hit)
        {
            ai.FistThrow(hit, facing);
        }));
        ref.OnResolve(OnIncendius([start, facing, length](boss_lord_incendius_rework& ai,
            BossMechanics::ResolveResult const& r)
        {
            ai.FistLanded(start, facing, length, r.hits.size());
        }));
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return {};
        Track(handle);
        me->SetFacingTo(facing);
        DoCastSelf(SPELL_IN_MAGMA_FIST_RING, true);
        Log("magma-fist", Acore::StringFormat("on={} tank={} length={:.0f} offset={:.0f} width={:.0f} pct={:.0f}",
            target->GetName(), me->GetVictim() == target ? 1 : 0, length, offset, kFistWidthYd, pct));
        return handle;
    }

    // A unit the fist hit: thrown 10 yd along the line (on the floor, or over the edge).
    void FistThrow(Unit* hit, float facing)
    {
        if (!hit || !hit->IsAlive())
            return;
        DungeonKit::EdgePushResult const r = DungeonKit::PushAlong(hit, std::span<Vec2 const>(_floor), facing,
            kFistThrowYd);
        Log("magma-fist-throw", Acore::StringFormat("unit={} over-edge={} yd={:.1f}", hit->GetName(),
            r.overEdge ? 1 : 0, r.distance));
    }

    void FistLanded(Position const& start, float facing, float length, std::size_t hits)
    {
        float const x = start.GetPositionX() + std::cos(facing) * length;
        float const y = start.GetPositionY() + std::sin(facing) * length;
        me->CastSpell(x, y, FloorZ(me, x, y), SPELL_IN_MAGMA_FIST_WAVE, true);
        Log("magma-fist-landed", Acore::StringFormat("hits={}", hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IN5 Lava Surge
    // ----------------------------------------------------------------------------------------------------------------

    MechanicHandle LavaSurge(std::optional<Side> forced = std::nullopt)
    {
        uint32 southEast = 0;
        uint32 northWest = 0;
        for (Player* player : FightPlayers())
        {
            if (SideOf(DungeonKit::PlaneOf(player)) == Side::SouthEast)
                ++southEast;
            else
                ++northWest;
        }
        Side const side = forced ? *forced : PickSurgeSide(southEast, northWest, urand(0, 1));
        Band const strip = SurgeStrip(side, _crumbleSteps);
        float const pct = kSurgePct(_heroic);
        Position const from = OnFloor(me, strip.from);
        Position const to = OnFloor(me, strip.to);
        MechanicRef ref = Mechanic::Line(me, from, to, strip.width, Ms(kSurgeWarnMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_IN_LAVA_SURGE).Weakened().Within(Bounds()).Tag(TAG_IN_LAVA_SURGE);
        ref.OnResolve(OnIncendius([strip](boss_lord_incendius_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.SurgeLanded(strip, r.hits.size());
        }));
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return {};
        Track(handle);
        Log("lava-surge", Acore::StringFormat("side={} players-se={} players-nw={} steps={} pct={:.0f}",
            SideName(side), southEast, northWest, _crumbleSteps, pct));
        return handle;
    }

    void SurgeLanded(Band const& strip, std::size_t hits)
    {
        for (uint32 i = 0; i < kSurgeBursts; ++i)
        {
            float const t = (static_cast<float>(i) + 0.5f) / static_cast<float>(kSurgeBursts);
            float const x = strip.from.x + (strip.to.x - strip.from.x) * t;
            float const y = strip.from.y + (strip.to.y - strip.from.y) * t;
            me->CastSpell(x, y, FloorZ(me, x, y), SPELL_IN_LAVA_SURGE_BURST, true);
        }
        Log("lava-surge-landed", Acore::StringFormat("hits={}", hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IN6 / IN7 Shatter and Reborn
    // ----------------------------------------------------------------------------------------------------------------

    void Shatter()
    {
        _shatterPending = false;
        if (_shattered || !_rebirthsLeft || !me->IsAlive())
            return;
        _shattered = true;
        --_rebirthsLeft;
        ++_rebirthsDone;
        _shatterMs = _clockMs;
        _trapClosed = false;
        _arrivedNow = 0;

        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MoveIdle();
        me->SetReactState(REACT_PASSIVE);
        Talk(YELL_IN_SHATTER);
        LookAt(me->GetPosition(), SPELL_IN_SHATTER, 3000);     // on a stalker: he is gone this tick
        me->RemoveAllAuras();                   // the players' DoTs and debuffs go with him
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetVisible(false);
        uint32 const spawned = SpawnEmbers();
        Log("shatter", Acore::StringFormat("rebirth={} left={} embers={} at=({:.1f}, {:.1f})", _rebirthsDone,
            _rebirthsLeft, spawned, me->GetPositionX(), me->GetPositionY()));
    }

    uint32 SpawnEmbers()
    {
        uint32 spawned = 0;
        std::vector<Player*> const players = FightPlayers();
        for (Vec2 const& spot : EmberSpots(EmbersFor(_heroic), _crumbleSteps))
        {
            Position const at = OnFloor(me, spot, DungeonKit::BearingTo(spot, kAnvil.XY()));
            TempSummon* ember = me->SummonCreature(NPC_BRD_EMBER_OF_INCENDIUS, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
                kEmberCorpseMs);
            if (!ember)
                continue;
            ++spawned;
            Mechanic::TrackUnit(me, ember);
            // Everyone in the fight at 0 (a one-entry threat list evades); it never attacks.
            for (Player* player : players)
                ember->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
            _embers.push_back({ ember->GetGUID(), false, false });
            if (auto* ai = dynamic_cast<npc_brd_ember_of_incendius*>(ember->AI()))
                ai->Roll(EmberSpeed(DungeonKit::Distance(spot, kAnvil.XY())));
        }
        return spawned;
    }

    // Each tick while shattered: the Embers (arrived, killed), the trap at reform - 5 s, the reform at 12 s.
    void UpdateShatter()
    {
        PollEmbers(false);
        uint64 const since = _clockMs - _shatterMs;
        if (!_trapClosed && since >= kBandRaiseAfterShatterMs)
        {
            _trapClosed = true;
            CloseTrap("rebirth");
        }
        if (since >= kReformMs)
            Reform();
    }

    // An Ember within kEmberArriveYd of the Anvil arrived (`reform`: every Ember still alive joins him now).
    void PollEmbers(bool reform)
    {
        for (EmberState& e : _embers)
        {
            if (e.arrived || e.killed)
                continue;
            Creature* ember = me->GetMap()->GetCreature(e.guid);
            if (!ember || !ember->IsAlive())
            {
                e.killed = true;
                ++_embersKilled;
                Log("ember-killed", Acore::StringFormat("killed={}", _embersKilled));
                continue;
            }
            if (!reform && DungeonKit::Distance(DungeonKit::PlaneOf(ember), kAnvil.XY()) > kEmberArriveYd)
                continue;
            e.arrived = true;
            ++_arrivedNow;
            ++_embersArrived;
            ember->CastSpell(ember, SPELL_IN_EMBER_ARRIVES, true);
            ember->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            ember->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            ember->DespawnOrUnsummon(Ms(500));
            Log("ember-arrived", Acore::StringFormat("arrived={} at-reform={}", _arrivedNow, reform ? 1 : 0));
        }
    }

    void Reform()
    {
        PollEmbers(true);
        _embers.clear();
        float const pct = RebornHealthPct(_arrivedNow);
        Vec2 const spotXY = ReformSpot();
        Position const spot = OnFloor(me, spotXY, DungeonKit::BearingTo(spotXY, kOrigin));
        me->NearTeleportTo(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), spot.GetOrientation());
        me->SetVisible(true);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetHealth(std::max<uint32>(1, static_cast<uint32>(me->GetMaxHealth() * pct / 100.f)));
        _shattered = false;
        if (_rebirthsLeft)
            _lethal.Reset();        // armed again: the next lethal hit shatters him again
        else
            _lethal.Disarm();       // the next death is real
        DoCastSelf(SPELL_IN_REBORN, true);
        Talk(YELL_IN_REBORN);
        Log("reborn", Acore::StringFormat("rebirth={} embers-arrived={} health={:.0f}% left={}", _rebirthsDone,
            _arrivedNow, pct, _rebirthsLeft));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IN8 The trap closes: the neck seals and the long-edge crumble steps
    // ----------------------------------------------------------------------------------------------------------------

    // The first rebirth seals the necks; rebirth n leaves CrumbleStepsAfter(n) steps.
    void CloseTrap(char const* why)
    {
        SealNecks(why);
        while (_crumbleSteps < CrumbleStepsAfter(_rebirthsDone))
            if (!Crumble(why))
                break;
    }

    bool NecksSealed() const override { return _necksSealed; }
    uint32 CrumbleSteps() const override { return _crumbleSteps; }

    bool SealNecks(char const* why) override
    {
        if (_necksSealed)
            return false;
        _necksSealed = true;
        WarnEdge();
        uint32 raised = 0;
        for (bool const east : { false, true })
            if (RaiseBand(NeckSeal(east), TAG_IN_NECK_SEAL, raised == 0))
                ++raised;
        Log("neck-seals", Acore::StringFormat("why={} bands={} width={:.0f}", why, raised, kNeckSealWidthYd));
        return true;
    }

    bool Crumble(char const* why) override
    {
        if (_crumbleSteps >= kCrumbleMaxSteps)
            return false;
        uint32 const step = ++_crumbleSteps;
        WarnEdge();
        uint32 raised = 0;
        for (std::size_t edge : kLongEdges)
            if (RaiseBand(CrumbleBand(_floor, edge, step), TAG_IN_CRUMBLE, raised == 0))
                ++raised;
        Log("crumble", Acore::StringFormat("why={} step={} depth={:.0f}-{:.0f} bands={}", why, step,
            CrumbledDepth(step - 1), CrumbledDepth(step), raised));
        return true;
    }

    // The 5 s warning's emote, once however many bands go up in the same tick.
    void WarnEdge()
    {
        if (_lastWarnMs && _clockMs < _lastWarnMs + 1000)
            return;
        _lastWarnMs = _clockMs ? _clockMs : 1;
        Talk(EMOTE_IN_EDGE_CRACKS);
    }

    // One lethal band on the floor: 5 s edge marker, then anyone inside is thrown over the real edge (the kit's
    // LethalBands, pets too). `emote`: this band's crumble says emote line 2 (once a step).
    bool RaiseBand(Band const& band, uint32 tag, bool emote)
    {
        if (band.width <= 0.f)
            return false;
        DungeonKit::LethalBandSpec spec;
        spec.from = OnFloor(me, band.from);
        spec.to = OnFloor(me, band.to);
        spec.width = band.width;
        spec.floor = _floor;
        spec.warn = Ms(kBandWarnMs);
        spec.pets = true;
        spec.pushSpell = SPELL_IN_CRUMBLING_GROUND;
        spec.tag = tag;
        spec.dungeon = kLogDungeon;
        spec.boss = kBossLogName;
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        spec.onCrumble = [map, guid, band, emote]()
        {
            if (boss_lord_incendius_rework* ai = AIOf(map, guid))
                ai->BandCrumbled(band, emote);
        };
        return static_cast<bool>(_bands.Add(me, spec));
    }

    // The crumble: Lava Strike along the band, the cracks for the rest of the fight (V-1: a crack every 10 yd).
    void BandCrumbled(Band const& band, bool emote)
    {
        if (emote && (!_lastCrumbleMs || _clockMs >= _lastCrumbleMs + 1000))
        {
            _lastCrumbleMs = _clockMs ? _clockMs : 1;
            Talk(EMOTE_IN_CRUMBLES);
        }
        float const length = DungeonKit::Distance(band.from, band.to);
        uint32 const looks = static_cast<uint32>(length / kCrackSpacingYd) + 1;
        for (uint32 i = 0; i < looks; ++i)
        {
            float const t = looks == 1 ? 0.5f : static_cast<float>(i) / static_cast<float>(looks - 1);
            Vec2 const p{ band.from.x + (band.to.x - band.from.x) * t, band.from.y + (band.to.y - band.from.y) * t };
            Position const at = OnFloor(me, p);
            me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_IN_CRUMBLE_BURST, true);
            LookAt(at, SPELL_IN_CRUMBLED_EDGE, 0);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Falls (ruling 48): caught 20 yd under the causeway over the lake, dead
    // ----------------------------------------------------------------------------------------------------------------

    void ArmFallWatch()
    {
        DungeonKit::FallWatchSpec spec;
        spec.deckZ = kFloorZ;
        spec.below = kFallCatchBelowYd;
        spec.region = LakeRegion();
        spec.grace = Ms(kFallGraceMs);
        spec.pets = true;
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        spec.onCatch = [map, guid](Unit* caught)
        {
            if (boss_lord_incendius_rework* ai = AIOf(map, guid))
                ai->FallCaught(caught);
        };
        _fall.Arm(std::move(spec));
    }

    void FallCaught(Unit* caught)
    {
        if (!caught || !caught->IsAlive())
            return;
        Log("fall", Acore::StringFormat("unit={} pet={} z={:.1f}", caught->GetName(), caught->IsPlayer() ? 0 : 1,
            caught->GetPositionZ()));
        Unit::Kill(me, caught);
    }

    bool ThrowOff(Unit* unit, std::optional<float> bearing, char const* why) override
    {
        if (!unit || !unit->IsAlive())
            return false;
        DungeonKit::EdgePushOptions options;
        options.bearing = bearing;
        me->CastSpell(unit, SPELL_IN_CRUMBLING_GROUND, true);
        DungeonKit::EdgePushResult const r = DungeonKit::PushOverEdge(unit, std::span<Vec2 const>(_floor), options);
        Log("thrown-off", Acore::StringFormat("why={} unit={} pushed={} yd={:.1f}", why, unit->GetName(),
            r.pushed ? 1 : 0, r.distance));
        return r.pushed;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IncendiusFight (D12's view) and the bots
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Boss() override { return me; }
    bool Heroic() const override { return _heroic; }
    IncendiusHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 FightMs() const override { return _clockMs; }
    std::vector<Vec2> const& Floor() const override { return _floor; }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> players;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            if (Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr)
                if (player->IsAlive() && !player->IsGameMaster())
                    players.push_back(player);
        return players;
    }

    BossMechanics::SpotBounds Bounds() const override
    {
        return BossMechanics::SpotBounds().Polygon(ToPositions(SafeFloor(_crumbleSteps), kFloorZ), kFloorZ - 4.f,
            kFloorZ + 6.f);
    }

    void HoldBeats(uint64 untilMs) override
    {
        if (untilMs <= _clockMs)
            return;
        uint64 const until = _beatMs + (untilMs - _clockMs);
        _storm.NotBefore(until);
        _fist.NotBefore(until);
        Log("hold", Acore::StringFormat("ms={}", untilMs - _clockMs));
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _handles.push_back(handle);
    }

    void TrackSummon(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // Kill order: the Embers (every role; AoE welcome). Fiery Burst on the interrupt list (a reward on normal,
    // expected on heroic: a higher priority). The Curse on the dispel list (a reward).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_INCENDIUS, SPELL_IN_FIERY_BURST, _heroic ? 3 : 1);
        d.dispels.emplace_back(SPELL_IN_CURSE, 1);
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_EMBER_OF_INCENDIUS, 2, BossMechanics::Who::Any)
            .AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest` entry points
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestShatter()
    {
        if (!me->IsEngaged())
            return "Lord Incendius must be in combat.";
        if (_shattered)
            return "He is already shattered.";
        if (!_rebirthsLeft)
            return "No rebirth left: the next death is real.";
        me->SetHealth(1);
        _shatterPending = true;
        return {};
    }

    std::string TestSurge(Player* gm)
    {
        if (!me->IsEngaged())
            return "Lord Incendius must be in combat.";
        if (!LavaSurge(gm ? std::optional<Side>(SideOf(DungeonKit::PlaneOf(gm))) : std::nullopt))
            return "The surge was refused.";
        return {};
    }

    std::string TestNeeds(char const* what) const
    {
        if (!me->IsEngaged())
            return Acore::StringFormat("Lord Incendius must be in combat ({}).", what);
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s beats={}s heroic={} hardmode={} shattered={} rebirths-left={} done={} "
            "embers-arrived={} killed={} necks={} steps={} bands={} fallwatch={} curse={} burst={} storm={} fist={} "
            "surge={}", _clockMs / 1000, _beatMs / 1000, _heroic ? 1 : 0, _hardMode ? 1 : 0, _shattered ? 1 : 0,
            _rebirthsLeft, _rebirthsDone, _embersArrived, _embersKilled, _necksSealed ? 1 : 0, _crumbleSteps,
            _bands.Count(), _fall.Armed() ? 1 : 0, _curse.On() ? "on" : "off", _burst.On() ? "on" : "off",
            _storm.On() ? "on" : "off", _fist.On() ? "on" : "off", _surge.On() ? "on" : "off");
    }

private:
    struct EmberState
    {
        ObjectGuid guid;
        bool arrived = false;
        bool killed = false;
    };

    static boss_lord_incendius_rework* AIOf(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_lord_incendius_rework*>(boss->AI());
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there (the map and the guid only:
    // a lambda the registry keeps never holds a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnIncendius(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_lord_incendius_rework* ai = AIOf(map, guid))
                fn(*ai, result);
        };
    }

    template <typename Fn>
    std::function<void(Unit*)> OnIncendiusUnit(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](Unit* hit)
        {
            if (boss_lord_incendius_rework* ai = AIOf(map, guid))
                fn(*ai, hit);
        };
    }

    // A look on a stalker at `at` (an aura's state, or a one-shot): `lifeMs` 0 = until the fight's cleanup.
    void LookAt(Position const& at, uint32 spell, uint32 lifeMs)
    {
        if (!StalkerExists())
            return;
        TempSummon* stalker = lifeMs ? me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN, lifeMs)
            : me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (stalker)
            stalker->CastSpell(stalker, spell, true);
    }

    bool LavaSurgeOn() const
    {
        return !_hardMode || _hardMode->LavaSurge(*this);
    }

    uint32 FireStormLifeMs() const
    {
        return _hardMode ? _hardMode->FireStormLifeMs(*this, kFireStormLifeMs) : kFireStormLifeMs;
    }

    uint32 FireStormEveryMs() const
    {
        return _hardMode ? _hardMode->FireStormEveryMs(*this, kFireStormEveryMs(_heroic)) : kFireStormEveryMs(_heroic);
    }

    // Every way the fight ends (and a new pull): the hard mode undone, the zones, the bands, the watch, the Embers and
    // the looks gone, the Curse off every player, his flags, look and react state back.
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        for (MechanicHandle const& h : _handles)
            Mechanic::Cancel(me, h);
        _handles.clear();
        _bands.Clear(me);
        _fall.Disarm();
        for (EmberState const& e : _embers)
            if (Creature* ember = me->GetMap()->GetCreature(e.guid))
                ember->DespawnOrUnsummon();
        _embers.clear();
        summons.DespawnAll();
        if (me->IsInWorld())
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_IN_CURSE);
        if (_shattered)
        {
            me->SetVisible(true);
            me->SetControlled(false, UNIT_STATE_ROOT);
        }
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        if (me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);
        _arena.Reset();
        _lethal.Reset();
        _curse.Stop();
        _burst.Stop();
        _storm.Stop();
        _fist.Stop();
        _surge.Stop();
        _engaged = false;
        _shattered = false;
        _shatterPending = false;
        _trapClosed = false;
        _necksSealed = false;
        _neckGrip.Clear();
        _neckCheckMs = 0;
        _crumbleSteps = 0;
        _rebirthsLeft = 0;
        _rebirthsDone = 0;
        _embersArrived = 0;
        _embersKilled = 0;
        _arrivedNow = 0;
        _clockMs = 0;
        _beatMs = 0;
        _shatterMs = 0;
        _lastWarnMs = 0;
        _lastCrumbleMs = 0;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalGuard _lethal;
    DungeonKit::LethalBands _bands;
    DungeonKit::FallWatch _fall;
    std::vector<Vec2> const _floor;
    std::unique_ptr<IncendiusHardMode> _hardMode;
    std::vector<MechanicHandle> _handles;
    std::vector<EmberState> _embers;
    FightClock _curse;
    FightClock _burst;
    FightClock _storm;
    FightClock _fist;
    FightClock _surge;
    DungeonKit::GripTracker _neckGrip{ kNeckGripGraceMs, kNeckGripCooldownMs };
    uint32 _neckCheckMs = 0;
    uint64 _clockMs = 0;            // ms since the pull (every AI tick in combat)
    uint64 _beatMs = 0;             // the beats' clock: stands still while he is shattered
    uint64 _shatterMs = 0;
    uint64 _lastWarnMs = 0;
    uint64 _lastCrumbleMs = 0;
    uint32 _rebirthsLeft = 0;
    uint32 _rebirthsDone = 0;
    uint32 _crumbleSteps = 0;
    uint32 _embersArrived = 0;
    uint32 _embersKilled = 0;
    uint32 _arrivedNow = 0;
    bool _heroic = false;
    bool _engaged = false;
    bool _shattered = false;
    bool _shatterPending = false;
    bool _trapClosed = false;
    bool _necksSealed = false;
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest brd incendius`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    boss_lord_incendius_rework* FindIncendiusAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_INCENDIUS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_lord_incendius_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Lord Incendius is not running boss_lord_incendius_rework (check the "
                "ScriptName).");
        return ai;
    }

    Player* GmPlayer(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* done)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Lord Incendius: {}", done);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_INCENDIUS, BOSS_INCENDIUS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Lord Incendius: {}", ai->TestState());
        return true;
    }

    // `.dbtest brd incendius firestorm`: IN3 under you (`.gm off` to take the ticks).
    bool HandleFireStorm(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("firestorm");
        if (error.empty() && !ai->FireStorm(GmPlayer(handler)))
            error = "The Fire Storm was refused.";
        return Report(handler, error, "Fire Storm marked under you (2 s, then the 5 yd patch).");
    }

    // `.dbtest brd incendius fist`: IN4 through you (the throw follows the line; near an edge it is a fall).
    bool HandleFist(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("fist");
        if (error.empty() && !ai->MagmaFist(GmPlayer(handler)))
            error = "The Magma Fist was refused.";
        return Report(handler, error, "Magma Fist aimed through you (2 s line).");
    }

    // `.dbtest brd incendius surge`: IN5 on your side of the bulge.
    bool HandleSurge(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestSurge(GmPlayer(handler)), "Lava Surge marked on your side (3 s).");
    }

    // `.dbtest brd incendius curse`: IN1 now.
    bool HandleCurse(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        ai->Curse();
        return Report(handler, {}, "Curse of the Elemental Lord cast (45 yd).");
    }

    // `.dbtest brd incendius burst`: IN2 on his victim (kick it).
    bool HandleBurst(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("burst");
        if (error.empty() && !ai->FieryBurst())
            error = "Fiery Burst did not cast (no victim, or already casting).";
        return Report(handler, error, "Fiery Burst started (1.5 s).");
    }

    // `.dbtest brd incendius shatter`: IN6 now (a rebirth must be left); IN7 and IN8 follow on their timers.
    bool HandleShatter(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestShatter(), "shattering (the Embers roll; he reforms in 12 s).");
    }

    // `.dbtest brd incendius seal`: IN8's neck seals now.
    bool HandleSeal(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("seal");
        if (error.empty() && !ai->SealNecks("dbtest"))
            error = "The necks are already sealed.";
        return Report(handler, error, "the necks seal in 5 s.");
    }

    // `.dbtest brd incendius crumble`: the next 2 yd of both long edges now.
    bool HandleCrumble(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("crumble");
        if (error.empty() && !ai->Crumble("dbtest"))
            error = "Every crumble step is already down.";
        return Report(handler, error, "the next 2 yd of both long edges crumble in 5 s.");
    }

    // `.dbtest brd incendius throwoff`: you, over the nearest edge (`.gm off`: the FallWatch kills you in the lake).
    bool HandleThrowOff(ChatHandler* handler)
    {
        boss_lord_incendius_rework* ai = FindIncendiusAI(handler);
        if (!ai)
            return false;
        std::string error = ai->TestNeeds("throwoff");
        if (error.empty() && !ai->ThrowOff(GmPlayer(handler), std::nullopt, "dbtest"))
            error = "The throw was refused.";
        return Report(handler, error, "thrown over the edge.");
    }

    ChatCommandTable const& BossLordIncendiusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "firestorm", HandleFireStorm, SEC_GAMEMASTER, Console::No },
            { "fist",      HandleFist,      SEC_GAMEMASTER, Console::No },
            { "surge",     HandleSurge,     SEC_GAMEMASTER, Console::No },
            { "curse",     HandleCurse,     SEC_GAMEMASTER, Console::No },
            { "burst",     HandleBurst,     SEC_GAMEMASTER, Console::No },
            { "shatter",   HandleShatter,   SEC_GAMEMASTER, Console::No },
            { "seal",      HandleSeal,      SEC_GAMEMASTER, Console::No },
            { "crumble",   HandleCrumble,   SEC_GAMEMASTER, Console::No },
            { "throwoff",  HandleThrowOff,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lord_incendius_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lord_incendius_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_ember_of_incendius, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("incendius", BossLordIncendiusTestCommands());
}
