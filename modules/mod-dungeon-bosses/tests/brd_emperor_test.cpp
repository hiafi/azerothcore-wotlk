// Host tests for EmperorLogic.h (D23: Emperor Dagran Thaurissan and Princess Moira): the slice, the text groups, the
// spec's numbers, the room (the spawns, the tank's Spot 12-20 yd from Moira, the wing ends), the phases and the
// Dagran-first branch, the clocks (first beats, cadences, the enrage, the 40% arm, the Avatar), the beam judge, the
// guard waves (cap 4, ruling 91; Ambassadors from 70%), the senator yells.
#include "EmperorLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdEmperor;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndTexts()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211610 && kSpellSlice.last == 211659);
        CHECK(SPELL_EM_HAND_OF_THAURISSAN == 211610);
        CHECK(SPELL_EM_MOIRA_CAGE == 211630 && SPELL_EM_MOIRA_CAGE_WHIRL == 211631);
        CHECK(kLastSpell == 211631 && kLastSpell <= kSpellSlice.last);
        // Never the stock ids it copies (rule 15)
        for (std::uint32_t id = kSpellSlice.first; id <= kLastSpell; ++id)
            CHECK(id != 17492 && id != 15587 && id != 15636 && id != 15643);

        TextRange const* dagran = nullptr;
        TextRange const* moira = nullptr;
        for (TextRange const& range : kTextRanges)
        {
            if (range.entry == NPC_EMPEROR)
                dagran = &range;
            if (range.entry == NPC_MOIRA)
                moira = &range;
        }
        CHECK(dagran && dagran->firstNew == 8);
        CHECK(moira && moira->firstNew == 1 && moira->last >= EMOTE_MOIRA_NEMESIS);
        // 8-12 fit the header's range now; 13 (Hammer Slam) waits for the shared-file request (0-13).
        CHECK(dagran && dagran->last >= EMOTE_EM_VOLCANIC_BLAST);
        CHECK(YELL_EM_GUARDS == 8 && YELL_EM_ENRAGE == 9 && YELL_EM_RAGNAROS_AWAKENS == 10);
        CHECK(EMOTE_EM_MAGMA_CLAP == 11 && EMOTE_EM_VOLCANIC_BLAST == 12 && EMOTE_EM_HAMMER_SLAM == 13);
        CHECK(YELL_EM_SENATORS_20 == 3 && YELL_EM_SENATORS_100 == 7 && YELL_EM_SLAY == 2);
    }

    void TestSpecNumbers()
    {
        CHECK(kDagranHealth(false) == 160000 && kDagranHealth(true) == 220000);
        CHECK(kMoiraHealth(false) == 50000 && kMoiraHealth(true) == 70000);
        CHECK(kGuardHealth(false) == 8000 && kGuardHealth(true) == 12000 && kAmbassadorHealth == 10000);
        CHECK(kHandStunMs == 2000 && kHandFirstMs == 4000 && kHandEveryMinMs == 12000 && kHandEveryMaxMs == 15000);
        CHECK(kNemesisFirstMs == 12000 && kNemesisEveryMs(false) == 25000 && kNemesisEveryMs(true) == 20000);
        CHECK(kNemesisChannelMs == 8000 && kNemesisTicks == 8);
        CHECK(Near(kRadiantBurnPct(false), 5.f) && Near(kRadiantBurnPct(true), 8.f));
        // An unblocked Nemesis heals both by 12% (S4 "Failing path")
        CHECK(Near(kNemesisHealPct * kNemesisTicks, 12.f));
        CHECK(kGuardFirstMs == 20000 && kGuardEveryMs(false) == 30000 && kGuardEveryMs(true) == 25000);
        CHECK(kGuardsPerWave == 2 && kGuardsMaxAlive == 4);
        CHECK(kNecrosisFirstMs == 8000 && kNecrosisEveryMs == 15000 && Near(kNecrosisTickPct, 6.f));
        CHECK(kNecrosisMs == 10000 && kNecrosisTickMs == 1000);
        CHECK(Near(kAmbassadorPct, 70.f) && Near(kTetherHealPct, 0.5f) && Near(kTetherBurnPct, 3.f));
        CHECK(Near(kFlamestrikePct, 40.f) && kFlamestrikeEveryMs == 12000 && Near(kFlamestrikeRadiusYd, 6.f));
        CHECK(kFlamestrikeWarnMs == 2000 && Near(kFlamestrikeHitPct, 45.f) && kFlamestrikeBurnMs == 4000);
        CHECK(Near(kFlamestrikeBurnPct, 8.f) && kFlamestrikeRandomSpots == 3);
        CHECK(Near(kEnrageDamagePct, 25.f));
        CHECK(kFirestormAfterMs == 5000 && kFirestormEveryMs(false) == 12000 && kFirestormEveryMs(true) == 10000);
        CHECK(kFirestormCount(false) == 3 && kFirestormCount(true) == 4 && Near(kFirestormRadiusYd, 6.f));
        CHECK(Near(kFirestormPct(false), 25.f) && Near(kFirestormPct(true), 40.f) && kFirestormWarnMs == 2000);
        CHECK(kHammerSlamAfterMs == 8000 && kHammerSlamEveryMs == 15000 && kHammerSlamCastMs == 1500);
        CHECK(Near(kHammerSlamLengthYd, 10.f) && Near(kHammerSlamPct(false), 40.f) && Near(kHammerSlamPct(true), 60.f));
        CHECK(kTransitionMs == 3000);
        // G2's `beam-block` row: 2 yd, need 1, 3 s to step in + 5 judged seconds = the 8 s channel
        CHECK(Near(kBeamWidthYd, 2.f) && kNemesisSoakWarnMs == 3000 && kNemesisSoakLiveMs == 5000);
        CHECK(kNemesisSoakWarnMs + kNemesisSoakLiveMs == kNemesisChannelMs);
        CHECK(TAG_EM_NEMESIS == 21);
    }

    void TestRoom()
    {
        Arena const arena = EmperorArena();
        CHECK(arena.Contains(kEmperorSpawn.XY(), kEmperorSpawn.z));
        CHECK(ArenaFor(BOSS_EMPEROR).Contains(kEmperorSpawn.XY(), kEmperorSpawn.z));
        CHECK(arena.Contains(kMoiraSpawn.XY(), kMoiraSpawn.z));
        CHECK(arena.Contains(kTankSpot, kFloorZ));
        for (Point3 const& wing : kGuardEntries)
        {
            CHECK(arena.Contains(wing.XY(), wing.z));
            // NM 4.6 says "48 yd from the Emperor"; straight from his spawn they are 76-78 yd (the 48 reads as from
            // the transept's middle): the guards have a long march either way.
            float const d = DungeonKit::Distance(wing.XY(), kEmperorSpawn.XY());
            CHECK(d > 70.f && d < 80.f);
            CHECK(DungeonKit::Distance(wing.XY(), { 1380.2f, -770.f }) < 48.f);
        }
        // Section 7 #19: the tank holds Dagran 12-20 yd from Moira; he stands within melee of the Spot (3 yd), so the
        // Spot sits at least 3 yd inside the band at both ends.
        float const hold = DungeonKit::Distance(kTankSpot, kMoiraSpot.XY());
        CHECK(hold >= kHoldMinYd + 3.f && hold <= kHoldMaxYd - 3.f);
        // The Spot is on the floor in front of the dais (off the 21 yd dais strip's back half), not on the throne.
        CHECK(kTankSpot.y > kMoiraSpot.y + 10.f);
        CHECK(Near(kMoiraSpot.x, 1384.6f) && Near(kMoiraSpot.y, -831.5f));
        CHECK(Near(DungeonKit::Distance(kMoiraSpot.XY(), kEmperorSpawn.XY()), 4.4f, 0.1f));
    }

    void TestPhases()
    {
        // The court: Hand, Nemesis, guards, the Spot; heroic adds Necrosis and Flamestrike
        CHECK(BeatRunsIn(Beat::Hand, Phase::Court, false) && BeatRunsIn(Beat::Nemesis, Phase::Court, false));
        CHECK(BeatRunsIn(Beat::Guards, Phase::Court, false) && BeatRunsIn(Beat::TankSpot, Phase::Court, false));
        CHECK(!BeatRunsIn(Beat::Necrosis, Phase::Court, false) && BeatRunsIn(Beat::Necrosis, Phase::Court, true));
        CHECK(!BeatRunsIn(Beat::Flamestrike, Phase::Court, false) && BeatRunsIn(Beat::Flamestrike, Phase::Court, true));
        CHECK(!BeatRunsIn(Beat::Firestorm, Phase::Court, true) && !BeatRunsIn(Beat::HammerSlam, Phase::Court, true));
        // The enrage: the court's beats stop; Firestorm, Hammer Slam, Hand (and heroic Flamestrike) run
        for (Beat b : { Beat::Nemesis, Beat::Guards, Beat::Necrosis, Beat::TankSpot })
            CHECK(!BeatRunsIn(b, Phase::Enraged, true));
        CHECK(BeatRunsIn(Beat::Firestorm, Phase::Enraged, false));
        CHECK(BeatRunsIn(Beat::HammerSlam, Phase::Enraged, false));
        CHECK(BeatRunsIn(Beat::Hand, Phase::Enraged, false) && BeatRunsIn(Beat::Flamestrike, Phase::Enraged, true));
        CHECK(!BeatRunsIn(Beat::Flamestrike, Phase::Enraged, false));
        // The transition: nothing; the Avatar: only Firestorm ("Firestorm continues")
        for (std::size_t i = 0; i < kBeatCount; ++i)
        {
            Beat const b = static_cast<Beat>(i);
            CHECK(!BeatRunsIn(b, Phase::Transition, true));
            CHECK(!BeatRunsIn(b, Phase::Idle, true));
            CHECK(BeatRunsIn(b, Phase::Avatar, true) == (b == Beat::Firestorm));
        }
        // The Dagran-first branch: heroic, Moira standing, D24 registered, the court
        CHECK(AwakensOnLethal(true, true, true, Phase::Court, false));
        CHECK(!AwakensOnLethal(false, true, true, Phase::Court, false));      // normal: a real kill, she stands down
        CHECK(!AwakensOnLethal(true, false, true, Phase::Court, false));      // Moira first: the enrage, then a kill
        CHECK(!AwakensOnLethal(true, true, false, Phase::Court, false));      // no D24: a real kill
        CHECK(!AwakensOnLethal(true, true, true, Phase::Enraged, false));
        CHECK(!AwakensOnLethal(true, true, true, Phase::Avatar, false));      // the Avatar's death is real
        // R-2-C m1: a refused awakening (off heroic, wave 2 unbound, slot not IN_PROGRESS) latches for the pull, so
        // the next lethal hit is a real kill instead of another 1 health hold
        CHECK(!AwakensOnLethal(true, true, true, Phase::Court, true));
    }

    struct Fire
    {
        std::uint64_t at = 0;
        Beat beat = Beat::Hand;
    };

    // The engine's loop, every 100 ms: each due beat fires (the Hand on its shortest cadence) and reschedules.
    std::vector<Fire> Run(Beats& beats, std::uint64_t from, std::uint64_t to)
    {
        std::vector<Fire> fires;
        for (std::uint64_t now = from; now <= to; now += 100)
            for (std::size_t i = 0; i < kBeatCount; ++i)
            {
                Beat const b = static_cast<Beat>(i);
                if (beats.Due(b, now))
                {
                    beats.Fired(b, now);
                    fires.push_back({ now, b });
                }
            }
        return fires;
    }

    std::vector<std::uint64_t> Times(std::vector<Fire> const& fires, Beat b)
    {
        std::vector<std::uint64_t> out;
        for (Fire const& f : fires)
            if (f.beat == b)
                out.push_back(f.at);
        return out;
    }

    void TestClocks()
    {
        // Normal court, 100 s: Nemesis 12, 37, 62, 87; guards 20, 50, 80; the Hand from 4 s every 12 s; no Necrosis
        {
            Beats beats;
            beats.Start(false, 0);
            std::vector<Fire> const fires = Run(beats, 0, 100000);
            CHECK((Times(fires, Beat::Nemesis) == std::vector<std::uint64_t>{ 12000, 37000, 62000, 87000 }));
            CHECK((Times(fires, Beat::Guards) == std::vector<std::uint64_t>{ 20000, 50000, 80000 }));
            CHECK(Times(fires, Beat::Hand).front() == 4000 && Times(fires, Beat::Hand).size() == 9);
            CHECK(Times(fires, Beat::Necrosis).empty() && Times(fires, Beat::Firestorm).empty());
            CHECK(Times(fires, Beat::Flamestrike).empty() && Times(fires, Beat::HammerSlam).empty());
            CHECK(Times(fires, Beat::TankSpot).front() == 100 && Times(fires, Beat::TankSpot).size() == 5);
        }
        // Heroic court: Nemesis every 20 s, guards every 25 s, Necrosis 8 s then every 15 s
        {
            Beats beats;
            beats.Start(true, 0);
            std::vector<Fire> const fires = Run(beats, 0, 60000);
            CHECK((Times(fires, Beat::Nemesis) == std::vector<std::uint64_t>{ 12000, 32000, 52000 }));
            CHECK((Times(fires, Beat::Guards) == std::vector<std::uint64_t>{ 20000, 45000 }));
            CHECK((Times(fires, Beat::Necrosis) == std::vector<std::uint64_t>{ 8000, 23000, 38000, 53000 }));
        }
        // The enrage at 30 s: Firestorm 35 s then every 12 s (heroic 10 s), Hammer Slam 38 s then every 15 s; the
        // court's beats are gone; the Hand keeps its clock
        {
            Beats beats;
            beats.Start(false, 0);
            std::vector<Fire> before = Run(beats, 0, 29900);
            beats.Enrage(30000);
            std::vector<Fire> const after = Run(beats, 30000, 70000);
            CHECK((Times(after, Beat::Firestorm) == std::vector<std::uint64_t>{ 35000, 47000, 59000 }));
            CHECK((Times(after, Beat::HammerSlam) == std::vector<std::uint64_t>{ 38000, 53000, 68000 }));
            CHECK(Times(after, Beat::Nemesis).empty() && Times(after, Beat::Guards).empty());
            CHECK(Times(after, Beat::TankSpot).empty());
            CHECK(!Times(after, Beat::Hand).empty());
            Beats heroic;
            heroic.Start(true, 0);
            heroic.Enrage(30000);
            CHECK((Times(Run(heroic, 30000, 56000), Beat::Firestorm) == std::vector<std::uint64_t>{ 35000, 45000,
                55000 }));
            CHECK(heroic.At(Beat::Necrosis) == 0);
        }
        // 40% (heroic): the first Flamestrike 2 s after the crossing, then every 12 s; arming twice changes nothing;
        // never on normal
        {
            Beats beats;
            beats.Start(true, 0);
            beats.ArmFlamestrike(50000);
            beats.ArmFlamestrike(51000);
            CHECK(beats.At(Beat::Flamestrike) == 52000);
            std::vector<Fire> const fires = Run(beats, 50000, 80000);
            CHECK((Times(fires, Beat::Flamestrike) == std::vector<std::uint64_t>{ 52000, 64000, 76000 }));
            Beats normal;
            normal.Start(false, 0);
            normal.ArmFlamestrike(50000);
            CHECK(normal.At(Beat::Flamestrike) == 0);
        }
        // The hard mode: the transition stops everything; the Avatar runs Firestorm (heroic) only
        {
            Beats beats;
            beats.Start(true, 0);
            beats.ArmFlamestrike(10000);
            beats.Stop();
            for (std::size_t i = 0; i < kBeatCount; ++i)
                CHECK(beats.at[i] == 0);
            beats.Avatar(100000);
            std::vector<Fire> const fires = Run(beats, 100000, 130000);
            CHECK((Times(fires, Beat::Firestorm) == std::vector<std::uint64_t>{ 105000, 115000, 125000 }));
            CHECK(fires.size() == 3);
        }
        // A beat that waited (a cast, a full wave) keeps its cadence from when it was due
        {
            Beats beats;
            beats.Start(false, 0);
            beats.Retry(Beat::Guards, 20000);
            beats.Retry(Beat::Guards, 21000);
            beats.Fired(Beat::Guards, 22000);
            CHECK(beats.At(Beat::Guards) == 22000 + kGuardEveryMs(false));
            beats.At(Beat::Nemesis) = 12000;
            beats.Fired(Beat::Nemesis, 13500);
            CHECK(beats.At(Beat::Nemesis) == 37000);
            beats.Fired(Beat::Hand, 4000, 14000);
            CHECK(beats.At(Beat::Hand) == 18000);
        }
    }

    void TestThresholds()
    {
        CHECK(Crossed(70.f, kAmbassadorPct, false) && Crossed(55.f, kAmbassadorPct, false));
        CHECK(!Crossed(70.1f, kAmbassadorPct, false) && !Crossed(50.f, kAmbassadorPct, true));
        CHECK(Crossed(40.f, kFlamestrikePct, false) && !Crossed(41.f, kFlamestrikePct, false));
    }

    void TestBeam()
    {
        Vec2 const moira{ 0.f, 0.f };
        Vec2 const dagran{ 16.f, 0.f };
        CHECK(OnBeam(moira, dagran, kBeamWidthYd, { 8.f, 0.f }));
        CHECK(OnBeam(moira, dagran, kBeamWidthYd, { 8.f, 0.99f }));
        CHECK(OnBeam(moira, dagran, kBeamWidthYd, { 1.f, -1.f }));         // the edge counts
        CHECK(!OnBeam(moira, dagran, kBeamWidthYd, { 8.f, 1.01f }));        // 2 yd wide: 1 yd each side
        CHECK(!OnBeam(moira, dagran, kBeamWidthYd, { -0.5f, 0.f }));        // behind Moira
        CHECK(!OnBeam(moira, dagran, kBeamWidthYd, { 16.5f, 0.f }));        // past Dagran (the tank's side)
        CHECK(!OnBeam(moira, moira, kBeamWidthYd, { 0.f, 0.f }));           // no beam
        // A diagonal beam (the real geometry: the dais to the tank's Spot)
        Vec2 const a = kMoiraSpot.XY();
        Vec2 const b = kTankSpot;
        Vec2 const mid{ (a.x + b.x) / 2.f, (a.y + b.y) / 2.f };
        CHECK(OnBeam(a, b, kBeamWidthYd, mid));
        CHECK(!OnBeam(a, b, kBeamWidthYd, { mid.x + 3.f, mid.y }));
        std::vector<Vec2> const players{ { 4.f, 0.5f }, { 8.f, 5.f }, { 12.f, -0.5f }, { 20.f, 0.f } };
        std::vector<std::size_t> const blockers = BeamBlockers(moira, dagran, kBeamWidthYd, players);
        CHECK(blockers.size() == 2 && blockers[0] == 0 && blockers[1] == 2);
        CHECK(BeamBlockers(moira, dagran, kBeamWidthYd, {}).empty());
        // An open tick: 1.5% each (160k: 2,400; Moira 50k: 750); the tether 0.5% (220k heroic: 1,100)
        CHECK(TickHeal(160000, kNemesisHealPct) == 2400);
        CHECK(TickHeal(50000, kNemesisHealPct) == 750);
        CHECK(TickHeal(220000, kTetherHealPct) == 1100);
        CHECK(TickHeal(10, kTetherHealPct) == 1);
        // The Soak is registered again once the live beam drifts 1.5 yd from its frozen length (G2's finding)
        CHECK(!BeamNeedsRefresh(16.f, 17.f) && BeamNeedsRefresh(16.f, 17.6f) && BeamNeedsRefresh(16.f, 14.4f));
        CHECK(!BeamNeedsRefresh(0.f, 10.f));
    }

    void TestWaves()
    {
        Wave w = WaveFor(0, false);
        CHECK(w.guards == 2 && !w.ambassador && !w.waits);
        w = WaveFor(2, false);
        CHECK(w.guards == 2 && !w.waits);
        w = WaveFor(3, true);                   // never past 4 alive
        CHECK(w.guards == 1 && w.ambassador && !w.waits);
        w = WaveFor(4, true);                   // ruling 91: the wave waits (and brings no Ambassador)
        CHECK(w.waits && w.guards == 0 && !w.ambassador);
        CHECK(WaveFor(5, false).waits);
        // One guard from each wing; a lone guard from a random wing
        CHECK(GuardEntryFor(0, 2, 0) == 0 && GuardEntryFor(1, 2, 0) == 1 && GuardEntryFor(1, 2, 1) == 1);
        CHECK(GuardEntryFor(0, 1, 0) == 0 && GuardEntryFor(0, 1, 1) == 1);
        // The Ambassador's stand: 20 yd from Dagran toward its wing (inside the room)
        Vec2 const dagran = kTankSpot;
        for (Point3 const& wing : kGuardEntries)
        {
            Vec2 const stand = AmbassadorStand(dagran, wing.XY());
            CHECK(Near(DungeonKit::Distance(stand, dagran), kAmbassadorStandYd, 0.01f));
            CHECK(DungeonKit::Distance(stand, wing.XY()) < DungeonKit::Distance(dagran, wing.XY()));
            CHECK(EmperorArena().Contains(stand, kFloorZ));
            CHECK(kAmbassadorStandYd < kTetherRangeYd);
        }
        Vec2 const close{ kGuardEntries[0].x + 5.f, kGuardEntries[0].y };
        CHECK(Near(AmbassadorStand(close, kGuardEntries[0].XY()).x, kGuardEntries[0].x));
        // Flamestrike: one under each of 5 players and 3 random spots
        CHECK(FlamestrikeCircles(5) == 8 && FlamestrikeCircles(0) == 3);
    }

    void TestSenators()
    {
        CHECK(!SenatorYell(19, 0));
        CHECK(SenatorYell(20, 0) && *SenatorYell(20, 0) == 3);
        CHECK(!SenatorYell(39, 1));
        CHECK(SenatorYell(40, 1) && *SenatorYell(40, 1) == 4);
        CHECK(SenatorYell(100, 4) && *SenatorYell(100, 4) == YELL_EM_SENATORS_100);
        CHECK(!SenatorYell(100, 5));
        // One per push (stock): a jump to 100% yells the next line only
        CHECK(SenatorYell(100, 0) && *SenatorYell(100, 0) == 3);
        CHECK(AggroYell(0) == YELL_EM_AGGRO_COUNCIL && AggroYell(4) == YELL_EM_AGGRO_COUNCIL);
        CHECK(AggroYell(5) == YELL_EM_AGGRO_ALONE);
    }
}

int main()
{
    TestSliceAndTexts();
    TestSpecNumbers();
    TestRoom();
    TestPhases();
    TestClocks();
    TestThresholds();
    TestBeam();
    TestWaves();
    TestSenators();
    return Report("brd_emperor_test");
}
