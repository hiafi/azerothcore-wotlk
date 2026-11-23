/*
 * mod-dungeon-bosses, the shared dungeon kit: zones that change over time (DungeonKitZones.h, Scarlet Monastery
 * WP-KT-SM). GrowingZone lifts the re-register-per-step growth of Blackrock Depths' Watchman Doomgrip
 * (boss_watchman_doomgrip_rework.cpp, the Vault field) into the kit.
 */

#include "DungeonKitZones.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "ObjectAccessor.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <span>
#include <utility>

namespace DungeonKit
{
    namespace
    {
        // A zone "until canceled": the registry wants a duration; an hour outlives any fight.
        uint32 constexpr kForeverMs = 3600000;

        Milliseconds Ms(uint32 ms)
        {
            return Milliseconds(static_cast<int64>(ms));
        }

        void DespawnLook(Unit* owner, ObjectGuid& guid)
        {
            if (guid.IsEmpty())
                return;
            if (owner)
                if (Creature* look = ObjectAccessor::GetCreature(*owner, guid))
                    look->DespawnOrUnsummon();
            guid.Clear();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GrowingZone
    // ----------------------------------------------------------------------------------------------------------------

    bool GrowingZone::Start(Unit* owner, GrowingZoneSpec spec)
    {
        Cancel(owner);
        if (!owner || !owner->IsInWorld())
            return false;
        _spec = std::move(spec);
        _plan = GrowthPlan{ _spec.fromYd, _spec.toYd, _spec.overMs, _spec.stepMs };
        _timed = _plan.Timed();
        _elapsedMs = 0;
        _radius = 0.f;
        if (!_spec.anchor.IsUnit() && _spec.look.IsEmpty() && _spec.lookEntry && !_spec.rungs.empty())
        {
            TempSummon* look = owner->SummonCreature(_spec.lookEntry, _spec.anchor.point, TEMPSUMMON_MANUAL_DESPAWN);
            if (look)
                _summonedLook = look->GetGUID();
        }
        if (!Register(owner, _spec.fromYd, _spec.warnMs))
        {
            ClearLook(owner);
            return false;
        }
        _active = true;
        LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-start").c_str(),
            Acore::StringFormat("radius={:.1f} to={:.1f} over={}ms life={}ms", _spec.fromYd, _spec.toYd,
                _spec.overMs, _spec.lifeMs));
        return true;
    }

    bool GrowingZone::Register(Unit* owner, float radius, uint32 warnMs)
    {
        uint32 duration = kForeverMs;
        if (_spec.lifeMs)
        {
            uint32 const endAt = _spec.warnMs + _spec.lifeMs;
            uint32 const liveAt = _elapsedMs + warnMs;
            if (liveAt >= endAt)
                return false;
            duration = endAt - liveAt;
        }
        bool const first = !_zone.IsValid();
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, BossMechanics::Shapes::Circle(_spec.anchor, radius),
            Ms(warnMs));
        if (!ref.IsValid())
            return false;
        ref.Persistent(Ms(duration), Ms(_spec.tickMs)).Damage(_spec.pct).School(_spec.school);
        if (_spec.tankPct >= 0.f)
            ref.TankDamage(_spec.tankPct);
        if (_spec.spellId)
            ref.Spell(_spec.spellId);
        if (_spec.rider)
            ref.Rider(_spec.rider);
        if (_spec.color)
            ref.Color(*_spec.color);
        if (_spec.tag)
            ref.Tag(_spec.tag);
        if (!first)
            ref.NoFillTimer();
        if (_spec.configure)
            _spec.configure(ref);
        BossMechanics::MechanicHandle const handle = ref.Handle();

        // The old zone ticks until the new one is live (no gap in the pool), then goes; a still older one goes now.
        if (_old)
            Mechanic::Cancel(owner, _old);
        _old = first ? BossMechanics::MechanicHandle{} : _zone;
        _oldEndMs = _elapsedMs + warnMs;
        _zone = handle;
        _radius = radius;
        WearRung(owner, radius);
        return true;
    }

