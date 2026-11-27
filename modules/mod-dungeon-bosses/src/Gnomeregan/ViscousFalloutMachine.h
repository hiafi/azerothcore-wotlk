/*
 * mod-dungeon-bosses, Gnomeregan D2: the DoseField machine's engine half (GnomereganMachines.h, handoff section 3.2
 * item 7, section 7 #8 A). The factory MakeDoseField is defined in ViscousFalloutMachine.cpp; the pure half (the dose
 * arithmetic, THE halving rule of STAGE-S0 Q10, the drain, Leaking and Meltdown crossings) is ViscousFalloutLogic.h
 * (GnomerFallout::DoseLedger), host-tested by tests/gnomer_fallout_test.cpp.
 *
 * What the machine does, for any owner (Viscous Fallout, or Thermaplugg's hard mode package, MT17-MT20):
 *   - keeps every player's dose (Add, Set, Halve, Dose, Carriers) and mirrors it as the stack count of
 *     DoseSpec::auraSpellId, cast by the owner (DungeonKit::AddStacks), on every change and again every second (rule
 *     25: a recalculation can reset it; the counter shows at most 255);
 *   - drains 1 per drainEveryMs while drains(player) says so (normal Fallout: out of every armed pool);
 *   - at capAt: onCap(player) (Fallout's Radiation Sickness), then the dose goes to 0;
 *   - at leakAt and up: onLeak(player, feet) every leakEveryMs (the first a full period after the crossing), the
 *     owner's leakEmoteGroup once per player per pull;
 *   - crossing meltdownAt: onMeltdown(player, true / false), the owner's meltdownEmoteGroup once per player per pull;
 *   - a dead player's dose goes to 0; a player who left the owner's map is forgotten (no callback: a caller keeping a
 *     shape per carrier checks Dose() against its threshold itself).
 * Callbacks run from Update only, never from inside Add / Set / Halve (which a registry OnHit may call: rule 11).
 * Clear() removes the aura from every known player on the owner's map and forgets everything; it never calls the
 * caller's callbacks (the caller undoes its own shapes). One INFO line per firing: "gnomer-build <logKey> dose <what>".
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_VISCOUS_FALLOUT_MACHINE_H
#define MOD_DUNGEON_BOSSES_GNOMER_VISCOUS_FALLOUT_MACHINE_H

#include "GnomereganMachines.h"
#include "ViscousFalloutLogic.h"

namespace GnomereganMachines
{
    // The pure rules of a DoseSpec (the numbers only; the callbacks stay in the spec).
    inline GnomerFallout::DoseRules DoseRulesOf(DoseSpec const& spec)
    {
        GnomerFallout::DoseRules rules;
        rules.capAt = spec.capAt;
        rules.drainEveryMs = spec.drainEveryMs;
        rules.leakAt = spec.leakAt;
        rules.leakEveryMs = spec.leakEveryMs;
        rules.meltdownAt = spec.meltdownAt;
        return rules;
    }
}

#endif
