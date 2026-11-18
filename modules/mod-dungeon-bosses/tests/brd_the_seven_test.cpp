// Host tests for TheSevenLogic.h (D21: The Seven): the slice, the ghosts (entries, moods, ranks, texts), the spec's
// numbers, the rotation (section 7 #18: Anger'rel alone 0-20 s, each ghost up 40 s, Doom'rel at 120 s, the spec's
// pairs), Gather Doom and the energy over whole turns (normal and heroic, with and without kicks: "blocking a mood
// takes 3 interrupts", at most one mood a turn), the kit table (stock timers, nothing retired, no DD double-use id),
// the picks (Furious Charge's target, Seething Cold's loners as the registry's Cluster(2), Dopey Haze's stumble) and
// the pool's per-ghost HealthModifier.
#include "TheSevenLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdTheSeven;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    Body At(std::uint64_t id, float x, float y, float z = -85.6f)
    {
        return { id, x, y, z };
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211520 && kSpellSlice.last == 211579);
        CHECK(SPELL_TS_INCORPOREAL == 211520);
        CHECK(SPELL_TS_IMMOLATE == 211557);
        CHECK(kSpellSlice.Contains(kLastSpell));
        for (std::uint32_t id = SPELL_TS_INCORPOREAL; id <= kLastSpell; ++id)
            CHECK(kSpellSlice.Contains(id));
        // the mood bars are seven distinct ids of the slice
        std::set<std::uint32_t> bars(kMoodCast.begin(), kMoodCast.end());
        CHECK(bars.size() == kGhostCount);
        for (std::uint32_t bar : kMoodCast)
            CHECK(kSpellSlice.Contains(bar));
    }

    void TestGhosts()
    {
        // the rotation order is the stock release order (instance TombBossGUIDs)
        CHECK(EntryOf(GHOST_ANGERREL) == 9035);
        CHECK(EntryOf(GHOST_SEETHREL) == 9038);
        CHECK(EntryOf(GHOST_DOPEREL) == 9040);
        CHECK(EntryOf(GHOST_GLOOMREL) == 9037);
        CHECK(EntryOf(GHOST_VILEREL) == 9036);
        CHECK(EntryOf(GHOST_HATEREL) == 9034);
        CHECK(EntryOf(GHOST_DOOMREL) == 9039);
        for (std::uint8_t g = 0; g < kGhostCount; ++g)
        {
            Ghost const ghost = static_cast<Ghost>(g);
            CHECK(GhostOf(EntryOf(ghost)) == ghost);
            CHECK(BossOfEntry(EntryOf(ghost)) == BOSS_THE_SEVEN);
        }
        CHECK(!GhostOf(9033));
        CHECK(kConductor == GHOST_DOOMREL);
        CHECK(EntryOfBoss(BOSS_THE_SEVEN) == NPC_DOOMREL);

        // each ghost's mood
        CHECK(MoodOf(GHOST_ANGERREL) == Mood::FuriousCharge);
        CHECK(MoodOf(GHOST_SEETHREL) == Mood::SeethingCold);
        CHECK(MoodOf(GHOST_DOPEREL) == Mood::DopeyHaze);
        CHECK(MoodOf(GHOST_GLOOMREL) == Mood::Gloom);
        CHECK(MoodOf(GHOST_VILEREL) == Mood::VileCommunion);
        CHECK(MoodOf(GHOST_HATEREL) == Mood::Hatred);
        CHECK(MoodOf(GHOST_DOOMREL) == Mood::Doom);
        CHECK(kMoodCast[GHOST_ANGERREL] == SPELL_TS_FURIOUS_CHARGE_CAST);
        CHECK(kMoodCast[GHOST_VILEREL] == SPELL_TS_VILE_COMMUNION_CAST);
        CHECK(kMoodCast[GHOST_DOOMREL] == SPELL_TS_DOOM_CAST);

        // the kill order and the interrupt list: Vile'rel, Doom'rel, Anger'rel, Dope'rel, Hate'rel, Seeth'rel,
        // Gloom'rel
        CHECK(RankOf(GHOST_VILEREL) == 1);
        CHECK(RankOf(GHOST_DOOMREL) == 2);
        CHECK(RankOf(GHOST_ANGERREL) == 3);
        CHECK(RankOf(GHOST_DOPEREL) == 4);
        CHECK(RankOf(GHOST_HATEREL) == 5);
        CHECK(RankOf(GHOST_SEETHREL) == 6);
        CHECK(RankOf(GHOST_GLOOMREL) == 7);
        std::set<int> kill;
        std::set<int> kicks;
        for (std::uint8_t g = 0; g < kGhostCount; ++g)
        {
            Ghost const ghost = static_cast<Ghost>(g);
            CHECK(KillPriority(ghost) > 0);     // above the owner's 0
            CHECK(GatherKickPriority(ghost) > 0 && GatherKickPriority(ghost) < kVileCommunionKick);
            kill.insert(KillPriority(ghost));
            kicks.insert(GatherKickPriority(ghost));
        }
        CHECK(kill.size() == kGhostCount && kicks.size() == kGhostCount);
        CHECK(KillPriority(GHOST_VILEREL) > KillPriority(GHOST_DOOMREL));
        CHECK(KillPriority(GHOST_SEETHREL) > KillPriority(GHOST_GLOOMREL));
        CHECK(GatherKickPriority(GHOST_VILEREL) > GatherKickPriority(GHOST_ANGERREL));
        CHECK(kDispelFrostNova >= 1);
    }

    void TestTexts()
    {
        // a rise line and a mood line per ghost, inside its text range; Doom'rel's group 0 is his stock challenge
        for (std::uint8_t g = 0; g < kGhostCount; ++g)
        {
            Ghost const ghost = static_cast<Ghost>(g);
            bool found = false;
            for (TextRange const& r : kTextRanges)
                if (r.entry == EntryOf(ghost))
                {
                    found = true;
                    CHECK(RiseText(ghost) >= r.firstNew && RiseText(ghost) <= r.last);
                    CHECK(MoodText(ghost) >= r.firstNew && MoodText(ghost) <= r.last);
                    CHECK(RiseText(ghost) != MoodText(ghost));
                }
            CHECK(found);
        }
        CHECK(RiseText(GHOST_DOOMREL) == 1 && MoodText(GHOST_DOOMREL) == 2);
        CHECK(RiseText(GHOST_ANGERREL) == 0 && MoodText(GHOST_ANGERREL) == 1);
        CHECK(SAY_DOOMREL_CHALLENGE == 0);
    }

    void TestTuning()
    {
        // S4 "Tuning starting points" and "New mechanics"
        CHECK(kPoolHealth.normal == 320000 && kPoolHealth.heroic == 450000);
        CHECK(kShadeDamageTakenPct == -90);
        CHECK(kStepMs == 20000 && kTurnMs == 40000);
        CHECK(kGatherCastMs.normal == 3000 && kGatherCastMs.heroic == 2000);
        CHECK(kGatherEveryMs.normal == 8000 && kGatherEveryMs.heroic == 6000);
        CHECK(kGatherFirstMs == 3000 && kEnergyFull == 3 && kMoodCastMs == 3000);
        CHECK(Near(kChargePct.normal, 30.f) && Near(kChargePct.heroic, 45.f));
        CHECK(kChargeLifeMs == 9000 && kChargeEveryMs == 3000 && kChargeCount == 3);
        CHECK(Near(kChargeSafeYd, 10.f) && Near(kChargeWidthYd, 3.f));
        CHECK(Near(kColdPct.normal, 6.f) && Near(kColdPct.heroic, 10.f));
        CHECK(Near(kColdRadiusYd, 6.f) && kColdMinOthers == 2 && kColdLifeMs == 10000 && kColdTicks == 10);
        CHECK(kColdSlowPct == 30);
        CHECK(Near(kStumblePct.normal, 15.f) && Near(kStumblePct.heroic, 25.f));
        CHECK(kHazeLifeMs == 6000 && kHazeTicks == 6);
        CHECK(kGloomMs == 12000 && kGloomHealingPct == -50 && kRecklessnessPct == 50);
        CHECK(Near(kVileHealPct.normal, 5.f) && Near(kVileHealPct.heroic, 8.f));
        CHECK(kVileChannelMs == 6000 && kVileTicks == 6);
        CHECK(Near(VileTickPct(false) * kVileTicks, 5.f) && Near(VileTickPct(true) * kVileTicks, 8.f));
        CHECK(Near(kHatredPct.normal, 5.f) && Near(kHatredPct.heroic, 8.f));
        CHECK(Near(kHatredRadiusYd, 6.f) && kHatredLifeMs == 8000 && kHatredTicks == 8);
        CHECK(kDoomMarks.normal == 1 && kDoomMarks.heroic == 2);
        CHECK(Near(kDoomOthersPct.normal, 30.f) && Near(kDoomOthersPct.heroic, 45.f));
        CHECK(Near(kDoomSelfPct.normal, 20.f) && Near(kDoomSelfPct.heroic, 30.f));
        CHECK(Near(kDoomRadiusYd, 10.f) && kDoomMarkMs == 6000);
        CHECK(kFrostNovaRootMs == 2000 && kGougeMs == 2000);    // TS10: the 2 s rule
        // the G2 drill's loner row is this mood's Stack (tag 22)
        CHECK(TAG_TS_SEETHING_COLD == 22);
        std::set<std::uint32_t> tags{ TAG_TS_SEETHING_COLD, TAG_TS_FURIOUS_CHARGE, TAG_TS_FURIOUS_STACK,
            TAG_TS_DOPEY_HAZE, TAG_TS_HATRED, TAG_TS_DOOM };
        CHECK(tags.size() == 6);
        // the "stock rescaled" percents: heroic never below normal, all in a sane band
        for (NH<float> const& pct : { kFrostboltPct, kConeOfColdPct, kFrostNovaPct, kBackstabPct, kRupturePct,
            kGougePct, kMindBlastPct, kShadowBoltPct, kVolleyPct, kImmolatePct, kImmolateTickPct })
        {
            CHECK(pct.normal > 0.f && pct.heroic >= pct.normal && pct.heroic <= 30.f);
        }
    }

    void TestRotation()
    {
        // the steps: ghost n mod 7 rises, ghost (n - 2) mod 7 fades from step 2 on
        for (std::uint32_t n = 0; n < 30; ++n)
        {
            RotationStep const s = StepAt(n);
            CHECK(s.rise && *s.rise == n % kGhostCount);
            CHECK(bool(s.fade) == (n >= 2));
            if (n >= 2)
                CHECK(*s.fade == (n - 2) % kGhostCount);
        }
        CHECK(*StepAt(0).rise == GHOST_ANGERREL);
        CHECK(*StepAt(6).rise == GHOST_DOOMREL && StepTimeMs(6) == 120000);     // Doom'rel rises at 120 s
        CHECK(*StepAt(7).rise == GHOST_ANGERREL && *StepAt(7).fade == GHOST_HATEREL);

        // Anger'rel alone for 0-20 s
        for (std::uint64_t t = 0; t < 20000; t += 100)
        {
            auto const c = CorporealAt(t);
            CHECK(c[GHOST_ANGERREL] && std::count(c.begin(), c.end(), true) == 1);
        }

        // at most two corporeal; each ghost up exactly 40 s a cycle; the spec's pairs; Seeth'rel and Hate'rel never
        // together
        std::array<std::uint64_t, kGhostCount> up{};
        std::set<std::pair<int, int>> pairs;
        std::uint64_t const cycle = std::uint64_t(kGhostCount) * kStepMs;      // 140 s
        for (std::uint64_t t = 0; t < 2 * cycle; t += 100)
        {
            auto const c = CorporealAt(t);
            int const n = int(std::count(c.begin(), c.end(), true));
            CHECK(n >= 1 && n <= 2);
            CHECK(!(c[GHOST_SEETHREL] && c[GHOST_HATEREL]));
            std::vector<int> on;
            for (std::uint8_t g = 0; g < kGhostCount; ++g)
                if (c[g])
                {
                    on.push_back(g);
                    if (t >= cycle)
                        up[g] += 100;
                }
            if (on.size() == 2)
                pairs.insert({ std::min(on[0], on[1]), std::max(on[0], on[1]) });
        }
        for (std::uint64_t u : up)
            CHECK(u == kTurnMs);
        std::set<std::pair<int, int>> const spec{ { GHOST_ANGERREL, GHOST_SEETHREL }, { GHOST_SEETHREL, GHOST_DOPEREL },
            { GHOST_DOPEREL, GHOST_GLOOMREL }, { GHOST_GLOOMREL, GHOST_VILEREL }, { GHOST_VILEREL, GHOST_HATEREL },
            { GHOST_HATEREL, GHOST_DOOMREL }, { GHOST_ANGERREL, GHOST_DOOMREL } };
        CHECK(pairs == spec);
        // a clean kill (~143 s) sees all seven
        std::set<int> seen;
        for (std::uint64_t t = 0; t <= 143000; t += 100)
        {
            auto const c = CorporealAt(t);
            for (std::uint8_t g = 0; g < kGhostCount; ++g)
                if (c[g])
                    seen.insert(g);
        }
        CHECK(seen.size() == kGhostCount);

        // the clock: each step once, in order, when due
        Rotation r;
        CHECK(!r.Due(0));
        r.Start();
        std::optional<RotationStep> s0 = r.Due(0);
        CHECK(s0 && *s0->rise == GHOST_ANGERREL && !s0->fade);
        CHECK(!r.Due(19999));
        std::optional<RotationStep> s1 = r.Due(20000);
        CHECK(s1 && *s1->rise == GHOST_SEETHREL && !s1->fade);
        // a late update catches up step by step
        int caught = 0;
        while (r.Due(60000))
            ++caught;
        CHECK(caught == 2 && r.Next() == 4);
        r.Stop();
        CHECK(!r.Due(1000000));
    }

    // One turn of a ghost, as the engine runs it every 100 ms: Gather Doom when due and not casting; the casts in
    // `kicked` (0-based, in start order) are interrupted half way; a mood starts as soon as the energy is full.
    struct TurnRun
    {
        std::vector<std::uint64_t> starts;
        std::vector<std::uint64_t> moods;
    };

    TurnRun RunTurn(bool heroic, std::set<int> const& kicked)
    {
        TurnRun out;
        GhostTurn t;
        t.Rise(0, heroic);
        std::uint64_t castEnd = 0;
        bool casting = false;
        bool kickThis = false;
        for (std::uint64_t now = 0; now <= kTurnMs; now += 100)
        {
            if (casting && kickThis && now >= castEnd - t.CastMs() / 2)
            {
                t.GatherInterrupted();
                casting = false;
            }
            if (casting && now >= castEnd)
            {
                t.GatherLanded();
                casting = false;
            }
            if (casting)
                continue;
            if (t.MoodDue())
            {
                t.MoodStarted();
                out.moods.push_back(now);
                continue;
            }
            if (t.GatherDue(now))
            {
                kickThis = kicked.count(int(out.starts.size())) > 0;
                out.starts.push_back(now);
                t.GatherStarted(now);
                castEnd = now + t.CastMs();
                casting = true;
            }
        }
        return out;
    }

    void TestGatherDoom()
    {
        // normal: casts at 3, 11, 19 s; the third lands at 22 s, the mood then; nothing more this turn
        TurnRun const n0 = RunTurn(false, {});
        CHECK(n0.starts.size() == 3);
        CHECK(n0.starts[0] == 3000 && n0.starts[1] == 11000 && n0.starts[2] == 19000);
        CHECK(n0.moods.size() == 1 && n0.moods[0] == 22000);

        // "a ghost casts about 5 times in its 40 s turn, so blocking its mood takes 3 interrupts"
        TurnRun const n1 = RunTurn(false, { 0 });
        CHECK(n1.moods.size() == 1 && n1.moods[0] == 30000);
        TurnRun const n2 = RunTurn(false, { 0, 1 });
        CHECK(n2.starts.size() == 5 && n2.moods.size() == 1 && n2.moods[0] == 38000);
        TurnRun const n3 = RunTurn(false, { 0, 1, 2 });
        CHECK(n3.starts.size() == 5 && n3.moods.empty());
        CHECK(n3.starts.back() == 35000);       // the last cast that lands before the fade

        // heroic: 2 s every 6 s; the mood at 17 s; at most one mood a turn even though the casts could land two
        TurnRun const h0 = RunTurn(true, {});
        CHECK(h0.starts.size() == 3 && h0.moods.size() == 1 && h0.moods[0] == 17000);
        TurnRun const h3 = RunTurn(true, { 0, 1, 2 });
        CHECK(h3.starts.size() == 6 && h3.moods.size() == 1 && h3.moods[0] == 35000);
        TurnRun const h4 = RunTurn(true, { 0, 1, 2, 3 });
        CHECK(h4.moods.empty());

        // a cast the fade would cut is never started; nothing after the fade
        GhostTurn t;
        t.Rise(1000, false);
        CHECK(t.FadeAt() == 41000 && t.NextGather() == 4000);
        CHECK(!t.GatherDue(3999) && t.GatherDue(4000));
        t.GatherStarted(4000);
        CHECK(!t.GatherDue(4000));                       // one cast at a time
        CHECK(t.NextGather() == 12000);
        CHECK(!t.GatherLanded() && t.Energy() == 1);
        GhostTurn late;
        late.Rise(0, false);
        late.GatherRefused(36000);                       // the next is due at 44 s: past the fade
        CHECK(!late.GatherDue(44000));
        late.Fade();
        CHECK(!late.Active() && !late.MoodDue() && !late.GatherDue(45000));
        CHECK(!late.GatherLanded());                     // a cast landing after the fade gives nothing

        // a refused cast (silence) is a blocked one: no energy, the next on the cadence
        GhostTurn r;
        r.Rise(0, true);
        r.GatherStarted(3000);
        r.GatherRefused(3000);
        CHECK(!r.Gathering() && r.Energy() == 0 && r.NextGather() == 9000);

        // the kit waits for a Gather Doom: a 3 s Frostbolt at 1 s fits before 3 s... not at 1.5 s
        GhostTurn k;
        k.Rise(0, false);
        CHECK(k.KitCastFits(0, 3000));
        CHECK(!k.KitCastFits(1500, 3000));
        CHECK(k.KitCastFits(1500, 0));                   // instants always
        for (int i = 0; i < 3; ++i)
        {
            k.GatherStarted(3000);
            k.GatherLanded();
        }
        CHECK(k.MoodDue());
        CHECK(k.KitCastFits(1500, 3000));                // a full energy waits for nothing but the mood
        k.MoodStarted();
        CHECK(k.MoodSpent() && k.Energy() == 0 && !k.MoodDue() && !k.GatherDue(100000));
        CHECK(k.KitCastFits(0, 3000));

        // the rise starts a fresh turn (the energy does not carry over)
        GhostTurn c;
        c.Rise(0, false);
        c.GatherStarted(3000);
        c.GatherLanded();
        c.Fade();
        c.Rise(140000, false);
        CHECK(c.Energy() == 0 && !c.MoodSpent() && c.NextGather() == 143000);

        // `.dbtest brd seven mood`
        GhostTurn f;
        f.ForceFull();
        CHECK(!f.MoodDue());                             // a shade cannot
        f.Rise(0, true);
        f.ForceFull();
        CHECK(f.MoodDue() && f.Heroic());
    }

    void TestKit()
    {
        std::set<std::uint32_t> const retired{ 15044, 15585, 15586, 12493, 15092, 15093, 15094, 12540, 12674, 15232,
            15582, 12675, 15244, 15583, 15587, 15245, 12742 };
        std::set<std::uint32_t> const doubleUse{ 15232, 15305, 15472, 15530, 15582, 15616 };
        std::set<std::uint32_t> const stock{ SPELL_STOCK_STRIKE, SPELL_STOCK_SUNDER_ARMOR, SPELL_STOCK_SHIELD_BLOCK,
            SPELL_STOCK_SHIELD_WALL, SPELL_STOCK_SINISTER_STRIKE, SPELL_STOCK_EVASION, SPELL_STOCK_PW_SHIELD,
            SPELL_STOCK_DEMON_ARMOR };
        std::array<int, kGhostCount> rows{};
        for (KitRow const& row : kKit)
        {
            ++rows[row.ghost];
            CHECK(!retired.count(row.spell) && !doubleUse.count(row.spell));
            CHECK(kSpellSlice.Contains(row.spell) || stock.count(row.spell));
            CHECK(row.firstMinMs <= row.firstMaxMs && row.everyMinMs <= row.everyMaxMs && row.everyMinMs > 0);
            CHECK(row.castMs == 0 || row.castMs <= 3000);
        }
        CHECK(rows[GHOST_ANGERREL] == 4 && rows[GHOST_SEETHREL] == 3 && rows[GHOST_DOPEREL] == 5);
        CHECK(rows[GHOST_GLOOMREL] == 0 && rows[GHOST_VILEREL] == 2 && rows[GHOST_HATEREL] == 2);
        CHECK(rows[GHOST_DOOMREL] == 3);
        for (KitRow const& row : kKit)
        {
            if (row.spell == SPELL_TS_SHADOW_BOLT && row.target == KitTarget::Victim)
                CHECK(row.everyMinMs == 8000 && row.everyMaxMs == 10000);       // was 3.4-4.8 s
            if (row.spell == SPELL_TS_IMMOLATE)
                CHECK(row.firstMinMs == 18000 && row.everyMinMs == 25000 && row.target == KitTarget::Random);
            if (row.spell == SPELL_TS_GOUGE)
                CHECK(row.target == KitTarget::Random);                         // ruling 90: anyone
            if (row.spell == SPELL_TS_BACKSTAB)
                CHECK(row.target == KitTarget::VictimBehind);
        }
        CHECK(ArmorOf(GHOST_SEETHREL) == SPELL_STOCK_FROST_ARMOR && ArmorOf(GHOST_DOOMREL) == SPELL_STOCK_DEMON_ARMOR);
        CHECK(ArmorOf(GHOST_ANGERREL) == 0);
    }

    void TestPicks()
    {
        Body const anger = At(0, 1250.f, -240.f);
        // nobody beyond 10 yd: the harmless stomp
        std::vector<Body> close{ At(1, 1255.f, -240.f), At(2, 1250.f, -230.f), At(3, 1257.f, -247.f) };
        CHECK(!FarthestBeyond(anger, close, kChargeSafeYd));
        // the farthest beyond 10 yd
        std::vector<Body> spread{ At(1, 1255.f, -240.f), At(2, 1270.f, -240.f), At(3, 1250.f, -270.f),
            At(4, 1261.f, -240.f) };
        std::optional<std::size_t> const far = FarthestBeyond(anger, spread, kChargeSafeYd);
        CHECK(far && *far == 2);
        // exactly 10 yd is not beyond
        std::vector<Body> edge{ At(1, 1260.f, -240.f) };
        CHECK(!FarthestBeyond(anger, edge, kChargeSafeYd));
        // the line runs 2 yd past the target
        Body const end = ChargeEnd(anger, At(9, 1270.f, -240.f));
        CHECK(Near(end.x, 1272.f) && Near(end.y, -240.f));
        Body const same = ChargeEnd(anger, anger);
        CHECK(Near(same.x, anger.x) && Near(same.y, anger.y));

        // Seething Cold: Cluster(2) (G2's rule cases): all together, nobody
        std::vector<Body> five{ At(1, 0, 0), At(2, 1, 0), At(3, 0, 1), At(4, 2, 2), At(5, -1, 1) };
        CHECK(Loners(five, kColdRadiusYd, kColdMinOthers).empty());
        // a trio and a pair 20 yd apart: the pair are loners
        std::vector<Body> split{ At(1, 0, 0), At(2, 2, 0), At(3, 0, 2), At(4, 20, 0), At(5, 22, 0) };
        std::vector<std::size_t> const l = Loners(split, kColdRadiusYd, kColdMinOthers);
        CHECK(l.size() == 2 && l[0] == 3 && l[1] == 4);
        // a chain 5 yd apart: the ends have one neighbour each
        std::vector<Body> chain{ At(1, 0, 0), At(2, 5, 0), At(3, 10, 0), At(4, 15, 0), At(5, 20, 0) };
        std::vector<std::size_t> const ends = Loners(chain, kColdRadiusYd, kColdMinOthers);
        CHECK(ends.size() == 2 && ends[0] == 0 && ends[1] == 4);
        // the 6 yd edge counts (inclusive); the tank alone is a loner like anyone (ruling 88)
        std::vector<Body> rim{ At(1, 0, 0), At(2, 6, 0), At(3, -6, 0) };
        std::vector<std::size_t> const r = Loners(rim, kColdRadiusYd, kColdMinOthers);
        CHECK(r.size() == 2 && r[0] == 1 && r[1] == 2);
        // a player straight above on the raised tier (7.5 yd up) is not "with" the others
        std::vector<Body> tiers{ At(1, 0, 0, -85.6f), At(2, 1, 0, -85.6f), At(3, 0, 1, -78.1f) };
        CHECK(Loners(tiers, kColdRadiusYd, kColdMinOthers, 6.f).size() == 3);

        // Dopey Haze: a stumble needs more than 0.5 yd since the last beat
        CHECK(!Stumbled(At(1, 0, 0), At(1, 0.4f, 0)));
        CHECK(Stumbled(At(1, 0, 0), At(1, 0.6f, 0)));
        CHECK(!Stumbled(At(1, 0, 0), At(1, 0, 0, -80.f)));       // a fall straight down is no stumble
    }

    void TestPool()
    {
        // every ghost's template carries the whole pool: HealthModifier x class base within 2 of 320,000 at 3 decimals
        // (creature_classlevelstats basehp0, live 2026-11-17)
        for (std::uint32_t base : { 2614u, 2091u, 2699u, 2159u })
        {
            double const hm = std::round(PoolHealthModifier(base) * 1000.0) / 1000.0;
            CHECK(std::fabs(hm * base - 320000.0) <= 2.0);
        }
        CHECK(Near(float(PoolHealthModifier(2159)), 148.217f, 0.001f));
        CHECK(PoolHealthModifier(0) == 0.0);
    }

    void TestArena()
    {
        // every ghost's post (creature spawns, live 2026-11-17) is on the tomb's arena
        std::array<Point3, kGhostCount> const posts{ { { 1215.05f, -220.656f, -85.59f },
            { 1286.56f, -253.331f, -78.06f }, { 1236.55f, -291.534f, -78.14f }, { 1226.69f, -246.124f, -85.59f },
            { 1272.32f, -199.817f, -85.59f }, { 1246.18f, -189.969f, -85.59f }, { 1281.14f, -282.151f, -78.14f } } };
        for (Point3 const& p : posts)
        {
            CHECK(TheSevenArena().Contains(p.XY(), p.z));
            CHECK(ArenaFor(BOSS_THE_SEVEN).Contains(p.XY(), p.z));
        }
        CHECK(TheSevenArena().Contains(kAngerrelSpawn.XY(), kAngerrelSpawn.z));
        CHECK(TheSevenArena().Contains(kDoomrelSpawn.XY(), kDoomrelSpawn.z));
        // the doors' own spots (the entrance (1230, -205), the exit (1263, -294)) are inside too: no edge at a door
        CHECK(TheSevenArena().Contains({ 1230.3f, -205.2f }, -85.7f));
        CHECK(TheSevenArena().Contains({ 1262.8f, -293.8f }, -78.2f));
        // the Tomb's doors by its state (the instance's rule, kept)
        TombDoors const fighting = TombDoorsFor(DungeonKit::State::InProgress);
        TombDoors const done = TombDoorsFor(DungeonKit::State::Done);
        TombDoors const reset = TombDoorsFor(DungeonKit::State::NotStarted);
        CHECK(!fighting.enterOpen && !fighting.exitOpen);
        CHECK(done.enterOpen && done.exitOpen);
        CHECK(reset.enterOpen && !reset.exitOpen);
    }
}

int main()
{
    TestSlice();
    TestGhosts();
    TestTexts();
    TestTuning();
    TestRotation();
    TestGatherDoom();
    TestKit();
    TestPicks();
    TestPool();
    TestArena();
    return Report("brd_the_seven_test");
}
