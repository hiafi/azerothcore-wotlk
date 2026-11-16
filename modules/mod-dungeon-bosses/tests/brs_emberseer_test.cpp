// Host tests for EmberseerLogic.h (B10: Pyroguard Emberseer): the slice, the text range and the post geometry, what a
// stack changes (damage, the nova, the rings, Furnace Heat, the lines), one Furnace Pulse as the kit plans it with the
// user's rolling front rulings (ring 1 shown 5 s ahead, the nova on 2.5 s, rings 2-4 from the apex), the post timing
// (the flare after the last ring passed 21 yd, the firing 8 s later, the next pulse held so its first ring cannot reach
// 15 yd first), the post picks, and the SP growth math over a whole fight (FightModel). The bots' ring and nova hits
// are tests/brs_emberseer_bots_test.cpp (it needs mod-boss-mechanics' solver).
#include "EmberseerLogic.h"
#include "check.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <set>
#include <string>
#include <utility>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsEmberseer;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceTextsAndRoom()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { SPELL_EM_GROWTH_DAMAGE, SPELL_EM_GROWTH_DAMAGE_H, SPELL_EM_FURNACE_HEAT,
                 SPELL_EM_NOVA, SPELL_EM_RING, SPELL_EM_BODY_FLARE, SPELL_EM_RING_LAUNCH, SPELL_EM_FIRE_NOVA_BURST,
                 SPELL_EM_FULL_STRENGTH, SPELL_EM_SUPERNOVA, SPELL_EM_PYROBLAST, SPELL_EM_SMOLDER,
                 SPELL_EM_FLARE_COLUMN, SPELL_EM_ENCAGE_BEAM, SPELL_EM_SEARING_BOND, SPELL_EM_SEARED,
                 SPELL_EM_UNSTABLE_POST, SPELL_EM_SEARING_STATE })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_EM_GROWTH_DAMAGE == 210350u);
        CHECK(SPELL_EM_PYROBLAST == 210360u);
        CHECK(SPELL_EM_SEARING_STATE == 210367u);
        CHECK(NPC_BRS_BINDING_POST == 300730u);
        CHECK(kCreaturesWave2.Contains(NPC_BRS_BINDING_POST));

        // Text range 9816 0-7, 0-3 stock (S0 section 6).
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_EMBERSEER)
            {
                found = true;
                CHECK(r.first == 0 && r.last == 7 && r.firstNew == 4);
                CHECK(TEXT_REGAIN_STRENGTH < r.firstNew && TEXT_THANK_YOU < r.firstNew);
                CHECK(TEXT_POSTS_SMOLDER >= r.firstNew && TEXT_UNSTABLE_POSTS <= r.last);
            }
        CHECK(found);

        // He spawns on his dais, inside his arena; the hall bounds sit inside the arena too.
        CHECK(EmberseerArena().Contains(kEmberseerSpawn.XY(), kEmberseerSpawn.z));
        CHECK(ArenaFor(BOSS_EMBERSEER).Contains(kEmberseerSpawn.XY(), kEmberseerSpawn.z));
        CHECK(kHallMinX > 114.5f && kHallMaxX < 174.5f && kHallMinY > -288.7f && kHallMaxY < -228.7f);
        CHECK(kEmberseerSpawn.x > kHallMinX && kEmberseerSpawn.x < kHallMaxX);
        CHECK(kEmberseerSpawn.y > kHallMinY && kEmberseerSpawn.y < kHallMaxY);

        // The seven posts (handoff section 3.8): inside the hall, axis posts 17-18 yd and diagonals about 25 yd from
        // the dais, never closer than 14 yd to one another, so a 6 yd eruption never reaches a neighbor's 3 yd circle.
        std::vector<float> fromDais;
        for (Vec2 const& p : kEmberseerPosts)
        {
            CHECK(p.x > kHallMinX + kUnstableYd && p.x < kHallMaxX - kUnstableYd);
            CHECK(p.y > kHallMinY + kUnstableYd && p.y < kHallMaxY - kUnstableYd);
            CHECK(EmberseerArena().Contains(p, kPostZ));
            fromDais.push_back(DungeonKit::Distance(p, kEmberseerSpawn.XY()));
        }
        std::sort(fromDais.begin(), fromDais.end());
        CHECK(fromDais.front() > 17.f && fromDais[2] < 18.5f && fromDais[3] > 24.5f && fromDais.back() < 26.f);
        float closest = 1000.f;
        for (std::size_t i = 0; i < kEmberseerPosts.size(); ++i)
            for (std::size_t j = i + 1; j < kEmberseerPosts.size(); ++j)
                closest = std::min(closest, DungeonKit::Distance(kEmberseerPosts[i], kEmberseerPosts[j]));
        CHECK(closest > 14.f && closest > kUnstableYd + kPostSoakYd);
        // The altar stands clear of every post's eruption.
        for (Vec2 const& p : kEmberseerPosts)
            CHECK(DungeonKit::Distance(p, kBlackrockAltar.XY()) > kUnstableYd);
        // A 45 yd front from the dais reaches every corner of the hall (41.3 to 42.4 yd).
        for (Vec2 const c : { Vec2{ kHallMinX, kHallMinY }, Vec2{ kHallMinX, kHallMaxY }, Vec2{ kHallMaxX, kHallMinY },
                 Vec2{ kHallMaxX, kHallMaxY } })
            CHECK(DungeonKit::Distance(c, kEmberseerSpawn.XY()) < kRingEndYd);
    }

    void TestGrowth()
    {
        // +3% (heroic +4%) on everything a stack; capped at 20.
        CHECK(Near(DamageMult(0, false), 1.f));
        CHECK(Near(DamageMult(10, false), 1.3f));
        CHECK(Near(DamageMult(10, true), 1.4f));
        CHECK(Near(DamageMult(25, false), 1.6f));
        // The nova: 7 yd, 13 yd at 20.
        CHECK(Near(NovaRadius(0), 7.f));
        CHECK(Near(NovaRadius(20), 13.f));
        CHECK(Near(NovaRadius(30), 13.f));
        // Rings: N 1 / 2 / 3 at 0-6 / 7-13 / 14+; H 2 / 3 / 4.
        CHECK(RingsFor(0, false) == 1 && RingsFor(6, false) == 1 && RingsFor(7, false) == 2);
        CHECK(RingsFor(13, false) == 2 && RingsFor(14, false) == 3 && RingsFor(20, false) == 3);
        CHECK(RingsFor(0, true) == 2 && RingsFor(7, true) == 3 && RingsFor(14, true) == 4 && RingsFor(20, true) == 4);
        // Furnace Heat: 0.5% + 0.1% a stack, not raised again.
        CHECK(Near(HeatPct(0), 0.5f) && Near(HeatPct(10), 1.5f) && Near(HeatPct(20), 2.5f));
        CHECK(Near(HitPct(SPELL_EM_FURNACE_HEAT, 10, true), 1.5f));
        // The hits: nova and rings 30%, Supernova 50%, Pyroblast 40% / 50%, each x DamageMult.
        CHECK(Near(HitPct(SPELL_EM_NOVA, 0, false), 30.f));
        CHECK(Near(HitPct(SPELL_EM_RING, 10, false), 39.f));
        CHECK(Near(HitPct(SPELL_EM_SUPERNOVA, 20, false), 80.f));
        CHECK(Near(HitPct(SPELL_EM_SUPERNOVA, 20, true), 90.f));
        CHECK(Near(HitPct(SPELL_EM_PYROBLAST, 5, false), 46.f));
        CHECK(Near(HitPct(SPELL_EM_PYROBLAST, 5, true), 60.f));
        CHECK(Near(HitPct(SPELL_EM_SMOLDER, 5, true), 0.f));
        // Lines 0 and 1 move to 7 and 14 stacks; a jump over both says line 1 only.
        CHECK(StrengthLine(6, 7) == std::optional<std::uint8_t>(TEXT_REGAIN_STRENGTH));
        CHECK(StrengthLine(13, 14) == std::optional<std::uint8_t>(TEXT_NEARLY_FULL));
        CHECK(StrengthLine(5, 15) == std::optional<std::uint8_t>(TEXT_NEARLY_FULL));
        CHECK(!StrengthLine(7, 8) && !StrengthLine(9, 7));
        CHECK(ClampStacks(-3) == 0 && ClampStacks(25) == 20);
        // The cage: 1 stack every 5 s, capped at 8 (a 25 s prelude: about 5).
        CHECK(kCageGrowMs == 5000 && kCageMaxStacks == 8 && 25000 / kCageGrowMs == 5);
        // The posts' push back is the same at any size: 2 posts x 2 = 4 posts x 1.
        CHECK(PostLoss(kBindingPosts.At(5), 5) == PostLoss(kBindingPosts.At(10), 10));
        CHECK(PostLoss(2, 5) == 4 && PostLoss(4, 6) == 4 && PostLoss(0, 5) == 0);
        CHECK(kBindingPosts.At(5) == 2 && kBindingPosts.At(6) == 4 && kUnstablePosts.At(5) == 2
            && kUnstablePosts.At(10) == 3);
        // At 10 players every post does something at each heroic flare (4 bind, 3 erupt).
        CHECK(kBindingPosts.At(10) + kUnstablePosts.At(10) == kPostCount);
    }

    void TestPulse()
    {
        for (bool heroic : { false, true })
            for (std::uint32_t stacks : { 0u, 5u, 9u, 16u, 20u })
            {
                Fronts::RingSequenceSpec const spec = PulseSpec(stacks, heroic, 1.f);
                std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(spec);
                CHECK(plan.size() == RingsFor(stacks, heroic));
                // Ring 1: registered at the pulse's start, 5 s warning, from the nova's edge (ruling 1).
                CHECK(plan[0].registerMs == 0 && plan[0].launchMs == kRingWarnMs);
                CHECK(Near(plan[0].startYd, NovaRadius(stacks)));
                // The nova registers at 2.5 s with a 2.5 s warning: it erupts as ring 1 launches.
                CHECK(kNovaCueMs + kNovaWarnMs == plan[0].launchMs && kEruptionMs == plan[0].launchMs);
                for (std::size_t k = 1; k < plan.size(); ++k)
                {
                    // Rings 2-4 from the apex (ruling 2), spaced 2 s (heroic 1.5 s), shown as the ring before launches.
                    CHECK(Near(plan[k].startYd, 0.f));
                    CHECK(plan[k].launchMs - plan[k - 1].launchMs == kRingSpacingMs(heroic));
                    CHECK(plan[k].registerMs == plan[k - 1].launchMs);
                    // Each slice turned 45 (heroic 60) degrees clockwise from the one before.
                    float const turn = Fronts::WrapPi(plan[k - 1].sliceBearing - plan[k].sliceBearing);
                    CHECK(Near(turn, Fronts::DegToRad(kTurnDeg(heroic)), 1e-4f));
                }
                CHECK(Near(spec.sliceDeg, heroic ? 45.f : 60.f));
                // The front rolls to 45 yd at 8 yd/s: ring 1 over (45 - nova) / 8 s after its launch.
                CHECK(plan[0].overMs - plan[0].launchMs == Fronts::MsOfSeconds((45.f - NovaRadius(stacks)) / 8.f));
            }
        // The first pulse erupts 8 s after the engage, so it starts 3 s after it.
        CHECK(kFirstPulseStartMs == 3000);
    }

    void TestPosts()
    {
        CHECK(IsPostPulse(0) && !IsPostPulse(1) && IsPostPulse(2) && !IsPostPulse(3));
        // Normal at 5 stacks: one ring from 8.5 yd launching at 5 s; it passes 21 yd 1.5625 s later.
        {
            Fronts::RingSequenceSpec const spec = PulseSpec(5, false, 0.f);
            std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(spec);
            CHECK(PostFlareMs(plan, spec) == 5000 + Fronts::MsOfSeconds((21.f - 8.5f) / 8.f));
            CHECK(PostFireMs(plan, spec) == PostFlareMs(plan, spec) + 8000);
        }
        // Heroic at 16 stacks: four rings, the last from the apex at 5 s + 3 x 1.5 s; it passes 21 yd 2.625 s later.
        {
            Fronts::RingSequenceSpec const spec = PulseSpec(16, true, 0.f);
            std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(spec);
            CHECK(PostFlareMs(plan, spec) == 9500 + Fronts::MsOfSeconds(21.f / 8.f));
        }
        // The hold: a pulse due before the posts fire waits until its first ring cannot reach 15 yd first.
        {
            Fronts::RingSequenceSpec const next = PulseSpec(16, true, 0.f);    // nova 11.8: ring 1 at 15 yd at launch
            std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(next);
            std::uint32_t const reach = Fronts::FirstReachMs(plan, next, kPostReachGuardYd);
            CHECK(reach == kRingWarnMs);
            CHECK(HeldPulseStart(12000, std::optional<std::uint64_t>(20125), next) == 20125 - reach);
            CHECK(HeldPulseStart(30000, std::optional<std::uint64_t>(20125), next) == 30000);
            CHECK(HeldPulseStart(12000, std::nullopt, next) == 12000);
        }
        // Picks: distinct posts, no unstable post among the binding ones, as many as the post count allows.
        std::uint32_t seed = 12345;
        auto rand = [&seed](std::uint32_t n)
        {
            seed = seed * 1664525u + 1013904223u;
            return (seed >> 8) % n;
        };
        std::array<std::uint32_t, kPostCount> bindHits{};
        for (int i = 0; i < 2000; ++i)
        {
            for (auto [b, u] : { std::pair{ 2u, 2u }, std::pair{ 4u, 3u }, std::pair{ 4u, 5u }, std::pair{ 2u, 0u } })
            {
                PostPick const p = PickPosts(b, u, rand);
                std::set<std::uint8_t> all(p.bind.begin(), p.bind.end());
                CHECK(p.bind.size() == b);
                CHECK(p.unstable.size() == std::min<std::size_t>(u, kPostCount - b));
                for (std::uint8_t x : p.unstable)
                    CHECK(all.insert(x).second);
                for (std::uint8_t x : all)
                    CHECK(x < kPostCount);
                if (b == 2 && u == 2)
                    for (std::uint8_t x : p.bind)
                        ++bindHits[x];
            }
        }
        // Every post comes up (uniform: about 2000 x 2 / 7 = 571 each).
        for (std::uint32_t h : bindHits)
            CHECK(h > 450 && h < 700);
    }

    void PrintTrace(char const* name, FightTrace const& t)
    {
        std::string const full = t.fullStrengthAtMs ? std::to_string(*t.fullStrengthAtMs / 1000) + "s" : "never";
        std::printf("emberseer fight %-34s stacks 30s %2u 60s %2u 75s %2u 90s %2u, full strength %s, supernovas %u, "
            "pulses %zu\n", name, t.StacksAt(30), t.StacksAt(60), t.StacksAt(75), t.StacksAt(90), full.c_str(),
            t.supernovas, t.pulses.size());
    }

    // The pulse / post rules hold over a whole fight: posts flare after the last ring passed 21 yd and fire before the
    // next pulse's first ring reaches 15 yd; pulses keep their cadence except where the post rule holds them.
    void CheckSpacing(FightTrace const& t, bool heroic)
    {
        for (std::size_t i = 0; i < t.pulses.size(); ++i)
        {
            PulseRecord const& p = t.pulses[i];
            CHECK(p.posts == IsPostPulse(p.index));
            CHECK(p.eruptionMs == p.startMs + kEruptionMs);
            if (p.posts)
            {
                CHECK(p.flareMs == p.lastPass21Ms && p.fireMs == p.flareMs + kPostWindowMs);
                if (i + 1 < t.pulses.size())
                    CHECK(t.pulses[i + 1].firstReach15Ms >= p.fireMs);
            }
            if (i > 0)
            {
                std::uint64_t const gap = p.startMs - t.pulses[i - 1].startMs;
                CHECK(gap >= kPulseEveryMs(heroic));
                if (!t.pulses[i - 1].posts)
                    CHECK(gap == kPulseEveryMs(heroic));
            }
        }
    }

    void TestFightModel()
    {
        // SP growth math (normal): every post held, about 8 stacks at a 1:15 kill; no post held, Full Strength at
        // about 1:30 (5 + 90 / 6 = 20).
        FightSetup n;
        FightTrace const held = SimulateFight(n);
        PrintTrace("normal 5, every post held", held);
        CHECK(held.StacksAt(75) >= 6 && held.StacksAt(75) <= 10);
        CHECK(!held.fullStrengthAtMs);
        CheckSpacing(held, false);
        CHECK(held.pulses.front().startMs == kFirstPulseStartMs && held.pulses.front().eruptionMs == 8000);

        FightSetup none = n;
        none.postsHeld = 0.f;
        FightTrace const missed = SimulateFight(none);
        PrintTrace("normal 5, no post held", missed);
        CHECK(missed.fullStrengthAtMs && *missed.fullStrengthAtMs >= 85000 && *missed.fullStrengthAtMs <= 95000);
        CHECK(missed.supernovas > 0);
        CheckSpacing(missed, false);
        // Two rings for the last third with every post held; three rings without.
        CHECK(RingsFor(held.StacksAt(75), false) <= 2 && RingsFor(missed.StacksAt(85), false) == 3);

        // The same push back at 10 players (4 posts x 1).
        FightSetup ten = n;
        ten.players = 10;
        FightTrace const heldTen = SimulateFight(ten);
        PrintTrace("normal 10, every post held", heldTen);
        CHECK(heldTen.StacksAt(75) == held.StacksAt(75));

        // Landed Pyroblasts each add 1.
        FightSetup pyro = n;
        pyro.pyroblastLands = true;
        FightTrace const fed = SimulateFight(pyro);
        PrintTrace("normal 5, held, Pyroblasts land", fed);
        CHECK(fed.StacksAt(75) > held.StacksAt(75));

        // Heroic: 15 a minute, posts 10 a minute (every 24 s), net +5; no post held: Full Strength at about 1:00.
        FightSetup h = n;
        h.heroic = true;
        FightTrace const heldH = SimulateFight(h);
        PrintTrace("heroic 5, every post held", heldH);
        CHECK(heldH.StacksAt(75) >= 9 && heldH.StacksAt(75) <= 14);
        CheckSpacing(heldH, true);
        FightSetup hNone = h;
        hNone.postsHeld = 0.f;
        FightTrace const missedH = SimulateFight(hNone);
        PrintTrace("heroic 5, no post held", missedH);
        CHECK(missedH.fullStrengthAtMs && *missedH.fullStrengthAtMs >= 55000 && *missedH.fullStrengthAtMs <= 65000);
        CheckSpacing(missedH, true);
        // One missed flare is +4 for the rest of the fight (heroic: a lasting setback).
        FightSetup hHalf = h;
        hHalf.postsHeld = 0.5f;
        FightTrace const halfH = SimulateFight(hHalf);
        PrintTrace("heroic 5, half the posts held", halfH);
        CHECK(halfH.StacksAt(75) > heldH.StacksAt(75));
        // Heroic at 14+ stacks the post rule holds a pulse a few seconds (SP: "about 1.5 s late" before the rings 2-4
        // ruling; the later rings from the apex pass 21 yd later now).
        std::uint64_t maxHeld = 0;
        for (PulseRecord const& p : missedH.pulses)
            maxHeld = std::max(maxHeld, p.heldByMs);
        std::printf("emberseer heroic, no post held: the longest post hold of a pulse %llu ms\n",
            static_cast<unsigned long long>(maxHeld));
        CHECK(maxHeld > 0 && maxHeld <= 5000);
        // Normal never holds (one ring at a time is far enough ahead).
        for (PulseRecord const& p : held.pulses)
            CHECK(p.heldByMs == 0);
    }
}

int main()
{
    TestSliceTextsAndRoom();
    TestGrowth();
    TestPulse();
    TestPosts();
    TestFightModel();
    return Report("brs_emberseer_test");
}
