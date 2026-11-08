// Host tests for RavenianLogic.h (S8: The Ravenian (10507) and Master Corvane (300542)): the ids, the build spec
// numbers, the order rotation (never the same twice), the order outcomes (Unbound, Driven), the transition, the filler
// rule, Bereaved and Driven scaling, the timeline, Corvane's seat and landing (the user's spot, at least 15 yd from the
// Ravenian, both inside his arena), Trample's lanes ending at the vault's walls, the solo lesson's plan, and the pair's
// lives (user ruling 1: the collapse at 1 HP, the real kill with Corvane, the reset on a wipe).
#include "DungeonKitLogic.h"
#include "RavenianLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <set>

using namespace ScholomanceRework;
using namespace ScholoRavenian;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A small deterministic generator (xorshift) for the rotation runs.
    struct Rng
    {
        std::uint32_t s = 0x2545F491u;

        std::uint32_t operator()()
        {
            s ^= s << 13;
            s ^= s >> 17;
            s ^= s << 5;
            return s;
        }
    };

    // On the vault's frame (the polygon of VaultWalls(), not its fallback circle).
    bool InVault(Vec2 p, float z)
    {
        return VaultWalls().regions.front().Contains(p, z);
    }

    DungeonKit::LinePath Lane(Vec2 from, Vec2 through, float z = 75.2f)
    {
        Arena const walls = VaultWalls();
        return DungeonKit::LineStrikePath(from, through, kTrampleOverrun, 0.f, &walls, z);
    }
}

