/*
 * mod-dungeon-bosses, the shared dungeon kit: water sheets that freeze, thaw and grow (DungeonKitWater.h, Zul'Farrak
 * WP-KT).
 */

#include "DungeonKitWater.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Map.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>

namespace DungeonKit
{
    namespace
    {
        Position ToPos(Vec2 p, float z)
        {
            return Position(p.x, p.y, z);
        }

        BossMechanics::ZoneSpec ShapeOf(WaterSheet const& s)
        {
            if (s.end)
                return BossMechanics::Shapes::Line(BossMechanics::Anchor(ToPos(s.center, s.z)),
                    BossMechanics::Anchor(ToPos(*s.end, s.z)), 2.f * s.radius);
            return BossMechanics::Shapes::Circle(BossMechanics::Anchor(ToPos(s.center, s.z)), s.radius);
        }

        std::string Ids(std::vector<uint32> const& ids)
        {
            std::string out;
            for (uint32 const id : ids)
                out += (out.empty() ? "" : ",") + std::to_string(id);
            return out.empty() ? "-" : out;
        }
    }

    void WaterField::Log(char const* what, std::string const& detail) const
    {
        LogMechanic(_spec.dungeon, _spec.boss, (std::string(_spec.name) + "-" + what).c_str(), detail);
    }

    uint32 WaterField::Add(Creature* owner, Position const& at, float radius, SheetRules const& rules,
        SheetState state)
    {
        if (!owner || !owner->IsInWorld() || radius <= 0.f)
            return 0;
        uint32 const id = _sheets.Add(Vec2{ at.GetPositionX(), at.GetPositionY() }, at.GetPositionZ(), radius, rules,
            state);
        if (!id)
            return 0;
        _looks[id] = Look{};
        Refresh(owner, id);
        WaterSheet const* s = _sheets.Find(id);
        Log("add", Acore::StringFormat("id={} at={:.1f},{:.1f} radius={:.1f} state={} kind={}", id, at.GetPositionX(),
            at.GetPositionY(), s ? s->radius : radius, state == SheetState::Ice ? "ice" : "water", rules.kind));
        return id;
    }

    uint32 WaterField::AddStrip(Creature* owner, Position const& from, Position const& to, float halfWidth,
        SheetRules const& rules)
    {
        if (!owner || !owner->IsInWorld() || halfWidth <= 0.f)
            return 0;
        uint32 const id = _sheets.AddStrip(Vec2{ from.GetPositionX(), from.GetPositionY() },
            Vec2{ to.GetPositionX(), to.GetPositionY() }, from.GetPositionZ(), halfWidth, rules);
        if (!id)
            return 0;
        _looks[id] = Look{};
        Refresh(owner, id);
        Log("add", Acore::StringFormat("id={} strip={:.1f},{:.1f}->{:.1f},{:.1f} half-width={:.1f} kind={}", id,
            from.GetPositionX(), from.GetPositionY(), to.GetPositionX(), to.GetPositionY(), halfWidth, rules.kind));
        return id;
    }

    FreezeResult WaterField::FreezeAt(Creature* owner, Position const& at)
    {
        FreezeResult const r = _sheets.FreezeAt(Vec2{ at.GetPositionX(), at.GetPositionY() }, at.GetPositionZ());
        for (uint32 const id : r.frozen)
            Refresh(owner, id);
        Log("freeze", Acore::StringFormat("at={:.1f},{:.1f} ids={} unfreezable={} meltwater={}", at.GetPositionX(),
            at.GetPositionY(), Ids(r.frozen), r.unfreezable ? 1 : 0, r.Meltwater() ? 1 : 0));
        return r;
    }

    FreezeResult WaterField::FreezeWithin(Creature* owner, Position const& at, float yd)
    {
        FreezeResult const r = _sheets.FreezeWithin(Vec2{ at.GetPositionX(), at.GetPositionY() }, at.GetPositionZ(),
            yd);
        for (uint32 const id : r.frozen)
            Refresh(owner, id);
        Log("freeze", Acore::StringFormat("at={:.1f},{:.1f} within={:.1f} ids={} unfreezable={} meltwater={}",
            at.GetPositionX(), at.GetPositionY(), yd, Ids(r.frozen), r.unfreezable ? 1 : 0, r.Meltwater() ? 1 : 0));
        return r;
    }

    bool WaterField::Freeze(Creature* owner, uint32 id)
    {
        if (!_sheets.Freeze(id))
            return false;
        Refresh(owner, id);
        Log("freeze", Acore::StringFormat("ids={}", id));
        return true;
    }

    bool WaterField::Thaw(Creature* owner, uint32 id)
    {
        std::optional<SheetChange> const c = _sheets.Thaw(id);
        if (!c)
            return false;
        if (c->kind == SheetChange::Kind::Gone)
            Drop(owner, id);
        else
            Refresh(owner, id);
        Log("thaw", Acore::StringFormat("id={} to={}", id, c->kind == SheetChange::Kind::Gone ? "gone" : "water"));
        return true;
    }

