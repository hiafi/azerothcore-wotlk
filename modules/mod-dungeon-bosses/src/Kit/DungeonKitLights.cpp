/*
 * mod-dungeon-bosses, the shared dungeon kit: turning lights (DungeonKitLights.h, Gnomeregan WP-KT-G).
 */

#include "DungeonKitLights.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <string>
#include <utility>

namespace DungeonKit
{
    namespace
    {
        uint32 MsOf(Milliseconds d)
        {
            return static_cast<uint32>(std::max<int64>(0, d.count()));
        }

        void Say(TurningLightsSpec const& spec, char const* what, std::string const& detail)
        {
            LogMechanic(spec.dungeon, spec.boss, (std::string(spec.name) + "-" + what).c_str(), detail);
        }

        bool CanBeSpotted(Player* p)
        {
            return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
        }
    }

    bool TurningLights::AnchorAt(Creature* owner, Position& out) const
    {
        if (_spec.anchorUnit.IsEmpty())
        {
            out = _spec.anchorPoint;
            return true;
        }
        Unit* unit = ObjectAccessor::GetUnit(*owner, _spec.anchorUnit);
        if (!unit || !unit->IsInWorld() || unit->GetMap() != owner->GetMap())
            return false;
        out = unit->GetPosition();
        return true;
    }

    bool TurningLights::Start(Creature* owner, TurningLightsSpec spec)
    {
        Stop(owner);
        if (!owner || !owner->IsInWorld() || !spec.stalkerEntry || spec.count == 0 || spec.lengthYd <= 0.f
            || spec.angleDeg <= 0.f)
            return false;
        _spec = std::move(spec);
        Position at;
        if (!AnchorAt(owner, at))
            return false;

        _clock = LightClock(_spec.startBearing, _spec.degPerSec, _spec.count, _spec.direction);
        _darkLeftMs = MsOf(_spec.litAfter);
        _clock.Hold(_darkLeftMs);
        _lit = _darkLeftMs == 0;
        _elapsedMs = 0;
        _spotted = 0;
        _latch.Clear();
        _active = true;

        for (uint8 i = 0; i < _clock.Count(); ++i)
        {
            Position pos = at;
            pos.SetOrientation(_clock.BearingOf(i));
            TempSummon* stalker = owner->SummonCreature(_spec.stalkerEntry, pos, TEMPSUMMON_MANUAL_DESPAWN);
            if (!stalker)
            {
                _stalkers.push_back(ObjectGuid::Empty);     // light i keeps index i
                _cones.push_back({});
                continue;
            }
            stalker->SetReactState(REACT_PASSIVE);
            _stalkers.push_back(stalker->GetGUID());
            // The lit cone: the marker and the bots' live hazard, turning with its stalker. Telegraph-only: the
            // touch is the script's (Judge). During the dark it is a warning (the dim cone).
            BossMechanics::MechanicRef ref = Mechanic::Cone(owner, stalker, _spec.angleDeg, _spec.lengthYd,
                Milliseconds(_darkLeftMs));
            if (!ref.IsValid())
            {
                _cones.push_back({});
                continue;
            }
            ref.Persistent(Milliseconds(kForeverMs), Milliseconds(0)).ZTolerance(_spec.zBand);
            if (!_spec.drawLights)
                ref.NoTelegraph();
            if (_spec.color)
                ref.Color(*_spec.color);
            if (_spec.tag)
                ref.Tag(_spec.tag);
            if (_spec.configureLight)
                _spec.configureLight(ref);
            _cones.push_back(ref.Handle());
        }
        if (std::none_of(_stalkers.begin(), _stalkers.end(), [](ObjectGuid const& g) { return !g.IsEmpty(); }))
        {
            Stop(owner);
            return false;
        }

        RegisterLookAhead(owner);
        _aheadLeftMs = MsOf(_spec.lookAheadStep);
        _syncLeftMs = kSyncMs;
        Say(_spec, "start", Acore::StringFormat("count={} bearing={:.0f}deg speed={:.1f}deg/s dir={} "
            "cone={:.0f}deg/{:.0f}yd dark={}ms life={}ms ahead={}ms", _clock.Count(), _clock.Bearing() * 180.f / kPi,
            _clock.DegPerSec(), _clock.Direction(), _spec.angleDeg, _spec.lengthYd, _darkLeftMs, MsOf(_spec.life),
            MsOf(_spec.lookAhead)));
        return true;
    }

