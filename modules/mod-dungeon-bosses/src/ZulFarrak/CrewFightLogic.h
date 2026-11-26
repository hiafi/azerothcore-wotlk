/*
 * mod-dungeon-bosses, Zul'Farrak D5: Sergeant Bly's crew as a boss, the pure, host-testable part (no engine headers).
 * WP-D5 owns this file (handoff section 3.5 row D5; build spec docs/dungeons/zul-farrak-rework.md "Sergeant Bly's
 * crew", BC1-BC13, rulings 24 and 26 to 30, 46). The crew are CR's (BlyCrew.h, BlyCrewLogic.h): D5 plugs a
 * CrewModeHandler into their Boss and Yielded modes (bly_crew_fight_rework.cpp) and keeps here what it decides:
 *
 *   CrewFightSpells       the slice 214030-214069 (kSpellsCrewFight of ZulFarrakRework.h)
 *   Tune                  every number of the fight (section 3.5 rule 32)
 *   GangUpTotalPct        BC1 Gang Up's total, heroic Focus Fire's escalation (15% more each call, no cap)
 *   PickSingledOut        BC1 heroic Singled Out: who outside the stack becomes the next mark
 *   PickGuarded           BC2 Bodyguard: the crew member at the lowest health percent (never Bly)
 *   SplitGuarded          BC2 the guarded's 75% cut and Bly's third of what was blocked
 *   LastCast, GreaterHealDue, ResurrectionAllowed      BC7 / BC12 Murta's two big casts, never back to back
 *   Standing, FightBook   who is fighting, fallen (heroic body), yielded (the Test) or dead; Avenge (BC13), the
 *                         Soulstone's clock (BC12) and when the fight is decided
 *   kStashSpot            section 7 #19 A: where the stash chest appears (the plaza)
 *
 * Health is ZulFarrakRework.h Health (kBly, kRaven, kOro, kMurta); never restated here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_CREW_FIGHT_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_CREW_FIGHT_LOGIC_H

#include "BlyCrewLogic.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ZfCrewFight
{
    using ZulFarrakRework::CrewMode;
    using ZulFarrakRework::kCrewCount;
    using ZulFarrakRework::NH;
    using ZulFarrakRework::Point3;
    using ZfCrew::Window;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsCrewFight;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (apps/dbc-tools source/npcs/zul_farrak/bly_crew_fight.py declares the same ids)
    // ----------------------------------------------------------------------------------------------------------------
    enum CrewFightSpells : std::uint32_t
    {
        SPELL_BC_GANG_UP_MARK       = 214030,   // BC1 the mark on the called player (Hunter's Mark SV 3239)
        SPELL_BC_GANG_UP_SHARE      = 214031,   // BC1 one share of the split strike (the script's base point)
        SPELL_BC_GUARDED            = 214032,   // BC2 Guarded on a crew member (the kill order's LacksAura)
        SPELL_BC_INTERVENE          = 214033,   // BC2 Bly's charge look (Intervene SV 9107)
        SPELL_BC_REFLECT            = 214034,   // BC3 heroic Spell Reflection on the guarded (one charge)
        SPELL_BC_VANISH             = 214035,   // BC4 Raven's vanish look (SV 255)
        SPELL_BC_AMBUSH             = 214036,   // BC4 the strike: resolve copy, Physical (Shadowstep SV 8262)
        SPELL_BC_GOUGE              = 214037,   // BC6 the 2 s Gouge (copy of 12540)
        SPELL_BC_KIDNEY_SHOT        = 214038,   // BC5 heroic Set Up: the 2 s stun
        SPELL_BC_WOUND_POISON       = 214039,   // BC5 heroic Set Up: 50% less healing taken, Poison
        SPELL_BC_RAIN_LOOK          = 214040,   // BC8 the fire falling at the point (SV 10379, persistent area)
        SPELL_BC_RAIN               = 214041,   // BC8 a tick: resolve copy, Fire
        SPELL_BC_SEED               = 214042,   // BC9 heroic Seed of Corruption on its carrier (Magic)
        SPELL_BC_SEED_BURST         = 214043,   // BC9 heroic the burst (the script's base point, Shadow)
        SPELL_BC_GREATER_HEAL       = 214044,   // BC7 normal: the 3 s heal (Holy, kickable)
        SPELL_BC_GREATER_HEAL_H     = 214045,   // BC7 heroic: the 2 s heal
        SPELL_BC_RESURRECTION       = 214046,   // BC12 heroic Murta's 8 s Resurrection (Holy, kickable)
        SPELL_BC_SOULSTONE          = 214047,   // BC12 heroic Oro's Soulstone on Murta
        SPELL_BC_AVENGE             = 214048,   // BC13 heroic the stacking buff
        SPELL_BC_WOUND_POISON_LOOK  = 214049,   // BC5 heroic the poison's lasting look (SV 14987)
        // 214050-214069 spare
    };

    inline std::array<std::uint32_t, 20> constexpr kCrewFightSpells{ {
        SPELL_BC_GANG_UP_MARK, SPELL_BC_GANG_UP_SHARE, SPELL_BC_GUARDED, SPELL_BC_INTERVENE, SPELL_BC_REFLECT,
        SPELL_BC_VANISH, SPELL_BC_AMBUSH, SPELL_BC_GOUGE, SPELL_BC_KIDNEY_SHOT, SPELL_BC_WOUND_POISON,
        SPELL_BC_RAIN_LOOK, SPELL_BC_RAIN, SPELL_BC_SEED, SPELL_BC_SEED_BURST, SPELL_BC_GREATER_HEAL,
        SPELL_BC_GREATER_HEAL_H, SPELL_BC_RESURRECTION, SPELL_BC_SOULSTONE, SPELL_BC_AVENGE,
        SPELL_BC_WOUND_POISON_LOOK,
    } };

    // Registry tags, the drill's (G1 `zul-farrak-shapes` row 7: RunOut/16, Stack/17, Zone/18, Zone/19).
    enum CrewFightTags : std::uint32_t
    {
        TAG_BC_SEED     = 16,
        TAG_BC_GANG_UP  = 17,
        TAG_BC_AMBUSH   = 18,
        TAG_BC_RAIN     = 19,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; section 3.6; rule 32). Percents are of the reference row (ZulFarrakRework.h
    // kReferenceNormal / kReferenceHeroic) unless they say "of the target's health".
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // BC1 Gang Up: a 6 yd Stack on a random player (tank included), struck 4 s after Bly's yell; heroic Focus Fire
        // every 16 s, 15% more total each call, no cap. Raven, Oro and Murta turn on the mark for 6 s.
        inline constexpr std::uint32_t kGangUpFirstMs = 8000;
        inline constexpr NH<std::uint32_t> kGangUpEveryMs{ 20000, 16000 };
        inline constexpr std::uint32_t kGangUpWarnMs = 4000;
        inline constexpr std::uint32_t kGangUpTurnMs = 6000;
        inline constexpr float kGangUpRadiusYd = 6.f;
        inline constexpr NH<float> kGangUpTotalPct{ 60.f, 90.f };
        inline constexpr float kFocusFireStepPct = 15.f;

        // BC2 Bodyguard: every 15 s (heroic 12 s), Guarded for 8 s; while Bly stands within 5 yd the guarded takes
        // 75% less and Bly takes a third of what was blocked. BC3 heroic: a one-charge Spell Reflection with it.
        inline constexpr NH<std::uint32_t> kBodyguardEveryMs{ 15000, 12000 };
        inline constexpr std::uint32_t kGuardedMs = 8000;
        inline constexpr float kGuardRangeYd = 5.f;
        inline constexpr std::uint32_t kGuardCutPct = 75;
        inline constexpr std::uint32_t kGuardBlyShareDiv = 3;
        inline constexpr float kGuardFollowYd = 2.f;        // Bly stands this close to the guarded

        // BC4 Ambush: first at 12 s, every 18 s (heroic 14 s), a 3 yd circle under a random player; 2 s (heroic
        // 1.5 s) later Raven steps into it: 40% Physical and Weakened. She stays on that player afterward.
        inline constexpr std::uint32_t kAmbushFirstMs = 12000;
        inline constexpr NH<std::uint32_t> kAmbushEveryMs{ 18000, 14000 };
        inline constexpr NH<std::uint32_t> kAmbushWarnMs{ 2000, 1500 };
        inline constexpr float kAmbushRadiusYd = 3.f;
        inline constexpr float kAmbushPct = 40.f;
        inline constexpr float kAmbushRangeYd = 40.f;

        // BC5 heroic Set Up: an Ambush hit is stunned 2 s and poisoned (50% less healing taken, 15 s), and Bly calls
        // an immediate Gang Up on the stunned player, struck 2 s later.
        inline constexpr std::uint32_t kKidneyShotMs = 2000;
        inline constexpr std::uint32_t kWoundPoisonMs = 15000;
        inline constexpr std::int32_t kWoundPoisonHealingPct = 50;
        inline constexpr std::uint32_t kSetUpWarnMs = 2000;

        // BC6 Gouge: a 2 s copy of 12540 on a random player within 5 yd (else her victim), first at 6 s, every 11 to
        // 23 s; Backstab from behind every 6 s (stock).
        inline constexpr std::uint32_t kGougeMs = 2000;
        inline constexpr Window kGougeFirst{ 6000, 6000 };
        inline constexpr Window kGouge{ 11000, 23000 };
        inline constexpr float kGougeRangeYd = 5.f;
        inline constexpr Window kBackstab{ 6000, 6000 };

        // BC7 Greater Heal: on a crew member under 50%, at most once every 15 s (heroic 12 s), a 3 s (heroic 2 s)
        // kickable cast healing 25% (heroic 50%) of the target's health.
        inline constexpr float kGreaterHealBelowPct = 50.f;
        inline constexpr NH<std::uint32_t> kGreaterHealEveryMs{ 15000, 12000 };
        inline constexpr NH<std::uint32_t> kGreaterHealCastMs{ 3000, 2000 };
        inline constexpr NH<float> kGreaterHealPct{ 25.f, 50.f };
        inline constexpr float kHealRangeYd = 40.f;

        // BC8 Rain of Fire: first at 6 s, every 11 to 23 s, an 8 yd circle under a random player within 30 yd (tank
        // included): 1.5 s of falling fire, then 9 s of ticks every 3 s for 6% (heroic 8%) Fire. No Weakened.
        inline constexpr Window kRainFirst{ 6000, 6000 };
        inline constexpr Window kRain{ 11000, 23000 };
        inline constexpr float kRainRadiusYd = 8.f;
        inline constexpr float kRainRangeYd = 30.f;
        inline constexpr std::uint32_t kRainWarnMs = 1500;
        inline constexpr std::uint32_t kRainMs = 9000;
        inline constexpr std::uint32_t kRainTickMs = 3000;
        inline constexpr NH<float> kRainTickPct{ 6.f, 8.f };

        // BC9 heroic Seed of Corruption: first at 10 s, every 20 s, a Magic debuff on a random player (tank
        // included); undispelled, it bursts after 6 s for 35% Shadow on everyone within 10 yd, the carrier included.
        inline constexpr std::uint32_t kSeedFirstMs = 10000;
        inline constexpr std::uint32_t kSeedEveryMs = 20000;
        inline constexpr std::uint32_t kSeedMs = 6000;
        inline constexpr std::uint32_t kSeedAuraMs = 6500;      // outlasts the burst (the script removes it)
        inline constexpr float kSeedRadiusYd = 10.f;
        inline constexpr float kSeedPct = 35.f;
        inline constexpr float kSeedRangeYd = 40.f;

        // BC10 steady pressure: the stock casts on their stock timers (SmartAI 7606 and 7608; SP "every 2 to 6 s" for
        // the Smite, "every 15 to 35 s" for Immolate, "once a minute" for the Curse). Bly's Shield Bash and Revenge
        // are CR's kit (BlyCrewLogic.h Tune).
        inline constexpr Window kShadowBoltFirst{ 0, 1000 };
        inline constexpr Window kShadowBolt{ 3000, 5000 };
        inline constexpr Window kImmolateFirst{ 13000, 15000 };
        inline constexpr Window kImmolate{ 15000, 35000 };
        inline constexpr Window kCurseFirst{ 0, 15000 };
        inline constexpr Window kCurse{ 60000, 60000 };
        inline constexpr Window kSmiteFirst{ 1000, 2000 };
        inline constexpr Window kSmite{ 2000, 6000 };
        inline constexpr Window kBuffCheckFirst{ 2000, 4000 };     // Murta's Renew and Shield (CR's percents)
        inline constexpr Window kBuffCheck{ 8000, 11000 };

        // BC11 the Test's yield: health floors at 30% (Bly's line 4 once all four yield).
        inline constexpr float kYieldPct = 30.f;

        // BC12 heroic No One Left Behind: Resurrection (8 s, kickable) raises a fallen or yielded member at 50%;
        // Oro's Soulstone raises Murta 10 s after she falls unless Oro is out by then. Oro puts a new stone on her
        // this long after one was used (SP "Oro keeps a Soulstone on Murta"; designer question 4).
        inline constexpr std::uint32_t kResurrectionCastMs = 8000;
        inline constexpr float kRisePct = 50.f;
        inline constexpr std::uint32_t kSoulstoneMs = 10000;
        inline constexpr std::uint32_t kSoulstoneRecastMs = 20000;

        // BC13 heroic Avenge: 20% damage and haste a stack, one stack per fall, death or yield, no cap.
        inline constexpr std::int32_t kAvengePctPerStack = 20;

        // The script's own polls.
        inline constexpr std::uint32_t kCasterCheckMs = 1000;   // Murta: a Greater Heal or a Resurrection now?

        // Boss data (SP "Boss data"; rulings 29, 30): the kill order, Murta and Oro together on heroic.
        inline constexpr std::int8_t kKillMurta = 4;
        inline constexpr std::int8_t kKillOro = 3;
        inline constexpr std::int8_t kKillRaven = 2;
        inline constexpr std::int8_t kKillBly = 1;
        inline constexpr std::int8_t kTankBly = 5;              // the bot tank holds Bly
        inline constexpr float kKillTogetherPct = 10.f;         // BM takes a percent of health (FF 2.5), not 10 s
        inline constexpr std::uint8_t kKickGreaterHeal = 3;
        inline constexpr std::uint8_t kKickResurrection = 4;
        inline constexpr std::uint8_t kDispelSeed = 3;
        inline constexpr std::uint8_t kDispelReward = 1;        // Wound Poison, Immolate, Curse of Weakness
        inline constexpr std::uint8_t kPurgeReward = 1;         // Murta's Renew and Shield

        // Section 3.5 rule 32: every warning holds the 1.5 s floor (SYS 4).
        static_assert(kGangUpWarnMs >= ZulFarrakRework::kWarningFloorMs, "Gang Up's warning");
        static_assert(kSetUpWarnMs >= ZulFarrakRework::kWarningFloorMs, "Set Up's Gang Up warning");
        static_assert(kAmbushWarnMs.heroic >= ZulFarrakRework::kWarningFloorMs, "Ambush heroic warning");
        static_assert(kAmbushWarnMs.normal >= kAmbushWarnMs.heroic, "Ambush normal warning");
        static_assert(kRainWarnMs >= ZulFarrakRework::kWarningFloorMs, "Rain of Fire's first tick");
        static_assert(kSeedMs >= ZulFarrakRework::kWarningFloorMs && kSeedAuraMs > kSeedMs, "Seed's clock");
        static_assert(kGangUpTurnMs >= kGangUpWarnMs, "the crew turn on the mark until it is struck");
        static_assert(kYieldPct < kGreaterHealBelowPct, "Greater Heal's window sits above the yield (SP: 20%)");
        static_assert(kRainMs % kRainTickMs == 0, "Rain of Fire ticks evenly");
        static_assert(kGuardCutPct <= 100 && kGuardBlyShareDiv > 0, "Bodyguard's split");
        static_assert(kKillMurta > kKillOro && kKillOro > kKillRaven && kKillRaven > kKillBly, "SP's kill order");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BC1 Gang Up and heroic Focus Fire / Singled Out
    // ----------------------------------------------------------------------------------------------------------------

    // The strike's total (percent of the reference row) for the `callIndex`-th call of the pull (0 = the first): flat
    // on normal; heroic Focus Fire 90, 105, 120, ... (SP "each call after hits 15% harder than the last", no cap).
    constexpr float GangUpTotalPct(bool heroic, std::uint32_t callIndex)
    {
        if (!heroic)
            return Tune::kGangUpTotalPct.normal;
        return Tune::kGangUpTotalPct.heroic + Tune::kFocusFireStepPct * float(callIndex);
    }

    // One share of the split: the total over the players in range (a mark left alone takes it all; none: 0).
    constexpr float SharePct(float totalPct, std::size_t inside)
    {
        return inside ? totalPct / float(inside) : 0.f;
    }

    // Heroic Singled Out: among the fight's players, the ones outside the stack when it lands; the next mark is the
    // one farthest from the mark (ties: the first). `outside[i]` and `distToMark[i]` describe player i.
    inline std::optional<std::size_t> PickSingledOut(std::vector<bool> const& outside,
        std::vector<float> const& distToMark)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < outside.size() && i < distToMark.size(); ++i)
            if (outside[i] && (!best || distToMark[i] > distToMark[*best]))
                best = i;
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BC2 Bodyguard
    // ----------------------------------------------------------------------------------------------------------------

    // The crew member Bly guards: the lowest health percent among the fighting Raven, Oro and Murta (`fighting`: a
    // CrewMember mask; Bly and Weegli never). Ties: the kill order's first (Murta, Oro, Raven).
    inline std::optional<std::uint32_t> PickGuarded(std::array<float, kCrewCount> const& healthPct,
        std::uint32_t fighting)
    {
        using ZulFarrakRework::CrewBit;
        std::array<std::uint32_t, 3> constexpr order{ { ZulFarrakRework::CREW_MURTA, ZulFarrakRework::CREW_ORO,
            ZulFarrakRework::CREW_RAVEN } };
        std::optional<std::uint32_t> best;
        for (std::uint32_t m : order)
            if ((fighting & CrewBit(m)) && (!best || healthPct[m] < healthPct[*best]))
                best = m;
        return best;
    }

    struct GuardSplit
    {
        std::uint32_t taken = 0;    // what the guarded takes
        std::uint32_t blocked = 0;  // what Bly's guard stopped
        std::uint32_t blyShare = 0; // what Bly takes of it (a third)
    };

    // A hit of `damage` on the guarded while Bly stands close.
    constexpr GuardSplit SplitGuarded(std::uint32_t damage)
    {
        GuardSplit s;
        s.blocked = std::uint32_t(std::uint64_t(damage) * Tune::kGuardCutPct / 100);
        s.taken = damage - s.blocked;
        s.blyShare = s.blocked / Tune::kGuardBlyShareDiv;
        return s;
    }

    // The guard holds while Bly fights and stands within reach of the guarded (2D, yards).
    constexpr bool GuardHolds(bool blyFighting, float distanceYd)
    {
        return blyFighting && distanceYd <= Tune::kGuardRangeYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BC7 / BC12 Murta's big casts
    // ----------------------------------------------------------------------------------------------------------------
    enum class LastCast : std::uint8_t
    {
        None,
        Other,          // a Smite, a Renew or a Shield came between
        GreaterHeal,
        Resurrection,
    };

    // SP BC12: "She never casts it and Greater Heal back to back".
    constexpr bool GreaterHealAllowed(LastCast last)
    {
        return last != LastCast::Resurrection;
    }

    constexpr bool ResurrectionAllowed(LastCast last)
    {
        return last != LastCast::GreaterHeal;
    }

    // A Greater Heal goes out now: someone under 50%, the cooldown over (`sinceLastMs` since the last one started;
    // none yet: `everCast` false), and not straight after a Resurrection.
    constexpr bool GreaterHealDue(float lowestPct, bool everCast, std::uint64_t sinceLastMs, bool heroic, LastCast last)
    {
        return lowestPct < Tune::kGreaterHealBelowPct && GreaterHealAllowed(last)
            && (!everCast || sinceLastMs >= Tune::kGreaterHealEveryMs(heroic));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Who stands: the fight's book (one per pull; the engine half keeps it per instance)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Standing : std::uint8_t
    {
        Fighting    = 0,
        Fallen      = 1,    // heroic betrayal: a held body (HeldBody) Murta can raise
        Yielded     = 2,    // the Test: at 30%, out of the fight (mode Yielded); Murta can raise it
        Dead        = 3,    // a real death (normal betrayal, a GM kill): nothing raises it
    };
    inline std::array<char const*, 4> constexpr kStandingNames{ { "fighting", "fallen", "yielded", "dead" } };

    constexpr bool IsOut(Standing s)
    {
        return s != Standing::Fighting;
    }

    constexpr bool CanRise(Standing s)
    {
        return s == Standing::Fallen || s == Standing::Yielded;
    }

    struct FightBook
    {
        bool running = false;
        bool heroic = false;
        std::uint32_t path = ZulFarrakRework::CREW_PATH_OPEN;
        std::array<Standing, kCrewCount> standing{};    // Weegli's entry is never read
        std::array<std::uint64_t, kCrewCount> outAtMs{};
        std::uint32_t avenge = 0;           // BC13 stacks (heroic)
        std::uint64_t soulstoneDueMs = 0;   // BC12 Murta rises at this time (0: none)
        bool soulstoneUp = false;           // the stone sits on Murta
        std::uint64_t soulstoneRecastAtMs = 0;
        std::uint32_t gangUpCalls = 0;      // BC1 calls this pull (Focus Fire's index)
        std::uint32_t falls = 0;            // falls, deaths and yields this pull (the log)
        std::uint32_t rises = 0;
    };

    // The four fighters that are fighting now (a CrewMember mask).
    constexpr std::uint32_t FightingMask(FightBook const& b)
    {
        std::uint32_t mask = 0;
        for (std::uint32_t m = 0; m < kCrewCount; ++m)
            if ((ZulFarrakRework::CrewBit(m) & ZulFarrakRework::kCrewFighters) && b.standing[m] == Standing::Fighting)
                mask |= ZulFarrakRework::CrewBit(m);
        return mask;
    }

    // A new pull: everyone fights, no stacks, no stone timer (heroic: the stone sits on Murta from the start).
    constexpr void StartBook(FightBook& b, bool heroic, std::uint32_t path)
    {
        b = FightBook();
        b.running = true;
        b.heroic = heroic;
        b.path = path;
        b.soulstoneUp = heroic;
    }

    // `member` goes out (`how`: Fallen, Yielded or Dead) at `nowMs`. Heroic: Avenge +1 (a death undone still counted,
    // so every fall counts); Murta's fall starts the Soulstone's clock while the stone sits on her and Oro fights; Oro
    // going out stops the clock. False when the member was already out the same way (a fallen or yielded member that
    // dies after counts no second stack).
    constexpr bool GoOut(FightBook& b, std::uint32_t member, Standing how, std::uint64_t nowMs)
    {
        using ZulFarrakRework::CrewBit;
        if (member >= kCrewCount || !(CrewBit(member) & ZulFarrakRework::kCrewFighters) || how == Standing::Fighting)
            return false;
        if (b.standing[member] == how)
            return false;
        bool const wasFighting = b.standing[member] == Standing::Fighting;
        b.standing[member] = how;
        if (member == ZulFarrakRework::CREW_MURTA && how == Standing::Dead)
            b.soulstoneDueMs = 0;       // a real death: nothing raises her
        if (!wasFighting)
            return true;
        b.outAtMs[member] = nowMs;
        ++b.falls;
        if (b.heroic)
            ++b.avenge;
        if (member == ZulFarrakRework::CREW_ORO)
            b.soulstoneDueMs = 0;
        if (member == ZulFarrakRework::CREW_MURTA && b.heroic && b.soulstoneUp
            && b.standing[ZulFarrakRework::CREW_ORO] == Standing::Fighting && how != Standing::Dead)
            b.soulstoneDueMs = nowMs + Tune::kSoulstoneMs;
        return true;
    }

    // `member` stands again (a Resurrection, the Soulstone). False when it cannot rise (fighting or dead).
    constexpr bool Rise(FightBook& b, std::uint32_t member)
    {
        if (member >= kCrewCount || !CanRise(b.standing[member]))
            return false;
        b.standing[member] = Standing::Fighting;
        ++b.rises;
        if (member == ZulFarrakRework::CREW_MURTA)
            b.soulstoneDueMs = 0;
        return true;
    }

    // The Soulstone raises Murta now: its clock ran out and Oro still fights (GoOut cleared it otherwise).
    constexpr bool SoulstoneDue(FightBook const& b, std::uint64_t nowMs)
    {
        return b.soulstoneDueMs && nowMs >= b.soulstoneDueMs
            && b.standing[ZulFarrakRework::CREW_ORO] == Standing::Fighting
            && CanRise(b.standing[ZulFarrakRework::CREW_MURTA]);
    }

    // The member Murta raises: the one out longest that can rise (never Murta herself). None: nobody to raise.
    constexpr std::optional<std::uint32_t> PickResurrection(FightBook const& b)
    {
        std::optional<std::uint32_t> best;
        for (std::uint32_t m = 0; m < kCrewCount; ++m)
            if ((ZulFarrakRework::CrewBit(m) & ZulFarrakRework::kCrewFighters) && m != ZulFarrakRework::CREW_MURTA
                && CanRise(b.standing[m]) && (!best || b.outAtMs[m] < b.outAtMs[*best]))
                best = m;
        return best;
    }

    // The fight is decided: none of the four fights and nothing can still raise one (Murta is out, so only the
    // Soulstone's clock could).
    constexpr bool Decided(FightBook const& b)
    {
        return b.running && FightingMask(b) == 0 && b.soulstoneDueMs == 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stash (section 7 #19 A): one chest when the fight ends, on either path, on the plaza between Bly's and
    // Murta's gather spots, about 5 yd east of them (the yielded crew stand on their spots meanwhile). The engine drops
    // z to the ground.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr Point3 kStashSpot{ 1887.8f, 1204.0f, 9.2f, 1.32f };

    constexpr std::uint32_t StashEntry(bool heroic)
    {
        return heroic ? ZulFarrakRework::GO_ZF_CREW_STASH_HEROIC : ZulFarrakRework::GO_ZF_CREW_STASH;
    }
}

#endif
