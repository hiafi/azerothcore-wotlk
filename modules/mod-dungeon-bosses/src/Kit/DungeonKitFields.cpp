/*
 * mod-dungeon-bosses, the shared dungeon kit: the Stratholme wave 1 engine helpers (DungeonKitFields.h, WP-KT-1).
 */

#include "DungeonKitFields.h"
#include "Creature.h"
#include "Log.h"
#include "Map.h"
#include "MoveSplineInit.h"
#include "MovementTypedefs.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>

namespace DungeonKit
{
    namespace
    {
        bool CountsAsPlayer(Player const* p)
        {
            return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
        }

        float Rand01()
        {
            return static_cast<float>(rand_norm());
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FloorPath on the map
    // ----------------------------------------------------------------------------------------------------------------

    std::vector<FloorPathPoint> FloorPathOnMap(WorldObject const* ref, Vec2 from, Vec2 to, float startZ, float step,
        float maxStepZ)
    {
        if (!ref)
            return { { from.x, from.y, startZ } };
        return FloorPath(from, to, startZ, [ref, maxStepZ](float x, float y, float z) -> std::optional<float>
        {
            float const h = ref->GetMapHeight(x, y, z + maxStepZ);
            return h > INVALID_HEIGHT + 1.f ? std::optional<float>(h) : std::nullopt;
        }, step, maxStepZ);
    }

    bool MoveAlongFloor(Unit* mover, std::vector<FloorPathPoint> const& path, float speed)
    {
        if (!mover || !mover->IsAlive() || path.size() < 2)
            return false;
        Movement::PointsArray points;
        points.reserve(path.size());
        for (FloorPathPoint const& p : path)
            points.emplace_back(p.x, p.y, p.z);
        Movement::MoveSplineInit init(mover);
        init.MovebyPath(points);
        if (speed > 0.f)
            init.SetVelocity(speed);
        init.Launch();
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PuddleField
    // ----------------------------------------------------------------------------------------------------------------

    PuddleField::PuddleField(Milliseconds tick, float zBand)
        : _tick(tick.count() > 0 ? tick : Milliseconds(1000)), _set(zBand)
    {
    }

    PuddleSet::AddResult PuddleField::Add(Creature* owner, Position const& at, PuddleSpec const& spec)
    {
        if (!owner || !owner->IsInWorld() || spec.radius <= 0.f)
            return {};
        uint32 const armMs = static_cast<uint32>(std::max<int64>(0, spec.armAfter.count()));
        uint32 const lifeMs = static_cast<uint32>(std::max<int64>(0, spec.life.count()));
        PuddleSet::AddResult const added = _set.Add(_clockMs, { at.GetPositionX(), at.GetPositionY() },
            at.GetPositionZ(), spec.radius, armMs, lifeMs, spec.merge);
        if (added.merged)
            return added;

        // Telegraph-only (no damage, rider, Weakened or onHit): it draws and steers the bots; Update applies the
        // effect. Its registry life runs from the arming moment, so it ends with the puddle.
        Milliseconds const persist = spec.life.count() > 0 ? spec.life - spec.armAfter : kWholeFight;
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, BossMechanics::Shapes::Circle(at, spec.radius),
            spec.armAfter);
        ref.Persistent(std::max(persist, Milliseconds(1)), Milliseconds(0));
        if (!spec.fillTimer)
            ref.NoFillTimer();
        if (spec.color)
            ref.Color(*spec.color);
        if (spec.tag)
            ref.Tag(spec.tag);
        _zones[added.id] = ref.Handle();
        return added;
    }

    void PuddleField::CancelZone(Creature* owner, uint32 id)
    {
        auto it = _zones.find(id);
        if (it == _zones.end())
            return;
        if (owner)
            Mechanic::Cancel(owner, it->second);
        _zones.erase(it);
    }

    void PuddleField::Update(Creature* owner, uint32 diff, TickFn const& onTick)
    {
        _clockMs += diff;
        if (!owner)
            return;
        for (uint32 const id : _set.Prune(_clockMs))
            CancelZone(owner, id);
        _pollMs += diff;
        _tickMs += diff;
        if (_pollMs < kPollMs)
            return;
        uint32 const elapsed = _pollMs;
        _pollMs = 0;

        std::vector<uint64> inside;
        if (_set.Size())
            for (auto const& ref : owner->GetMap()->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!CountsAsPlayer(player))
                    continue;
                if (_set.Contains(_clockMs, PlaneOf(player), player->GetPositionZ()))
                    inside.push_back(player->GetGUID().GetRawValue());
            }
        _inside = _clock.Update(inside, elapsed);

        uint32 const tickMs = static_cast<uint32>(_tick.count());
        if (_tickMs < tickMs)
            return;
        _tickMs %= tickMs;
        if (!onTick)
            return;
        // Copy: the callback may add or remove puddles (and so change _inside at the next poll only).
        std::vector<std::pair<uint64, uint32>> const now = _inside;
        Map* map = owner->GetMap();
        for (auto const& [raw, ms] : now)
        {
            Player* player = ObjectAccessor::GetPlayer(map, ObjectGuid(raw));
            if (CountsAsPlayer(player))
                onTick(player, ms);
        }
    }