    void TurningLights::Update(Creature* owner, uint32 diff)
    {
        if (!_active || !owner || !owner->IsInWorld())
            return;
        _elapsedMs += diff;
        uint32 const life = MsOf(_spec.life);
        if (life && _elapsedMs >= life)
        {
            auto const onEnd = _spec.onEnd;
            Say(_spec, "end", Acore::StringFormat("after={}ms spotted={} turned={:.0f}deg", _elapsedMs, _spotted,
                _clock.TurnedDeg()));
            Stop(owner);
            if (onEnd)
                onEnd(owner);
            return;
        }

        _clock.Advance(diff);
        if (!_lit)
        {
            if (diff >= _darkLeftMs)
            {
                _darkLeftMs = 0;
                _lit = true;
                Say(_spec, "lit", Acore::StringFormat("bearing={:.0f}deg", _clock.Bearing() * 180.f / kPi));
            }
            else
                _darkLeftMs -= diff;
        }

        Position at;
        if (!AnchorAt(owner, at))
        {
            Say(_spec, "lost", Acore::StringFormat("anchor={}", _spec.anchorUnit.ToString()));
            Stop(owner);
            return;
        }
        bool sync = false;
        if (diff >= _syncLeftMs)
        {
            sync = true;
            _syncLeftMs = kSyncMs;
        }
        else
            _syncLeftMs -= diff;
        PlaceStalkers(owner, at, sync);

        std::vector<std::pair<ObjectGuid, uint8>> spotted;
        if (_lit)
            Judge(owner, at, spotted);

        uint32 const step = MsOf(_spec.lookAheadStep);
        if (step)
        {
            if (diff >= _aheadLeftMs)
            {
                RegisterLookAhead(owner);
                _aheadLeftMs = step;
            }
            else
                _aheadLeftMs -= diff;
        }

        Fire(owner, spotted);
    }