    std::vector<uint32> WaterField::GrowWater(Creature* owner, float deltaYd)
    {
        std::vector<uint32> const grown = _sheets.GrowWater(deltaYd);
        for (uint32 const id : grown)
            Refresh(owner, id);
        Log("grow", Acore::StringFormat("by={:.1f} ids={} water={} ice={}", deltaYd, Ids(grown),
            _sheets.CountIn(SheetState::Water), _sheets.CountIn(SheetState::Ice)));
        return grown;
    }

    bool WaterField::Grow(Creature* owner, uint32 id, float deltaYd)
    {
        if (!_sheets.Grow(id, deltaYd))
            return false;
        Refresh(owner, id);
        WaterSheet const* s = _sheets.Find(id);
        Log("grow", Acore::StringFormat("id={} by={:.1f} radius={:.1f}", id, deltaYd, s ? s->radius : 0.f));
        return true;
    }

    bool WaterField::SetRadius(Creature* owner, uint32 id, float radiusYd)
    {
        if (!_sheets.SetRadius(id, radiusYd))
            return false;
        Refresh(owner, id);
        WaterSheet const* s = _sheets.Find(id);
        Log("grow", Acore::StringFormat("id={} radius={:.1f}", id, s ? s->radius : 0.f));
        return true;
    }

    std::vector<BossMechanics::MechanicHandle> WaterField::RegisterDischarge(Creature* owner, Milliseconds warn,
        std::function<void(BossMechanics::MechanicRef&)> const& configure)
    {
        CancelDischarge(owner);
        std::vector<BossMechanics::MechanicHandle> handles;
        if (!owner || !owner->IsInWorld())
            return handles;
        uint32 const warnMs = static_cast<uint32>(std::max<int64>(1, warn.count()));
        std::vector<uint32> ids;
        for (WaterSheet const& s : _sheets.All())
        {
            if (!s.IsWater() || !s.rules.discharge)
                continue;
            BossMechanics::MechanicRef ref = Mechanic::Zone(owner, ShapeOf(s), Milliseconds(warnMs));
            if (!ref.IsValid())
                continue;
            if (_spec.color)
                ref.Color(*_spec.color);
            if (_spec.tag)
                ref.Tag(_spec.tag);
            if (configure)
                configure(ref);
            _looks[s.id].discharge = ref.Handle();
            handles.push_back(ref.Handle());
            ids.push_back(s.id);
        }
        _stormLeftMs = warnMs;
        for (uint32 const id : ids)
            Refresh(owner, id);
        Log("discharge", Acore::StringFormat("warn={}ms sheets={} ids={}", warnMs, ids.size(), Ids(ids)));
        return handles;
    }

    void WaterField::CancelDischarge(Creature* owner)
    {
        bool any = false;
        for (auto& [id, look] : _looks)
            if (look.discharge)
            {
                if (owner)
                    Mechanic::Cancel(owner, look.discharge);
                look.discharge = {};
                any = true;
            }
        bool const wasStorming = _stormLeftMs > 0;
        _stormLeftMs = 0;
        if (any || wasStorming)
            for (WaterSheet const& s : _sheets.All())
                Refresh(owner, s.id);
    }

    std::vector<SheetChange> WaterField::Update(Creature* owner, uint32 diff)
    {
        if (_stormLeftMs)
        {
            _stormLeftMs = diff >= _stormLeftMs ? 0 : _stormLeftMs - diff;
            if (!_stormLeftMs)
            {
                // Resolved by the registry: forget the handles, put the discs back.
                for (auto& [id, look] : _looks)
                    look.discharge = {};
                for (WaterSheet const& s : _sheets.All())
                    Refresh(owner, s.id);
            }
        }
        std::vector<SheetChange> const changes = _sheets.Advance(diff);
        for (SheetChange const& c : changes)
        {
            if (c.kind == SheetChange::Kind::Gone)
                Drop(owner, c.id);
            else
                Refresh(owner, c.id);
            Log("thaw", Acore::StringFormat("id={} to={}", c.id, c.kind == SheetChange::Kind::Gone ? "gone" : "water"));
        }
        return changes;
    }

    void WaterField::Remove(Creature* owner, uint32 id)
    {
        if (!_sheets.Remove(id))
            return;
        Drop(owner, id);
        Log("remove", Acore::StringFormat("id={}", id));
    }

    void WaterField::Clear(Creature* owner)
    {
        std::vector<uint32> ids;
        ids.reserve(_looks.size());
        for (auto const& [id, look] : _looks)
            ids.push_back(id);
        for (uint32 const id : ids)
            Drop(owner, id);
        _looks.clear();
        _sheets.Clear();
        _stormLeftMs = 0;
    }

