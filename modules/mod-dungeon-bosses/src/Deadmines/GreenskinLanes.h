/*
 * mod-dungeon-bosses, Deadmines: the deck gun lanes (WP-B7), shared by Captain Greenskin (GS2-GS4) and Edwin
 * VanCleef's "The guns" (VC3, WP-B8). Engine glue; the pure parts (Greenskin::LaneVolley, kFireOnMyMark, the frame
 * math and the once-per-volley memory) are in GreenskinLogic.h. Defined in boss_captain_greenskin_rework.cpp.
 *
 * VanCleef (B8):
 *
 *     bool const heroic = DeadminesKit::IsHeroicMap(me);
 *     Greenskin::LaneVolley guns = Greenskin::kFireOnMyMark(heroic); // heroic: 4 across + 2 along, 2.5 s, burning
 *     if (!heroic)
 *         guns.across = 3;                                            // VC3 normal: 3 lanes across, 2 s
 *     guns.acrossTag = 3;                                             // VC3 is one mechanic id for all its parts
 *     guns.alongTag = 3;
 *     guns.cellTag = 3;
 *     GreenskinLanes::Volley const v = GreenskinLanes::Fire(me, guns);
 *     LOG_INFO("module.dungeonbosses", "dm-pilot vancleef the-guns lanes={} cells={}", v.Lanes(), v.cells.size());
 *     ...
 *     GreenskinLanes::ForgetOwner(me);                                // Reset / JustDied (optional bookkeeping)
 *
 * The lane hits use Greenskin's spells (205340 rail to rail, 205341 bow to stern, 205342 the burning crossings), so the
 * combat log names them "Fire on My Mark", "Crossfire" and "Burning Deck" for both bosses (DM VC "New spells":
 * Greenskin's lane spells reused). spell_dm_greenskin_lane_hit (registered by Greenskin's AddSC_) applies the
 * once-per-volley rule per owner, so it needs nothing from B8.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_GREENSKIN_LANES_H
#define MOD_DUNGEON_BOSSES_DEADMINES_GREENSKIN_LANES_H

#include "BossMechanics.h"
#include "GreenskinLogic.h"
#include <vector>

class Unit;

namespace GreenskinLanes
{
    // What one volley registered. Handles stay valid until the mechanic ends (store them, never the refs).
    struct Volley
    {
        uint32 laneSet = 0;                                     // mod-boss-mechanics lane set id (0: refused)
        std::vector<BossMechanics::MechanicHandle> across;      // rail to rail (Axis::Y), spell 205340
        std::vector<BossMechanics::MechanicHandle> along;       // bow to stern (Axis::X), spell 205341
        std::vector<BossMechanics::MechanicHandle> cells;       // burning crossings, spell 205342

        std::size_t Lanes() const { return across.size() + along.size(); }
    };

    // Registers one volley on the Juggernaut's deck frame (DeadminesKit::DeckFrame()) with `owner` as the encounter:
    // spec.across lanes rail to rail and spec.along lanes bow to stern, spec.width wide with gaps >= spec.minGap,
    // marked for spec.warnMs, each hit spec.lanePct % of reference non-tank health (Physical) plus 1 Weakened, once
    // per player per volley; with spec.burnCrossings (and lanes on both axes) every crossing burns spec.burnMs, ticking
    // spec.burnPct % Fire every spec.burnTickMs, with the shared "Standing in It" slow. Tags: spec.acrossTag,
    // spec.alongTag, spec.cellTag. No yell, cast bar or log: the caller owns those. Call it from the owner's AI while
    // the owner is in the world (an empty Volley otherwise).
    Volley Fire(Unit* owner, Greenskin::LaneVolley const& spec);

    // Drops the once-per-volley memory of `owner` (its encounter ended). Optional: a stale entry is replaced by the
    // next volley anyway.
    void ForgetOwner(Unit const* owner);
}

#endif
