/*
 * mod-dungeon-bosses, the shared dungeon kit: the ring wall (DungeonKitRing.h, Blackrock Spire WP-KT-B2).
 */

#include "DungeonKitRing.h"
#include "Creature.h"
#include "DungeonKitWalls.h"
#include "GameTime.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

namespace DungeonKit
{
    namespace
    {
        // One ring's state, shared by the copies of its OnResolve callback (the registry copies the function).
        struct RingState
        {
            explicit RingState(LethalRingSpec const& s)
                : spec(s), ring(RingWallOf(s)), watch(ring)
            {
            }

            LethalRingSpec spec;
            RingWall ring;
            RingWatch watch;
            StrikeBook book;
            GraceBook grace;
        };

        uint64 NowMs()
        {
            return static_cast<uint64>(GameTime::GetGameTimeMS().count());
        }

        Unit* FindOwner(Map* map, ObjectGuid guid)
        {
            if (!map)
                return nullptr;
            if (guid.IsPlayer())
                return ObjectAccessor::GetPlayer(map, guid);
            return map->GetCreature(guid);
        }

        // A player or a player's pet / guardian, alive, here, never a GM (nor a GM's pet), in the ring's z band.
        bool CountsForRing(Unit const* u, Map const* map, RingState const& r)
        {
            if (!u || !u->IsInWorld() || !u->IsAlive() || u->GetMap() != map)
                return false;
            Player const* controller = u->GetCharmerOrOwnerPlayerOrPlayerItself();
            if (!controller || controller->IsGameMaster())
                return false;
            return std::fabs(u->GetPositionZ() - r.spec.center.GetPositionZ()) <= r.spec.zBand;
        }

        bool KeptIn(RingState const& r, ObjectGuid g)
        {
            return std::find(r.spec.keepIn.begin(), r.spec.keepIn.end(), g) != r.spec.keepIn.end();
        }

        Vec2 At(Unit const* u)
        {
            return { u->GetPositionX(), u->GetPositionY() };
        }

        // Every player on the map that counts, then (with `pets`) each one's controlled units that count (pets,
        // guardians, totems and charms: m_Controlled). Copied first: a push or a kill can change the set.
        template <typename Fn>
        void ForEachCandidate(Map* map, RingState const& r, bool pets, Fn&& fn)
        {
            for (auto const& ref : map->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!CountsForRing(player, map, r))
                    continue;
                fn(static_cast<Unit*>(player));
                if (!pets)
                    continue;
                std::vector<Unit*> controlled(player->m_Controlled.begin(), player->m_Controlled.end());
                for (Unit* u : controlled)
                    if (u && !u->IsPlayer() && CountsForRing(u, map, r))
                        fn(u);
            }
        }

        void Push(Unit* owner, RingState& r, Unit* u)
        {
            float const fallback = owner ? owner->GetAbsoluteAngle(u) : 0.f;
            PushOut const p = PlanPushOut(r.ring, At(u), r.spec.pushClearYd, fallback);
            if (p.distance <= 0.f)
                return;
            u->KnockbackFrom(p.source.x, p.source.y, PushSpeedXY(p.distance, r.spec.pushSpeedZ), r.spec.pushSpeedZ);
            r.grace.Grant(u->GetGUID().GetRawValue(), NowMs() + PushFlightMs(r.spec.pushSpeedZ)
                + kRingPushGraceExtraMs);
            LogMechanic(r.spec.dungeon, r.spec.boss, "lethal-ring-push", "unit=" + u->GetName()
                + (u->IsPlayer() ? "" : " pet=1") + " yd=" + std::to_string(static_cast<int>(p.distance + 0.5f)));
            if (r.spec.onPush)
                r.spec.onPush(u);
        }

        // Pushes everyone not kept in who must go (closing: inside the band's outer edge; later: inside the disc).
        void PushOutAll(Unit* owner, RingState& r, bool closing)
        {
            if (!r.spec.pushOut || !owner)
                return;
            Map* map = owner->GetMap();
            uint64 const now = NowMs();
            std::vector<ObjectGuid> push;
            ForEachCandidate(map, r, true, [&](Unit* u)
            {
                ObjectGuid const g = u->GetGUID();
                if (u->IsTotem() || r.grace.Has(g.GetRawValue(), now))
                    return;         // a totem is rooted: it stays (and dies if it stands in the band)
                if (PushOutNeeded(r.ring, At(u), KeptIn(r, g), closing))
                    push.push_back(g);
            });
            for (ObjectGuid const& g : push)
                if (Unit* u = ObjectAccessor::GetUnit(*owner, g))
                    Push(owner, r, u);
        }

