/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff sections 3.11 and 3.4 F37, F54; SP CP1-CP7,
 * MT24): a called combination. The pure rules are DungeonKitComboLogic.h (ComboFrame, ComboShapeDef, PlacedShape,
 * ComboTimeline).
 *
 *   CalledCombination  a chain of punches on a frame (a reference point and a facing: the pocket's center line, the
 *                      line from a Gnome Face through the room's center). Each punch is one shape, or several at once
 *                      (the One-Two). At Start the whole chain is registered for the bots: one real Zone per shape,
 *                      NoTelegraph, resolving at its strike (damage, Weakened, rider, the shape's own options). The
 *                      players see the calls (Decoy Zones in the call color, outline only: in order, or all at once
 *                      with numbered markers) and each punch's live marker (a Decoy with the fill, liveMs before the
 *                      strike); a Decoy hits nobody and the bots never see it. A punch has landed when its real Zone
 *                      hit a player (the heroic +1 per landed punch); onEnd gets the count after the last strike.
 *
 * Crowd Pummeler (normal): Sequential, call 1000, live 1500, spacing 2000; heroic live 800, spacing 1200, One-Two
 * pairs from the fourth punch. The fist (MT24): AllAtOnce, call 4000 (the wind-up), live 0, spacing 2500, numeral
 * displays CDI 90853-90855 on numeralEntry, the frame from FrameFacing(face, z, room center).
 *
 * Owned by one AI: Configure once (or per combination), Start per combination, Update from UpdateAI, Stop from Reset,
 * JustDied, EnterEvadeMode and any hold that ends the chain (RB-18: it cancels every shape still to come). Lambdas
 * capture guids only.
 *
 *     DungeonKit::CalledCombination _combo;
 *     _combo.Configure({ .shapes = { leftHook, rightHook, pummel }, .timing = { .liveMs = 1500, .spacingMs = 2000 },
 *         .onEnd = [](Creature* owner, DungeonKit::ComboResult const& r) { ... }, .dungeon = "gnomer-build",
 *         .boss = "pummeler", .name = "combo" });
 *     _combo.Start(me, kPocketFrame, { { { HOOK_LEFT } }, { { PUMMEL } }, { { HOOK_RIGHT, PUMMEL } } });
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_COMBO_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_COMBO_H

#include "BossMechanics.h"
#include "DungeonKitComboLogic.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <vector>

class Creature;

namespace DungeonKit
{
    // One kind of punch: its shape on the frame and its hit.
    struct ComboShape
    {
        ComboShapeDef def;
        float pct = 40.f;                       // % of the reference non-tank row
        float tankPct = -1.f;                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;                     // a dungeon copy of the resolve spell (0: by school)
        bool weakened = true;
        uint32 rider = 0;
        std::optional<BossMechanics::Color> color;      // the live marker's (and the hidden real Zone's)
        // Extra registry options on the real Zone (OnHit for a knockback, Within, ZTolerance ...). Capture guids only.
        std::function<void(BossMechanics::MechanicRef&)> configure;
        char const* name = "punch";             // log
    };

    // One punch: the indexes of its shapes in the spec's list (two or more at once: a One-Two).
    struct ComboPunch
    {
        std::vector<uint8> shapes;
    };

    struct ComboResult
    {
        uint8 punches = 0;
        uint8 landed = 0;                       // punches whose real Zone hit at least one player
        std::vector<bool> landedPunch;
        bool stopped = false;                   // Stop ended it before the last strike (onEnd is not called then)
    };

    struct CalledCombinationSpec
    {
        std::vector<ComboShape> shapes;
        ComboTiming timing;
        float zTolerance = 6.f;                 // every Zone's height band
        bool drawCalls = true;
        bool callFill = false;                  // false: the calls are outlines (a flash, not a warning)
        std::optional<BossMechanics::Color> callColor;
        bool drawLive = true;
        uint32 tag = 0;
        // The numbered markers (AllAtOnce, MT24): a stalker of numeralEntry at each shape's LabelPoint from the
        // punch's call to its strike, wearing numeralDisplays[punch] at numeralScale (no display for that punch: no
        // marker). 0: none.
        uint32 numeralEntry = 0;
        std::vector<uint32> numeralDisplays;
        float numeralScale = 1.f;
        // At each punch's call (from Start / Update): its placed shapes and how long until its strike (a look of
        // your own). Capture guids only.
        std::function<void(Creature* owner, uint8 punch, std::vector<PlacedShape> const& shapes, uint32 untilStrikeMs)>
            onCall;
        std::function<void(Creature* owner, uint8 punch)> onStrike;             // at each strike (the punch pose)
        std::function<void(Creature* owner, ComboResult const& result)> onEnd;  // after the last strike resolved
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> <name>-start|-strike|-end|-stop"
        char const* boss = "combo";
        char const* name = "combo";
    };

    class CalledCombination
    {
    public:
        static uint32 constexpr kEndSlackMs = 1000;     // onEnd at the latest this long after the last strike

        void Configure(CalledCombinationSpec spec);
        CalledCombinationSpec const& Spec() const { return _spec; }

        // Registers the whole chain on `frame` (an unknown shape index is skipped). False with no owner, no punch, or
        // a chain already running (Stop it first).
        bool Start(Creature* owner, ComboFrame const& frame, std::vector<ComboPunch> punches);
        // Calls, live markers, strikes and the end.
        void Update(Creature* owner, uint32 diff);
        // Cancels every shape and marker still to come (a hold, a wipe).
        void Stop(Creature* owner);

        bool Active() const { return _active; }
        uint32 ElapsedMs() const { return _elapsedMs; }
        std::size_t Punches() const { return _punches.size(); }
        uint8 Landed() const;
        ComboFrame const& Frame() const { return _frame; }
        std::vector<PunchTimes> const& Times() const { return _times; }
        // The map shapes of punch `i` (empty: no such punch).
        std::vector<PlacedShape> ShapesOf(std::size_t i) const;

    private:
        struct State
        {
            std::vector<bool> landed;
            uint32 resolved = 0;
        };

        struct Step
        {
            ComboPunch punch;
            std::vector<PlacedShape> placed;
            bool called = false;
            bool live = false;
            bool struck = false;
        };

        void Call(Creature* owner, uint8 i);
        void Live(Creature* owner, uint8 i);
        void Strike(Creature* owner, uint8 i);
        void Finish(Creature* owner);

        CalledCombinationSpec _spec;
        ComboFrame _frame;
        std::vector<Step> _punches;
        std::vector<PunchTimes> _times;
        std::vector<BossMechanics::MechanicHandle> _real;
        std::vector<BossMechanics::MechanicHandle> _decoys;
        std::vector<ObjectGuid> _numerals;
        std::shared_ptr<State> _state;
        uint32 _elapsedMs = 0;
        bool _active = false;
    };

    // A placed shape as a registry ZoneSpec on point anchors (a Rect is a LineFacing).
    BossMechanics::ZoneSpec ZoneSpecOf(PlacedShape const& shape);
}

#endif
