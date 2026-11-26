/*
 * mod-dungeon-bosses, the shared dungeon kit: two-ring mines (DungeonKitMines.h, Gnomeregan WP-KT-G).
 */

#include "DungeonKitMines.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include "Unit.h"
#include <algorithm>
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

        void Say(TwoRingMineSpec const& spec, char const* what, std::string const& detail)
        {
            LogMechanic(spec.dungeon, spec.boss, (std::string(spec.name) + "-" + what).c_str(), detail);
        }
    }

    void TwoRingMines::Configure(TwoRingMineSpec spec)
    {
        _spec = std::move(spec);
    }

    uint32 TwoRingMines::Add(Creature* owner, Position const& at)
    {
        if (!owner || !owner->IsInWorld() || !MineRings{ _spec.triggerYd, _spec.blastYd }.Valid())
            return 0;
        uint32 const id = _nextId++;

        // The trigger: the registry's mine, telegraph-only (the blast is the kit's). Players only, as every kind.
        BossMechanics::MechanicRef trigger = Mechanic::Mine(owner, at, _spec.triggerYd, _spec.arm, _spec.grace);
        if (!trigger.IsValid())
            return 0;
        std::weak_ptr<std::vector<uint32>> queue = _tripped;
        trigger.ZTolerance(_spec.zBand).OnResolve([queue, id](BossMechanics::ResolveResult const& r)
        {
            if (r.fizzled)
                return;
            if (std::shared_ptr<std::vector<uint32>> q = queue.lock())
                q->push_back(id);     // the blast waits for Update: no registration inside the resolve
        });
        if (_spec.triggerColor)
            trigger.Color(*_spec.triggerColor);
        if (_spec.tag)
            trigger.Tag(_spec.tag);
        if (_spec.configureTrigger)
            _spec.configureTrigger(trigger);

        Entry e;
        e.id = id;
        e.at = at;
        e.spec = _spec;
        e.trigger = trigger.Handle();

        // The blast ring: lasting, telegraph-only, outline only; it warns over the arming and keeps the bots out.
        BossMechanics::MechanicRef ring = Mechanic::Circle(owner, at, _spec.blastYd, _spec.arm);
        if (ring.IsValid())
        {
            ring.Persistent(Milliseconds(kForeverMs), Milliseconds(0)).NoFillTimer().ZTolerance(_spec.zBand);
            if (!_spec.drawBlast)
                ring.NoTelegraph();
            if (_spec.blastColor)
                ring.Color(*_spec.blastColor);
            if (_spec.tag)
                ring.Tag(_spec.tag);
            if (_spec.configureBlast)
                _spec.configureBlast(ring);
            e.ring = ring.Handle();
        }

        _book.Add(id, _nowMs, MsOf(_spec.arm), MsOf(_spec.life));
        _mines.push_back(std::move(e));
        Say(_spec, "add", Acore::StringFormat("id={} at=({:.1f}, {:.1f}) trigger={:.1f}yd blast={:.1f}yd arm={}ms "
            "life={}ms live={}", id, at.GetPositionX(), at.GetPositionY(), _spec.triggerYd, _spec.blastYd,
            MsOf(_spec.arm), MsOf(_spec.life), _mines.size()));
        return id;
    }

    void TwoRingMines::Update(Creature* owner, uint32 diff)
    {
        _nowMs += diff;
        if (!owner || !owner->IsInWorld())
            return;
        if (!_tripped->empty())
        {
            std::vector<uint32> tripped = std::move(*_tripped);
            _tripped->clear();
            for (uint32 const id : tripped)
                if (_book.Has(id))
                    Blast(owner, id, true);
        }
        for (uint32 const id : _book.Expired(_nowMs))
        {
            Say(_spec, "fizzle", Acore::StringFormat("id={} after life", id));
            Drop(owner, id);
        }
    }

    void TwoRingMines::Blast(Creature* owner, uint32 id, bool tripped)
    {
        auto it = std::find_if(_mines.begin(), _mines.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _mines.end())
            return;
        Entry const e = *it;
        Drop(owner, id);

        GuidSet hit;
        Vec2 const center{ e.at.GetPositionX(), e.at.GetPositionY() };
        for (auto const& ref : owner->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (InBlast(center, e.at.GetPositionZ(), { player->GetPositionX(), player->GetPositionY() },
                    player->GetPositionZ(), e.spec.blastYd, e.spec.zBand))
                hit.insert(player->GetGUID());
        }
        if (!hit.empty())
        {
            RegistryHitSpec h;
            h.pct = e.spec.pct;
            h.tankPct = e.spec.tankPct;
            h.school = e.spec.school;
            h.spellId = e.spec.spellId;
            h.weakened = e.spec.weakened;
            h.rider = e.spec.rider;
            h.tag = e.spec.tag;
            h.onHit = e.spec.onHit;
            RegistryHit(owner, hit, h);
        }
        Say(e.spec, "blast", Acore::StringFormat("id={} by={} hits={} live={}", id, tripped ? "trigger" : "detonator",
            hit.size(), _mines.size()));
        if (e.spec.onBlast)
            e.spec.onBlast(owner, id, e.at, hit, tripped);
    }

    void TwoRingMines::Drop(Creature* owner, uint32 id)
    {
        _book.Remove(id);
        auto it = std::find_if(_mines.begin(), _mines.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _mines.end())
            return;
        if (owner)
        {
            if (it->trigger)
                Mechanic::Cancel(owner, it->trigger);
            if (it->ring)
                Mechanic::Cancel(owner, it->ring);
        }
        _mines.erase(it);
    }

    bool TwoRingMines::Detonate(Creature* owner, uint32 id)
    {
        if (!owner || !owner->IsInWorld() || !_book.Has(id))
            return false;
        Blast(owner, id, false);
        return true;
    }

    uint32 TwoRingMines::DetonateAll(Creature* owner, bool armedOnly)
    {
        if (!owner || !owner->IsInWorld())
            return 0;
        uint32 n = 0;
        for (uint32 const id : _book.Detonations(_nowMs, armedOnly))
            if (Detonate(owner, id))
                ++n;
        Say(_spec, "detonate-all", Acore::StringFormat("blown={} armedOnly={} left={}", n, armedOnly, _mines.size()));
        return n;
    }

    void TwoRingMines::Remove(Creature* owner, uint32 id)
    {
        if (_book.Has(id))
            Say(_spec, "fizzle", Acore::StringFormat("id={} removed", id));
        Drop(owner, id);
    }

    void TwoRingMines::Clear(Creature* owner)
    {
        for (uint32 const id : _book.Ids())
            Drop(owner, id);
        _book.Clear();
        _mines.clear();
        _tripped->clear();
        _nowMs = 0;
    }

    std::optional<Position> TwoRingMines::PositionOf(uint32 id) const
    {
        for (Entry const& e : _mines)
            if (e.id == id)
                return e.at;
        return std::nullopt;
    }

    BossMechanics::MechanicHandle TwoRingMines::TriggerOf(uint32 id) const
    {
        for (Entry const& e : _mines)
            if (e.id == id)
                return e.trigger;
        return {};
    }

    BossMechanics::MechanicHandle TwoRingMines::BlastRingOf(uint32 id) const
    {
        for (Entry const& e : _mines)
            if (e.id == id)
                return e.ring;
        return {};
    }
}