        Unit* NearestStriker(Unit* owner, RingState const& r, Unit const* victim)
        {
            Unit* best = nullptr;
            float bestDist = 0.f;
            for (ObjectGuid const& g : r.spec.strikers)
            {
                Unit* s = ObjectAccessor::GetUnit(*owner, g);
                if (!s || !s->IsInWorld() || s->GetMap() != owner->GetMap())
                    continue;
                float const d = s->GetExactDist2d(victim);
                if (!best || d < bestDist)
                {
                    best = s;
                    bestDist = d;
                }
            }
            return best ? best : owner;
        }

        void Strike(Unit* owner, RingState& r, ObjectGuid victimGuid, bool crossed)
        {
            Unit* victim = ObjectAccessor::GetUnit(*owner, victimGuid);
            if (!CountsForRing(victim, owner->GetMap(), r))
                return;
            if (r.spec.spareKeepIn && KeptIn(r, victimGuid))
                return;
            uint64 const now = NowMs();
            if (r.grace.Has(victimGuid.GetRawValue(), now))
                return;         // flying over the band on the kit's own push
            if (!r.book.Due(victimGuid.GetRawValue(), now))
                return;
            Unit* caster = NearestStriker(owner, r, victim);
            if (r.spec.killSpell)
                caster->CastSpell(victim, r.spec.killSpell, TRIGGERED_FULL_MASK, nullptr, nullptr, owner->GetGUID());
            FinishLethalStrike(caster->IsInMap(victim) ? caster : owner, victim);
            LogMechanic(r.spec.dungeon, r.spec.boss, "lethal-ring",
                "victim=" + victim->GetName() + (victim->IsPlayer() ? "" : " pet=1") + (crossed ? " crossed=1" : ""));
            if (r.spec.onStrike)
                r.spec.onStrike(victim);
        }

