/*
 * mod-dungeon-bosses, the shared dungeon kit: the arena guard and cell confinement (ArenaGuard.h). The guard is the
 * Deadmines Pilot's Greenskin "aboard" code (PT1 fix: PullAboard, KeepAboard, Grip) with the deck replaced by an Arena.
 */

#include "ArenaGuard.h"
#include "CombatManager.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "ThreatManager.h"
#include "Unit.h"
#include <tuple>
#include <unordered_set>
#include <utility>

namespace DungeonKit
{
    namespace
    {
        // A prop on the threat list that is nobody's target: a non-player unit that cannot be attacked or selected (a
        // scripted vehicle with a player aboard picks up threat for its passenger: Vehicle.cpp, ThreatManager's
        // redirect to the vehicle). It never counts as "inside" and is never gripped. Not IsControlledByPlayer(): a
        // vehicle charmed by its passenger reports true; not offline references: those also drop feigning hunters.
        bool IsProp(Unit const* unit)
        {
            return !unit->IsPlayer()
                && (unit->HasUnitFlag(UNIT_FLAG_NON_ATTACKABLE) || unit->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE));
        }

        // Everyone in combat with `boss`: his threat list (players, pets, guardians, bots; DoZoneInCombat adds every
        // player and their pets at the pull), less the props (IsProp).
        std::vector<Unit*> CombatUnits(Creature const* boss)
        {
            std::vector<Unit*> out;
            for (ThreatReference const* ref : boss->GetThreatMgr().GetUnsortedThreatList())
                if (Unit* unit = ref->GetVictim())
                    if (!IsProp(unit))
                        out.push_back(unit);
            return out;
        }

