/*
 * mod-dungeon-bosses, Blackrock Depths D3:
 * Houndmaster Grebmar (9319) and his Kennel Hounds (300781), the pure, host-testable part (no engine headers). Build
 * spec S1 "Houndmaster Grebmar" (docs/dungeons/blackrock-depths-1-detention-block.md, GR1-GR8; rulings 15-16, 88),
 * handoff sections 3.4 (rows D3), 3.5 (row D3), 3.6, 3.8 (NM: the round cavern, the kennel row, the Fetch exit), 3.9
 * (the G1 `leap` drill row, tags 4 / 5). Tested by tests/brd_grebmar_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsGrebmar (210780-210809), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/grebmar.py
 *   Tuning         NH<> constants straight from the build spec (normal / heroic); the unset "stock scaled" cells
 *                  (Pummel, the hounds' Rend and melee) are this WP's defaults (report, designer questions)
 *   Commands       GR2's rotation: three commands, never the same one twice in a row
 *   Horn           GR1: hounds per blow against the pack cap
 *   Leap           GR3 / GR4: the lock, the take-off and the landing; which hounds draw a line
 *   Geometry       the pack at his feet, the two kennel doors, the Fetch exit, the Heel ring
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_GREBMAR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_GREBMAR_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstdint>

namespace BrdGrebmar
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsGrebmar;

    enum GrebmarSpells : std::uint32_t
    {
        SPELL_GR_WHISTLE_SIC_EM     = kSpellSlice.first + 0,    // 210780 GR2 the 2 s whistle, "Sic 'em!" (Physical)
        SPELL_GR_WHISTLE_FETCH      = kSpellSlice.first + 1,    // 210781 GR2 the 2 s whistle, "Fetch!" (Nature)
        SPELL_GR_WHISTLE_HEEL       = kSpellSlice.first + 2,    // 210782 GR2 the 2 s whistle, "Heel!" (Arcane)
        SPELL_GR_SIC_EM_MARK        = kSpellSlice.first + 3,    // 210783 GR3 the mark on the player during the whistle
        SPELL_GR_SIC_EM_LANDING     = kSpellSlice.first + 4,    // 210784 GR3 the landing circle's hit (resolve copy)
        SPELL_GR_SIC_EM_LEAP        = kSpellSlice.first + 5,    // 210785 GR4 a leap line's hit (resolve copy)
        SPELL_GR_LEAP_LOOK          = kSpellSlice.first + 6,    // 210786 look: Leap, a hound taking off
        SPELL_GR_SNATCHED           = kSpellSlice.first + 7,    // 210787 GR5 -30% damage and healing done
        SPELL_GR_FETCH_RUNNER       = kSpellSlice.first + 8,    // 210788 GR5 the runner's mark (the kill order key)
        SPELL_GR_LICK_WOUNDS        = kSpellSlice.first + 9,    // 210789 GR6 the 5 s channel (heal, +30% taken)
        SPELL_GR_FRENZY             = kSpellSlice.first + 10,   // 210790 GR6 +30% attack speed, 15 s, an Enrage
        SPELL_GR_FRENZY_FLASH       = kSpellSlice.first + 11,   // 210791 look: Frenzy's flash on the application
        SPELL_GR_KENNEL_HORN        = kSpellSlice.first + 12,   // 210792 look: the horn on Grebmar (sound + anim)
        SPELL_GR_KENNEL_HORN_BURST  = kSpellSlice.first + 13,   // 210793 look: the horn burst on a hound at its door
        SPELL_GR_RELEASE_THE_HOUNDS = kSpellSlice.first + 14,   // 210794 look: the 30% finale's summoning bark
        SPELL_GR_REND               = kSpellSlice.first + 15,   // 210795 the hounds' bleed (stock Rend rescaled)
        SPELL_GR_PUMMEL             = kSpellSlice.first + 16,   // 210796 GR7 Pummel (stock 15615 rescaled)
        // 210797-210809 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_GR_PUMMEL;
    static_assert(kLastSpell <= kSpellSlice.last, "Grebmar's spells must stay in his slice");

    // GR8: the stock Bloodlust 21049 (+30% attack speed, 30 s, Magic), kept as is (it deals no damage, so nothing to
    // rescale) and moved to the 30% finale. On the purge list.
    inline constexpr std::uint32_t SPELL_STOCK_BLOODLUST = 21049;

    // Registry tags. The leap pair matches the G1 drill's `leap` row (BM MechanicDrill.h kBrdTagLeapLine 4 and
    // kBrdTagLeapLanding 5): the sweep's DRILL_BARS gate those two tags, the fight's ledger keys on the same.
    enum GrebmarTags : std::uint32_t
    {
        TAG_GR_LEAP_LINE    = 4,    // GR4
        TAG_GR_LEAP_LANDING = 5,    // GR3
    };

    // creature_text groups of 9319 (S1 "Text"; S0 range 0-6, all new). Yells; the horn is a boss emote (type 41).
    enum GrebmarTexts : std::uint8_t
    {
        SAY_GREBMAR_PULL    = 0,    // "Escaped prisoners! My pups are hungry!"
        SAY_GREBMAR_SIC_EM  = 1,    // GR2 / GR3
        SAY_GREBMAR_FETCH   = 2,    // GR2 / GR5
        SAY_GREBMAR_HEEL    = 3,    // GR2 / GR6
        SAY_GREBMAR_FINALE  = 4,    // GR8 "Release the hounds! All of them!"
        EMOTE_GREBMAR_HORN  = 5,    // GR1 "%s blows his kennel horn!"
        SAY_GREBMAR_DEATH   = 6,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // GR2 the commands
    // ----------------------------------------------------------------------------------------------------------------
    enum class Command : std::uint8_t
    {
        SicEm = 0,
        Fetch = 1,
        Heel = 2,
    };
    inline constexpr std::uint8_t kCommandCount = 3;

    // Each command has its own whistle spell, each in its own school: a kick locks only the kicked command's school,
    // so the heroic second whistle 2.5 s later (always another command) is never refused by the first one's lockout.
    inline constexpr std::uint32_t WhistleSpell(Command c)
    {
        switch (c)
        {
            case Command::SicEm: return SPELL_GR_WHISTLE_SIC_EM;
            case Command::Fetch: return SPELL_GR_WHISTLE_FETCH;
            case Command::Heel:  return SPELL_GR_WHISTLE_HEEL;
        }
        return SPELL_GR_WHISTLE_SIC_EM;
    }

    inline constexpr std::uint8_t CommandText(Command c)
    {
        switch (c)
        {
            case Command::SicEm: return SAY_GREBMAR_SIC_EM;
            case Command::Fetch: return SAY_GREBMAR_FETCH;
            case Command::Heel:  return SAY_GREBMAR_HEEL;
        }
        return SAY_GREBMAR_SIC_EM;
    }

    inline constexpr char const* CommandName(Command c)
    {
        switch (c)
        {
            case Command::SicEm: return "sic-em";
            case Command::Fetch: return "fetch";
            case Command::Heel:  return "heel";
        }
        return "?";
    }

    // The command a whistle spell names (false: not a whistle).
    inline constexpr bool CommandOfSpell(std::uint32_t spellId, Command& out)
    {
        for (std::uint8_t i = 0; i < kCommandCount; ++i)
            if (WhistleSpell(static_cast<Command>(i)) == spellId)
            {
                out = static_cast<Command>(i);
                return true;
            }
        return false;
    }

    // The first command of a pull: any of the three (`roll` taken modulo 3).
    inline constexpr Command FirstCommand(std::uint32_t roll)
    {
        return static_cast<Command>(roll % kCommandCount);
    }

    // The next command: one of the two others (`roll` taken modulo 2), never `last` again (S1 GR2 "never the same
    // one twice in a row"). A kicked whistle still counts as named: the next one differs from it too.
    inline constexpr Command NextCommand(Command last, std::uint32_t roll)
    {
        std::uint32_t const step = 1u + roll % 2u;
        return static_cast<Command>((static_cast<std::uint32_t>(last) + step) % kCommandCount);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S1 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kLandingPct{ 30.f, 45.f };       // GR3
    inline constexpr NH<float> kLeapLinePct{ 15.f, 25.f };      // GR4
    // Unset in the spec ("stock scaled", gaps 8 / 36): this WP's defaults, designer questions in the report.
    inline constexpr NH<float> kPummelPct{ 10.f, 15.f };        // GR7, on the caster it hits
    inline constexpr NH<float> kRendPctPerTick{ 1.f, 1.5f };    // the hounds' bleed, every 3 s for 15 s

    inline constexpr std::int32_t kSnatchedPct = 30;            // GR5: -30% damage and healing done
    inline constexpr std::int32_t kLickHealPctPerSec = 5;       // GR6: 5% of the hound's health a second
    inline constexpr std::int32_t kLickDamageTakenPct = 30;     // GR6: +30% damage taken while it licks
    inline constexpr std::int32_t kFrenzyHastePct = 30;         // GR6: +30% attack speed
    inline constexpr float kFinalePct = 30.f;                   // GR8: at 30% health

    // Health at 5 players (handoff 3.6; heroic by WP-H's overrides). Grebmar's own are the S0 boss columns.
    inline constexpr NH<std::uint32_t> kHoundHealth{ 5000, 9000 };

    // Kick priorities (the interrupt list): the whistle is a reward on normal, expected on heroic (S1 Heroic). Lick
    // Wounds is the stop list's (a reward on both).
    inline constexpr std::uint8_t kWhistleKickPriorityNormal = 2;
    inline constexpr std::uint8_t kWhistleKickPriorityHeroic = 3;
    inline constexpr std::uint8_t kLickKickPriority = 2;
    // Kill order: the Fetch runner first, then the pack (cleaved), then Grebmar (0).
    inline constexpr std::int8_t kRunnerPriority = 3;
    inline constexpr std::int8_t kHoundPriority = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms). The pull is t = 0.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kWhistleFirstMs = 8000;              // GR2
    inline constexpr NH<std::uint32_t> kWhistleEveryMs{ 12000, 10000 }; // GR2 (from the whistle's start)
    inline constexpr std::uint32_t kWhistleCastMs = 2000;
    // Heroic below 30%: two whistles back to back, the second starting this long after the first (handoff 8 #5:
    // the gap is unset in the spec; 2.5 s). The second starts 0.5 s after the first ends: one interrupt fits.
    inline constexpr std::uint32_t kDoubleWhistleGapMs = 2500;
    static_assert(kDoubleWhistleGapMs > kWhistleCastMs, "the second whistle starts after the first ends");
    static_assert(kDoubleWhistleGapMs + kWhistleCastMs < kWhistleEveryMs.heroic,
        "a double whistle is over before the next one is due");

    inline constexpr std::uint32_t kHornFirstMs = 30000;        // GR1
    inline constexpr std::uint32_t kHornEveryMs = 40000;

    inline constexpr std::uint32_t kLeapMs = 1500;              // GR3 / GR4: the lock to the landing
    inline constexpr std::uint32_t kLeapFlightMs = 500;         // the hounds take off this long before the landing
    inline constexpr std::uint32_t kSicEmMarkMs = kWhistleCastMs + kLeapMs;     // the mark: whistle + leap warning

    inline constexpr std::uint32_t kFetchWindowMs = 15000;      // GR5: kill the runner within 15 s
    inline constexpr std::uint32_t kSnatchedMs = 30000;         // GR5: 30 s (refreshed when the runner escapes)

    inline constexpr std::uint32_t kHeelRunMs = 3000;           // GR6: the run back; it licks where it is after this
    inline constexpr std::uint32_t kLickMs = 5000;              // GR6
    inline constexpr std::uint32_t kLickTickMs = 1000;
    inline constexpr std::uint32_t kFrenzyMs = 15000;
    inline constexpr float kLickMovedYd = 2.f;                  // knocked or gripped this far off: the lick stops

    inline constexpr std::uint32_t kPummelFirstMinMs = 5000;    // GR7 (stock event 105: 5-7 s, then 12-14 s)
    inline constexpr std::uint32_t kPummelFirstMaxMs = 7000;
    inline constexpr std::uint32_t kPummelEveryMinMs = 12000;
    inline constexpr std::uint32_t kPummelEveryMaxMs = 14000;
    inline constexpr float kPummelRangeYd = 5.f;
    inline constexpr std::uint32_t kPummelLockoutMs = 5000;     // the stock 5 s school lockout

    inline constexpr std::uint32_t kRendEveryMinMs = 7000;      // the hounds' Rend (stock 8921: 7-11 s, 0-5 yd)
    inline constexpr std::uint32_t kRendEveryMaxMs = 11000;
    inline constexpr std::uint32_t kRendMs = 15000;
    inline constexpr std::uint32_t kRendTickMs = 3000;
    inline constexpr float kRendRangeYd = 5.f;

    inline constexpr std::uint32_t kRetryMs = 500;              // a due move that cannot start yet

    // ----------------------------------------------------------------------------------------------------------------
    // GR1 the pack and the horn
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kPackAtPull = 4;             // GR1 / The Pack: 4 at his feet
    inline constexpr NH<std::uint32_t> kHornHounds{ 2, 3 };     // per blow
    inline constexpr NH<std::uint32_t> kPackCap{ 6, 8 };        // never more alive at once

    // Hounds a blow brings with `alive` hounds up (the Fetch runner counts: it is still alive).
    inline constexpr std::uint32_t HornSummons(std::uint32_t alive, bool heroic)
    {
        std::uint32_t const cap = kPackCap(heroic);
        if (alive >= cap)
            return 0;
        return std::min(kHornHounds(heroic), cap - alive);
    }
    static_assert(kPackAtPull <= kPackCap.normal, "the pull's pack fits the cap");

    // ----------------------------------------------------------------------------------------------------------------
    // GR3 / GR4 Sic 'em
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kLandingRadius = 5.f;
    inline constexpr float kLeapLineWidth = 3.f;
    inline constexpr float kMinLineYd = 2.f;        // a hound this close to the spot draws no line (it just lands)

    struct LeapPlan
    {
        // From the lock (the whistle's end): the hounds take off, then land as the zones resolve.
        static constexpr std::uint32_t TakeOffMs() { return kLeapMs - kLeapFlightMs; }
        static constexpr std::uint32_t LandMs() { return kLeapMs; }
    };
    static_assert(LeapPlan::TakeOffMs() < LeapPlan::LandMs(), "a hound takes off before it lands");

    // A hound draws a leap line when it is far enough from the landing spot for a line to mean anything.
    inline constexpr bool DrawsLine(float distanceYd)
    {
        return distanceYd >= kMinLineYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry [navmesh estimate] (handoff 3.8, NAVMESH 1.3; [db] where marked). Axes: +x north, +y west.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kFloorZ = -84.4f;

    // The pack at his feet: four of the five stock Bloodhound spots the SQL rev deletes [db] (46271, 46273, 46281,
    // and 46297 / 46298 merged into one).
    inline constexpr std::array<Point3, kPackAtPull> kPackSpots{ {
        { 612.4f, -173.6f, -84.4f },
        { 604.8f, -177.6f, -84.4f },
        { 606.2f, -168.2f, -84.4f },
        { 610.7f, -178.0f, -84.5f },
    } };

    // GR1: the two kennel doors on the cell row (gap 11); the hounds bound in from there.
    inline constexpr std::array<Point3, 2> kHornEntries{ {
        { 581.4f, -175.4f, -84.4f },
        { 581.1f, -190.5f, -84.4f },
    } };

    // The hound i of a blow comes out of door i % 2.
    inline constexpr Point3 HornEntry(std::uint32_t index)
    {
        return kHornEntries[index % kHornEntries.size()];
    }

    // GR5: the runner's way out, the farthest rim cell along the cell row (45 yd from his spawn).
    inline constexpr Point3 kFetchExit{ 574.7f, -196.6f, -84.4f };

    // GR3/GR5/GR6: a hound takes an order only while alive, fighting (not holding, leaping, licking or running) and
    // not under crowd control (R-1-A m2: a feared, trapped, stunned, rooted or banished hound ignores him; CC is the
    // group's answer to an order, and an order would wipe the CC's own movement).
    inline constexpr bool HoundObeys(bool alive, bool fighting, bool crowdControlled)
    {
        return alive && fighting && !crowdControlled;
    }

    // GR6: the Heel ring around him (hound i of n at its own bearing).
    inline constexpr float kHeelRadius = 3.f;

    inline Vec2 HeelSpot(Vec2 center, std::uint32_t index, std::uint32_t count)
    {
        float const n = static_cast<float>(std::max<std::uint32_t>(count, 1));
        float const bearing = 2.f * DungeonKit::kPi * static_cast<float>(index) / n;
        return DungeonKit::Advance(center, bearing, kHeelRadius);
    }
}

#endif
