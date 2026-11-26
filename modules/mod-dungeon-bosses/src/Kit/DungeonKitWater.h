/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F41; SP GZ2-GZ8, GZ13, GZ15,
 * GZ22, GZ23; user D7): one owner of N water sheets that freeze, thaw and grow. The pure rules are
 * DungeonKitWaterLogic.h (WaterSheets, DiscFor); this is the engine half.
 *
 *   WaterField   per sheet: a persistent telegraph-only registry Zone while it is water and `avoid` (the bots stay
 *                out; frozen sheets are not registered, GZ2), re-registered on every grow, dropped on a freeze and back
 *                on the thaw; a disc creature wearing the state's display at radius / 4.8 (water 90830, ice 90831),
 *                changed in one SetDisplayId(display, scale) call; RegisterDischarge registers every water sheet as
 *                a one-shot Zone for the cast (GZ3, 3 s) and swaps the discs to the storm display (90832) until it
 *                resolves; a sheet that freezes during the cast loses its Discharge zone. The thaw clock runs in
 *                Update.
 *
 * Owned by one AI (Gahz'rilla's, or the instance's helper before he rises). Update from UpdateAI (in combat), Clear
 * from Reset, JustDied and EnterEvadeMode (RB-1: Clear removes every zone, disc and sheet). The registry also ends the
 * zones of an owner that dies, evades or despawns; Clear then only removes the discs.
 *
 *     DungeonKit::WaterField _water;
 *     _water.Configure({ .discEntry = NPC_DISC_STALKER, .looks = { 90830, 90831, 90832 }, .dungeon = "zf",
 *         .boss = "gahzrilla", .name = "water" });
 *     uint32 id = _water.Add(me, spot, 8.f);                         // Spill the Pool's puddle
 *     FreezeResult r = _water.FreezeAt(me, target->GetPosition());   // Icicle; r.Meltwater(): add one under him
 *     _water.RegisterDischarge(me, 3000ms, [](BossMechanics::MechanicRef& z) { z.Damage(50.f).School(3); });
 *     ... on the Discharge's resolve: _water.GrowWater(me, heroic ? 3.f : 2.f);
 *     UpdateAI: for (SheetChange const& c : _water.Update(me, diff)) ...;  Reset: _water.Clear(me);
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WATER_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WATER_H

#include "BossMechanics.h"
#include "DungeonKitWaterLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

class Creature;
class WorldObject;

namespace DungeonKit
{
    struct WaterFieldSpec
    {
        uint32 discEntry = 0;               // the disc's creature (an invisible stalker, CDI 11686); 0: no discs
        DiscLooks looks;                    // the displays (water 0: no discs either)
        bool drawAvoid = false;             // false: the avoid zones carry NoTelegraph (the disc is the look); true:
                                            // the BM marker draws them (the fallback without discs, section 7 #47 B)
        std::optional<BossMechanics::Color> color;
        uint32 tag = 0;                     // the avoid zones' tag
        // Extra registry options on every avoid zone (Within, ZTolerance ...). Capture guids only.
        std::function<void(BossMechanics::MechanicRef&)> configureAvoid;
        char const* dungeon = "kit";        // LogMechanic: "<dungeon> <boss> <name>-add|-freeze|-thaw|-grow|..."
        char const* boss = "water";
        char const* name = "water";
    };

    class WaterField
    {
    public:
        static Milliseconds constexpr kWholeFight{ 4 * 3600 * 1000 };  // an avoid zone's registry life

        void Configure(WaterFieldSpec spec) { _spec = std::move(spec); }
        WaterFieldSpec const& Spec() const { return _spec; }

        // A circle sheet at `at` (its z is the floor height the caller found). Returns its id (0: refused: no owner,
        // radius <= 0). `state` Ice adds a floe (rules.thawTo Gone for one that melts away).
        uint32 Add(Creature* owner, Position const& at, float radius, SheetRules const& rules = {},
            SheetState state = SheetState::Water);
        // A strip (the pool as a Line, `halfWidth` either side of from -> to). No disc.
        uint32 AddStrip(Creature* owner, Position const& from, Position const& to, float halfWidth,
            SheetRules const& rules = {});

        // Icicle: the sheet `at` stands in. Freeze Solid: every sheet within `yd`. See FreezeResult for Meltwater and
        // the pool.
        FreezeResult FreezeAt(Creature* owner, Position const& at);
        FreezeResult FreezeWithin(Creature* owner, Position const& at, float yd);
        bool Freeze(Creature* owner, uint32 id);
        // Now, not on the clock (a thawTo Gone sheet goes).
        bool Thaw(Creature* owner, uint32 id);

        // Rising Water: every water sheet that grows (frozen keep their radius). Returns the ids that grew.
        std::vector<uint32> GrowWater(Creature* owner, float deltaYd);
        bool Grow(Creature* owner, uint32 id, float deltaYd);
        bool SetRadius(Creature* owner, uint32 id, float radiusYd);

        // GZ3: every water sheet with rules.discharge as a one-shot Zone resolving in `warn` (`configure` sets the
        // damage, school, rider, OnHit ...; none: telegraph-only), and the storm disc on each until then. A Discharge
        // still pending is canceled first. Returns the handles.
        std::vector<BossMechanics::MechanicHandle> RegisterDischarge(Creature* owner, Milliseconds warn,
            std::function<void(BossMechanics::MechanicRef&)> const& configure = {});
        // An interrupted cast (RB-18): its zones go, the discs go back.
        void CancelDischarge(Creature* owner);
        bool DischargePending() const { return _stormLeftMs > 0; }

        // The thaw clock and the end of the storm tell. Returns the sheets that thawed or went.
        std::vector<SheetChange> Update(Creature* owner, uint32 diff);

        void Remove(Creature* owner, uint32 id);
        void Clear(Creature* owner);

        // Queries (a unit's plane and height).
        bool IsWater(WorldObject const* o) const;
        bool IsWater(Position const& p) const;
        bool IsIce(Position const& p) const;
        std::optional<uint32> WaterSheetAt(Position const& p) const;
        bool InWaterSheet(uint32 id, WorldObject const* o) const;
        WaterSheet const* Find(uint32 id) const { return _sheets.Find(id); }
        std::vector<WaterSheet> const& All() const { return _sheets.All(); }
        std::size_t Count() const { return _sheets.Count(); }
        WaterSheets const& Sheets() const { return _sheets; }

        // The avoid zone of sheet `id` (empty while ice, or with avoid off): a DropSpotRule's preferred zone.
        BossMechanics::MechanicHandle AvoidZoneOf(uint32 id) const;
        // The disc creature of sheet `id` (empty: none).
        ObjectGuid DiscOf(uint32 id) const;

    private:
        struct Look
        {
            BossMechanics::MechanicHandle avoid;
            float avoidRadius = 0.f;
            BossMechanics::MechanicHandle discharge;
            ObjectGuid disc;
            DiscLook worn;
        };

        // Brings the sheet's zone and disc in line with its state and radius.
        void Refresh(Creature* owner, uint32 id);
        void Drop(Creature* owner, uint32 id);
        bool RegisterAvoid(Creature* owner, WaterSheet const& s, Look& look);
        void Log(char const* what, std::string const& detail) const;

        WaterFieldSpec _spec;
        WaterSheets _sheets;
        std::unordered_map<uint32, Look> _looks;
        uint32 _stormLeftMs = 0;
    };
}

#endif
