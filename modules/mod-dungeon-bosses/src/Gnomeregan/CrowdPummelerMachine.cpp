/*
 * mod-dungeon-bosses, Gnomeregan D5: the ComboMachine (GnomereganMachines.h; CrowdPummelerMachine.h says what it does).
 * Crowd Pummeler owns one on the pocket frame; the Whole Workshop's fist (D6Hb, MT24) owns one on a Gnome Face's frame,
 * re-set every combination. It wraps the shared kit's DungeonKit::CalledCombination (KT-G) and never forks it.
 */

#include "CrowdPummelerMachine.h"
#include "BossMechanics.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitCombo.h"
#include "GnomereganKit.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include <algorithm>
#include <string>
#include <utility>
#include <vector>

namespace GnomereganMachines
{
    // CrowdPummelerLogic.h mirrors the contract's PunchShape (it stays engine-free).
    static_assert(uint8(PunchShape::LeftHalf) == uint8(GnomerPummeler::Shape::LeftHalf)
        && uint8(PunchShape::RightHalf) == uint8(GnomerPummeler::Shape::RightHalf)
        && uint8(PunchShape::Near) == uint8(GnomerPummeler::Shape::Near)
        && uint8(PunchShape::Far) == uint8(GnomerPummeler::Shape::Far)
        && uint8(PunchShape::Lane) == uint8(GnomerPummeler::Shape::Lane)
        && kPunchShapeCount == GnomerPummeler::kShapeCount, "the pure Shape mirrors PunchShape");

    namespace
    {
        GnomerPummeler::FrameParams ParamsOf(ComboFrame const& frame)
        {
            GnomerPummeler::FrameParams p;
            p.halfReachYd = frame.halfReachYd;
            p.nearRadiusYd = frame.nearRadiusYd;
            p.farOuterYd = frame.farOuterYd;
            p.laneWidthYd = frame.laneWidthYd;
            p.laneLengthYd = frame.laneLengthYd;
            return p;
        }

        DungeonKit::ComboFrame KitFrame(ComboFrame const& frame)
        {
            Position const& o = frame.origin;
            return DungeonKit::ComboFrame{ { o.GetPositionX(), o.GetPositionY() }, o.GetPositionZ(),
                o.GetOrientation() };
        }

        // The players each punch of one chain hit, filled by the registry's OnHit (players only: KT-G Q7). The
        // registry's closures hold it weakly, so a resolve after a Clear finds nothing.
        struct HitBook
        {
            std::vector<GuidSet> hits;
        };

        class PummelerComboMachine final : public ComboMachine
        {
        public:
            PummelerComboMachine(MachineOwner const& owner, ComboSpec spec, ComboExtras extras)
                : _logKey(owner.logKey ? owner.logKey : ""), _heroic(owner.heroic), _spec(std::move(spec)),
                _extras(std::move(extras))
            {
                if (owner.owner)
                {
                    _owner = owner.owner->GetGUID();
                    _map = owner.owner->GetMap();
                }
                SetFrame(_spec.frame);
            }

            void Update(uint32 diff) override
            {
                if (!_running)
                    return;
                Creature* owner = Owner();
                if (!owner || !owner->IsInWorld())
                    return;
                _kit.Update(owner, diff);
                FireLive(owner);
                Report(owner, false);
                if (_ended)
                    Finish(owner);
            }

            void Clear() override
            {
                bool const was = _running;
                _kit.Stop(Owner());     // a null owner (gone) only forgets: its zones went with it
                _book.reset();
                _chain.clear();
                _reported.clear();
                _liveFired.clear();
                _running = false;
                _ended = false;
                _landed = 0;
                if (was)
                    Log("clear", "the chain stopped");
            }

            std::string Describe() const override
            {
                Position const& o = _spec.frame.origin;
                return Acore::StringFormat("combination running={} punches={} elapsed={}ms landed={} frame=({:.1f}, "
                    "{:.1f}) facing={:.0f}deg heroic={}", _running ? 1 : 0, _chain.size(), _kit.ElapsedMs(), _landed,
                    o.GetPositionX(), o.GetPositionY(), o.GetOrientation() * 180.f / DungeonKit::kPi,
                    _heroic ? 1 : 0);
            }

