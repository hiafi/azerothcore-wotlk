/*
 * mod-dungeon-bosses, the shared dungeon kit: lethal walls and relic dispensers (DungeonKitWalls.h, WP-KT-2).
 */

#include "DungeonKitWalls.h"
#include "Chat.h"
#include "Creature.h"
#include "GameObject.h"
#include "GameTime.h"
#include "Group.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Unit.h"
#include <algorithm>
#include <memory>
#include <cmath>
#include <string>
#include <string_view>

namespace DungeonKit
{
    namespace
    {
        // One wall's state, shared by the copies of its OnResolve callback (the registry copies the function).
        struct WallState
        {
            explicit WallState(LethalWallSpec const& s)
                : spec(s), line(WallLineOf(s)), watch(line)
            {
            }

            LethalWallSpec spec;
            WallLine line;
            WallWatch watch;
            StrikeBook book;
        };

        Unit* FindOwner(Map* map, ObjectGuid guid)
        {
            if (!map)
                return nullptr;
            if (guid.IsPlayer())
                return ObjectAccessor::GetPlayer(map, guid);
            return map->GetCreature(guid);
        }

        // The wall's floor height at the point of the line nearest `p`.
        float WallZAt(WallState const& w, Vec2 p)
        {
            float along = 0.f;
            SegmentDistance(w.line.from, w.line.to, p, &along);
            float const len = w.line.Length();
            float const t = len > 1e-4f ? along / len : 0.f;
            return w.spec.from.GetPositionZ() + t * (w.spec.to.GetPositionZ() - w.spec.from.GetPositionZ());
        }

        bool CountsForWall(Unit const* u, Map const* map)
        {
            if (!u || !u->IsInWorld() || !u->IsAlive() || u->GetMap() != map)
                return false;
            Player const* controller = u->GetCharmerOrOwnerPlayerOrPlayerItself();
            return controller && !controller->IsGameMaster();
        }

        Unit* NearestStriker(Unit* owner, WallState const& w, Unit const* victim)
        {
            Unit* best = nullptr;
            float bestDist = 0.f;
            for (ObjectGuid const& g : w.spec.strikers)
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

        void Strike(Unit* owner, WallState& w, ObjectGuid victimGuid, bool crossed)
        {
            Unit* victim = ObjectAccessor::GetUnit(*owner, victimGuid);
            if (!CountsForWall(victim, owner->GetMap()))        // alive, here, and never a GM (nor a GM's pet)
                return;
            if (!w.book.Due(victimGuid.GetRawValue(), GameTime::GetGameTimeMS().count()))
                return;
            Unit* caster = NearestStriker(owner, w, victim);
            if (w.spec.killSpell)
                caster->CastSpell(victim, w.spec.killSpell, TRIGGERED_FULL_MASK, nullptr, nullptr, owner->GetGUID());
            // User ruling (F-2): an outright kill. The spell's script already killed a survivor; this catches a cast
            // that did not land (no spell, a refused cast, a caster gone mid-cast).
            FinishLethalStrike(caster->IsInMap(victim) ? caster : owner, victim);
            LogMechanic(w.spec.dungeon, w.spec.boss, "lethal-wall",
                "victim=" + victim->GetName() + (victim->IsPlayer() ? "" : " pet=1") + (crossed ? " crossed=1" : ""));
            if (w.spec.onStrike)
                w.spec.onStrike(victim);
        }

        // One tick of an armed wall: the registry's list (players inside), then every player and controlled unit on
        // the map (pets inside the hitbox; anyone whose step crossed the line), then the strikes. Victims are
        // collected first: a strike kills, and a dead pet leaves its owner's control set mid-loop.
        void TickWall(Map* map, ObjectGuid ownerGuid, WallState& w, BossMechanics::ResolveResult const& r)
        {
            Unit* owner = FindOwner(map, ownerGuid);
            if (!owner)
                return;
            BossMechanics::MechanicHandle const handle{ r.mechanicId };

            std::vector<std::pair<ObjectGuid, bool>> victims;      // guid, crossed
            GuidUnorderedSet listed;
            auto add = [&](ObjectGuid g, bool crossed)
            {
                if (listed.insert(g).second)
                    victims.emplace_back(g, crossed);
            };
            for (ObjectGuid const& g : r.hits)
                add(g, false);

            auto watch = [&](Unit* u)
            {
                Vec2 const p{ u->GetPositionX(), u->GetPositionY() };
                if (std::fabs(u->GetPositionZ() - WallZAt(w, p)) > w.spec.zBand)
                    return false;
                return w.watch.Observe(u->GetGUID().GetRawValue(), p);
            };

            if (w.spec.crossings || w.spec.pets)
            {
                for (auto const& ref : map->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (!CountsForWall(player, map))
                        continue;
                    if (w.spec.crossings && watch(player))
                        add(player->GetGUID(), true);
                    if (!w.spec.pets)
                        continue;
                    for (Unit* u : player->m_Controlled)
                    {
                        if (!CountsForWall(u, map) || u->IsPlayer())
                            continue;
                        bool const crossed = w.spec.crossings && watch(u);
                        if (crossed || Mechanic::Contains(owner, handle, u))
                            add(u->GetGUID(), crossed);
                    }
                }
                w.watch.Sweep();
            }

            for (auto const& [g, crossed] : victims)
            {
                // A strike may end the encounter (the last player dies): stop when the owner is gone.
                Unit* again = FindOwner(map, ownerGuid);
                if (!again)
                    break;
                Strike(again, w, g, crossed);
            }
            w.book.Prune(GameTime::GetGameTimeMS().count());
        }
    }