    void TurningLights::PlaceStalkers(Creature* owner, Position const& at, bool syncClients)
    {
        for (uint8 i = 0; i < _stalkers.size(); ++i)
        {
            if (_stalkers[i].IsEmpty())
                continue;
            Creature* stalker = ObjectAccessor::GetCreature(*owner, _stalkers[i]);
            if (!stalker || !stalker->IsInWorld())
                continue;
            float const o = _clock.BearingOf(i);
            if (!syncClients)
            {
                // The server's pose every tick: the registry reads the cone's facing from it.
                stalker->UpdatePosition(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), o);
                continue;
            }
            // The clients' pose a few times a second (no SetFacingTo in the tick of a move, RB-19).
            if (stalker->GetExactDist(&at) > 0.25f)
                stalker->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), o);
            else
            {
                stalker->UpdatePosition(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), o);
                stalker->SetFacingTo(o);
            }
        }
    }

    uint32 TurningLights::HorizonMs() const
    {
        uint32 horizon = MsOf(_spec.lookAhead);
        uint32 const life = MsOf(_spec.life);
        if (life)
            horizon = std::min(horizon, life > _elapsedMs ? life - _elapsedMs : 0);
        return horizon;
    }

    void TurningLights::RegisterLookAhead(Creature* owner)
    {
        std::vector<BossMechanics::MechanicHandle> old = std::move(_ahead);
        _ahead.clear();
        uint32 const horizon = HorizonMs();
        if (MsOf(_spec.lookAhead) && horizon)
        {
            Position at;
            bool const found = AnchorAt(owner, at);
            for (uint8 i = 0; found && i < _clock.Count(); ++i)
            {
                LightSector const sector = SweptSector(_clock.Ahead(i, horizon), _spec.angleDeg);
                BossMechanics::ZoneSpec zone;
                if (_spec.anchorUnit.IsEmpty())
                    zone.anchor = BossMechanics::Anchor(at);
                else if (Unit* unit = ObjectAccessor::GetUnit(*owner, _spec.anchorUnit))
                    zone.anchor = BossMechanics::Anchor(unit);     // moves with him, keeps the sector's facing
                zone.anchor.followFacing = false;
                zone.anchor.point.SetOrientation(sector.bearing);
                zone.shape = sector.Full() ? BossMechanics::Shape::Circle(_spec.lengthYd)
                    : BossMechanics::Shape::Cone(sector.angleDeg, _spec.lengthYd);
                // Telegraph-only and hot at once: the floor the light crosses next; bots leave it.
                BossMechanics::MechanicRef ref = Mechanic::Zone(owner, zone, Milliseconds(0));
                if (!ref.IsValid())
                    continue;
                ref.Persistent(Milliseconds(kForeverMs), Milliseconds(0)).NoFillTimer().ZTolerance(_spec.zBand);
                if (!_spec.drawLookAhead)
                    ref.NoTelegraph();
                if (_spec.lookAheadColor)
                    ref.Color(*_spec.lookAheadColor);
                if (_spec.tag)
                    ref.Tag(_spec.tag);
                if (_spec.configureLookAhead)
                    _spec.configureLookAhead(ref);
                _ahead.push_back(ref.Handle());
            }
        }
        // The new sectors are live before the old ones go: no gap for the bots.
        CancelLookAhead(owner, old);
    }

    void TurningLights::CancelLookAhead(Creature* owner, std::vector<BossMechanics::MechanicHandle>& handles)
    {
        if (owner)
            for (BossMechanics::MechanicHandle const& h : handles)
                if (h)
                    Mechanic::Cancel(owner, h);
        handles.clear();
    }

    void TurningLights::Judge(Creature* owner, Position const& at, std::vector<std::pair<ObjectGuid, uint8>>& spotted)
    {
        Vec2 const apex{ at.GetPositionX(), at.GetPositionY() };
        uint32 const latch = MsOf(_spec.latch);
        for (auto const& ref : owner->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CanBeSpotted(player) || std::fabs(player->GetPositionZ() - at.GetPositionZ()) > _spec.zBand)
                continue;
            Vec2 const p{ player->GetPositionX(), player->GetPositionY() };
            for (uint8 i = 0; i < _clock.Count(); ++i)
            {
                if (!InLight(apex, _clock.BearingOf(i), _spec.angleDeg, _spec.lengthYd, p))
                    continue;
                if (_spec.eligible && !_spec.eligible(player))
                    break;
                if (_latch.Try(player->GetGUID().GetRawValue(), _elapsedMs, latch))
                    spotted.emplace_back(player->GetGUID(), i);
                break;
            }
        }
    }

    void TurningLights::Fire(Creature* owner, std::vector<std::pair<ObjectGuid, uint8>> const& spotted)
    {
        for (auto const& [guid, light] : spotted)
        {
            if (!_active)
                return;     // a callback stopped the lights
            Player* player = ObjectAccessor::GetPlayer(*owner, guid);
            if (!player)
                continue;
            ++_spotted;
            Say(_spec, "spotted", Acore::StringFormat("player={} light={} bearing={:.0f}deg count={}",
                player->GetName(), light == kNoLight ? -1 : int32(light),
                light == kNoLight ? -1.f : _clock.BearingOf(light) * 180.f / kPi, _spotted));
            if (_spec.onSpotted)
                _spec.onSpotted(owner, player, light);
        }
    }

    bool TurningLights::TrySpot(Creature* owner, Player* who, uint8 light)
    {
        if (!_active || !owner || !CanBeSpotted(who))
            return false;
        if (!_latch.Try(who->GetGUID().GetRawValue(), _elapsedMs, MsOf(_spec.latch)))
            return false;
        Fire(owner, { { who->GetGUID(), light } });
        return true;
    }

    void TurningLights::Reverse(Creature* owner, Milliseconds stop)
    {
        if (!_active)
            return;
        _clock.Reverse(std::max(MsOf(stop), _clock.HoldLeftMs()));
        Say(_spec, "reverse", Acore::StringFormat("dir={} stop={}ms reversals={}", _clock.Direction(), MsOf(stop),
            _clock.Reversals()));
        if (owner && owner->IsInWorld())
        {
            RegisterLookAhead(owner);
            _aheadLeftMs = MsOf(_spec.lookAheadStep);
        }
    }

    void TurningLights::Hold(Creature* owner, Milliseconds hold)
    {
        if (!_active)
            return;
        _clock.Hold(MsOf(hold));
        if (owner && owner->IsInWorld())
        {
            RegisterLookAhead(owner);
            _aheadLeftMs = MsOf(_spec.lookAheadStep);
        }
    }

    void TurningLights::SetSpeed(Creature* owner, float degPerSec)
    {
        if (!_active)
            return;
        _clock.SetSpeed(degPerSec);
        Say(_spec, "speed", Acore::StringFormat("speed={:.1f}deg/s", _clock.DegPerSec()));
        if (owner && owner->IsInWorld())
        {
            RegisterLookAhead(owner);
            _aheadLeftMs = MsOf(_spec.lookAheadStep);
        }
    }

    void TurningLights::Stop(Creature* owner)
    {
        if (owner)
            for (BossMechanics::MechanicHandle const& h : _cones)
                if (h)
                    Mechanic::Cancel(owner, h);
        _cones.clear();
        CancelLookAhead(owner, _ahead);
        for (ObjectGuid const& guid : _stalkers)
            if (owner && !guid.IsEmpty())
                if (Creature* stalker = ObjectAccessor::GetCreature(*owner, guid))
                    stalker->DespawnOrUnsummon();
        _stalkers.clear();
        if (_active)
            Say(_spec, "stop", Acore::StringFormat("after={}ms spotted={} reversals={}", _elapsedMs, _spotted,
                _clock.Reversals()));
        _active = false;
        _lit = false;
        _latch.Clear();
    }
}
