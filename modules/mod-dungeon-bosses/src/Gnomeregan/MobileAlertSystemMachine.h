/*
 * mod-dungeon-bosses, Gnomeregan D4: the LightsMachine's engine half (GnomereganMachines.h, handoff section 3.2 item 7,
 * section 7 #8 A), wrapping KT-G's DungeonKit::TurningLights (src/Kit/DungeonKitLights.h). The pure half (the light
 * plans, the speed, the reversal roll) is MobileAlertSystemLogic.h.
 *
 * The contract's factory (GnomereganMachines.h MakeLightsMachine) builds it with the default extras below; the
 * Mobile Alert System and anyone who needs more (a registry tag, a dim warning on the turning lights, who the cones may
 * spot, how a player was spotted) calls the extended factory here. The hard mode (D6Hb, MT23) can use either.
 *
 *   Sweep    (normal Alert System) nothing until Sweep(target): one cone locks on the target dim for dimMs, then
 *            sweeps sweepDeg clockwise over sweepMs and goes dark; the swept floor is drawn at once (the bots' sector).
 *            Refused while a sweep runs. Start() arms the extra rule (alsoSpotted) between sweeps.
 *   Turning  (heroic Alert System, the hard mode) Start(): `cones` cones evenly spaced from the anchor's facing (or
 *            extras.startBearing), dim for extras.litAfterMs, then always lit, turning; +speedUpPctPerSpotted on every
 *            Spotted (additive on the base, no cap); a reversal every reverseMinMs to reverseMaxMs with a stop of
 *            reverseStopMs and the owner's reverseEmoteGroup.
 *
 * Spotted: a player inside a lit cone (the kit's judge, every tick, only players on `floor` when it is set, plus
 * extras.eligible), or for whom spec.alsoSpotted answers true (judged every extras.alsoEveryMs while started), at most
 * once per latchMs per player across every source (one latch for the cones and the extra rule: KT-G Q2). The machine
 * then speeds the lights up (Turning) and calls extras.onSpottedBy (else spec.onSpotted). One INFO line per firing:
 * "gnomer-build <logKey> lights-<what> ..." (the kit's lines) and "gnomer-build <logKey> lights spotted ..." (ours).
 *
 * Ownership (the contract's rules): the owner is kept as a guid and resolved on its map every call; Clear() stops the
 * lights (cones, look ahead, stalkers: despawned through the map when the owner is gone), resets the latch, the counts
 * and the speed; it is safe twice. Callbacks run inside Update (never inside a registry callback) and capture guids.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_MOBILE_ALERT_SYSTEM_MACHINE_H
#define MOD_DUNGEON_BOSSES_GNOMER_MOBILE_ALERT_SYSTEM_MACHINE_H

#include "GnomereganMachines.h"
#include "MechanicRegistry.h"
#include "MobileAlertSystemLogic.h"
#include <functional>
#include <memory>
#include <optional>

namespace GnomereganMachines
{
    // How a player was spotted.
    enum class SpotSource : uint8
    {
        Light,      // inside a lit cone
        Also,       // the spec's extra rule (the Alert System's cameras past 30 yd)
        Script,     // AlertLightsMachine::Spot (a `.dbtest`, a caller's own rule)
    };

    char const* SpotSourceName(SpotSource source);

    struct LightsExtras
    {
        uint32 tag = 0;                     // registry tag on the lit cones; the look ahead takes tag + 1 (0: none)
        uint32 litAfterMs = 0;              // Turning: the dim warning before the first light (the Alert System 3 s)
        int direction = -1;                 // Turning: the first direction (-1 clockwise, +1 counter-clockwise)
        std::optional<float> startBearing;  // Turning: light 0's first bearing (else the anchor's facing)
        uint32 stalkerEntry = GnomereganRework::NPC_LIGHT_STALKER;
        float zBand = 6.f;
        // The bots' bounds on every cone and look-ahead zone (default: the spec's floor, when it is set).
        std::optional<BossMechanics::SpotBounds> bounds;
        std::optional<BossMechanics::Color> color;
        // Who the cones may spot besides the floor rule (capture guids only).
        std::function<bool(Player*)> eligible;
        uint32 alsoEveryMs = 500;           // how often spec.alsoSpotted is judged
        // Every Spotted, with its source and the light (0xFF: none). When set, spec.onSpotted is not called.
        std::function<void(Player*, SpotSource, uint8 light)> onSpottedBy;
    };

    // The concrete machine's extra interface (the boss AI, `.dbtest` and the hard mode may use it).
    class AlertLightsMachine : public LightsMachine
    {
    public:
        // Spots `who` now through the shared latch (a `.dbtest`, a caller's own rule). True when it did.
        virtual bool Spot(Player* who, SpotSource source) = 0;
        // A light is up (Sweep: a sweep runs; Turning: started and not cleared) and lit (past its dim warning).
        virtual bool Active() const = 0;
        virtual bool Lit() const = 0;
        virtual float DegPerSec() const = 0;
        virtual uint32 Reversals() const = 0;
        virtual uint32 Sweeps() const = 0;
    };

    std::unique_ptr<AlertLightsMachine> MakeAlertLightsMachine(MachineOwner const& owner, LightsAnchor anchor,
        LightsSpec spec, LightsExtras extras);
}

#endif
