// Host tests for TaragamanLogic.h (D4: Taragaman the Hungerer): the ids and tags, the arena points, the Feast's pick
// and landing, Gorged, the Felstorm's arithmetic, the fel spots' rotation, the Nova's spikes, and the timeline's
// cadence on every difficulty (section 3.5 rule 24).
#include "TaragamanLogic.h"
#include "check.h"
#include "rfc_edge_check.h"
#include <cmath>
#include <cstdint>
#include <initializer_list>
#include <map>
#include <set>
#include <vector>

using namespace RagefireChasmRework;
using namespace RfcTaragaman;

namespace
{
    // A small deterministic generator: RandBelow's shape.
    struct Rng
    {
        std::uint32_t state = 1;

        std::uint32_t operator()(std::uint32_t n)
        {
            state = state * 1664525u + 1013904223u;
            return n ? (state >> 8) % n : 0;
        }
    };

    constexpr std::initializer_list<Mode> kModes{ Mode::Normal, Mode::Heroic, Mode::HardMode };

    struct Started
    {
        Beat beat;
        std::uint64_t at;
        std::uint64_t end;
    };

    // The AI's own use of the timeline: the beats last as long as they do in the fight (`feastMs` from the mark to the
    // end, the Nova with a `leapMs` leap); every `feastEveryMs` != 0 the hard mode asks for a Feast of its own.
    std::vector<Started> Run(Mode mode, std::uint32_t feastMs, std::uint32_t leapMs, std::uint64_t totalMs,
        bool feastByTimer = true, std::uint32_t tickMs = 100)
    {
        Timeline timeline;
        timeline.Start(mode, 0);
        std::vector<Started> out;
        std::uint64_t endsAt = 0;
        for (std::uint64_t now = 0; now < totalMs; now += tickMs)
        {
            if (timeline.Running() && now >= endsAt)
                timeline.Ended(now);
            std::optional<Beat> const beat = timeline.Next(now, feastByTimer);
            if (!beat)
                continue;
            CHECK(timeline.MayStart(*beat, now));
            timeline.Fired(*beat, now);
            endsAt = now + (*beat == Beat::Felstorm ? Tune::kFelstormCastMs + FelstormOverMs(mode)
                : *beat == Beat::Nova ? leapMs + Tune::kNovaCastMs(mode) : feastMs);
            out.push_back({ *beat, now, endsAt });
        }
        return out;
    }

    std::vector<std::uint64_t> Times(std::vector<Started> const& started, Beat beat)
    {
        std::vector<std::uint64_t> out;
        for (Started const& s : started)
            if (s.beat == beat)
                out.push_back(s.at);
        return out;
    }

    std::uint64_t MaxGap(std::vector<std::uint64_t> const& times)
    {
        std::uint64_t gap = 0;
        for (std::size_t i = 1; i < times.size(); ++i)
            gap = std::max(gap, times[i] - times[i - 1]);
        return gap;
    }

