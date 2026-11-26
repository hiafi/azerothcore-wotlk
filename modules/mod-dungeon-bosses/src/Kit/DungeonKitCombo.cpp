/*
 * mod-dungeon-bosses, the shared dungeon kit: a called combination (DungeonKitCombo.h, Gnomeregan WP-KT-G).
 */

#include "DungeonKitCombo.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "ObjectAccessor.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <string>
#include <utility>

namespace DungeonKit
{
    namespace
    {
        void Say(CalledCombinationSpec const& spec, char const* what, std::string const& detail)
        {
            LogMechanic(spec.dungeon, spec.boss, (std::string(spec.name) + "-" + what).c_str(), detail);
        }

        std::string ShapeNames(CalledCombinationSpec const& spec, ComboPunch const& punch)
        {
            std::string out;
            for (uint8 const s : punch.shapes)
            {
                if (!out.empty())
                    out += "+";
                out += s < spec.shapes.size() ? spec.shapes[s].name : "?";
            }
            return out;
        }
    }

    BossMechanics::ZoneSpec ZoneSpecOf(PlacedShape const& shape)
    {
        Position const at = ToPosition(shape.at, shape.z, shape.facing);
        switch (shape.type)
        {
            case ComboShapeType::Circle:
                return BossMechanics::Shapes::Circle(at, shape.radiusYd);
            case ComboShapeType::Donut:
                return BossMechanics::Shapes::Donut(at, shape.innerYd, shape.radiusYd);
            case ComboShapeType::Cone:
                return BossMechanics::Shapes::Cone(at, shape.angleDeg, shape.lengthYd);
            case ComboShapeType::Rect:
                return BossMechanics::Shapes::LineFacing(at, shape.facing, shape.lengthYd, shape.widthYd);
        }
        return BossMechanics::Shapes::Circle(at, shape.radiusYd);
    }

    void CalledCombination::Configure(CalledCombinationSpec spec)
    {
        _spec = std::move(spec);
    }

    bool CalledCombination::Start(Creature* owner, ComboFrame const& frame, std::vector<ComboPunch> punches)
    {
        if (_active || !owner || !owner->IsInWorld() || punches.empty())
            return false;
        _frame = frame;
        _punches.clear();
        _real.clear();
        _decoys.clear();
        _numerals.clear();
        for (ComboPunch& punch : punches)
        {
            Step step;
            for (uint8 const s : punch.shapes)
                if (s < _spec.shapes.size())
                {
                    step.punch.shapes.push_back(s);
                    step.placed.push_back(Place(_frame, _spec.shapes[s].def));
                }
            if (!step.placed.empty())
                _punches.push_back(std::move(step));
        }
        if (_punches.empty())
            return false;
        _times = ComboTimeline(_spec.timing, _punches.size());
        _state = std::make_shared<State>();
        _state->landed.assign(_punches.size(), false);
        _elapsedMs = 0;
        _active = true;

        // The whole chain for the bots, now: one hidden real Zone per shape, resolving at its strike.
        std::weak_ptr<State> const weak = _state;
        for (uint8 i = 0; i < _punches.size(); ++i)
        {
            Step const& step = _punches[i];
            for (std::size_t k = 0; k < step.placed.size(); ++k)
            {
                ComboShape const& shape = _spec.shapes[step.punch.shapes[k]];
                BossMechanics::MechanicRef ref = Mechanic::Zone(owner, ZoneSpecOf(step.placed[k]),
                    Milliseconds(_times[i].strikeAt));
                if (!ref.IsValid())
                    continue;
                ref.NoTelegraph().ZTolerance(_spec.zTolerance);
                if (shape.pct > 0.f)
                    ref.Damage(shape.pct).School(shape.school);
                if (shape.tankPct >= 0.f)
                    ref.TankDamage(shape.tankPct);
                if (shape.spellId)
                    ref.Spell(shape.spellId);
                if (shape.weakened)
                    ref.Weakened();
                if (shape.rider)
                    ref.Rider(shape.rider);
                if (shape.color)
                    ref.Color(*shape.color);
                if (_spec.tag)
                    ref.Tag(_spec.tag);
                ref.OnResolve([weak, i](BossMechanics::ResolveResult const& r)
                {
                    std::shared_ptr<State> s = weak.lock();
                    if (!s)
                        return;
                    ++s->resolved;
                    for (ObjectGuid const& hit : r.hits)
                        if (hit.IsPlayer() && i < s->landed.size())
                            s->landed[i] = true;
                });
                if (shape.configure)
                    shape.configure(ref);
                _real.push_back(ref.Handle());
            }
        }

        std::string chain;
        for (Step const& step : _punches)
            chain += (chain.empty() ? "" : ",") + ShapeNames(_spec, step.punch);
        Say(_spec, "start", Acore::StringFormat("punches={} chain={} frame=({:.1f}, {:.1f}) facing={:.0f}deg last={}ms",
            _punches.size(), chain, _frame.origin.x, _frame.origin.y, _frame.facing * 180.f / kPi,
            _times.back().strikeAt));
        Update(owner, 0);   // the calls and markers due now (AllAtOnce draws every call at once)
        return true;
    }

