// Host tests for RasHardModeLogic.h (S12: Ras Frostwhisper's hard mode, the Torn Keepsake): the ids, the build spec's
// numbers, the hard mode clock (transition, Siphon Warmth, Mortal Decay and the holds), the Siphon's heal and backfire
// math, and the keepsake gameobjects' rules (pages, book, alchemy table).
#include "RasHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace ScholomanceRework;
using namespace ScholoRasHardMode;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Runs `clock` for `ms` in steps of `step`, the Siphon always free to start; sums what the steps asked for.
    struct Totals
    {
        std::uint32_t siphonCasts = 0;
        std::uint32_t channels = 0;
        std::uint32_t ticks = 0;
        std::uint32_t ends = 0;
        std::uint32_t decayTo = 0;
        bool transitionDone = false;
    };

    Totals Run(KeepsakeClock& clock, std::uint32_t ms, std::uint32_t step = 100, bool mayStart = true)
    {
        Totals t;
        for (std::uint32_t done = 0; done < ms; done += step)
        {
            ClockStep const s = clock.Advance(step, mayStart);
            t.siphonCasts += s.siphonCast ? 1 : 0;
            t.channels += s.channelStart ? 1 : 0;
            t.ticks += s.siphonTicks;
            t.ends += s.siphonEnd ? 1 : 0;
            if (s.decayTo)
                t.decayTo = s.decayTo;
            t.transitionDone = t.transitionDone || s.transitionDone;
        }
        return t;
    }
}