    bool FinishLethalStrike(Unit* killer, Unit* victim)
    {
        if (!victim || !victim->IsInWorld())
            return false;
        LethalStrikeTarget t;
        t.alive = victim->IsAlive() && victim->GetHealth() > 0;
        Player const* player = victim->ToPlayer();
        t.godMode = player && player->GetCommandStatus(CHEAT_GOD);
        t.spiritOfRedemption = victim->HasAuraType(SPELL_AURA_SPIRIT_OF_REDEMPTION);
        if (!LethalStrikeKills(t))
            return false;
        Unit::Kill(killer, victim);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LethalWall
    // ----------------------------------------------------------------------------------------------------------------

    BossMechanics::MechanicRef LethalWall(Unit* owner, LethalWallSpec const& spec)
    {
        if (!owner || !owner->IsInWorld() || spec.width <= 0.f)
            return {};
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner,
            BossMechanics::Shapes::Line(spec.from, spec.to, spec.width), spec.armAfter);
        if (!ref.IsValid())
            return ref;
        // Lethal() first, in the registering statement (refused after the commit; X4).
        ref.Lethal().Persistent(spec.lifetime, spec.tick).NoFillTimer();
        if (spec.color)
            ref.Color(*spec.color);
        if (spec.tag)
            ref.Tag(spec.tag);
        if (spec.zTolerance > 0.f)
            ref.ZTolerance(spec.zTolerance);

        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        auto state = std::make_shared<WallState>(spec);
        ref.OnResolve([map, ownerGuid, state](BossMechanics::ResolveResult const& r)
        {
            TickWall(map, ownerGuid, *state, r);
        });
        LogMechanic(spec.dungeon, spec.boss, "lethal-wall-raised",
            "length=" + std::to_string(static_cast<int>(state->line.Length() + 0.5f)) + " arm="
            + std::to_string(spec.armAfter.count()));
        return ref;
    }

    BossMechanics::MechanicRef LethalWall(Unit* owner, Position const& from, Position const& to, float width,
        uint32 killSpell, Milliseconds armAfter)
    {
        LethalWallSpec spec;
        spec.from = from;
        spec.to = to;
        spec.width = width;
        spec.killSpell = killSpell;
        spec.armAfter = armAfter;
        return LethalWall(owner, spec);
    }

    BossMechanics::MechanicHandle LethalWalls::Add(Unit* owner, LethalWallSpec const& spec)
    {
        BossMechanics::MechanicHandle const h = LethalWall(owner, spec);
        if (h)
            _walls.push_back(h);
        return h;
    }

    void LethalWalls::Clear(Unit* owner)
    {
        if (owner)
            for (BossMechanics::MechanicHandle const& h : _walls)
                Mechanic::Cancel(owner, h);
        _walls.clear();
    }

    bool LethalWalls::Contains(Unit* owner, Unit const* who) const
    {
        if (!owner || !who)
            return false;
        return std::any_of(_walls.begin(), _walls.end(), [owner, who](BossMechanics::MechanicHandle const& h)
        {
            return Mechanic::Contains(owner, h, who);
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RelicDispenser
    // ----------------------------------------------------------------------------------------------------------------

    DispenseResult Dispense(WorldObject const* where, Player* user, uint32 itemId, char const* dungeon)
    {
        DispenseResult result;
        if (!where || !user || !itemId)
            return result;
        Map const* map = where->GetMap();

        std::vector<Player*> players{ user };
        if (Group* group = user->GetGroup())
            for (GroupReference* itr = group->GetFirstMember(); itr; itr = itr->next())
                if (Player* member = itr->GetSource())
                    if (member != user)
                        players.push_back(member);

        std::vector<RelicCandidate> candidates;
        candidates.reserve(players.size());
        for (Player* p : players)
        {
            RelicCandidate c;
            c.id = p->GetGUID().GetRawValue();
            c.sameMap = p->IsInWorld() && p->GetMap() == map;
            c.hasItem = c.sameMap && p->HasItemCount(itemId, 1, true);
            candidates.push_back(c);
        }
        DispensePlan const plan = PlanDispense(candidates);
        result.had = plan.had;
        result.away = plan.away;

        for (std::uint64_t id : plan.give)
        {
            auto it = std::find_if(players.begin(), players.end(), [id](Player const* p)
            {
                return p->GetGUID().GetRawValue() == id;
            });
            if (it == players.end())
                continue;
            if ((*it)->AddItem(itemId, 1))
                result.given.push_back((*it)->GetGUID());
            else
                ++result.noRoom;
        }

        LogMechanic(dungeon, "relic", "dispense", "item=" + std::to_string(itemId) + " user=" + user->GetName()
            + " given=" + std::to_string(result.given.size()) + " had=" + std::to_string(result.had) + " away="
            + std::to_string(result.away) + " noRoom=" + std::to_string(result.noRoom));
        return result;
    }

    RelicDispenserAI::RelicDispenserAI(GameObject* go, uint32 itemId, char const* dungeon)
        : GameObjectAI(go), _itemId(itemId), _dungeon(dungeon)
    {
    }

    bool RelicDispenserAI::GossipHello(Player* player, bool reportUse)
    {
        // Handled either way (true): the click never reaches GameObject::Use (no loot, no state change, no despawn).
        // The use itself only (a report-use follows some clicks).
        if (!DispensesOnClick(player != nullptr, reportUse) || !CanDispense(player))
            return true;
        DispenseResult const result = Dispense(me, player, _itemId, _dungeon);
        if (result.given.empty() && !result.noRoom)
            ChatHandler(player->GetSession()).SendNotification(std::string_view("Everyone here already carries one."));
        OnDispensed(player, result);
        return true;
    }
}