    void GrowingZone::Update(Unit* owner, uint32 diff)
    {
        if (!_active || !owner)
            return;
        _elapsedMs += diff;
        if (_old && _elapsedMs >= _oldEndMs)
        {
            Mechanic::Cancel(owner, _old);
            _old = {};
        }
        if (_spec.lifeMs && _elapsedMs >= _spec.warnMs + _spec.lifeMs)
        {
            LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-end").c_str(),
                Acore::StringFormat("radius={:.1f} lived={}ms", _radius, _spec.lifeMs));
            _zone = {};
            Cancel(owner);
            return;
        }
        if (!_timed || _elapsedMs < _spec.warnMs)
            return;
        float const target = _plan.RadiusAt(_elapsedMs - _spec.warnMs);
        if (std::fabs(target - _radius) < 0.01f)
            return;
        float const before = _radius;
        if (Register(owner, target, _spec.stepWarnMs))
            LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-grow").c_str(),
                Acore::StringFormat("radius={:.1f}->{:.1f} at={}ms", before, target, _elapsedMs));
        else
            _timed = false;     // refused, or past its life: stay at this radius
    }

    void GrowingZone::GrowTo(Unit* owner, float radiusYd)
    {
        if (!_active || !owner || radiusYd <= 0.f || std::fabs(radiusYd - _radius) < 0.01f)
            return;
        _timed = false;
        float const before = _radius;
        if (Register(owner, radiusYd, _spec.stepWarnMs))
            LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-grow").c_str(),
                Acore::StringFormat("radius={:.1f}->{:.1f} by-hand", before, radiusYd));
    }

    void GrowingZone::Cancel(Unit* owner)
    {
        if (owner)
        {
            if (_old)
                Mechanic::Cancel(owner, _old);
            if (_zone)
                Mechanic::Cancel(owner, _zone);
        }
        _old = {};
        _zone = {};
        ClearLook(owner);
        _active = false;
        _timed = false;
    }

    Unit* GrowingZone::LookUnit(Unit* owner) const
    {
        if (!owner)
            return nullptr;
        ObjectGuid guid = _spec.look;
        if (guid.IsEmpty() && _spec.anchor.IsUnit())
            guid = _spec.anchor.unit;
        if (guid.IsEmpty())
            guid = _summonedLook;
        if (guid.IsEmpty())
            return nullptr;
        return ObjectAccessor::GetUnit(*owner, guid);
    }

    void GrowingZone::WearRung(Unit* owner, float radius)
    {
        if (_spec.rungs.empty())
            return;
        std::vector<float> radii;
        radii.reserve(_spec.rungs.size());
        for (GrowRung const& r : _spec.rungs)
            radii.push_back(r.radiusYd);
        std::optional<std::size_t> const i = NearestRung(std::span<float const>(radii), radius);
        uint32 const spell = i ? _spec.rungs[*i].spellId : 0;
        if (spell == _rungSpell)
            return;
        Unit* look = LookUnit(owner);
        if (!look)
            return;
        if (_rungSpell)
            look->RemoveAurasDueToSpell(_rungSpell);
        if (spell)
            look->CastSpell(look, spell, true);
        _rungSpell = spell;
    }

    void GrowingZone::ClearLook(Unit* owner)
    {
        if (_rungSpell)
            if (Unit* look = LookUnit(owner))
                look->RemoveAurasDueToSpell(_rungSpell);
        _rungSpell = 0;
        DespawnLook(owner, _summonedLook);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GrowingZones
    // ----------------------------------------------------------------------------------------------------------------

    uint32 GrowingZones::Add(Unit* owner, GrowingZoneSpec spec)
    {
        Entry e;
        e.id = _nextId;
        if (!e.zone.Start(owner, std::move(spec)))
            return 0;
        ++_nextId;
        _zones.push_back(std::move(e));
        return _zones.back().id;
    }

    void GrowingZones::Update(Unit* owner, uint32 diff)
    {
        for (Entry& e : _zones)
            e.zone.Update(owner, diff);
        std::erase_if(_zones, [](Entry const& e) { return !e.zone.Active(); });
    }

    void GrowingZones::GrowTo(Unit* owner, uint32 id, float radiusYd)
    {
        for (Entry& e : _zones)
            if (e.id == id)
                e.zone.GrowTo(owner, radiusYd);
    }

    void GrowingZones::Grow(Unit* owner, uint32 id, float deltaYd)
    {
        for (Entry& e : _zones)
            if (e.id == id)
                e.zone.Grow(owner, deltaYd);
    }

    void GrowingZones::Cancel(Unit* owner, uint32 id)
    {
        for (Entry& e : _zones)
            if (e.id == id)
                e.zone.Cancel(owner);
        std::erase_if(_zones, [id](Entry const& e) { return e.id == id; });
    }

    void GrowingZones::Clear(Unit* owner)
    {
        for (Entry& e : _zones)
            e.zone.Cancel(owner);
        _zones.clear();
    }

    GrowingZone const* GrowingZones::Get(uint32 id) const
    {
        for (Entry const& e : _zones)
            if (e.id == id)
                return &e.zone;
        return nullptr;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TurningBeams
    // ----------------------------------------------------------------------------------------------------------------

    bool TurningBeams::Start(Unit* owner, TurningBeamsSpec spec)
    {
        Stop(owner);
        if (!owner || !owner->IsInWorld() || spec.stepMs == 0)
            return false;
        _spec = std::move(spec);
        _clock = BeamClock(_spec.startBearing, _spec.stepDeg, _spec.count, _spec.direction);
        _active = true;
        if (_spec.endEntry)
            for (uint8 i = 0; i < _clock.Count(); ++i)
                if (TempSummon* end = owner->SummonCreature(_spec.endEntry, _spec.anchor, TEMPSUMMON_MANUAL_DESPAWN))
                    _ends.push_back(end->GetGUID());
        PlaceLook(owner, _clock);
        MarkNext(owner);
        _stepLeftMs = _spec.stepMs;
        LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-start").c_str(),
            Acore::StringFormat("count={} step={:.0f}deg every={}ms dir={}", _clock.Count(), _spec.stepDeg,
                _spec.stepMs, _clock.Direction()));
        return true;
    }

    void TurningBeams::Update(Unit* owner, uint32 diff)
    {
        if (!_active || !owner)
            return;
        if (diff < _stepLeftMs)
        {
            _stepLeftMs -= diff;
            return;
        }
        _stepLeftMs = _spec.stepMs;
        // The marked step resolves now (the registry): the beams are on it.
        PlaceLook(owner, _clock);
        _clock.Step();
        MarkNext(owner);
    }

    void TurningBeams::Flip()
    {
        if (!_active)
            return;
        _clock.Flip();
        LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-flip").c_str(),
            Acore::StringFormat("dir={} steps={}", _clock.Direction(), _clock.Steps()));
    }

    void TurningBeams::Stop(Unit* owner)
    {
        if (owner)
            for (BossMechanics::MechanicHandle const& h : _marked)
                if (h)
                    Mechanic::Cancel(owner, h);
        _marked.clear();
        for (ObjectGuid& guid : _ends)
            DespawnLook(owner, guid);
        _ends.clear();
        if (_active)
            LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-stop").c_str(),
                Acore::StringFormat("steps={}", _clock.Steps()));
        _active = false;
    }

    void TurningBeams::MarkNext(Unit* owner)
    {
        _marked.clear();    // the previous marks have resolved (one step ago)
        Vec2 const anchor{ _spec.anchor.GetPositionX(), _spec.anchor.GetPositionY() };
        float const z = _spec.anchor.GetPositionZ();
        for (uint8 i = 0; i < _clock.Count(); ++i)
        {
            float const bearing = _clock.BearingOf(i);
            std::optional<float> wall;
            if (_spec.clip)
                wall = _spec.clip->RayToEdge(anchor, z, bearing);
            std::optional<BeamLane> const lane = BeamSegment(anchor, bearing, _spec.innerYd, _spec.lengthYd, wall,
                _spec.inset);
            if (!lane)
                continue;
            BossMechanics::MechanicRef ref = Mechanic::Line(owner, ToPosition(lane->from, z, bearing), bearing,
                lane->length, _spec.widthYd, Ms(_spec.stepMs));
            if (!ref.IsValid())
                continue;
            ref.Damage(_spec.pct).School(_spec.school);
            if (_spec.tankPct >= 0.f)
                ref.TankDamage(_spec.tankPct);
            if (_spec.spellId)
                ref.Spell(_spec.spellId);
            if (_spec.weakened)
                ref.Weakened();
            if (_spec.color)
                ref.Color(*_spec.color);
            if (_spec.tag)
                ref.Tag(_spec.tag);
            if (_spec.configure)
                _spec.configure(ref);
            _marked.push_back(ref.Handle());
        }
    }

    void TurningBeams::PlaceLook(Unit* owner, BeamClock const& at)
    {
        if (_ends.empty())
            return;
        Vec2 const anchor{ _spec.anchor.GetPositionX(), _spec.anchor.GetPositionY() };
        float const z = _spec.anchor.GetPositionZ();
        Unit* source = _spec.beamSource.IsEmpty() ? owner : ObjectAccessor::GetUnit(*owner, _spec.beamSource);
        for (uint8 i = 0; i < _ends.size() && i < at.Count(); ++i)
        {
            Creature* end = ObjectAccessor::GetCreature(*owner, _ends[i]);
            if (!end)
                continue;
            float const bearing = at.BearingOf(i);
            std::optional<float> wall;
            if (_spec.clip)
                wall = _spec.clip->RayToEdge(anchor, z, bearing);
            std::optional<BeamLane> const lane = BeamSegment(anchor, bearing, _spec.innerYd, _spec.lengthYd, wall,
                _spec.inset);
            Vec2 const tip = lane ? lane->to : Advance(anchor, bearing, _spec.innerYd);
            end->NearTeleportTo(tip.x, tip.y, z, bearing);
            // The chain runs from each end stalker to the source (one source cannot channel two chains).
            if (_spec.beamSpell && source && !end->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
                end->CastSpell(source, _spec.beamSpell, true);
        }
    }
}
