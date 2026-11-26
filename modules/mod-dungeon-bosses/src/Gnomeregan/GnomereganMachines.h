/*
 * mod-dungeon-bosses, Gnomeregan: the machines contract (handoff section 3.2 item 7, section 7 #8 A, FACTS-FRAMEWORK
 * F50). Written by WP-S0; owned by the orchestrator once S0 reports (a WP asks for a change in its report).
 *
 * The Whole Workshop (Thermaplugg's heroic hard mode, SP 1738-1864) loads each earlier boss's machine onto Thermaplugg
 * at 90 / 75 / 60 / 45 / 30% (MT15). So each of the five machines is built once, by its own boss WP, as a helper that
 * any boss AI can own: parameterized by an owner, an anchor and its numbers, never by "the Techbot AI". Each boss AI
 * calls its own machine; D6Ha and D6Hb call the same machines from the hard mode packages (ThermapluggFight.h).
 *
 *   Machine             what       built by                                  used by
 *   Duplicator          TB3        D1  TechbotMachine.{h,cpp}                Techbot (Dupe Bugs), D6Ha MT16 (bombs)
 *   DoseField           VF1-VF8    D2  ViscousFalloutMachine.{h,cpp}         Fallout, D6Ha MT17-MT20 (venting, dose)
 *   VoltageMeter        EL1, EL2   D3  ElectrocutionerMachine.{h,cpp}        Electrocutioner, D6Hb MT21-MT22
 *   LightsMachine       MA1-MA4    D4  MobileAlertSystemMachine.{h,cpp}      the Alert System, D6Hb MT23
 *   ComboMachine        CP1-CP7    D5  CrowdPummelerMachine.{h,cpp}          Crowd Pummeler, D6Hb MT24 (the fist)
 *
 * The pure halves (the rules a host test pins: when a duplication is due, the dose arithmetic, the Justice cadence, the
 * cone geometry and the latch, the combination lengths and frame shapes) live in each boss's <Boss>Logic.h; the engine
 * halves in <Boss>Machine.{h,cpp}, which define the factory below. The kit pieces under them are KT-G's (src/Kit/:
 * DungeonKit::TurningLights (DungeonKitLights.h), DungeonKit::CalledCombination (DungeonKitCombo.h),
 * DungeonKit::TwoRingMines (DungeonKitMines.h), ranked DwellSoaks (Reprioritize, SetRank): STAGE-KT-G-REPORT s1).
 * A machine wraps them and never forks them. The machines are named apart from the kit classes they wrap
 * (LightsMachine, ComboMachine), so a boss file never meets two TurningLights / CalledCombination names: boss files
 * qualify the kit's as DungeonKit::.
 *
 * Rules every machine keeps (section 3.5):
 *   - Owner: the creature whose summons, registry zones and RefFlat hits these are (rule 2: the boss is the owner). The
 *     factory takes a Creature* and the machine keeps its ObjectGuid (cpp-guidelines: no raw pointer past the call);
 *     each Update resolves it and does nothing when it is gone. Shapes that must outlive a unit sit on a stalker the
 *     caller owns (rule 31).
 *   - Update(diff) every tick of the owner's AI (or the package's OnUpdate); every timer is the machine's own.
 *   - Clear() undoes everything the machine made: auras on players and on the owner, its units, its registry handles,
 *     its clocks and per-player latches (RB-1). The owner calls it at reset, evade and death; a hard mode package in
 *     its OnEnd. Clear() is safe to call twice and after the owner is gone. The destructor does not clear (the owner
 *     may already be gone at the AI's destruction).
 *   - One INFO line per firing: "gnomer-build <logKey> <machine> <what> ..." (DungeonKit::LogMechanic, kLogDungeon).
 *   - An aura amount the machine sets (the dose, Voltage) is reasserted every 1 s and on every change (rule 25).
 *   - Numbers come in through the spec, never from the boss's Tune: the hard mode passes its own (section 3.7).
 *   - Never registered inside the registry's own resolve callback (rule 11): a machine queues to its next Update.
 *
 * Stubs: S0's <Boss>Machine.cpp files defined each factory with an inert machine so the hard mode packages and the
 * boss AIs compiled before D1-D5 reported; D1-D5 replaced every stub with the real machine behind this interface. A
 * change to it is a shared-file request (the boss AIs and both hard mode packages build on it). Two machines have an
 * extended factory beside the contract's: MakeAlertLightsMachine (MobileAlertSystemMachine.h) and the 3-argument
 * MakeComboMachine (CrowdPummelerMachine.h); the contract's factories are those with no extras.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_MACHINES_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_MACHINES_H

#include "Define.h"
#include "DungeonKitArena.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <array>
#include <cstddef>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class Creature;
class Player;

namespace GnomereganMachines
{
    // ----------------------------------------------------------------------------------------------------------------
    // The base every machine shares: the owner's cleanup loops over its machines (RB-1).
    // ----------------------------------------------------------------------------------------------------------------
    class Machine
    {
    public:
        virtual ~Machine() = default;

        // "duplicator", "dose", "voltage", "lights", "combination": the log lines' and `.dbtest`'s name.
        virtual char const* Name() const = 0;
        virtual void Update(uint32 diff) = 0;
        // Undo everything (see the rules above). Safe twice, safe with the owner gone.
        virtual void Clear() = 0;
        // One line for `.dbtest gnomer <boss> state` and the hard mode's `state`.
        virtual std::string Describe() const = 0;
    };

    // Who owns a machine and how it logs: `owner` is resolved to its guid at once; `logKey` is a string literal
    // ("techbot", "thermaplugg"); `heroic` picks nothing by itself (the spec carries the numbers), it only tags logs.
    struct MachineOwner
    {
        Creature* owner = nullptr;
        char const* logKey = "";
        bool heroic = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Duplicator (D1; SP TB3, MT16): a tracked unit casts Duplication after `firstAfterMs` of life (then every
    // `repeatMs`) and becomes two: the copy is the same entry, summoned by the owner at the source's spot with the
    // source's current health (ruling 47, 51). A stun or an interrupt stops the bar (the reward): that cast is lost,
    // the next one comes at the next due time (once-only units never retry). At `capAlive` living tracked units a due
    // cast waits (normal Dupe Bugs: 8); 0 is no cap (heroic, the hard mode).
    // ----------------------------------------------------------------------------------------------------------------
    struct DuplicatorSpec
    {
        uint32 barSpellId = 0;          // the Duplication bar (Nature, interruptible: the kick and dispel table)
        uint32 castMs = 3000;           // normal bugs 3 s; heroic bugs and hard mode bombs 2 s
        uint32 firstAfterMs = 9000;     // normal bugs 9 s; heroic bugs 7 s; hard mode bombs 10 s
        uint32 repeatMs = 0;            // 0: once per unit (normal bugs); heroic bugs 7 s; hard mode bombs 10 s
        uint32 capAlive = 0;            // 0: no cap
        std::vector<uint32> entries;    // the entries that duplicate (a tracked unit of another entry only counts)
        std::optional<uint8> emoteGroup;    // said by the unit at the bar's start (Dupe Bug line 0)
        // The caller's set-up of the copy (fixate it, give it the source's mark, track it in its own lists). The
        // machine tracks the copy itself (its life clock starts at the copy).
        std::function<void(Creature* source, Creature* copy)> onCopy;
    };
    // Duplicator notes (D1, TechbotMachine.h; no interface change):
    //   - The bar spell should apply a short aura of itself on its caster: that aura is the machine's "done" (Techbot's
    //     214302 / 214303). Without one the machine falls back on the bar's remaining time last seen.
    //   - Copies are TEMPSUMMON_CORPSE_TIMED_DESPAWN (5 s) summoned by the owner, so the owner's JustSummoned sees
    //     them: set them up there or in onCopy, never Track them again (a second Track is buffered while the machine
    //     updates, then ignored for a guid it already tracks).
    //   - `entries` filters Track: a unit of another entry is not tracked.

    class Duplicator : public Machine
    {
    public:
        char const* Name() const override { return "duplicator"; }

        // A unit's life clock starts now (it was just summoned by the caller).
        virtual void Track(Creature* unit) = 0;
        // A unit leaves the machine (died, despawned, deleted by Patch); unknown guids are ignored.
        virtual void Forget(ObjectGuid unit) = 0;
        // The tracked units alive now, in tracking order (Patch counts and deletes them; echoes circle them).
        virtual std::vector<ObjectGuid> Units() const = 0;
        virtual uint32 Alive() const = 0;
        // The tracked units casting Duplication now (the bots' kill order: a casting unit first).
        virtual std::vector<ObjectGuid> Casting() const = 0;
    };

    // TechbotMachine.cpp
    std::unique_ptr<Duplicator> MakeDuplicator(MachineOwner const& owner, DuplicatorSpec spec);

    // ----------------------------------------------------------------------------------------------------------------
    // DoseField (D2; SP VF1-VF8, MT17-MT20): the Irradiated stacks on each player. The aura's own effects carry the
    // per-stack percents (done and healing; the hard mode's copy also damage taken), so a registry hit is multiplied by
    // the victim's taken modifiers (section 2.4). The machine owns the count: it sets the stacks, reasserts them,
    // drains them, and runs Leaking and Meltdown on their thresholds.
    // ----------------------------------------------------------------------------------------------------------------
    struct DoseSpec
    {
        uint32 auraSpellId = 0;         // Irradiated (Fallout's) or the hard mode's copy (with damage taken)
        uint32 drainEveryMs = 0;        // 0: never drains (heroic, the hard mode); normal: 1 per 3,000 ms
        std::function<bool(Player*)> drains;    // normal: true while the player stands in no armed pool
        uint32 capAt = 0;               // 0: no cap; normal 10 (Radiation Sickness)
        // At capAt: the caller's Sickness (hit, pulse, stun, emote); the machine then sets the dose to 0.
        std::function<void(Player*)> onCap;
        uint32 leakAt = 0;              // 0: no Leaking; heroic and the hard mode 10
        uint32 leakEveryMs = 10000;
        // A Leaking drop at the player's feet: Fallout a 4 yd pool, the hard mode a Wandering Puddle (the caller's).
        std::function<void(Player*, Position const&)> onLeak;
        uint32 meltdownAt = 0;          // 0: none; heroic and the hard mode 20
        // The carrier crossed meltdownAt upward (true) or fell below it (false): the caller's Spread (MT20, VF8).
        std::function<void(Player*, bool on)> onMeltdown;
        std::optional<uint8> leakEmoteGroup;        // the owner's emote, once per player per pull
        std::optional<uint8> meltdownEmoteGroup;
    };

    class DoseField : public Machine
    {
    public:
        char const* Name() const override { return "dose"; }

        // +doses (or -doses), floored at 0, capped by the spec; returns the new dose.
        virtual uint32 Add(Player* player, int32 doses, char const* why) = 0;
        virtual void Set(Player* player, uint32 dose, char const* why) = 0;
        // The dose after halving (the plate touch MT4/MT18, Half-Life VF9): the rounding is D2's pure rule
        // (ViscousFalloutLogic.h), one for both callers. Returns the new dose.
        virtual uint32 Halve(Player* player, char const* why) = 0;
        virtual uint32 Dose(ObjectGuid player) const = 0;
        // Every carrier with a dose above 0, highest first (the hard mode's plate claim, F41).
        virtual std::vector<std::pair<ObjectGuid, uint32>> Carriers() const = 0;
    };

    // ViscousFalloutMachine.cpp
    std::unique_ptr<DoseField> MakeDoseField(MachineOwner const& owner, DoseSpec spec);

    // ----------------------------------------------------------------------------------------------------------------
    // VoltageMeter (D3; SP EL1, EL2, MT21, MT22): Voltage stacks on the owner (1,000 volts a stack) and Electric
    // Justice at every `justiceEvery` stacks: a donut safe within `safeRadius` of the owner wherever he stands, over
    // `floor`; heroic Electrocutioner alternates it with a 15 yd circle on him (donut first).
    // ----------------------------------------------------------------------------------------------------------------
    struct JusticeSpec
    {
        uint32 barSpellId = 0;          // a Physical bar with InterruptFlags 0 (rule 26: a kick never deletes it)
        uint32 castMs = 4000;
        float safeRadius = 8.f;         // the donut's hole
        float circleRadius = 15.f;      // the heroic circle
        bool alternate = false;         // heroic Electrocutioner: donut, circle, donut ...; the hard mode: donut only
        float pct = 75.f;               // % of the reference row (RefFlat with the owner as the owner)
        DungeonKit::Arena floor;        // the donut's outer reach: the platform, Thermaplugg's room
        std::optional<uint8> yellGroup;         // Electrocutioner line 1 ("Electric justice!")
        std::optional<uint8> donutEmoteGroup;   // Electrocutioner line 2; Thermaplugg line 10 (the hard mode)
        std::optional<uint8> circleEmoteGroup;  // Electrocutioner line 3
        // The registry tag of both shapes (the drill's name for them): 0 keeps Electrocutioner's own 40 (donut) and 41
        // (circle, ElectrocutionerLogic.h); the hard mode passes 85 (G1's kGnTagHmJustice).
        uint32 tag = 0;
    };

    struct VoltageSpec
    {
        uint32 auraSpellId = 0;         // Voltage on the owner (the stack count is the thousands of volts)
        uint32 tickEveryMs = 5000;      // +1 every 5 s
        uint32 justiceEvery = 6;        // at every 6th stack (6,000 volts)
        bool resetAfterJustice = false; // normal: back to 0 after the Justice
        uint32 pauseAfterJusticeMs = 0; // normal: no climb during the bar or for 10 s after it
        uint32 justiceMinGapMs = 0;     // the floor between two bars' starts (normal Electrocutioner 25 s; 0: none)
        float damagePctPerStack = 0.f;  // heroic and the hard mode: +3% per stack (DamageMultiplier)
        JusticeSpec justice;
        // After a Justice bar starts (the caller holds its other casts) and when it lands.
        std::function<void(uint32 count)> onJusticeStart;
        std::function<void(uint32 count, std::vector<Player*> const& hit)> onJusticeLand;
    };

    class VoltageMeter : public Machine
    {
    public:
        char const* Name() const override { return "voltage"; }

        // +stacks: a Megavolt hit, a jump, a discharge, a mine or bomb hit (MT21); returns the new count.
        virtual uint32 Add(uint32 stacks, char const* why) = 0;
        virtual uint32 Stacks() const = 0;
        // 1 + stacks x damagePctPerStack / 100: the caller multiplies its own lightning (or all of its damage).
        virtual float DamageMultiplier() const = 0;
        virtual bool JusticeRunning() const = 0;
        // No climb for `ms` (a phase change; the caller's own pauses).
        virtual void Pause(uint32 ms) = 0;
    };

    // ElectrocutionerMachine.cpp
    std::unique_ptr<VoltageMeter> MakeVoltageMeter(MachineOwner const& owner, VoltageSpec spec);

    // ----------------------------------------------------------------------------------------------------------------
    // LightsMachine (D4; SP MA1-MA4, MT23): searchlight cones on an anchor. Sweep (normal Alert System): one cone locks
    // on a player (a dim cone for `dimMs`), then sweeps `sweepDeg` clockwise over `sweepMs` and goes dark. Turning
    // (heroic Alert System, the hard mode): `cones` cones, evenly spaced (two: opposite), always lit, turning at
    // `turnDegPerSec`, +`speedUpPctPerSpotted` per Spotted, reversing with a stop. Spotted is judged by the machine's
    // script, players only, at most once per `latchMs` per player; the bots read the lit cones and KT-G's look ahead.
    // ----------------------------------------------------------------------------------------------------------------
    // The cones turn around a unit (the light stalker, or the boss himself: the hard mode's moving Thermaplugg) or a
    // fixed point.
    struct LightsAnchor
    {
        ObjectGuid unit;
        std::optional<Position> point;
    };

    struct LightsSpec
    {
        enum class Mode : uint8
        {
            Sweep,
            Turning,
        };

        Mode mode = Mode::Turning;
        uint32 cones = 2;
        float coneDeg = 30.f;           // normal 40, heroic and the hard mode 30
        float rangeYd = 30.f;           // the Alert System 30 (section 7 #21 A); the hard mode to the room's wall
        float turnDegPerSec = 12.f;
        float speedUpPctPerSpotted = 0.f;
        uint32 reverseMinMs = 0;        // 0: never reverses; heroic Alert System 15 to 25 s
        uint32 reverseMaxMs = 0;
        uint32 reverseStopMs = 2000;
        float sweepDeg = 60.f;          // Sweep mode
        uint32 dimMs = 2000;
        uint32 sweepMs = 3000;
        uint32 latchMs = 3000;          // one Spotted per player per latch
        DungeonKit::Arena floor;        // the cones' floor (shapes and bot bounds)
        std::function<void(Player*)> onSpotted;     // the caller's penalty (hit, Weakened, Response Team, a face opens)
        // An extra Spotted rule judged with the cones (the Alert System's 30 yd rule, section 7 #21 A); may be empty.
        std::function<bool(Player*)> alsoSpotted;
        std::optional<uint8> reverseEmoteGroup;     // the Alert System line 3
    };
    // The Turning dim warning and the registry tag are not in LightsSpec: MakeAlertLightsMachine
    // (MobileAlertSystemMachine.h, D4) is the extended factory with a tag (the look ahead takes tag + 1), the dim
    // warning (litAfterMs), a start bearing and direction, and the Spotted source (onSpottedBy). The Alert System and
    // the hard mode's MT23 use it.

    class LightsMachine : public Machine
    {
    public:
        char const* Name() const override { return "lights"; }

        // Turning: lit now (after the caller's opening delay). Sweep: nothing until Sweep().
        virtual void Start() = 0;
        // Sweep mode: lock on `target`, dim, then sweep. Refused (false) while a sweep runs.
        virtual bool Sweep(Player* target) = 0;
        virtual void Reverse() = 0;
        virtual void SpeedUp(float pct) = 0;
        // The first cone's facing (radians, the map's orientation) and the Spotted count of this pull.
        virtual float Facing() const = 0;
        virtual uint32 SpottedCount() const = 0;
    };

    // MobileAlertSystemMachine.cpp
    std::unique_ptr<LightsMachine> MakeLightsMachine(MachineOwner const& owner, LightsAnchor anchor, LightsSpec spec);

    // ----------------------------------------------------------------------------------------------------------------
    // ComboMachine (D5; SP CP1-CP7, MT24): a called chain of punches on a room frame read from a reference point
    // and facing. The whole chain is registered at the call (the call flashes in order, then each live marker, the real
    // zone at the marker's end, no telegraph of its own: KT-G's DungeonKit::CalledCombination). Pummeler's frame is the
    // pocket's (section 7 #28 A); the hard mode fist's is re-set from a random Gnome Face each combination (ruling 68).
    // ----------------------------------------------------------------------------------------------------------------
    enum class PunchShape : uint8
    {
        LeftHalf    = 0,    // the half left of the center line (Pummeler: Left Hook, the east half)
        RightHalf   = 1,    // the half right of it (Right Hook, the west half)
        Near        = 2,    // within nearRadius of the origin (Crowd Pummel; the fist's "near", section 7 #33 A)
        Far         = 3,    // past nearRadius to farOuter (Clinch; the fist's "far")
        Lane        = 4,    // laneWidth wide down the center line for laneLength (Uppercut)
    };
    std::size_t constexpr kPunchShapeCount = 5;

    // One punch of a chain; `paired`: a One-Two, both shapes at once (CP7).
    struct Punch
    {
        PunchShape shape = PunchShape::LeftHalf;
        std::optional<PunchShape> paired;
    };

    struct ComboFrame
    {
        Position origin;                // the frame's origin; its orientation is the center line's direction
        float halfReachYd = 30.f;       // the halves reach this far from the origin
        float nearRadiusYd = 12.f;
        float farOuterYd = 40.f;
        float laneWidthYd = 8.f;
        float laneLengthYd = 25.f;
        DungeonKit::Arena floor;        // the bots' bounds for every shape (`.Within`); the hits are not clipped
    };

    struct ComboSpec
    {
        ComboFrame frame;
        uint32 callFlashMs = 1000;      // a call flash per punch, in order (0: none, the hard mode draws at once)
        uint32 windUpMs = 0;            // the hard mode: the face lights and the fist winds up 4 s before punch 1
        uint32 markerMs = 1500;         // the live marker: normal 1.5 s, heroic 0.8 s
        uint32 gapMs = 2000;            // punches apart: normal 2 s, heroic 1.2 s, the hard mode 2.5 s
        bool drawAllAtOnce = false;     // the hard mode: every shape drawn at the call, numbered in order
        std::array<float, kPunchShapeCount> pct{};      // % of the reference row by PunchShape
        bool weakened = true;
        std::optional<uint8> callEmoteGroup;            // Pummeler line 0; Thermaplugg line 11
        // A punch landed: the players it hit (the caller's riders: knockback, knock up; heroic counts landed punches).
        std::function<void(uint32 index, Punch const& punch, std::vector<Player*> const& hit)> onPunch;
        // A numbered marker for punch `index` (1-based) of a drawAllAtOnce chain: the caller's numeral (V's displays).
        std::function<void(uint32 index, Position const& at)> onNumber;
    };

    class ComboMachine : public Machine
    {
    public:
        char const* Name() const override { return "combination"; }

        // Register the whole chain now; returns its length in ms (0: refused, one is running or the chain is empty).
        virtual uint32 Call(std::vector<Punch> const& chain) = 0;
        // A new frame for the next call (the hard mode fist: a new face each combination).
        virtual void SetFrame(ComboFrame const& frame) = 0;
        virtual bool Running() const = 0;
        // The punches of the running (or last) chain that hit at least one player.
        virtual uint32 Landed() const = 0;
    };

    // CrowdPummelerMachine.cpp. The 3-argument MakeComboMachine(owner, spec, ComboExtras) in CrowdPummelerMachine.h
    // adds per-shape hit spells and registry tags, names, a rider and onLive / onStrike / onHit / onEnd (D5; the hard
    // mode's fist uses it for its tag 84).
    std::unique_ptr<ComboMachine> MakeComboMachine(MachineOwner const& owner, ComboSpec spec);
}

#endif
