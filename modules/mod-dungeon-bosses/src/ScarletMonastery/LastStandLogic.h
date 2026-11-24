/*
 * mod-dungeon-bosses, Scarlet Monastery D13:
 * The Last Stand: Scarlet Commander Mograine (3976) and the Crusade's companies (300950-300955), the pure,
 * host-testable part (no engine headers). Build spec CATH "The Last Stand" (docs/dungeons/
 * scarlet-monastery-4-cathedral.md, LS0-LS7; HUB rulings 45, 46, 54), handoff sections 3.5 (row D13), 3.6, 3.8 (NM:
 * the nave, the crossing, the arm ends), 7 #19 A (the nave cleared), #20 A (the chest), #33 A (the charge lines at the
 * arm mouths, LOS-clipped). Tested by tests/sm_last_stand_test.cpp; the DT twin is apps/dbc-tools
 * source/npcs/scarlet_monastery/last_stand.py.
 *
 *   Spells     the WP's ids, inside kSpellsLastStand (213100-213149)
 *   Tuning     NH<> constants straight from the build spec (normal / heroic)
 *   Companies  LS1 the three companies (heroic: five units each, plus LS7 the Last Reserve at Mograine's 50%), their
 *              arms, the call clock (the current company falls, or 30 / 25 s after it arrived), the descent and the
 *              fall rules
 *   Picks      the Greater Heal target (the most hurt), the healer's turn, the arrival target (the tank first), the
 *              heroic charge targets (in line of sight of the arm mouth)
 *   Geometry   the arm ends, the arm mouths, the crossing, the chest at the altar steps, the stand's floor (landing,
 *              nave, crossing, altar platform) and the wipe watch's zone
 *
 * Compass names follow the build spec, whose nave runs "east" from the Chapel Door: its north transept arm is the +y
 * arm (the NAVMESH report's "west", y 1430-1465) and its south arm the -y arm (y 1333-1366, Fairbanks's side). Points
 * are [navmesh estimate] unless marked [db].
 */

