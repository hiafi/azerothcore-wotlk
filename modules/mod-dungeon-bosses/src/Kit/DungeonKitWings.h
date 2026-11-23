/*
 * mod-dungeon-bosses, the shared dungeon kit (Scarlet Monastery WP-KT-SM, handoff section 3.11 #2 to #4): a dungeon of
 * several wings on one map. The pure rules are DungeonKitWingLogic.h (JudgeTraveler, ClearOfTriggers, SealClock,
 * IsStraggler, CreditLatch).
 *
 *   WingPortals            in-map wing portals (F30, section 7 #15), owned by the instance script: Open spawns a
 *                          portal object at its spot (on the end boss's DONE, and again on load from the saved slots;
 *                          idempotent), Update brings one back after its grid was unloaded, and a use (WingPortalAI)
 *                          teleports the user plus every group member on the map within escortYd of the portal who
 *                          is alive and out of combat to the destination (same map: a near teleport, pets along); one
 *                          log line per use
 *   PortalTravel           that use as a free function, for an instance that spawns its portals itself
 *   WingPortalHost         the interface the instance script implements so a portal object finds its WingPortals
 *   WingPortalAI           the portal object's AI (a dungeon registers it under its own script name)
 *   SealedArena            a boss room sealed shortly after the pull (section 7 #22): Engage at the pull; the door
 *                          (or a summoned seal object) shuts `delayMs` later with an emote, and at that moment every
 *                          living player outside the arena in the same wing within pullInYd of the entry spot is moved
 *                          to the entry spot; while sealed a door opened by hand is shut again; Release (death, reset,
 *                          evade) opens it
 *   CreditEncounterBySpell an encounter credit for a spell-credit row (creditType 1, F25: the council, the Last Stand;
 *                          the BRD 211066 precedent): Map::UpdateEncounterState with the spell, and on a heroic
 *                          dungeon or a raid the bind (InstanceMap::PermBindAllPlayers): only a killed creature with
 *                          INSTANCE_BIND binds by itself, so the bind follows the credit carrier here
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WINGS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WINGS_H

#include "DungeonKitArena.h"
#include "DungeonKitWingLogic.h"
#include "GameObjectAI.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

class Creature;
class GameObject;
class Map;
class Player;
class Unit;
class WorldObject;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Wing portals
    // ----------------------------------------------------------------------------------------------------------------

    struct WingPortalSpec
    {
        uint32 id = 0;                          // the dungeon's portal number (1: P1 ...); one open portal per id
        std::string name = "portal";            // log and messages ("P1", "the Library")
        uint32 goEntry = 0;                     // the portal object (a GOOBER whose ScriptName runs WingPortalAI)
        Position spot;                          // where it stands (orientation: its facing)
        Position destination;                   // where travelers land (the next wing's start)
        float escortYd = kPortalEscortYd;       // group members this close to the portal object go along
        bool userInCombatGoes = false;          // the user may travel while in combat (escorts never do)
        uint32 travelSpell = 0;                 // cast triggered on each traveler before the jump (a look; 0: none)
        std::string dungeon = "kit";            // log: "<dungeon> portal <name> use|open|close ..."
    };

    class WingPortals
    {
    public:
        // Spawns spec.goEntry at spec.spot (no-op when portal spec.id is already open and its object is there; a
        // changed spec for an open id replaces it: P1 -> P1h). The map must be the instance's. False when the
        // object could not be spawned (the portal still counts as open, and Update keeps trying).
        bool Open(Map* map, WingPortalSpec const& spec);
        void Close(Map* map, uint32 id);
        void CloseAll(Map* map);

        // Every 2 s: an open portal whose object is gone (its grid was unloaded) is spawned again once its grid is
        // loaded. Call it from the instance's Update.
        void Update(Map* map, uint32 diff);

        bool IsOpen(uint32 id) const;
        std::vector<uint32> OpenIds() const;
        ObjectGuid ObjectOf(uint32 id) const;
        WingPortalSpec const* SpecOf(uint32 id) const;
        WingPortalSpec const* SpecOfObject(ObjectGuid go) const;

        // A use of the portal object `go` by `user`: the travelers (JudgeTraveler) jump to the destination. Returns
        // how many players moved (0: refused; the user is told why).
        uint32 Use(Player* user, GameObject const* go);
        // The same for portal `id` without its object (`.dbtest` portal tests).
        uint32 UseById(Player* user, uint32 id);

    private:
        struct Entry
        {
            WingPortalSpec spec;
            ObjectGuid object;
        };

        GameObject* Spawn(Map* map, Entry& e);
        uint32 Travel(Player* user, WorldObject const* portal, WingPortalSpec const& spec);

        std::vector<Entry> _portals;
        std::unordered_map<uint64, uint64> _lastUseMs;     // user guid -> game time ms (one use per second)
        uint32 _checkMs = 0;
    };

    // One use of a portal, without WingPortals (an instance that spawns its portal objects itself): `user` and every
    // group member on the map within spec.escortYd of `portal` (null: of the user) who is alive, out of combat and free
    // to move (JudgeTraveler) are cast spec.travelSpell on and near-teleported to spec.destination with their pets. A
    // user in combat is refused with a notification unless spec.userInCombatGoes. One log line
    // "<dungeon> portal <name> use user=.. moved=N left=[name:why,..] to=(x, y, z)". Returns how many players moved
    // (0: refused). No use cooldown here (WingPortals::Use keeps one second per user).
    uint32 PortalTravel(Player* user, WorldObject const* portal, WingPortalSpec const& spec);

    // The instance script implements this (class instance_x : public InstanceScript, public WingPortalHost), so the
    // portal object's AI reaches the instance's WingPortals through GetInstanceScript().
    class WingPortalHost
    {
    public:
        virtual ~WingPortalHost() = default;
        virtual WingPortals& GetWingPortals() = 0;
    };

    // The portal object's AI: a use (the click) asks the instance's WingPortals to travel. A dungeon registers it under
    // its object's ScriptName:
    //
    //     struct go_sm_wing_portal : public DungeonKit::WingPortalAI { using WingPortalAI::WingPortalAI; };
    //     RegisterDungeonReworkGameObjectAI(go_sm_wing_portal, ScarletMonasteryRework::kInstanceScriptName);
    struct WingPortalAI : public GameObjectAI
    {
        explicit WingPortalAI(GameObject* go) : GameObjectAI(go) { }

        bool GossipHello(Player* player, bool reportUse) override;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Sealed arena
    // ----------------------------------------------------------------------------------------------------------------

    struct SealedArenaSpec
    {
        Arena arena;                            // inside: never pulled in (the boss's arena, or the room)
        Position entry;                         // where stragglers land: just inside the door
        uint32 delayMs = kSealDelayMs;          // the pull -> the close
        float pullInYd = kSealPullInYd;         // stragglers this close to `entry` (3D) are moved in
        // The dungeon's wing test (a straggler must be in the boss's wing; empty: any). Called with the boss and a
        // player.
        std::function<bool(Creature const* boss, Player const* player)> sameWing;
        std::optional<uint8> emoteGroup;        // the boss says this text group at the close
        // The door: a guid (from the instance), else the nearest object of doorEntry within doorSearchYd of the boss.
        // The door shuts at the close (GO_STATE_READY), is shut again if opened while sealed, and opens on Release.
        ObjectGuid door;
        uint32 doorEntry = 0;
        float doorSearchYd = 100.f;
        // Or a seal object summoned at the close at sealAt (despawned on Release; 0: none).
        uint32 sealEntry = 0;
        Position sealAt;
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> seal-close|seal-open"
        char const* boss = "arena";
    };

    // Owned by the boss AI:
    //
    //     DungeonKit::SealedArena _seal{ MySealSpec() };
    //     void JustEngagedWith(Unit* who) override { BossAI::JustEngagedWith(who); _seal.Engage(me); }
    //     void UpdateAI(uint32 diff) override { _seal.Update(me, diff); if (!UpdateVictim()) return; ... }
    //     void Reset() / JustDied() / EnterEvadeMode(): _seal.Release(me, "reset" / "death" / "evade");
    //
    // The door must not also be in the instance's DoorData (a ROOM door there shuts at the pull, a PASSAGE door
    // before it): the seal owns it.
    class SealedArena
    {
    public:
        SealedArena() = default;
        explicit SealedArena(SealedArenaSpec spec) : _spec(std::move(spec)) { }

        void Configure(SealedArenaSpec spec) { _spec = std::move(spec); }
        // An instance-held door guid (set before Engage, or any time).
        void SetDoor(ObjectGuid door) { _spec.door = door; }

        // The pull: the close is delayMs away.
        void Engage(Creature* boss);
        // Counts down; at the close shuts the door, says the emote and moves the stragglers in; while sealed keeps the
        // door shut (every second). True on the tick it closed. Call it every tick, before UpdateVictim.
        bool Update(Creature* boss, uint32 diff);
        // Opens the door, removes the seal object. Safe to call any time (a no-op when open).
        void Release(Creature* boss, char const* why);

        bool IsSealed() const { return _clock.IsSealed(); }
        bool IsClosing() const { return _clock.IsClosing(); }
        SealClock const& Clock() const { return _clock; }
        SealedArenaSpec const& Spec() const { return _spec; }

        // The stragglers' move, now (the close calls it; `.dbtest` may too). Returns how many moved.
        uint32 PullIn(Creature* boss);

    private:
        GameObject* Door(Creature* boss) const;

        SealedArenaSpec _spec;
        SealClock _clock;
        ObjectGuid _seal;
        uint32 _holdMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter credit
    // ----------------------------------------------------------------------------------------------------------------

    // Credits the encounter whose instance_encounters row is a spell credit (creditType 1) on `spellId`:
    // Map::UpdateEncounterState(ENCOUNTER_CREDIT_CAST_SPELL, spellId, source) (the completed-encounter mask, the
    // Finder's end of section when the row is a last encounter), then on a heroic dungeon or a raid
    // InstanceMap::PermBindAllPlayers (with `bind`). `source` gives the instance for the mask: a unit in the instance
    // (the boss); null: the first player on the map. The spell must exist (spell_dbc), or the core skips the row at
    // load. Nothing is cast. Returns false with no map, no spell id, or no unit to stand as the source.
    bool CreditEncounterBySpell(Map* map, uint32 spellId, Unit* source, char const* dungeon, char const* encounter,
        bool bind = true);
}

#endif