    void PuddleField::Remove(Creature* owner, uint32 id)
    {
        _set.Remove(id);
        CancelZone(owner, id);
    }

    void PuddleField::Clear(Creature* owner)
    {
        for (Puddle const& p : _set.All())
            CancelZone(owner, p.id);
        _zones.clear();
        _set.Clear();
        _clock.Clear();
        _inside.clear();
        _pollMs = 0;
        _tickMs = 0;
    }

    bool PuddleField::Contains(Position const& p) const
    {
        return _set.Contains(_clockMs, { p.GetPositionX(), p.GetPositionY() }, p.GetPositionZ());
    }

    bool PuddleField::Contains(WorldObject const* o) const
    {
        return o && Contains(o->GetPosition());
    }

    std::optional<uint32> PuddleField::PuddleAt(Position const& p) const
    {
        return _set.PuddleAt(_clockMs, { p.GetPositionX(), p.GetPositionY() }, p.GetPositionZ());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RegistryHit
    // ----------------------------------------------------------------------------------------------------------------

    BossMechanics::MechanicHandle RegistryHit(Unit* owner, GuidSet const& targets, RegistryHitSpec const& spec)
    {
        if (!owner || !owner->IsInWorld() || targets.empty())
            return {};
        // A RunOut measured from the owner hits exactly its carrier (its resolve pass is limited to that player) when
        // the carrier is within its radius of the owner: the radius covers the farthest target (plus a margin for a
        // tick of movement), the z tolerance the highest one. R-1-KIT F2: BM's bot view shows a RunOut measured from
        // the owner to each carrier as a circle hazard on the owner (MechanicBotView.cpp Carriers()) from the resolve
        // until postResolveHold (500 ms) after it, so a targeted tank inside that (reach + 10) yd circle may plan a
        // step off the boss. This warn-0 NoTelegraph hit cannot be dodged; BM leaves such script hits out of the bot
        // view (requested of F-1b; no kit-side handle exists: Detonate and a 0 ms warn still resolve on the next tick).
        GuidSet found;
        float reach = 0.f;
        float dz = 0.f;
        for (ObjectGuid const& guid : targets)
        {
            Player* player = ObjectAccessor::GetPlayer(owner->GetMap(), guid);
            if (!CountsAsPlayer(player))
                continue;
            found.insert(guid);
            reach = std::max(reach, owner->GetExactDist2d(player));
            dz = std::max(dz, std::fabs(player->GetPositionZ() - owner->GetPositionZ()));
        }
        if (found.empty())
            return {};
        float constexpr kMarginYd = 10.f;
        BossMechanics::Eligibility who;
        who.carriers = found;
        BossMechanics::MechanicRef ref = Mechanic::RunOut(owner, nullptr, reach + kMarginYd, Milliseconds(0));
        ref.Targets(found).From(BossMechanics::MeasuredFrom::Owner).Eligible(who).NoTelegraph()
            .ZTolerance(dz + kMarginYd);
        if (spec.pct > 0.f)
            ref.Damage(spec.pct).School(spec.school);
        if (spec.tankPct >= 0.f)
            ref.TankDamage(spec.tankPct);
        if (spec.spellId)
            ref.Spell(spec.spellId);
        if (spec.weakened)
            ref.Weakened();
        if (spec.rider)
            ref.Rider(spec.rider);
        if (spec.tag)
            ref.Tag(spec.tag);
        if (spec.onHit)
            ref.OnHit(spec.onHit);
        return ref.Handle();    // the ref commits here
    }

    BossMechanics::MechanicHandle RegistryHit(Unit* owner, GuidSet const& targets, float pct, uint8 school,
        bool weakened, uint32 rider)
    {
        RegistryHitSpec spec;
        spec.pct = pct;
        spec.school = school;
        spec.weakened = weakened;
        spec.rider = rider;
        return RegistryHit(owner, targets, spec);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WeightedShares
    // ----------------------------------------------------------------------------------------------------------------

    std::vector<std::pair<ObjectGuid, uint32>> WeightedShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, std::vector<uint32> const& stacks, float perStack, float capPct)
    {
        std::vector<std::pair<ObjectGuid, uint32>> out;
        std::vector<Unit const*> units;
        std::vector<uint32> unitStacks;
        for (std::size_t i = 0; i < inside.size(); ++i)
            if (inside[i])
            {
                units.push_back(inside[i]);
                unitStacks.push_back(i < stacks.size() ? stacks[i] : 0);
            }
        if (!owner || units.empty())
            return out;
        uint32 const total = RefFlat(owner, totalPct);
        uint32 const cap = capPct > 0.f ? RefFlat(owner, capPct) : 0;
        std::vector<uint32> const shares = WeightedSplit(total, unitStacks, perStack, cap);
        for (std::size_t i = 0; i < units.size(); ++i)
            out.emplace_back(units[i]->GetGUID(), shares[i]);
        return out;
    }

    std::vector<std::pair<ObjectGuid, uint32>> WeightedShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, uint32 stackSpell, float perStack, float capPct)
    {
        std::vector<uint32> stacks;
        stacks.reserve(inside.size());
        for (Unit const* unit : inside)
            stacks.push_back(unit ? Stacks(unit, stackSpell) : 0);
        return WeightedShares(owner, inside, totalPct, stacks, perStack, capPct);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FollowThenLand
    // ----------------------------------------------------------------------------------------------------------------

    BossMechanics::MechanicRef FollowThenLand(Unit* owner, Unit* target, float radius, Milliseconds warn,
        ImpactSpec const& impact, LandFn onLand)
    {
        if (!owner || !target || !owner->IsInWorld() || !target->IsInMap(owner) || radius <= 0.f)
            return {};
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, BossMechanics::Shapes::Circle(target, radius), warn);
        if (impact.pct > 0.f)
            ref.Damage(impact.pct).School(impact.school);
        if (impact.tankPct >= 0.f)
            ref.TankDamage(impact.tankPct);
        if (impact.spellId)
            ref.Spell(impact.spellId);
        if (impact.weakened)
            ref.Weakened();
        if (impact.tag)
            ref.Tag(impact.tag);

        // Capture the map and guids only. The registry calls OnResolve only while the owner is present; the landing
        // spot is the anchor's pose the resolve was judged at (the carrier's spot then, or its last known one).
        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        ref.OnResolve([map, ownerGuid, targetGuid, onLand = std::move(onLand)](BossMechanics::ResolveResult const& r)
        {
            if (!map || !onLand)
                return;
            Position spot;
            BossMechanics::Registry const* reg = BossMechanics::Registry::Get(map);
            BossMechanics::ActiveMechanic const* m = reg ? reg->Find(r.mechanicId) : nullptr;
            if (m)
                spot = Position(m->lastPose.x, m->lastPose.y, m->lastPose.z, m->lastPose.o);
            else if (Unit* carrier = ObjectAccessor::GetPlayer(map, targetGuid))
                spot = carrier->GetPosition();
            else
                return;
            onLand(map->GetCreature(ownerGuid), spot, r);
        });
        return ref;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PickFloorSpot
    // ----------------------------------------------------------------------------------------------------------------

    std::optional<Position> PickFloorSpot(WorldObject const* ref, Arena const* arena, FloorSpotRules const& rules,
        FloorProbe const& probe, std::vector<Vec2> const& fixed)
    {
        if (!ref || !ref->IsInWorld())
            return std::nullopt;
        Map const* map = ref->GetMap();
        auto floor = [ref, map, arena, &probe](Vec2 p) -> std::optional<float>
        {
            float const h = ref->GetMapHeight(p.x, p.y, probe.z + probe.probeUp);
            if (h <= INVALID_HEIGHT + 1.f || std::fabs(h - probe.z) > probe.zBand)
                return std::nullopt;
            if (arena && !arena->Empty() && !arena->Contains(p, h))
                return std::nullopt;
            if (probe.reachable)
            {
                float x = p.x;
                float y = p.y;
                float z = h;
                if (!map->CanReachPositionAndGetValidCoords(ref, x, y, z)
                    || Distance(p, Vec2{ x, y }) > 1.f || std::fabs(z - h) > probe.zBand)
                    return std::nullopt;
            }
            return h;
        };
        std::optional<FloorSpot> const spot = PickFloorSpotFrom(rules, Rand01, floor, fixed);
        if (!spot)
            return std::nullopt;
        return ToPosition(spot->p, spot->z, BearingTo(spot->p, rules.near));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SummonWave
    // ----------------------------------------------------------------------------------------------------------------

    std::vector<Creature*> SummonWave(Creature* boss, WaveSpec const& spec, std::vector<Position> const& at,
        SummonList& list)
    {
        std::vector<Creature*> out;
        if (!boss || !boss->IsInWorld() || !spec.entry)
            return out;
        uint32 const despawnMs = static_cast<uint32>(std::max<int64>(0, spec.despawn.count()));
        for (Position const& pos : at)
        {
            TempSummon* add = boss->SummonCreature(spec.entry, pos, spec.type, despawnMs);
            if (!add)
                continue;
            if (std::find(list.begin(), list.end(), add->GetGUID()) == list.end())
                list.Summon(add);
            if (spec.health)
            {
                add->SetMaxHealth(spec.health);
                add->SetHealth(spec.health);
            }
            if (spec.passive)
                add->SetReactState(REACT_PASSIVE);
            if (spec.track)
                Mechanic::TrackUnit(boss, add);
            if (spec.onSummon)
                spec.onSummon(add);
            out.push_back(add);
        }
        return out;
    }

    std::vector<Creature*> SummonWave(Creature* boss, uint32 entry, std::vector<Position> const& at, SummonList& list,
        uint32 health)
    {
        WaveSpec spec;
        spec.entry = entry;
        spec.health = health;
        return SummonWave(boss, spec, at, list);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HoldInUnit
    // ----------------------------------------------------------------------------------------------------------------

    bool HoldInUnit::Hold(Unit* holder, Unit* held, HoldSpec spec)
    {
        if (!holder || !held || !spec.holdSpell || !holder->IsAlive() || !held->IsAlive() || !held->IsInMap(holder))
            return false;
        uint32 const maxMs = static_cast<uint32>(std::max<int64>(1, spec.maxHold.count()));
        if (!_book.Add(holder->GetGUID().GetRawValue(), held->GetGUID().GetRawValue(), maxMs))
            return false;
        auto apply = [holder, held, maxMs](uint32 spellId) -> bool
        {
            Aura* aura = holder->AddAura(spellId, held);
            if (!aura)
                return false;
            aura->SetMaxDuration(static_cast<int32>(maxMs));
            aura->SetDuration(static_cast<int32>(maxMs));
            return true;
        };
        if (!apply(spec.holdSpell))
        {
            _book.Release(held->GetGUID().GetRawValue());
            LOG_ERROR(kLogCategory, "dungeon-kit hold: aura {} refused on {} (holder {})", spec.holdSpell,
                held->GetGUID().ToString(), holder->GetEntry());
            return false;
        }
        if (spec.immuneSpell && !apply(spec.immuneSpell))
            LOG_ERROR(kLogCategory, "dungeon-kit hold: immunity aura {} refused on {} (holder {})", spec.immuneSpell,
                held->GetGUID().ToString(), holder->GetEntry());
        _entries.push_back({ holder->GetGUID(), held->GetGUID(), std::move(spec) });
        return true;
    }

    void HoldInUnit::End(WorldObject* owner, HoldBook::Ended const& ended)
    {
        auto it = std::find_if(_entries.begin(), _entries.end(), [&ended](Entry const& e)
        {
            return e.held.GetRawValue() == ended.held;
        });
        if (it == _entries.end())
            return;
        Entry const e = std::move(*it);
        _entries.erase(it);
        if (Unit* held = owner ? ObjectAccessor::GetUnit(*owner, e.held) : nullptr)
        {
            held->RemoveAurasDueToSpell(e.spec.holdSpell, e.holder);
            if (e.spec.immuneSpell)
                held->RemoveAurasDueToSpell(e.spec.immuneSpell, e.holder);
        }
        LOG_INFO(kLogCategory, "dungeon-kit hold end held={} holder={} why={}", e.held.ToString(),
            e.holder.ToString(), HoldEndName(ended.why));
        if (e.spec.onRelease)
            e.spec.onRelease(e.holder, e.held, ended.why);
    }

    void HoldInUnit::Update(WorldObject* owner, uint32 diff)
    {
        if (_entries.empty())
        {
            _checkMs = 0;
            return;
        }
        _checkMs += diff;
        if (_checkMs < kCheckMs || !owner)
            return;
        uint32 const elapsed = _checkMs;
        _checkMs = 0;
        auto present = [owner](uint64 raw)
        {
            Unit const* unit = ObjectAccessor::GetUnit(*owner, ObjectGuid(raw));
            return unit && unit->IsInWorld() && unit->IsAlive() && unit->IsInMap(owner);
        };
        for (HoldBook::Ended const& ended : _book.Update(elapsed, present, present))
            End(owner, ended);
    }

    bool HoldInUnit::Release(WorldObject* owner, ObjectGuid held)
    {
        std::optional<HoldBook::Ended> const ended = _book.Release(held.GetRawValue(), HoldEnd::Released);
        if (!ended)
            return false;
        End(owner, *ended);
        return true;
    }

    void HoldInUnit::Clear(WorldObject* owner)
    {
        for (HoldBook::Ended const& ended : _book.Clear())
            End(owner, ended);
        _entries.clear();
        _checkMs = 0;
    }

    ObjectGuid HoldInUnit::HolderOf(ObjectGuid held) const
    {
        for (Entry const& e : _entries)
            if (e.held == held)
                return e.holder;
        return ObjectGuid::Empty;
    }
}
