/*
 * mod-dungeon-bosses, the shared dungeon kit: wing portals, sealed arenas and spell credits (DungeonKitWings.h,
 * Scarlet Monastery WP-KT-SM).
 */

#include "DungeonKitWings.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameTime.h"
#include "Group.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include "Unit.h"
#include <cmath>
#include <utility>

namespace DungeonKit
{
    namespace
    {
        uint32 constexpr kPortalCheckMs = 2000;
        uint32 constexpr kPortalUseCooldownMs = 1000;
        uint32 constexpr kSealHoldMs = 1000;

        uint64 NowMs()
        {
            return static_cast<uint64>(GameTime::GetGameTimeMS().count());
        }

        bool Busy(Player const* p)
        {
            return p->IsBeingTeleported() || p->IsInFlight() || p->GetVehicle();
        }

        void Notify(Player* player, std::string const& text)
        {
            if (player && player->GetSession())
                ChatHandler(player->GetSession()).SendNotification(text);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WingPortals
    // ----------------------------------------------------------------------------------------------------------------

    GameObject* WingPortals::Spawn(Map* map, Entry& e)
    {
        float const o = e.spec.spot.GetOrientation();
        GameObject* go = map->SummonGameObject(e.spec.goEntry, e.spec.spot, 0.f, 0.f, std::sin(o * 0.5f),
            std::cos(o * 0.5f), 0);
        e.object = go ? go->GetGUID() : ObjectGuid::Empty;
        LOG_INFO(kLogCategory, "{} portal {} {} object={} at=({:.1f}, {:.1f}, {:.1f})", e.spec.dungeon, e.spec.name,
            go ? "open" : "open-failed", e.spec.goEntry, e.spec.spot.GetPositionX(), e.spec.spot.GetPositionY(),
            e.spec.spot.GetPositionZ());
        return go;
    }

    bool WingPortals::Open(Map* map, WingPortalSpec const& spec)
    {
        if (!map || !spec.goEntry)
            return false;
        for (Entry& e : _portals)
        {
            if (e.spec.id != spec.id)
                continue;
            bool const same = e.spec.goEntry == spec.goEntry && e.spec.spot.GetExactDist(&spec.spot) < 0.1f;
            GameObject* go = e.object.IsEmpty() ? nullptr : map->GetGameObject(e.object);
            if (same && go)
            {
                e.spec = spec;      // the destination or the escort range may change; the object stays
                return true;
            }
            if (go)
                go->DespawnOrUnsummon();
            e.spec = spec;
            return Spawn(map, e) != nullptr;
        }
        Entry e;
        e.spec = spec;
        _portals.push_back(std::move(e));
        return Spawn(map, _portals.back()) != nullptr;
    }

    void WingPortals::Close(Map* map, uint32 id)
    {
        for (Entry& e : _portals)
            if (e.spec.id == id)
            {
                if (map && !e.object.IsEmpty())
                    if (GameObject* go = map->GetGameObject(e.object))
                        go->DespawnOrUnsummon();
                LOG_INFO(kLogCategory, "{} portal {} close", e.spec.dungeon, e.spec.name);
            }
        std::erase_if(_portals, [id](Entry const& e) { return e.spec.id == id; });
    }

    void WingPortals::CloseAll(Map* map)
    {
        std::vector<uint32> const ids = OpenIds();
        for (uint32 id : ids)
            Close(map, id);
    }

    void WingPortals::Update(Map* map, uint32 diff)
    {
        if (!map || _portals.empty())
            return;
        _checkMs += diff;
        if (_checkMs < kPortalCheckMs)
            return;
        _checkMs = 0;
        for (Entry& e : _portals)
        {
            if (!e.object.IsEmpty() && map->GetGameObject(e.object))
                continue;
            // Gone with its grid (or never spawned): back once the grid is loaded again (a player came near).
            if (map->IsGridLoaded(e.spec.spot.GetPositionX(), e.spec.spot.GetPositionY()))
                Spawn(map, e);
        }
    }

    bool WingPortals::IsOpen(uint32 id) const
    {
        return SpecOf(id) != nullptr;
    }

    std::vector<uint32> WingPortals::OpenIds() const
    {
        std::vector<uint32> ids;
        for (Entry const& e : _portals)
            ids.push_back(e.spec.id);
        return ids;
    }

    ObjectGuid WingPortals::ObjectOf(uint32 id) const
    {
        for (Entry const& e : _portals)
            if (e.spec.id == id)
                return e.object;
        return ObjectGuid::Empty;
    }

    WingPortalSpec const* WingPortals::SpecOf(uint32 id) const
    {
        for (Entry const& e : _portals)
            if (e.spec.id == id)
                return &e.spec;
        return nullptr;
    }

    WingPortalSpec const* WingPortals::SpecOfObject(ObjectGuid go) const
    {
        if (go.IsEmpty())
            return nullptr;
        for (Entry const& e : _portals)
            if (e.object == go)
                return &e.spec;
        return nullptr;
    }

    uint32 WingPortals::Use(Player* user, GameObject const* go)
    {
        if (!user || !go)
            return 0;
        WingPortalSpec const* spec = SpecOfObject(go->GetGUID());
        if (!spec)
        {
            LOG_WARN(kLogCategory, "dungeon-kit portal use of an object no open portal owns entry={} user={}",
                go->GetEntry(), user->GetName());
            return 0;
        }
        return Travel(user, go, *spec);
    }

    uint32 WingPortals::UseById(Player* user, uint32 id)
    {
        WingPortalSpec const* spec = SpecOf(id);
        if (!user || !spec)
            return 0;
        GameObject const* go = nullptr;
        if (Map* map = user->FindMap())
            if (ObjectGuid const object = ObjectOf(id))
                go = map->GetGameObject(object);
        return Travel(user, go, *spec);
    }

    uint32 WingPortals::Travel(Player* user, WorldObject const* portal, WingPortalSpec const& spec)
    {
        uint64 const now = NowMs();
        uint64& last = _lastUseMs[user->GetGUID().GetRawValue()];
        if (last && now < last + kPortalUseCooldownMs)
            return 0;
        last = now;
        return PortalTravel(user, portal, spec);
    }

    uint32 PortalTravel(Player* user, WorldObject const* portal, WingPortalSpec const& spec)
    {
        if (!user)
            return 0;
        WorldObject const* from = portal && portal->IsInMap(user) ? portal : user;

        TravelerFacts self;
        self.isUser = true;
        self.sameMap = user->IsInWorld();
        self.alive = user->IsAlive();
        self.inCombat = user->IsInCombat();
        self.busy = Busy(user);
        TravelVerdict const userVerdict = JudgeTraveler(self, spec.escortYd, spec.userInCombatGoes);
        if (userVerdict != TravelVerdict::Go)
        {
            if (userVerdict == TravelVerdict::InCombat)
                Notify(user, "The portal will not take you while you are in combat.");
            LOG_INFO(kLogCategory, "{} portal {} use refused user={} why={}", spec.dungeon, spec.name,
                user->GetName(), TravelVerdictName(userVerdict));
            return 0;
        }

        std::vector<Player*> travelers{ user };
        std::string left;
        if (Group* group = user->GetGroup())
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
            {
                Player* member = ref->GetSource();
                if (!member || member == user)
                    continue;
                TravelerFacts f;
                f.sameMap = member->IsInWorld() && member->GetMap() == user->GetMap();
                f.alive = member->IsAlive();
                f.inCombat = member->IsInCombat();
                f.busy = Busy(member);
                f.distYd = f.sameMap ? from->GetExactDist(member) : 0.f;
                TravelVerdict const v = JudgeTraveler(f, spec.escortYd);
                if (v == TravelVerdict::Go)
                    travelers.push_back(member);
                else if (v != TravelVerdict::OtherMap)
                    left += Acore::StringFormat("{}{}:{}", left.empty() ? "" : ",", member->GetName(),
                        TravelVerdictName(v));
            }

        Position const& to = spec.destination;
        for (Player* p : travelers)
        {
            if (spec.travelSpell)
                p->CastSpell(p, spec.travelSpell, true);
            p->NearTeleportTo(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), to.GetOrientation(), false,
                false, true);
        }
        LOG_INFO(kLogCategory, "{} portal {} use user={} moved={} left=[{}] to=({:.1f}, {:.1f}, {:.1f})", spec.dungeon,
            spec.name, user->GetName(), travelers.size(), left, to.GetPositionX(), to.GetPositionY(),
            to.GetPositionZ());
        return static_cast<uint32>(travelers.size());
    }

