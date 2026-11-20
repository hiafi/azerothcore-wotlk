// Host tests for GerstahnLogic.h (D1: High Interrogator Gerstahn): the slice and the arena (S0's), the Doubt and
// Knowledge rules, the Shadow Word: Pain ticks that add Doubt, the Mind Flay pick, the Mind Sear reach, the percents
// and the beats against the build spec (S1 181-228).
#include "GerstahnLogic.h"
#include "check.h"

#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdGerstahn;

namespace
{
    bool Near(float a, float b)
    {
        return a - b < 0.001f && b - a < 0.001f;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, in declaration order.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210720 && kSpellSlice.last == 210749);
        CHECK(SPELL_GE_DOUBT == 210720);
        CHECK(SPELL_GE_SHADOW_WORD_PAIN == 210725);
        CHECK(SPELL_GE_MIND_FLAY == 210726);
        CHECK(SPELL_GE_LINGERING_DOUBT == 210733);
        for (std::uint32_t id = SPELL_GE_DOUBT; id <= SPELL_GE_LINGERING_DOUBT; ++id)
            CHECK(kSpellSlice.Contains(id));
        // The stock spells are never ids of the slice (rule 15: copies, never edits).
        for (std::uint32_t stock : { SPELL_STOCK_SHADOW_WORD_PAIN, SPELL_STOCK_MANA_BURN, SPELL_STOCK_PSYCHIC_SCREAM,
                 SPELL_STOCK_SHADOW_SHIELD })
            CHECK(!kSpellSlice.Contains(stock));
        CHECK(ShieldSpell(false) == SPELL_GE_SHADOW_SHIELD);
        CHECK(ShieldSpell(true) == SPELL_GE_SHADOW_SHIELD_H);
    }

    void TestArena()
    {
        // High Interrogator Gerstahn spawns kGerstahnSpawn, inside the arena; the Circle around her spawn fits it.
        CHECK(GerstahnArena().Contains(kGerstahnSpawn.XY(), kGerstahnSpawn.z));
        CHECK(ArenaFor(BOSS_GERSTAHN).Contains(kGerstahnSpawn.XY(), kGerstahnSpawn.z));
        CHECK(GerstahnArena().Contains({ kGerstahnSpawn.x + kCircleRadius + 1.f, kGerstahnSpawn.y },
            kGerstahnSpawn.z));
        // The texts sit in her range (0-4, all new).
        CHECK(SAY_PULL == 0 && SAY_DEATH == 4);
        bool found = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_GERSTAHN)
            {
                found = true;
                CHECK(range.first == SAY_PULL && range.last == SAY_DEATH && range.firstNew == 0);
            }
        CHECK(found);
    }

    void TestDoubt()
    {
        // A step below 5 just adds; at 5 or more the player breaks and Doubt goes to 0 (the excess is lost).
        CHECK(AddDoubt(0, 1).stacks == 1 && !AddDoubt(0, 1).broke);
        CHECK(AddDoubt(3, 1).stacks == 4 && !AddDoubt(3, 1).broke);
        CHECK(AddDoubt(4, 1).broke && AddDoubt(4, 1).stacks == 0);
        CHECK(AddDoubt(4, 3).broke && AddDoubt(4, 3).stacks == 0);
        CHECK(AddDoubt(2, 3).broke);                    // the Circle breaks anyone at 2 or more
        CHECK(!AddDoubt(1, 3).broke && AddDoubt(1, 3).stacks == 4);
        CHECK(!AddDoubt(4, 0).broke && AddDoubt(4, 0).stacks == 4);
        // Mind Flay's three ticks break anyone at 2 or more (S1 GE3); a player at 1 ends at 4.
        std::uint32_t at = 2;
        bool broke = false;
        for (std::uint32_t t = 0; t < kFlayTicks; ++t)
        {
            DoubtStep const step = AddDoubt(at, kFlayDoubtPerTick);
            broke = broke || step.broke;
            at = step.stacks;
        }
        CHECK(broke);
        at = 1;
        broke = false;
        for (std::uint32_t t = 0; t < kFlayTicks; ++t)
        {
            DoubtStep const step = AddDoubt(at, kFlayDoubtPerTick);
            broke = broke || step.broke;
            at = step.stacks;
        }
        CHECK(!broke && at == 4);
        // The swirl at 4 only.
        CHECK(!SwirlOn(0) && !SwirlOn(3) && SwirlOn(4) && !SwirlOn(5));
    }

    void TestKnowledge()
    {
        // Normal: one a break up to 5; heroic: no cap but the aura's counter.
        CHECK(KnowledgeAfterBreak(0, false) == 1);
        CHECK(KnowledgeAfterBreak(4, false) == 5);
        CHECK(KnowledgeAfterBreak(5, false) == 5);
        CHECK(KnowledgeAfterBreak(5, true) == 6);
        CHECK(KnowledgeAfterBreak(40, true) == 41);
        CHECK(KnowledgeAfterBreak(255, true) == 255);
        CHECK(KnowledgeStackLimit(false) == 5 && KnowledgeStackLimit(true) == 255);
        // +10% a stack.
        CHECK(Near(KnowledgeScale(0), 1.f));
        CHECK(Near(KnowledgeScale(1), 1.1f));
        CHECK(Near(KnowledgeScale(5), 1.5f));
        CHECK(Near(ScaledPct(SPELL_GE_CIRCLE, false, 5), 22.5f));
        CHECK(Near(ScaledPct(SPELL_GE_MIND_FLAY, true, 0), 8.f));
    }

    void TestPain()
    {
        // Normal: ticks 2, 4, 6 (a Doubt every 6 s); heroic: every tick (6 a cast).
        CHECK(kPainTicks == 6);
        CHECK(!PainTickAddsDoubt(1, false) && PainTickAddsDoubt(2, false) && PainTickAddsDoubt(6, false));
        CHECK(PainTickAddsDoubt(1, true) && PainTickAddsDoubt(6, true));
        CHECK(!PainTickAddsDoubt(0, true) && !PainTickAddsDoubt(7, true) && !PainTickAddsDoubt(7, false));
        CHECK(PainDoubtPerCast(false) == 3);
        CHECK(PainDoubtPerCast(true) == 6);
    }

    void TestPercents()
    {
        // S1 "Build spec" N / H.
        CHECK(Near(BasePct(SPELL_GE_SHADOW_WORD_PAIN, false), 2.f));
        CHECK(Near(BasePct(SPELL_GE_SHADOW_WORD_PAIN, true), 3.f));
        CHECK(Near(BasePct(SPELL_GE_MIND_FLAY, false), 6.f) && Near(BasePct(SPELL_GE_MIND_FLAY, true), 8.f));
        CHECK(Near(BasePct(SPELL_GE_CIRCLE, false), 15.f) && Near(BasePct(SPELL_GE_CIRCLE, true), 25.f));
        CHECK(Near(BasePct(SPELL_GE_MIND_SEAR_TICK, false), 3.f) && Near(BasePct(SPELL_GE_MIND_SEAR_TICK, true), 5.f));
        // Dread: 30% / 40% over 10 s in five ticks.
        CHECK(Near(BasePct(SPELL_GE_DREAD, false) * kDreadTicks, kDreadTotalPct(false)));
        CHECK(Near(BasePct(SPELL_GE_DREAD, true) * kDreadTicks, kDreadTotalPct(true)));
        // Spells without damage.
        CHECK(Near(BasePct(SPELL_GE_DOUBT, false), 0.f) && Near(BasePct(SPELL_GE_MIND_SEAR, true), 0.f));
        CHECK(kShieldAbsorb(false) == 4000 && kShieldAbsorb(true) == 6500);
        CHECK(kBrokenMs == 2000);   // the shared doc's 2 s loss of control limit
    }

    void TestFlay()
    {
        auto first = [](std::uint32_t) { return 0u; };
        auto last = [](std::uint32_t n) { return n - 1; };
        // The most Doubt wins.
        std::vector<FlayCandidate> c{ { 1, 0 }, { 2, 3 }, { 3, 1 } };
        CHECK(PickFlayTarget(c, first) == std::optional<std::size_t>(1));
        CHECK(PickFlayTarget(c, last) == std::optional<std::size_t>(1));
        // A tie goes to the roll among the tied only.
        std::vector<FlayCandidate> tie{ { 1, 2 }, { 2, 0 }, { 3, 2 } };
        CHECK(PickFlayTarget(tie, first) == std::optional<std::size_t>(0));
        CHECK(PickFlayTarget(tie, last) == std::optional<std::size_t>(2));
        // Nobody with Doubt: anyone (random), the tank included.
        std::vector<FlayCandidate> none{ { 1, 0 }, { 2, 0 } };
        CHECK(PickFlayTarget(none, last) == std::optional<std::size_t>(1));
        // A roll out of range is clamped.
        auto wild = [](std::uint32_t) { return 99u; };
        CHECK(PickFlayTarget(tie, wild) == std::optional<std::size_t>(2));
        CHECK(!PickFlayTarget(std::vector<FlayCandidate>{}, first));
    }

    void TestSear()
    {
        CHECK(InSear(0.f, 0.f));
        CHECK(InSear(8.f, 0.f));
        CHECK(!InSear(8.1f, 0.f));
        CHECK(InSear(3.f, -5.f));
        CHECK(!InSear(3.f, 6.f));
        CHECK(kSearTicks == 5);
    }

    void TestBeats()
    {
        // S1 GE2-GE7 first / cooldown, normal / heroic.
        CHECK(kPainBeat(false).firstMs == 4000 && kPainBeat(false).everyMs == 8000 && kPainBeat(true).everyMs == 6000);
        CHECK(kFlayBeat(false).firstMs == 8000 && kFlayBeat(false).everyMs == 12000
            && kFlayBeat(true).everyMs == 10000);
        CHECK(kCircleBeat(false).firstMs == 15000 && kCircleBeat(false).everyMs == 25000
            && kCircleBeat(true).everyMs == 20000);
        CHECK(kSearBeat(false).firstMs == 20000 && kSearBeat(false).everyMs == 20000
            && kSearBeat(true).everyMs == 15000);
        CHECK(kShieldBeat(false).firstMs == 8000 && kShieldBeat(false).everyMs == 25000
            && kShieldBeat(true).everyMs == 25000);
        // A Mind Flay channel is over before the next one is due.
        CHECK(kFlayMs < kFlayBeat(true).everyMs);
        // The clock: start to start, never in the past.
        BeatClock clock;
        CHECK(!clock.Due(100000));
        clock.Start(0, 4000);
        CHECK(!clock.Due(3999) && clock.Due(4000));
        clock.Fired(4500, 8000);
        CHECK(clock.DueMs() == 12000);
        clock.Fired(40000, 8000);
        CHECK(clock.DueMs() == 48000);
        clock.Stop();
        CHECK(!clock.Due(100000));
        // The heroic pools (S1 heroic space math, NAVMESH 1.1): three at once fit 160-240 sq yd.
        CHECK(PoolArea(kPoolsAtOnce) >= 160.f && PoolArea(kPoolsAtOnce) <= 240.f);
        CHECK(kPoolWarnMs < kPoolMs && kPoolTickMs == 1000);
    }
}

int main()
{
    TestSlice();
    TestArena();
    TestDoubt();
    TestKnowledge();
    TestPain();
    TestPercents();
    TestFlay();
    TestSear();
    TestBeats();
    return Report("brd_gerstahn_test");
}