int main()
{
    // ---- Ids: every spell in the slice, inside the reservation, none of S4's -------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206190 && kSpellSlice.last == 206204);
    for (std::uint32_t id : { std::uint32_t(SPELL_RK_CLINGING_TO_LIFE), std::uint32_t(SPELL_RK_SIPHON_CAST),
        std::uint32_t(SPELL_RK_SIPHON_CHANNEL), std::uint32_t(SPELL_RK_SIPHONED), std::uint32_t(SPELL_RK_SIPHON_HEAL),
        std::uint32_t(SPELL_RK_SIPHON_BACKFIRE), std::uint32_t(SPELL_RK_MORTAL_DECAY),
        std::uint32_t(SPELL_RK_THAWING) })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsRas.Contains(id));
    }
    CHECK(NPC_SC_ICE_TOMB == 300535);
    CHECK(GO_SC_TORN_PAGE == 301150 && GO_SC_KEEPSAKE_BOOK == 301151 && GO_SC_KEEPSAKE_BOOK_BOUND == 301152);
    CHECK(GO_SC_ALCHEMY_TABLE == 301154);
    CHECK(EMOTE_RAS_KEEPSAKE_LIT == 3);
    CHECK(EMOTE_RAS_SIPHON_WARMTH == 2 && YELL_RAS_THIS_CANNOT_BE == 0);
    CHECK(TAG_SIPHON != ScholoRas::TAG_CHILL && TAG_SIPHON != ScholoRas::TAG_WARMTH);
    CHECK(TAG_SIPHON != ScholoRas::TAG_THAW && TAG_SIPHON != ScholoRas::TAG_FROST_MARK);
    CHECK(TAG_SIPHON != ScholoRas::TAG_BLIZZARD);

    // ---- The build spec's numbers (SC 1122-1134, 1207-1209; handoff section 3.6) ------------------------------------
    CHECK(kLichHealth == 400000 && kHumanHealth == 400000);
    CHECK(kTombHealth == 12000);
    CHECK(kTransitionMs == 3000);
    CHECK(kHumanDisplay == 3975);
    CHECK(kSiphonFirstMs == 10000 && kSiphonEveryMs == 30000);
    CHECK(kSiphonCastMs == 2000 && kSiphonChannelMs == 5000 && kSiphonTicks == 5);
    CHECK(kSiphonWarmChill == 3 * ScholoRas::kChillColdPerBeat);
    CHECK(kSiphonColdChill == ScholoRas::kChillColdPerBeat);
    CHECK(Near(kSiphonHealPctPerWarm, 1.f) && Near(kSiphonHealCapPct, 10.f));
    CHECK(Near(kSiphonBackfirePctPerCold, 1.3f));
    CHECK(Near(kSiphonSpreadRadius, 8.f));
    CHECK(Near(kDecayPctPerStack, 0.5f) && kDecayEveryMs == 10000);
    // The tomb's thaw is S4's (6 yd, 45% heroic, +3 Chill); the crack is shorter than S4's own 2 s tomb.
    CHECK(Near(ScholoRas::kThawRadius, 6.f) && Near(ScholoRas::kThawPct(true), 45.f));
    CHECK(ScholoRas::kThawChill(true) == 3);
    CHECK(kTombCrackMs > 0 && kTombCrackMs <= ScholoRas::kTombMs);

    // ---- The clock: nothing happens in the lich phase ---------------------------------------------------------------
    {
        KeepsakeClock c;
        Totals const t = Run(c, 120000);
        CHECK(c.phase == Phase::Lich);
        CHECK(t.siphonCasts == 0 && t.ticks == 0 && t.decayTo == 0 && !t.transitionDone);
        CHECK(!c.HoldsTimeline() && !c.HoldsFrostMark() && !c.HoldsChillBeat() && !c.Mortal());
    }

    // ---- The transition: 3 s, S4's clock held, then phase 2 ---------------------------------------------------------
    {
        KeepsakeClock c;
        CHECK(c.StartTransition());
        CHECK(!c.StartTransition());            // once
        CHECK(c.phase == Phase::Transition && c.HoldsTimeline() && !c.Mortal());
        Totals t = Run(c, 2900);
        CHECK(!t.transitionDone && c.phase == Phase::Transition);
        t = Run(c, 100);
        CHECK(t.transitionDone && c.phase == Phase::Human && c.humanMs == 0);
        CHECK(!c.HoldsTimeline() && c.Mortal());
        CHECK(!c.StartTransition());            // never twice
    }

    // ---- The transition heals to full over the bar ------------------------------------------------------------------
    CHECK(TransitionHealth(400000, 0) == 1);
    CHECK(TransitionHealth(400000, 1500) == 200000);
    CHECK(TransitionHealth(400000, 3000) == 400000);
    CHECK(TransitionHealth(400000, 9999) == 400000);
    CHECK(TransitionHealth(400000, 750) < TransitionHealth(400000, 2250));

    // ---- Phase 2: Siphons at 10 s and 40 s, each a 2 s warning then 5 ticks in 5 s ---------------------------------
    {
        KeepsakeClock c;
        c.StartTransition();
        Run(c, 3000);
        CHECK(c.phase == Phase::Human);
        Totals t = Run(c, 9900);
        CHECK(t.siphonCasts == 0);
        t = Run(c, 100);                        // 10 s
        CHECK(t.siphonCasts == 1 && c.siphon == SiphonStage::Warning);
        CHECK(c.HoldsFrostMark() && !c.HoldsChillBeat());
        t = Run(c, 1900);
        CHECK(t.channels == 0);
        t = Run(c, 100);                        // 12 s: the channel
        CHECK(t.channels == 1 && c.siphon == SiphonStage::Channel);
        CHECK(c.HoldsFrostMark() && c.HoldsChillBeat());
        t = Run(c, 5000);                       // 17 s
        CHECK(t.ticks == kSiphonTicks && t.ends == 1 && c.siphon == SiphonStage::Idle);
        CHECK(!c.HoldsFrostMark() && !c.HoldsChillBeat());
        t = Run(c, 22900);                      // 39.9 s
        CHECK(t.siphonCasts == 0);
        t = Run(c, 100);                        // 40 s
        CHECK(t.siphonCasts == 1 && c.siphons == 2);
    }

    // ---- A due Siphon waits (a cast, a Frost Mark), then the cadence counts from its real start ---------------------
    {
        KeepsakeClock c;
        c.StartTransition();
        Run(c, 3000);
        Totals t = Run(c, 15000, 100, false);   // due at 10 s, held to 15 s
        CHECK(t.siphonCasts == 0 && c.siphon == SiphonStage::Idle && !c.HoldsFrostMark());
        t = Run(c, 100);
        CHECK(t.siphonCasts == 1 && c.nextSiphonAt == c.humanMs + kSiphonEveryMs);
        // Once warning, nothing stops it (a hold only delays the start).
        t = Run(c, 7000, 100, false);
        CHECK(t.channels == 1 && t.ticks == kSiphonTicks && t.ends == 1);
    }

    // ---- Big steps still give every tick, once --------------------------------------------------------------------
    {
        KeepsakeClock c;
        c.StartTransition();
        Run(c, 3000, 1000);
        Totals const t = Run(c, 20000, 1000);
        CHECK(t.siphonCasts == 1 && t.channels == 1 && t.ticks == kSiphonTicks && t.ends == 1);
    }

    // ---- `.dbtest` SiphonNow --------------------------------------------------------------------------------------
    {
        KeepsakeClock c;
        c.SiphonNow();                          // not in phase 2: nothing
        CHECK(c.nextSiphonAt == kSiphonFirstMs);
        c.StartTransition();
        Run(c, 3000);
        Run(c, 1000);
        c.SiphonNow();
        Totals const t = Run(c, 100);
        CHECK(t.siphonCasts == 1);
    }

    // ---- Mortal Decay: one stack per whole 10 s of phase 2 (5 at 50 s, 12 at 2 min) --------------------------------
    CHECK(DecayStacksAt(0) == 0);
    CHECK(DecayStacksAt(9999) == 0);
    CHECK(DecayStacksAt(10000) == 1);
    CHECK(DecayStacksAt(50000) == 5);
    CHECK(DecayStacksAt(120000) == 12);
    CHECK(DecayStacksAt(5000000) == kDecayMaxStacks);
    CHECK(Near(float(DecayStacksAt(50000)) * kDecayPctPerStack, 2.5f));
    CHECK(Near(float(DecayStacksAt(120000)) * kDecayPctPerStack, 6.f));
    {
        KeepsakeClock c;
        c.StartTransition();
        Run(c, 3000);
        Totals t = Run(c, 9900);
        CHECK(t.decayTo == 0);
        t = Run(c, 100);
        CHECK(t.decayTo == 1);
        t = Run(c, 40000);
        CHECK(t.decayTo == 5 && c.decayStacks == 5);
    }

    // ---- Siphon math: heal 1% per warm player per tick, capped at 10% a Siphon; backfire 1.3% per cold player ------
    CHECK(Near(SiphonHealPct(0, 0.f), 0.f));
    CHECK(Near(SiphonHealPct(3, 0.f), 3.f));
    CHECK(Near(SiphonHealPct(5, 8.f), 2.f));
    CHECK(Near(SiphonHealPct(5, 10.f), 0.f));
    {
        // Five warm for the whole channel: 5% a tick, capped at 10% (two ticks).
        float healed = 0.f;
        for (std::uint32_t i = 0; i < kSiphonTicks; ++i)
            healed += SiphonHealPct(5, healed);
        CHECK(Near(healed, kSiphonHealCapPct));
    }
    // All five cold for the full 5 s: about 32% of his bar (SC RF10).
    CHECK(Near(SiphonBackfirePct() * 5.f * float(kSiphonTicks), 32.5f));
    CHECK(PctOf(400000, 1.3f) == 5200);
    CHECK(PctOf(400000, 1.f) == 4000);
    CHECK(PctOf(400000, 0.f) == 0);
    // Two clean Siphons take about 260k of the 400k human bar (SC tuning): all cold twice.
    CHECK(PctOf(kHumanHealth, SiphonBackfirePct() * 5.f * float(kSiphonTicks)) * 2 == 260000);

    // ---- The pages: each spawn spot names its page; nothing else does --------------------------------------------
    for (std::size_t i = 0; i < kKeepsakePageCount; ++i)
    {
        Point4 const& p = kKeepsakePages[i];
        CHECK(PageAt(p.x, p.y, p.z) == i);
        CHECK(PageAt(p.x + 1.f, p.y - 1.f, p.z + 0.5f) == i);
    }
    CHECK(PageAt(kKeepsakeBook.x, kKeepsakeBook.y, kKeepsakeBook.z) == kKeepsakePageCount);
    CHECK(PageAt(kHardModeTable.x, kHardModeTable.y, kHardModeTable.z) == kKeepsakePageCount);
    // The three spots are far apart (no spawn can match two pages).
    for (std::size_t i = 0; i < kKeepsakePageCount; ++i)
        for (std::size_t j = i + 1; j < kKeepsakePageCount; ++j)
        {
            float const dx = kKeepsakePages[i].x - kKeepsakePages[j].x;
            float const dy = kKeepsakePages[i].y - kKeepsakePages[j].y;
            CHECK(std::sqrt(dx * dx + dy * dy) > 2.f * kPageMatchYd);
        }

    // A page shows on heroic, until found, while Ras lives.
    CHECK(PageShows(true, 0, 0, DungeonKit::State::NotStarted));
    CHECK(PageShows(true, 0b010, 0, DungeonKit::State::InProgress));
    CHECK(!PageShows(true, 0b001, 0, DungeonKit::State::NotStarted));
    CHECK(!PageShows(false, 0, 0, DungeonKit::State::NotStarted));
    CHECK(!PageShows(true, 0, 1, DungeonKit::State::Done));
    CHECK(!PageShows(true, 0, kKeepsakePageCount, DungeonKit::State::NotStarted));
    // The page rule agrees with the instance's (KeepsakePageAllowed): a page that shows is one the instance takes.
    for (std::uint32_t state :
        { DungeonKit::State::NotStarted, DungeonKit::State::InProgress, DungeonKit::State::Done })
        for (bool heroic : { false, true })
            CHECK(PageShows(heroic, 0, 0, state) == KeepsakePageAllowed(0, heroic, state));

    // The book: the empty one until bound, then the bound one; never both, never neither.
    CHECK(BookShows(false, false) && !BookShows(true, false));
    CHECK(!BookShows(false, true) && BookShows(true, true));

    // ---- The alchemy table ------------------------------------------------------------------------------------------
    using DungeonKit::State::Done;
    using DungeonKit::State::InProgress;
    using DungeonKit::State::NotStarted;
    CHECK(TableCheck(true, true, false, NotStarted) == TableRefusal::None);
    CHECK(TableCheck(false, true, false, NotStarted) == TableRefusal::NotHeroic);
    CHECK(TableCheck(true, false, false, NotStarted) == TableRefusal::NotBound);
    CHECK(TableCheck(true, true, true, NotStarted) == TableRefusal::AlreadyLit);
    CHECK(TableCheck(true, true, false, InProgress) == TableRefusal::RasFighting);
    CHECK(TableCheck(true, true, false, Done) == TableRefusal::RasDead);
    CHECK(TableCheck(true, true, false, DungeonKit::State::Fail) == TableRefusal::None);
    // The table agrees with the instance's own rule (RasHardModeChangeAllowed) whenever the flag is still unlit.
    for (std::uint32_t state : { NotStarted, InProgress, DungeonKit::State::Fail, Done })
        for (bool heroic : { false, true })
            for (bool bound : { false, true })
                CHECK((TableCheck(heroic, bound, false, state) == TableRefusal::None)
                    == RasHardModeChangeAllowed(1, bound, heroic, state));
    for (TableRefusal why : { TableRefusal::NotHeroic, TableRefusal::RasDead, TableRefusal::AlreadyLit,
        TableRefusal::NotBound, TableRefusal::RasFighting })
        CHECK(TableRefusalText(why)[0] != '\0');
    CHECK(TableRefusalText(TableRefusal::None)[0] == '\0');

    // The book and the table stand outside Ras's arena (KS's scholomance_test checks every arena).
    CHECK(!RasArena().Contains(kKeepsakeBook.XY(), kKeepsakeBook.z));
    CHECK(!RasArena().Contains(kHardModeTable.XY(), kHardModeTable.z));

    return Report("scholo_keepsake_test");
}