    bool WingPortalAI::GossipHello(Player* player, bool /*reportUse*/)
    {
        WingPortalHost* host = dynamic_cast<WingPortalHost*>(me->GetInstanceScript());
        if (!host)
        {
            LOG_WARN(kLogCategory, "dungeon-kit portal entry={} has no WingPortalHost instance (map {})",
                me->GetEntry(), me->GetMapId());
            return true;
        }
        host->GetWingPortals().Use(player, me);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SealedArena
    // ----------------------------------------------------------------------------------------------------------------

    GameObject* SealedArena::Door(Creature* boss) const
    {
        if (!boss)
            return nullptr;
        if (!_spec.door.IsEmpty())
            return boss->GetMap()->GetGameObject(_spec.door);
        if (_spec.doorEntry)
            return boss->FindNearestGameObject(_spec.doorEntry, _spec.doorSearchYd);
        return nullptr;
    }

    void SealedArena::Engage(Creature* boss)
    {
        if (!boss || !_clock.IsOpen())
            return;
        _clock.Engage(_spec.delayMs);
        _holdMs = 0;
        LogMechanic(_spec.dungeon, _spec.boss, "seal-pull", Acore::StringFormat("closes-in={}ms", _spec.delayMs));
    }

    bool SealedArena::Update(Creature* boss, uint32 diff)
    {
        if (!boss || _clock.IsOpen())
            return false;
        if (_clock.Update(diff))
        {
            if (GameObject* door = Door(boss))
                door->SetGoState(GO_STATE_READY);
            if (_spec.sealEntry && _seal.IsEmpty())
            {
                // Owned by the boss (GO_SUMMON_TIMED_OR_CORPSE_DESPAWN): if he leaves the world without a Release (a
                // GM delete, a despawn) the seal goes with him (Unit::RemoveFromWorld -> RemoveAllGameObjects) instead
                // of blocking the doorway until the instance resets (R-1-LIB n3).
                float const o = _spec.sealAt.GetOrientation();
                if (GameObject* seal = boss->SummonGameObject(_spec.sealEntry, _spec.sealAt.GetPositionX(),
                    _spec.sealAt.GetPositionY(), _spec.sealAt.GetPositionZ(), o, 0.f, 0.f, std::sin(o * 0.5f),
                    std::cos(o * 0.5f), 0, false, GO_SUMMON_TIMED_OR_CORPSE_DESPAWN))
                    _seal = seal->GetGUID();
            }
            if (_spec.emoteGroup && boss->AI())
                boss->AI()->Talk(*_spec.emoteGroup);
            uint32 const moved = PullIn(boss);
            LogMechanic(_spec.dungeon, _spec.boss, "seal-close",
                Acore::StringFormat("door={} seal={} pulled-in={}", Door(boss) ? 1 : 0, _seal.IsEmpty() ? 0 : 1,
                    moved));
            return true;
        }
        if (!_clock.IsSealed())
            return false;
        _holdMs += diff;
        if (_holdMs < kSealHoldMs)
            return false;
        _holdMs = 0;
        if (GameObject* door = Door(boss))
            if (door->GetGoState() != GO_STATE_READY)
            {
                door->SetGoState(GO_STATE_READY);
                LogMechanic(_spec.dungeon, _spec.boss, "seal-hold", "door opened while sealed: shut again");
            }
        return false;
    }

    uint32 SealedArena::PullIn(Creature* boss)
    {
        if (!boss)
            return 0;
        uint32 moved = 0;
        std::string names;
        for (auto const& ref : boss->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsInWorld())
                continue;
            StragglerFacts f;
            f.alive = player->IsAlive();
            f.inArena = _spec.arena.Contains(PlaneOf(player), player->GetPositionZ());
            f.sameWing = !_spec.sameWing || _spec.sameWing(boss, player);
            f.busy = Busy(player);
            f.gameMaster = player->IsGameMaster();
            f.distYd = player->GetExactDist(&_spec.entry);
            if (!IsStraggler(f, _spec.pullInYd))
                continue;
            player->NearTeleportTo(_spec.entry.GetPositionX(), _spec.entry.GetPositionY(), _spec.entry.GetPositionZ(),
                _spec.entry.GetOrientation(), false, false, true);
            ++moved;
            names += Acore::StringFormat("{}{}", names.empty() ? "" : ",", player->GetName());
        }
        if (moved)
            LogMechanic(_spec.dungeon, _spec.boss, "seal-pull-in", Acore::StringFormat("moved=[{}]", names));
        return moved;
    }

