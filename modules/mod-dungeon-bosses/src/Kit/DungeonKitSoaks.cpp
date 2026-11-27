/*
 * mod-dungeon-bosses, the shared dungeon kit: Soaks that must be held (DungeonKitSoaks.h, Zul'Farrak WP-KT).
 */

#include "DungeonKitSoaks.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include "Unit.h"
#include <algorithm>

namespace DungeonKit
{
    namespace
    {
        uint32 Ms(Milliseconds d)
        {
            return static_cast<uint32>(std::max<int64>(0, d.count()));
        }

        bool Counts(Player const* p)
        {
            return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
        }

        void Say(DwellSoakSpec const& spec, char const* what, std::string const& detail)
        {
            LogMechanic(spec.dungeon, spec.boss, (std::string(spec.name) + "-" + what).c_str(), detail);
        }
    }

    bool DwellSoaks::Excluded(Unit const* who) const
    {
        if (!who)
            return true;
        for (Entry const& e : _soaks)
        {
            if (e.anchor == who->GetGUID())
                return true;
            if (e.spec.excludeAura && who->HasAura(e.spec.excludeAura))
                return true;
        }
        return false;
    }

    GuidSet DwellSoaks::CarriersFor(Creature* owner, Entry const& e) const
    {
        GuidSet out;
        if (!e.spec.who.carriers.empty())
        {
            for (ObjectGuid const& g : e.spec.who.carriers)
            {
                Unit const* u = ObjectAccessor::GetUnit(*owner, g);
                if (!u || !Excluded(u))
                    out.insert(g);
            }
            return out;
        }
        for (auto const& ref : owner->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (Counts(player) && !Excluded(player))
                out.insert(player->GetGUID());
        }
        return out;
    }

    void DwellSoaks::Register(Creature* owner, Entry& e, GuidSet carriers)
    {
        if (e.soak)
            Mechanic::Cancel(owner, e.soak);
        e.soak = {};
        e.carriers = std::move(carriers);
        Unit* anchor = ObjectAccessor::GetUnit(*owner, e.anchor);
        if (!anchor || e.carriers.empty())
            return;     // nobody may hold it now: no job for the bots (an empty set would mean everyone)
        // A held Soak with a life is canceled before its warning ends; one without lasts the whole fight.
        uint32 const left = e.clock.LeftMs();
        Milliseconds const warn = left ? Milliseconds(left) + kWarnSlack : kWholeFight;
        BossMechanics::Eligibility who = e.spec.who;
        who.carriers = e.carriers;
        BossMechanics::MechanicRef ref = Mechanic::Soak(owner, anchor, e.spec.radius, std::max<uint8>(1, e.spec.count),
            warn);
        if (!ref.IsValid())
            return;
        ref.MissedSoak(BossMechanics::MissedSoakMode::Never).Eligible(who).NoFillTimer();
        if (e.spec.oneClaimPerBot)
            ref.OneClaimPerBot();
        if (!e.spec.draw)
            ref.NoTelegraph();
        if (e.spec.color)
            ref.Color(*e.spec.color);
        if (e.spec.tag)
            ref.Tag(e.spec.tag);
        if (e.spec.configure)
            e.spec.configure(ref);
        e.soak = ref.Handle();
    }

    uint32 DwellSoaks::Add(Creature* owner, Unit* anchor, DwellSoakSpec spec)
    {
        if (!owner || !owner->IsInWorld() || !anchor || !anchor->IsInWorld() || !anchor->IsAlive()
            || anchor->GetMap() != owner->GetMap() || spec.radius <= 0.f || Has(anchor->GetGUID()))
            return 0;
        Entry e;
        e.id = _nextId++;
        e.anchor = anchor->GetGUID();
        e.clock = SoakAt(Ms(spec.dwell), Ms(spec.life));
        e.spec = std::move(spec);
        if (e.spec.rank != 0)
            _ranked = true;
        std::size_t at = _soaks.size();
        if (_ranked)
        {
            std::vector<int32> ranks;
            ranks.reserve(_soaks.size());
            for (Entry const& other : _soaks)
                ranks.push_back(other.spec.rank);
            at = SoakRankAt(ranks, e.spec.rank);
        }
        uint32 const id = e.id;
        _soaks.insert(_soaks.begin() + static_cast<std::ptrdiff_t>(at), std::move(e));
        // A new anchor leaves every other held Soak's carriers: bring them all up to date (the new one registers).
        RefreshCarriers(owner, at);
        Entry const& added = *std::find_if(_soaks.begin(), _soaks.end(), [id](Entry const& x) { return x.id == id; });
        Say(added.spec, "start", Acore::StringFormat("id={} anchor={} dwell={}ms life={}ms carriers={}", added.id,
            added.anchor.ToString(), Ms(added.spec.dwell), Ms(added.spec.life), added.carriers.size()));
        return added.id;
    }