            uint32 Call(std::vector<Punch> const& chain) override
            {
                Creature* owner = Owner();
                if (_running || chain.empty() || !owner || !owner->IsInWorld())
                    return 0;
                std::size_t const n = std::min<std::size_t>(chain.size(), GnomerPummeler::Tune::kMaxPunches);
                std::vector<Punch> punches(chain.begin(), chain.begin() + n);

                std::shared_ptr<HitBook> book = std::make_shared<HitBook>();
                book->hits.resize(n);
                std::weak_ptr<HitBook> const weak = book;

                DungeonKit::CalledCombinationSpec ks;
                ks.timing = GnomerPummeler::KitTiming(_spec.callFlashMs, _spec.windUpMs, _spec.markerMs, _spec.gapMs,
                    _spec.drawAllAtOnce);
                ks.drawCalls = _spec.drawAllAtOnce || _spec.callFlashMs > 0;
                ks.callColor = _extras.callColor;
                ks.dungeon = GnomereganRework::kLogDungeon;
                ks.boss = _logKey;
                ks.name = "combination";
                std::vector<DungeonKit::ComboPunch> kitPunches;
                kitPunches.reserve(n);
                for (uint32 i = 0; i < n; ++i)
                {
                    DungeonKit::ComboPunch kp;
                    std::vector<PunchShape> shapes{ punches[i].shape };
                    if (punches[i].paired && *punches[i].paired != punches[i].shape)
                        shapes.push_back(*punches[i].paired);
                    for (PunchShape const shape : shapes)
                    {
                        kp.shapes.push_back(static_cast<uint8>(ks.shapes.size()));
                        ks.shapes.push_back(KitShape(shape, i, weak));
                    }
                    kitPunches.push_back(std::move(kp));
                }
                // The kit calls these from its own Start / Update, inside this machine's calls: `this` outlives them.
                ks.onCall = [this](Creature* /*o*/, uint8 i, std::vector<DungeonKit::PlacedShape> const& placed,
                    uint32 /*untilStrikeMs*/)
                {
                    if (!_spec.drawAllAtOnce || !_spec.onNumber)
                        return;
                    for (DungeonKit::PlacedShape const& shape : placed)
                        _spec.onNumber(uint32(i) + 1, DungeonKit::ToPosition(shape.LabelPoint(), shape.z,
                            shape.facing));
                };
                ks.onStrike = [this](Creature* o, uint8 i)
                {
                    if (_extras.onStrike && i < _chain.size())
                        _extras.onStrike(o, i, _chain[i]);
                };
                ks.onEnd = [this](Creature* /*o*/, DungeonKit::ComboResult const& /*r*/) { _ended = true; };
                _kit.Configure(std::move(ks));

                _book = book;
                _chain = std::move(punches);
                _reported.assign(n, false);
                _liveFired.assign(n, false);
                _landed = 0;
                _ended = false;
                _running = true;
                if (!_kit.Start(owner, _kitFrame, std::move(kitPunches)))
                {
                    Log("refused", "the kit refused the chain");
                    Clear();
                    return 0;
                }
                if (_spec.callEmoteGroup && owner->IsAIEnabled && owner->AI())
                    owner->AI()->Talk(*_spec.callEmoteGroup);
                FireLive(owner);
                return _kit.Times().empty() ? 0 : _kit.Times().back().strikeAt;
            }

            void SetFrame(ComboFrame const& frame) override
            {
                _spec.frame = frame;
                _params = ParamsOf(frame);
                _kitFrame = KitFrame(frame);
                _bounds.reset();
                if (!frame.floor.Empty())
                    _bounds = GnomereganRework::BoundsOf(frame.floor);
            }

            bool Running() const override { return _running; }
            uint32 Landed() const override { return _landed; }

        private:
            Creature* Owner() const
            {
                return _map && !_owner.IsEmpty() ? _map->GetCreature(_owner) : nullptr;
            }

            void Log(char const* what, std::string const& detail) const
            {
                DungeonKit::LogMechanic(GnomereganRework::kLogDungeon, _logKey,
                    (std::string("combination-") + what).c_str(), detail);
            }