    void CheckIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(SPELL_TG_FEAST_MARK == 213650);
        CHECK(kLastSpell == 213668);
        CHECK(NovaTag(Mode::Normal) == 12 && NovaTag(Mode::Heroic) == 13 && NovaTag(Mode::HardMode) == 13);
        CHECK(NovaBarSpell(Mode::Normal) == SPELL_TG_NOVA_CAST && NovaBarSpell(Mode::Heroic) == SPELL_TG_NOVA_CAST);
        CHECK(NovaBarSpell(Mode::HardMode) == SPELL_TG_NOVA_CAST_HM);
    }

    void CheckPlaces()
    {
        // His spawn and the hub are on his arena, and the slot's arena is the same one.
        CHECK(TaragamanArena().Contains(kTaragamanSpawn.XY(), kTaragamanSpawn.z));
        CHECK(ArenaFor(BOSS_TARAGAMAN).Contains(kTaragamanSpawn.XY(), kTaragamanSpawn.z));
        CHECK(TaragamanArena().Contains(kHub.XY(), kHub.z));
        // The build spec's normal health: HealthModifier 36 on the level 16 warrior base 356; heroic 103 on 3,052.
        CHECK(Tune::kHealth.normal == 36 * 356);
        CHECK(Tune::kHealth.heroic == 103 * 3052);
        CHECK(Tune::kHealth.hardMode == 200 * 3052);
        // The floor band holds every measured floor point of the plateau and no lava.
        CHECK(OnFloorBand(kHub.z));
        for (Point3 const& p : kSpikePoints)
            CHECK(OnFloorBand(p.z));
        for (Point3 const& p : kGlobuleStarts)
            CHECK(OnFloorBand(p.z));
        CHECK(OnFloorBand(-22.5f));
        CHECK(!OnFloorBand(kLavaZ));
        // The probe starts over the highest floor of the band.
        CHECK(kFloorMidZ + kFloorProbeUpYd > kFloorMidZ + kFloorBandYd);
        // Every spike's hide spot is on the arena (bots' bounds) and over 13 yd from the hub, the moved one too.
        for (std::size_t i = 0; i < kSpikePointCount; ++i)
        {
            Vec2 const spot = SpikeHideSpot(i, Tune::kSpikeHideYd);
            CHECK(TaragamanArena().Contains(spot, kSpikePoints[i].z));
            CHECK(DungeonKit::Distance(kHub.XY(), spot) > 13.f);
        }
        CHECK(std::fabs(kSpikePoints[SPIKE_MINUS_Y].x + 247.3f) < 0.01f
            && std::fabs(kSpikePoints[SPIKE_MINUS_Y].y - 140.4f) < 0.01f);
    }

    void CheckFeast()
    {
        Rng rng;
        CHECK(!PickPrey(std::vector<float>{}, rng));
        std::vector<float> const health{ 90.f, 40.f, 100.f, 55.f };
        for (int i = 0; i < 50; ++i)
            CHECK(PickPrey(health, rng) == std::size_t(1));
        // ties: every one of the lowest is picked, nobody else
        std::vector<float> const ties{ 100.f, 60.f, 60.f, 60.f, 80.f };
        std::set<std::size_t> picked;
        for (int i = 0; i < 400; ++i)
            picked.insert(*PickPrey(ties, rng));
        CHECK(picked == (std::set<std::size_t>{ 1, 2, 3 }));
        std::vector<float> const full(5, 100.f);
        picked.clear();
        for (int i = 0; i < 400; ++i)
            picked.insert(*PickPrey(full, rng));
        CHECK(picked.size() == 5);      // the tank too: no slot is left out

        CHECK(PreyEligible(true, true, 40.f) && !PreyEligible(true, true, 40.1f));
        CHECK(!PreyEligible(false, true, 5.f) && !PreyEligible(true, false, 5.f));

        CHECK(Gorges(49.9f) && !Gorges(50.f) && !Gorges(100.f));
        CHECK(std::fabs(DamageMult(0) - 1.f) < 1e-6f);
        CHECK(std::fabs(DamageMult(3) - 1.3f) < 1e-6f);
        CHECK(std::fabs(DamageMult(12) - 2.2f) < 1e-5f);
        CHECK(Tune::kGorgedCap(Mode::Normal) == 3 && Tune::kGorgedCap(Mode::Heroic) == 0
            && Tune::kGorgedCap(Mode::HardMode) == 0);
        CHECK(PctOfHealth(12816, Tune::kGorgeHealPct) == 384);
        CHECK(PctOfHealth(314356, Tune::kDevourHealPct) == 3143);
        CHECK(PctOfHealth(610400, Tune::kGlobuleDrunkHealPct) == 12208);

        CHECK(!HasDevour(Mode::Normal) && HasDevour(Mode::Heroic) && HasDevour(Mode::HardMode));
        CHECK(std::fabs(Tune::kDevourTickPct(Mode::Heroic) * Tune::kDevourTicks - 70.f) < 1e-4f);
        CHECK(std::fabs(Tune::kDevourTickPct(Mode::HardMode) * Tune::kDevourTicks - 80.f) < 1e-4f);
        CHECK(Tune::kDevourTicks * Tune::kDevourTickMs == 5000);

        CHECK(LeapMs(0.f) == kLeapMinMs && LeapMs(25.f) == 1000 && LeapMs(40.f) == kLeapMaxMs && LeapMs(90.f)
            == kLeapMaxMs);

        // A landing is always on the arena, wherever on (or off) the plateau's floor the prey stands.
        std::uint32_t tested = 0;
        for (float x = -282.f; x <= -204.f; x += 1.f)
            for (float y = 108.f; y <= 192.f; y += 1.f)
            {
                Vec2 const prey{ x, y };
                if (!DungeonKit::PointInPolygon(std::span<Vec2 const>(kPlateauFloorPolygon), prey))
                    continue;
                ++tested;
                for (Vec2 const from : { kHub.XY(), Vec2{ -230.f, 152.f }, Vec2{ -238.f, 180.f }, prey })
                {
                    Vec2 const to = LeapLanding(from, prey);
                    CHECK(RfcEdgeCheck::StrictlyInside(TaragamanArena(), to, kHub.z));
                    // near the prey: 2 yd short, plus at most the floor's rim to the arena
                    CHECK(DungeonKit::Distance(to, prey) <= 11.f);
                }
            }
        CHECK(tested > 1400);
        // In the open he lands 2 yd short, on his side.
        Vec2 const to = LeapLanding({ -250.f, 150.f }, { -240.f, 150.f });
        CHECK(std::fabs(to.x + 242.f) < 0.01f && std::fabs(to.y - 150.f) < 0.01f);
    }

    void CheckFelstorm()
    {
        CHECK(RingTicks(Mode::Normal) == 6 && RingTicks(Mode::Heroic) == 5 && RingTicks(Mode::HardMode) == 5);
        CHECK(std::fabs(Tune::kFelstormTickPct(Mode::Normal) * RingTicks(Mode::Normal) - 48.f) < 1e-4f);
        CHECK(std::fabs(Tune::kFelstormTickPct(Mode::Heroic) * RingTicks(Mode::Heroic) - 100.f) < 1e-4f);
        CHECK(PulseCount(Mode::Normal) == 0 && PulseCount(Mode::Heroic) == 5 && PulseCount(Mode::HardMode) == 5);
        CHECK(std::fabs(Tune::kPulsePct(Mode::Heroic) * PulseCount(Mode::Heroic) - 20.f) < 1e-4f);
        CHECK(std::fabs(Tune::kPulsePct(Mode::HardMode) * PulseCount(Mode::HardMode) - 25.f) < 1e-4f);
        CHECK(SpotCount(Mode::Normal) == 0 && SpotCount(Mode::Heroic) == 10 && SpotCount(Mode::HardMode) == 10);
        // Ten spots, every 0.5 s of the spin: the last one is marked in it and lands 1 s (0.75 s) after it.
        CHECK(SpotAtMs(0) == 0 && SpotAtMs(9) == 4500);
        CHECK(FelstormOverMs(Mode::Normal) == 6000 && FelstormOverMs(Mode::Heroic) == 6000
            && FelstormOverMs(Mode::HardMode) == 5750);
        CHECK(SpotAtMs(9) < Tune::kFelstormSpinMs(Mode::Heroic));
        // The hard mode's Nova 2 s after the spin starts with the last spot gone.
        CHECK(FelstormOverMs(Mode::HardMode) < Tune::kFelstormSpinMs(Mode::HardMode) + Tune::kComboNovaAfterSpinMs);
        // A hit spot and every pulse leave a player at about 45% (SP, heroic "Failing path").
        CHECK(Tune::kSpotPct(Mode::Heroic) + Tune::kPulsePct(Mode::Heroic) * PulseCount(Mode::Heroic) == 55.f);

        // The rotation: two each for five players in ten spots, the same order twice.
        Rng rng;
        SpotRotation rotation;
        CHECK(rotation.Empty());
        rotation.Shuffle({ 1, 2, 3, 4, 5 }, rng);
        std::map<std::uint64_t, int> count;
        std::vector<std::uint64_t> order;
        for (std::uint32_t i = 0; i < SpotCount(Mode::Heroic); ++i)
        {
            std::optional<std::uint64_t> const key = rotation.Next([](std::uint64_t) { return true; });
            CHECK(key.has_value());
            ++count[*key];
            order.push_back(*key);
        }
        CHECK(count.size() == 5);
        for (auto const& [key, n] : count)
            CHECK(n == 2);
        for (std::size_t i = 0; i < 5; ++i)
            CHECK(order[i] == order[i + 5]);
        // Somebody dies: their turns go to the next in order; nobody left: no spot.
        rotation.Shuffle({ 1, 2, 3, 4, 5 }, rng);
        for (int i = 0; i < 20; ++i)
            CHECK(rotation.Next([](std::uint64_t key) { return key != 3; }) != std::uint64_t(3));
        CHECK(!rotation.Next([](std::uint64_t) { return false; }));
        // Every order comes up (the tank is nowhere special).
        std::set<std::uint64_t> first;
        for (int i = 0; i < 200; ++i)
        {
            rotation.Shuffle({ 1, 2, 3, 4, 5 }, rng);
            first.insert(*rotation.Next([](std::uint64_t) { return true; }));
        }
        CHECK(first.size() == 5);
        rotation.Clear();
        CHECK(rotation.Empty() && !rotation.Next([](std::uint64_t) { return true; }));
    }

    void CheckSpikes()
    {
        Rng rng;
        std::set<std::vector<std::size_t>> normal;
        std::set<std::vector<std::size_t>> pairs;
        for (int i = 0; i < 400; ++i)
        {
            std::vector<std::size_t> const three = PickSpikes(Tune::kNovaSpikes(Mode::Normal), rng);
            CHECK(three.size() == 3);
            CHECK(std::set<std::size_t>(three.begin(), three.end()).size() == 3);
            normal.insert(three);
            for (Mode const mode : { Mode::Heroic, Mode::HardMode })
            {
                std::vector<std::size_t> const two = PickSpikes(Tune::kNovaSpikes(mode), rng);
                CHECK(two.size() == 2);
                pairs.insert(two);
                // An opposite pair: the hub lies between the two.
                Vec2 const a = kSpikePoints[two[0]].XY();
                Vec2 const b = kSpikePoints[two[1]].XY();
                CHECK(DungeonKit::Distance(a, b) > 19.f);
            }
        }
        CHECK(normal.size() == 4);      // each of the four points is the one left out
        CHECK(pairs == (std::set<std::vector<std::size_t>>{ { SPIKE_PLUS_X, SPIKE_MINUS_X },
            { SPIKE_PLUS_Y, SPIKE_MINUS_Y } }));
        // Places for the whole group: two a spike, or the players over the spikes when there are too few.
        for (Mode const mode : kModes)
        {
            std::uint32_t const spikes = Tune::kNovaSpikes(mode);
            std::uint32_t const share = std::max(2u, (5u + spikes - 1) / spikes);
            CHECK(spikes * share >= 5);
        }
        // Within 18 yd of the hub a player reaches a hide spot of an opposite pair inside 4 s (STAGE-G1 finding 2).
        for (int deg = 0; deg < 360; deg += 5)
        {
            Vec2 const at = DungeonKit::Advance(kHub.XY(), float(deg) * DungeonKit::kPi / 180.f, 18.f);
            for (std::size_t const first : { std::size_t(SPIKE_PLUS_X), std::size_t(SPIKE_PLUS_Y) })
            {
                float const nearest = std::min(DungeonKit::Distance(at, SpikeHideSpot(first, Tune::kSpikeHideYd)),
                    DungeonKit::Distance(at, SpikeHideSpot(first + 1, Tune::kSpikeHideYd)));
                CHECK(nearest <= 24.85f);
            }
        }
    }

    void CheckTimelineRules()
    {
        Timeline t;
        CHECK(!t.On() && !t.Next(100000, true) && !t.MayStart(Beat::Feast, 100000));
        t.Start(Mode::Normal, 1000);
        CHECK(t.DueMs(Beat::Felstorm) == 13000 && t.DueMs(Beat::Nova) == 26000 && t.DueMs(Beat::Feast) == 19000);
        CHECK(!t.Next(12999, true));
        CHECK(t.Next(13000, true) == Beat::Felstorm);
        t.Fired(Beat::Felstorm, 13000);
        CHECK(t.SetPieceRunning() && t.Running() == Beat::Felstorm);
        CHECK(t.DueMs(Beat::Felstorm) == 43000);
        CHECK(!t.Next(19000, true) && !t.MayStart(Beat::Nova, 19000));      // one at a time
        t.Ended(21000);
        // The Feast due at 19 s waits for 4 s after it, and starts exactly then.
        CHECK(!t.MayStart(Beat::Feast, 24999) && !t.Next(24999, true));
        CHECK(t.Next(25000, true) == Beat::Feast);
        // The hard mode's own Feasts (no timer): the timer never starts one.
        CHECK(!t.Next(25000, false));
        // A Nova due meanwhile goes after the older Feast, not before it (rule 24).
        CHECK(t.Next(26000, true) == Beat::Feast);
        t.Fired(Beat::Feast, 26000);
        CHECK(t.DueMs(Beat::Feast) == 39000);           // its own pace: 19 s + 20 s
        CHECK(!t.SetPieceRunning());
        t.Ended(30000);                                 // a Feast leaves no hold behind
        CHECK(t.MayStart(Beat::Feast, 30000));
        CHECK(t.Next(30000, true) == Beat::Nova);
        // A phase's first 2 s.
        t.PhaseChanged(30000);
        CHECK(!t.MayStart(Beat::Feast, 31999) && t.MayStart(Beat::Feast, 32000));
        // A Feast with nobody to mark: its next time.
        Timeline s;
        s.Start(Mode::Normal, 0);
        s.Skip(Beat::Feast, 18000);
        CHECK(s.DueMs(Beat::Feast) == 38000 && !s.Running());
        // Far behind: half a period away, and the missed ones are gone.
        s.Fired(Beat::Felstorm, 12000 + 60000);
        CHECK(s.DueMs(Beat::Felstorm) == 72000 + 15000);
        s.Ended(80000);
        // Started early (the hard mode's combo): its next from then.
        Timeline h;
        h.Start(Mode::HardMode, 0);
        h.Fired(Beat::Felstorm, 5000);
        CHECK(h.DueMs(Beat::Felstorm) == 30000);
        h.Ended(13000);
        // Held set pieces never start by their timers, and keep what was left when released.
        h.HoldSetPieces(true, 13000);
        CHECK(h.Held() && !h.Next(100000, false));
        CHECK(h.MayStart(Beat::Nova, 20000) && h.MayStart(Beat::Felstorm, 20000));
        std::uint64_t const nova = h.DueMs(Beat::Nova);
        h.HoldSetPieces(true, 15000);       // again: nothing
        h.HoldSetPieces(false, 23000);
        CHECK(h.DueMs(Beat::Nova) == nova + 10000);

        // The hold after a set piece: 4 s at every pull, as the hard mode sets it afterwards.
        Timeline f;
        f.Start(Mode::HardMode, 0);
        CHECK(f.FeastHoldMs() == Tune::kFeastAfterSetPieceMs);
        f.SetFeastHold(1500);
        f.Fired(Beat::Nova, 1000);
        f.Ended(5000);
        CHECK(!f.MayStart(Beat::Feast, 6499) && f.MayStart(Beat::Feast, 6500));
        f.Start(Mode::HardMode, 0);
        CHECK(f.FeastHoldMs() == Tune::kFeastAfterSetPieceMs);

        // A set piece that came due during a Feast goes before the Feast the poll asks for (R-1-TG m1): the Feast's end
        // in a kick's handler, the poll on the next tick.
        Timeline k;
        k.Start(Mode::HardMode, 0);
        k.Fired(Beat::Feast, 5000);
        CHECK(!k.SetPieceDue(12000));       // a beat runs
        k.Ended(11000);
        CHECK(k.MayStart(Beat::Feast, 11050) && k.SetPieceDue(11050));
        CHECK(k.Next(11050, false) == Beat::Felstorm);
        k.Fired(Beat::Felstorm, 11050);
        k.Ended(19000);
        CHECK(!k.SetPieceDue(21999) && k.SetPieceDue(22000));
        k.HoldSetPieces(true, 22000);
        CHECK(!k.SetPieceDue(23000));       // phase 2: the combo's clock asks first
        CHECK(DevourInterruptEveryMs(Mode::Heroic) == Tune::kDevourInterruptEveryMs);
        CHECK(DevourInterruptEveryMs(Mode::HardMode) == Tune::kStarvingGapMs);
    }

    // The rim band past his arena (R-1-BOSS M-1's question for the plateau): a tank out of the 10 yd ring often stands
    // there. The plain leash turned him to someone else for it; from his edge he reaches nearly all of it.
    void CheckRimBand()
    {
        Arena const arena = TaragamanArena();
        Arena const floor = PlateauFloor();
        Arena const reach = ReachArena();
        std::uint32_t cells = 0;
        std::uint32_t reached = 0;
        for (float x = -290.f; x <= -195.f; x += 0.5f)
            for (float y = 100.f; y <= 200.f; y += 0.5f)
            {
                Vec2 const p{ x, y };
                CHECK(!arena.Contains(p, kHub.z) || (floor.Contains(p, kHub.z) && reach.Contains(p, kHub.z)));
                if (!floor.Contains(p, kHub.z))
                    continue;
                ++cells;
                Vec2 const spot = EdgeSpot(p);
                CHECK(RfcEdgeCheck::StrictlyInside(arena, spot, kHub.z));
                if (!reach.Contains(p, kHub.z))
                {
                    CHECK(DungeonKit::Distance(p, spot) > kEdgeReachYd - 0.3f);
                    continue;
                }
                ++reached;
                // In reach: from his edge within the 5 yd melee range, 1 yd of height spare.
                CHECK(DungeonKit::Distance(p, spot) <= kEdgeReachYd + 0.4f);
            }
        std::printf("reach: %u of %u floor cells\n", reached, cells);
        CHECK(reached * 100 >= cells * 97);
        RfcEdgeCheck::CheckEdge("taragaman", kPlateauArenaPolygon, arena, floor, reach, kHub.z,
            { -290.f, -195.f, 100.f, 200.f }, 5.83f, 2.25f);

        for (float const d : { 3.f, 7.f, 11.f, 13.f })
        {
            std::uint32_t spots = 0;
            std::uint32_t before = 0;
            std::uint32_t now = 0;
            for (float x = -290.f; x <= -195.f; x += 1.f)
                for (float y = 100.f; y <= 200.f; y += 1.f)
                {
                    Vec2 const him{ x, y };
                    if (!arena.Contains(him, kHub.z))
                        continue;
                    for (int k = 0; k < 36; ++k)
                    {
                        Vec2 const tank = DungeonKit::Advance(him, static_cast<float>(k) * 0.1745329f, d);
                        if (!floor.Contains(tank, kHub.z))
                            continue;
                        ++spots;
                        before += arena.Contains(tank, kHub.z) ? 0 : 1;
                        now += reach.Contains(tank, kHub.z) ? 0 : 1;
                    }
                }
            std::printf("tank %.0f yd off: the plain leash turns him on %.1f%% of the spots, the reach on %.1f%%\n",
                d, 100.0 * before / spots, 100.0 * now / spots);
            CHECK(now * 20 < spots && before > now);
        }
    }

    // Rule 24: the cadence of every difficulty, with Devour kicked (or none) and run in full.
    void CheckCadence()
    {
        struct Case
        {
            Mode mode;
            std::uint32_t feastMs;
            std::uint32_t leapMs;
            std::uint32_t setPieceGap;      // the longest a Felstorm or a Nova may be from the last one
            std::uint32_t feastGap;
            std::uint32_t feasts;           // in 200 s, at least
        };
        std::uint32_t const leap = 800;
        for (Case const& c : { Case{ Mode::Normal, 3000 + 800, leap, 36000, 28000, 9 },
            Case{ Mode::Heroic, 3000 + 800 + 1500, leap, 36000, 25000, 9 },         // Devour kicked after 1.5 s
            Case{ Mode::Heroic, 3000 + 1600 + 5000, 1600, 46000, 30000, 7 } })      // heal-through, the longest leaps
        {
            std::vector<Started> const run = Run(c.mode, c.feastMs, c.leapMs, 200000);
            for (std::size_t i = 1; i < run.size(); ++i)
            {
                CHECK(run[i].at >= run[i - 1].end);         // never two at once
                // a Feast at least 4 s after a Felstorm or a Nova
                if (run[i].beat == Beat::Feast && run[i - 1].beat != Beat::Feast)
                    CHECK(run[i].at >= run[i - 1].end + Tune::kFeastAfterSetPieceMs);
            }
            for (Beat const beat : { Beat::Felstorm, Beat::Nova })
            {
                std::vector<std::uint64_t> const times = Times(run, beat);
                CHECK(times.size() >= 5);
                CHECK(MaxGap(times) <= c.setPieceGap);
            }
            std::vector<std::uint64_t> const feasts = Times(run, Beat::Feast);
            CHECK(feasts.size() >= c.feasts);
            CHECK(MaxGap(feasts) <= c.feastGap);
        }
        // Normal keeps the build spec's Felstorm exactly (12 s, every 30 s) and its Feast on average every 20 s.
        std::vector<Started> const normal = Run(Mode::Normal, 3800, leap, 200000);
        std::vector<std::uint64_t> const storms = Times(normal, Beat::Felstorm);
        for (std::size_t i = 0; i < storms.size(); ++i)
            CHECK(storms[i] == 12000 + 30000 * i);
        // Hard mode, phase 1: the Felstorm and the Nova by their timers, the Feasts by the poll alone. Both keep 25 s.
        std::vector<Started> const hard = Run(Mode::HardMode, 0, leap, 200000, false);
        CHECK(Times(hard, Beat::Feast).empty());
        CHECK(MaxGap(Times(hard, Beat::Felstorm)) <= 25000 && MaxGap(Times(hard, Beat::Nova)) <= 25000);
        // Hard mode, phase 2 (section 7 #27 A): cast, spin, 2 s, leap, 3 s Nova, the 4 s hold fit the 25 s combo.
        CHECK(Tune::kFelstormCastMs + Tune::kFelstormSpinMs(Mode::HardMode) + Tune::kComboNovaAfterSpinMs + leap
            + Tune::kNovaCastMs(Mode::HardMode) + Tune::kFeastAfterSetPieceMs < Tune::kComboEveryMs);
    }

    void CheckWarnings()
    {
        // Rule 30, and ruling 16: no hard mode value is milder than heroic's.
        CHECK(Tune::kFeastMarkMs(Mode::Normal) >= kNormalWarningFloorMs);
        CHECK(Tune::kNovaCastMs(Mode::HardMode) <= Tune::kNovaCastMs(Mode::Heroic));
        CHECK(Tune::kFeastBitePct(Mode::HardMode) >= Tune::kFeastBitePct(Mode::Heroic));
        CHECK(Tune::kDevourTickPct(Mode::HardMode) >= Tune::kDevourTickPct(Mode::Heroic));
        CHECK(Tune::kFelstormEveryMs(Mode::HardMode) <= Tune::kFelstormEveryMs(Mode::Heroic));
        CHECK(Tune::kNovaEveryMs(Mode::HardMode) <= Tune::kNovaEveryMs(Mode::Heroic));
        CHECK(Tune::kComboEveryMs <= Tune::kFelstormEveryMs(Mode::Heroic));
        CHECK(Tune::kFeastEveryMs(Mode::HardMode) <= Tune::kFeastEveryMs(Mode::Heroic));
    }
}

int main()
{
    CheckIds();
    CheckPlaces();
    CheckFeast();
    CheckFelstorm();
    CheckSpikes();
    CheckTimelineRules();
    CheckRimBand();
    CheckCadence();
    CheckWarnings();
    return Report("rfc_taragaman_test");
}
