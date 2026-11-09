/*
 * mod-dungeon-bosses, the shared dungeon kit: lethal walls and relic dispensers (Stratholme WP-KT-2,
 * .agents/plans/stratholme-build/stratholme-build.HANDOFF.md section 3.11 #15 and #26). The pure rules are
 * DungeonKitWallLogic.h; the strike's damage is spell_dungeon_lethal_strike (DungeonKitSpells.cpp).
 *
 *   LethalWall          an arena wall (The Unforgiven's Cordon, Galford's Pyre and north wall): a telegraph-only
 *                       persistent registry Line, `.Lethal()` (mod-boss-mechanics X4: bots never plan a way across),
 *                       armed `armAfter` after it registers; every tick the kit strikes each player and pet inside it,
 *                       and each one that crossed its line since the last tick (a blink, a charge, a mount)
 *   LethalWalls         the walls one boss AI raised: Add, Clear (Reset / JustDied / EnterEvadeMode)
 *   RelicDispenserAI    a GameObjectAI base: a click gives one copy of an item to the user and every member of the
 *                       user's group on the same map who lacks it (bots too); Dispense does the same from any script
 *
 * Lambdas kept by the registry capture the map and guids only, never a Unit*.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WALLS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WALLS_H

#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitWallLogic.h"
#include "Duration.h"
#include "GameObjectAI.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class GameObject;
class Player;
class Unit;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // LethalWall (#15)
    // ----------------------------------------------------------------------------------------------------------------

    struct LethalWallSpec
    {
        Position from;                                  // the wall's ends on the floor (z: the floor height there)
        Position to;
        float width = kWallDefaultWidthYd;              // the hitbox and the marker: the whole width kills
        // The strike (a spell bound to spell_dungeon_lethal_strike: damage equal to the victim's maximum health).
        // 0: Unit::Kill, a fallback for a test before the spell exists.
        uint32 killSpell = 0;
        Milliseconds armAfter{ kWallArmMs };            // the warning: drawn and seen by bots at once, kills from then
        Milliseconds lifetime{ 4 * 3600 * 1000 };       // the whole fight (it ends with the encounter or Clear)
        Milliseconds tick{ kWallTickMs };
        float zBand = 6.f;                              // the crossing check's floor band round the wall's height
        float zTolerance = 0.f;                         // > 0: the registry hitbox's ZTolerance (0: its default)
        bool pets = true;                               // pets, guardians and charmed units die too (ST: "Pets too")
        bool crossings = true;                          // also strike a unit whose step went across between ticks
        std::optional<BossMechanics::Color> color;      // default: the encounter's get-out color
        uint32 tag = 0;
        // Units that deliver the strike for the look (the footmen of the rank, a Pyre stalker): the nearest one to
        // the victim casts it with the owner as the original caster (credit, ledger). Empty or none present: the
        // owner casts it.
        std::vector<ObjectGuid> strikers;
        char const* dungeon = "kit";                    // LogMechanic: "<dungeon> <boss> lethal-wall ..."
        char const* boss = "wall";
        std::function<void(Unit* victim)> onStrike;     // after each strike (capture guids only)
    };

    // Registers (and, at the end of the calling statement, commits) one wall: a telegraph-only persistent Line from
    // `spec.from` to `spec.to` of `spec.width`, warn `spec.armAfter`, ticking every `spec.tick`, NoFillTimer, Lethal,
    // with no Eligible and no TankExempt (every bot keeps out). Further options may be chained on the returned ref (a
    // color, Within); do not replace its OnResolve, and do not add Damage, Weakened or OnHit (the strike is the
    // kit's). Returns an invalid ref when the registry refuses it (no owner, no map, width <= 0).
    BossMechanics::MechanicRef LethalWall(Unit* owner, LethalWallSpec const& spec);
    // The handoff's short form (section 3.11 #15).
    BossMechanics::MechanicRef LethalWall(Unit* owner, Position const& from, Position const& to, float width,
        uint32 killSpell, Milliseconds armAfter = Milliseconds(kWallArmMs));

    // The pure line of a spec (for host-side placement checks: KeepsClear, CheckPlacement).
    inline WallLine WallLineOf(LethalWallSpec const& spec)
    {
        return { { spec.from.GetPositionX(), spec.from.GetPositionY() },
            { spec.to.GetPositionX(), spec.to.GetPositionY() }, spec.width };
    }

    // The walls one boss AI raised. Raise them at the pull (after the pull grip, so armAfter counts from it) and
    // Clear them from Reset / JustDied / EnterEvadeMode: the encounter's end cancels them too (the registry ends an
    // owner's mechanics on death, evade and despawn), Clear makes it explicit and immediate.
    //
    //     DungeonKit::LethalWalls _cordon;
    //     void JustEngagedWith(Unit* who) override
    //     {
    //         ...; _guard.OnEngage(me);                           // the pull grip
    //         for (LethalWallSpec const& w : CordonWalls())       // armAfter 2 s: section 10
    //             _cordon.Add(me, w);
    //     }
    //     void JustDied(Unit*) override { _cordon.Clear(me); ... }
    class LethalWalls
    {
    public:
        // The wall's handle (invalid: refused).
        BossMechanics::MechanicHandle Add(Unit* owner, LethalWallSpec const& spec);
        void Clear(Unit* owner);

        // A unit stands inside any of the walls now (the registry's hitbox).
        bool Contains(Unit* owner, Unit const* who) const;
        std::vector<BossMechanics::MechanicHandle> const& Handles() const { return _walls; }
        std::size_t Count() const { return _walls.size(); }

    private:
        std::vector<BossMechanics::MechanicHandle> _walls;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RelicDispenser (#26)
    // ----------------------------------------------------------------------------------------------------------------

    struct DispenseResult
    {
        std::vector<ObjectGuid> given;      // each got one copy
        uint32 had = 0;                     // on the map, already carrying one
        uint32 away = 0;                    // in the group, not on the map
        uint32 noRoom = 0;                  // lacked one but had no bag space (told so by Player::AddItem)
    };

    // One copy of `itemId` to `user` and every member of `user`'s group who is on `where`'s map (this instance) and
    // carries none (bags or bank). Bots are group members like any player. Logs one line in module.dungeonbosses.
    DispenseResult Dispense(WorldObject const* where, Player* user, uint32 itemId, char const* dungeon = "kit");

    // A dispenser gameobject's AI: derive one per relic (the item in the constructor) and register it under the
    // gameobject's ScriptName with RegisterDungeonReworkGameObjectAI. The gameobject should be a GOOBER (type 10)
    // with no lock, spell, loot or despawn: the click is handled here and the object stays, so a member who joins
    // late or lost a copy clicks again. Override CanDispense to refuse (a closed hard mode, a fight in progress),
    // OnDispensed for a line or an emote.
    //
    //     struct go_st_scarlet_standard : DungeonKit::RelicDispenserAI
    //     {
    //         explicit go_st_scarlet_standard(GameObject* go)
    //             : RelicDispenserAI(go, ITEM_ST_SCARLET_STANDARD, kLogDungeon) { }
    //     };
    //     RegisterDungeonReworkGameObjectAI(go_st_scarlet_standard, StratholmeRework::kInstanceScriptName);
    struct RelicDispenserAI : public GameObjectAI
    {
        RelicDispenserAI(GameObject* go, uint32 itemId, char const* dungeon = "kit");

        bool GossipHello(Player* player, bool reportUse) override;

        // False: the click does nothing (the default allows every click).
        virtual bool CanDispense(Player* /*user*/) { return true; }
        // After a click that was allowed (result.given may be empty: everyone had one).
        virtual void OnDispensed(Player* /*user*/, DispenseResult const& /*result*/) { }

        uint32 ItemId() const { return _itemId; }

    protected:
        uint32 _itemId;
        char const* _dungeon;
    };
}

#endif