        // One tick of an armed ring: push-outs first (they get their grace), then the registry's list (players in the
        // band), then pets in the band and every crossing, then the strikes.
        void TickRing(Map* map, ObjectGuid ownerGuid, RingState& r, BossMechanics::ResolveResult const& res)
        {
            Unit* owner = FindOwner(map, ownerGuid);
            if (!owner)
                return;
            if (r.spec.pushDuringLife)
                PushOutAll(owner, r, false);

            BossMechanics::MechanicHandle const handle{ res.mechanicId };
            uint64 const now = NowMs();
            std::vector<std::pair<ObjectGuid, bool>> victims;      // guid, crossed
            GuidUnorderedSet listed;
            auto add = [&](ObjectGuid g, bool crossed)
            {
                if (listed.insert(g).second)
                    victims.emplace_back(g, crossed);
            };
            for (ObjectGuid const& g : res.hits)
                add(g, false);

            ForEachCandidate(map, r, r.spec.pets, [&](Unit* u)
            {
                ObjectGuid const g = u->GetGUID();
                // Observe always (a pushed unit's landing must not read as a crossing once its grace ends).
                bool const crossed = r.spec.crossings && r.watch.Observe(g.GetRawValue(), At(u));
                if (r.grace.Has(g.GetRawValue(), now))
                    return;
                if (crossed)
                    add(g, true);
                else if (!u->IsPlayer() && Mechanic::Contains(owner, handle, u))
                    add(g, false);
            });
            r.watch.Sweep();

            for (auto const& [g, crossed] : victims)
            {
                // A strike may end the encounter (the last player dies): stop when the owner is gone.
                Unit* again = FindOwner(map, ownerGuid);
                if (!again)
                    break;
                Strike(again, r, g, crossed);
            }
            r.book.Prune(now);
            r.grace.Prune(now);
        }
    }

    BossMechanics::MechanicRef LethalRing(Unit* owner, LethalRingSpec const& spec, ObjectGuid* carrier)
    {
        if (!owner || !owner->IsInWorld() || spec.radius <= 0.f || spec.width <= 0.f
            || spec.width * 0.5f >= spec.radius)
            return {};
        auto state = std::make_shared<RingState>(spec);
        BossMechanics::MechanicRef ref = Mechanic::Donut(owner, BossMechanics::Anchor(spec.center),
            state->ring.Inner(), state->ring.Outer(), spec.armAfter);
        if (!ref.IsValid())
            return ref;
        // Lethal() first, in the registering statement (refused after the commit; X4).
        ref.Lethal().Persistent(spec.lifetime, spec.tick).NoFillTimer();
        // Blackrock Spire F-3: a ring that never strikes pets (pushed out instead) tells the bots, so a pet owner's
        // view keeps no pet margin from it (BM ViewRules::LethalPetExtraYd).
        if (!spec.pets)
            ref.SparesPets();
        if (spec.color)
            ref.Color(*spec.color);
        if (spec.tag)
            ref.Tag(spec.tag);
        if (spec.zTolerance > 0.f)
            ref.ZTolerance(spec.zTolerance);

        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        ref.OnResolve([map, ownerGuid, state](BossMechanics::ResolveResult const& r)
        {
            TickRing(map, ownerGuid, *state, r);
        });

        // The close: everyone not kept in inside the band's outer edge goes out now (the push lands before the arm).
        PushOutAll(owner, *state, true);

        if (spec.carrierEntry)
        {
            uint32 const life = static_cast<uint32>(std::max<int64>(0, (spec.armAfter + spec.lifetime).count()));
            if (TempSummon* c = owner->SummonCreature(spec.carrierEntry, spec.center, TEMPSUMMON_TIMED_DESPAWN, life))
            {
                if (spec.carrierAura)
                    c->CastSpell(c, spec.carrierAura, true);
                if (carrier)
                    *carrier = c->GetGUID();
            }
        }

        LogMechanic(spec.dungeon, spec.boss, "lethal-ring-raised",
            "radius=" + std::to_string(static_cast<int>(spec.radius + 0.5f)) + " arm="
            + std::to_string(spec.armAfter.count()) + " life=" + std::to_string(spec.lifetime.count()) + " keepIn="
            + std::to_string(spec.keepIn.size()));
        return ref;
    }

    BossMechanics::SpotBounds RingInside(LethalRingSpec const& spec, float marginYd)
    {
        RingWall const w = RingWallOf(spec);
        float const r = std::max(0.5f, w.Inner() - std::max(0.f, marginYd));
        return BossMechanics::SpotBounds().Circle(spec.center, r);
    }

    BossMechanics::MechanicHandle LethalRings::Add(Unit* owner, LethalRingSpec const& spec)
    {
        ObjectGuid carrier;
        BossMechanics::MechanicHandle h;
        {
            BossMechanics::MechanicRef ref = LethalRing(owner, spec, &carrier);
            h = ref;
        }   // committed here
        if (h)
            _rings.push_back({ h, carrier });
        else if (!carrier.IsEmpty() && owner)
            if (Creature* c = owner->GetMap()->GetCreature(carrier))
                c->DespawnOrUnsummon();
        return h;
    }

    void LethalRings::Clear(Unit* owner)
    {
        if (owner)
            for (Live const& l : _rings)
            {
                Mechanic::Cancel(owner, l.handle);
                if (!l.carrier.IsEmpty() && owner->IsInWorld())
                    if (Creature* c = owner->GetMap()->GetCreature(l.carrier))
                        c->DespawnOrUnsummon();
            }
        _rings.clear();
    }

    bool LethalRings::Prune(Unit* owner)
    {
        if (!owner || !owner->IsInWorld())
            return !_rings.empty();
        BossMechanics::Registry const* reg = Mechanic::Read(owner->GetMap());
        for (auto it = _rings.begin(); it != _rings.end();)
        {
            if (reg && reg->Find(it->handle.id))
            {
                ++it;
                continue;
            }
            if (!it->carrier.IsEmpty())
                if (Creature* c = owner->GetMap()->GetCreature(it->carrier))
                    c->DespawnOrUnsummon();
            it = _rings.erase(it);
        }
        return !_rings.empty();
    }

    bool LethalRings::Contains(Unit* owner, Unit const* who) const
    {
        if (!owner || !who)
            return false;
        return std::any_of(_rings.begin(), _rings.end(), [owner, who](Live const& l)
        {
            return Mechanic::Contains(owner, l.handle, who);
        });
    }
}
