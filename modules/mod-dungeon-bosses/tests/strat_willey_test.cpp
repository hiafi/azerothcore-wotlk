// Host tests for WilleyLogic.h (S5: Cannon Master Willey): the slice, the arena, the ranks' clock and beat, the
// halves and the guns on the hall frame, the Barrage's orders and call, the cannon shot.
#include "WilleyLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string>

using namespace StratholmeRework;
using namespace StratWilley;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { SPELL_WY_AIM, SPELL_WY_TAKING_AIM, SPELL_WY_FIRE, SPELL_WY_HOLDING_CANNONBALL,
                 SPELL_WY_CANNON_SHOT, SPELL_WY_SHAKEN, SPELL_WY_CANNON_FIRE, SPELL_WY_BARRAGE, SPELL_WY_BLAST_LOOK })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_WY_AIM == 206500u);
        CHECK(SPELL_WY_BLAST_LOOK == 206508u);
        CHECK(kSpellSlice.Contains(SPELL_WY_MERCY_GLOW) && kSpellSlice.Contains(SPELL_WY_ZEAL_GLOW));
        CHECK(SPELL_WY_ZEAL_GLOW == 206510u);
        // The glow stalker sits in the wave 2 creature slice, past every named Stratholme creature.
        CHECK(kCreaturesWave2.Contains(kNpcGunGlow));
        CHECK(kNpcGunGlow > NPC_ST_SWARM);
        // The boss spawns inside his arena.
        CHECK(WilleyArena().Contains(kWilleySpawn.XY(), kWilleySpawn.z));
        CHECK(ArenaFor(BOSS_WILLEY).Contains(kWilleySpawn.XY(), kWilleySpawn.z));
    }

    void TestDrill()
    {
        // 3 + 3 fit under 6, a third rank waits; heroic 4 + 4 under 8.
        CHECK(CanForm(0, kRankSize(false), kRiflemanCap(false)));
        CHECK(CanForm(3, kRankSize(false), kRiflemanCap(false)));
        CHECK(!CanForm(4, kRankSize(false), kRiflemanCap(false)));
        CHECK(!CanForm(6, kRankSize(false), kRiflemanCap(false)));
        CHECK(CanForm(4, kRankSize(true), kRiflemanCap(true)));
        CHECK(!CanForm(5, kRankSize(true), kRiflemanCap(true)));
        // The rank's spots match its size.
        CHECK(RankSpotCount(false) == kRankSize(false));
        CHECK(RankSpotCount(true) == kRankSize(true));

        DrillClock clock;
        CHECK(!clock.Due(5999));
        CHECK(clock.Due(6000));
        clock.Formed(6000);
        CHECK(!clock.Due(25999));
        CHECK(clock.Due(26000));
        // A rank held by the cap comes late; the next is 20 s after it came.
        CHECK(clock.Due(31000));
        clock.Formed(31000);
        CHECK(clock.DueMs() == 51000u);
        clock.Reset();
        CHECK(clock.DueMs() == kRankCadence.first);

        // Every rank spot and both march-in ends lie in the hall's arena or its yard opening; the spots are inside
        // the hall frame at X 52.
        for (bool heroic : { false, true })
            for (std::size_t i = 0; i < RankSpotCount(heroic); ++i)
            {
                Point3 const p = RankSpot(heroic, i);
                Vec2 const f = DungeonKit::ToFrame(kWilleyHall, p.XY());
                CHECK(Near(f.x, 52.f, 0.6f));
                CHECK(f.y > 0.f && f.y < kWilleyHall.sizeY);
                CHECK(WilleyArena().Contains(p.XY(), p.z));
            }
        Vec2 const a = MarchStart(0, 3);
        Vec2 const b = MarchStart(2, 3);
        CHECK(Near(a.x, kYardOpeningA.x) && Near(a.y, kYardOpeningA.y));
        CHECK(Near(b.x, kYardOpeningB.x) && Near(b.y, kYardOpeningB.y));
        // The opening lies on the hall's east side (frame Y about 20), toward its far end.
        Vec2 const mid = DungeonKit::ToFrame(kWilleyHall, MarchStart(1, 3));
        CHECK(mid.x > 40.f && mid.x < 58.f);
        CHECK(mid.y > 15.f);
    }

    void TestRankCycle()
    {
        // Normal: summoned at 6 s, formed at 8.5 s, Aim at 14.5 s, Fire at 17.5 s, Aim again at 25.5 s.
        RankCycle cycle;
        cycle.Summoned(6000, false);
        CHECK(cycle.Update(14499) == RankStep::None);
        CHECK(cycle.Update(14500) == RankStep::Aim);
        CHECK(cycle.Aiming());
        CHECK(cycle.Update(17499) == RankStep::None);
        CHECK(cycle.Update(17500) == RankStep::Fire);
        CHECK(!cycle.Aiming());
        CHECK(cycle.Update(25499) == RankStep::None);
        CHECK(cycle.Update(25500) == RankStep::Aim);
        CHECK(cycle.Update(28500) == RankStep::Fire);
        // An 11 s volley cycle on normal: 6 riflemen x 15% every 11 s when nobody kills them (ST failing path).
        CHECK(kFireAfterAimMs(false) + kReaimAfterFireMs == 11000u);

        // Heroic: Aim 4 s after forming, Fire 2 s after Aim.
        RankCycle hc;
        hc.Summoned(0, true);
        CHECK(hc.Update(kMarchMs + 3999) == RankStep::None);
        CHECK(hc.Update(kMarchMs + 4000) == RankStep::Aim);
        CHECK(hc.Update(kMarchMs + 5999) == RankStep::None);
        CHECK(hc.Update(kMarchMs + 6000) == RankStep::Fire);
        CHECK(hc.NextMs() == kMarchMs + 6000 + kReaimAfterFireMs);
        CHECK(kVolleyPct(false) == 15.f && kVolleyPct(true) == 20.f);
    }

    void TestHalvesAndGuns()
    {
        // Mercy's half is the east one (Y 10..20), Zeal's the west one (Y 0..10).
        CHECK(Near(HalfCenterY(Gun::Mercy), 15.f));
        CHECK(Near(HalfCenterY(Gun::Zeal), 5.f));
        CHECK(Near(kHallLength, 58.f));
        CHECK(Near(kHalfWidth, 10.f));
        // The stock cannons' spots: 176216 (Mercy) at frame (12.0, 14.8), 176217 (Zeal) at (11.8, 5.3).
        Vec2 const m = DungeonKit::ToFrame(kWilleyHall, GunAt(Gun::Mercy).XY());
        Vec2 const z = DungeonKit::ToFrame(kWilleyHall, GunAt(Gun::Zeal).XY());
        CHECK(Near(m.x, 12.0f, 0.2f) && Near(m.y, 14.8f, 0.2f));
        CHECK(Near(z.x, 11.8f, 0.2f) && Near(z.y, 5.3f, 0.2f));
        CHECK(HalfOf(GunAt(Gun::Mercy).XY()) == Gun::Mercy);
        CHECK(HalfOf(GunAt(Gun::Zeal).XY()) == Gun::Zeal);
        // He stands on the split line (frame Y 10): both lanes reach him.
        Vec2 const w = DungeonKit::ToFrame(kWilleyHall, kWilleySpawn.XY());
        CHECK(Near(w.y, 10.f, 0.2f));
        // Each lane starts at the back wall in its half's middle and its far end is still in the frame.
        for (Gun gun : { Gun::Mercy, Gun::Zeal })
        {
            Vec2 const s = DungeonKit::ToFrame(kWilleyHall, LaneStart(gun));
            CHECK(Near(s.x, 0.f) && Near(s.y, HalfCenterY(gun)));
            Vec2 const e = DungeonKit::ToFrame(kWilleyHall, LanePoint(gun, kHallLength));
            CHECK(Near(e.x, kHallLength) && Near(e.y, HalfCenterY(gun)));
            CHECK(HalfOf(LaneStart(gun)) == gun);
            for (float x : kBurstX)
            {
                CHECK(HalfOf(LanePoint(gun, x)) == gun);
                CHECK(InsideFrame(kWilleyHall, LanePoint(gun, x)));
            }
            // The load spot: behind the breech, in the gun's own half, inside the arena, 2.5 yd clear of the gun.
            Vec2 const l = LoadSpot(gun);
            CHECK(HalfOf(l) == gun);
            CHECK(WilleyArena().Contains(l, GunAt(gun).z));
            CHECK(DungeonKit::Distance(l, GunAt(gun).XY()) > kLoadRadius);
            CHECK(DungeonKit::ToFrame(kWilleyHall, l).x < DungeonKit::ToFrame(kWilleyHall, GunAt(gun).XY()).x);
            CHECK(OtherGun(OtherGun(gun)) == gun);
        }
        // Each gun's own glow ring.
        CHECK(GlowSpell(Gun::Mercy) == SPELL_WY_MERCY_GLOW);
        CHECK(GlowSpell(Gun::Zeal) == SPELL_WY_ZEAL_GLOW);
        CHECK(GlowSpell(Gun::Mercy) != GlowSpell(Gun::Zeal));
        CHECK(GunFromRoll(0) == Gun::Mercy);
        CHECK(GunFromRoll(1) == Gun::Zeal);
        CHECK(std::string(GunName(Gun::Mercy)) == "Mercy");
        CHECK(std::string(GunName(Gun::Zeal)) == "Zeal");
    }

    void TestBarrage()
    {
        // Every order: five blasts, three on one half and two on the other; the 20 orders are all different.
        std::set<std::string> seen;
        for (std::uint32_t roll = 0; roll < kBarrageOrders; ++roll)
        {
            BarrageOrder const order = MakeBarrageOrder(roll);
            std::uint32_t const mercy = CountOf(order, Gun::Mercy);
            std::uint32_t const zeal = CountOf(order, Gun::Zeal);
            CHECK(mercy + zeal == kBarrageBlasts);
            CHECK((mercy == 3 && zeal == 2) || (mercy == 2 && zeal == 3));
            seen.insert(BarrageCall(order));
        }
        CHECK(seen.size() == kBarrageOrders);
        // Any value works (modulo the order count).
        CHECK(BarrageCall(MakeBarrageOrder(7)) == BarrageCall(MakeBarrageOrder(7 + kBarrageOrders)));
        // The build spec's example call.
        BarrageOrder const example{ { Gun::Mercy, Gun::Zeal, Gun::Mercy, Gun::Mercy, Gun::Zeal } };
        CHECK(BarrageCall(example) == "%s calls the Barrage: Mercy! Zeal! Mercy! Mercy! Zeal!");
        // Roll 6 = Mercy major, Zeal on blasts 2 and 5 (pair { 1, 4 }).
        CHECK(MakeBarrageOrder(6) == example);
        // Timing: the call 3 s before the first blast, then 1.5 s apart (the drill's 3000 ... 9000).
        CHECK(BlastDelayMs(0) == 3000u);
        CHECK(BlastDelayMs(4) == 9000u);
        // The last blast lands well before the next Barrage.
        CHECK(BlastDelayMs(kBarrageBlasts - 1) < kBarrageCadence.every);
        CHECK(kBarragePct == 30.f && kCannonFirePct == 40.f);
    }

    void TestShot()
    {
        // 5% of 185,001 = 9,250 with no Shaken; at 2 stacks the base point is cut so the hit lands at 5% again.
        CHECK(ShotDamage(185001, 185001, 0) == 9250u);
        CHECK(ShotDamage(185001, 185001, 2) == 7708u);
        CHECK(static_cast<std::uint32_t>(ShotDamage(185001, 185001, 2) * 1.2 + 0.5) == 9250u);
        CHECK(ShotDamage(230000, 230000, 3) == 8846u);
        // Never lethal: it leaves him at 1 health at worst.
        CHECK(ShotDamage(185001, 5000, 0) == 4999u);
        CHECK(ShotDamage(185001, 2, 0) == 1u);
        CHECK(ShotDamage(185001, 1, 0) == 0u);
        CHECK(ShotDamage(185001, 0, 0) == 0u);
        // Even through Shaken the capped hit stays below his health.
        CHECK(static_cast<std::uint32_t>(ShotDamage(185001, 3000, 3) * 1.3) < 3000u);
        CHECK(kShakenMaxStacks == 3u);
        // F-2: a player's +damage-taken debuff on top (Curse of the Elements' 13%) would push the capped hit past his
        // health; the after-modifier clamp holds it at health - 1 whatever it became.
        std::uint32_t const raised = static_cast<std::uint32_t>(ShotDamage(185001, 3000, 3) * 1.3 * 1.13 + 0.5);
        CHECK(raised >= 3000u);
        CHECK(SelfDamageCap(3000, raised) == 2999u);
        CHECK(SelfDamageCap(3000, 1200) == 1200u);
        CHECK(SelfDamageCap(3000, 2999) == 2999u);
        CHECK(SelfDamageCap(3000, 3000) == 2999u);
        CHECK(SelfDamageCap(1, 50) == 0u && SelfDamageCap(0, 50) == 0u);
    }

    // The bots' spot bounds (F-2): the hall, never the yard its far end opens into.
    void TestSpotBounds()
    {
        std::array<Vec2, 4> const hall = HallSpotCorners();
        auto inside = [&hall](Vec2 p) { return DungeonKit::PointInPolygon(hall, p); };
        // The yard opening's ends and the yard beyond it (the tunnel portcullis, frame (27.4, 48.8)) are out.
        CHECK(!inside(kYardOpeningA));
        CHECK(!inside(kYardOpeningB));
        CHECK(!inside(DungeonKit::FramePoint(kWilleyHall, 49.f, 22.f)));
        CHECK(!inside({ 3575.01f, -2984.0f }));
        // Every spot a dodge wants is in: both halves down the whole hall, the rank spots, the load spots, his own.
        for (float x : { 2.f, 16.f, 30.f, 44.f, 56.f })
            for (Gun gun : { Gun::Mercy, Gun::Zeal })
                CHECK(inside(LanePoint(gun, x)));
        for (StratholmeRework::Point3 const& p : kWilleyRank4)
            CHECK(inside(p.XY()));
        CHECK(inside(LoadSpot(Gun::Mercy)) && inside(LoadSpot(Gun::Zeal)));
        CHECK(inside(kWilleySpawn.XY()));
        CHECK(kSpotZMin < kRankZ && kRankZ < kSpotZMax && kSpotZMin < kWilleySpawn.z && kWilleySpawn.z < kSpotZMax);
    }

    void TestTimers()
    {
        CHECK(kCannonFireCadence.first == 10000u && kCannonFireCadence.every == 12000u);
        CHECK(kBarrageCadence.first == 12000u && kBarrageCadence.every == 20000u);
        CHECK(kCannonFireWarnMs == 2500u);
        CHECK(PickInRange(kKnockAwayEvery, 0.f) == 11000u);
        CHECK(PickInRange(kKnockAwayEvery, 1.f) == 17000u);
        CHECK(PickInRange(kPummelEvery, 0.5f) == 15000u);
        // The ball lies 20 s; the carrier has 30 s; the load needs 2 s.
        CHECK(kBallLifeMs == 20000u && kHoldingMs == 30000u && kLoadDwellMs == 2000u);
        CHECK(kRiflemanHealth(false) == 5000u && kRiflemanHealth(true) == 7000u);
    }
}

int main()
{
    TestSliceAndArena();
    TestDrill();
    TestRankCycle();
    TestHalvesAndGuns();
    TestBarrage();
    TestShot();
    TestSpotBounds();
    TestTimers();
    return Report("strat_willey_test");
}
