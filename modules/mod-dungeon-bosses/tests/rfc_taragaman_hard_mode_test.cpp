// Host tests for TaragamanHardModeLogic.h (D4H: Starving): the ids, the trigger's rules, the Starving Feast's wakes,
// the ring's drift clamp, the globules' way and kill order, the combo's and the waves' clocks, and the whole fight's
// cadence on D4's own timeline (section 3.5 rule 24, ruling 16).
#include "TaragamanHardModeLogic.h"
#include "TaragamanLogic.h"
#include "check.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <optional>
#include <random>
#include <vector>

using namespace RagefireChasmRework;
using namespace RfcStarving;
using RfcTaragaman::Beat;

namespace
{
    constexpr float kPi = 3.14159265f;

    void CheckIdsAndPlaces()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(SPELL_HM_HUNGERERS_BLOOD == 213690);
        CHECK(kLastSpell == 213695);
        CHECK(TAG_HM_BURST == 17);
        // The hard mode fights in Taragaman's arena; the globules start on the plateau's floor, 30 to 33 yd from the
        // hub, so the straight walk is 12.8 s at 2.5 yd/s (section 7 #22 A).
        CHECK(ArenaFor(BOSS_STARVING).Contains(kTaragamanSpawn.XY(), kTaragamanSpawn.z));
        for (std::size_t i = 0; i < kGlobuleStarts.size(); ++i)
        {
            Point3 const& start = kGlobuleStarts[i];
            CHECK(PlateauFloor().Contains(start.XY(), start.z));
            CHECK(RfcTaragaman::OnFloorBand(start.z));
            float const d = DungeonKit::Distance(start.XY(), kHub.XY());
            CHECK(d > 30.f && d < 33.5f);
            CHECK(d / Tune::kGlobuleSpeed > 12.f && d / Tune::kGlobuleSpeed < 13.4f);
            // The lake's look stands in the lava past the same arm's end, off the plateau.
            CHECK(!PlateauFloor().Contains(kBloodLakeSpots[i].XY(), kBloodLakeSpots[i].z));
            CHECK(kBloodLakeSpots[i].z == kLavaZ);
            CHECK(DungeonKit::Distance(kBloodLakeSpots[i].XY(), start.XY()) < 12.f);
        }
        CHECK(Tune::kHealth.hardMode == 814884);
        // The pour spot is at the foot of the -x arm, over 30 yd from his spawn, beside the lava cell of its look.
        CHECK(DungeonKit::Distance(kPourSpot.XY(), kTaragamanSpawn.XY()) > 30.f);
        CHECK(DungeonKit::Distance(kPourSpot.XY(), kPourLava.XY()) < 2.f);
        CHECK(DungeonKit::Distance(kBloodShrine.XY(), kOrb.XY()) > 3.f);
    }

    void CheckRuling16()
    {
        // The hard mode matches or exceeds heroic on every value.
        CHECK(Tune::kFeastEveryMs.hardMode <= Tune::kFeastEveryMs.heroic);
        CHECK(Tune::kFeastFirstMs.hardMode <= Tune::kFeastFirstMs.heroic);
        CHECK(Tune::kFeastMarkMs.hardMode <= Tune::kFeastMarkMs.heroic);
        CHECK(Tune::kFeastBitePct.hardMode >= Tune::kFeastBitePct.heroic);
        CHECK(Tune::kDevourTickPct.hardMode >= Tune::kDevourTickPct.heroic);
        CHECK(Tune::kFelstormEveryMs.hardMode <= Tune::kFelstormEveryMs.heroic);
        CHECK(Tune::kFelstormTickPct.hardMode >= Tune::kFelstormTickPct.heroic);
        CHECK(Tune::kFelstormRadius.hardMode >= Tune::kFelstormRadius.heroic);
        CHECK(Tune::kPulsePct.hardMode >= Tune::kPulsePct.heroic);
        CHECK(Tune::kSpotRadius.hardMode >= Tune::kSpotRadius.heroic);
        CHECK(Tune::kSpotWarnMs.hardMode <= Tune::kSpotWarnMs.heroic);
        CHECK(Tune::kSpotPct.hardMode >= Tune::kSpotPct.heroic);
        CHECK(Tune::kNovaEveryMs.hardMode <= Tune::kNovaEveryMs.heroic);
        CHECK(Tune::kNovaCastMs.hardMode <= Tune::kNovaCastMs.heroic);
        CHECK(Tune::kNovaPct.hardMode >= Tune::kNovaPct.heroic);
        CHECK(Tune::kComboEveryMs <= Tune::kFelstormEveryMs.heroic && Tune::kComboEveryMs <= Tune::kNovaEveryMs.heroic);
        CHECK(Tune::kGorgedCap.heroic == 0 && Tune::kGorgedCap.hardMode == 0);      // no cap (ruling 15)
    }

    void CheckTrigger()
    {
        TriggerState s;
        s.heroic = true;
        s.alive = true;
        CHECK(ShrineRefusal(s) == Refusal::None);
        CHECK(PourRefusal(s) == Refusal::NoBlood);
        s.carries = true;
        CHECK(ShrineRefusal(s) == Refusal::None);       // may be drawn again
        CHECK(PourRefusal(s) == Refusal::None);

        // A bot never, whatever else holds, and it reads nothing.
        TriggerState bot = s;
        bot.bot = true;
        CHECK(ShrineRefusal(bot) == Refusal::Bot && PourRefusal(bot) == Refusal::Bot);
        bot.armed = true;
        CHECK(PourRefusal(bot) == Refusal::Bot);
        CHECK(RefusalNotice(Refusal::Bot) == nullptr);

        auto with = [&s](auto change)
        {
            TriggerState t = s;
            change(t);
            CHECK(ShrineRefusal(t) == PourRefusal(t));
            return PourRefusal(t);
        };
        CHECK(with([](TriggerState& t) { t.heroic = false; }) == Refusal::NotHeroic);
        CHECK(with([](TriggerState& t) { t.armed = true; }) == Refusal::AlreadyPoured);
        CHECK(with([](TriggerState& t) { t.inCombat = true; }) == Refusal::InCombat);
        CHECK(with([](TriggerState& t) { t.alive = false; }) == Refusal::Dead);
        CHECK(with([](TriggerState& t) { t.taragamanState = DungeonKit::State::InProgress; }) == Refusal::Fighting);
        CHECK(with([](TriggerState& t) { t.taragamanState = DungeonKit::State::Done; }) == Refusal::Killed);
        // A wipe's FAIL, a fresh instance's NOT_STARTED and the not yet settled slot are open.
        CHECK(with([](TriggerState& t) { t.taragamanState = DungeonKit::State::Fail; }) == Refusal::None);
        CHECK(with([](TriggerState& t) { t.taragamanState = DungeonKit::State::ToBeDecided; }) == Refusal::None);
        // What the trigger accepts the instance accepts (and the other way round for a living, free human carrier).
        for (bool const heroic : { false, true })
            for (std::uint32_t const state : { DungeonKit::State::NotStarted, DungeonKit::State::InProgress,
                DungeonKit::State::Fail, DungeonKit::State::Done })
                CHECK((ClosedFor(heroic, state, false) == Refusal::None) == HardModeChangeAllowed(heroic, state, 1));
        for (Refusal const r : { Refusal::NotHeroic, Refusal::InCombat, Refusal::Fighting, Refusal::Killed,
            Refusal::AlreadyPoured, Refusal::NoBlood, Refusal::Instance })
            CHECK(RefusalNotice(r) && std::strlen(RefusalNotice(r)) > 8);
        CHECK(RefusalNotice(Refusal::None) == nullptr);

        // The loot bit (the instance's rule, set at the pour and at every pull).
        CHECK(HardModeLootLit(1, DungeonKit::State::NotStarted) && HardModeLootLit(1, DungeonKit::State::InProgress));
        CHECK(!HardModeLootLit(0, DungeonKit::State::InProgress) && !HardModeLootLit(1, DungeonKit::State::Done));
        // The flag survives the save.
        RfcSave save;
        save.hardMode = 1;
        RfcSave loaded;
        CHECK(ParseRfcSave(FormatRfcSave(save), loaded) && loaded.hardMode == 1);
    }

    void CheckWakes()
    {
        // Nobody under the line: D4's timer, any time after the gap to the last mark (ruling 16: at its own pace).
        CHECK(!FallbackDue(20999, 15000) && FallbackDue(21000, 15000));
        // D4's timer is due 15 s after a mark at the latest, whether that was early or late.
        for (std::uint64_t mark = 2000; mark < 60000; mark += 500)
        {
            RfcTaragaman::Timeline t;
            t.Start(Mode::HardMode, 0);
            t.Fired(Beat::Feast, mark);
            t.Ended(mark);
            t.HoldSetPieces(true, mark);
            CHECK(t.Next(mark + Tune::kFeastEveryMs(Mode::HardMode), true) == Beat::Feast);
        }
        // Under 30%: at once, but not in the pull's first 2 s and not within 6 s of the last mark. 30% is not under it.
        CHECK(!LineWake(1999, 0, 10.f) && LineWake(2000, 0, 10.f));
        CHECK(LineWake(5000, 0, 29.9f) && !LineWake(5000, 0, 30.f) && !LineWake(50000, 0, 80.f));
        CHECK(!LineWake(15999, 10000, 5.f) && LineWake(16000, 10000, 5.f) && LineWake(40000, 10000, 5.f));
        CHECK(Phase2Due(30.f) && Phase2Due(12.f) && !Phase2Due(30.01f));
    }

    void CheckDrift()
    {
        Vec2 const spawn = kTaragamanSpawn.XY();
        std::span<Vec2 const> const arena(kPlateauArenaPolygon);
        // The whole disc is arena: a straight drift between two clamped points never leaves it.
        for (float r = 0.f; r <= Tune::kDriftClampYd + 0.001f; r += 0.25f)
            for (int deg = 0; deg < 360; deg += 2)
                CHECK(DungeonKit::PointInPolygon(arena, DungeonKit::Advance(spawn, deg * kPi / 180.f, r)));
        // Every target anywhere on the plateau (and off it) is clamped to 8 yd; inside the disc it is itself.
        for (float x = -290.f; x <= -195.f; x += 1.f)
            for (float y = 100.f; y <= 200.f; y += 1.f)
            {
                Vec2 const p{ x, y };
                Vec2 const c = DriftClamp(p);
                float const d = DungeonKit::Distance(spawn, c);
                CHECK(d <= Tune::kDriftClampYd + 0.01f);
                CHECK(DungeonKit::PointInPolygon(arena, c));
                if (DungeonKit::Distance(spawn, p) <= Tune::kDriftClampYd)
                    CHECK(c.x == p.x && c.y == p.y);
                else
                    CHECK(std::fabs(d - Tune::kDriftClampYd) < 0.01f);
                // He stands in the disc for the bar, so the ring's center is never outside it.
                std::optional<Vec2> const spot = FelstormSpotFor(p);
                Vec2 const bar = spot.value_or(p);
                CHECK(DungeonKit::Distance(spawn, bar) <= Tune::kDriftClampYd + 0.51f);
                if (spot)
                    CHECK(DungeonKit::Distance(spawn, *spot) <= Tune::kDriftClampYd + 0.01f);
            }
        CHECK(!FelstormSpotFor(spawn));
        // One pick moves him 6 yd at most (2 s at 3 yd/s): the ring is a hazard that creeps, not a chase.
        CHECK(Tune::kDriftSpeed * Tune::kDriftRepickMs / 1000.f <= 6.01f);
        // The ring never reaches an arm's end: 18 yd from his spawn at most.
        for (Point3 const& start : kGlobuleStarts)
            CHECK(DungeonKit::Distance(spawn, start.XY()) > Tune::kDriftClampYd
                + Tune::kFelstormRadius(Mode::HardMode) + 10.f);
    }

    void CheckGlobules()
    {
        Vec2 const hub = kHub.XY();
        // From every start straight to the hub over the floor.
        for (Point3 const& start : kGlobuleStarts)
        {
            CHECK(StraightOnFloor(start.XY(), hub));
            CHECK(GlobuleLeg(start.XY(), hub) == Leg::ToHim);
            // He tanked on another arm: the hub first, then straight on.
            for (Point3 const& other : kGlobuleStarts)
            {
                if (&other == &start)
                    continue;
                Leg const leg = GlobuleLeg(start.XY(), other.XY());
                CHECK(leg == Leg::ToHub || leg == Leg::ToHim);
                CHECK(GlobuleLeg(hub, other.XY()) == Leg::ToHim);
            }
        }
        // Everywhere on the arena he can be reached: a line from the hub, or the navmesh (a few cells round a corner).
        std::uint32_t cells = 0;
        std::uint32_t straight = 0;
        for (float x = -280.f; x <= -206.f; x += 1.f)
            for (float y = 110.f; y <= 192.f; y += 1.f)
                if (DungeonKit::PointInPolygon(kPlateauArenaPolygon, { x, y }))
                {
                    ++cells;
                    straight += StraightOnFloor(hub, { x, y }) ? 1 : 0;
                }
        CHECK(cells > 900);
        CHECK(straight * 100 >= cells * 80);
        std::printf("globule ways: %u of %u arena cells straight from the hub\n", straight, cells);
        // Off the plateau or in the lava there is no straight line.
        CHECK(GlobuleLeg({ -220.f, 180.f }, { -270.f, 180.f }) == Leg::Path);

        CHECK(Drunk(2.f, 0.f) && !Drunk(2.1f, 0.f) && !Drunk(1.f, 9.f) && Drunk(1.f, -3.f));
        CHECK(GlobuleSpeed(0) == Tune::kGlobuleSpeed);                  // low health is no slow (R-1-TG m3)
        CHECK(std::fabs(GlobuleSpeed(-50) - Tune::kGlobuleSpeed / 2.f) < 0.01f);
        CHECK(GlobuleSpeed(40) == Tune::kGlobuleSpeed);                 // nothing speeds it up
        CHECK(GlobuleSpeed(-100) > 0.f);                                // MovePoint reads 0 as its own speed

        // The kill order: nearer bands rank higher, every one over him (0), and the last covers the whole walk.
        for (std::size_t i = 1; i < kGlobuleTiers.size(); ++i)
        {
            CHECK(kGlobuleTiers[i].withinYd > kGlobuleTiers[i - 1].withinYd);
            CHECK(kGlobuleTiers[i].priority < kGlobuleTiers[i - 1].priority);
        }
        CHECK(kGlobuleTiers.back().priority > 0 && kGlobuleTiers.back().withinYd > 2.f * 33.5f);
    }

    void CheckClocks()
    {
        // The combo: at once when the phase starts with no Felstorm before it.
        ComboClock c;
        CHECK(c.At(1000) == ComboClock::Due::None);
        c.Start(1000, false);
        CHECK(c.At(1000) == ComboClock::Due::Felstorm);
        CHECK(c.At(1100) == ComboClock::Due::Felstorm);     // refused: asked again
        c.SpinStarted(1200);
        CHECK(c.At(3200) == ComboClock::Due::None);
        c.SpinEnded(8200);
        CHECK(c.At(10199) == ComboClock::Due::None);
        CHECK(c.At(8200 + Tune::kComboNovaAfterSpinMs) == ComboClock::Due::Nova);
        CHECK(c.At(60000) == ComboClock::Due::Nova);        // the Nova before any next Felstorm
        c.NovaStarted();
        CHECK(c.At(1000 + Tune::kComboEveryMs - 1) == ComboClock::Due::None);
        CHECK(c.At(1000 + Tune::kComboEveryMs) == ComboClock::Due::Felstorm);
        // Pushed back by a Feast: its own pace from the time it was due (R-1-TG m2).
        c.SpinStarted(26000 + 3000);
        c.SpinEnded(34200);
        c.NovaStarted();
        CHECK(c.FelstormDueMs() == 26000 + Tune::kComboEveryMs);
        // Far behind: half an interval after its bar at least.
        c.SpinStarted(51000 + 20200);
        c.SpinEnded(78200);
        c.NovaStarted();
        CHECK(c.FelstormDueMs() == 71200 + Tune::kComboEveryMs / 2);
        // A GM's: from its bar.
        c.Hurry(80000);
        CHECK(c.At(80000) == ComboClock::Due::Felstorm);
        c.SpinStarted(80500);
        CHECK(c.FelstormDueMs() == 80000 + Tune::kComboEveryMs);
        c.SpinEnded(87500);
        c.NovaStarted();
        c.SpinStarted(90000);       // early
        CHECK(c.FelstormDueMs() == 90000 + Tune::kComboEveryMs);

        // The phase starts while phase 1's Felstorm spins: that is the first one.
        ComboClock spinning;
        spinning.SpinStarted(50000);
        spinning.Start(53000, true);
        CHECK(spinning.At(54000) == ComboClock::Due::None);
        spinning.SpinEnded(57000);
        CHECK(spinning.At(59000) == ComboClock::Due::Nova);
        spinning.NovaStarted();
        CHECK(spinning.At(74999) == ComboClock::Due::None);
        CHECK(spinning.At(75000) == ComboClock::Due::Felstorm);

        // Just after one: half a period after its bar, so never two spins back to back.
        ComboClock after;
        after.SpinStarted(50000);
        after.SpinEnded(57000);     // phase 1: no Nova of ours
        after.Start(57500, false);
        CHECK(after.At(57500) == ComboClock::Due::None);
        CHECK(after.At(62500) == ComboClock::Due::Felstorm);
        ComboClock longAfter;
        longAfter.SpinStarted(10000);
        longAfter.Start(57500, false);
        CHECK(longAfter.At(57500) == ComboClock::Due::Felstorm);

        // The bar's own phase start: a Felstorm cast runs (not spinning yet). Its spin moves the next one.
        ComboClock casting;
        casting.Start(57500, false);
        casting.SpinStarted(57000);
        CHECK(casting.At(59000) == ComboClock::Due::None);

        WaveClock w;
        CHECK(!w.Take(1000));
        w.Start(1000);
        CHECK(w.Take(1000));
        CHECK(!w.Take(1001));
        CHECK(!w.Take(1000 + Tune::kGlobuleEveryMs - 1));
        CHECK(w.Take(1000 + Tune::kGlobuleEveryMs));
        CHECK(w.DueMs() == 1000 + 2 * Tune::kGlobuleEveryMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The whole fight on D4's timeline, the way taragaman_hard_mode.cpp and boss_taragaman_rework.cpp run it: OnUpdate
    // (phase, combo, poll), then the running beat's end, then D4's own due beat.
    // ----------------------------------------------------------------------------------------------------------------
    struct Fight
    {
        struct Start
        {
            Beat beat;
            std::uint64_t at;
            std::uint64_t end;
        };
        std::vector<Start> starts;
        std::uint32_t waves = 0;
    };

    struct Setup
    {
        std::uint32_t feastMs = 8100;       // mark 2 s, leap 1.1 s, Devour in full 5 s
        std::uint32_t leapMs = 1600;        // before a Felstorm's bar and a Nova's cast
        float lowestPct = 100.f;            // the group's lowest health, all fight long
        bool kicked = false;
        std::uint32_t fullEvery = 0;        // kicked, but every n-th Devour runs in full (8.1 s)
        std::uint64_t phase2At = 113000;
        std::uint64_t total = 400000;
    };

    // Phase 2's leaps cannot be as long as phase 1's: the Felstorm's goes from anywhere on the arena into the disc
    // (CheckPhase2Leaps); the Nova starts 2 s after a spin that ended in the disc, at his run speed (1.14286 x 7 yd).
    std::uint32_t constexpr kPhase2FelstormLeapMs = 1300;
    float constexpr kRunYd = 8.f;

    std::uint32_t Phase2LeapMs(Beat beat)
    {
        return beat == Beat::Felstorm ? kPhase2FelstormLeapMs : RfcTaragaman::LeapMs(DungeonKit::Distance(
            kTaragamanSpawn.XY(), kHub.XY()) + Tune::kDriftClampYd + kRunYd * Tune::kComboNovaAfterSpinMs / 1000.f);
    }

    void CheckPhase2Leaps()
    {
        for (float x = -280.f; x <= -205.f; x += 0.5f)
            for (float y = 110.f; y <= 192.f; y += 0.5f)
                if (DungeonKit::PointInPolygon(kPlateauArenaPolygon, { x, y }))
                    if (std::optional<Vec2> const spot = FelstormSpotFor({ x, y }))
                        CHECK(RfcTaragaman::LeapMs(DungeonKit::Distance(*spot, { x, y })) <= kPhase2FelstormLeapMs);
        CHECK(Phase2LeapMs(Beat::Nova) <= 1000);
    }

    Fight Run(Setup const& s)
    {
        RfcTaragaman::Timeline timeline;
        timeline.Start(Mode::HardMode, 0);
        ComboClock combo;
        WaveClock waves;
        Fight fight;
        bool phase2 = false;
        bool spinning = false;
        bool nova = false;
        std::uint64_t lastFeast = 0;
        std::uint64_t spinAt = 0;
        std::uint64_t spinEnds = 0;
        std::uint64_t endsAt = 0;
        std::uint32_t const tick = 50;
        std::uint32_t feasts = 0;
        bool thisKicked = false;
        auto start = [&](Beat beat, std::uint64_t now)
        {
            timeline.Fired(beat, now);
            std::uint32_t const leapMs = phase2 ? std::min(s.leapMs, Phase2LeapMs(beat)) : s.leapMs;
            if (beat == Beat::Felstorm)
            {
                spinAt = now + leapMs + Tune::kFelstormCastMs;
                spinEnds = spinAt + Tune::kFelstormSpinMs(Mode::HardMode);
                endsAt = spinAt + RfcTaragaman::FelstormOverMs(Mode::HardMode);
            }
            else if (beat == Beat::Nova)
            {
                endsAt = now + leapMs + Tune::kNovaCastMs(Mode::HardMode);
                combo.NovaStarted();
                nova = true;
            }
            else
            {
                thisKicked = s.kicked && !(s.fullEvery && ++feasts % s.fullEvery == 0);
                endsAt = now + (s.kicked && !thisKicked ? 8100 : s.feastMs);
                lastFeast = std::max<std::uint64_t>(1, now);
            }
            fight.starts.push_back({ beat, now, endsAt });
        };
        for (std::uint64_t now = 0; now < s.total; now += tick)
        {
            // A kick ends the Feast in the player's spell handler, between two AI ticks.
            if (thisKicked && timeline.Running() == Beat::Feast && now >= endsAt)
                timeline.Ended(now);
            // OnUpdate
            if (!phase2 && now >= s.phase2At)
            {
                phase2 = true;
                timeline.PhaseChanged(now);
                timeline.HoldSetPieces(true, now);
                timeline.SetFeastHold(Tune::kPhase2FeastHoldMs);
                combo.Start(now, spinning);
                waves.Start(now);
            }
            if (phase2)
            {
                fight.waves += waves.Take(now) ? 1 : 0;
                ComboClock::Due const due = combo.At(now);
                if (due != ComboClock::Due::None)
                {
                    Beat const beat = due == ComboClock::Due::Nova ? Beat::Nova : Beat::Felstorm;
                    if (timeline.MayStart(beat, now))
                        start(beat, now);
                }
            }
            if (now % Tune::kStarvingPollMs == 0 && LineWake(now, lastFeast, s.lowestPct)
                && timeline.MayStart(Beat::Feast, now) && !timeline.SetPieceDue(now))
                start(Beat::Feast, now);
            // the running beat
            if (spinAt && now >= spinAt && !spinning)
            {
                spinning = true;
                spinAt = 0;
                combo.SpinStarted(now - Tune::kFelstormCastMs);
            }
            if (spinning && now >= spinEnds)
            {
                spinning = false;
                combo.SpinEnded(now);
            }
            if (timeline.Running() && now >= endsAt)
                timeline.Ended(now);
            // D4's due beat (a Feast of its own only as the fallback)
            if (std::optional<Beat> const beat = timeline.Next(now, TimerFeastMay(now, lastFeast, combo)))
            {
                CHECK(*beat == Beat::Feast || !phase2);
                CHECK(combo.At(now) == ComboClock::Due::None);      // never in front of a due combo (RF-M2)
                start(*beat, now);
            }
        }
        CHECK(nova);
        return fight;
    }

    std::uint64_t MaxGap(Fight const& fight, Beat beat, std::uint64_t from, std::uint64_t to)
    {
        std::uint64_t last = from;
        std::uint64_t gap = 0;
        for (Fight::Start const& s : fight.starts)
            if (s.beat == beat && s.at >= from && s.at < to)
            {
                gap = std::max(gap, s.at - last);
                last = s.at;
            }
        return std::max(gap, to - last);
    }

    // The gap across `line`: from the last start before it to the first one after it.
    std::uint64_t GapAcross(Fight const& fight, Beat beat, std::uint64_t line)
    {
        std::uint64_t before = 0;
        for (Fight::Start const& s : fight.starts)
            if (s.beat == beat && s.at < line)
                before = s.at;
            else if (s.beat == beat)
                return s.at - before;
        return 0;
    }

    struct Devours
    {
        std::uint32_t ms;               // a Feast's whole run
        std::uint32_t fullEvery;        // every n-th one in full (0: all alike)
    };

    void CheckCadence()
    {
        // TG7's arithmetic: leap, bar, spin, 2 s, leap, cast, 4 s is under the interval, with time for a whole Feast.
        std::uint32_t const combo = RfcTaragaman::kLeapMaxMs + Tune::kFelstormCastMs
            + Tune::kFelstormSpinMs(Mode::HardMode) + Tune::kComboNovaAfterSpinMs + RfcTaragaman::kLeapMinMs
            + Tune::kNovaCastMs(Mode::HardMode) + Tune::kPhase2FeastHoldMs;
        CHECK(combo < Tune::kComboEveryMs);
        CHECK(Tune::kComboEveryMs - combo > 7000);
        std::uint64_t acrossFeast = 0;
        std::uint64_t acrossFelstorm = 0;
        std::uint64_t acrossNova = 0;
        // The Nova of a combo never waits for the last spots, and no Feast fits between the spin and the Nova.
        CHECK(RfcTaragaman::FelstormOverMs(Mode::HardMode) - Tune::kFelstormSpinMs(Mode::HardMode)
            < Tune::kComboNovaAfterSpinMs);
        CHECK(Tune::kPhase2FeastHoldMs < Tune::kFeastAfterSetPieceMs && Tune::kPhase2FeastHoldMs
            + RfcTaragaman::FelstormOverMs(Mode::HardMode) - Tune::kFelstormSpinMs(Mode::HardMode)
            > Tune::kComboNovaAfterSpinMs);

        for (float const lowest : { 100.f, 10.f })
            for (Devours const& devours : { Devours{ 4000, 0 }, Devours{ 4000, 4 }, Devours{ 4000, 3 },
                Devours{ 4000, 2 }, Devours{ 8100, 0 }, Devours{ 8600, 0 } })
                for (std::uint32_t const leapMs : { 0u, 500u, 1600u })
                    for (std::uint64_t phase2At = 100000; phase2At < 126000; phase2At += 1000)
                    {
                        Setup s;
                        s.lowestPct = lowest;
                        s.feastMs = devours.ms;
                        s.fullEvery = devours.fullEvery;
                        s.leapMs = leapMs;
                        s.phase2At = phase2At;
                        s.kicked = devours.ms < 8000;
                        std::uint32_t const feastMs = s.fullEvery ? 8100 : s.feastMs;     // the longest
                        Fight const fight = Run(s);
                        // Phase 1: no beat is starved, a permanent failure included.
                        CHECK(MaxGap(fight, Beat::Felstorm, 0, phase2At) <= 40000);
                        CHECK(MaxGap(fight, Beat::Nova, 0, phase2At) <= 40000);
                        CHECK(MaxGap(fight, Beat::Feast, 0, phase2At) <= 30000);
                        // Phase 2, from its start (across the line: GapAcross below): the combo at most one Feast
                        // late, a Feast every cycle, whoever kicks the Devours.
                        CHECK(MaxGap(fight, Beat::Felstorm, phase2At, s.total) <= Tune::kComboEveryMs + feastMs + 2000);
                        CHECK(MaxGap(fight, Beat::Nova, phase2At, s.total) <= Tune::kComboEveryMs + feastMs + 2000);
                        CHECK(MaxGap(fight, Beat::Feast, phase2At, s.total) <= 33000);
                        CHECK(fight.waves == (s.total - 1 - phase2At) / Tune::kGlobuleEveryMs + 1);
                        // Once a fight, across the 30% line (RF2-m2): a Felstorm and a Nova of phase 1 that were just
                        // due, then the first combo, before the next Feast.
                        acrossFeast = std::max(acrossFeast, GapAcross(fight, Beat::Feast, phase2At));
                        acrossFelstorm = std::max(acrossFelstorm, GapAcross(fight, Beat::Felstorm, phase2At));
                        acrossNova = std::max(acrossNova, GapAcross(fight, Beat::Nova, phase2At));

                        std::optional<Fight::Start> last;
                        std::uint64_t lastFeast = 0;
                        std::uint32_t combosOnEnd = 0;
                        for (Fight::Start const& b : fight.starts)
                        {
                            if (last)
                            {
                                CHECK(b.at >= last->end);       // never two at once
                                if (b.beat == Beat::Feast && last->beat != Beat::Feast)
                                    CHECK(b.at >= last->end + (last->end >= phase2At ? Tune::kPhase2FeastHoldMs
                                        : Tune::kFeastAfterSetPieceMs));
                                // Phase 2: never two combos on end with no Feast between them, the start aside.
                                combosOnEnd = b.beat == Beat::Feast ? 0 : combosOnEnd + (b.beat == Beat::Nova ? 1 : 0);
                                CHECK(b.at < phase2At + 30000 || combosOnEnd <= 1);
                                // Phase 2: every Nova 2 s after a spin, every Felstorm but the last has its Nova.
                                if (last->at >= phase2At && last->beat == Beat::Felstorm)
                                    CHECK(b.beat == Beat::Nova);
                                if (b.beat == Beat::Nova && b.at >= phase2At + 30000)
                                {
                                    CHECK(last->beat == Beat::Felstorm);
                                    std::uint64_t const spinEnd = last->end - RfcTaragaman::FelstormOverMs(
                                        Mode::HardMode) + Tune::kFelstormSpinMs(Mode::HardMode);
                                    CHECK(b.at >= spinEnd + Tune::kComboNovaAfterSpinMs);
                                    CHECK(b.at <= spinEnd + Tune::kComboNovaAfterSpinMs + 100);
                                }
                                if (b.beat == Beat::Felstorm && last->beat == Beat::Felstorm)
                                    CHECK(b.at >= last->at + Tune::kFelstormEveryMs(Mode::HardMode) / 2);
                            }
                            if (b.beat == Beat::Feast)
                            {
                                if (lastFeast)
                                    CHECK(b.at >= lastFeast + Tune::kStarvingGapMs);
                                // Nobody under the line: D4's timer, half a period apart at least.
                                if (lowest >= Tune::kStarvingLinePct && lastFeast)
                                    CHECK(b.at >= lastFeast + Tune::kFeastEveryMs(Mode::HardMode) / 2);
                                lastFeast = b.at;
                            }
                            last = b;
                        }
                    }

        // The gap across the line is longer than any inside a phase, a one-time effect (RF-2's model: the Feast at most
        // 33.5 to 42.4 s and the Nova 38 to 48 s by the leaps' lengths; this one has 8.6 s Feasts too: 43.1 s).
        CHECK(acrossFeast > 33000 && acrossFeast <= 43500);
        CHECK(acrossNova > 37000 && acrossNova <= 49000);
        CHECK(acrossFelstorm <= 39000);
        std::printf("across the 30%% line (once a fight): feast %.1f felstorm %.1f nova %.1f s at most\n",
            acrossFeast / 1000.0, acrossFelstorm / 1000.0, acrossNova / 1000.0);

        // Printed for the report.
        for (float const lowest : { 100.f, 10.f })
        {
            Setup s;
            s.lowestPct = lowest;
            Fight const fight = Run(s);
            std::printf("lowest %.0f%%: phase 1 gaps felstorm %.1f nova %.1f feast %.1f s; phase 2 felstorm %.1f nova "
                "%.1f feast %.1f s\n", lowest, MaxGap(fight, Beat::Felstorm, 0, s.phase2At) / 1000.0,
                MaxGap(fight, Beat::Nova, 0, s.phase2At) / 1000.0, MaxGap(fight, Beat::Feast, 0, s.phase2At) / 1000.0,
                MaxGap(fight, Beat::Felstorm, s.phase2At, s.total) / 1000.0,
                MaxGap(fight, Beat::Nova, s.phase2At, s.total) / 1000.0,
                MaxGap(fight, Beat::Feast, s.phase2At, s.total) / 1000.0);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Ruling 16 on the real timers: the mean gap of each beat against heroic's, 50 fights of 400 s a case (the leaps,
    // the kicks and who is hurt at random).
    // ----------------------------------------------------------------------------------------------------------------
    struct Means
    {
        std::array<double, RfcTaragaman::kBeatCount> sum{};
        std::array<std::uint32_t, RfcTaragaman::kBeatCount> n{};
        std::array<double, RfcTaragaman::kBeatCount> max{};
        double Mean(Beat beat) const
        {
            std::size_t const i = static_cast<std::size_t>(beat);
            return n[i] ? sum[i] / n[i] / 1000.0 : 0.0;
        }
        double Max(Beat beat) const { return max[static_cast<std::size_t>(beat)] / 1000.0; }
    };

    struct MeanSetup
    {
        Mode mode = Mode::Heroic;
        bool phase2 = false;
        std::uint32_t lowPollPct = 0;       // a poll that finds someone under the line
        std::uint32_t fullPct = 0;          // Devours that run in full (the others kicked after 1 to 2.5 s)
    };

    Means RunMeans(MeanSetup const& s)
    {
        Means out;
        std::mt19937 rng(1);
        auto between = [&rng](std::uint32_t a, std::uint32_t b)
        {
            return a + static_cast<std::uint32_t>(rng() % (b - a + 1));
        };
        bool const hard = s.mode == Mode::HardMode;
        for (std::uint32_t fight = 0; fight < 50; ++fight)
        {
            RfcTaragaman::Timeline timeline;
            timeline.Start(s.mode, 0);
            ComboClock combo;
            if (s.phase2)
            {
                timeline.PhaseChanged(0);
                timeline.HoldSetPieces(true, 0);
                timeline.SetFeastHold(Tune::kPhase2FeastHoldMs);
                combo.Start(0, false);
            }
            std::array<std::uint64_t, RfcTaragaman::kBeatCount> last{};
            std::uint64_t lastFeast = 0;
            std::uint64_t endsAt = 0;
            std::uint64_t spinAt = 0;
            std::uint64_t spinEnds = 0;
            bool spinning = false;
            bool full = false;
            auto start = [&](Beat beat, std::uint64_t now)
            {
                timeline.Fired(beat, now);
                std::size_t const i = static_cast<std::size_t>(beat);
                if (last[i])
                {
                    double const gap = static_cast<double>(now - last[i]);
                    out.sum[i] += gap;
                    ++out.n[i];
                    out.max[i] = std::max(out.max[i], gap);
                }
                last[i] = now;
                if (beat == Beat::Feast)
                {
                    lastFeast = now;
                    full = between(1, 100) <= s.fullPct;
                    endsAt = now + Tune::kFeastMarkMs(s.mode) + between(0, RfcTaragaman::kLeapMaxMs)
                        + (full ? Tune::kDevourTicks * Tune::kDevourTickMs : between(1000, 2500));
                }
                else if (beat == Beat::Nova)
                {
                    endsAt = now + between(0, RfcTaragaman::kLeapMaxMs) + Tune::kNovaCastMs(s.mode);
                    combo.NovaStarted();
                }
                else
                {
                    spinAt = now + (hard ? between(0, 1000) : 0) + Tune::kFelstormCastMs;
                    spinEnds = spinAt + Tune::kFelstormSpinMs(s.mode);
                    endsAt = spinAt + RfcTaragaman::FelstormOverMs(s.mode);
                }
            };
            for (std::uint64_t now = 50; now < 400000; now += 50)
            {
                if (!full && timeline.Running() == Beat::Feast && now >= endsAt)
                    timeline.Ended(now);        // a kick, between two ticks
                if (s.phase2)
                {
                    ComboClock::Due const due = combo.At(now);
                    Beat const beat = due == ComboClock::Due::Nova ? Beat::Nova : Beat::Felstorm;
                    if (due != ComboClock::Due::None && timeline.MayStart(beat, now))
                        start(beat, now);
                }
                if (hard && s.lowPollPct && now % Tune::kStarvingPollMs == 0 && between(1, 100) <= s.lowPollPct
                    && LineWake(now, lastFeast, 10.f) && timeline.MayStart(Beat::Feast, now)
                    && !timeline.SetPieceDue(now))
                    start(Beat::Feast, now);
                if (spinAt && now >= spinAt)
                {
                    spinning = true;
                    combo.SpinStarted(spinAt - Tune::kFelstormCastMs);
                    spinAt = 0;
                }
                if (spinning && now >= spinEnds)
                {
                    spinning = false;
                    combo.SpinEnded(now);
                }
                if (timeline.Running() && now >= endsAt)
                    timeline.Ended(now);
                if (std::optional<Beat> const beat = timeline.Next(now, !hard
                    || TimerFeastMay(now, lastFeast, combo)))
                {
                    CHECK(!s.phase2 || combo.At(now) == ComboClock::Due::None);
                    start(*beat, now);
                }
            }
        }
        return out;
    }

    void CheckMeansAgainstHeroic()
    {
        auto print = [](char const* what, Means const& m)
        {
            std::printf("%-42s mean (max) feast %4.1f (%4.1f) felstorm %4.1f (%4.1f) nova %4.1f (%4.1f) s\n", what,
                m.Mean(Beat::Feast), m.Max(Beat::Feast), m.Mean(Beat::Felstorm), m.Max(Beat::Felstorm),
                m.Mean(Beat::Nova), m.Max(Beat::Nova));
        };
        for (std::uint32_t const fullPct : { 0u, 25u, 50u, 100u })
        {
            MeanSetup h;
            h.fullPct = fullPct;
            Means const heroic = RunMeans(h);
            char what[64];
            std::snprintf(what, sizeof what, "heroic, %u%% unkicked", fullPct);
            print(what, heroic);
            for (bool const phase2 : { false, true })
                for (std::uint32_t const low : { 0u, 5u, 100u })
                {
                    MeanSetup s;
                    s.mode = Mode::HardMode;
                    s.phase2 = phase2;
                    s.lowPollPct = low;
                    s.fullPct = fullPct;
                    Means const m = RunMeans(s);
                    std::snprintf(what, sizeof what, "hard mode phase %d, %u%% low, %u%% unkicked", phase2 ? 2 : 1, low,
                        fullPct);
                    print(what, m);
                    // Never slower than heroic: the Feast, the Felstorm and the Nova at once.
                    for (Beat const beat : { Beat::Feast, Beat::Felstorm, Beat::Nova })
                        CHECK(m.Mean(beat) <= heroic.Mean(beat) + 0.05);
                    if (phase2)
                        CHECK(m.Max(Beat::Feast) <= 28.0);      // 41 s before RF-M2's fix
                }
        }
    }
}

int main()
{
    CheckIdsAndPlaces();
    CheckRuling16();
    CheckTrigger();
    CheckWakes();
    CheckDrift();
    CheckGlobules();
    CheckClocks();
    CheckPhase2Leaps();
    CheckCadence();
    CheckMeansAgainstHeroic();
    return Report("rfc_taragaman_hard_mode_test");
}