        // The unit behind a tracker key is gone from `owner`'s map (logged out, left the instance, despawned).
        bool LeftMap(WorldObject const* owner, std::uint64_t raw)
        {
            Unit const* unit = ObjectAccessor::GetUnit(*owner, ObjectGuid(raw));
            return !unit || !unit->IsInWorld() || !unit->IsInMap(owner);
        }
    }

    ArenaGuard::ArenaGuard(Arena arena, ArenaGuardOptions options)
    {
        Configure(std::move(arena), std::move(options));
    }

    void ArenaGuard::Configure(Arena arena, ArenaGuardOptions options)
    {
        _arena = std::move(arena);
        _options = std::move(options);
        _grip = GripTracker(_options.graceMs, _options.cooldownMs);
        _leash.Reset();
        _checkMs = 0;
        _emptyMs = 0;
        _holding = false;
        _switchedTo.Clear();
    }

    bool ArenaGuard::Contains(WorldObject const* o) const
    {
        return o && _arena.Contains(PlaneOf(o), o->GetPositionZ());
    }

    bool ArenaGuard::Grippable(Creature const* boss, Unit const* unit) const
    {
        return unit && unit->IsInWorld() && unit->IsAlive() && unit->IsInMap(boss) && !unit->IsTotem()
            && !unit->IsVehicle() && !unit->GetVehicle() && boss->GetExactDist2d(unit) <= _options.maxGripYd
            && !(_options.skipGrip && _options.skipGrip(boss, unit));
    }

    std::function<bool(Creature const*, Unit const*)> SkipEngagedWithOtherBoss(std::function<bool(uint32)> isBossEntry)
    {
        return [isBossEntry = std::move(isBossEntry)](Creature const* boss, Unit const* unit)
        {
            if (!unit || !isBossEntry)
                return false;
            for (auto const& [guid, ref] : unit->GetCombatManager().GetPvECombatRefs())
            {
                Unit const* other = ref ? ref->GetOther(unit) : nullptr;
                if (other && other != boss && other->IsCreature() && other->IsAlive()
                    && isBossEntry(other->GetEntry()))
                    return true;
            }
            return false;
        };
    }

    void ArenaGuard::Engage(Creature* boss)
    {
        if (!boss || !_options.gripOnPull || _arena.Empty())
            return;
        uint32 gripped = 0;
        for (Unit* unit : CombatUnits(boss))
            if (Grippable(boss, unit) && _grip.PullNow(unit->GetGUID().GetRawValue(), Contains(unit)))
            {
                Grip(boss, unit, "pull");
                ++gripped;
            }
        LOG_INFO(kLogCategory, "{} grip pull units={} gripped={}", _options.logPrefix, CombatUnits(boss).size(),
            gripped);
    }

    bool ArenaGuard::Update(Creature* boss, uint32 diff)
    {
        if (!boss || _arena.Empty())
            return true;
        _checkMs += diff;
        if (_checkMs < _options.checkMs)
            return true;
        uint32 const elapsed = _checkMs;
        _checkMs = 0;

        if (_options.evadeWhenBossOff
            && _leash.Update(Contains(boss), _options.leashSkipAirborne
                && (boss->HasUnitState(UNIT_STATE_JUMPING) || boss->IsFalling()), elapsed, _options.bossGraceMs))
        {
            _leash.Reset();
            LOG_INFO(kLogCategory, "{} grip leash at=({:.1f}, {:.1f}, {:.1f})", _options.logPrefix,
                boss->GetPositionX(), boss->GetPositionY(), boss->GetPositionZ());
            if (boss->IsAIEnabled && boss->AI())
                boss->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_BOUNDARY);
            return false;
        }

        if (_options.evadeNoTargetInsideMs)
        {
            bool anyInside = false;
            for (Unit* unit : CombatUnits(boss))
                if (unit->IsAlive() && Contains(unit))
                {
                    anyInside = true;
                    break;
                }
            _emptyMs = anyInside ? 0 : _emptyMs + elapsed;
            if (_emptyMs >= _options.evadeNoTargetInsideMs)
            {
                LOG_INFO(kLogCategory, "{} grip leash nobody-inside ms={}", _options.logPrefix, _emptyMs);
                _emptyMs = 0;
                if (boss->IsAIEnabled && boss->AI())
                    boss->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_BOUNDARY);
                return false;
            }
        }

        _grip.ForgetIf([boss](std::uint64_t raw) { return LeftMap(boss, raw); });
        if (_options.gripBack)
            for (Unit* unit : CombatUnits(boss))
                if (Grippable(boss, unit) && _grip.Update(unit->GetGUID().GetRawValue(), Contains(unit), elapsed))
                    Grip(boss, unit, _options.offArenaReason.c_str());

        if (_options.switchWhenVictimOff)
            UpdateSwitch(boss);

        if (!_options.holdWhileVictimOff)
            return true;
        // Never dragged off: no chasing a victim who is off the arena (the grip brings it back).
        Unit* victim = boss->GetVictim();
        bool const victimOff = victim && !Contains(victim);
        if (victimOff && boss->GetMotionMaster()->GetCurrentMovementGeneratorType() == CHASE_MOTION_TYPE)
        {
            boss->GetMotionMaster()->Clear(false);
            boss->StopMoving();
            if (!_holding)
                LOG_INFO(kLogCategory, "{} grip hold victim={}", _options.logPrefix, victim->GetName());
            _holding = true;
        }
        else if (!victimOff && _holding)
        {
            _holding = false;
            if (victim)
                boss->GetMotionMaster()->MoveChase(victim);
        }
        return true;
    }

    void ArenaGuard::UpdateSwitch(Creature* boss)
    {
        ThreatManager& threat = boss->GetThreatMgr();
        Unit* top = nullptr;        // the top of the threat list (what he would attack with no fixate)
        Unit* inside = nullptr;     // the highest-threat unit on the arena
        for (ThreatReference const* ref : threat.GetSortedThreatList())
        {
            Unit* unit = ref->IsAvailable() ? ref->GetVictim() : nullptr;
            if (!unit || !unit->IsAlive())
                continue;
            if (!top)
                top = unit;
            if (!inside && Contains(unit))
                inside = unit;
            if (inside)
                break;
        }
        Unit* const fixed = threat.GetFixateTarget();
        bool const ours = fixed && !_switchedTo.IsEmpty() && fixed->GetGUID() == _switchedTo;
        if (fixed && !ours)
            return;                 // the script's own fixate wins
        Unit* const want = top && !Contains(top) ? inside : nullptr;
        if (want && want == fixed)
            return;
        if (want)
        {
            threat.FixateTarget(want);
            _switchedTo = want->GetGUID();
            LOG_INFO(kLogCategory, "{} grip switch victim={} to={}", _options.logPrefix, top->GetName(),
                want->GetName());
        }
        else
        {
            if (ours)
            {
                threat.ClearFixate();
                LOG_INFO(kLogCategory, "{} grip switch back", _options.logPrefix);
            }
            _switchedTo.Clear();
        }
    }

    void ArenaGuard::Grip(Creature* boss, Unit* unit, char const* why)
    {
        if (!boss || !unit)
            return;
        Vec2 const from = PlaneOf(unit);
        float const fromZ = unit->GetPositionZ();

        // The floor band to land in: the boss's region, else the whole arena.
        ArenaRegion const* region = _arena.RegionAt(PlaneOf(boss), boss->GetPositionZ());
        float const searchZ = region ? region->zMax : _arena.ZMax();
        float const minZ = region ? region->zMin : _arena.ZMin();

        Vec2 dest;
        std::optional<float> fixedZ;
        if (_options.landing)
        {
            Position const p = _options.landing(boss, unit);
            dest = { p.GetPositionX(), p.GetPositionY() };
            if (_options.landingKeepsZ)
                fixedZ = p.GetPositionZ();
        }
        else
            dest = LandingToward(PlaneOf(boss), from, _options.landYd, _options.landBox);

        float z = 0.f;
        if (fixedZ)
            z = *fixedZ;
        else
        {
            z = boss->GetMapHeight(dest.x, dest.y, searchZ);
            if (z <= INVALID_HEIGHT || z < minZ)
                z = boss->GetPositionZ();
        }
        // The default landing must be on the arena (a gap, a ledge, outside every region): else the boss's spot.
        if (!_options.landing)
            std::tie(dest, z) = LandingOrBoss(_arena, dest, z, PlaneOf(boss), boss->GetPositionZ());
        float const dist = Distance(from, dest);
        JumpTo(unit, Position(dest.x, dest.y, z + 0.5f), _options.jumpSpeedXY, _options.minJumpSpeedZ,
            _options.gripSpell, boss);
        _grip.Gripped(unit->GetGUID().GetRawValue(), GripCooldownMs(_options.cooldownMs, dist, _options.jumpSpeedXY));
        LOG_INFO(kLogCategory, "{} grip {} unit={} from=({:.1f}, {:.1f}, {:.1f}) to=({:.1f}, {:.1f}, {:.1f}) "
            "dist={:.1f}", _options.logPrefix, why, unit->GetName(), from.x, from.y, fromZ, dest.x, dest.y, z, dist);
    }

    void ArenaGuard::Reset()
    {
        _grip.Clear();
        _leash.Reset();
        _checkMs = 0;
        _emptyMs = 0;
        _holding = false;
        _switchedTo.Clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Confinement
    // ----------------------------------------------------------------------------------------------------------------

    Confinement::Confinement(ConfineOptions options)
        : _options(std::move(options)), _jailTracker(_options.graceMs, _options.cooldownMs)
    {
    }

    void Confinement::ConfineIn(Unit const* unit, Arena cell, Position const& putBack)
    {
        if (!unit)
            return;
        ObjectGuid const guid = unit->GetGUID();
        for (Jail& j : _jails)
            if (j.unit == guid)
            {
                j.cell = std::move(cell);
                j.putBack = putBack;
                return;
            }
        _jails.push_back({ guid, std::move(cell), putBack });
    }

    uint32 Confinement::KeepOut(Arena cell, Position const& putOut)
    {
        Fence f;
        f.id = _nextFence++;
        f.cell = std::move(cell);
        f.putOut = putOut;
        f.tracker = GripTracker(_options.graceMs, _options.cooldownMs);
        _fences.push_back(std::move(f));
        return _fences.back().id;
    }

    void Confinement::Release(ObjectGuid unit)
    {
        std::erase_if(_jails, [unit](Jail const& j) { return j.unit == unit; });
        _jailTracker.Forget(unit.GetRawValue());
    }

    void Confinement::ReleaseKeepOut(uint32 id)
    {
        std::erase_if(_fences, [id](Fence const& f) { return f.id == id; });
    }

    void Confinement::Clear()
    {
        _jails.clear();
        _fences.clear();
        _jailTracker.Clear();
        _checkMs = 0;
    }

    bool Confinement::IsConfined(ObjectGuid unit) const
    {
        for (Jail const& j : _jails)
            if (j.unit == unit)
                return true;
        return false;
    }

    uint32 Confinement::PutAt(Unit* unit, Position const& at, char const* why)
    {
        uint32 cooldown = _options.cooldownMs;
        if (_options.jump)
        {
            cooldown = GripCooldownMs(cooldown, unit->GetExactDist2d(&at), _options.jumpSpeedXY);
            JumpTo(unit, at, _options.jumpSpeedXY, _options.minJumpSpeedZ);
        }
        else
            unit->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), unit->GetOrientation());
        LOG_INFO(kLogCategory, "{} {} unit={} to=({:.1f}, {:.1f}, {:.1f})", _options.logPrefix, why, unit->GetName(),
            at.GetPositionX(), at.GetPositionY(), at.GetPositionZ());
        return cooldown;
    }

    void Confinement::Update(WorldObject* owner, uint32 diff)
    {
        if (!owner || !owner->IsInWorld() || (_jails.empty() && _fences.empty()))
            return;
        _checkMs += diff;
        if (_checkMs < _options.checkMs)
            return;
        uint32 const elapsed = _checkMs;
        _checkMs = 0;
        Map* map = owner->GetMap();

        for (Jail const& j : _jails)
        {
            Unit* unit = ObjectAccessor::GetUnit(*owner, j.unit);
            if (!unit || !unit->IsAlive() || !unit->IsInMap(owner))
                continue;
            bool const inside = j.cell.Contains(PlaneOf(unit), unit->GetPositionZ());
            if (_jailTracker.Update(j.unit.GetRawValue(), inside, elapsed))
            {
                _jailTracker.Gripped(j.unit.GetRawValue(), PutAt(unit, j.putBack, "put-back"));
            }
        }

        if (_fences.empty())
            return;
        std::vector<Unit*> units;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
            {
                if (!player->IsAlive() || player->IsGameMaster())
                    continue;
                units.push_back(player);
                if (Pet* pet = player->GetPet())
                    units.push_back(pet);
            }
        std::unordered_set<uint64> seen;
        for (Unit* unit : units)
            seen.insert(unit->GetGUID().GetRawValue());
        for (Fence& f : _fences)
        {
            // Units that left the map (or died, or turned GM) start over when they come back.
            f.tracker.ForgetIf([&seen](std::uint64_t raw) { return !seen.count(raw); });
            for (Unit* unit : units)
            {
                if (IsConfined(unit->GetGUID()))
                    continue;
                bool const outside = !f.cell.Contains(PlaneOf(unit), unit->GetPositionZ());
                if (f.tracker.Update(unit->GetGUID().GetRawValue(), outside, elapsed))
                    f.tracker.Gripped(unit->GetGUID().GetRawValue(), PutAt(unit, f.putOut, "put-out"));
            }
        }
    }
}