int main()
{
    // ---- ids and slice --------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206270 && kSpellSlice.last == 206289);
    for (std::uint32_t id = SPELL_RV_LEASH; id <= SPELL_RV_SUNDERING_CLEAVE; ++id)
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsPolkelt.Contains(id));
        CHECK(!kSpellsAlexei.Contains(id));
    }
    CHECK(NPC_SC_MASTER_CORVANE == 300542 && NPC_SC_EXAMINER_RAVENIAN == 300551 && NPC_SC_EXAMINER_CORVANE == 300552);
    CHECK(kExaminerRavenianHealth == 60000 && kExaminerCorvaneHealth == 20000);
    CHECK(!HeroicValues(false, false) && HeroicValues(true, false) && HeroicValues(false, true));

    // ---- the orders: spells, yells, tags --------------------------------------------------------------------------
    std::set<std::uint32_t> casts;
    std::set<std::uint32_t> hits;
    for (std::size_t i = 0; i < kOrderCount; ++i)
    {
        Order const o = Order(i);
        casts.insert(OrderCastSpell(o));
        hits.insert(OrderHitSpell(o));
        CHECK(OrderOfCast(OrderCastSpell(o)) == o);
        CHECK(!OrderOfCast(OrderHitSpell(o)));
        CHECK(OrderTag(o) == std::uint32_t(i) + 1);
    }
    CHECK(casts.size() == 3 && hits.size() == 3);
    CHECK(!OrderOfCast(SPELL_RV_MEND) && !OrderOfCast(SPELL_RV_SHADOW_BOLT));
    CHECK(OrderYell(Order::Trample) == YELL_CORVANE_TRAMPLE);
    CHECK(OrderYell(Order::Sweep) == YELL_CORVANE_SWEEP);
    CHECK(OrderYell(Order::Smash) == YELL_CORVANE_SMASH);
    CHECK(OrderTag(Order::Trample) == TAG_TRAMPLE && OrderTag(Order::Sweep) == TAG_SWEEP
        && OrderTag(Order::Smash) == TAG_SMASH);

    // ---- build spec numbers (SC 2193-2259) -------------------------------------------------------------------------
    CHECK(kOrderCastMs == 2000 && kOrderMarkerMs == 2000);
    CHECK(OrderPct(Order::Trample, false) == 35.f && OrderPct(Order::Trample, true) == 50.f);
    CHECK(OrderPct(Order::Sweep, false) == 45.f && OrderPct(Order::Sweep, true) == 60.f);
    CHECK(OrderPct(Order::Smash, false) == 30.f && OrderPct(Order::Smash, true) == 40.f);
    CHECK(kTrampleWidth == 4.f && kSweepAngle == 120.f && kSweepLength == 12.f && kSmashRadius == 6.f);
    CHECK(kLeashOrderFirstMs == 8000 && kLeashOrderEveryMs == 12000 && kHandOrderEveryMs == 15000);
    CHECK(!kPairedOrders(false) && kPairedOrders(true));
    CHECK(kTransitionHealthPct == 50.f);
    CHECK(kTransitionHealPct(false) == 10.f && kTransitionHealPct(true) == 15.f);
    CHECK(kTransitionFallbackMs > kTransitionCastMs);
    CHECK(kUnboundPct == 8.f && kUnboundStandMs == 2000);
    CHECK(!kDriven(false) && kDriven(true));
    CHECK(kMendCastMs == 3000 && kMendFirstMs == 10000 && kMendEveryMs == 20000);
    CHECK(kMendPct(false) == 6.f && kMendPct(true) == 10.f);
    CHECK(kShadowBoltPct(false) == 15.f && kShadowBoltPct(true) == 20.f);
    CHECK(kBereavedEveryMs == 5000 && kUnleashedOrderEveryMs == 10000 && kStackDamagePct == 10.f);
    // Paced for heroic's one 10 s interrupt: a heal every 20 s or slower (SC "Interrupt load").
    CHECK(kMendEveryMs >= 20000);

    // ---- RV4: the rotation is never the same twice ----------------------------------------------------------------
    {
        Rng rng;
        std::optional<Order> last;
        std::array<int, kOrderCount> seen{};
        for (int i = 0; i < 3000; ++i)
        {
            Order const o = NextOrder(last, rng());
            if (last)
                CHECK(o != *last);
            ++seen[std::size_t(o)];
            last = o;
        }
        for (int n : seen)
            CHECK(n > 800);         // all three come up, about evenly
        // Every roll from every last order: one of the other two, and both reachable.
        for (std::size_t l = 0; l < kOrderCount; ++l)
        {
            std::set<int> got;
            for (std::uint32_t roll = 0; roll < 8; ++roll)
            {
                Order const o = NextOrder(Order(l), roll);
                CHECK(o != Order(l));
                got.insert(int(o));
            }
            CHECK(got.size() == 2);
        }
        std::set<int> first;
        for (std::uint32_t roll = 0; roll < 9; ++roll)
            first.insert(int(NextOrder(std::nullopt, roll)));
        CHECK(first.size() == 3);
        // A heroic pair: its second order is never its first.
        for (std::uint32_t a = 0; a < 6; ++a)
            for (std::uint32_t b = 0; b < 6; ++b)
            {
                Order const one = NextOrder(std::nullopt, a);
                CHECK(NextOrder(one, b) != one);
            }
    }

    // ---- RV5-RV7: the transition and the order outcomes -----------------------------------------------------------
    CHECK(!TransitionDue(Stage::Leash, 50.1f));
    CHECK(TransitionDue(Stage::Leash, 50.f));
    CHECK(TransitionDue(Stage::Leash, 12.f));
    CHECK(!TransitionDue(Stage::Transition, 40.f) && !TransitionDue(Stage::Hand, 40.f));
    CHECK(!TransitionDue(Stage::Bereaved, 40.f));
    // Phase 1: nothing stops an order (he is unselectable); a lost cast is just lost; no Driven yet.
    CHECK(OrderResult(Stage::Leash, true, false) == OrderOutcome::Performed);
    CHECK(OrderResult(Stage::Leash, true, true) == OrderOutcome::Performed);
    CHECK(OrderResult(Stage::Leash, false, true) == OrderOutcome::Lost);
    // Phase 2: a kick unbinds him; an order nobody kicks lands, and on heroic it drives him.
    CHECK(OrderResult(Stage::Hand, false, false) == OrderOutcome::Unbound);
    CHECK(OrderResult(Stage::Hand, false, true) == OrderOutcome::Unbound);
    CHECK(OrderResult(Stage::Hand, true, false) == OrderOutcome::Performed);
    CHECK(OrderResult(Stage::Hand, true, true) == OrderOutcome::PerformedDriven);
    CHECK(OrderResult(Stage::Bereaved, true, true) == OrderOutcome::Lost);

    // ---- RV7 / RV10: the stacks scale every hit by 10% each, uncapped ---------------------------------------------
    CHECK(Near(DamageScale(0), 1.f));
    CHECK(Near(DamageScale(1), 1.1f));
    CHECK(Near(DamageScale(12), 2.2f));
    CHECK(Near(DamageScale(100), 11.f));
    // Driven and Bereaved multiply, as the engine does with the two auras on his melee (R-B RV-N2).
    CHECK(Near(StackedDamageScale(0, 0), 1.f));
    CHECK(Near(StackedDamageScale(3, 0), 1.3f));
    CHECK(Near(StackedDamageScale(0, 6), 1.6f));
    CHECK(Near(StackedDamageScale(3, 6), 2.08f));      // 1.3 x 1.6, not the additive 1.9
    CHECK(Near(StackedDamageScale(3, 6), StackedDamageScale(6, 3)));

    // ---- user ruling 1: the Ravenian collapses at 1 HP while Corvane stands, dies for real with him -----------------
    {
        // A lethal hit while Corvane stands: 1 HP left, the collapse.
        RavenianHit h = RavenianDamage(Pair::Both, 5000, 7000, true);
        CHECK(h.collapse && h.damage == 4999);
        h = RavenianDamage(Pair::Both, 5000, 5000, true);
        CHECK(h.collapse && h.damage == 4999);
        h = RavenianDamage(Pair::Both, 1, 300, true);
        CHECK(h.collapse && h.damage == 0);
        // Not lethal: it lands whole.
        h = RavenianDamage(Pair::Both, 5000, 4999, true);
        CHECK(!h.collapse && h.damage == 4999);
        // Corvane already dead (RV10, the Ravenian unleashed): the Ravenian dies normally.
        h = RavenianDamage(Pair::Both, 5000, 7000, false);
        CHECK(!h.collapse && h.damage == 7000);
        // Collapsed: nothing lands, whatever Corvane does.
        h = RavenianDamage(Pair::Collapsed, 1, 7000, true);
        CHECK(!h.collapse && h.damage == 0);
        h = RavenianDamage(Pair::Collapsed, 1, 7000, false);
        CHECK(!h.collapse && h.damage == 0);
        // Over (dead): untouched (the engine's own rules).
        h = RavenianDamage(Pair::Over, 0, 10, true);
        CHECK(!h.collapse && h.damage == 10);

        // The collapsed tick: Corvane's death kills him (even a corpse not yet reported, even a wipe the same tick),
        // a wipe or Corvane gone without a death resets both, else he lies still.
        CHECK(NextCollapsedStep(false, false, true) == CollapsedStep::Hold);
        CHECK(NextCollapsedStep(true, false, true) == CollapsedStep::Kill);
        CHECK(NextCollapsedStep(true, true, true) == CollapsedStep::Kill);
        CHECK(NextCollapsedStep(true, false, false) == CollapsedStep::Kill);
        CHECK(NextCollapsedStep(false, true, true) == CollapsedStep::Reset);
        CHECK(NextCollapsedStep(false, false, false) == CollapsedStep::Reset);

        // A whole fight in the two orders: the pair's state through the hits and Corvane's death.
        struct Sim
        {
            Pair pair = Pair::Both;
            std::uint32_t ravenian = 160000;
            bool corvaneUp = true;
            bool corvaneDied = false;
            bool wipe = false;
            bool ravenianDead = false;

            void HitRavenian(std::uint32_t damage)
            {
                RavenianHit const h = RavenianDamage(pair, ravenian, damage, corvaneUp);
                if (h.collapse)
                    pair = Pair::Collapsed;
                ravenian -= std::min(ravenian, h.damage);
                if (!ravenian)
                {
                    ravenianDead = true;
                    pair = Pair::Over;
                }
            }

            void Tick()
            {
                if (pair != Pair::Collapsed)
                    return;
                switch (NextCollapsedStep(corvaneDied, wipe, corvaneUp || corvaneDied))
                {
                    case CollapsedStep::Hold:
                        break;
                    case CollapsedStep::Kill:
                        ravenian = 0;
                        ravenianDead = true;
                        pair = Pair::Over;
                        break;
                    case CollapsedStep::Reset:
                        pair = Pair::Both;
                        ravenian = 160000;
                        corvaneUp = true;       // a fresh Corvane on his seat
                        wipe = false;
                        break;
                }
            }
        };

        // The Ravenian first: he collapses, stays at 1 HP under any damage, and dies only with Corvane.
        Sim a;
        a.HitRavenian(159000);
        a.HitRavenian(5000);
        CHECK(a.pair == Pair::Collapsed && a.ravenian == 1 && !a.ravenianDead);
        a.HitRavenian(100000);
        a.Tick();
        CHECK(a.pair == Pair::Collapsed && a.ravenian == 1);
        a.corvaneUp = false;
        a.corvaneDied = true;
        a.Tick();
        CHECK(a.ravenianDead && a.pair == Pair::Over);

        // The Ravenian first, then a wipe on Corvane alone: both reset, the Ravenian whole, nothing dead.
        Sim b;
        b.HitRavenian(170000);
        CHECK(b.pair == Pair::Collapsed && b.ravenian == 1);
        b.wipe = true;
        b.Tick();
        CHECK(b.pair == Pair::Both && b.ravenian == 160000 && !b.ravenianDead);

        // Corvane gone without a death (a GM despawn, the examiner's gauntlet): the same reset.
        Sim c;
        c.HitRavenian(170000);
        c.corvaneUp = false;
        c.Tick();
        CHECK(c.pair == Pair::Both && !c.ravenianDead);

        // Corvane first (RV10): the Ravenian is never clamped and dies to the next lethal hit.
        Sim d;
        d.corvaneUp = false;
        d.corvaneDied = true;
        d.HitRavenian(170000);
        CHECK(d.ravenianDead && d.pair == Pair::Over);
    }

    // ---- RV9: the bolt only between orders and heals --------------------------------------------------------------
    CHECK(BoltFits(1000, 1000 + kShadowBoltCastMs + kShadowBoltMarginMs, kNever));
    CHECK(!BoltFits(1000, 1000 + kShadowBoltCastMs, kNever));
    CHECK(!BoltFits(1000, kNever, 2000));
    CHECK(BoltFits(0, kNever, kNever));

    // ---- the timeline: never paused, a beat waits while due -------------------------------------------------------
    {
        Timeline t;
        t.Start(5000);
        CHECK(!t.Due(Beat::Order) && !t.Due(Beat::Mend) && !t.Due(Beat::Bolt) && !t.Due(Beat::Bereaved));
        t.Advance(5000);
        CHECK(t.Due(Beat::Cleave) && !t.Due(Beat::Order) && t.Due(Beat::Leash));
        t.Advance(3000);
        CHECK(t.Due(Beat::Order));
        t.Advance(1000);                // a beat that came due while Corvane cast stays due
        CHECK(t.Due(Beat::Order));
        t.Set(Beat::Order, kLeashOrderEveryMs);
        CHECK(!t.Due(Beat::Order) && t.At(Beat::Order) == 9000 + kLeashOrderEveryMs);
        t.Land();
        CHECK(t.At(Beat::Order) == t.now + kHandOrderFirstMs && t.At(Beat::Mend) == t.now + kMendFirstMs);
        CHECK(t.Due(Beat::Bolt));
        t.Unleash();
        CHECK(!t.Due(Beat::Mend) && !t.Due(Beat::Bolt) && t.At(Beat::Mend) == kNever);
        CHECK(t.At(Beat::Order) == t.now + kUnleashedOrderFirstMs && t.At(Beat::Bereaved) == t.now + kBereavedEveryMs);
        t.Retry(Beat::Cleave);
        CHECK(t.At(Beat::Cleave) == t.now + kRetryMs);
        t.Stop(Beat::Cleave);
        t.Advance(1000000);
        CHECK(!t.Due(Beat::Cleave));
    }

    // ---- Corvane's seat (user ruling 2026-11-08) and his landing --------------------------------------------------
    {
        // The seat is the user's spot right behind the Ravenian, at the vault's west end, inside his arena: nothing
        // leashes or evades Corvane there.
        CHECK(kCorvaneSeat.x == kRavenianUserSpot.x && kCorvaneSeat.y == kRavenianUserSpot.y);
        CHECK(RavenianArena().Contains(kCorvaneSeat.XY(), kCorvaneSeat.z));
        CHECK(kCorvaneSeat.x < kRavenianSpawn.x);                           // behind him (he faces east, +x)
        CHECK(DungeonKit::Distance(kCorvaneSeat.XY(), kRavenianSpawn.XY()) < 13.f);
        // The landing: the user's (128, -1), at least 15 yd from the Ravenian's spawn.
        CHECK(PickLanding(kRavenianSpawn.XY()) == 0);
        CHECK(Near(kCorvaneLandings[0].x, 128.f) && Near(kCorvaneLandings[0].y, -1.f));
        CHECK(DungeonKit::Distance(kCorvaneLandings[0].XY(), kRavenianSpawn.XY()) >= kLandingMinYd);
        CHECK(DungeonKit::Distance(kCorvaneLandings[0].XY(), kRavenianSpawn.XY()) > 24.f);
        // Tanked on (128, -1) itself: none of the three is 15 yd off, the farthest (140, -1) wins.
        CHECK(PickLanding({ 128.f, -1.f }) == 1);
        // Tanked at (133, -1): 5, 7 and 11 yd: the farthest, (122, 0).
        CHECK(PickLanding({ 133.f, -1.f }) == 2);
        // Tanked at the gate end or the seat end: (128, -1) is 15 yd off already.
        CHECK(PickLanding({ 145.f, 0.f }) == 0);
        CHECK(PickLanding({ 110.f, 0.f }) == 0);
        // Every landing lies in his arena.
        for (Point3 const& p : kCorvaneLandings)
            CHECK(RavenianArena().Contains(p.XY(), p.z));
    }

    // ---- Trample: lanes end at the vault's walls and stay on the frame (KS note) -----------------------------------
    {
        float const z = 75.2f;
        // From his spawn through a player in the band: the line runs east to the gate-end wall (x 150), 0.5 yd short.
        DungeonKit::LinePath const east = Lane(kRavenianSpawn.XY(), { 125.f, -1.f });
        CHECK(east.clipped);
        CHECK(east.end.x <= 150.f && east.end.x > 148.f);
        CHECK(InVault(east.end, z));
        // Through a player in the north hall (y 12): the line reaches past them and stops in the hall.
        DungeonKit::LinePath const hall = Lane({ 120.f, 0.f }, { 135.f, 12.f });
        CHECK(hall.length > DungeonKit::Distance({ 120.f, 0.f }, { 135.f, 12.f }));
        CHECK(InVault(hall.end, z));
        // West, toward Corvane's seat: stops at the west wall (x 92), never past the frame.
        DungeonKit::LinePath const west = Lane({ 110.f, -1.f }, { 100.f, -1.f });
        CHECK(west.end.x >= 92.f && west.end.x < 93.f);
        // Across the band: stops at the side wall, inside the arena circle too.
        DungeonKit::LinePath const across = Lane({ 110.f, -1.f }, { 110.f, 4.f });
        CHECK(across.end.y <= 8.f && across.end.y > 7.f);
        CHECK(RavenianArena().Contains(across.end, z));
        // Every lane from anywhere in the band, at any bearing, ends inside the frame. The Ravenian never runs the
        // lane (it is a marker, not a charge), so his arena circle does not bind it: the north hall's far corners lie
        // 0.8 yd past the circle (32.8 yd from its center), which is where the longest lanes may end.
        for (float x = 94.f; x <= 148.f; x += 6.f)
            for (float y = -10.f; y <= 6.f; y += 4.f)
                for (int k = 0; k < 16; ++k)
                {
                    float const bearing = float(k) * 0.3927f;
                    DungeonKit::LinePath const p = Lane({ x, y }, DungeonKit::Advance({ x, y }, bearing, 3.f));
                    CHECK(InVault(p.end, z));
                    CHECK(DungeonKit::Distance(p.end, { 122.f, -1.f }) <= 33.f);
                }
    }

    // ---- the solo lesson ------------------------------------------------------------------------------------------
    {
        CHECK(kLessonOrders == 3);
        CHECK(kLessonCallMs == kOrderCastMs && kLessonMarkerMs == kOrderMarkerMs);
        // Each order is called after the last one landed, and the last lands inside the 15 s.
        for (std::size_t i = 1; i < kLessonOrders; ++i)
            CHECK(kLessonCallAtMs[i] >= kLessonCallAtMs[i - 1] + kLessonCallMs + kLessonMarkerMs);
        CHECK(kLessonCallAtMs.back() + kLessonCallMs + kLessonMarkerMs <= kLessonMs);
        CHECK(LessonPct(false) == 15.f && LessonPct(true) == 25.f);
        // The source stands close enough for the Sweep to reach the student.
        CHECK(kLessonSourceYd < kSweepLength);
        // Every roll gives a permutation of the three orders (never the same twice).
        std::set<int> firsts;
        for (std::uint32_t a = 0; a < 6; ++a)
            for (std::uint32_t b = 0; b < 6; ++b)
            {
                std::array<Order, kLessonOrders> const plan = LessonOrders(a, b);
                std::set<int> distinct{ int(plan[0]), int(plan[1]), int(plan[2]) };
                CHECK(distinct.size() == 3);
                CHECK(plan[0] != plan[1] && plan[1] != plan[2]);
                firsts.insert(int(plan[0]));
            }
        CHECK(firsts.size() == 3);
    }

    // ---- the arena (KS stub) --------------------------------------------------------------------------------------
    CHECK(RavenianArena().Contains(kRavenianSpawn.XY(), kRavenianSpawn.z));
    CHECK(ArenaFor(BOSS_RAVENIAN).Contains(kRavenianSpawn.XY(), kRavenianSpawn.z));
    CHECK(RavenianArena().Contains(kClassroomLandings[std::size_t(Classroom::RavenianVault)].XY(),
        kClassroomLandings[std::size_t(Classroom::RavenianVault)].z));

    return Report("scholo_ravenian_test");
}
