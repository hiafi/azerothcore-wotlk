// Host tests for Baron Silverlaine (WP-S3): SilverlaineLogic.h. Handoff section 5: echo order and "one alive" on
// normal (on the timer ruling, section 10 / section 7 #21), Lingering Echoes and The Night Ends on heroic, the echoes'
// reused mechanics (fragment points and cap, the hook's cadence, the hunt and Maul numbers) and Accursed Veil.
#include "SilverlaineLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <array>
#include <cmath>
#include <optional>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace Silverlaine;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Reference rows (handoff section 3.7): normal 1,300 / heroic 4,120 for a non-tank.
    float RefPct(float pct, bool heroic)
    {
        return (heroic ? 4120.f : 1300.f) * pct / 100.f;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(kSlice.first));
        CHECK(kSpellsReservation.Contains(kSlice.last));
        CHECK(kSlice.first <= kSlice.last);
        CHECK(SilverlaineArena().Contains(kSilverlaineSpawn.XY(), kSilverlaineSpawn.z));

        std::array<std::uint32_t, 5> const spells{ { SPELL_ACCURSED_VEIL, SPELL_ACCURSED_VEIL_SPREAD, SPELL_ECHO_MAUL,
            SPELL_SPECTRAL_ECHO, SPELL_ECHO_ARRIVAL } };
        std::set<std::uint32_t> unique;
        for (std::uint32_t const id : spells)
        {
            CHECK(kSlice.Contains(id));
            unique.insert(id);
        }
        CHECK(unique.size() == spells.size());

        // The reused spells are the other bosses', in their slices (never copied into this one).
        CHECK(kSpellsRethilgore.Contains(Rethilgore::SPELL_SOUL_DRAIN));
        CHECK(kSpellsRethilgore.Contains(Rethilgore::SPELL_SOUL_FEAST));
        CHECK(kSpellsRazorclaw.Contains(Razorclaw::SPELL_RC_MEAT_HOOK_HIT));
        CHECK(!kSlice.Contains(Rethilgore::SPELL_SOUL_DRAIN) && !kSlice.Contains(Razorclaw::SPELL_RC_MEAT_HOOK_HIT));

        // Tags are the build spec's mechanic numbers, distinct.
        std::set<std::uint32_t> const tags{ kTagEchoFragment, kTagEchoHook, kTagEchoHunt, kTagAccursedVeil };
        CHECK(tags.size() == 4);
    }

    void TestEchoKinds()
    {
        std::set<std::uint32_t> entries;
        for (EchoKind const kind : kKillOrder)
        {
            std::uint32_t const entry = EchoEntry(kind);
            entries.insert(entry);
            CHECK(kCreaturesReservation.Contains(entry));
            CHECK(KindOfEntry(entry) == kind);
        }
        CHECK(entries.size() == kEchoKinds);
        CHECK(EchoEntry(EchoKind::Rethilgore) == 300503);
        CHECK(EchoEntry(EchoKind::Razorclaw) == 300504);
        CHECK(EchoEntry(EchoKind::Odo) == 300505);
        CHECK(!KindOfEntry(NPC_SILVERLAINE));
        CHECK(!KindOfEntry(NPC_SFK_SOUL_FRAGMENT));

        // Kill order (the build spec's): Rethilgore, Razorclaw, Odo, with yells 1-3.
        CHECK(kKillOrder[0] == EchoKind::Rethilgore && kKillOrder[1] == EchoKind::Razorclaw
            && kKillOrder[2] == EchoKind::Odo);
        CHECK(EchoYell(EchoKind::Rethilgore) == 1 && EchoYell(EchoKind::Razorclaw) == 2
            && EchoYell(EchoKind::Odo) == 3);
        CHECK(YELL_SILVERLAINE_NIGHT_ENDS == 4);
        CHECK((Bit(EchoKind::Rethilgore) | Bit(EchoKind::Razorclaw) | Bit(EchoKind::Odo)) == 0x7);

        // Health: 1,200 on normal (warrior base 484 x the modifier, rounded up by the core), 20,000 on heroic.
        CHECK(std::ceil(static_cast<float>(kWarriorBaseHealthL20) * kEchoHealthModifier) == 1200.f);
        CHECK(kEchoHealth(false) == 1200 && kEchoHealth(true) == 20000);
    }

    // The ruling: first at 15 s, then every 25 s; nothing on health.
    void TestEchoClockTimers()
    {
        EchoClock clock;
        clock.Start();
        CHECK(clock.UntilMs() == 15000);
        CHECK(!clock.Update(14999, 0, false));
        std::optional<EchoKind> due = clock.Update(1, 0, false);
        CHECK(due == EchoKind::Rethilgore);
        clock.Summoned(*due);
        CHECK(clock.UntilMs() == 25000);
        CHECK(clock.NextKind() == EchoKind::Razorclaw);
        CHECK(!clock.Update(24999, 0, false));
        due = clock.Update(1, 0, false);
        CHECK(due == EchoKind::Razorclaw);
        clock.Summoned(*due);
        due = clock.Update(25000, 0, false);
        CHECK(due == EchoKind::Odo);
        clock.Summoned(*due);
        // Round again in kill order.
        due = clock.Update(25000, 0, false);
        CHECK(due == EchoKind::Rethilgore);

        // Start resets the clock and the order.
        clock.Start();
        CHECK(clock.UntilMs() == 15000 && clock.NextKind() == EchoKind::Rethilgore);
    }

    // Normal: one alive at most; a due echo waits for the live one, then comes at once.
    void TestEchoClockNormalWaits()
    {
        EchoClock clock;
        clock.Start();
        std::optional<EchoKind> due = clock.Update(15000, 0, false);
        CHECK(due == EchoKind::Rethilgore);
        clock.Summoned(*due);
        // The Rethilgore echo is still alive when the next is due: Razorclaw waits.
        CHECK(!clock.Update(25000, Bit(EchoKind::Rethilgore), false));
        CHECK(!clock.Update(5000, Bit(EchoKind::Rethilgore), false));
        // Any echo alive blocks it, whatever its kind.
        CHECK(!clock.Update(100, Bit(EchoKind::Odo), false));
        due = clock.Update(100, 0, false);
        CHECK(due == EchoKind::Razorclaw);
        clock.Summoned(*due);
        CHECK(clock.UntilMs() == 25000);
    }

    // Heroic (Lingering Echoes): several alive; a due kind still alive gives its turn to the next kind not alive; all
    // three alive wait.
    void TestEchoClockHeroic()
    {
        EchoClock clock;
        clock.Start();
        std::optional<EchoKind> due = clock.Update(15000, 0, true);
        CHECK(due == EchoKind::Rethilgore);
        clock.Summoned(*due);
        due = clock.Update(25000, Bit(EchoKind::Rethilgore), true);
        CHECK(due == EchoKind::Razorclaw);
        clock.Summoned(*due);
        std::uint8_t alive = Bit(EchoKind::Rethilgore) | Bit(EchoKind::Razorclaw);
        due = clock.Update(25000, alive, true);
        CHECK(due == EchoKind::Odo);
        clock.Summoned(*due);
        alive |= Bit(EchoKind::Odo);
        CHECK(!clock.Update(25000, alive, true));
        // Razorclaw's echo died: Rethilgore's turn, still alive, passes to Razorclaw.
        alive = Bit(EchoKind::Rethilgore) | Bit(EchoKind::Odo);
        due = clock.Update(0, alive, true);
        CHECK(due == EchoKind::Razorclaw);
        clock.Summoned(*due);
        CHECK(clock.NextKind() == EchoKind::Odo);
        // Odo's turn, Odo alive, Rethilgore alive, Razorclaw alive again: wait; Odo dead: Odo.
        alive = 0x7;
        CHECK(!clock.Update(25000, alive, true));
        due = clock.Update(0, static_cast<std::uint8_t>(alive & ~Bit(EchoKind::Odo)), true);
        CHECK(due == EchoKind::Odo);
    }

    // A normal fight at the build spec's pace (about 75 s): echoes at 15, 40 and 65 s, each fading at 12 s, never two
    // alive. Steps of 100 ms.
    void TestNormalFightTimeline()
    {
        EchoClock clock;
        clock.Start();
        std::vector<std::pair<std::uint32_t, EchoKind>> arrivals;
        std::optional<std::uint32_t> aliveSince;
        std::uint8_t alive = 0;
        std::uint32_t maxAlive = 0;
        for (std::uint32_t t = 100; t <= 90000; t += 100)
        {
            if (aliveSince && EchoFades(t - *aliveSince, kEchoLifeMs(false), false))
            {
                alive = 0;
                aliveSince.reset();
            }
            if (std::optional<EchoKind> const due = clock.Update(100, alive, false))
            {
                clock.Summoned(*due);
                arrivals.emplace_back(t, *due);
                alive = Bit(*due);
                aliveSince = t;
            }
            std::uint32_t count = 0;
            for (std::size_t i = 0; i < kEchoKinds; ++i)
                count += (alive >> i) & 1u;
            maxAlive = std::max(maxAlive, count);
        }
        CHECK(arrivals.size() == 4);
        CHECK(arrivals.size() >= 3 && arrivals[0].first == 15000 && arrivals[1].first == 40000
            && arrivals[2].first == 65000);
        CHECK(arrivals.size() >= 3 && arrivals[0].second == EchoKind::Rethilgore
            && arrivals[1].second == EchoKind::Razorclaw && arrivals[2].second == EchoKind::Odo);
        CHECK(maxAlive == 1);
        // The 12 s life always ends before the next is due (25 s cadence): normal never actually waits.
        CHECK(kEchoLifeMs(false) < kEchoEveryMs);
    }

    void TestNightEnds()
    {
        CHECK(!NightEndsDue(false, false, 5.f));
        CHECK(!NightEndsDue(true, false, 10.1f));
        CHECK(NightEndsDue(true, false, 10.f));
        CHECK(NightEndsDue(true, false, 1.f));
        CHECK(!NightEndsDue(true, true, 5.f));

        std::vector<EchoKind> back = NightEndsReturns(0);
        CHECK(back.size() == 3 && back[0] == EchoKind::Rethilgore && back[1] == EchoKind::Razorclaw
            && back[2] == EchoKind::Odo);
        back = NightEndsReturns(Bit(EchoKind::Razorclaw));
        CHECK(back.size() == 2 && back[0] == EchoKind::Rethilgore && back[1] == EchoKind::Odo);
        CHECK(NightEndsReturns(0x7).empty());
        // At most three alive after it.
        CHECK(NightEndsReturns(Bit(EchoKind::Odo)).size() + 1 == kEchoKinds);
    }

    void TestFade()
    {
        // Normal: 12 s, but a move under way lands first; heroic: never.
        CHECK(!EchoFades(11999, kEchoLifeMs(false), false));
        CHECK(EchoFades(12000, kEchoLifeMs(false), false));
        CHECK(!EchoFades(12500, kEchoLifeMs(false), true));
        CHECK(EchoFades(12600, kEchoLifeMs(false), false));
        CHECK(!EchoFades(600000, kEchoLifeMs(true), false));
        CHECK(kEchoesTogether(true) && !kEchoesTogether(false));
    }

    // The echoes burst into the hall: inside the arena, out of the alcove, clear of the table holes, apart.
    void TestEchoSpawns()
    {
        Arena const hall = SilverlaineArena();
        std::array<Vec2, 5> const holes{ { { -255.2f, 2286.9f }, { -243.8f, 2287.5f }, { -238.1f, 2293.1f },
            { -238.1f, 2285.6f }, { -235.4f, 2279.0f } } };
        std::vector<Vec2> spawns;
        for (EchoKind const kind : kKillOrder)
        {
            Vec2 const p = EchoSpawn(kind);
            spawns.push_back(p);
            CHECK(hall.Contains(p, kSilverlaineSpawn.z));
            float const fromHim = DungeonKit::Distance(p, kSilverlaineSpawn.XY());
            CHECK(fromHim >= 12.f && fromHim <= 30.f);
            for (Vec2 const& h : holes)
                CHECK(DungeonKit::Distance(p, h) >= 3.f);
        }
        for (std::size_t i = 0; i < spawns.size(); ++i)
            for (std::size_t j = i + 1; j < spawns.size(); ++j)
                CHECK(DungeonKit::Distance(spawns[i], spawns[j]) >= 6.f);
        // The report's conversion (x = -275.3 - 0.367u + 0.930v, y = 2297.4 - 0.930u - 0.367v).
        Vec2 const odo = EchoSpawn(EchoKind::Odo);
        CHECK(Near(odo.x, -275.3f + 0.930f * 28.f, 0.1f) && Near(odo.y, 2297.4f - 0.367f * 28.f, 0.1f));
    }

    // BS3: fragment points 3-6 yd from the drained player, inside the hall, 2 yd apart; six per echo at most (18%).
    void TestEchoFragments()
    {
        Arena const hall = SilverlaineArena();
        Vec2 const middle = ReportPoint(kSilverlaineSpawn.XY(), kKeepUp, 0.f, 30.f);
        std::vector<Vec2> const points = EchoFragmentPoints(middle, kSilverlaineSpawn.z, hall);
        CHECK(points.size() == kEchoFragmentBearings);
        for (Vec2 const& p : points)
        {
            float const d = DungeonKit::Distance(p, middle);
            CHECK(d >= 3.f && d <= 6.f);
            CHECK(hall.Contains(p, kSilverlaineSpawn.z));
        }
        for (std::size_t i = 0; i < points.size(); ++i)
            for (std::size_t j = i + 1; j < points.size(); ++j)
                CHECK(DungeonKit::Distance(points[i], points[j]) >= kEchoFragmentMinGap);

        // Against a wall (the hall's west edge, u -11.5): only the points inside remain.
        Vec2 const atWall = ReportPoint(kSilverlaineSpawn.XY(), kKeepUp, -11.5f, 30.f);
        std::vector<Vec2> const walled = EchoFragmentPoints(atWall, kSilverlaineSpawn.z, hall);
        CHECK(!walled.empty() && walled.size() < kEchoFragmentBearings);
        for (Vec2 const& p : walled)
            CHECK(hall.Contains(p, kSilverlaineSpawn.z));
        // Off the floor's height band: none.
        CHECK(EchoFragmentPoints(middle, 90.f, hall).empty());

        // The free-point pick (Rethilgore's) skips taken points and runs out.
        auto first = [](std::uint32_t) { return 0u; };
        std::vector<Vec2> occupied;
        std::size_t picked = 0;
        while (std::optional<std::size_t> const pick = Rethilgore::PickFreePoint(points, occupied,
            kEchoFragmentMinGap, first))
        {
            for (Vec2 const& o : occupied)
                CHECK(DungeonKit::Distance(points[*pick], o) >= kEchoFragmentMinGap);
            occupied.push_back(points[*pick]);
            if (++picked > points.size())
                break;
        }
        CHECK(picked == points.size());

        // Six per echo: the normal 12 s life's six 2 s ticks; the same cap on heroic.
        std::uint32_t fragments = 0;
        for (std::uint32_t tick = 1; tick <= 20; ++tick)
            if (EchoFragmentOnTick(fragments))
                ++fragments;
        CHECK(fragments == 6);
        CHECK(kEchoLifeMs(false) / kEchoDrainTickMs == kEchoFragmentsPerEcho);
        // User ruling 2026-11-07: the drain lasts 12 s on both difficulties (six ticks), heroic included.
        std::uint32_t ticks = 0;
        while (ticks < 100 && EchoDrainGoesOn(ticks))
            ++ticks;
        CHECK(ticks == kEchoDrainTicks);
        CHECK(kEchoDrainTicks * kEchoDrainTickMs == 12000);
        CHECK(kEchoDrainTicks * kEchoDrainTickMs == kEchoLifeMs(false));
        CHECK(kEchoLifeMs(true) == 0);                      // the heroic echo itself still lives until killed
        CHECK(Near(EchoFeastCapPct(), 18.f));
        CHECK(Near(kEchoFragmentHealPct, 5.f) && Near(kEchoFeastPct, 3.f));
        CHECK(kEchoFragmentLifeMs == 6000 && Near(kEchoFragmentRadius, 1.5f));
        // The drain's tick is Rethilgore's 5% (normal 65, heroic 206).
        CHECK(Near(Rethilgore::kDrainPct, 5.f) && kEchoDrainTickMs == Rethilgore::kDrainTickMs);
        CHECK(Near(RefPct(Rethilgore::kDrainPct, false), 65.f) && Near(RefPct(Rethilgore::kDrainPct, true), 206.f));
    }

    // BS4: Razorclaw's normal hook (one line, 35%, no bleed) on both difficulties, the echo's own tag; three on normal
    // inside the 12 s life (0, 5, 10 s, the last landing at 12 s), no cap on heroic.
    void TestEchoHook()
    {
        Razorclaw::HookTuning const t = EchoHook();
        CHECK(t.lines == 1);
        CHECK(Near(t.pct, 35.f));
        CHECK(Near(t.bleedPct, 0.f));
        CHECK(t.tag == kTagEchoHook);
        CHECK(t.warnMs == 2000 && Near(t.widthYd, 3.f) && Near(t.overrunYd, 5.f) && Near(t.excludeYd, 4.f));
        CHECK(Near(RefPct(t.pct, false), 455.f) && Near(RefPct(t.pct, true), 1442.f));

        CHECK(EchoMayHook(false, 0) && EchoMayHook(false, 2) && !EchoMayHook(false, 3));
        CHECK(EchoMayHook(true, 3) && EchoMayHook(true, 100));

        std::uint32_t thrown = 0;
        std::uint32_t lastLands = 0;
        for (std::uint32_t at = 0; at < 60000; at += kEchoHookEveryMs)
        {
            if (!EchoMayHook(false, thrown))
                break;
            ++thrown;
            lastLands = at + t.warnMs;
        }
        CHECK(thrown == 3);
        CHECK(lastLands == kEchoLifeMs(false));
    }

    // BS5: S5's kEchoHunt (80%, 2 s howl, 8 s, 3 yd); the Maul 1.5 s stun + 20% in three 0.5 s ticks.
    void TestEchoHunt()
    {
        CHECK(Near(kEchoHunt.ratePct, 80.f));
        CHECK(kEchoHunt.warnMs == 2000 && kEchoHunt.chaseMs == 8000 && Near(kEchoHunt.radius, 3.f));
        CHECK(Near(SfkHunt::GainYd(kEchoHunt), 11.2f, 0.05f));     // navmesh report: 11.2 yd
        CHECK(SfkHunt::TotalMs(kEchoHunt) <= kEchoLifeMs(false));   // the howl and chase fit the normal life
        CHECK(SfkHunt::MaulTicks(kEchoMaulMs, kEchoMaulTickMs) == 3);
        float const tick = SfkHunt::MaulTickPct(kEchoMaulPct, kEchoMaulMs, kEchoMaulTickMs);
        CHECK(Near(tick * 3.f, 20.f));
        CHECK(Near(RefPct(kEchoMaulPct, false), 260.f) && Near(RefPct(kEchoMaulPct, true), 824.f));
    }

    // BS6: 3% per 2 s for 12 s (18%), healing -50%, a 4 yd spread every 2 s, 6 s then 20 s.
    void TestAccursedVeil()
    {
        CHECK(kVeilFirstMs == 6000 && kVeilEveryMs == 20000 && kVeilCastMs == 1500);
        CHECK(kVeilDurationMs == 12000 && kVeilTickMs == 2000 && kVeilPulseMs == 2000 && kVeilWarnMs == 2000);
        CHECK(Near(kVeilTickPct, 3.f) && Near(VeilTotalPct(), 18.f));
        CHECK(Near(kVeilHealingTakenPct, -50.f));
        CHECK(Near(kVeilSpreadYd, 4.f));
        CHECK(Near(RefPct(kVeilTickPct, false), 39.f) && Near(RefPct(kVeilTickPct, true), 123.6f));
        // A cursed player keeps its own 12 s; a pulse copies onto uncursed players only.
        CHECK(VeilCatches(true, false));
        CHECK(!VeilCatches(true, true));
        CHECK(!VeilCatches(false, false));
        // The Veil (6 s, 26 s, ...) and the echoes (15 s, 40 s, ...) never start on the same second.
        for (std::uint32_t veil = kVeilFirstMs; veil < 180000; veil += kVeilEveryMs)
            for (std::uint32_t echo = kEchoFirstMs; echo < 180000; echo += kEchoEveryMs)
                CHECK(veil != echo);
    }
}

int main()
{
    TestSliceAndArena();
    TestEchoKinds();
    TestEchoClockTimers();
    TestEchoClockNormalWaits();
    TestEchoClockHeroic();
    TestNormalFightTimeline();
    TestNightEnds();
    TestFade();
    TestEchoSpawns();
    TestEchoFragments();
    TestEchoHook();
    TestEchoHunt();
    TestAccursedVeil();
    return Report("sfk_silverlaine_test");
}
