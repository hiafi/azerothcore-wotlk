/*
 * mod-dungeon-bosses, Gnomeregan D6Ha: the Whole Workshop, part a (Mekgineer Thermaplugg's heroic hard mode, SP
 * 1738-1864, rulings 43-53, 68, 69; handoff section 3.5 row D6Ha, 3.6, 3.7, 3.8, section 7 #1 A, #32 A, #35 A, #38 i
 * A): the pure, host-testable part (no engine headers). The engine side is thermaplugg_hard_mode.cpp (the console,
 * package SchematicsA through ThermapluggFight.h, the Wandering Puddle, the workshop stalkers, `.dbtest gnomer
 * workshop`); tested by tests/gnomer_hard_mode_test.cpp; the DT file source/npcs/gnomeregan/thermaplugg_hard_mode.py
 * declares the same ids (lib/test_gnomeregan_hard_mode.py pins them). Health is GnomereganRework.h Health (the hard
 * mode's 800,000 is D6's at the pull): never restated here. Every value of SP 1799's hard mode column (faces, Override,
 * bombs, blasts, mines, Detonator, lockout) is D6's own (ThermapluggLogic.h ValuesFor(Mode::HardMode)): this package
 * only adds its schematics and the Reactor Leak.
 *
 * What part a owns (the split of handoff s3.5 / s3.7 with D6Hb):
 *   - the Clearance Console (GO 301382): the Prismatic Punch Card in the bags, heroic, out of combat, a confirmation;
 *     the card is read and kept; bots are refused (rule 34: a playerbot session has no socket); the flag
 *     (DATA_HARD_MODE), the pull's verdict, slot 6 and the loot bit are the instance's and D6's;
 *   - MT15 for its two schematics: the yell (7800 line 9) on the first (90%) and the console's line "Loading
 *     schematic: TECHBOT" / "VISCOUS FALLOUT", a raid boss emote from Thermaplugg over the room (D6Hb's form for its
 *     three loads at 60 / 45 / 30, which says its own lines; 7800 groups 10 and 11 are D6Hb's);
 *   - MT16 the Techbot schematic (90%): every walking bomb alive 10 s casts Duplication (2 s, Nature, kickable, a stun
 *     stops it) and becomes two at its current health, again every 10 s, no cap (D1's Duplicator; D6's AdoptBomb);
 *   - MT17 to MT20 the Viscous Fallout schematic (75%): venting (1 dose to every player per open face every 8 s), the
 *     hard mode dose (Fallout's aura plus 3% damage taken a dose; D2's DoseField; it never drains), a plate touch
 *     halves it (D2's Halve: loses half, rounded up), Leaking at 10 (a Wandering Puddle every 10 s: 4 yd, 2 yd/s, 2
 *     min, 8% and 1 dose a second inside), Meltdown at 20 (6 yd, 5% a second); the bots' plate rule while it runs
 *     (PlatePlan: D6's one plate Soak per lit plate takes the dose ordering, a bot at 8 or more is sent to its
 *     nearest lit plate first; F-1d, STAGE-R-1-C Minor-1 and DQ1);
 *   - MT25 the Reactor Leak: 180 s from the pull, the alarm at 2 min, 1 min, 30 s and 10 s left, then 10% of the
 *     reference row a second to every player on his threat list (s7 #35 A), multiplied by the dose.
 *
 * The dose halving rule is D2's (GnomerFallout::Halve(d) = d / 2: a halved dose loses half, rounded up; STAGE-S0 Q10):
 * this header never restates it; the package calls DoseField::Halve.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_HARD_MODE_LOGIC_H

#include "GnomereganRework.h"
#include "ThermapluggLogic.h"
#include "ViscousFalloutLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace GnomerWorkshop
{
    using GnomereganRework::Vec2;

    // Every spell of this WP sits in this slice. The console's 214620-214639 (kSpellsConsoleAndSpare) stay unused (the
    // console casts nothing): released to the orchestrator.
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsHardModeA;

    // The DT file declares the same ids; 214549-214579 are spare.
    enum WorkshopSpells : std::uint32_t
    {
        SPELL_HM_IRRADIATED     = kSpellSlice.first + 0,    // MT18 the dose: Fallout's aura + 3% damage taken a stack
        SPELL_HM_DOSE_GLOW      = kSpellSlice.first + 1,    // MT18 the bright glow at 10 and up (Leaking)
        SPELL_HM_DUPLICATION    = kSpellSlice.first + 2,    // MT16 the bomb's 2 s bar (Nature, kickable)
        SPELL_HM_VENT           = kSpellSlice.first + 3,    // MT17 the green vapor on a vent stalker (lasting look)
        SPELL_HM_PUDDLE         = kSpellSlice.first + 4,    // MT19 the puddle's tick (resolve copy, Nature)
        SPELL_HM_MELTDOWN       = kSpellSlice.first + 5,    // MT20 (resolve copy, Nature)
        SPELL_HM_MELTDOWN_AURA  = kSpellSlice.first + 6,    // MT20 the carrier's read
        SPELL_HM_REACTOR_LEAK   = kSpellSlice.first + 7,    // MT25 the flood's tick (resolve copy, Nature)
        SPELL_HM_LEAK_AURA      = kSpellSlice.first + 8,    // MT25 the flooded room's screen effect on each player
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_HM_LEAK_AURA;

    // Mekgineer Thermaplugg's package line (7800 group 9 = GnomerThermaplugg::kFirstPackageTextGroup).
    inline constexpr std::uint8_t SAY_HM_SCHEMATIC = GnomerThermaplugg::kFirstPackageTextGroup;

    // The room alarm 301137 (it stands at the Clearance Console): the Reactor Leak's countdown, boss emotes, map-wide.
    enum AlarmTexts : std::uint8_t
    {
        ALARM_TWO_MINUTES   = 0,    // "Reactor containment failing: 2 minutes."
        ALARM_ONE_MINUTE    = 1,
        ALARM_THIRTY        = 2,
        ALARM_TEN           = 3,
        ALARM_FAILURE       = 4,    // "Warning! Reactor containment failure!"
    };
    inline constexpr std::uint8_t kAlarmLastGroup = ALARM_FAILURE;

    // The registry tags of part a, in the Whole Workshop's block 80-89 (BM MechanicDrill.h: 80 mines, 81 puddles, 82-83
    // lights, 84 fist, 85 Justice; LESSONS A.3 #4). 81 is the drill's; 87-89 are live only (not drilled). D6Hb keeps
    // 80 and 82-85. 86 is spare: the dose claim's own Soak group went (F-1d: the plates are D6's one group, tag 71).
    enum WorkshopTags : std::uint32_t
    {
        TAG_HM_PUDDLE           = 81,   // MT19 the Wandering Puddle's lasting zone (telegraph only; drill Zone/81)
        TAG_HM_MELTDOWN         = 87,   // MT20 the 6 yd Spread and the carrier's tick
        TAG_HM_PUDDLE_TICK      = 88,   // MT19 the script's tick on players inside a puddle
        TAG_HM_REACTOR_LEAK     = 89,   // MT25 the flood's tick
    };

    struct DrillTag
    {
        char const* name;
        std::uint32_t tag;
    };

    inline constexpr std::array<DrillTag, 4> kDrillTags{ {
        { "puddle", TAG_HM_PUDDLE }, { "meltdown", TAG_HM_MELTDOWN }, { "puddle-tick", TAG_HM_PUDDLE_TICK },
        { "reactor-leak", TAG_HM_REACTOR_LEAK },
    } };
    // D6Hb's tags of the block (BM MechanicDrill.h kGnTagHm*): part a never uses them.
    inline constexpr std::array<std::uint32_t, 5> kPartBTags{ { 80, 82, 83, 84, 85 } };

    // Looks and sounds (WP-V's _visuals.py; the DT test pins each).
    inline constexpr std::uint32_t kDisplayNatureDisc = 90850;      // MT_PUDDLE, MT_LEAK (DISPLAY_NATURE_DISC)
    inline constexpr std::uint32_t kSoundGeiger = 11757;            // MT_GEIGER
    inline constexpr std::uint32_t kSoundAlarm = 5763;              // MT_LEAK_ALARM_SOUND
    inline constexpr float kLeakDiscScale = 10.4f;                  // LEAK_DISC_SCALE: about a 50 yd radius

    // ----------------------------------------------------------------------------------------------------------------
    // MT15 part a's schematics (ruling 45): each earlier boss's machine at a health line, in kill order, to the end.
    // D6Hb's three (Electrocutioner 60%, the Alert System 45%, Crowd Pummeler 30%): ThermapluggHardModeMachinesLogic.h.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Schematic : std::uint8_t
    {
        Techbot = 0,            // MT16
        ViscousFallout = 1,     // MT17 to MT20
    };
    std::size_t constexpr kSchematicCount = 2;

    inline constexpr std::array<float, kSchematicCount> kSchematicPct{ { 90.f, 75.f } };
    inline constexpr std::array<char const*, kSchematicCount> kSchematicKeys{ { "techbot", "viscous-fallout" } };
    // The console's names (SP: "Loading schematic: TECHBOT" and so on; D6Hb's line form).
    inline constexpr std::array<char const*, kSchematicCount> kSchematicNames{ { "TECHBOT", "VISCOUS FALLOUT" } };
    inline constexpr char kLoadLinePrefix[] = "Loading schematic: ";

    // The schematic loaded at a health line (OnHealthPct passes the line itself); none for any other value.
    constexpr std::optional<Schematic> SchematicAt(float pct)
    {
        for (std::size_t i = 0; i < kSchematicCount; ++i)
            if (pct == kSchematicPct[i])
                return Schematic(i);
        return std::nullopt;
    }

    inline std::string LoadLine(Schematic s)
    {
        return std::string(kLoadLinePrefix) + kSchematicNames[std::size_t(s)];
    }

    namespace Tune
    {
        using GnomereganRework::kWarningFloorMs;

        // MT16 Bomb Duplication (SP 1837: a bomb alive 10 s, a 2 s cast, again every 10 s, no cap)
        inline constexpr std::uint32_t kDupCastMs = 2000;
        inline constexpr std::uint32_t kDupFirstMs = 10000;
        inline constexpr std::uint32_t kDupRepeatMs = 10000;
        inline constexpr std::uint32_t kDupCapAlive = 0;
        inline constexpr std::uint8_t kDupKickPriority = 3;             // the kick table: a reward
        inline constexpr std::int8_t kCastingBombPriority = 3;          // above D6's walking bombs (2): first

        // MT15 the console's line: a raid boss emote from him over the room (D6Hb's kConsoleLineYd)
        inline constexpr float kConsoleLineYd = 120.f;

        // MT17 venting, MT18 the dose (ruling 49)
        inline constexpr std::uint32_t kVentEveryMs = 8000;
        inline constexpr std::uint32_t kVentDosePerFace = 1;
        inline constexpr std::uint32_t kDosePctPerStack = 3;            // done, healing done and taken, a stack
        inline constexpr std::uint32_t kAuraStackLimit = GnomerFallout::Tune::kAuraStackLimit;
        inline constexpr std::uint32_t kPlateDoseFloor = 8;             // SP MT18: a bot at 8 or more takes a plate
        inline constexpr std::uint32_t kPlatePlanMs = 1000;             // PlatePlan again (the plates' serve order)
        inline constexpr std::uint32_t kGlowAt = 10;                    // the bright glow: Leaking
        inline constexpr std::uint32_t kCarrierPollMs = 250;
        inline constexpr std::uint32_t kCarrierSecondMs = 1000;

        // MT19 Leaking and the Wandering Puddle (rulings 48, 52)
        inline constexpr std::uint32_t kLeakAt = 10;
        inline constexpr std::uint32_t kLeakEveryMs = 10000;
        inline constexpr float kPuddleYd = 4.f;
        inline constexpr std::uint32_t kPuddleFormMs = 1500;            // "the puddle forms over 1.5 sec"
        inline constexpr std::uint32_t kPuddleLifeMs = 120000;          // ruling 52, after it formed
        inline constexpr float kPuddleSpeedYdPerSec = 2.f;
        inline constexpr float kPuddlePct = 8.f;
        inline constexpr std::uint32_t kPuddleDose = 1;
        inline constexpr std::uint32_t kPuddleTickMs = 1000;
        inline constexpr float kPuddleZBandYd = 6.f;
        inline constexpr float kPuddleLegYd = 8.f;                      // (switch) one straight drift before a check
        inline constexpr std::uint32_t kPuddleLegTimeoutMs = 6000;      // a leg not done by then (a snag): the next one
        inline constexpr float kPuddleTurnStepDeg = 30.f;               // at a wall: the way back, then 30 deg steps
        inline constexpr std::uint32_t kPuddleTurnTries = 12;
        inline constexpr float kPuddleBounceJitterDeg = 40.f;           // (switch) the bounce's spread, +- this
        inline constexpr float kPuddleFormScale = 0.5f;                 // of the full disc while it forms
        inline constexpr float kPuddleDiscScale = GnomerFallout::DiscScale(kPuddleYd);

        // MT20 Meltdown (as Fallout's heroic)
        inline constexpr std::uint32_t kMeltdownAt = 20;
        inline constexpr float kMeltdownYd = 6.f;
        inline constexpr float kMeltdownPct = 5.f;
        inline constexpr std::uint32_t kMeltdownTickMs = 1000;
        inline constexpr std::uint32_t kMeltdownWarnMs = 1500;

        // MT25 the Reactor Leak (rulings 46, 50): 180 s from the pull, 10% a second, no ramp
        inline constexpr std::uint64_t kLeakStartMs = 180000;
        inline constexpr std::uint32_t kLeakTickMs = 1000;
        inline constexpr float kLeakPct = 10.f;
        // The alarm lines 0 to 3: 2 min, 1 min, 30 s and 10 s left.
        inline constexpr std::array<std::uint64_t, 4> kAlarmAtMs{ { 60000, 120000, 150000, 170000 } };

        inline constexpr std::uint32_t kWholeFightMs = 4u * 3600u * 1000u;

        static_assert(kDupCastMs >= kWarningFloorMs, "the Duplication bar is the warning");
        static_assert(kPuddleFormMs >= kWarningFloorMs, "a puddle forms over at least 1.5 s");
        static_assert(kMeltdownWarnMs >= kWarningFloorMs, "Meltdown warns for at least 1.5 s");
        static_assert(kLeakAt < kMeltdownAt, "Leaking before Meltdown");
        static_assert(kPlateDoseFloor < kLeakAt, "bots shed the dose before they leak");
        static_assert(kAuraStackLimit == 255, "the client counter");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT17 venting, MT18 the dose
    // ----------------------------------------------------------------------------------------------------------------

    // The doses one venting pulse adds to each player.
    constexpr std::uint32_t VentDoses(std::uint32_t openFaces)
    {
        return openFaces * Tune::kVentDosePerFace;
    }

    // The damage taken factor of a dose (one MOD_DAMAGE_PERCENT_TAKEN effect whose amount is 3 x the stacks).
    constexpr float DamageTakenFactor(std::uint32_t dose)
    {
        return 1.f + float(Tune::kDosePctPerStack * dose) / 100.f;
    }

    // A vent stalker stands at a face while the Fallout schematic runs and the face is open.
    constexpr bool VentWanted(bool falloutLoaded, bool faceOpen)
    {
        return falloutLoaded && faceOpen;
    }

    // The beats use D6's GnomerThermaplugg::NextDue(due, period, now) (RB-16: one rule; F-1d dropped this header's
    // copy, whose argument order was swapped).

    // ----------------------------------------------------------------------------------------------------------------
    // MT18 the plates while the Fallout schematic runs (F-1d, STAGE-R-1-C Minor-1 and DQ1)
    // ----------------------------------------------------------------------------------------------------------------
    // One exclusive group: D6's plate Soak (tag 71, one claim a bot) takes the dose ordering (Irradiated, the highest
    // first, no floor: a bot under 8 still presses plates, SP MT4) and the bots serve the lit plates in the order
    // PlatePlan gives. BM serves the group plate by plate, each plate taking the best bot left by (tier, dose, ETA),
    // so the plates the dose bots should take go first, each in its bot's turn: every bot at 8 or more ends on the
    // nearest lit plate not yet taken (SP MT18) and holds that one claim.
    struct PlatePlayer
    {
        std::uint64_t guid = 0;
        std::uint32_t dose = 0;
        bool bot = false;
        bool tank = false;          // the role provider's tank (his victim)
        bool eligible = false;      // alive in the room and not Locked Out
        Vec2 at;
    };

    struct LitPlate
    {
        std::uint32_t face = 0;
        Vec2 at;
        std::int32_t rank = 0;      // D6's face priority (GnomerThermaplugg::PlateRank): lower is served first
    };

    // STAGE-R-1-C DQ1 (orchestrator ruling): the tank sheds its dose last. It stays in the plates' last tier (SP MT4,
    // non-tanks first) unless it is at the floor and no other eligible player is: then it is ranked by its dose with
    // the others, so it takes a plate before anyone under 8.
    inline bool TankPlatesLast(std::vector<PlatePlayer> const& players)
    {
        bool tankAtFloor = false;
        for (PlatePlayer const& p : players)
        {
            if (!p.eligible || p.dose < Tune::kPlateDoseFloor)
                continue;
            if (!p.tank)
                return true;        // another player at 8 or more can shed: the tank waits
            tankAtFloor = true;
        }
        return !tankAtFloor;
    }

    // RF-1 Minor-5: the bots PlatePlan places (at the floor or more, eligible; the tank only when TankPlatesLast is
    // false), by guid, sorted. D6 registers the plates anew whenever this set changes, not only when the serve order
    // does: a bot that just reached 8 is then served in its plan turn, not after an older sticky claim (BM serves a
    // sticky bot claim before the rule order, and a claim lives on its registration).
    inline std::vector<std::uint64_t> PlatePlanBots(std::vector<PlatePlayer> const& players, bool tankLast)
    {
        std::vector<std::uint64_t> out;
        for (PlatePlayer const& p : players)
            if (p.bot && p.eligible && p.dose >= Tune::kPlateDoseFloor && !(p.tank && tankLast))
                out.push_back(p.guid);
        std::sort(out.begin(), out.end());
        out.erase(std::unique(out.begin(), out.end()), out.end());
        return out;
    }

    // SP MT18: the lit plates in the order the bots serve them. The bots at the floor or more (eligible; the tank
    // only when TankPlatesLast is false) go highest dose first, each to the nearest lit plate not yet taken; among
    // bots of one dose the closest bot and plate pair goes first (BM breaks a dose tie by the ETA to the plate, so
    // the bot it picks for that plate is the one planned). Ties: the lower rank, the lower face, the lower guid. Those
    // plates come first, in that order; the rest follow by rank, then face. Each face once.
    inline std::vector<std::uint32_t> PlatePlan(std::vector<LitPlate> plates, std::vector<PlatePlayer> const& players,
        bool tankLast)
    {
        std::sort(plates.begin(), plates.end(), [](LitPlate const& a, LitPlate const& b)
        {
            return a.rank != b.rank ? a.rank < b.rank : a.face < b.face;
        });
        std::vector<PlatePlayer const*> bots;
        for (PlatePlayer const& p : players)
            if (p.bot && p.eligible && p.dose >= Tune::kPlateDoseFloor && !(p.tank && tankLast))
                bots.push_back(&p);
        std::sort(bots.begin(), bots.end(), [](PlatePlayer const* a, PlatePlayer const* b)
        {
            return a->dose != b->dose ? a->dose > b->dose : a->guid < b->guid;
        });
        std::vector<bool> taken(plates.size(), false);
        std::vector<bool> placed(bots.size(), false);
        std::vector<std::uint32_t> out;
        out.reserve(plates.size());
        for (std::size_t from = 0; from < bots.size();)
        {
            // the bots of the highest dose left: [from, to)
            std::size_t to = from;
            while (to < bots.size() && bots[to]->dose == bots[from]->dose)
                ++to;
            for (std::size_t round = from; round < to; ++round)
            {
                std::size_t bestBot = to, bestPlate = plates.size();
                float bestYd = 0.f;
                for (std::size_t b = from; b < to; ++b)
                {
                    if (placed[b])
                        continue;
                    for (std::size_t i = 0; i < plates.size(); ++i)
                    {
                        if (taken[i])
                            continue;
                        float const yd = DungeonKit::Distance(bots[b]->at, plates[i].at);
                        if (bestPlate == plates.size() || yd < bestYd)
                        {
                            bestBot = b;
                            bestPlate = i;
                            bestYd = yd;
                        }
                    }
                }
                if (bestPlate == plates.size())
                    break;      // every lit plate is taken
                placed[bestBot] = true;
                taken[bestPlate] = true;
                out.push_back(plates[bestPlate].face);
            }
            from = to;
        }
        for (std::size_t i = 0; i < plates.size(); ++i)
            if (!taken[i])
                out.push_back(plates[i].face);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT25 the Reactor Leak's clock
    // ----------------------------------------------------------------------------------------------------------------

    // The alarm lines (0 to 3) due at `clockMs` that `fired` (a bit per line) has not said yet, in order.
    inline std::vector<std::uint8_t> AlarmsDue(std::uint64_t clockMs, std::uint8_t fired)
    {
        std::vector<std::uint8_t> out;
        for (std::size_t i = 0; i < Tune::kAlarmAtMs.size(); ++i)
            if (clockMs >= Tune::kAlarmAtMs[i] && !(fired & (1u << i)))
                out.push_back(std::uint8_t(i));
        return out;
    }

    constexpr bool LeakOn(std::uint64_t clockMs)
    {
        return clockMs >= Tune::kLeakStartMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT19 the Wandering Puddle: a drift across the room at 2 yd/s, turning at the walls
    // ----------------------------------------------------------------------------------------------------------------
    using DungeonKit::kPi;

    constexpr float DegToRad(float deg)
    {
        return deg * kPi / 180.f;
    }

    struct PuddleLeg
    {
        float heading = 0.f;    // radians, the map's orientation (+x north, +y west)
        Vec2 to;
        bool moved = false;     // false: no leg fits (the puddle stands this leg out)
    };

    // The whole leg on the floor: three points along it and its end inside the arena at `z`.
    inline bool LegInside(GnomereganRework::Arena const& arena, Vec2 from, Vec2 to, float z)
    {
        for (int i = 1; i <= 4; ++i)
        {
            float const t = float(i) / 4.f;
            Vec2 const p{ from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t };
            if (!arena.Contains(p, z))
                return false;
        }
        return true;
    }

    // The next leg: straight on while the floor goes on; at a wall the way back first (spread by `jitterDeg`, the
    // caller's random), then turns of kPuddleTurnStepDeg to either side, alternating.
    inline PuddleLeg NextPuddleLeg(GnomereganRework::Arena const& arena, Vec2 from, float z, float heading,
        float jitterDeg, float legYd = Tune::kPuddleLegYd)
    {
        auto end = [&](float h) { return Vec2{ from.x + std::cos(h) * legYd, from.y + std::sin(h) * legYd }; };
        if (Vec2 const to = end(heading); LegInside(arena, from, to, z))
            return { heading, to, true };
        float const back = heading + kPi + DegToRad(jitterDeg);
        for (std::uint32_t i = 0; i < Tune::kPuddleTurnTries; ++i)
        {
            float const step = float((i + 1) / 2) * DegToRad(Tune::kPuddleTurnStepDeg);
            float const h = back + ((i % 2) ? step : -step);
            if (Vec2 const to = end(h); LegInside(arena, from, to, z))
                return { std::remainder(h, 2.f * kPi), to, true };
        }
        return { heading, from, false };
    }

    struct PuddleSpot
    {
        Vec2 at;                // the puddle's live position
        float z = 0.f;
        std::uint64_t bornMs = 0;
    };

    constexpr bool PuddleArmed(std::uint64_t bornMs, std::uint64_t nowMs)
    {
        return nowMs >= bornMs + Tune::kPuddleFormMs;
    }

    // MT19: a player inside any armed puddle (once a second however many overlap, as Fallout's pools).
    inline bool InAnyPuddle(std::vector<PuddleSpot> const& puddles, Vec2 p, float z, std::uint64_t nowMs)
    {
        for (PuddleSpot const& s : puddles)
        {
            if (!PuddleArmed(s.bornMs, nowMs) || std::fabs(s.z - z) > Tune::kPuddleZBandYd)
                continue;
            float const dx = p.x - s.at.x;
            float const dy = p.y - s.at.y;
            if (dx * dx + dy * dy <= Tune::kPuddleYd * Tune::kPuddleYd)
                return true;
        }
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Clearance Console (handoff 3.7; GnomereganRework.h ConsoleCheck is the rule, this is its screen)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kConsoleGossipMenu = 5300022;
    inline constexpr std::uint32_t kConsoleGossipOption = 0;        // "Insert the Prismatic Punch Card."
    inline constexpr std::uint32_t kConsoleNpcText = 900029;
    inline constexpr std::uint32_t kConsoleActionArm = 1;
    inline constexpr std::uint32_t kConsolePollMs = 1000;

    inline constexpr char kConsoleAccepted[] = "Clearance: PRISMATIC. All schematics unlocked.";

    inline constexpr char kConsoleBossDone[] = "Clearance refused: the Mekgineer is already defeated.";

    // The line a refused player reads (none for a bot: a bot gets no menu and no line). `bossDone`: Thermaplugg's slot
    // is DONE (S0's ConsoleCheck answers CONSOLE_BOSS_ENGAGED for a fight and a kill alike; STAGE-R-1-C Nit-3).
    constexpr char const* ConsoleRefusalText(GnomereganRework::ConsoleVerdict v, bool bossDone = false)
    {
        switch (v)
        {
            case GnomereganRework::CONSOLE_ACCEPTED:
            case GnomereganRework::CONSOLE_BOT:
                return "";
            case GnomereganRework::CONSOLE_NOT_HEROIC:
                return "Clearance Console offline: heroic only.";
            case GnomereganRework::CONSOLE_IN_COMBAT:
                return "Clearance refused: not while in combat.";
            case GnomereganRework::CONSOLE_NO_CARD:
                return "Clearance refused: a Prismatic Punch Card is required.";
            case GnomereganRework::CONSOLE_BOSS_ENGAGED:
                return bossDone ? kConsoleBossDone : "Clearance refused: the Mekgineer is already at work.";
            case GnomereganRework::CONSOLE_ALREADY_SET:
                return kConsoleAccepted;
        }
        return "";
    }
}

#endif