    void DwellSoaks::Update(Creature* owner, uint32 diff)
    {
        if (!owner || !owner->IsInWorld() || _soaks.empty())
            return;
        _pollMs += diff;
        if (_pollMs < kPollMs)
            return;
        uint32 const elapsed = _pollMs;
        _pollMs = 0;

        Map* map = owner->GetMap();
        BossMechanics::Registry const* reg = BossMechanics::Registry::Get(map);
        for (uint32 const id : Ids())
        {
            auto it = std::find_if(_soaks.begin(), _soaks.end(), [id](Entry const& e) { return e.id == id; });
            if (it == _soaks.end())
                continue;
            Unit* anchor = ObjectAccessor::GetUnit(*owner, it->anchor);
            if (!anchor || !anchor->IsInWorld() || !anchor->IsAlive() || anchor->GetMap() != map)
            {
                Entry e = std::move(*it);
                _soaks.erase(it);
                Mechanic::Cancel(owner, e.soak);
                Say(e.spec, "lost", Acore::StringFormat("id={} anchor={}", e.id, e.anchor.ToString()));
                if (e.spec.onLost)
                    e.spec.onLost(e.anchor);
                continue;
            }

            // Who holds it now: alive, in range, in the registry's rule, and neither an anchor nor excluded.
            BossMechanics::ActiveMechanic const* soak = reg && it->soak ? reg->Find(it->soak.id) : nullptr;
            std::vector<uint64> inside;
            std::vector<Player*> players;
            for (auto const& ref : map->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!Counts(player) || Excluded(player))
                    continue;
                if (!InPickupRange(player->GetExactDist2d(anchor), player->GetPositionZ() - anchor->GetPositionZ(),
                        it->spec.radius, it->spec.zBand))
                    continue;
                if (soak ? !reg->IsEligible(*soak, player) : !it->carriers.count(player->GetGUID()))
                    continue;
                inside.push_back(player->GetGUID().GetRawValue());
                players.push_back(player);
            }

            SoakAtResult const r = it->clock.Update(inside, elapsed);
            if (r.step == SoakAtStep::Wait)
                continue;
            Entry e = std::move(*it);
            _soaks.erase(it);
            Mechanic::Cancel(owner, e.soak);
            if (r.step == SoakAtStep::Done)
            {
                Player* taker = nullptr;
                for (Player* p : players)
                    if (p->GetGUID().GetRawValue() == r.taker)
                        taker = p;
                Say(e.spec, "done", Acore::StringFormat("id={} anchor={} taker={} after={}ms", e.id,
                    e.anchor.ToString(), taker ? taker->GetName() : "?", e.clock.AgeMs()));
                if (e.spec.onDone && taker)
                    e.spec.onDone(taker, anchor);
            }
            else
            {
                Say(e.spec, "expire", Acore::StringFormat("id={} anchor={} after={}ms", e.id, e.anchor.ToString(),
                    e.clock.AgeMs()));
                if (e.spec.onExpire)
                    e.spec.onExpire(e.anchor);
            }
        }