    void WaterField::Drop(Creature* owner, uint32 id)
    {
        auto it = _looks.find(id);
        if (it == _looks.end())
            return;
        Look look = it->second;
        _looks.erase(it);
        if (!owner)
            return;
        if (look.avoid)
            Mechanic::Cancel(owner, look.avoid);
        if (look.discharge)
            Mechanic::Cancel(owner, look.discharge);
        if (!look.disc.IsEmpty() && owner->IsInWorld())
            if (Creature* disc = owner->GetMap()->GetCreature(look.disc))
                disc->DespawnOrUnsummon();
    }

    bool WaterField::RegisterAvoid(Creature* owner, WaterSheet const& s, Look& look)
    {
        // Telegraph-only and lasting: it steers the bots and hits nobody; the effects are the script's.
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, ShapeOf(s), Milliseconds(0));
        if (!ref.IsValid())
            return false;
        ref.Persistent(kWholeFight, Milliseconds(0)).NoFillTimer();
        if (!_spec.drawAvoid)
            ref.NoTelegraph();
        if (_spec.color)
            ref.Color(*_spec.color);
        if (_spec.tag)
            ref.Tag(_spec.tag);
        if (_spec.configureAvoid)
            _spec.configureAvoid(ref);
        look.avoid = ref.Handle();
        look.avoidRadius = s.radius;
        return true;
    }

    void WaterField::Refresh(Creature* owner, uint32 id)
    {
        WaterSheet const* s = _sheets.Find(id);
        auto it = _looks.find(id);
        if (!s || it == _looks.end() || !owner || !owner->IsInWorld())
            return;
        Look& look = it->second;

        // The avoid zone: water only; the registry cannot resize a zone, so a grown sheet registers anew.
        bool const wantAvoid = s->IsWater() && s->rules.avoid;
        if (look.avoid && (!wantAvoid || std::fabs(look.avoidRadius - s->radius) >= 0.01f))
        {
            Mechanic::Cancel(owner, look.avoid);
            look.avoid = {};
        }
        if (wantAvoid && !look.avoid)
            RegisterAvoid(owner, *s, look);

        // A frozen sheet is no Discharge target (GZ2): its zone for the cast goes.
        if (!s->IsWater() && look.discharge)
        {
            Mechanic::Cancel(owner, look.discharge);
            look.discharge = {};
        }

        // The disc: one SetDisplayId(display, scale) call (a display change after SetObjectScale resets the scale).
        std::optional<DiscLook> const want = _spec.discEntry ? DiscFor(*s, look.discharge.IsValid(), _spec.looks)
            : std::nullopt;
        Creature* disc = look.disc.IsEmpty() ? nullptr : owner->GetMap()->GetCreature(look.disc);
        if (!want)
        {
            if (disc)
                disc->DespawnOrUnsummon();
            look.disc.Clear();
            look.worn = {};
            return;
        }
        if (!disc)
        {
            disc = owner->SummonCreature(_spec.discEntry, ToPos(s->center, s->z), TEMPSUMMON_MANUAL_DESPAWN);
            if (!disc)
                return;
            disc->SetReactState(REACT_PASSIVE);
            look.disc = disc->GetGUID();
            look.worn = {};
        }
        if (!(look.worn == *want))
        {
            disc->SetDisplayId(want->display, want->scale);
            look.worn = *want;
        }
    }

    bool WaterField::IsWater(WorldObject const* o) const
    {
        return o && _sheets.IsWater(PlaneOf(o), o->GetPositionZ());
    }

    bool WaterField::IsWater(Position const& p) const
    {
        return _sheets.IsWater(Vec2{ p.GetPositionX(), p.GetPositionY() }, p.GetPositionZ());
    }

    bool WaterField::IsIce(Position const& p) const
    {
        return _sheets.IsIce(Vec2{ p.GetPositionX(), p.GetPositionY() }, p.GetPositionZ());
    }

    std::optional<uint32> WaterField::WaterSheetAt(Position const& p) const
    {
        return _sheets.WaterSheetAt(Vec2{ p.GetPositionX(), p.GetPositionY() }, p.GetPositionZ());
    }

    bool WaterField::InWaterSheet(uint32 id, WorldObject const* o) const
    {
        return o && _sheets.InWaterSheet(id, PlaneOf(o), o->GetPositionZ());
    }

    BossMechanics::MechanicHandle WaterField::AvoidZoneOf(uint32 id) const
    {
        auto it = _looks.find(id);
        return it == _looks.end() ? BossMechanics::MechanicHandle{} : it->second.avoid;
    }

    ObjectGuid WaterField::DiscOf(uint32 id) const
    {
        auto it = _looks.find(id);
        return it == _looks.end() ? ObjectGuid::Empty : it->second.disc;
    }
}