    void CalledCombination::Update(Creature* owner, uint32 diff)
    {
        if (!_active || !owner || !owner->IsInWorld())
            return;
        _elapsedMs += diff;
        for (uint8 i = 0; i < _punches.size() && _active; ++i)
        {
            PunchTimes const& t = _times[i];
            if (!_punches[i].called && _elapsedMs >= t.callFrom)
                Call(owner, i);
            if (!_punches[i].live && _elapsedMs >= t.liveFrom)
                Live(owner, i);
            if (!_punches[i].struck && _elapsedMs >= t.strikeAt)
                Strike(owner, i);
        }
        if (!_active)
            return;     // a hook stopped it
        uint32 const last = _times.back().strikeAt;
        if (_elapsedMs >= last && (_state->resolved >= _real.size() || _elapsedMs >= last + kEndSlackMs))
            Finish(owner);
    }

    void CalledCombination::Call(Creature* owner, uint8 i)
    {
        Step& step = _punches[i];
        step.called = true;
        PunchTimes const& t = _times[i];
        uint32 const now = std::min(_elapsedMs, t.callTo);
        uint32 const show = t.callTo > now ? t.callTo - now : 0;
        if (_spec.drawCalls && show)
            for (PlacedShape const& placed : step.placed)
            {
                BossMechanics::MechanicRef ref = Mechanic::Zone(owner, ZoneSpecOf(placed), Milliseconds(show));
                if (!ref.IsValid())
                    continue;
                ref.Decoy().ZTolerance(_spec.zTolerance);
                if (!_spec.callFill)
                    ref.NoFillTimer();
                if (_spec.callColor)
                    ref.Color(*_spec.callColor);
                if (_spec.tag)
                    ref.Tag(_spec.tag);
                _decoys.push_back(ref.Handle());
            }
        uint32 const untilStrike = t.strikeAt > _elapsedMs ? t.strikeAt - _elapsedMs : 0;
        if (_spec.numeralEntry && i < _spec.numeralDisplays.size() && _spec.numeralDisplays[i] && untilStrike)
            for (PlacedShape const& placed : step.placed)
            {
                Position const at = ToPosition(placed.LabelPoint(), placed.z, _frame.facing);
                TempSummon* numeral = owner->SummonCreature(_spec.numeralEntry, at, TEMPSUMMON_TIMED_DESPAWN,
                    untilStrike);
                if (!numeral)
                    continue;
                numeral->SetReactState(REACT_PASSIVE);
                numeral->SetDisplayId(_spec.numeralDisplays[i], _spec.numeralScale);
                _numerals.push_back(numeral->GetGUID());
            }
        if (_spec.onCall)
            _spec.onCall(owner, i, step.placed, untilStrike);
    }

    void CalledCombination::Live(Creature* owner, uint8 i)
    {
        Step& step = _punches[i];
        step.live = true;
        PunchTimes const& t = _times[i];
        uint32 const warn = t.strikeAt > _elapsedMs ? t.strikeAt - _elapsedMs : 0;
        if (!_spec.drawLive || !warn || _spec.timing.liveMs == 0)
            return;
        for (std::size_t k = 0; k < step.placed.size(); ++k)
        {
            ComboShape const& shape = _spec.shapes[step.punch.shapes[k]];
            BossMechanics::MechanicRef ref = Mechanic::Zone(owner, ZoneSpecOf(step.placed[k]), Milliseconds(warn));
            if (!ref.IsValid())
                continue;
            ref.Decoy().ZTolerance(_spec.zTolerance);
            if (shape.color)
                ref.Color(*shape.color);
            if (_spec.tag)
                ref.Tag(_spec.tag);
            _decoys.push_back(ref.Handle());
        }
    }

    void CalledCombination::Strike(Creature* owner, uint8 i)
    {
        _punches[i].struck = true;
        Say(_spec, "strike", Acore::StringFormat("punch={} of {} shapes={} at={}ms", i + 1, _punches.size(),
            ShapeNames(_spec, _punches[i].punch), _elapsedMs));
        if (_spec.onStrike)
            _spec.onStrike(owner, i);
    }

    void CalledCombination::Finish(Creature* owner)
    {
        ComboResult r;
        r.punches = static_cast<uint8>(_punches.size());
        r.landedPunch = _state->landed;
        r.landed = Landed();
        _active = false;
        _real.clear();
        _decoys.clear();
        _numerals.clear();
        Say(_spec, "end", Acore::StringFormat("punches={} landed={} after={}ms", r.punches, r.landed, _elapsedMs));
        if (_spec.onEnd)
            _spec.onEnd(owner, r);
    }

    void CalledCombination::Stop(Creature* owner)
    {
        if (owner)
        {
            for (BossMechanics::MechanicHandle const& h : _real)
                if (h)
                    Mechanic::Cancel(owner, h);
            for (BossMechanics::MechanicHandle const& h : _decoys)
                if (h)
                    Mechanic::Cancel(owner, h);
            for (ObjectGuid const& guid : _numerals)
                if (Creature* numeral = ObjectAccessor::GetCreature(*owner, guid))
                    numeral->DespawnOrUnsummon();
        }
        if (_active)
            Say(_spec, "stop", Acore::StringFormat("after={}ms landed={}", _elapsedMs, Landed()));
        _real.clear();
        _decoys.clear();
        _numerals.clear();
        _active = false;
        _state.reset();     // a late resolve of a canceled shape finds nothing
    }

    uint8 CalledCombination::Landed() const
    {
        if (!_state)
            return 0;
        return static_cast<uint8>(std::count(_state->landed.begin(), _state->landed.end(), true));
    }

    std::vector<PlacedShape> CalledCombination::ShapesOf(std::size_t i) const
    {
        return i < _punches.size() ? _punches[i].placed : std::vector<PlacedShape>{};
    }
}