            // One shape of punch `i` as the kit's: the frame's geometry, the contract's percent (the tank's row at the
            // same percent: mechanics include the tank), Weakened, the extras' spell, tag and rider, the bots' floor.
            DungeonKit::ComboShape KitShape(PunchShape shape, uint32 i, std::weak_ptr<HitBook> const& weak) const
            {
                std::size_t const k = static_cast<std::size_t>(shape);
                DungeonKit::ComboShape s;
                s.def = GnomerPummeler::ShapeDef(static_cast<GnomerPummeler::Shape>(shape), _params);
                s.pct = _spec.pct[k];
                s.tankPct = _spec.pct[k];
                s.school = _extras.school;
                s.spellId = _extras.spellIds[k];
                s.weakened = _spec.weakened;
                s.rider = _extras.rider;
                s.color = _extras.liveColor;
                s.name = _extras.names[k] ? _extras.names[k] : "punch";
                uint32 const tag = _extras.tags[k];
                std::optional<BossMechanics::SpotBounds> const bounds = _bounds;
                std::function<void(Player*, PunchShape)> const onHit = _extras.onHit;
                // Stored in the registry with the zone: guids and copies only (no `this`).
                s.configure = [weak, i, shape, tag, bounds, onHit](BossMechanics::MechanicRef& ref)
                {
                    if (tag)
                        ref.Tag(tag);
                    if (bounds)
                        ref.Within(*bounds);
                    ref.OnHit([weak, i, shape, onHit](Unit* hit)
                    {
                        Player* player = hit ? hit->ToPlayer() : nullptr;
                        if (!player)
                            return;     // pets and guardians never count (KT-G Q7)
                        if (std::shared_ptr<HitBook> book = weak.lock())
                            if (i < book->hits.size())
                                book->hits[i].insert(player->GetGUID());
                        if (onHit)
                            onHit(player, shape);
                    });
                };
                return s;
            }

            // Sequential calls: each punch's live marker start (the kit drew it this tick).
            void FireLive(Creature* owner)
            {
                std::vector<DungeonKit::PunchTimes> const& times = _kit.Times();
                for (std::size_t i = 0; i < _liveFired.size() && i < times.size(); ++i)
                {
                    if (_liveFired[i] || _kit.ElapsedMs() < times[i].liveFrom)
                        continue;
                    _liveFired[i] = true;
                    uint32 const until = times[i].strikeAt > _kit.ElapsedMs() ? times[i].strikeAt - _kit.ElapsedMs()
                        : 0;
                    if (_extras.onLive && _spec.markerMs > 0 && until > 0)
                        _extras.onLive(owner, uint32(i), _chain[i], until);
                }
            }

            // onPunch for every punch whose report is due (all: the chain ended).
            void Report(Creature* owner, bool all)
            {
                std::vector<DungeonKit::PunchTimes> const& times = _kit.Times();
                for (std::size_t i = 0; i < _reported.size() && i < times.size(); ++i)
                {
                    if (_reported[i] || (!all && !GnomerPummeler::PunchReportDue(_kit.ElapsedMs(), times[i].strikeAt)))
                        continue;
                    _reported[i] = true;
                    std::vector<Player*> hit;
                    if (_book && i < _book->hits.size())
                        for (ObjectGuid const& guid : _book->hits[i])
                            if (Player* player = ObjectAccessor::GetPlayer(*owner, guid))
                                hit.push_back(player);
                    if (_book && i < _book->hits.size() && !_book->hits[i].empty())
                        ++_landed;
                    Punch const& punch = _chain[i];
                    std::string shapes = _extras.names[std::size_t(punch.shape)];
                    if (punch.paired)
                        shapes += std::string("+") + _extras.names[std::size_t(*punch.paired)];
                    Log("punch", Acore::StringFormat("punch={} of {} shapes={} hit={} landed={}", i + 1,
                        _chain.size(), shapes, _book && i < _book->hits.size() ? _book->hits[i].size() : 0, _landed));
                    if (_spec.onPunch)
                        _spec.onPunch(uint32(i), punch, hit);
                }
            }

            void Finish(Creature* owner)
            {
                Report(owner, true);
                _running = false;
                _ended = false;
                uint32 const punches = uint32(_chain.size());
                if (_extras.onEnd)
                    _extras.onEnd(owner, punches, _landed);
            }

            char const* _logKey;
            bool _heroic;
            ComboSpec _spec;
            ComboExtras _extras;
            ObjectGuid _owner;
            Map* _map = nullptr;
            GnomerPummeler::FrameParams _params;
            DungeonKit::ComboFrame _kitFrame;
            std::optional<BossMechanics::SpotBounds> _bounds;
            DungeonKit::CalledCombination _kit;
            std::shared_ptr<HitBook> _book;
            std::vector<Punch> _chain;
            std::vector<bool> _reported;
            std::vector<bool> _liveFired;
            uint32 _landed = 0;
            bool _running = false;
            bool _ended = false;
        };
    }

    std::unique_ptr<ComboMachine> MakeComboMachine(MachineOwner const& owner, ComboSpec spec, ComboExtras extras)
    {
        return std::make_unique<PummelerComboMachine>(owner, std::move(spec), std::move(extras));
    }

    std::unique_ptr<ComboMachine> MakeComboMachine(MachineOwner const& owner, ComboSpec spec)
    {
        return MakeComboMachine(owner, std::move(spec), ComboExtras{});
    }
}
