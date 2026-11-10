// Host tests for ForrestenLogic.h (S2: Hearthsinger Forresten (10558)): the ids, the build spec numbers (ST 826-882),
// the set list (timers, never health), the rat counts, the notes, Drowsy and the hearth, the rat volley's queue,
// aim and lanes, the Lullaby focus, Plague Bite and the arena.
#include "ForrestenLogic.h"
#include "check.h"
#include <cmath>
#include <map>
#include <set>

using namespace StratholmeRework;
using namespace StratForresten;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    constexpr float kDeg = DungeonKit::kPi / 180.f;
    Vec2 Spawn() { return kForrestenSpawn.XY(); }

    // The song starts and ends of a pull up to `endMs`, stepping `stepMs` (a long frame must not skip any).
    std::vector<SetList::Event> Play(bool heroic, std::uint64_t endMs, std::uint64_t stepMs)
    {
        SetList list;
        list.Reset(heroic);
        std::vector<SetList::Event> out;
        for (std::uint64_t now = 0; now <= endMs; now += stepMs)
            for (SetList::Event const& e : list.Advance(now))
                out.push_back(e);
        return out;
    }
}

int main()
{
    // ---- ids and slice --------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206440 && kSpellSlice.last == 206459);
    CHECK(SPELL_HF_NOTE == 206440 && SPELL_HF_HEARTH_GLOW == 206448);
    CHECK(SPELL_HF_HEARTH_GLOW <= kSpellSlice.last);
    // The ids are distinct and none sits outside the slice.
    std::set<std::uint32_t> const ids{ SPELL_HF_NOTE, SPELL_HF_DANCE, SPELL_HF_DROWSY, SPELL_HF_ASLEEP,
        SPELL_HF_RAT_LINE, SPELL_HF_CRESCENDO_LINE, SPELL_HF_CRESCENDO, SPELL_HF_PLAGUE_BITE, SPELL_HF_HEARTH_GLOW };
    CHECK(ids.size() == 9);
    for (std::uint32_t id : ids)
        CHECK(kSpellSlice.Contains(id));
    // The rat and the hearth stalker are the wave 2 slice's.
    CHECK(kCreaturesWave2.Contains(NPC_ST_GUTTER_RAT) && kCreaturesWave2.Contains(NPC_ST_HEARTH));
    CHECK(NPC_ST_GUTTER_RAT == 300602 && NPC_ST_HEARTH == 300603);
    // The boss spawns inside his arena.
    CHECK(ForrestenArena().Contains(kForrestenSpawn.XY(), kForrestenSpawn.z));
    CHECK(ArenaFor(BOSS_FORRESTEN).Contains(kForrestenSpawn.XY(), kForrestenSpawn.z));

    // ---- HF1 the set list: timers, normal --------------------------------------------------------------------------
    CHECK(kFirstSongMs == 6000);
    CHECK(kSongMs(false) == 20000 && kSongMs(true) == 18000);
    CHECK(kBreakMs(false) == 6000 && kBreakMs(true) == 4000);
    {
        std::vector<SetList::Event> const events = Play(false, 100000, 100);
        // Song starts at 6, 32, 58, 84 s; each ends 20 s later; the rotation is Jig, Lullaby, Piper, Jig.
        std::vector<std::pair<std::uint64_t, Song>> starts;
        std::vector<std::uint64_t> ends;
        for (SetList::Event const& e : events)
        {
            if (e.kind == SetList::Event::Kind::SongStart)
                starts.emplace_back(e.at, e.song);
            else
                ends.push_back(e.at);
        }
        CHECK(starts.size() == 4);
        CHECK(starts[0].first == 6000 && starts[0].second == Song::Jig);
        CHECK(starts[1].first == 32000 && starts[1].second == Song::Lullaby);
        CHECK(starts[2].first == 58000 && starts[2].second == Song::Piper);
        CHECK(starts[3].first == 84000 && starts[3].second == Song::Jig);
        CHECK(ends.size() == 3 && ends[0] == 26000 && ends[1] == 52000 && ends[2] == 78000);
    }
    // heroic: 18 s songs with 4 s breaks: starts at 6, 28, 50 s
    {
        std::vector<SetList::Event> const events = Play(true, 60000, 100);
        std::vector<std::uint64_t> starts;
        for (SetList::Event const& e : events)
            if (e.kind == SetList::Event::Kind::SongStart)
                starts.push_back(e.at);
        CHECK(starts.size() == 3 && starts[0] == 6000 && starts[1] == 28000 && starts[2] == 50000);
    }
    // a 7 s frame never skips a start or an end, and gives the same list as 100 ms steps
    {
        std::vector<SetList::Event> const fine = Play(false, 100000, 100);
        std::vector<SetList::Event> const coarse = Play(false, 100000, 7000);
        CHECK(fine.size() == coarse.size());
        for (std::size_t i = 0; i < fine.size() && i < coarse.size(); ++i)
            CHECK(fine[i].at == coarse[i].at && fine[i].kind == coarse[i].kind && fine[i].song == coarse[i].song);
    }
    // state queries
    {
        SetList list;
        list.Reset(false);
        CHECK(list.InBreak() && !list.InSong());
        CHECK(list.Advance(5999).empty());
        CHECK(list.NextStartMs() == 6000 && list.NextPlaying() == Song::Jig);
        CHECK(list.Advance(6000).size() == 1);
        CHECK(list.InSong() && list.Current() == Song::Jig && list.StartMs() == 6000 && list.EndMs() == 26000);
        CHECK(list.Advance(26000).size() == 1);
        CHECK(list.InBreak() && list.NextStartMs() == 32000 && list.NextPlaying() == Song::Lullaby);
        CHECK(list.Index() == 1);
        // A GM test starts a song at once; the rotation goes on after it
        CHECK(list.Force(Song::Piper, 27000));
        std::vector<SetList::Event> const forced = list.Advance(27000);
        CHECK(forced.size() == 1 && forced[0].song == Song::Piper && forced[0].at == 27000);
        CHECK(!list.Force(Song::Jig, 28000));   // one is playing
        list.Advance(47000);
        CHECK(list.NextPlaying() == Song::Jig && list.NextStartMs() == 53000);
    }
    CHECK(NextSong(Song::Jig) == Song::Lullaby && NextSong(Song::Lullaby) == Song::Piper
        && NextSong(Song::Piper) == Song::Jig);

    // ---- HF2 the rats ----------------------------------------------------------------------------------------------
    CHECK(RatsAtStart(Song::Jig, false) == 6 && RatsAtStart(Song::Lullaby, false) == 6
        && RatsAtStart(Song::Piper, false) == 3);
    CHECK(RatsAtStart(Song::Jig, true) == 8 && RatsAtStart(Song::Lullaby, true) == 8
        && RatsAtStart(Song::Piper, true) == 4);
    CHECK(kMissedRats(false) == 0 && kMissedRats(true) == 4);
    // Plague Bite: +1 a bite, at most 5; 10 s
    CHECK(BiteStacks(0) == 1 && BiteStacks(4) == 5 && BiteStacks(5) == 5 && BiteStacks(9) == 5);
    CHECK(kBiteMs == 10000);

    // ---- HF4 the notes ---------------------------------------------------------------------------------------------
    CHECK(NoteCount(false, 5) == 2 && NoteCount(false, 1) == 1 && NoteCount(false, 0) == 0);
    CHECK(NoteCount(true, 5) == 5 && NoteCount(true, 3) == 3);
    CHECK(kNoteSpots == 2 && kNoteRadius == 4.f && kNoteWarnMs == 1500 && kNotePct == 20.f);
    CHECK(kJigBeatMs(false) == 2000 && kJigBeatMs(true) == 2000 && kJigDoubleBeatMs == 1000);
    // The beats of a normal 20 s song at 2 s from 1 s: 10 beats, the last at 19 s (its hit at 20.5 s)
    {
        int beats = 0;
        for (std::uint32_t t = kJigFirstBeatMs; t < kSongMs(false); t += kJigBeatMs(false))
            ++beats;
        CHECK(beats == 10);
    }

    // ---- HF6 Drowsy and the hearth ---------------------------------------------------------------------------------
    {
        DrowsyResult r = DrowsyStep(0);
        CHECK(r.stacks == 1 && !r.sleep);
        r = DrowsyStep(r.stacks);
        CHECK(r.stacks == 2 && !r.sleep);
        r = DrowsyStep(r.stacks);
        CHECK(r.stacks == 0 && r.sleep);        // three ticks: asleep, the stacks clear
    }
    CHECK(kSleepMs == 2000 && kDrowsyTickMs == 2000 && kDrowsyToSleep == 3);
    CHECK(InHearth(0.f, 0.f) && InHearth(8.f, 0.f) && !InHearth(8.1f, 0.f));
    CHECK(InHearth(5.f, 5.9f) && !InHearth(5.f, 6.5f) && !InHearth(5.f, -7.f));
    CHECK(kHearthRadius == 8.f);

    // ---- HF5 / HF10 where the hearth lights ------------------------------------------------------------------------
    {
        DungeonKit::FloorSpotRules const first = HearthRules(Spawn(), false, std::nullopt);
        CHECK(first.minRange == 10.f && first.maxRange == 15.f && first.awayFrom.empty());
        DungeonKit::FloorSpotRules const moved = HearthRules(Spawn(), true, Vec2{ 3608.f, -3510.f });
        CHECK(moved.minRange == 15.f && moved.maxRange == 20.f);
        CHECK(moved.awayFrom.size() == 1 && moved.minFromAway == kHearthAwayFromOldYd);
        // The measured hearths of the navmesh report sit in the first ring (10..15 yd from his spawn), the moved ones
        // in the second (15..20 yd).
        for (Vec2 const& h : HearthFallbacks(false))
        {
            float const d = DungeonKit::Distance(Spawn(), h);
            CHECK(d >= 10.f && d <= 15.f);
        }
        for (Vec2 const& h : HearthFallbacks(true))
        {
            float const d = DungeonKit::Distance(Spawn(), h);
            CHECK(d >= 15.f && d <= 20.1f);
        }
        CHECK(HearthFallbacks(false).size() == 3 && HearthFallbacks(true).size() == 3);
        // A pick on an open floor lands in the ring and away from the old hearth.
        float u = 0.1f;
        auto rand01 = [&u]() { u = std::fmod(u * 7.31f + 0.137f, 1.f); return u; };
        auto floor = [](Vec2) -> std::optional<float> { return 137.f; };
        std::optional<DungeonKit::FloorSpot> const spot = DungeonKit::PickFloorSpotFrom(moved, rand01, floor,
            HearthFallbacks(true));
        CHECK(spot.has_value() && spot->full);
        if (spot)
        {
            float const d = DungeonKit::Distance(Spawn(), spot->p);
            CHECK(d >= 15.f - 0.01f && d <= 20.f + 0.01f);
            CHECK(DungeonKit::Distance(spot->p, Vec2{ 3608.f, -3510.f }) >= kHearthAwayFromOldYd - 0.01f);
        }
    }
    CHECK(kMovedGlowMs == 2000);

    // ---- HF2 / HF6 the rats go for the drowsy and the sleeping ----------------------------------------------------
    {
        std::vector<FocusCandidate> pool;
        CHECK(!LullabyFocus(pool).has_value());
        pool.push_back({ 1, false, 0, 5.f });
        CHECK(!LullabyFocus(pool).has_value());                         // nobody drowsy: no preference
        pool.push_back({ 2, false, 1, 20.f });
        pool.push_back({ 3, false, 2, 30.f });
        CHECK(LullabyFocus(pool) == std::optional<std::uint64_t>(3));   // the most Drowsy
        pool.push_back({ 4, true, 0, 40.f });
        CHECK(LullabyFocus(pool) == std::optional<std::uint64_t>(4));   // asleep beats stacks
        pool.push_back({ 5, true, 0, 10.f });
        CHECK(LullabyFocus(pool) == std::optional<std::uint64_t>(5));   // then the nearest
        std::vector<FocusCandidate> tie{ { 7, false, 2, 12.f }, { 8, false, 2, 9.f } };
        CHECK(LullabyFocus(tie) == std::optional<std::uint64_t>(8));
    }

    // ---- HF8 Crescendo ---------------------------------------------------------------------------------------------
    CHECK(CrescendoOffsetMs(0.f) == 5000 && CrescendoOffsetMs(1.f) == 12000);
    CHECK(CrescendoOffsetMs(0.5f) == 8500);
    CHECK(CrescendoOffsetMs(-1.f) == 5000 && CrescendoOffsetMs(3.f) == 12000);
    CHECK(kCrescendoCastMs == 3000);
    // The latest cast ends inside the shortest song: 12 + 3 s < 18 s
    CHECK(CrescendoOffsetMs(1.f) + kCrescendoCastMs < kSongMs(true));
    CHECK(kBigLineWidth == 6.f && kBigLineWarnMs == 2000 && kBigLinePct == 30.f);

    // ---- HF7 aim, lanes and turns ----------------------------------------------------------------------------------
    {
        Vec2 const player{ 3610.f, -3500.f };
        CHECK(Near(DungeonKit::Distance(player, AimPoint(player, 0.f, 0.f)), 0.f));
        CHECK(Near(DungeonKit::Distance(player, AimPoint(player, 0.3f, 0.5f)), 2.f));
        CHECK(Near(DungeonKit::Distance(player, AimPoint(player, 0.9f, 0.999f)), 4.f, 0.01f));
        // the direction follows the angle: a quarter turn is +y
        Vec2 const q = AimPoint(player, 0.25f, 0.5f);
        CHECK(Near(q.x, player.x, 0.01f) && Near(q.y, player.y + 2.f, 0.01f));
    }
    {
        // North (+x), bearing 0 and 45: open for the whole cap (the table: 77 and 59 yd of square)
        Vec2 const north = LaneEnd(Spawn(), { Spawn().x + 10.f, Spawn().y }, kRatLineCapYd);
        CHECK(Near(DungeonKit::Distance(Spawn(), north), 30.f, 0.01f));
        Vec2 const diag = LaneEnd(Spawn(), DungeonKit::Advance(Spawn(), 45.f * kDeg, 10.f), kRatLineCapYd);
        CHECK(Near(DungeonKit::Distance(Spawn(), diag), 30.f, 0.01f));
        // Toward his back wall (bearing 120: the table says 1..3 yd) the line is a stub
        Vec2 const back = LaneEnd(Spawn(), DungeonKit::Advance(Spawn(), 120.f * kDeg, 10.f), kRatLineCapYd);
        float const stub = DungeonKit::Distance(Spawn(), back);
        CHECK(stub > 1.f && stub < 4.f);
        Vec2 const back210 = LaneEnd(Spawn(), DungeonKit::Advance(Spawn(), 210.f * kDeg, 10.f), kRatLineCapYd);
        CHECK(DungeonKit::Distance(Spawn(), back210) < 1.f);
        // A longer cap for the big lines (HF11): 60 yd on the open side
        Vec2 const big = LaneEnd(Spawn(), { Spawn().x + 10.f, Spawn().y }, kBigLineCapYd);
        CHECK(Near(DungeonKit::Distance(Spawn(), big), 60.f, 0.01f));
        // From the leash center (the tank moved him) every bearing toward the square is the cap
        Vec2 const center{ 3610.f, -3500.f };
        for (int bearing : { 0, 30, 60, 90, 330, 345 })
        {
            Vec2 const end = LaneEnd(center, DungeonKit::Advance(center, bearing * kDeg, 10.f), kRatLineCapYd);
            CHECK(DungeonKit::Distance(center, end) > 13.f);
        }
    }
    {
        // players are taken in turn: three ids come up once each before any repeats
        TurnOrder order;
        std::vector<std::uint64_t> const ids3{ 11, 12, 13 };
        std::uint32_t seed = 1;
        auto pick = [&seed](std::uint32_t n) { seed = seed * 1103515245u + 12345u; return (seed >> 16) % n; };
        for (int cycle = 0; cycle < 4; ++cycle)
        {
            std::set<std::uint64_t> seen;
            for (int i = 0; i < 3; ++i)
            {
                std::optional<std::uint64_t> const id = order.Next(ids3, pick);
                CHECK(id.has_value());
                if (id)
                    seen.insert(*id);
            }
            CHECK(seen.size() == 3);
        }
        // one leaves, one joins mid-cycle: the leaver is skipped, the joiner takes a turn
        order.Reset();
        std::optional<std::uint64_t> const first = order.Next(ids3, pick);
        std::vector<std::uint64_t> const next{ 12, 13, 14 };
        std::set<std::uint64_t> seen;
        if (first)
            seen.insert(*first);
        for (int i = 0; i < 3; ++i)
            if (std::optional<std::uint64_t> const id = order.Next(next, pick))
                seen.insert(*id);
        CHECK(seen.count(14) == 1 || *first == 14);
        CHECK(!order.Next({}, pick).has_value());
        // a lone player always draws
        TurnOrder solo;
        for (int i = 0; i < 3; ++i)
            CHECK(solo.Next({ 99 }, pick) == std::optional<std::uint64_t>(99));
    }

    // ---- HF7 the volley's queue ------------------------------------------------------------------------------------
    {
        Volley volley;
        CHECK(!volley.Active());
        CHECK(!volley.LineDue(0, 3));
        volley.Begin(10000);
        CHECK(volley.Active());
        CHECK(!volley.LineDue(10000, 0));       // nobody staged yet
        CHECK(volley.LineDue(10000, 2));
        volley.LineLaunched(10000);
        CHECK(!volley.LineDue(10499, 2));       // a new line every 0.5 s
        CHECK(volley.LineDue(10500, 2));
        volley.LineLaunched(10500);
        CHECK(volley.Launched() == 2 && volley.LastLaunchAt() == 10500);
        CHECK(!volley.Done(1, 0));
        CHECK(!volley.Done(0, 2));              // rats still on their way join the queue
        CHECK(volley.Done(0, 0));
        volley.End();
        CHECK(!volley.Active() && !volley.Done(0, 0));
        // 20 rats make 20 lines over 10 s (the build spec)
        Volley twenty;
        twenty.Begin(0);
        std::uint64_t t = 0;
        std::uint32_t left = 20;
        while (left)
        {
            if (twenty.LineDue(t, left))
            {
                twenty.LineLaunched(t);
                --left;
            }
            t += 100;
        }
        CHECK(twenty.Launched() == 20 && twenty.LastLaunchAt() == 9500);
    }
    // The second volley: 2 s after the first's last line, if 3 s of the song remain
    {
        // the song runs 6 s..26 s (normal); the volley starts 4 s in (10 s)
        CHECK(SecondVolleyAt(15000, 26000) == std::optional<std::uint64_t>(17000));      // 9 s left
        CHECK(SecondVolleyAt(21000, 26000) == std::optional<std::uint64_t>(23000));      // exactly 3 s left
        CHECK(!SecondVolleyAt(21001, 26000).has_value());                                // 2.999 s left
        CHECK(!SecondVolleyAt(30000, 26000).has_value());
        CHECK(kVolleyFirstMs == 4000 && kVolleySecondGapMs == 2000 && kVolleySecondMinLeftMs == 3000);
    }
    // A rat's run: out and back, at 12 yd/s; the registry's declared speed is a little lower.
    CHECK(RatRunMs(30.f) == 5000);
    CHECK(RatRunMs(6.f) == 1000);
    CHECK(kRatLineSpeed < kRatRunSpeed);
    CHECK(kRatLineWidth == 2.f && kRatLineWarnMs == 2000 && kRatLinePct == 15.f && kRatLineCapYd == 30.f);
    CHECK(kRatLineWarnMs >= 2 * kVolleyLineEveryMs);
    // One hit per player per line (ORCH F-2 ruling, ST HF7): the return pass spares whoever the out pass took.
    {
        std::map<std::uint32_t, std::set<std::uint64_t>> hit;
        CHECK(!HitOnEarlierPass(hit, 1, std::uint64_t(7)));
        hit[0] = { 7, 8 };
        CHECK(!HitOnEarlierPass(hit, 0, std::uint64_t(7)));     // the out pass itself: never spared
        CHECK(HitOnEarlierPass(hit, 1, std::uint64_t(7)));
        CHECK(HitOnEarlierPass(hit, 1, std::uint64_t(8)));
        CHECK(!HitOnEarlierPass(hit, 1, std::uint64_t(9)));     // new on the way back: hit
        hit[1] = { 9 };
        CHECK(!HitOnEarlierPass(hit, 1, std::uint64_t(9)));     // its own pass does not count
    }

    // ---- the stock bow ---------------------------------------------------------------------------------------------
    CHECK(SPELL_SHOOT_FORRESTEN == 16100 && SPELL_MULTI_SHOT == 14443);
    // The shortest break (heroic 4 s) holds two shots and the Multi-Shot
    CHECK(kShootFirstMs + kShootEveryMs < kBreakMs(true) && kMultiShotAtMs < kBreakMs(true));

    // ---- texts ------------------------------------------------------------------------------------------------------
    CHECK(YELL_FORRESTEN_AGGRO == 0 && YELL_FORRESTEN_JIG == 1 && YELL_FORRESTEN_LULLABY == 2
        && YELL_FORRESTEN_PIPER == 3 && EMOTE_FORRESTEN_CRESCENDO == 4 && YELL_FORRESTEN_DEATH == 5);

    return Report("strat_forresten_test");
}
