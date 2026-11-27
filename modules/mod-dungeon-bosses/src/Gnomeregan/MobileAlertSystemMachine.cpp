/*
 * mod-dungeon-bosses, Gnomeregan D4: the LightsMachine (GnomereganMachines.h, MobileAlertSystemMachine.h), on KT-G's
 * DungeonKit::TurningLights. Replaces WP-S0's inert stub behind the same factory.
 */

#include "MobileAlertSystemMachine.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitLights.h"
#include "GnomereganKit.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "StringFormat.h"
#include <string>
#include <utility>
#include <vector>

namespace GnomereganMachines
{
    char const* SpotSourceName(SpotSource source)
    {
        switch (source)
        {
            case SpotSource::Light:
                return "light";
            case SpotSource::Also:
                return "also";
            case SpotSource::Script:
                return "script";
        }
        return "?";
    }

    namespace
    {
        using namespace GnomerAlert;

        bool CanBeSpotted(Player const* p)
        {
            return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
        }

        float Degrees(float rad)
        {
            return rad * 180.f / DungeonKit::kPi;
        }

        class LightsMachineImpl final : public AlertLightsMachine
        {
        public:
            LightsMachineImpl(MachineOwner const& owner, LightsAnchor anchor, LightsSpec spec, LightsExtras extras)
                : _logKey(owner.logKey ? owner.logKey : ""), _heroic(owner.heroic), _anchor(std::move(anchor)),
                  _spec(std::move(spec)), _x(std::move(extras))
            {
                if (owner.owner)
                {
                    _owner = owner.owner->GetGUID();
                    _map = owner.owner->GetMap();
                }
                if (_anchor.unit.IsEmpty() && !_anchor.point)
                    _anchor.unit = _owner;      // no anchor given: the lights ride on the owner
                if (_x.bounds)
                    _bounds = _x.bounds;
                else if (!_spec.floor.Empty())
                    _bounds = GnomereganRework::BoundsOf(_spec.floor);
            }

            // --- Machine ---------------------------------------------------------------------------------------------

            void Update(uint32 diff) override
            {
                Creature* owner = Owner();
                if (!owner || !owner->IsInWorld())
                    return;
                _clockMs += diff;

                if (_kit.Active())
                {
                    _kit.Update(owner, diff);       // may call OnSpotted (the judge) and end a sweep's life
                    if (_kit.Active())
                        _lastFacing = _kit.BearingOf(0);
                }

                if (_spec.mode == LightsSpec::Mode::Turning && _started && _kit.Active() && _spec.reverseMinMs)
                {
                    if (diff >= _reverseInMs)
                        Reverse();
                    else
                        _reverseInMs -= diff;
                }

                if (_started && _spec.alsoSpotted)
                {
                    if (diff >= _alsoInMs)
                    {
                        _alsoInMs = std::max<uint32>(_x.alsoEveryMs, 100);
                        JudgeAlso(owner);
                    }
                    else
                        _alsoInMs -= diff;
                }
            }

            void Clear() override
            {
                Creature* owner = Owner();
                bool const wasUp = _started || _kit.Active();
                if (!owner && _map)
                {
                    // The owner is gone: its stalkers are found through the map (the kit needs the owner for it).
                    for (uint8 i = 0; i < 8; ++i)
                    {
                        ObjectGuid const g = _kit.StalkerOf(i);
                        if (g.IsEmpty())
                            continue;
                        if (Creature* stalker = _map->GetCreature(g))
                            stalker->DespawnOrUnsummon();
                    }
                }
                _kit.Stop(owner);
                if (wasUp)
                    DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "lights",
                        Acore::StringFormat("clear spotted={} sweeps={} reversals={} speed={:.1f}", _spotted, _sweeps,
                            _reversals, CurrentDegPerSec()));
                _latch.Clear();
                _started = false;
                _spotted = 0;
                _sweeps = 0;
                _reversals = 0;
                _speedPct = 0.f;
                _clockMs = 0;
                _reverseInMs = 0;
                _alsoInMs = 0;
            }

            std::string Describe() const override
            {
                return Acore::StringFormat("lights mode={} started={} active={} lit={} facing={:.0f}deg speed={:.1f}"
                    "deg/s dir={} spotted={} sweeps={} reversals={} next-reverse={}ms", ModeName(), _started ? 1 : 0,
                    _kit.Active() ? 1 : 0, _kit.Lit() ? 1 : 0, Degrees(Facing()), CurrentDegPerSec(),
                    _kit.Active() ? _kit.Clock().Direction() : 0, _spotted, _sweeps, _reversals, _reverseInMs);
            }

            // --- LightsMachine ---------------------------------------------------------------------------------------

