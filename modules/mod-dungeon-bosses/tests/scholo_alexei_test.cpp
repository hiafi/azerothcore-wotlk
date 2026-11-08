// Host tests for AlexeiLogic.h (S9: Lord Alexei Barov (10504)): the slice and the arena (WP-KS's stub), the rule pool
// and the heroic pairs (AB1, AB8), the Rod ladder (AB9, ruling 19), the forbidden third (AB5), the lane (AB6), the
// desks (AB7), the fortune's spots (AB10), the Veil gate (AB11), the solo lesson's timeline and the examiner's numbers.
#include "AlexeiLogic.h"
#include "SoloLessonLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoAlexei;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool Contains(std::vector<RuleSet> const& pool, RuleSet set)
    {
        for (RuleSet s : pool)
            if (s == set)
                return true;
        return false;
    }

    // A deterministic [0, 1) sequence.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return float(state >> 8) / float(1u << 24);
        }
    };
}

int main()
{
    // ---- KS's stub checks: the slice and the arena ----------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(AlexeiArena().Contains(kAlexeiSpawn.XY(), kAlexeiSpawn.z));
    CHECK(ArenaFor(BOSS_ALEXEI).Contains(kAlexeiSpawn.XY(), kAlexeiSpawn.z));

    // ---- Ids: every spell in the slice ----------------------------------------------------------------------------
    for (std::uint32_t id = SPELL_AX_RULE_NO_RUNNING; id <= SPELL_AX_VEIL_OF_SHADOW; ++id)
        CHECK(kSpellSlice.Contains(id));
    CHECK(SPELL_AX_RULE_NO_RUNNING == 206290);
    CHECK(SPELL_AX_DEANS_ROD == 206300);
    CHECK(SPELL_AX_VEIL_OF_SHADOW == 206302);
    // The fortune unit is the kit's entry; the examiner is S13's.
    CHECK(NPC_SC_BAROV_FORTUNE == 300543);
    CHECK(NPC_SC_EXAMINER_ALEXEI == 300553);

    // ---- AB1-AB8 the rules ------------------------------------------------------------------------------------------
    // Each rule: its own icon, yell (creature_text groups 1-6), tag (mod-boss-mechanics' `alexei` drill's) and words.
    std::set<std::uint32_t> auras;
    std::set<std::uint8_t> yells;
    for (std::size_t i = 0; i < kRuleCount; ++i)
    {
        RuleBit const r = kRules[i];
        auras.insert(RuleAura(r));
        yells.insert(RuleYell(r));
        CHECK(RuleTag(r) == 2 + i);
        CHECK(RuleWords(r)[0] != '\0');
        CHECK(RuleCountOf(r) == 1);
    }
    CHECK(auras.size() == kRuleCount);
    CHECK(yells.size() == kRuleCount);
    CHECK(RuleYell(RULE_NO_RUNNING) == YELL_ALEXEI_NO_RUNNING);
    CHECK(RuleYell(RULE_OUT_OF_BOUNDS) == YELL_ALEXEI_CORNER);
    CHECK(RuleYell(RULE_DESKS) == YELL_ALEXEI_DESKS);

    // Normal: the four rules, never the last one again.
    {
        std::vector<RuleSet> const pool = RulePool(false, 3, 5, RULE_NONE);
        CHECK(pool.size() == 4);
        CHECK(!Contains(pool, RULE_LINE_UP));
        CHECK(!Contains(pool, RULE_DESKS));
        std::vector<RuleSet> const again = RulePool(false, 3, 5, RULE_ASSEMBLY);
        CHECK(again.size() == 3);
        CHECK(!Contains(again, RULE_ASSEMBLY));
        for (RuleSet s : pool)
            CHECK(IsAllowedSet(s, false));
    }
    // Heroic: any of the six first, then the seven pairs only.
    {
        std::vector<RuleSet> const first = RulePool(true, 0, 5, RULE_NONE);
        CHECK(first.size() == 6);
        for (RuleSet s : first)
            CHECK(RuleCountOf(s) == 1);
        std::vector<RuleSet> const later = RulePool(true, 1, 5, RULE_LINE_UP);
        CHECK(later.size() == 7);
        for (RuleSet s : later)
        {
            CHECK(RuleCountOf(s) == 2);
            CHECK(IsAllowedSet(s, true));
            CHECK(!IsAllowedSet(s, false));
            // AB8: No running only with Out of bounds; never Assembly with Keep your distance or desks.
            if (Has(s, RULE_NO_RUNNING))
                CHECK(s == RuleSet(RULE_NO_RUNNING | RULE_OUT_OF_BOUNDS));
            CHECK(!(Has(s, RULE_ASSEMBLY) && Has(s, RULE_KEEP_DISTANCE)));
            CHECK(!(Has(s, RULE_ASSEMBLY) && Has(s, RULE_DESKS)));
        }
        // Out of bounds pairs with every other rule.
        for (RuleBit r : kRules)
            if (r != RULE_OUT_OF_BOUNDS)
                CHECK(Contains(later, RuleSet(r | RULE_OUT_OF_BOUNDS)));
        CHECK(Contains(later, RuleSet(RULE_ASSEMBLY | RULE_LINE_UP)));
        CHECK(Contains(later, RuleSet(RULE_LINE_UP | RULE_KEEP_DISTANCE)));
        CHECK(!Contains(RulePool(true, 2, 5, RuleSet(RULE_ASSEMBLY | RULE_LINE_UP)),
            RuleSet(RULE_ASSEMBLY | RULE_LINE_UP)));
        CHECK(!IsAllowedSet(RuleSet(RULE_NO_RUNNING | RULE_ASSEMBLY), true));
        CHECK(!IsAllowedSet(RuleSet(RULE_ASSEMBLY | RULE_KEEP_DISTANCE), true));
        CHECK(!IsAllowedSet(RuleSet(RULE_ASSEMBLY | RULE_DESKS), true));
    }
    // Assembly needs three players.
    {
        CHECK(!Contains(RulePool(false, 0, 2, RULE_NONE), RULE_ASSEMBLY));
        CHECK(Contains(RulePool(false, 0, 3, RULE_NONE), RULE_ASSEMBLY));
        std::vector<RuleSet> const pairs = RulePool(true, 1, 2, RULE_NONE);
        CHECK(pairs.size() == 5);
        for (RuleSet s : pairs)
            CHECK(!Has(s, RULE_ASSEMBLY));
    }
    // The pick: uniform over the pool, never outside it, never the previous set (a run of announcements).
    {
        Lcg rng;
        RuleSet previous = RULE_NONE;
        std::set<RuleSet> seen;
        for (std::uint32_t n = 0; n < 400; ++n)
        {
            RuleSet const s = PickRuleSet(RulePool(true, n, 5, previous), rng());
            CHECK(s != RULE_NONE);
            CHECK(s != previous);
            CHECK(n == 0 ? RuleCountOf(s) == 1 : RuleCountOf(s) == 2);
            if (n > 0)
                seen.insert(s);
            previous = s;
        }
        CHECK(seen.size() == kHeroicPairs.size());
        CHECK(PickRuleSet({}, 0.5f) == RULE_NONE);
        std::vector<RuleSet> const two{ RULE_ASSEMBLY, RULE_DESKS };
        CHECK(PickRuleSet(two, 0.f) == RULE_ASSEMBLY);
        CHECK(PickRuleSet(two, 0.9999f) == RULE_DESKS);
    }
    // Timing: 3 / 4 s warning, a 6 s window, 25 s apart; the window always closes before the next announcement.
    CHECK(kRuleWarnMs(false) == 3000 && kRuleWarnMs(true) == 4000);
    CHECK(kRuleWindowMs == 6000 && kRuleFirstMs == 10000 && kRuleEveryMs == 25000);
    CHECK(kRuleWarnMs(true) + kRuleWindowMs < kRuleEveryMs);
    {
        RuleTimes const t{ 10000, 4000, 6000 };
        CHECK(t.PhaseAt(9999) == RulePhase::Idle);
        CHECK(t.PhaseAt(10000) == RulePhase::Warning);
        CHECK(t.PhaseAt(13999) == RulePhase::Warning);
        CHECK(t.PhaseAt(14000) == RulePhase::Window);
        CHECK(t.PhaseAt(19999) == RulePhase::Window);
        CHECK(t.PhaseAt(20000) == RulePhase::Idle);
    }

    // ---- AB9 the Dean's Rod (ruling 19): base + 50% of the base per Demerit held, capped at the 5th ---------------
    {
        float const normal[] = { 20.f, 30.f, 40.f, 50.f, 60.f, 60.f, 60.f };
        float const heroic[] = { 30.f, 45.f, 60.f, 75.f, 90.f, 90.f, 90.f };
        for (std::uint32_t held = 0; held < 7; ++held)
        {
            CHECK(Near(RodPct(false, held), normal[held]));
            CHECK(Near(RodPct(true, held), heroic[held]));
        }
        CHECK(kDemeritCap == 5);
    }

    // ---- AB5 the thirds ---------------------------------------------------------------------------------------------
    CHECK(ThirdOf(kAlexeiSpawn.XY()) == 2);
    CHECK(ThirdOf(kDeedToCaerDarrow.XY()) == 2);
    CHECK(ThirdOf({ 180.f, -40.f }) == 0);
    CHECK(ThirdOf({ 180.f, -60.f }) == 1);
    CHECK(ThirdOf({ 180.f, -20.f }) == kThirdCount);
    for (std::size_t t = 0; t + 1 < kThirdCount; ++t)
        CHECK(Near(ThirdMinY(t), ThirdMaxY(t + 1)));       // the thirds tile the vault's length
    // Most of the group; a tie goes to the roll; nobody inside: the nearest; no players: Alexei's third.
    CHECK(PickForbiddenThird({ { 180.f, -88.f }, { 182.f, -85.f }, { 190.f, -40.f } }, 0.9f) == 2);
    CHECK(PickForbiddenThird({ { 180.f, -40.f }, { 180.f, -60.f } }, 0.f) == 0);
    CHECK(PickForbiddenThird({ { 180.f, -40.f }, { 180.f, -60.f } }, 0.99f) == 1);
    CHECK(PickForbiddenThird({ { 180.f, -25.f } }, 0.5f) == 0);
    CHECK(PickForbiddenThird({}, 0.5f) == 2);
    // The zone covers the whole vault across (x 168-197) and exactly the third along.
    for (std::size_t t = 0; t < kThirdCount; ++t)
    {
        Strip const z = ThirdZone(t);
        CHECK(Near(z.from.y, ThirdMaxY(t)));
        CHECK(Near(z.length, ThirdMaxY(t) - ThirdMinY(t)));
        CHECK(z.from.x - 0.5f * z.width <= kVaultMinX && z.from.x + 0.5f * z.width >= kVaultMaxX);
        CHECK(Near(z.facing, 4.71238898f));
    }
    // The arena holds the whole vault frame.
    for (Vec2 corner : { Vec2{ 168.5f, -35.5f }, Vec2{ 196.5f, -35.5f }, Vec2{ 168.5f, -92.5f },
        Vec2{ 196.5f, -92.5f } })
        CHECK(AlexeiArena().Contains(corner, kVaultFloorZ));

    // ---- AB6 the lane -----------------------------------------------------------------------------------------------
    {
        LaneSpan const full = LaneFor(std::nullopt, -60.f);
        CHECK(Near(full.yMin, kVaultMinY) && Near(full.yMax, kVaultMaxY));
        CHECK(Near(full.Length(), 58.f));
        Strip const s = LaneStrip(full);
        CHECK(Near(s.width, 4.f) && Near(s.from.x, 194.5f) && Near(s.from.y, -35.f) && Near(s.length, 58.f));
        // Clear of the pit's east edge (x 192 at y -61 to -74) and inside the north strip.
        CHECK(s.from.x - 0.5f * s.width > 192.f);
        CHECK(s.from.x + 0.5f * s.width <= kBarovLaneMaxX);
        // Each forbidden third: the lane stays out of it, at least 8 yd long.
        for (std::size_t t = 0; t < kThirdCount; ++t)
            for (float groupY : { -40.f, -64.f, -88.f })
            {
                LaneSpan const lane = LaneFor(t, groupY);
                CHECK(lane.Length() >= kLaneMinLength);
                CHECK(lane.yMax < ThirdMinY(t) || lane.yMin > ThirdMaxY(t));
                CHECK(lane.yMin >= kVaultMinY - 0.01f && lane.yMax <= kVaultMaxY + 0.01f);
            }
        // Gate third forbidden: the lane runs Alexei's way; his third: the gate's way; the middle: nearer the group.
        CHECK(LaneFor(0, -40.f).yMax < -53.5f);
        CHECK(LaneFor(2, -88.f).yMin > -73.5f);
        CHECK(LaneFor(1, -40.f).yMin > -53.5f);
        CHECK(LaneFor(1, -88.f).yMax < -73.5f);
        CHECK(InLane(full, { 194.5f, -60.f }));
        CHECK(!InLane(full, { 190.f, -60.f }));
    }

    // ---- AB7 the desks ----------------------------------------------------------------------------------------------
    {
        // The first five are the build spec's (ScholomanceRework.h kBarovDesks).
        for (std::size_t i = 0; i < kCanonicalDesks; ++i)
            CHECK(Near(kDeskGrid[i].x, kBarovDesks[i].x) && Near(kDeskGrid[i].y, kBarovDesks[i].y));
        // Every pair at least 8 yd apart; all inside the vault.
        for (std::size_t i = 0; i < kDeskGrid.size(); ++i)
        {
            CHECK(InVault(kDeskGrid[i], 1.5f));            // the south lane is only 4 yd wide (x 168-172)
            for (std::size_t j = i + 1; j < kDeskGrid.size(); ++j)
                CHECK(DungeonKit::Distance(kDeskGrid[i], kDeskGrid[j]) >= kDeskMinApart - 0.01f);
        }
        // No Out of bounds: the five.
        CHECK(DeskCandidates(std::nullopt, 5).size() == 5);
        // Any third forbidden: 7 or more desks clear of it by a desk radius (five players need five).
        for (std::size_t t = 0; t < kThirdCount; ++t)
        {
            std::vector<Vec2> const c = DeskCandidates(t, 5);
            CHECK(c.size() >= 7);
            for (Vec2 d : c)
                CHECK(d.y + kDeskRadius < ThirdMinY(t) || d.y - kDeskRadius > ThirdMaxY(t));
        }
        // The assignment: one desk each, all different, the nearest first.
        std::vector<Vec2> const players{ { 192.f, -45.f }, { 190.f, -76.f }, { 180.f, -60.f }, { 175.f, -88.f },
            { 186.f, -50.f } };
        std::vector<Vec2> const five = DeskCandidates(std::nullopt, players.size());
        std::vector<std::size_t> const picks = AssignDesks(players, five);
        std::set<std::size_t> used;
        for (std::size_t p : picks)
        {
            CHECK(p != kNoDesk);
            used.insert(p);
        }
        CHECK(used.size() == players.size());
        CHECK(picks[0] == 0);       // standing on desk 1
        CHECK(picks[1] == 4);       // next to desk 5
        // More players than desks: the rest get none.
        std::vector<std::size_t> const short2 = AssignDesks(players, { five[0], five[1] });
        CHECK(std::count(short2.begin(), short2.end(), kNoDesk) == 3);
    }

    // ---- AB10 the fortune -------------------------------------------------------------------------------------------
    {
        std::vector<Vec2> const group{ { 180.f, -85.f }, { 183.f, -88.f }, { 176.f, -87.f }, { 186.f, -84.f } };
        FortuneRules rules;
        rules.set = RULE_NO_RUNNING;
        rules.players = group;
        // The band: 8-12 yd from the nearest player.
        CHECK(!FortuneFits({ 182.f, -82.f }, rules));
        CHECK(FortuneFits({ 180.f, -75.f }, rules));
        CHECK(!FortuneFits({ 180.f, -60.f }, rules));
        CHECK(!FortuneFits({ 160.f, -80.f }, rules));      // outside the vault
        // Out of bounds: inside the forbidden third only.
        rules.set = RuleSet(RULE_OUT_OF_BOUNDS | RULE_NO_RUNNING);
        rules.forbidden = 1;
        CHECK(!FortuneFits({ 180.f, -75.f }, rules));      // 1.5 yd past the third's edge: outside it
        CHECK(FortuneFits({ 186.f, -72.4f }, rules));     // inside it, 11.6 yd from the nearest player
        // Line up: off the lane.
        FortuneRules lane;
        lane.set = RULE_LINE_UP;
        lane.players = { { 194.5f, -50.f } };
        lane.lane = LaneFor(std::nullopt, -50.f);
        CHECK(!FortuneFits({ 194.5f, -60.f }, lane));
        CHECK(FortuneFits({ 186.f, -55.f }, lane));
        // Desks: off every desk.
        FortuneRules desks;
        desks.set = RULE_DESKS;
        desks.players = { { 192.5f, -45.f } };
        desks.desks = { { 192.5f, -53.f }, { 192.5f, -45.f } };
        CHECK(!FortuneFits({ 192.5f, -55.f }, desks));
        // The picks: as many as asked, each fits, heroic's two at least 6 yd apart.
        Lcg rng;
        for (std::size_t t = 0; t < kThirdCount; ++t)
        {
            FortuneRules r;
            r.set = RuleSet(RULE_OUT_OF_BOUNDS | RULE_ASSEMBLY);
            r.forbidden = t;
            r.players = { { 182.5f, (ThirdMinY(t) + ThirdMaxY(t)) * 0.5f + 2.f } };
            std::vector<Vec2> const spots = PickFortuneSpots(r, kFortunesPerRule(true), rng, [](Vec2) { return true; });
            CHECK(spots.size() == kFortunesPerRule(true));
            for (Vec2 p : spots)
                CHECK(InThird(t, p) && InVault(p));
            if (spots.size() == 2)
                CHECK(DungeonKit::Distance(spots[0], spots[1]) >= kFortunesApartYd);
        }
        // No floor anywhere: nothing placed.
        CHECK(PickFortuneSpots(rules, 1, rng, [](Vec2) { return false; }).empty());
        CHECK(kFortunesPerRule(false) == 1 && kFortunesPerRule(true) == 2);
        CHECK(kIllGottenGainsPct == 40 && kIllGottenGainsMs == 15000);
    }

    // ---- AB11 Veil of Shadow: never during a rule ------------------------------------------------------------------
    CHECK(VeilMayStart(5000, false, 10000));
    CHECK(!VeilMayStart(8100, false, 10000));       // its 1.5 s cast would run into the announcement
    CHECK(!VeilMayStart(12000, true, 35000));
    CHECK(VeilMayStart(20000, false, 35000));

    // ---- The Barov Family Vault's solo lesson -----------------------------------------------------------------------
    {
        LessonRule const& oob = kLessonRules[0];
        LessonRule const& still = kLessonRules[1];
        CHECK(oob.rule == RULE_OUT_OF_BOUNDS && still.rule == RULE_NO_RUNNING);
        // Both rules end inside the 15 s lesson, with time to spare for the last tick.
        for (LessonRule const& r : kLessonRules)
            CHECK(r.times.CloseMs() + 250 <= kLessonMs);
        // No running is read while Out of bounds still runs; its window opens after that one closes.
        CHECK(still.times.announceMs < oob.times.CloseMs());
        CHECK(still.times.OpenMs() >= oob.times.CloseMs());
        // The student lands on Alexei's spot in his third, 17.6 yd from its edge: 4 s to get out.
        CHECK(ThirdOf(kClassroomLandings[std::size_t(Classroom::BarovVault)].XY()) == 2);
        CHECK(oob.times.warnMs >= 4000);
        CHECK(oob.fortuneMaxYd <= 8.f && still.fortuneMaxYd <= 6.f);   // "in reach"
        // The failure hit (SoloLesson.h): 15% normal, 25% heroic.
        CHECK(kLessonFailurePctNormal == 15 && kLessonFailurePctHeroic == 25);
    }

    // ---- The Graduate Examiner (S13) --------------------------------------------------------------------------------
    CHECK(kExaminerHealth == 80000);
    CHECK(kExaminerHeroic);
    CHECK(kExaminerFirstRuleMs < 22000);            // a gauntlet room lasts about 22 s
    CHECK(kExaminerFirstRuleMs + kRuleWarnMs(true) + kRuleWindowMs <= kExaminerRuleEveryMs + kExaminerFirstRuleMs);

    // ---- Numbers (handoff section 3.6) ------------------------------------------------------------------------------
    CHECK(kNormalHealth == 160000 && kHeroicHealth == 250000);
    CHECK(std::lround(52.425 * 3052) == 160001);    // the dbc-tools HealthModifier on the warrior base

    return Report("scholo_alexei_test");
}