        // The group changed (an anchor went, a player died or arrived, an aura came or went): the bots' sets follow.
        RefreshCarriers(owner, _soaks.size());
    }

    void DwellSoaks::RefreshCarriers(Creature* owner, std::size_t from)
    {
        std::vector<GuidSet> want;
        std::vector<bool> changed;
        want.reserve(_soaks.size());
        changed.reserve(_soaks.size());
        for (Entry const& e : _soaks)
        {
            want.push_back(CarriersFor(owner, e));
            changed.push_back(want.back() != e.carriers);
        }
        // Unranked: only the changed ones (and the forced one). Ranked: every one from the first change on, in rank
        // order, so the registry's ids follow the ranks.
        std::vector<bool> const again = SoakRegisterMask(_ranked, from, changed);
        for (std::size_t i = 0; i < _soaks.size(); ++i)
            if (again[i])
                Register(owner, _soaks[i], std::move(want[i]));
    }

    void DwellSoaks::Reprioritize(Creature* owner, std::vector<uint32> const& order)
    {
        std::vector<uint32> const ids = SoakPriorityOrder(Ids(), order);
        std::vector<Entry> sorted;
        sorted.reserve(_soaks.size());
        std::size_t listed = 0;     // SoakPriorityOrder puts the listed ones first
        while (listed < ids.size() && std::find(order.begin(), order.end(), ids[listed]) != order.end())
            ++listed;
        for (std::size_t i = 0; i < ids.size(); ++i)
        {
            uint32 const id = ids[i];
            auto it = std::find_if(_soaks.begin(), _soaks.end(), [id](Entry const& e) { return e.id == id; });
            it->spec.rank = static_cast<int32>(std::min(i, listed));
            sorted.push_back(std::move(*it));
        }
        _soaks = std::move(sorted);
        _ranked = true;
        std::string line;
        for (Entry const& e : _soaks)
            line += (line.empty() ? "" : ",") + Acore::StringFormat("{}:{}", e.id, e.spec.rank);
        if (!_soaks.empty())
            Say(_soaks.front().spec, "rank", Acore::StringFormat("order={}", line));
        if (owner && owner->IsInWorld())
            RefreshCarriers(owner, 0);
    }

    void DwellSoaks::SetRank(Creature* owner, uint32 id, int32 rank)
    {
        auto it = std::find_if(_soaks.begin(), _soaks.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _soaks.end())
            return;
        std::size_t const was = static_cast<std::size_t>(it - _soaks.begin());
        it->spec.rank = rank;
        _ranked = true;
        std::stable_sort(_soaks.begin(), _soaks.end(),
            [](Entry const& a, Entry const& b) { return a.spec.rank < b.spec.rank; });
        std::size_t const now = static_cast<std::size_t>(std::find_if(_soaks.begin(), _soaks.end(),
            [id](Entry const& e) { return e.id == id; }) - _soaks.begin());
        if (owner && owner->IsInWorld())
            RefreshCarriers(owner, std::min(was, now));
    }

    int32 DwellSoaks::RankOf(uint32 id) const
    {
        for (Entry const& e : _soaks)
            if (e.id == id)
                return e.spec.rank;
        return 0;
    }

    void DwellSoaks::Cancel(Creature* owner, uint32 id)
    {
        auto it = std::find_if(_soaks.begin(), _soaks.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _soaks.end())
            return;
        Entry e = std::move(*it);
        _soaks.erase(it);
        if (owner)
        {
            Mechanic::Cancel(owner, e.soak);
            if (owner->IsInWorld())
                RefreshCarriers(owner, _soaks.size());
        }
    }

    void DwellSoaks::CancelOn(Creature* owner, ObjectGuid anchor)
    {
        for (Entry const& e : _soaks)
            if (e.anchor == anchor)
            {
                Cancel(owner, e.id);
                return;
            }
    }

    void DwellSoaks::Clear(Creature* owner)
    {
        std::vector<Entry> all = std::move(_soaks);
        _soaks.clear();
        _pollMs = 0;
        _ranked = false;
        if (owner)
            for (Entry const& e : all)
                Mechanic::Cancel(owner, e.soak);
    }

    bool DwellSoaks::Has(ObjectGuid anchor) const
    {
        return std::any_of(_soaks.begin(), _soaks.end(), [anchor](Entry const& e) { return e.anchor == anchor; });
    }

    std::vector<uint32> DwellSoaks::Ids() const
    {
        std::vector<uint32> ids;
        ids.reserve(_soaks.size());
        for (Entry const& e : _soaks)
            ids.push_back(e.id);
        return ids;
    }

    ObjectGuid DwellSoaks::AnchorOf(uint32 id) const
    {
        for (Entry const& e : _soaks)
            if (e.id == id)
                return e.anchor;
        return ObjectGuid::Empty;
    }

    uint32 DwellSoaks::LeftMs(uint32 id) const
    {
        for (Entry const& e : _soaks)
            if (e.id == id)
                return e.clock.LeftMs();
        return 0;
    }

    BossMechanics::MechanicHandle DwellSoaks::SoakOf(uint32 id) const
    {
        for (Entry const& e : _soaks)
            if (e.id == id)
                return e.soak;
        return {};
    }
}