            void Start() override
            {
                Creature* owner = Owner();
                if (!owner || !owner->IsInWorld())
                    return;
                _started = true;
                _alsoInMs = std::max<uint32>(_x.alsoEveryMs, 100);
                if (_spec.mode == LightsSpec::Mode::Sweep)
                {
                    DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "lights",
                        Acore::StringFormat("armed mode=sweep heroic={}", _heroic ? 1 : 0));
                    return;
                }
                Position at;
                if (!AnchorAt(owner, at))
                    return;
                float const bearing = _x.startBearing ? *_x.startBearing : at.GetOrientation();
                LightPlan const plan = TurningPlan(_spec.cones, SpeedAfter(_spec.turnDegPerSec, _speedPct),
                    _x.direction, _x.litAfterMs);
                if (!StartKit(owner, bearing, plan))
                    return;
                _reverseInMs = _x.litAfterMs + NextReversal();
            }

            bool Sweep(Player* target) override
            {
                Creature* owner = Owner();
                if (_spec.mode != LightsSpec::Mode::Sweep || !owner || !owner->IsInWorld() || !target
                    || !target->IsInWorld() || _kit.Active())
                    return false;
                Position at;
                if (!AnchorAt(owner, at))
                    return false;
                float const bearing = BearingTo({ at.GetPositionX(), at.GetPositionY() },
                    { target->GetPositionX(), target->GetPositionY() });
                if (!StartKit(owner, bearing, SweepPlan(_spec.sweepDeg, _spec.dimMs, _spec.sweepMs)))
                    return false;
                ++_sweeps;
                DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "lights",
                    Acore::StringFormat("sweep target={} bearing={:.0f}deg n={}", target->GetName(), Degrees(bearing),
                        _sweeps));
                return true;
            }

            void Reverse() override
            {
                Creature* owner = Owner();
                if (!owner || _spec.mode != LightsSpec::Mode::Turning || !_kit.Active())
                    return;
                _kit.Reverse(owner, Milliseconds(_spec.reverseStopMs));
                ++_reversals;
                _reverseInMs = _spec.reverseStopMs + NextReversal();
                if (_spec.reverseEmoteGroup && owner->IsAIEnabled && owner->AI())
                    owner->AI()->Talk(*_spec.reverseEmoteGroup);
            }

            void SpeedUp(float pct) override
            {
                _speedPct += std::max(0.f, pct);
                if (_spec.mode != LightsSpec::Mode::Turning || !_kit.Active())
                    return;
                if (Creature* owner = Owner())
                    _kit.SetSpeed(owner, CurrentDegPerSec());
            }

            float Facing() const override { return _kit.Active() ? _kit.BearingOf(0) : _lastFacing; }
            uint32 SpottedCount() const override { return _spotted; }

            // --- AlertLightsMachine ----------------------------------------------------------------------------------

            bool Spot(Player* who, SpotSource source) override
            {
                return OnSpotted(who, source, DungeonKit::TurningLights::kNoLight);
            }

            bool Active() const override { return _kit.Active(); }
            bool Lit() const override { return _kit.Lit(); }
            float DegPerSec() const override { return CurrentDegPerSec(); }
            uint32 Reversals() const override { return _reversals; }
            uint32 Sweeps() const override { return _sweeps; }

        private:
            Creature* Owner() const
            {
                return _map ? _map->GetCreature(_owner) : nullptr;
            }

            char const* ModeName() const { return _spec.mode == LightsSpec::Mode::Sweep ? "sweep" : "turning"; }

            float CurrentDegPerSec() const
            {
                if (_spec.mode == LightsSpec::Mode::Sweep)
                    return SweepPlan(_spec.sweepDeg, _spec.dimMs, _spec.sweepMs).degPerSec;
                return SpeedAfter(_spec.turnDegPerSec, _speedPct);
            }

            uint32 NextReversal() const
            {
                return ReversalInMs(_spec.reverseMinMs, _spec.reverseMaxMs, frand(0.f, 1.f));
            }

            bool AnchorAt(Creature* owner, Position& out) const
            {
                if (_anchor.point)
                {
                    out = *_anchor.point;
                    return true;
                }
                Unit* unit = ObjectAccessor::GetUnit(*owner, _anchor.unit);
                if (!unit || !unit->IsInWorld())
                    return false;
                out = unit->GetPosition();
                return true;
            }

            bool Eligible(Player* p) const
            {
                if (!CanBeSpotted(p))
                    return false;
                if (!_spec.floor.Empty()
                    && !_spec.floor.Contains({ p->GetPositionX(), p->GetPositionY() }, p->GetPositionZ()))
                    return false;
                return !_x.eligible || _x.eligible(p);
            }

            bool StartKit(Creature* owner, float bearing, LightPlan const& plan)
            {
                DungeonKit::TurningLightsSpec k;
                if (_anchor.point)
                    k.anchorPoint = *_anchor.point;
                else
                    k.anchorUnit = _anchor.unit;
                k.stalkerEntry = _x.stalkerEntry;
                k.count = static_cast<uint8>(std::min<uint32>(plan.count, 8));
                k.startBearing = bearing;
                k.degPerSec = plan.degPerSec;
                k.direction = plan.direction;
                k.angleDeg = _spec.coneDeg;
                k.lengthYd = _spec.rangeYd;
                k.zBand = _x.zBand;
                k.litAfter = Milliseconds(plan.litAfterMs);
                k.life = Milliseconds(plan.lifeMs);
                k.latch = Milliseconds(_spec.latchMs);
                k.lookAhead = Milliseconds(plan.lookAheadMs);
                k.lookAheadStep = Milliseconds(plan.lookAheadStepMs);
                k.drawLookAhead = plan.drawLookAhead;
                k.color = _x.color;
                k.tag = _x.tag;
                k.eligible = [this](Player* who) { return Eligible(who); };
                k.onSpotted = [this](Creature* /*owner*/, Player* who, uint8 light)
                {
                    OnSpotted(who, SpotSource::Light, light);
                };
                std::optional<BossMechanics::SpotBounds> const bounds = _bounds;
                uint32 const floorTag = _x.tag ? FloorTag(_x.tag) : 0;
                k.configureLight = [bounds](BossMechanics::MechanicRef& ref)
                {
                    if (bounds)
                        ref.Within(*bounds);
                };
                k.configureLookAhead = [bounds, floorTag](BossMechanics::MechanicRef& ref)
                {
                    if (bounds)
                        ref.Within(*bounds);
                    if (floorTag)
                        ref.Tag(floorTag);
                };
                k.dungeon = GnomereganRework::kLogDungeon;
                k.boss = _logKey;
                k.name = "lights";
                return _kit.Start(owner, std::move(k));
            }

            void JudgeAlso(Creature* owner)
            {
                std::vector<ObjectGuid> hits;
                for (auto const& ref : owner->GetMap()->GetPlayers())
                {
                    Player* p = ref.GetSource();
                    if (CanBeSpotted(p) && _spec.alsoSpotted(p))
                        hits.push_back(p->GetGUID());
                }
                for (ObjectGuid const& g : hits)
                    if (Player* p = ObjectAccessor::GetPlayer(*owner, g))
                        OnSpotted(p, SpotSource::Also, DungeonKit::TurningLights::kNoLight);
            }

            bool OnSpotted(Player* who, SpotSource source, uint8 light)
            {
                if (!CanBeSpotted(who) || !Owner())
                    return false;
                if (!_latch.Try(who->GetGUID().GetRawValue(), _clockMs, _spec.latchMs))
                    return false;
                ++_spotted;
                DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey, "lights",
                    Acore::StringFormat("spotted player={} by={} light={} count={} heroic={}", who->GetName(),
                        SpotSourceName(source), light == DungeonKit::TurningLights::kNoLight ? -1 : int32(light),
                        _spotted, _heroic ? 1 : 0));
                ObjectGuid const guid = who->GetGUID();
                if (_spec.mode == LightsSpec::Mode::Turning && _spec.speedUpPctPerSpotted > 0.f)
                    SpeedUp(_spec.speedUpPctPerSpotted);
                Creature* owner = Owner();
                Player* again = owner ? ObjectAccessor::GetPlayer(*owner, guid) : nullptr;
                if (!again)
                    return true;
                if (_x.onSpottedBy)
                    _x.onSpottedBy(again, source, light);
                else if (_spec.onSpotted)
                    _spec.onSpotted(again);
                return true;
            }

            Map* _map = nullptr;
            ObjectGuid _owner;
            char const* _logKey = "";
            bool _heroic = false;
            LightsAnchor _anchor;
            LightsSpec _spec;
            LightsExtras _x;
            std::optional<BossMechanics::SpotBounds> _bounds;
            DungeonKit::TurningLights _kit;
            DungeonKit::TouchLatch _latch;
            uint32 _clockMs = 0;
            uint32 _reverseInMs = 0;
            uint32 _alsoInMs = 0;
            uint32 _spotted = 0;
            uint32 _sweeps = 0;
            uint32 _reversals = 0;
            float _speedPct = 0.f;
            float _lastFacing = 0.f;
            bool _started = false;
        };
    }

    std::unique_ptr<AlertLightsMachine> MakeAlertLightsMachine(MachineOwner const& owner, LightsAnchor anchor,
        LightsSpec spec, LightsExtras extras)
    {
        return std::make_unique<LightsMachineImpl>(owner, std::move(anchor), std::move(spec), std::move(extras));
    }

    std::unique_ptr<LightsMachine> MakeLightsMachine(MachineOwner const& owner, LightsAnchor anchor, LightsSpec spec)
    {
        return MakeAlertLightsMachine(owner, std::move(anchor), std::move(spec), LightsExtras{});
    }
}