#ifndef MOD_DUNGEON_BOSSES_SM_LAST_STAND_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_LAST_STAND_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace SmLastStand
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;
    using ScarletMonasteryRework::Point4;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsLastStand;

    enum LastStandSpells : std::uint32_t
    {
        SPELL_LS_HAMMER_THROW           = kSpellSlice.first + 0,    // 213100 LS4 look: the thrown hammer (missile)
        SPELL_LS_HAMMER_HIT             = kSpellSlice.first + 1,    // 213101 LS4 others in the circle (resolve copy)
        SPELL_LS_HAMMER_STRIKE          = kSpellSlice.first + 2,    // 213102 LS4 the marked player's own hit (refflat)
        SPELL_LS_HAMMER_STUN            = kSpellSlice.first + 3,    // 213103 LS4 the 2 s stun (everyone in the circle)
        SPELL_LS_DIVINE_STORM_CAST      = kSpellSlice.first + 4,    // 213104 LS5 the 2 s wind-up bar
        SPELL_LS_DIVINE_STORM_HIT       = kSpellSlice.first + 5,    // 213105 LS5 the whirl on the others (resolve copy)
        SPELL_LS_DIVINE_STORM_TANK      = kSpellSlice.first + 6,    // 213106 LS5 the tank's own hit (refflat, tank row)
        SPELL_LS_DEVOTION_AURA          = kSpellSlice.first + 7,    // 213107 LS1a the buff on a member within 15 yd
        SPELL_LS_DEVOTION_PULSE         = kSpellSlice.first + 8,    // 213108 LS1a look: the Captain's rune on arrival
        SPELL_LS_CONSECRATION_HIT       = kSpellSlice.first + 9,    // 213109 LS1b a Monk's ground tick (resolve copy)
        SPELL_LS_CONSECRATION_GROUND    = kSpellSlice.first + 10,   // 213110 LS1b look: the ground (dynamic object)
        SPELL_LS_FIREBALL               = kSpellSlice.first + 11,   // 213111 LS1c the 2.5 s Fireball (refflat)
        SPELL_LS_PURIFYING_FLAME_CAST   = kSpellSlice.first + 12,   // 213112 LS2 the 2.5 s cast at a player's spot
        SPELL_LS_PURIFYING_FLAME_HIT    = kSpellSlice.first + 13,   // 213113 LS2 the circle's hit (resolve copy)
        SPELL_LS_PURIFYING_FLAME_FIRE   = kSpellSlice.first + 14,   // 213114 LS2 the fire's ticks (resolve copy)
        SPELL_LS_PURIFYING_FLAME_POOL   = kSpellSlice.first + 15,   // 213115 LS2 look: the fire, 6 s (normal)
        SPELL_LS_PURIFYING_FLAME_POOL_H = kSpellSlice.first + 16,   // 213116 LS2 look: the fire, 10 s (heroic)
        SPELL_LS_GREATER_HEAL           = kSpellSlice.first + 17,   // 213117 LS3 normal: 3 s, 30% of the target
        SPELL_LS_GREATER_HEAL_H         = kSpellSlice.first + 18,   // 213118 LS3 heroic: the 3 s bar (a DUMMY)
        SPELL_LS_GREATER_HEAL_PULSE     = kSpellSlice.first + 19,   // 213119 LS3 heroic missed: 50% on every member
        SPELL_LS_CHARGE_HIT             = kSpellSlice.first + 20,   // 213120 LS6 the charge line (resolve copy)
        SPELL_LS_CHARGE_LOOK            = kSpellSlice.first + 21,   // 213121 LS6 look: Charge's run
        // 213122-213149 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_LS_CHARGE_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "the Last Stand's spells must stay in its slice");

    // The stock spells the build spec keeps (CATH "Stock kit": not rescaled, so cast as they are; rule 15 covers only
    // rescaled ones). Hammer of Justice 5589 is a live player override: never cast here (the thrown copy is LS4).
    enum LastStandStockSpells : std::uint32_t
    {
        SPELL_CRUSADER_STRIKE   = 14518,    // Mograine, on the tank
        SPELL_RETRIBUTION_AURA  = 8990,     // Mograine, on the pull (and when he rises: D14)
        SPELL_HOLY_STRIKE       = 17143,    // the Champions
        SPELL_KICK              = 11978,    // the Monks, on a casting victim
        SPELL_THRASH            = 3417,     // the Monks' passive extra attacks
        SPELL_FIRE_SHIELD       = 2601,     // the Wizards, on arrival
        SPELL_POWER_WORD_SHIELD = 6066,     // the Clergy's Chaplain, on the company
        SPELL_RENEW             = 8362,     // the Chaplains and the Abbots
        SPELL_FRENZY            = 8269,     // the Abbots, at 40% health
    };
    inline constexpr std::uint32_t kStockHammerOfJustice = 5589;    // retired as his cast (CATH "New spells")

    // Registry tags (the build spec's mechanic numbers).
    enum LastStandTags : std::uint32_t
    {
        TAG_LS_CONSECRATION = 12,   // LS1b
        TAG_LS_FLAME        = 2,    // LS2 the circle
        TAG_LS_FLAME_FIRE   = 22,   // LS2 the fire
        TAG_LS_HAMMER       = 4,    // LS4
        TAG_LS_DIVINE_STORM = 5,    // LS5
        TAG_LS_CHARGE       = 6,    // LS6
    };

    // creature_text groups of 3976 (CATH "Text"; S0 range 0-13: 0-6 stock, 7-11 this WP's, 12-13 D14's).
    enum MograineTexts : std::uint8_t
    {
        SAY_MOGRAINE_AGGRO          = 0,    // stock "Infidels! They must be purified!": his descent (or an early pull)
        SAY_MOGRAINE_KILL           = 1,    // stock "Unworthy."
        SAY_MOGRAINE_RISEN          = 2,    // stock "At your side, milady!" (D14)
        SAY_MOGRAINE_DOOR           = 7,    // LS0
        SAY_MOGRAINE_CALL_GUARD     = 8,    // company 1
        SAY_MOGRAINE_CALL_PYRE      = 9,    // company 2
        SAY_MOGRAINE_CALL_CLERGY    = 10,   // company 3
        SAY_MOGRAINE_LAST_RESERVE   = 11,   // LS7 (heroic)
    };
    inline constexpr std::uint8_t kFirstOwnText = SAY_MOGRAINE_DOOR;
    inline constexpr std::uint8_t kLastOwnText = SAY_MOGRAINE_LAST_RESERVE;

    // ----------------------------------------------------------------------------------------------------------------
    // Mograine's states (the stand, the fall, the vigil, D14's rising)
    // ----------------------------------------------------------------------------------------------------------------
    enum class MograineState : std::uint8_t
    {
        Altar,      // before the stand: on the altar steps, passive, attackable (a pull starts the stand)
        Stand,      // the companies come; he waits on the altar steps, out of combat
        Fight,      // he fights (the descent after the third company, or an early pull)
        Falling,    // fallen at 1%: he walks to his body spot before the altar, not attackable
        Fallen,     // lies before the altar (the vigil: D14's Whitemane kneels over him); a cold load with slot 5 DONE
        Risen,      // D14's finale (MograineFight.h)
    };

    inline constexpr char const* StateName(MograineState s)
    {
        switch (s)
        {
            case MograineState::Altar:   return "altar";
            case MograineState::Stand:   return "stand";
            case MograineState::Fight:   return "fight";
            case MograineState::Falling: return "falling";
            case MograineState::Fallen:  return "fallen";
            case MograineState::Risen:   return "risen";
        }
        return "?";
    }

    // Where a (re)loaded Mograine stands: lying before the altar once the Last Stand is DONE (the vigil, and after the
    // finale too), else on the altar steps.
    inline constexpr MograineState StateForStage(ScarletMonasteryRework::CathedralStage stage)
    {
        return stage == ScarletMonasteryRework::CathedralStage::Vigil
            || stage == ScarletMonasteryRework::CathedralStage::Done ? MograineState::Fallen : MograineState::Altar;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (CATH "Tuning starting points" and "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<std::uint32_t> kMograineHealth{ 55000, 250000 };    // handoff 3.6 (heroic: WP-H's override)
    inline constexpr NH<std::uint32_t> kBigMemberHealth{ 4000, 15000 };     // Champions, the Captain, Monks, Abbots
    inline constexpr NH<std::uint32_t> kSmallMemberHealth{ 3000, 12000 };   // Wizards, Chaplains

    inline constexpr NH<std::uint32_t> kCallEveryMs{ 30000, 25000 };    // LS1: the next company, after the arrival
    inline constexpr std::uint32_t kFirstCallMs = 2000;                 // after the door yell (line 7), the first call
    inline constexpr std::uint32_t kMarchGiveUpMs = 15000;              // a company that never reaches its mouth
    inline constexpr std::uint32_t kStandCompanies = 3;                 // LS1: three companies (the cap)

    inline constexpr NH<std::int32_t> kDevotionPct{ 30, 40 };           // LS1a less damage taken
    inline constexpr float kDevotionRadiusYd = 15.f;
    inline constexpr std::uint32_t kDevotionPulseMs = 1000;             // the Captain re-applies it every second
    inline constexpr std::uint32_t kDevotionAuraMs = 2500;              // the buff's own duration (DT)

    inline constexpr std::uint32_t kConsecrationFirstMs = 4000;         // LS1b: after the Monk's arrival
    inline constexpr std::uint32_t kConsecrationEveryMs = 12000;
    inline constexpr std::uint32_t kConsecrationMs = 8000;
    inline constexpr std::uint32_t kConsecrationTickMs = 1000;
    inline constexpr float kConsecrationRadiusYd = 6.f;
    inline constexpr NH<float> kConsecrationPct{ 10.f, 15.f };          // per second

    inline constexpr std::uint32_t kFireballFirstMs = 3000;             // LS1c: after the Wizard's arrival
    inline constexpr std::uint32_t kFireballEveryMs = 8000;
    inline constexpr std::uint32_t kFireballCastMs = 2500;
    inline constexpr NH<float> kFireballPct{ 15.f, 20.f };

    inline constexpr std::uint32_t kFlameFirstMs = 6000;                // LS2: after the Wizard's arrival
    inline constexpr std::uint32_t kFlameEveryMs = 12000;
    inline constexpr std::uint32_t kFlameCastMs = 2500;
    inline constexpr float kFlameRadiusYd = 5.f;
    inline constexpr NH<float> kFlamePct{ 30.f, 45.f };
    inline constexpr NH<std::uint32_t> kFlameFireMs{ 6000, 10000 };
    inline constexpr std::uint32_t kFlameFireTickMs = 1000;
    inline constexpr NH<float> kFlameFirePct{ 10.f, 15.f };             // per second

    inline constexpr std::uint32_t kGreaterHealFirstMs = 5000;          // LS3: after the company's arrival
    inline constexpr std::uint32_t kGreaterHealEveryMs = 10000;         // one cast per company
    inline constexpr std::uint32_t kGreaterHealCastMs = 3000;
    inline constexpr std::int32_t kGreaterHealPct = 30;                 // normal: the target
    inline constexpr std::int32_t kMissedHealPct = 50;                  // heroic missed: every member of the company
    inline constexpr float kHealBelowPct = 100.f;                       // a member below this is "hurt"

    inline constexpr std::uint32_t kHammerFirstMs = 8000;               // LS4: from his descent (M)
    inline constexpr std::uint32_t kHammerEveryMs = 20000;
    inline constexpr std::uint32_t kHammerWarnMs = 2000;
    inline constexpr float kHammerRadiusYd = 5.f;
    inline constexpr NH<float> kHammerPct{ 20.f, 30.f };
    inline constexpr NH<std::uint32_t> kHammerTargets{ 1, 2 };
    inline constexpr std::uint32_t kHammerStunMs = 2000;                // the loss-of-control limit (DT)
    inline constexpr float kHammerMissileSpeed = 20.f;                  // yd/s (the throw look's Speed)

    inline constexpr std::uint32_t kStormFirstMs = 12000;               // LS5: from M
    inline constexpr std::uint32_t kStormEveryMs = 15000;
    inline constexpr std::uint32_t kStormCastMs = 2000;
    inline constexpr NH<float> kStormRadiusYd{ 8.f, 10.f };
    inline constexpr NH<float> kStormPct{ 30.f, 45.f };
    inline constexpr NH<float> kStormTankPct{ 15.f, 25.f };

    inline constexpr std::uint32_t kCrusaderStrikeFirstMs = 3000;       // stock 1-5 s
    inline constexpr std::uint32_t kCrusaderStrikeEveryMs = 10000;

    inline constexpr std::uint32_t kChargeWarnMs = 2000;                // LS6 (heroic): the 2 s marker
    inline constexpr float kChargeWidthYd = 3.f;
    inline constexpr float kChargeOverrunYd = 3.f;
    inline constexpr float kChargePct = 45.f;                           // heroic only (no normal value)
    inline constexpr float kChargeSpeed = 30.f;                         // yd/s along the line

    inline constexpr float kReservePct = 50.f;                          // LS7 (heroic): Mograine's health
    inline constexpr float kFallPct = 1.f;                              // he falls at 1% (the stock fake death)

    inline constexpr std::uint32_t kHolyStrikeFirstMinMs = 1000;        // stock Champion row 1: 1-5 s, then 6-9 s
    inline constexpr std::uint32_t kHolyStrikeFirstMaxMs = 5000;
    inline constexpr std::uint32_t kHolyStrikeEveryMinMs = 6000;
    inline constexpr std::uint32_t kHolyStrikeEveryMaxMs = 9000;
    inline constexpr std::uint32_t kKickCooldownMs = 7000;              // stock Monk row 2
    inline constexpr std::uint32_t kRenewEveryMs = 8000;                // stock Chaplain / Abbot rows
    inline constexpr std::uint32_t kShieldEveryMs = 8000;               // stock Chaplain row 3
    inline constexpr std::uint32_t kFireShieldEveryMs = 30000;          // stock Wizard row 2
    inline constexpr float kFrenzyBelowPct = 40.f;                      // stock Abbot row 3
    inline constexpr std::uint32_t kRenewMissingHealth = 400;           // stock "friendly missing 400 health"

    inline constexpr std::uint32_t kRetryMs = 500;                      // a due cast that cannot start yet
    inline constexpr std::uint32_t kCompanyTickMs = 250;
    inline constexpr std::uint32_t kWipeGraceMs = 5000;                 // nobody alive on the stand's floor this long
    inline constexpr std::uint32_t kFallWalkGiveUpMs = 8000;            // the walk to his body spot
    inline constexpr std::uint32_t kKillLineCooldownMs = 8000;
    inline constexpr std::uint32_t kCorpseDespawnMs = 15000;            // a company corpse (it outlives the fire)
    inline constexpr float kArriveRangeYd = 150.f;                      // whom an arriving unit may pick
    static_assert(kCorpseDespawnMs > 10000, "a corpse outlives the longest fire it may have cast the look of");
    static_assert(kHammerStunMs <= 2000, "the 2 s loss-of-control rule");

    // Kill order (CATH "Bots"): the healers, the Captain, the Wizards, the Monks, the Champions, then Mograine (0).
    inline constexpr std::int8_t kChaplainPriority = 5;
    inline constexpr std::int8_t kAbbotPriority = 5;
    inline constexpr std::int8_t kCaptainPriority = 4;
    inline constexpr std::int8_t kWizardPriority = 3;
    inline constexpr std::int8_t kMonkPriority = 2;
    inline constexpr std::int8_t kChampionPriority = 1;
    // The tank gathers the melee (the Monks first: it drags them off their Consecration).
    inline constexpr std::int8_t kTankMonkPriority = 2;
    inline constexpr std::int8_t kTankMeleePriority = 1;
    // The interrupt list (CATH "Bots"): Greater Heal (heroic expected), Purifying Flame, Fireball.
    inline constexpr NH<std::uint8_t> kGreaterHealKickPriority{ 3, 4 };
    inline constexpr std::uint8_t kFlameKickPriority = 2;
    inline constexpr std::uint8_t kFireballKickPriority = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // LS1 the companies
    // ----------------------------------------------------------------------------------------------------------------
    enum class Company : std::uint8_t
    {
        ChapelGuard = 0,    // company 1, the north arm
        PyreBrethren = 1,   // company 2, the south arm
        Clergy = 2,         // company 3, both arms
        LastReserve = 3,    // LS7 heroic, at Mograine's 50%: as the Chapel Guard, both arms
    };
    inline constexpr std::size_t kCompanyKinds = 4;

    enum class Arm : std::uint8_t
    {
        North = 0,  // +y (y 1430-1465)
        South = 1,  // -y (y 1333-1366)
    };

    struct Member
    {
        std::uint32_t entry = 0;
        Arm arm = Arm::North;
    };

    inline constexpr char const* CompanyName(Company c)
    {
        switch (c)
        {
            case Company::ChapelGuard:  return "chapel-guard";
            case Company::PyreBrethren: return "pyre-brethren";
            case Company::Clergy:       return "clergy";
            case Company::LastReserve:  return "last-reserve";
        }
        return "?";
    }

    // The call line of each company.
    inline constexpr std::uint8_t CallLine(Company c)
    {
        switch (c)
        {
            case Company::ChapelGuard:  return SAY_MOGRAINE_CALL_GUARD;
            case Company::PyreBrethren: return SAY_MOGRAINE_CALL_PYRE;
            case Company::Clergy:       return SAY_MOGRAINE_CALL_CLERGY;
            case Company::LastReserve:  return SAY_MOGRAINE_LAST_RESERVE;
        }
        return SAY_MOGRAINE_CALL_GUARD;
    }

    // The members of a company in their marching order (CATH "Companies"): normal / heroic.
    inline std::vector<Member> Members(Company c, bool heroic)
    {
        using namespace ScarletMonasteryRework;
        std::uint32_t const champion = NPC_SM_CHAPEL_GUARD_CHAMPION;
        std::uint32_t const captain = NPC_SM_CAPTAIN_OF_THE_GUARD;
        std::uint32_t const chaplain = NPC_SM_COMPANY_CHAPLAIN;
        std::uint32_t const monk = NPC_SM_COMPANY_MONK;
        std::uint32_t const wizard = NPC_SM_COMPANY_WIZARD;
        std::uint32_t const abbot = NPC_SM_COMPANY_ABBOT;
        switch (c)
        {
            case Company::ChapelGuard:
                if (heroic)
                    return { { champion, Arm::North }, { champion, Arm::North }, { captain, Arm::North },
                        { champion, Arm::North }, { chaplain, Arm::North } };
                return { { champion, Arm::North }, { captain, Arm::North }, { champion, Arm::North },
                    { chaplain, Arm::North } };
            case Company::PyreBrethren:
                if (heroic)
                    return { { monk, Arm::South }, { monk, Arm::South }, { wizard, Arm::South },
                        { wizard, Arm::South }, { wizard, Arm::South } };
                return { { monk, Arm::South }, { monk, Arm::South }, { wizard, Arm::South }, { wizard, Arm::South } };
            case Company::Clergy:
                if (heroic)
                    return { { champion, Arm::North }, { champion, Arm::South }, { abbot, Arm::North },
                        { abbot, Arm::South }, { chaplain, Arm::North } };
                return { { champion, Arm::North }, { abbot, Arm::South }, { abbot, Arm::North },
                    { chaplain, Arm::South } };
            case Company::LastReserve:
                return { { champion, Arm::North }, { champion, Arm::South }, { captain, Arm::North },
                    { champion, Arm::South }, { chaplain, Arm::North } };
        }
        return {};
    }

    inline constexpr bool IsCompanyEntry(std::uint32_t entry)
    {
        return entry >= ScarletMonasteryRework::NPC_SM_CHAPEL_GUARD_CHAMPION
            && entry <= ScarletMonasteryRework::NPC_SM_COMPANY_ABBOT;
    }

    // The heroic Chapel Guard charge (LS6): every Champion of the Chapel Guard and of the Last Reserve, heroic only.
    inline constexpr bool ChargesOnArrival(Company c, std::uint32_t entry, bool heroic)
    {
        return heroic && entry == ScarletMonasteryRework::NPC_SM_CHAPEL_GUARD_CHAMPION
            && (c == Company::ChapelGuard || c == Company::LastReserve);
    }

    // LS1: the next company is called when the current one has fallen, or `everyMs` after it arrived; at most
    // kStandCompanies. `arrivedAtMs` 0 = the current company has not arrived yet. The first call is the stand's own.
    inline constexpr bool NextCallDue(std::uint32_t called, bool currentFallen, std::uint64_t arrivedAtMs,
        std::uint64_t nowMs, std::uint32_t everyMs)
    {
        if (called == 0 || called >= kStandCompanies)
            return false;
        if (currentFallen)
            return true;
        return arrivedAtMs != 0 && nowMs >= arrivedAtMs + everyMs;
    }

    // He comes down when the third company falls (and he is not fighting yet: an early pull).
    inline constexpr bool DescentDue(std::uint32_t called, bool everyCompanyFallen, bool engaged)
    {
        return !engaged && called >= kStandCompanies && everyCompanyFallen;
    }

    // LS7 (heroic): once, at his 50%.
    inline constexpr bool ReserveDue(bool heroic, bool reserveCalled, float healthPct)
    {
        return heroic && !reserveCalled && healthPct <= kReservePct;
    }

    // He falls at 1% only once no company is left to call or alive (the Last Reserve too): until then he holds at 1%
    // and fights on (pulling him early never skips a company: the failing path check).
    inline constexpr bool FallAllowed(bool atFloor, std::uint32_t called, bool anyMemberAlive, bool reservePending)
    {
        return atFloor && called >= kStandCompanies && !anyMemberAlive && !reservePending;
    }

    // The lowest health he may drop to: `floorPct` of his maximum (at least 1 health).
    inline std::uint32_t FloorHealth(std::uint32_t maxHealth, float floorPct)
    {
        auto const floor = static_cast<std::uint32_t>(std::ceil(static_cast<double>(maxHealth) * floorPct / 100.0));
        return std::max<std::uint32_t>(floor, 1);
    }

    // The part of `damage` he takes and stays at the floor.
    inline std::uint32_t ClampToFloor(std::uint32_t health, std::uint32_t maxHealth, std::uint32_t damage,
        float floorPct)
    {
        std::uint32_t const floor = FloorHealth(maxHealth, floorPct);
        if (health <= floor)
            return 0;
        return std::min(damage, health - floor);
    }

    // The stand's wipe while he waits on the altar: nobody alive on its floor for kWipeGraceMs.
    inline constexpr bool WipeDue(std::uint32_t emptyMs)
    {
        return emptyMs >= kWipeGraceMs;
    }

    // LS5: the whirl belongs to its wind-up. A storm whose 2 s bar ends early (her save, the Truth's or the light's
    // kneel, the Verdict's root: every scripted interrupt reaches OnSpellFailed) lands on nobody, the tank included.
    inline constexpr bool StormCancelledBy(std::uint32_t failedSpell)
    {
        return failedSpell == SPELL_LS_DIVINE_STORM_CAST;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    // LS3: the most hurt living member (lowest percent below kHealBelowPct); -1 when nobody is hurt.
    struct HealCandidate
    {
        float healthPct = 100.f;
        bool alive = true;
    };

    inline int MostHurt(std::vector<HealCandidate> const& members)
    {
        int best = -1;
        for (std::size_t i = 0; i < members.size(); ++i)
        {
            HealCandidate const& m = members[i];
            if (!m.alive || m.healthPct >= kHealBelowPct)
                continue;
            if (best < 0 || m.healthPct < members[static_cast<std::size_t>(best)].healthPct)
                best = static_cast<int>(i);
        }
        return best;
    }

    // LS3: the company's healer this turn. The Chapel Guard and the Last Reserve: the Chaplain. The Clergy: its two
    // Abbots taking turns (the one still free when the other cannot cast). The Pyre Brethren: none. `healers` are the
    // company's living members (entry, free to cast now); -1 when none may.
    struct HealerCandidate
    {
        std::uint32_t entry = 0;
        bool free = true;
    };

    inline int PickHealer(Company c, std::vector<HealerCandidate> const& healers, std::uint32_t turn)
    {
        std::uint32_t wanted = 0;
        switch (c)
        {
            case Company::ChapelGuard:
            case Company::LastReserve:
                wanted = ScarletMonasteryRework::NPC_SM_COMPANY_CHAPLAIN;
                break;
            case Company::Clergy:
                wanted = ScarletMonasteryRework::NPC_SM_COMPANY_ABBOT;
                break;
            case Company::PyreBrethren:
                return -1;
        }
        std::vector<std::size_t> ready;
        for (std::size_t i = 0; i < healers.size(); ++i)
            if (healers[i].entry == wanted && healers[i].free)
                ready.push_back(i);
        if (ready.empty())
            return -1;
        return static_cast<int>(ready[turn % ready.size()]);
    }

    // Whom an arriving unit attacks (rule 19, the BRD Hurley ruling): the nearest tank within kArriveRangeYd, else the
    // nearest player there; -1 when nobody is.
    struct ArrivalCandidate
    {
        float distance = 0.f;
        bool tank = false;
    };

    inline int PickArrival(std::vector<ArrivalCandidate> const& candidates)
    {
        int best = -1;
        for (std::size_t i = 0; i < candidates.size(); ++i)
        {
            ArrivalCandidate const& c = candidates[i];
            if (c.distance > kArriveRangeYd)
                continue;
            if (best < 0)
            {
                best = static_cast<int>(i);
                continue;
            }
            ArrivalCandidate const& b = candidates[static_cast<std::size_t>(best)];
            if ((c.tank && !b.tank) || (c.tank == b.tank && c.distance < b.distance))
                best = static_cast<int>(i);
        }
        return best;
    }

    // LS6: a charge target per Champion, from the players in line of sight of the arm mouth (handoff 7 #33 A: the
    // lines are clipped to LOS), a different one for each Champion while there are enough; `roll(n)` in [0, n).
    // Returns indexes into `inLos` (true = that player is in sight); empty when nobody is in sight.
    template <class Roll>
    std::vector<std::size_t> ChargeTargets(std::size_t champions, std::vector<bool> const& inLos, Roll&& roll)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < inLos.size(); ++i)
            if (inLos[i])
                pool.push_back(i);
        std::vector<std::size_t> out;
        if (pool.empty())
            return out;
        std::vector<std::size_t> left = pool;
        for (std::size_t c = 0; c < champions; ++c)
        {
            if (left.empty())
                left = pool;
            std::size_t const k = static_cast<std::size_t>(roll(left.size())) % left.size();
            out.push_back(left[k]);
            left.erase(left.begin() + static_cast<std::ptrdiff_t>(k));
        }
        return out;
    }

    // LS4: the throw look leaves so it lands as the circle resolves.
    inline std::uint32_t HammerLaunchDelayMs(float distanceYd)
    {
        float const flightMs = distanceYd / kHammerMissileSpeed * 1000.f;
        return flightMs >= static_cast<float>(kHammerWarnMs) ? 0u
            : static_cast<std::uint32_t>(static_cast<float>(kHammerWarnMs) - flightMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry (NM "Last Stand"; handoff 3.8)
    // ----------------------------------------------------------------------------------------------------------------
    // The arm ends the companies march from (8.2 s at 8 yd/s to the crossing center) and the arm mouths, where an arm
    // opens onto the crossing (the heroic charge lines start there).
    inline constexpr std::array<Point3, 2> kArmEnds{ { { 1149.8f, 1459.8f, 31.0f }, { 1149.8f, 1337.8f, 30.9f } } };
    inline constexpr std::array<Point3, 2> kArmMouths{ { { 1141.0f, 1430.0f, 31.6f }, { 1141.0f, 1366.0f, 31.6f } } };
    inline constexpr Point3 kCrossingCenter{ 1140.f, 1398.f, 31.4f };

    inline constexpr Point3 ArmEnd(Arm a)
    {
        return kArmEnds[static_cast<std::size_t>(a)];
    }

    inline constexpr Point3 ArmMouth(Arm a)
    {
        return kArmMouths[static_cast<std::size_t>(a)];
    }

    // A company's marching column at its arm end: one unit every 2.5 yd toward the mouth, alternate units 2 yd toward
    // the crossing's middle (x), so up to five stand inside the arm's floor.
    inline constexpr float kColumnStepYd = 2.5f;
    inline constexpr float kColumnSideYd = 2.f;

    inline Point4 ColumnSpot(Arm a, std::uint32_t index)
    {
        Point3 const end = ArmEnd(a);
        float const toward = a == Arm::North ? -1.f : 1.f;     // toward the crossing along y
        float const y = end.y + toward * kColumnStepYd * static_cast<float>(index);
        float const x = end.x - ((index % 2) ? kColumnSideYd : 0.f);
        float const o = a == Arm::North ? DungeonKit::kPi * 1.5f : DungeonKit::kPi * 0.5f;
        return { x, y, end.z, o };
    }

    // The chest (section 7 #20 A) at the altar steps, south of his body and off the vigil's line (the platform, z 32.2
    // to 34.3; the navmesh reads 32.7 there, the floor about 0.4 lower). Faces the nave.
    inline constexpr Point4 kChestSpot{ 1158.0f, 1391.0f, 32.35f, DungeonKit::kPi };

    // The stand's floor (bots' bounds and his leash): the landing before the Chapel Door, the nave, the crossing with
    // both arms and the altar platform. NM boxes, z band 28-37 (the platform tops out at 34.3).
    inline constexpr float kFloorZMin = 28.f;
    inline constexpr float kFloorZMax = 37.f;

    struct Box
    {
        float minX;
        float maxX;
        float minY;
        float maxY;

        constexpr bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
    };

    inline constexpr Box kLandingBox{ 1054.f, 1073.f, 1355.f, 1443.f };
    inline constexpr Box kNaveBox{ 1073.f, 1131.f, 1366.f, 1428.f };
    inline constexpr Box kCrossingBox{ 1131.f, 1151.f, 1333.f, 1465.f };
    inline constexpr Box kPlatformBox{ 1151.f, 1172.f, 1366.f, 1428.f };
    inline constexpr std::array<Box, 4> kFloorBoxes{ { kLandingBox, kNaveBox, kCrossingBox, kPlatformBox } };

    inline DungeonKit::Arena StandFloor()
    {
        DungeonKit::Arena floor;
        for (Box const& b : kFloorBoxes)
            floor.Add(ScarletMonasteryRework::BoxRegion(b.minX, b.maxX, b.minY, b.maxY, kFloorZMin, kFloorZMax));
        return floor;
    }

    // The wipe watch's zone: the stand's floor with a margin, the landing's steps included.
    inline constexpr Box kStandZone{ 1048.f, 1176.f, 1325.f, 1475.f };
    inline constexpr float kStandZoneZMin = 24.f;
    inline constexpr float kStandZoneZMax = 40.f;

    inline constexpr bool InStandZone(Vec2 p, float z)
    {
        return kStandZone.Contains(p) && z >= kStandZoneZMin && z <= kStandZoneZMax;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The companies' items (V's picks: _visuals.py ITEM_CAPTAIN_*; the stock trash's equipment for the rest; the DT
    // test pins them) and their kill priority
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kItemChampionWeapon = 5491;      // stock Scarlet Champion 4302
    inline constexpr std::uint32_t kItemCaptainSword = 1899;        // ITEM_CAPTAIN_SWORD
    inline constexpr std::uint32_t kItemCaptainShield = 1984;       // ITEM_CAPTAIN_SHIELD
    inline constexpr std::uint32_t kItemChaplainWeapon = 5291;      // stock Scarlet Chaplain 4299
    inline constexpr std::uint32_t kItemWizardWeapon = 1907;        // stock Scarlet Wizard 4300
    inline constexpr std::uint32_t kItemAbbotWeapon = 5291;         // stock Scarlet Abbot 4303

    struct Equipment
    {
        std::uint32_t mainHand = 0;
        std::uint32_t offHand = 0;
    };

    inline constexpr Equipment EquipmentOf(std::uint32_t entry)
    {
        using namespace ScarletMonasteryRework;
        switch (entry)
        {
            case NPC_SM_CHAPEL_GUARD_CHAMPION: return { kItemChampionWeapon, 0 };
            case NPC_SM_CAPTAIN_OF_THE_GUARD:  return { kItemCaptainSword, kItemCaptainShield };
            case NPC_SM_COMPANY_CHAPLAIN:      return { kItemChaplainWeapon, 0 };
            case NPC_SM_COMPANY_WIZARD:        return { kItemWizardWeapon, 0 };
            case NPC_SM_COMPANY_ABBOT:         return { kItemAbbotWeapon, 0 };
            default:                           return { 0, 0 };     // the Monks fight bare-handed (stock)
        }
    }

    inline constexpr std::int8_t KillPriority(std::uint32_t entry)
    {
        using namespace ScarletMonasteryRework;
        switch (entry)
        {
            case NPC_SM_COMPANY_CHAPLAIN:      return kChaplainPriority;
            case NPC_SM_COMPANY_ABBOT:         return kAbbotPriority;
            case NPC_SM_CAPTAIN_OF_THE_GUARD:  return kCaptainPriority;
            case NPC_SM_COMPANY_WIZARD:        return kWizardPriority;
            case NPC_SM_COMPANY_MONK:          return kMonkPriority;
            case NPC_SM_CHAPEL_GUARD_CHAMPION: return kChampionPriority;
            default:                           return 0;
        }
    }

    inline constexpr char const* MemberName(std::uint32_t entry)
    {
        using namespace ScarletMonasteryRework;
        switch (entry)
        {
            case NPC_SM_CHAPEL_GUARD_CHAMPION: return "champion";
            case NPC_SM_CAPTAIN_OF_THE_GUARD:  return "captain";
            case NPC_SM_COMPANY_CHAPLAIN:      return "chaplain";
            case NPC_SM_COMPANY_MONK:          return "monk";
            case NPC_SM_COMPANY_WIZARD:        return "wizard";
            case NPC_SM_COMPANY_ABBOT:         return "abbot";
            default:                           return "?";
        }
    }
}

#endif
