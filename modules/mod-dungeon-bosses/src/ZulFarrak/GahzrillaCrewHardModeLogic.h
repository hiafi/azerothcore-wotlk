/*
 * mod-dungeon-bosses, Zul'Farrak D7Ha: the crew at the pool, the main half of the hard mode "The Crew at the Pool"
 * (heroic only, armed by Bly's Test with all five crew at the pool), the pure, host-testable part (no engine headers).
 * Build spec: docs/dungeons/zul-farrak-rework.md "Hard mode: the crew at the pool" (GZ15-GZ21, rulings 41-43);
 * handoff sections 3.5 row D7Ha, 3.6, 3.7, 3.8 (the pool), 3.9 rows 9 and 13, 7 #16, #17, #39, #43, #58 and 10.
 * Tested by tests/zf_hard_mode_test.cpp; apps/dbc-tools lib/test_zul_farrak_crew_hard_mode.py pins the spell rows and
 * the numbers the DT file restates against this file.
 *
 *   PoolCrewSpells / Tags   the spells (kSpellsPoolCrew 214150-214189) and the registry tags (35, 36, 39, 40: the hard
 *                           mode's band; G1's drill rows 9 and 13 use 35 and 40)
 *   Tune                    every number of the package (rule 32)
 *   HardModeClock           the package's beats from Velratha's pull: Wellspring (phases 1 and 2), Storm's Chosen,
 *                           Overcharge; a grid keeps its pace after a late beat (D7's Beat)
 *   The crew's spots        CrewFightSpot (Bly and Raven in melee, Oro, Murta and Weegli 20 yd out, fanned toward the
 *                           group), NearestOf (the nearest candidate a predicate accepts: dry ground or ice), the
 *                           candidates (rings around a point plus the ice sheets), OnShore (the shore off the pool)
 *   The crew's rules        WaterExitDue (2 s late), CrewDischargePct (D7's heroic rule on their own health),
 *                           HealPick (Murta's Greater Heal: the lowest under 80%), CrewHitAmount (their small damage)
 *   The five answers        SpringSpotOk (GZ15), ChosenFor (GZ17: Bly, the marked player alone, or the split),
 *                           SiphonCanStart (GZ18), InMassDispel (GZ19), RavenCanKick (GZ20)
 *
 * Health is ZulFarrakRework.h Health (the crew's pool health is their heroic boss health, WP-H's overrides; Weegli
 * kWeegliPoolAlly). Every water rule is KT's WaterField and D7's PoolFight (PoolFight.h).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_CREW_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_CREW_HARD_MODE_LOGIC_H

#include "DungeonKitMath.h"
#include "GahzrillaLogic.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <vector>

namespace ZfPoolCrew
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsPoolCrew;

    // apps/dbc-tools source/npcs/zul_farrak/gahzrilla_crew_hard_mode.py declares them (its test pins these ids).
    enum PoolCrewSpells : std::uint32_t
    {
        SPELL_HM_WELLSPRING             = kSpellSlice.first + 0,    // GZ15: the geyser look on the spring (repeats)
        SPELL_HM_BLASTING_CHARGE        = kSpellSlice.first + 1,    // GZ16: the registry's resolve copy (Fire)
        SPELL_HM_BLAST_LOOK             = kSpellSlice.first + 2,    // GZ16: the blast on the spring (look)
        SPELL_HM_PLANT_CHARGE           = kSpellSlice.first + 3,    // GZ16: Weegli's 5 s plant (his bar)
        SPELL_HM_STORMS_CHOSEN          = kSpellSlice.first + 4,    // GZ17: the marked player's 4 s debuff
        SPELL_HM_STORMS_CHOSEN_BOLT     = kSpellSlice.first + 5,    // GZ17: the bolt (script base point, Nature)
        SPELL_HM_STORM_BOLT_LOOK        = kSpellSlice.first + 6,    // GZ17: the bolt on Bly (look)
        SPELL_HM_BODYGUARD              = kSpellSlice.first + 7,    // GZ17: Bly takes it (look)
        SPELL_HM_OVERCHARGE             = kSpellSlice.first + 8,    // GZ18: the player's 8 s debuff
        SPELL_HM_SIPHON_CHARGE          = kSpellSlice.first + 9,    // GZ18: Oro's 3 s channel on that player
        SPELL_HM_MASS_DISPEL            = kSpellSlice.first + 10,   // GZ19: Murta's 2 s cast (her bar)
        SPELL_HM_GREATER_HEAL           = kSpellSlice.first + 11,   // GZ21: Murta's Greater Heal on a crew member
        SPELL_HM_TWIN_CALL              = kSpellSlice.first + 12,   // GZ20: the second head's kickable 2 s Arcane
    };
    // The first id D7Ha leaves free (214163-214189: spare).
    inline constexpr std::uint32_t kFirstSpareSpell = kSpellSlice.first + 13;
    static_assert(kFirstSpareSpell <= kSpellSlice.last + 1);

    // Registry tags: the hard mode's band 35-40 (D7's note in GahzrillaLogic.h; D7Hb has 37 and 38). G1's drill uses 35
    // for the loose gather (row 9) and 40 for Twin Call (row 13, a kick judged as Soak/40); the live Twin Call has no
    // shape, so 40 tags the Blasting Charge.
    enum PoolCrewTags : std::uint32_t
    {
        TAG_HM_GATHER       = 35,   // GZ19: within 15 yd of Murta for her Mass Dispel (D7's Conductive Spread keeps 6)
        TAG_HM_OVERCHARGE   = 36,   // GZ18: the Overcharged player to Oro
        TAG_HM_CHOSEN       = 39,   // GZ17: the marked player to Bly (Bly dead: everyone on the marked player)
        TAG_HM_BLAST        = 40,   // GZ16: Weegli's 10 yd blast on the spring
    };

    // WaterField SheetRules::kind of D7Ha's sheets (the packages use 10 and up; D7Hb has 30 to 39).
    enum PoolCrewSheetKind : std::uint32_t
    {
        SHEET_WELLSPRING    = 10,
    };

    // Text groups (0-based, rule 34). Gahz'rilla 7273 group 2 is D7Ha's (this rev); Bly 7604 group 5 and Weegli 7607
    // group 4 are CR's rev (BlyCrew.h CrewTexts YELL_BLY_BEHIND_ME, YELL_WEEGLI_CHARGE).
    enum PoolCrewTexts : std::uint8_t
    {
        EMOTE_GAHZRILLA_DEVOURS = 2,    // "%s devours $n!" (GZ21, a crew death)
    };

    // The descriptor's priorities: the Wellspring above both bosses while Weegli is dead (Velratha 2, Gahz'rilla 1);
    // the second head's Call the Waters on the interrupt list only while Raven is dead (D7's Call is 1).
    inline constexpr std::int8_t kWellspringTargetPriority = 3;
    inline constexpr std::uint8_t kTwinCallKickPriority = 1;

    // Movement point ids of D7Ha's moves (CR forwards ids >= kPointHandlerBase 100 to the handler).
    inline constexpr std::uint32_t kPointCrewFight = 140;       // a crew member's fight spot or the way out of water
    inline constexpr std::uint32_t kPointWeegliSpring = 141;    // GZ16: Weegli to the newest spring
    inline constexpr std::uint32_t kPointCrewHome = 142;        // the encounter is over: back to the pool spot

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (rule 32). Damage percents of players are of the reference row (RefFlatOn: the tank row on the tank); the
    // crew's are of their own maximum health (rule 29, SP GZ21).
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // GZ15 Wellspring: 20 s, then every 40 s, phases 1 and 2 only; a 6 yd puddle that cannot freeze and grows 2 yd
        // every 5 s (no cap: rule 23); a random shore point at least 15 yd from every player; 40,000 health (WP-H).
        inline constexpr std::uint32_t kWellspringFirstMs = 20000;
        inline constexpr std::uint32_t kWellspringEveryMs = 40000;
        inline constexpr float kWellspringRadiusYd = 6.f;
        inline constexpr float kWellspringGrowYd = 2.f;
        inline constexpr std::uint32_t kWellspringGrowEveryMs = 5000;
        inline constexpr float kWellspringMinFromPlayerYd = 15.f;
        inline constexpr float kWellspringMaxFromPoolYd = 40.f;     // NAVMESH: 4,234 sq yd of shore within 40 yd
        inline constexpr float kWellspringGridYd = 3.f;             // the candidate grid over the shore
        inline constexpr float kWellspringZBandYd = 6.f;
        inline constexpr std::uint32_t kWellspringLookEveryMs = 4000;   // the one-shot geyser again (no lasting spout)

        // GZ16 Blasting Charge: Weegli runs to the newest spring, plants for 5 s, then a 3 s fuse: 60% Fire to the
        // players within 10 yd of the spring; the spring and its puddle are gone.
        inline constexpr std::uint32_t kPlantMs = 5000;
        inline constexpr std::uint32_t kFuseMs = 3000;
        inline constexpr float kBlastRadiusYd = 10.f;
        inline constexpr float kBlastPct = 60.f;
        inline constexpr float kPlantReachYd = 3.f;                 // he plants from this close to the spring
        inline constexpr std::uint32_t kWeegliRunTimeoutMs = 20000; // a run that never arrives plants from there
        inline constexpr float kWeegliStepAwayYd = 12.f;            // after the plant he leaves the blast

        // GZ17 Storm's Chosen: 15 s, then every 30 s; a random player, the tank included, 4 s mark, then 150% Nature.
        // Bly within 5 yd, dry and not stunned takes it (+2 Charged); Bly dead: split among players within 5 yd of the
        // mark, 1 Charged each.
        inline constexpr std::uint32_t kChosenFirstMs = 15000;
        inline constexpr std::uint32_t kChosenEveryMs = 30000;
        inline constexpr std::uint32_t kChosenMarkMs = 4000;
        inline constexpr float kChosenPct = 150.f;
        inline constexpr float kBodyguardYd = 5.f;
        inline constexpr std::uint32_t kBodyguardCharged = 2;
        inline constexpr float kChosenSplitYd = 5.f;
        inline constexpr std::uint32_t kChosenSplitCharged = 1;
        inline constexpr float kChosenStackYd = 4.f;                // the bots' stack on Bly: inside his 5 yd

        // GZ18 Overcharge: 25 s, then every 25 s; a random player, the tank included, 8 s; then 5 Charged for good
        // unless Oro (alive, dry, not stunned, within 10 yd) drained it with his 3 s Siphon Charge (+1 Charged on Oro).
        inline constexpr std::uint32_t kOverchargeFirstMs = 25000;
        inline constexpr std::uint32_t kOverchargeEveryMs = 25000;
        inline constexpr std::uint32_t kOverchargeMs = 8000;
        inline constexpr std::uint32_t kOverchargeStacks = 5;
        inline constexpr float kSiphonRangeYd = 10.f;
        inline constexpr std::uint32_t kSiphonMs = 3000;
        inline constexpr std::uint32_t kSiphonOroCharged = 1;
        inline constexpr float kOverchargeStackYd = 8.f;            // the bots' stack on Oro: inside his 10 yd

        // GZ19 Conductive on everyone and Murta's Mass Dispel: a 2 s cast after each Discharge, everyone within 15 yd.
        inline constexpr std::uint32_t kMassDispelCastMs = 2000;
        inline constexpr float kMassDispelRangeYd = 15.f;
        inline constexpr float kGatherStackYd = 13.f;               // the bots' gather on Murta: inside her 15 yd
        inline constexpr std::uint32_t kGatherSlackMs = 1000;       // the gather holds past her cast's end

        // GZ20 Twin Call: Raven (alive, in melee of Gahz'rilla, dry, not stunned) kicks the second head this long into
        // its cast (the group kicks Gahz'rilla's own).
        inline constexpr std::uint32_t kRavenKickDelayMs = 800;
        inline constexpr std::uint32_t kTwinCallCastMs = ZfPool::Tune::kCallCastMs.heroic;

        // GZ21 the crew's rules.
        inline constexpr std::uint32_t kCrewThinkMs = 1000;
        inline constexpr std::uint32_t kWaterExitLateMs = 2000;     // they step out of water about 2 s late
        inline constexpr float kDevourHealPct = 5.f;                // Gahz'rilla eats a fallen member
        inline constexpr float kCrewConductivePct = 25.f;           // of their own health, as D7's arcs on players
        inline constexpr std::uint32_t kCrewStunMs = ZfPool::Tune::kStaticShockMs;
        inline constexpr float kCrewRangedYd = 20.f;                // Oro, Murta and Weegli stand about 20 yd out
        inline constexpr float kCrewMeleeInsetYd = 1.f;             // Bly and Raven: his combat reach less this
        inline constexpr float kCrewMinMeleeYd = 2.f;
        inline constexpr float kCrewMoveSlackYd = 3.f;              // a spot this close is kept (no re-walk)
        inline constexpr std::uint32_t kCrewHitEveryMs = 2000;
        // Their damage: about 15% of the hard mode target (3,774 group DPS, section 3.6) = 566 a second in all.
        inline constexpr std::array<std::uint32_t, ZulFarrakRework::kCrewCount> kCrewDps{ { 150, 160, 130, 80, 46 } };
        inline constexpr float kCrewHitRangeYd = 30.f;              // the casters' reach (Oro, Murta, Weegli)
        // Murta's Greater Heal: the lowest crew member under 80%, 30% of their health, a 2.5 s cast, 6 s apart; never
        // started when a Discharge lands before it ends (her Mass Dispel comes first, RB-17).
        inline constexpr std::uint32_t kGreaterHealCastMs = 2500;
        inline constexpr std::uint32_t kGreaterHealEveryMs = 6000;
        inline constexpr float kGreaterHealPct = 30.f;
        inline constexpr float kGreaterHealBelowPct = 80.f;
        inline constexpr float kGreaterHealRangeYd = 40.f;
        inline constexpr std::uint32_t kCastMarginMs = 500;

        // The crew's dry-spot search: rings around the wanted spot.
        inline constexpr std::array<float, 9> kSearchRingsYd{ { 0.f, 3.f, 6.f, 9.f, 12.f, 16.f, 20.f, 25.f, 30.f } };
        inline constexpr std::uint32_t kSearchAngles = 12;

        // The warning floor (section 3.5 rule 32, SYS 4) and the answers' geometry.
        static_assert(kFuseMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kChosenMarkMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kTwinCallCastMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kSiphonMs < kOverchargeMs, "Oro must be able to finish inside the debuff");
        static_assert(kChosenStackYd < kBodyguardYd && kOverchargeStackYd < kSiphonRangeYd
            && kGatherStackYd < kMassDispelRangeYd, "the bots' stacks sit inside the answers' reach");
        static_assert(kRavenKickDelayMs + 500 < kTwinCallCastMs, "Raven kicks before the head's cast ends");
        static_assert(kWellspringRadiusYd + kWellspringGrowYd * 2 < kWellspringMinFromPlayerYd,
            "a fresh spring reaches nobody within its first two growths");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The package's clock (from Velratha's pull; Storm Builds is D7's)
    // ----------------------------------------------------------------------------------------------------------------

    enum class HmAct : std::uint8_t
    {
        None,
        Wellspring,
        StormsChosen,
        Overcharge,
    };

    class HardModeClock
    {
    public:
        void Start()
        {
            *this = HardModeClock();
            _spring.Start(Tune::kWellspringFirstMs, Tune::kWellspringEveryMs);
            _chosen.Start(Tune::kChosenFirstMs, Tune::kChosenEveryMs);
            _overcharge.Start(Tune::kOverchargeFirstMs, Tune::kOverchargeEveryMs);
            _running = true;
        }
        void Stop() { *this = HardModeClock(); }
        bool Running() const { return _running; }

        std::uint64_t Now() const { return _now; }
        void Advance(std::uint32_t diff) { _now += diff; }

        // GZ15: Wellsprings stop in the Deluge (SP: nothing is left to flood).
        void StopSprings() { _spring = ZfPool::Beat(); }
        bool SpringsRunning() const { return _spring.Running(); }

        // The beat due now, in a fixed order. Every act is instant to start (its warning runs on its own), so a beat
        // never waits on another and none starves (RB-17).
        HmAct Next() const
        {
            if (!_running)
                return HmAct::None;
            if (_chosen.Due(_now))
                return HmAct::StormsChosen;
            if (_overcharge.Due(_now))
                return HmAct::Overcharge;
            if (_spring.Due(_now))
                return HmAct::Wellspring;
            return HmAct::None;
        }

        void Done(HmAct act)
        {
            if (ZfPool::Beat* b = Of(act))
                b->Done(_now);
        }

        // Nothing could own it now (between Velratha's death and his arrival): tried again shortly (D7's kRetryMs).
        void Retry(HmAct act)
        {
            if (ZfPool::Beat* b = Of(act))
                b->Retry(_now);
        }

        std::uint64_t In(HmAct act) const
        {
            switch (act)
            {
                case HmAct::Wellspring:
                    return _spring.In(_now);
                case HmAct::StormsChosen:
                    return _chosen.In(_now);
                case HmAct::Overcharge:
                    return _overcharge.In(_now);
                case HmAct::None:
                    break;
            }
            return 0;
        }

    private:
        ZfPool::Beat* Of(HmAct act)
        {
            switch (act)
            {
                case HmAct::Wellspring:
                    return &_spring;
                case HmAct::StormsChosen:
                    return &_chosen;
                case HmAct::Overcharge:
                    return &_overcharge;
                case HmAct::None:
                    break;
            }
            return nullptr;
        }

        std::uint64_t _now = 0;
        bool _running = false;
        ZfPool::Beat _spring;
        ZfPool::Beat _chosen;
        ZfPool::Beat _overcharge;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Where the crew stand (SP: "Bly and Raven in melee, Oro, Murta and Weegli about 20 yd out")
    // ----------------------------------------------------------------------------------------------------------------

    // Each member's angle off the line from the boss to the group (degrees), by CrewMember: the melee pair either side
    // of the tank's line, the casters fanned toward the group, Murta in the middle (the group gathers on her, GZ19).
    // 20 yd out the casters stand 20 yd apart and the melee pair 17 yd apart at his reach of 15: no Conductive arc
    // (6 yd) between them.
    inline constexpr std::array<float, ZulFarrakRework::kCrewCount> kCrewAngleDeg{ { -35.f, 35.f, -60.f, 60.f, 0.f } };

    constexpr bool IsMeleeCrew(std::uint32_t member)
    {
        return member == ZulFarrakRework::CREW_BLY || member == ZulFarrakRework::CREW_RAVEN;
    }

    // The distance from the boss a member fights at (`bossReach`: the boss's combat reach).
    inline float CrewFightDistance(std::uint32_t member, float bossReach)
    {
        if (!IsMeleeCrew(member))
            return Tune::kCrewRangedYd;
        return std::max(Tune::kCrewMinMeleeYd, bossReach - Tune::kCrewMeleeInsetYd);
    }

    // The member's spot: `towardGroup` is the bearing from the boss to the group's middle (radians).
    inline Vec2 CrewFightSpot(std::uint32_t member, Vec2 boss, float towardGroup, float bossReach)
    {
        if (member >= ZulFarrakRework::kCrewCount)
            return boss;
        float const angle = towardGroup + kCrewAngleDeg[member] * DungeonKit::kPi / 180.f;
        return DungeonKit::Advance(boss, angle, CrewFightDistance(member, bossReach));
    }

    // The bearing from `from` to the middle of `points` (`fallback` with none, or with the middle on `from`).
    inline float BearingToMiddle(Vec2 from, std::span<Vec2 const> points, float fallback)
    {
        if (points.empty())
            return fallback;
        Vec2 mid{};
        for (Vec2 const& p : points)
        {
            mid.x += p.x;
            mid.y += p.y;
        }
        mid.x /= float(points.size());
        mid.y /= float(points.size());
        if (DungeonKit::Distance(from, mid) < 0.5f)
            return fallback;
        return DungeonKit::BearingTo(from, mid);
    }

    // Inside D7's pool strip: the registry's rectangle from kPoolAxisFrom to kPoolAxisTo, kPoolHalfWidthYd either side,
    // square ends (KT's WaterSheet::EdgeDistance; its bank counts as water, section 7 #37 A).
    inline bool InPoolStrip(Vec2 p)
    {
        Vec2 const a = ZfPool::kPoolAxisFrom;
        Vec2 const b = ZfPool::kPoolAxisTo;
        float const len = DungeonKit::Distance(a, b);
        float const ux = (b.x - a.x) / len;
        float const uy = (b.y - a.y) / len;
        float const along = (p.x - a.x) * ux + (p.y - a.y) * uy;
        float const side = std::fabs(-(p.x - a.x) * uy + (p.y - a.y) * ux);
        return along >= 0.f && along <= len && side <= ZfPool::kPoolHalfWidthYd;
    }

    // On the shore and off the pool: inside the shore polygon, outside the pool's water polygon and its strip.
    inline bool OnShore(Vec2 p)
    {
        using namespace ZulFarrakRework;
        if (!DungeonKit::PointInPolygon(std::span<Vec2 const>(kShorePolygon), p))
            return false;
        if (DungeonKit::PointInPolygon(std::span<Vec2 const>(kPoolWaterPolygon), p))
            return false;
        return !InPoolStrip(p);
    }

    // The search's candidates around `want`: the rings of Tune::kSearchRingsYd (nearest first), then `extra` (the ice
    // sheets' middles: in the Deluge the only dry ground).
    inline std::vector<Vec2> SearchCandidates(Vec2 want, std::span<Vec2 const> extra = {})
    {
        std::vector<Vec2> out;
        out.reserve(Tune::kSearchRingsYd.size() * Tune::kSearchAngles + extra.size());
        for (float const r : Tune::kSearchRingsYd)
        {
            if (r <= 0.f)
            {
                out.push_back(want);
                continue;
            }
            for (std::uint32_t i = 0; i < Tune::kSearchAngles; ++i)
                out.push_back(DungeonKit::Advance(want, DungeonKit::kTwoPi * float(i) / float(Tune::kSearchAngles), r));
        }
        out.insert(out.end(), extra.begin(), extra.end());
        return out;
    }

    // The candidate nearest `from` that `ok` accepts (nullopt: none). Ties keep the earlier candidate.
    template <typename Ok>
    std::optional<Vec2> NearestOf(Vec2 from, std::span<Vec2 const> candidates, Ok&& ok)
    {
        std::optional<Vec2> best;
        float bestD = std::numeric_limits<float>::max();
        for (Vec2 const& c : candidates)
        {
            float const d = DungeonKit::Distance(from, c);
            if (d < bestD && ok(c))
            {
                best = c;
                bestD = d;
            }
        }
        return best;
    }

    // GZ21: a member in water steps out about 2 s late (`wetSince`: the package's clock when water reached it).
    constexpr bool WaterExitDue(std::uint64_t now, std::uint64_t wetSince)
    {
        return now >= wetSince + Tune::kWaterExitLateMs;
    }

    // GZ21: a Discharge on a crew member, as a percent of its own maximum health (D7's heroic rule: 40%, raised 10% a
    // stack of Charged, wherever it stands).
    constexpr float CrewDischargePct(std::uint32_t charged)
    {
        return ZfPool::DischargePct(true, false, charged);
    }

    // `pct` percent of `maxHealth` (rounded down, at least 1 for a positive percent, at most the whole).
    constexpr std::uint32_t PctOfHealth(std::uint32_t maxHealth, float pct)
    {
        if (pct <= 0.f || !maxHealth)
            return 0;
        std::uint64_t const v = std::uint64_t(double(maxHealth) * double(pct) / 100.0);
        return std::uint32_t(std::max<std::uint64_t>(1, std::min<std::uint64_t>(v, maxHealth)));
    }

    // A member's hit on the boss every kCrewHitEveryMs.
    constexpr std::uint32_t CrewHitAmount(std::uint32_t member)
    {
        if (member >= ZulFarrakRework::kCrewCount)
            return 0;
        return Tune::kCrewDps[member] * Tune::kCrewHitEveryMs / 1000;
    }

    // A crew hit never lands the killing blow (the loot and the credit are the players', and Velratha's death before
    // the gong is D7's to refuse): at most health - 1.
    constexpr std::uint32_t CrewHitCapped(std::uint32_t amount, std::uint32_t health)
    {
        return health > 1 ? std::min(amount, health - 1) : 0;
    }

    // One crew member as Murta's heal pick sees it.
    struct HealCandidate
    {
        std::uint32_t member = 0;
        float healthPct = 100.f;
        bool alive = false;
        bool inRange = false;
    };

    // GZ21: the member lowest on health under 80% (alive, in her reach); nullopt: nobody.
    inline std::optional<std::uint32_t> HealPick(std::span<HealCandidate const> crew)
    {
        std::optional<std::uint32_t> best;
        float bestPct = Tune::kGreaterHealBelowPct;
        for (HealCandidate const& c : crew)
        {
            if (!c.alive || !c.inRange || c.healthPct >= bestPct)
                continue;
            best = c.member;
            bestPct = c.healthPct;
        }
        return best;
    }

    // GZ21 (section 7 #17 A, designer question): a player's heal on a crew member counts as the same share of the
    // member's health as of a player's: the crew take every hit as a percent of their own (boss-sized) health, so a
    // heal is scaled by their health over the reference row (`refRow`: the non-tank row), never down.
    constexpr std::uint32_t ScaledCrewHeal(std::uint32_t heal, std::uint32_t crewMaxHealth, std::uint32_t refRow)
    {
        if (!refRow || crewMaxHealth <= refRow)
            return heal;
        std::uint64_t const v = std::uint64_t(heal) * crewMaxHealth / refRow;
        return std::uint32_t(std::min<std::uint64_t>(v, std::numeric_limits<std::uint32_t>::max()));
    }

    // A cast of `castMs` may start now: the next Discharge lands later than its end (with the margin); 0: no clock.
    constexpr bool CastFitsBeforeDischarge(std::uint64_t nextDischargeInMs, std::uint32_t castMs)
    {
        return nextDischargeInMs == 0 || nextDischargeInMs > std::uint64_t(castMs) + Tune::kCastMarginMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The five answers
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kPoolMiddle{ (ZfPool::kPoolAxisFrom.x + ZfPool::kPoolAxisTo.x) / 2.f,
        (ZfPool::kPoolAxisFrom.y + ZfPool::kPoolAxisTo.y) / 2.f };

    // GZ15: a spring's spot: on the shore off the pool, within 40 yd of the pool's middle, at least 15 yd from every
    // player.
    inline bool SpringSpotOk(Vec2 p, std::span<Vec2 const> players)
    {
        if (DungeonKit::Distance(p, kPoolMiddle) > Tune::kWellspringMaxFromPoolYd || !OnShore(p))
            return false;
        for (Vec2 const& q : players)
            if (DungeonKit::Distance(p, q) < Tune::kWellspringMinFromPlayerYd)
                return false;
        return true;
    }

    // GZ15: every grid point a spring may burst at (the engine draws one and checks its floor and the water).
    inline std::vector<Vec2> SpringCandidates(std::span<Vec2 const> players)
    {
        std::vector<Vec2> out;
        float const r = Tune::kWellspringMaxFromPoolYd;
        std::uint32_t const steps = std::uint32_t(2.f * r / Tune::kWellspringGridYd);
        for (std::uint32_t i = 0; i <= steps; ++i)
            for (std::uint32_t j = 0; j <= steps; ++j)
            {
                Vec2 const p{ kPoolMiddle.x - r + float(i) * Tune::kWellspringGridYd,
                    kPoolMiddle.y - r + float(j) * Tune::kWellspringGridYd };
                if (SpringSpotOk(p, players))
                    out.push_back(p);
            }
        return out;
    }

    // GZ17: who takes the bolt.
    enum class Chosen : std::uint8_t
    {
        Bodyguard,      // Bly (alive, dry, not stunned) within 5 yd of the mark: nothing to players, Bly +2 Charged
        Alone,          // Bly alive but out of reach, wet or stunned: 150% on the marked player
        Split,          // Bly dead: 150% split among the players within 5 yd of the mark, 1 Charged each
    };

    constexpr Chosen ChosenFor(bool blyAlive, bool blyAble, float markToBlyYd)
    {
        if (!blyAlive)
            return Chosen::Split;
        return blyAble && markToBlyYd <= Tune::kBodyguardYd ? Chosen::Bodyguard : Chosen::Alone;
    }

    // GZ18: Oro starts his Siphon Charge now: able (alive, dry, not stunned, not draining already), within 10 yd of
    // the Overcharged player, and the debuff lasts long enough for the whole channel.
    constexpr bool SiphonCanStart(bool oroAble, float oroToPlayerYd, std::uint64_t debuffLeftMs)
    {
        return oroAble && oroToPlayerYd <= Tune::kSiphonRangeYd && debuffLeftMs >= Tune::kSiphonMs;
    }

    // GZ19: the Mass Dispel reaches this unit.
    constexpr bool InMassDispel(float murtaToUnitYd)
    {
        return murtaToUnitYd <= Tune::kMassDispelRangeYd;
    }

    // GZ20: Raven kicks the second head now: able (alive, dry, not stunned), in melee of Gahz'rilla, and the head has
    // been casting for at least kRavenKickDelayMs.
    constexpr bool RavenCanKick(bool ravenAble, bool inMelee, std::uint64_t castElapsedMs)
    {
        return ravenAble && inMelee && castElapsedMs >= Tune::kRavenKickDelayMs;
    }

    // GZ16: Weegli's job on one spring.
    enum class WeegliStep : std::uint8_t
    {
        Idle,
        Running,        // to the newest spring
        Planting,       // 5 s (a stun stops the plant: it starts over once he can act)
        Fuse,           // 3 s: the blast's warning, he steps away
    };
}

#endif
