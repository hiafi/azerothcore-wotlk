/*
 * mod-dungeon-bosses, Gnomeregan D5: the ComboMachine's engine half (GnomereganMachines.h, handoff section 3.2 item 7,
 * section 7 #8 A). The contract is GnomereganMachines.h; the pure half (the frame's shapes, the contract's timing as
 * the kit's, the report rule) is CrowdPummelerLogic.h; under it all is the shared kit's DungeonKit::CalledCombination
 * (DungeonKitCombo.h, KT-G), wrapped, never forked.
 *
 * What the machine does with a ComboSpec:
 *   - SetFrame: the frame (origin and facing; the halves' reach, the near radius, the far donut's outer edge, the lane)
 *     for the next Call. `floor` becomes every real Zone's bot bounds (`.Within`): the bots plan their spots on it.
 *     The hits are not clipped to it (SP: the corridors are inside the hooks for their first 10 yd).
 *   - Call(chain): the whole chain registered at once for the bots (one hidden real Zone per shape, the tank in every
 *     hit at the same percent, Weakened); the players see each punch's call flash (outline, in order: callFlashMs
 *     each; drawAllAtOnce: every shape from the start, numbered through onNumber) and its live marker (markerMs, the
 *     fill). The owner says callEmoteGroup. Returns the last strike in ms (0: refused: running, empty, no owner).
 *   - Update: the kit's clock; then each punch's report (onPunch with the players it hit, kReportAfterMs after its
 *     strike), and the chain's end.
 *   - Landed: the punches of the running (or last) chain that hit a player (pets never count, KT-G Q7).
 *   - Clear: the kit's Stop (every shape, decoy and numeral still to come), the books; safe twice, owner gone.
 *
 * Beyond the contract (ComboExtras, for Crowd Pummeler and any caller that wants them): the resolve copies and tags
 * per shape (the combat log names the punch; the drill's tags), a rider on every hit, the call color, the shapes'
 * log names, and four hooks: onLive (a punch's live marker starts: the boss's pose bar), onStrike (the strike: the
 * punch emote), onHit (inside the registry's resolve, per player hit: knockbacks; never register anything there,
 * rule 11) and onEnd. Every hook gets the owner; capture guids only (the onHit closure lives in the registry).
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_CROWD_PUMMELER_MACHINE_H
#define MOD_DUNGEON_BOSSES_GNOMER_CROWD_PUMMELER_MACHINE_H

#include "CrowdPummelerLogic.h"
#include "GnomereganMachines.h"
#include "MechanicRegistry.h"
#include <array>
#include <functional>
#include <memory>
#include <optional>

class Creature;
class Player;

namespace GnomereganMachines
{
    struct ComboExtras
    {
        // By PunchShape: the resolve copy that deals the hit (0: the registry's own by `school`) and its registry tag
        // (0: none).
        std::array<uint32, kPunchShapeCount> spellIds{};
        std::array<uint32, kPunchShapeCount> tags{};
        std::array<char const*, kPunchShapeCount> names{ { "left", "right", "near", "far", "lane" } };
        uint8 school = 0;                       // SPELL_SCHOOL_NORMAL
        uint32 rider = 0;                       // cast on every unit a punch hits (a look)
        std::optional<BossMechanics::Color> callColor;
        std::optional<BossMechanics::Color> liveColor;
        // A punch's live marker starts (Sequential; AllAtOnce has none): `untilStrikeMs` to its strike.
        std::function<void(Creature* owner, uint32 index, Punch const& punch, uint32 untilStrikeMs)> onLive;
        // A punch strikes (the kit's strike, before the registry resolves it).
        std::function<void(Creature* owner, uint32 index, Punch const& punch)> onStrike;
        // Per player hit, inside the registry's resolve (the hit spell's AfterHit): knockbacks and the like only.
        std::function<void(Player* hit, PunchShape shape)> onHit;
        // The chain ended (every punch reported): its length and how many punches landed.
        std::function<void(Creature* owner, uint32 punches, uint32 landed)> onEnd;
    };

    // The contract's factory (GnomereganMachines.h) is this with no extras.
    std::unique_ptr<ComboMachine> MakeComboMachine(MachineOwner const& owner, ComboSpec spec, ComboExtras extras);
}

#endif