    void SealedArena::Release(Creature* boss, char const* why)
    {
        if (!_clock.Release())
            return;
        if (boss)
        {
            if (GameObject* door = Door(boss))
                door->SetGoState(GO_STATE_ACTIVE);
            if (!_seal.IsEmpty())
                if (GameObject* seal = boss->GetMap()->GetGameObject(_seal))
                    seal->DespawnOrUnsummon();
        }
        _seal.Clear();
        _holdMs = 0;
        LogMechanic(_spec.dungeon, _spec.boss, "seal-open", Acore::StringFormat("why={}", why ? why : "?"));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter credit
    // ----------------------------------------------------------------------------------------------------------------

    bool CreditEncounterBySpell(Map* map, uint32 spellId, Unit* source, char const* dungeon, char const* encounter,
        bool bind)
    {
        if (!map || !spellId)
            return false;
        if (!source)
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    source = player;
                    break;
                }
        if (!source)
        {
            LOG_WARN(kLogCategory, "{} {} credit-spell {} refused: no unit in the instance to credit from",
                dungeon, encounter, spellId);
            return false;
        }
        map->UpdateEncounterState(ENCOUNTER_CREDIT_CAST_SPELL, spellId, source);
        bool bound = false;
        if (bind && map->IsDungeon() && map->IsRaidOrHeroicDungeon())
            if (InstanceMap* instance = map->ToInstanceMap())
            {
                instance->PermBindAllPlayers();
                bound = true;
            }
        LogMechanic(dungeon, encounter, "credit-spell",
            Acore::StringFormat("spell={} source={} bound={}", spellId, source->GetName(), bound ? 1 : 0));
        return true;
    }
}
