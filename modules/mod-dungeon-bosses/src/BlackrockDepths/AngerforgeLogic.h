/*
 * mod-dungeon-bosses, Blackrock Depths D14:
 * General Angerforge (9033) and his squads (Squad Officer 300830, Squad Reservist 300831, Squad Medic 300832, the mole
 * machine GO 301289), the pure, host-testable part (no engine headers). Build spec S3 "General Angerforge"
 * (docs/dungeons/blackrock-depths-3-manufactory.md, AF1-AF6; rulings 52, 53, 88), handoff sections 3.4 (rows D14),
 * 3.5 (row D14), 3.6, 3.8 (NM: the hall, the four mole spots), 3.10. Tested by tests/brd_angerforge_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsAngerforge (211300-211329), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/angerforge.py
 *   Tuning         NH<> constants straight from the build spec (normal / heroic); the unset "stock rescaled" cells
 *                  (Mighty Blow, Cleave, the squad's melee) are this WP's defaults (report, designer questions)
 *   Squads         AF3: the composition of the n-th drop, the Officer cap, the spot pick (never the same twice), the
 *                  formation around the machine, the 6 yd rule that keeps the machine's collision off a player
 *   Commanding     AF4: which units the Officer shields, the pulse
 *   Medic          AF5: the heal and the cadence
 *   Grenade        AF6: how many players are marked
 *   Geometry       the four mole spots [navmesh estimate]
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_ANGERFORGE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_ANGERFORGE_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstdint>

namespace BrdAngerforge
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsAngerforge;

    enum AngerforgeSpells : std::uint32_t
    {
        SPELL_AF_MIGHTY_BLOW        = kSpellSlice.first + 0,    // 211300 AF1 the tank hit, knocked back (stock 14099)
        SPELL_AF_CLEAVE             = kSpellSlice.first + 1,    // 211301 AF2 the frontal swing (stock 20691 copy)
        SPELL_AF_COMMANDING_AURA    = kSpellSlice.first + 2,    // 211302 AF4 on each Officer: the aura itself
        SPELL_AF_COMMANDED          = kSpellSlice.first + 3,    // 211303 AF4 on a shielded add: -50% taken, no kicks
        SPELL_AF_COMMANDING_SHOUT   = kSpellSlice.first + 4,    // 211304 look: Commanding Shout, every 5 s
        SPELL_AF_HEAL               = kSpellSlice.first + 5,    // 211305 AF5 the Medic's 3 s heal on Angerforge
        SPELL_AF_GRENADE_MARK       = kSpellSlice.first + 6,    // 211306 AF6 the mark on a carrier (5 s)
        SPELL_AF_GRENADE_MARKED     = kSpellSlice.first + 7,    // 211307 AF6 a carrier's own hit (15% / 25%)
        SPELL_AF_GRENADE            = kSpellSlice.first + 8,    // 211308 AF6 the others' hit (resolve copy)
        SPELL_AF_GRENADE_LOOK       = kSpellSlice.first + 9,    // 211309 look: Iron Grenade's bomb on a carrier
        SPELL_AF_MOLE_DEPLOY_LOOK   = kSpellSlice.first + 10,   // 211310 look: the dirt burst, machine up
        SPELL_AF_MOLE_RETREAT_LOOK  = kSpellSlice.first + 11,   // 211311 look: the burst where it goes down again
        // 211312-211329 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_AF_MOLE_RETREAT_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "Angerforge's spells must stay in his slice");

    // The Medic keeps the stock Mind Blast 15587 (S3 "Implementation": "keeps Mind Blast"): 139-161 Shadow, a 1.5 s
    // cast, no damage to rescale (a stock spell kept; DD scales it on heroic).
    inline constexpr std::uint32_t SPELL_STOCK_MIND_BLAST = 15587;

    // Registry tag of the grenade's circles (per encounter; the spec has no drill row for it).
    enum AngerforgeTags : std::uint32_t
    {
        TAG_AF_GRENADE = 1,
        TAG_AF_COMMANDING_RING = 2,
    };

    // creature_text groups of 9033 (S3 "Text"; S0 range 0-3, all new). The grenade is a boss emote (type 41).
    enum AngerforgeTexts : std::uint8_t
    {
        SAY_AF_PULL         = 0,    // "Intruders in the Shadowforge! To arms!"
        SAY_AF_REINFORCE    = 1,    // AF3 "Reinforcements, up from below!"
        EMOTE_AF_GRENADE    = 2,    // AF6 "%s lobs a Fireburst Grenade at $n!"
        SAY_AF_DEATH        = 3,    // "The Emperor... will avenge..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S3 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    // AF6 (the spec's numbers): the carrier's own hit and the hit on everyone else within the ring, Weakened.
    inline constexpr NH<float> kGrenadeMarkedPct{ 15.f, 25.f };
    inline constexpr NH<float> kGrenadeOthersPct{ 25.f, 40.f };
    inline constexpr NH<std::uint32_t> kGrenadeCount{ 2, 3 };
    inline constexpr float kGrenadeRadius = 8.f;
    // The marks never go on the tank (orchestrator default 2026-11-17, R-2-A designer question 1: the 2026-11-14
    // rule's exception, an 8 yd Spread on the tank pushes the melee off him); a tank alone in the fight is still
    // marked.
    inline constexpr bool kGrenadeMarksTank = false;

    // Unset in the spec ("stock rescaled", gaps 8 / 36): this WP's defaults, designer questions in the report. Mighty
    // Blow is the tank's swing-class hit (20-30% of the tank row, the BRS convention), Cleave a group pulse on up to
    // five (10-15%).
    inline constexpr NH<float> kMightyBlowPct{ 25.f, 30.f };
    inline constexpr NH<float> kCleavePct{ 12.f, 15.f };
    inline constexpr std::uint32_t kCleaveMaxTargets = 5;       // the stock chain of 5

    // Health at 5 players (handoff 3.6). Angerforge's own is the S0 boss column (150k normal, WP-H's 210k heroic); the
    // squad's heroic health is WP-H's kit table.
    inline constexpr NH<std::uint32_t> kOfficerHealth{ 10000, 15000 };
    inline constexpr NH<std::uint32_t> kReservistHealth{ 3000, 4500 };
    inline constexpr NH<std::uint32_t> kMedicHealth{ 5000, 7500 };

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms). The pull is t = 0.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kMightyBlowFirstMs = 8000;       // AF1 (stock 14099: 8 s, then 18 s)
    inline constexpr std::uint32_t kMightyBlowEveryMs = 18000;
    inline constexpr std::uint32_t kCleaveFirstMs = 16000;          // AF2 (stock 20691: 16 s, then 9 s)
    inline constexpr std::uint32_t kCleaveEveryMs = 9000;

    inline constexpr std::uint32_t kSquadFirstMs = 10000;           // AF3
    inline constexpr NH<std::uint32_t> kSquadEveryMs{ 30000, 25000 };
    inline constexpr std::uint32_t kRumbleMs = 2000;                // the warning: the yell and the dirt burst
    inline constexpr std::uint32_t kMachineWaitMs = 3000;           // the machine stands this long, then goes down
    inline constexpr std::uint32_t kMachineBackstopSec = 12;        // the GO's own despawn if the script never does
    inline constexpr std::uint32_t kCapRetryMs = 1000;              // a drop held back by the Officer cap tries again

    inline constexpr std::uint32_t kGrenadeFirstMs = 15000;         // AF6
    inline constexpr NH<std::uint32_t> kGrenadeEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kGrenadeWarnMs = 5000;           // the mark
    inline constexpr std::uint32_t kGrenadeLookLeadMs = 600;        // the bomb is thrown this long before it resolves
    static_assert(kGrenadeWarnMs < kGrenadeEveryMs.heroic, "a grenade is over before the next one is due");
    static_assert(kGrenadeLookLeadMs < kGrenadeWarnMs, "the bomb is thrown after the mark goes up");

    inline constexpr std::uint32_t kRetryMs = 500;                  // a due swing that cannot start yet

    // ----------------------------------------------------------------------------------------------------------------
    // AF3 the squads
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kOfficerCap = 2;                 // no drill while this many Officers live

    struct SquadPlan
    {
        std::uint32_t officers = 0;
        std::uint32_t reservists = 0;
        std::uint32_t medics = 0;

        constexpr std::uint32_t Total() const { return officers + reservists + medics; }
    };

    // The n-th squad of the fight (0-based). Normal: an Officer and 2 Reservists; every other squad swaps a Reservist
    // for a Medic (the second, the fourth ...). Heroic: an Officer, 2 Reservists and a Medic every time.
    inline constexpr SquadPlan SquadFor(std::uint32_t index, bool heroic)
    {
        if (heroic)
            return { 1, 2, 1 };
        return (index % 2 == 0) ? SquadPlan{ 1, 2, 0 } : SquadPlan{ 1, 1, 1 };
    }

    // A drill may start only while fewer than kOfficerCap Officers live (the squad then waits and the timer is not
    // restarted).
    inline constexpr bool DropAllowed(std::uint32_t officersAlive)
    {
        return officersAlive < kOfficerCap;
    }

    // The next drop's timer: the first at kSquadFirstMs, then every kSquadEveryMs from the previous drop's start.
    inline constexpr std::uint32_t NextSquadDelayMs(std::uint32_t squadsSoFar, bool heroic)
    {
        return squadsSoFar == 0 ? kSquadFirstMs : kSquadEveryMs(heroic);
    }

    // The entries a squad drops, Officer first (the formation puts the first one in the middle), then the Medic, then
    // the Reservists.
    inline constexpr std::uint32_t kSquadMaxSize = 4;
    inline constexpr std::array<std::uint32_t, kSquadMaxSize> SquadEntries(SquadPlan const& plan)
    {
        std::array<std::uint32_t, kSquadMaxSize> out{};
        std::uint32_t n = 0;
        for (std::uint32_t i = 0; i < plan.officers && n < kSquadMaxSize; ++i)
            out[n++] = BlackrockDepthsRework::NPC_BRD_SQUAD_OFFICER;
        for (std::uint32_t i = 0; i < plan.medics && n < kSquadMaxSize; ++i)
            out[n++] = BlackrockDepthsRework::NPC_BRD_SQUAD_MEDIC;
        for (std::uint32_t i = 0; i < plan.reservists && n < kSquadMaxSize; ++i)
            out[n++] = BlackrockDepthsRework::NPC_BRD_SQUAD_RESERVIST;
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry [navmesh estimate] (handoff 3.8, NAVMESH 3.1; z -59.8 on the whole hall). Axes: +x north, +y west.
    // ----------------------------------------------------------------------------------------------------------------

    // The four mole spots on the hall's edge, clear of the drop behind him (NM: clearances 4.5, 4.5, 5.9 and 4.6 yd for
    // the machine's 9 yd footprint, 23-44 yd from him). Gap 26.
    inline constexpr std::uint32_t kMoleSpotCount = 4;
    inline constexpr std::array<Point3, kMoleSpotCount> kMoleSpots{ {
        { 680.8f, -9.8f, -59.8f },      // M1 north-west corner
        { 681.2f, 54.8f, -59.8f },      // M2 north-east corner
        { 662.2f, 42.2f, -59.8f },      // M3 east flank
        { 674.8f, 13.2f, -59.8f },      // M4 north-center-left
    } };
    inline constexpr std::uint32_t kNoSpot = 0xFFu;
    // The pick's roll is `urand(0, kSpotRolls - 1)`: 12 divides by 4 (the first drop) and by 3 (every other), so every
    // spot is equally likely both times.
    inline constexpr std::uint32_t kSpotRolls = 12;
    static_assert(kSpotRolls % kMoleSpotCount == 0 && kSpotRolls % (kMoleSpotCount - 1) == 0,
        "the spot roll divides evenly by 4 and by 3");

    // The spot of a drop: one of the three others, never the one used last (a `roll` taken modulo 3; none yet: any of
    // the four). The spots sit 15-45 yd from each other, so a repeat would put two squads on one flank.
    inline constexpr std::uint32_t NextSpot(std::uint32_t last, std::uint32_t roll)
    {
        if (last >= kMoleSpotCount)
            return roll % kMoleSpotCount;
        std::uint32_t index = roll % (kMoleSpotCount - 1);
        if (index >= last)
            ++index;
        return index;
    }

    // The machine is a GO with a collision model about 7 yd square (display 7510 at 0.6): never put it on a player. A
    // player within this distance of the spot at the landing gives the squad its dirt burst and no machine (§7 #13).
    inline constexpr float kMachineClearYd = 6.f;
    inline constexpr bool MachineMayStand(float nearestPlayerYd)
    {
        return nearestPlayerYd >= kMachineClearYd;
    }

    // The formation: slot i (0 = the Officer) of a squad stands on a ring around the machine, on the side that faces
    // him (the hall's inside), the slots fanned 40 degrees apart: 0, -40, +40, -80 ...
    inline constexpr float kSlotRadiusYd = 5.5f;
    inline constexpr float kSlotStepDeg = 40.f;

    inline constexpr float SlotAngleDeg(std::uint32_t index)
    {
        if (index == 0)
            return 0.f;
        float const rank = static_cast<float>((index + 1) / 2);
        return (index % 2 == 1 ? -1.f : 1.f) * rank * kSlotStepDeg;
    }

    // The slot's point: `towardBearing` is the bearing from the spot to the hall's middle (to Angerforge).
    inline Vec2 SlotPoint(Vec2 spot, float towardBearing, std::uint32_t index)
    {
        float const bearing = towardBearing + SlotAngleDeg(index) * DungeonKit::kPi / 180.f;
        return DungeonKit::Advance(spot, bearing, kSlotRadiusYd);
    }

    // The four stock Reservists (8901) stand 4-5 yd from him; the pull and the kill order take the ones within this.
    inline constexpr float kStockReservistRadiusYd = 15.f;

    // ----------------------------------------------------------------------------------------------------------------
    // AF4 Commanding Aura
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kCommandingRadiusYd = 15.f;
    inline constexpr std::int32_t kCommandedDamageTakenPct = -50;
    inline constexpr std::uint32_t kCommandedMs = 2500;             // the shield lingers this long past the last pulse
    inline constexpr std::uint32_t kCommandingPulseMs = 1000;
    inline constexpr std::uint32_t kCommandingShoutEveryMs = 5000;  // the look (V-1: re-cast every 5 s)
    inline constexpr std::uint32_t kCommandingRingMs = 20000;       // the orange ring is a decoy re-registered at this
    static_assert(kCommandedMs > kCommandingPulseMs, "the shield survives until the next pulse");

    // Who an Officer shields: the other adds (the squad's three, the other Officer and the stock Reservists). Never
    // Angerforge (designer: with one tank nobody can drag an Officer away, so the Officer is the priority target).
    inline constexpr bool IsShielded(std::uint32_t entry)
    {
        return entry == BlackrockDepthsRework::NPC_BRD_SQUAD_OFFICER
            || entry == BlackrockDepthsRework::NPC_BRD_SQUAD_RESERVIST
            || entry == BlackrockDepthsRework::NPC_BRD_SQUAD_MEDIC
            || entry == BlackrockDepthsRework::NPC_ANVILRAGE_RESERVIST;
    }

    // Whether a unit of `entry` at `distanceYd` from an Officer gets its shield (`isSelf`: the Officer itself).
    inline constexpr bool ShieldReaches(std::uint32_t entry, bool isSelf, float distanceYd)
    {
        return !isSelf && IsShielded(entry) && distanceYd <= kCommandingRadiusYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AF5 the Medic
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kHealCastMs = 3000;
    inline constexpr std::uint32_t kHealFirstMs = 6000;
    inline constexpr std::uint32_t kHealEveryMs = 12000;
    inline constexpr std::int32_t kHealPctOfBoss = 5;               // of Angerforge's maximum health
    inline constexpr float kHealMinMissingPct = 5.f;                // no heal is cast at him while he misses less
    inline constexpr std::uint32_t kMindBlastMinMs = 3000;          // the stock row: every 3-5 s on the victim
    inline constexpr std::uint32_t kMindBlastMaxMs = 5000;
    inline constexpr float kMedicRangeYd = 28.f;                    // it stands off and casts
    inline constexpr float kMedicHealRangeYd = 40.f;                // Heal 211305's range (angerforge.py)
    // R-2-A MI-1: it stands off its own victim, which can be a ranged player far from him; past this distance from
    // Angerforge (or out of his sight) it walks back to kMedicRangeYd of him, so the heal can always reach.
    inline constexpr float kMedicLeashYd = 36.f;
    static_assert(kMedicRangeYd < kMedicLeashYd && kMedicLeashYd < kMedicHealRangeYd,
        "the Medic closes in before Angerforge leaves its heal's range, and stops well inside it");

    // Must the Medic walk back toward Angerforge? (its distance to him, whether it sees him)
    inline constexpr bool MedicMustCloseIn(float distanceToBossYd, bool bossInSight)
    {
        return !bossInSight || distanceToBossYd > kMedicLeashYd;
    }

    // Kick priorities (the interrupt list): the heal is a reward on normal, expected on heroic (S3 Heroic).
    inline constexpr std::uint8_t kHealKickPriorityNormal = 2;
    inline constexpr std::uint8_t kHealKickPriorityHeroic = 3;

    // Does he miss enough health for a heal to be worth the bar? (his current health percent)
    inline constexpr bool HealWanted(float bossHealthPct)
    {
        return 100.f - bossHealthPct >= kHealMinMissingPct;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Kill order (S3 "Boss data": Officer, Medic, Reservist, Angerforge): the descriptor's target priorities.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::int8_t kOfficerPriority = 4;
    inline constexpr std::int8_t kMedicPriority = 3;
    inline constexpr std::int8_t kReservistPriority = 2;
    inline constexpr std::int8_t kAngerforgePriority = 0;
    static_assert(kOfficerPriority > kMedicPriority && kMedicPriority > kReservistPriority
        && kReservistPriority > kAngerforgePriority, "kill order: Officer, Medic, Reservist, Angerforge");

    // ----------------------------------------------------------------------------------------------------------------
    // AF6 the grenade
    // ----------------------------------------------------------------------------------------------------------------
    // How many players one throw marks: the spec's count, never more than there are players to mark.
    inline constexpr std::uint32_t GrenadeMarks(bool heroic, std::uint32_t playersInFight)
    {
        return std::min<std::uint32_t>(kGrenadeCount(heroic), playersInFight);
    }

    // The pick rule for the marks: not the tank (kGrenadeMarksTank). No tankIfAlone: a distinct pick of 3 would fill
    // the last mark with the tank in a small group; the AI marks the tank (GrenadeTankAloneRule, one mark) only when
    // this rule finds nobody.
    inline DungeonKit::PickRule GrenadePickRule()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = !kGrenadeMarksTank;
        return rule;
    }

    inline DungeonKit::PickRule GrenadeTankAloneRule()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return rule;
    }
}

#endif
