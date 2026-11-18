// Host tests for IncendiusHardModeLogic.h (D12: Lord Incendius's hard mode, Lord of the Lake): the slice, the tuning,
// the crumble timer, the giant's spot and reach, the reach band and the tank bot's soak line, the Arm Sweep's bands and
// throw, the Lava Spawn spots, Firelord's Will, the Cinder's refusals and the island, the intro.
#include "DungeonKitEdgeLogic.h"
#include "IncendiusHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <span>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdLordOfTheLake;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool Inside(std::vector<Vec2> const& poly, Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(poly), p);
    }

    BrdIncendius::FramePoint F(Vec2 p)
    {
        return BrdIncendius::ToFrame(p);
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211180 && kSpellSlice.last == 211229);
        CHECK(SPELL_LAKE_CRUSHING_FIST == 211180 && SPELL_LAKE_CINDER_TOSS == 211191);
        CHECK(kSpellSlice.Contains(SPELL_LAKE_FIRELORDS_WILL) && kSpellSlice.Contains(SPELL_LAKE_FIRELORDS_BREATH));
        // Never D11's slice; the Cinder's use spell is IT's (event items), item 70621.
        CHECK(!BrdIncendius::kSpellSlice.Contains(SPELL_LAKE_CRUSHING_FIST));
        CHECK(kSpellCinderUse == 211260 && kSpellsEventItems.Contains(kSpellCinderUse));
        CHECK(kItemCinder == 70621);
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_LORD_OF_THE_LAKE));
        CHECK(!ArenaFor(BOSS_LORD_OF_THE_LAKE).Empty());
        // Tags: the Arm Sweep is the drill's 15 (D11 reserved it); the others never collide with D11's.
        CHECK(TAG_LAKE_ARM_SWEEP == 15);
        for (std::uint32_t tag : { std::uint32_t(TAG_LAKE_CRUSHING_FIST), std::uint32_t(TAG_LAKE_REACH),
            std::uint32_t(TAG_LAKE_NO_BEHIND) })
        {
            CHECK(tag != BrdIncendius::TAG_IN_FIRE_STORM && tag != BrdIncendius::TAG_IN_MAGMA_FIST);
            CHECK(tag != BrdIncendius::TAG_IN_LAVA_SURGE && tag != BrdIncendius::TAG_IN_NECK_SEAL);
            CHECK(tag != BrdIncendius::TAG_IN_CRUMBLE && tag != TAG_LAKE_ARM_SWEEP);
        }
        // Texts: D11's 4, 6, 7 are the hard mode's lines; this WP owns 8-9.
        CHECK(YELL_LAKE_CINDER == 4 && EMOTE_LAKE_ARM_RAISED == 6 && EMOTE_LAKE_BREATH == 7);
        CHECK(EMOTE_LAKE_RISES == 8 && EMOTE_LAKE_SPAWNS == 9);
    }

    void TestTuning()
    {
        // Section 3.6 / the build spec.
        CHECK(kLakeHealth == 340000 && kLavaSpawnHealth == 6000 && kRebirths == 0);
        CHECK(kFireStormEveryMs == 10000 && kFireStormLifeMs == 20000);
        CHECK(kFireStormLifeMs < BrdIncendius::kFireStormLifeMs);
        CHECK(!kMagmaFistOnTank && !kLavaSurge);
        CHECK(kCrushingFirstMs == 10000 && kCrushingEveryMs == 15000 && kCrushingWarnMs == 3000);
        CHECK(Near(kCrushingRadiusYd, 6.f) && Near(kCrushingTankPct, 35.f) && Near(kCrushingOthersPct, 45.f));
        CHECK(kSweepFirstMs == 20000 && kSweepEveryMs == 30000 && kSweepCastMs == 4000);
        CHECK(Near(kSweepWidthYd, 10.f) && Near(kSweepPct, 30.f));
        CHECK(kSpawnFirstMs == 15000 && kSpawnEveryMs == 20000 && kSpawnCount == 2 && kSpawnWalkMs == 10000);
        CHECK(kSpawnHealPct == 5 && Near(kWillPctPerStack, 10.f) && kWillMaxStacks == 10);
        CHECK(kBreathCheckMs == 1000 && kBreathGraceMs == 3000 && Near(kBreathPct, 8.f));
        // Under 50% the avoidable single hits carry Weakened (shared doc section 4): Crushing Fist does.
        CHECK(kCrushingOthersPct < 50.f);
        // "Nothing lands during the Sweep": the pre-hold covers the longest marker (Crushing Fist 3 s; Fire Storm
        // and Magma Fist 2 s).
        CHECK(kSweepPreHoldMs >= kCrushingWarnMs);
        CHECK(kSweepPreHoldMs >= BrdIncendius::kFireStormWarnMs && kSweepPreHoldMs >= BrdIncendius::kFistWarnMs);
        // The 3 s grace covers a sweep slide only if it is shorter than the cast: the tank must not be breathed on
        // for stepping out late.
        CHECK(kBreathGraceMs < kSweepCastMs);
        // The kill target (S2 tuning): 340k + 60k of spawns at 3,774 effective DPS is about 106 s, ahead of the last
        // crumble at 120 s.
        CHECK((kLakeHealth + 10 * kLavaSpawnHealth) / 3774 < kCrumbleAtMs.back() / 1000);
    }

    void TestCrumbleTimer()
    {
        CHECK(kCrumbleAtMs[0] == 40000 && kCrumbleAtMs[1] == 80000 && kCrumbleAtMs[2] == 120000);
        CHECK(kCrumbleAtMs.size() == BrdIncendius::kCrumbleMaxSteps);
        for (std::size_t i = 0; i < kCrumbleAtMs.size(); ++i)
        {
            CHECK(CrumbleRaiseMs(i) + BrdIncendius::kBandWarnMs == kCrumbleAtMs[i]);
            if (i)
                CHECK(CrumbleRaiseMs(i) > kCrumbleAtMs[i - 1]);     // one step at a time
        }
        // Three steps of 2 yd: 6 yd of each long edge at most.
        CHECK(Near(BrdIncendius::CrumbledDepth(3), 6.f));
    }

    void TestGiant()
    {
        CHECK(kGiantDisplay == 1204);
        CHECK(kGiantScale >= 8.f && kGiantScale <= 10.f);       // VISUALS INCENDIUS_GIANT_SCALE_RANGE
        // Section 7 #14 A: near causeway height at (876.8, -290.3), beside the Anvil, over the lake (off the floor).
        CHECK(Near(kGiantSpot.x, 876.8f) && Near(kGiantSpot.y, -290.3f));
        CHECK(Near(kGiantSpot.z, BrdIncendius::kFloorZ, 1.f));
        CHECK(GiantOnSouthEast());
        CHECK(!Inside(BrdIncendius::CausewayFloor(), kGiantSpot.XY()));
        CHECK(!Inside(BrdIncendius::ArenaFloor(), kGiantSpot.XY()));
        CHECK(Near(F(kGiantSpot.XY()).s, F(BrdIncendius::kAnvil.XY()).s, 0.5f));
        // The lava is 37-40 yd under the causeway; the intro jump ends at its surface.
        CHECK(BrdIncendius::kFloorZ - kLakeSurfaceZ >= 35.f && BrdIncendius::kFloorZ - kLakeSurfaceZ <= 40.f);
        // At least 12 yd of lava between him and the nearest real edge: nobody stands behind him.
        CHECK(DungeonKit::NearestEdge(std::span<Vec2 const>(BrdIncendius::CausewayFloor()), kGiantSpot.XY())->distance
            > 10.f);
    }

    void TestReach()
    {
        std::vector<Vec2> const floor = BrdIncendius::CausewayFloor();
        float lastReach = 0.f;
        for (std::uint32_t steps = 0; steps <= BrdIncendius::kCrumbleMaxSteps; ++steps)
        {
            float const depth = BrdIncendius::CrumbledDepth(steps);
            // The band: 6 yd deep from the current near edge, moving in 2 yd a step.
            // (Sampled between the profile's vertices: the crumbled depth's lateral shift steps at a vertex.)
            for (float s = kReachSMin + 0.5f; s <= kReachSMax + 0.01f; s += 2.f)
            {
                float const edge = NearEdgeW(s, steps);
                CHECK(Near(ReachInnerW(s, steps) - edge, kReachDepthYd));
                CHECK(edge >= BrdIncendius::ProfileAt(s).wLo + depth - 0.01f);      // never past the crumbled depth
                // In reach: a point 3 yd inside the edge; 1 yd past the inner side is not; the band's middle is on the
                // real floor and outside the crumbled bands.
                Vec2 const mid = BrdIncendius::ToWorld(s, edge + kReachDepthYd * 0.5f);
                CHECK(InReach(mid, steps));
                CHECK(Inside(floor, mid));
                CHECK(!InReach(BrdIncendius::ToWorld(s, edge + kReachDepthYd + 1.f), steps));
                CHECK(!InReach(BrdIncendius::ToWorld(s, edge - kReachRimSlackYd - 0.5f), steps));
            }
            // Only over the bulge.
            CHECK(!InReach(BrdIncendius::ToWorld(kReachSMin - 1.f, NearEdgeW(kReachSMin, steps) + 3.f), steps));
            CHECK(!InReach(BrdIncendius::ToWorld(kReachSMax + 1.f, NearEdgeW(kReachSMax, steps) + 3.f), steps));
            // The giant's spot, the far side and the floor's middle at the bulge are never in reach.
            CHECK(!InReach(kGiantSpot.XY(), steps));
            CHECK(!InReach(BrdIncendius::ToWorld(6.f, BrdIncendius::ProfileAt(6.f).wHi - 1.f), steps));

            // His combat reach: everyone in the band is within melee range of him (melee range is 3D; he hovers at
            // the causeway's height), and it grows with each step.
            float const reach = GiantCombatReach(steps);
            for (Vec2 const& p : ReachSamples(steps))
                CHECK(DungeonKit::Distance(p, kGiantSpot.XY()) < MeleeRangeYd(reach));
            CHECK(reach > lastReach);
            lastReach = reach;
            // Within reason: the island's far side stays out of his reach at the pull.
            if (steps == 0)
            {
                Vec2 const farSide = BrdIncendius::ToWorld(6.f, BrdIncendius::ProfileAt(6.f).wHi);
                CHECK(DungeonKit::Distance(farSide, kGiantSpot.XY()) > MeleeRangeYd(reach));
            }

            // The tank bot's soak line: in the band and wholly on the bots' safe floor (2 yd inside the lethal edge)
            // along its whole length, in front of him.
            Band const soak = SoakLine(steps);
            CHECK(Near(soak.width, kSoakWidthYd));
            std::vector<Vec2> const safe = BrdIncendius::SafeFloor(steps);
            for (int i = 0; i <= 16; ++i)
            {
                float const t = static_cast<float>(i) / 16.f;
                Vec2 const c{ soak.from.x + (soak.to.x - soak.from.x) * t,
                    soak.from.y + (soak.to.y - soak.from.y) * t };
                BrdIncendius::FramePoint const f = F(c);
                float const edge = NearEdgeW(f.s, steps);
                CHECK(f.w - kSoakWidthYd * 0.5f >= edge + BrdIncendius::kBoundsMarginYd - 0.05f);
                CHECK(f.w + kSoakWidthYd * 0.5f <= edge + kReachDepthYd + 0.05f);
                CHECK(InReach(c, steps));
                CHECK(Inside(safe, BrdIncendius::ToWorld(f.s, f.w - kSoakWidthYd * 0.5f)));
                CHECK(Inside(safe, BrdIncendius::ToWorld(f.s, f.w + kSoakWidthYd * 0.5f)));
                CHECK(std::fabs(f.s - F(kGiantSpot.XY()).s) <= 4.f);
            }
        }
    }

    void TestSweep()
    {
        std::vector<Vec2> const floor = BrdIncendius::CausewayFloor();
        float const bearing = SweepThrowBearing();
        // The throw goes across the causeway away from the giant (+w, north-west).
        Vec2 const step{ std::cos(bearing), std::sin(bearing) };
        BrdIncendius::FramePoint const dir = F({ BrdIncendius::kOrigin.x + step.x, BrdIncendius::kOrigin.y + step.y });
        CHECK(Near(dir.s, 0.f, 0.02f) && Near(dir.w, 1.f, 0.02f));

        float lastHi = -1000.f;
        for (std::size_t i = 0; i < kSweepSpots.size(); ++i)
        {
            Band const band = SweepBand(static_cast<SweepSpot>(i));
            CHECK(Near(band.width, kSweepWidthYd));
            BrdIncendius::FramePoint const a = F(band.from);
            BrdIncendius::FramePoint const b = F(band.to);
            float const s = kSweepSpots[i];
            CHECK(Near(a.s, s, 0.05f) && Near(b.s, s, 0.05f));
            // Inside the arena (s -24..+24), never touching the neck seals.
            CHECK(s - kSweepWidthYd * 0.5f >= BrdIncendius::kArenaSMin);
            CHECK(s + kSweepWidthYd * 0.5f <= BrdIncendius::kArenaSMax);
            // Across the whole width: past both real edges everywhere in the band.
            for (float t = s - kSweepWidthYd * 0.5f; t <= s + kSweepWidthYd * 0.5f + 0.01f; t += 0.5f)
            {
                BrdIncendius::ProfilePoint const p = BrdIncendius::ProfileAt(t);
                CHECK(a.w < p.wLo && b.w > p.wHi);
            }
            // Gaps of safe ground between the bands (the slide's way out).
            CHECK(s - kSweepWidthYd * 0.5f > lastHi + 1.f);
            lastHi = s + kSweepWidthYd * 0.5f;
            // Every spot in the band on the floor is thrown over the far (north-west) edge.
            for (float t = s - 4.f; t <= s + 4.f; t += 2.f)
                for (float frac : { 0.1f, 0.5f, 0.9f })
                {
                    BrdIncendius::ProfilePoint const p = BrdIncendius::ProfileAt(t);
                    Vec2 const at = BrdIncendius::ToWorld(t, p.wLo + (p.wHi - p.wLo) * frac);
                    DungeonKit::EdgePush const push = DungeonKit::PlanOverEdge(std::span<Vec2 const>(floor), at,
                        bearing);
                    CHECK(push.overEdge);
                    CHECK(F(push.exit).w > BrdIncendius::MidlineAt(F(push.exit).s));
                    CHECK(!Inside(floor, push.landing));
                }
        }
        // The middle sweep leaves room in the reach band on both sides (the tank slides along the edge, in reach).
        float const midLo = kSweepSpots[1] - kSweepWidthYd * 0.5f;
        float const midHi = kSweepSpots[1] + kSweepWidthYd * 0.5f;
        CHECK(midLo - kReachSMin >= 4.f && kReachSMax - midHi >= 4.f);
        // The spot pick: any of three first, never the same twice running.
        CHECK(PickSweepSpot(kNoSpot, 0) == SweepSpot::SouthWest);
        CHECK(PickSweepSpot(kNoSpot, 1) == SweepSpot::Middle);
        CHECK(PickSweepSpot(kNoSpot, 2) == SweepSpot::NorthEast);
        for (std::uint8_t last = 0; last < 3; ++last)
            for (std::uint32_t roll = 0; roll < 4; ++roll)
                CHECK(static_cast<std::uint8_t>(PickSweepSpot(last, roll)) != last);
        CHECK(PickSweepSpot(1, 0) != PickSweepSpot(1, 1));
    }

    void TestLavaSpawn()
    {
        std::vector<Vec2> const floor = BrdIncendius::CausewayFloor();
        Vec2 const anvil = BrdIncendius::kAnvil.XY();
        CHECK(Near(SpawnS(0.f), kSpawnSMin) && Near(SpawnS(1.f), kSpawnSMax) && Near(SpawnS(2.f), kSpawnSMax));
        for (std::uint32_t steps = 0; steps <= BrdIncendius::kCrumbleMaxSteps; ++steps)
            for (float roll = 0.f; roll <= 1.001f; roll += 0.1f)
                for (bool se : { true, false })
                {
                    Vec2 const spot = SpawnSpot(SpawnS(roll), se, steps);
                    BrdIncendius::FramePoint const f = F(spot);
                    BrdIncendius::ProfilePoint const p = BrdIncendius::ProfileAt(f.s);
                    // On the floor, inside the crumbled edge (or on the middle line where the floor is too narrow),
                    // on its own side, in the arena.
                    CHECK(Inside(floor, spot));
                    float const depth = BrdIncendius::CrumbledDepth(steps);
                    if (se)
                        CHECK(f.w >= p.wLo + depth - 0.01f && f.w <= BrdIncendius::MidlineAt(f.s) + 0.01f);
                    else
                        CHECK(f.w <= p.wHi - depth + 0.01f && f.w >= BrdIncendius::MidlineAt(f.s) - 0.01f);
                    CHECK(f.s >= BrdIncendius::kArenaSMin && f.s <= BrdIncendius::kArenaSMax);
                    // The walk: about 10 s to the Anvil (less from close by, at the slowest speed), always a walk.
                    float const d = DungeonKit::Distance(spot, anvil);
                    CHECK(d > kSpawnArriveYd + 1.f);
                    CHECK(d / SpawnSpeed(d) <= kSpawnWalkMs / 1000.f + 0.01f);
                    if (d >= kSpawnMinSpeedYdS * kSpawnWalkMs / 1000.f)
                        CHECK(Near(d / SpawnSpeed(d), kSpawnWalkMs / 1000.f, 0.01f));
                }
        CHECK(Near(SpawnSpeed(0.f), kSpawnMinSpeedYdS));
    }

    void TestWill()
    {
        CHECK(Near(WillFactor(0), 1.f));
        CHECK(Near(WillFactor(1), 1.1f));
        CHECK(Near(WillFactor(10), 2.f));
        CHECK(Near(WillFactor(15), 2.f));      // the cap
        CHECK(HealedHealth(100000, 340000) == 117000);
        CHECK(HealedHealth(330000, 340000) == 340000);
        CHECK(HealedHealth(340000, 340000) == 340000);
        CHECK(HealedHealth(0, 340000) == 17000);   // S2: an arrival is about 17,000 of his health
    }

    void TestCinder()
    {
        CinderCheck ok;
        ok.mapId = kMapBlackrockDepths;
        ok.hasInstance = true;
        ok.heroic = true;
        ok.incendiusAlive = true;
        ok.incendiusState = DungeonKit::State::NotStarted;
        ok.onTheIsland = true;
        CHECK(CinderUseRefusal(ok) == CinderRefusal::None);

        CinderCheck c = ok;
        c.mapId = 229;
        CHECK(CinderUseRefusal(c) == CinderRefusal::NotInDungeon);
        c = ok;
        c.hasInstance = false;
        CHECK(CinderUseRefusal(c) == CinderRefusal::NotInDungeon);
        c = ok;
        c.heroic = false;
        CHECK(CinderUseRefusal(c) == CinderRefusal::NotHeroic);
        c = ok;
        c.lit = true;
        CHECK(CinderUseRefusal(c) == CinderRefusal::AlreadyLit);
        c = ok;
        c.incendiusAlive = false;
        CHECK(CinderUseRefusal(c) == CinderRefusal::IncendiusGone);
        c = ok;
        c.incendiusState = DungeonKit::State::Done;
        CHECK(CinderUseRefusal(c) == CinderRefusal::IncendiusGone);
        c = ok;
        c.incendiusEngaged = true;
        CHECK(CinderUseRefusal(c) == CinderRefusal::IncendiusFighting);
        c = ok;
        c.incendiusState = DungeonKit::State::InProgress;
        CHECK(CinderUseRefusal(c) == CinderRefusal::IncendiusFighting);
        c = ok;
        c.casterInCombat = true;
        CHECK(CinderUseRefusal(c) == CinderRefusal::InCombat);
        c = ok;
        c.onTheIsland = false;
        CHECK(CinderUseRefusal(c) == CinderRefusal::NotOnTheIsland);
        // A wipe (Fail, then NotStarted) does not stop a second attempt; the instance keeps the flag anyway.
        c = ok;
        c.incendiusState = DungeonKit::State::Fail;
        CHECK(CinderUseRefusal(c) == CinderRefusal::None);
        // Every refusal has words; the item is kept on each (CheckCast).
        for (CinderRefusal r : { CinderRefusal::NotInDungeon, CinderRefusal::NotHeroic, CinderRefusal::AlreadyLit,
            CinderRefusal::IncendiusGone, CinderRefusal::IncendiusFighting, CinderRefusal::InCombat,
            CinderRefusal::NotOnTheIsland })
            CHECK(CinderRefusalText(r)[0] != '\0');

        // The island: the spawn, the Anvil and the tips at the causeway's height; not the lake, not the walkway above,
        // not the causeway past the sealed necks.
        float const z = BrdIncendius::kFloorZ;
        CHECK(OnTheIsland(kIncendiusSpawn.XY(), z));
        CHECK(OnTheIsland(BrdIncendius::kAnvil.XY(), z + 1.f));
        CHECK(OnTheIsland(kIncendiusTipWest.XY(), z) && OnTheIsland(kIncendiusTipEast.XY(), z));
        CHECK(!OnTheIsland(kIncendiusSpawn.XY(), z + 22.f));
        CHECK(!OnTheIsland(kGiantSpot.XY(), z));
        CHECK(!OnTheIsland(BrdIncendius::ToWorld(-30.f, BrdIncendius::MidlineAt(-30.f)), z));
        CHECK(!OnTheIsland(BrdIncendius::ToWorld(30.f, BrdIncendius::MidlineAt(30.f)), z));
        // The rope's climb spot (D10) is on the island too: the Cinder works there.
        CHECK(OnTheIsland(kRopeClimbSpot.XY(), kRopeClimbSpot.z));
        // He patrols round the Anvil within the boss range of any island spot.
        CHECK(DungeonKit::Distance(kIncendiusTipWest.XY(), BrdIncendius::kAnvil.XY()) < kCinderBossRangeYd - 20.f);
    }

    void TestIntro()
    {
        CHECK(IntroStepAt(0) == IntroStep::Yell);
        CHECK(IntroStepAt(kIntroJumpMs - 1) == IntroStep::Yell);
        CHECK(IntroStepAt(kIntroJumpMs) == IntroStep::Jump);
        CHECK(IntroStepAt(kIntroRiseMs - 1) == IntroStep::Jump);
        CHECK(IntroStepAt(kIntroRiseMs) == IntroStep::Rise);
        CHECK(IntroStepAt(60000) == IntroStep::Rise);
        // The jump lands before he rises: from anywhere on the island to the lake under his spot.
        float const far = DungeonKit::Distance(kIncendiusTipEast.XY(), kGiantSpot.XY());
        CHECK(far / kIntroJumpSpeedXY * 1000.f < static_cast<float>(kIntroRiseMs - kIntroJumpMs));
        CHECK(kIdleCheckMs <= 1000);
    }
}

namespace
{
    // R-1-B M2 / M1 (orchestrator default): the giant's small reach, his Hand on the near rim, his corpse on the rim.
    void TestHandAndRanged()
    {
        // No point of the arena floor is inside his melee range plus the longest ranged minimum: no hunter or wand is
        // ever too close to him (Spell.cpp: TOO_CLOSE inside min range + the melee range of both reaches).
        float const tooClose = MeleeRangeYd(kGiantReachYd) + kRangedMinYd;
        std::vector<Vec2> const arena = BrdIncendius::ArenaFloor();
        float nearest = 1000.f;
        for (std::size_t i = 0; i < arena.size(); ++i)
        {
            Vec2 const a = arena[i];
            Vec2 const b = arena[(i + 1) % arena.size()];
            for (int k = 0; k <= 20; ++k)
            {
                float const t = 0.05f * float(k);
                nearest = std::min(nearest, DungeonKit::Distance({ a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t },
                    kGiantSpot.XY()));
            }
        }
        CHECK(nearest > tooClose);
        // ... and nobody can melee him: the Hand is the melee's target.
        CHECK(nearest > MeleeRangeYd(kGiantReachYd));
        CHECK(kGiantReachYd < GiantCombatReach(0));
        CHECK(kCreaturesWave1.Contains(NPC_LAKE_HAND));
        CHECK(NPC_LAKE_HAND != NPC_BRD_LAVA_SPAWN && NPC_LAKE_HAND != NPC_BRD_STALKER);

        for (std::uint32_t steps = 0; steps <= BrdIncendius::kCrumbleMaxSteps; ++steps)
        {
            float const reachFar = ReachFarthestYd(steps);
            // His swing needs no reach, but his Fiery Burst (40 yd) and the taunts (30 yd) on a tank in the band do.
            CHECK(reachFar < 40.f + kGiantReachYd + kPlayerCombatReach);
            // A 30 yd taunt reaches the tank's soak line at every step.
            Band const line = SoakLine(steps);
            for (Vec2 const& end : { line.from, line.to })
                CHECK(DungeonKit::Distance(end, kGiantSpot.XY()) < 30.f + kGiantReachYd + kPlayerCombatReach);
            Vec2 const hand = HandSpot(steps);
            // On the floor (inside the crumbled edge, never in the next step's band at its warning: the step counts
            // from its warning) and in the reach band, by the tank's soak line (the tank melees it from there).
            CHECK(InReach(hand, steps));
            CHECK(Inside(BrdIncendius::ArenaFloor(), hand));
            CHECK(Near(std::fabs(F(hand).w - NearEdgeW(F(hand).s, steps)), kHandEdgeInsetYd, 0.05f));
            Band const soak = SoakLine(steps);
            Vec2 const soakMid{ (soak.from.x + soak.to.x) * 0.5f, (soak.from.y + soak.to.y) * 0.5f };
            CHECK(DungeonKit::Distance(hand, soakMid) <= kPlayerCombatReach * 2.f + 4.f / 3.f + 0.5f);
            // His corpse lands on the rim at the Hand's spot: inside the arena floor (lootable), not in the lava.
            CHECK(Inside(BrdIncendius::ArenaFloor(), CorpseSpot(steps)));
            CHECK(Inside(BrdIncendius::CausewayFloor(), CorpseSpot(steps)));
        }
        CHECK(kHandSyncMs <= 500);
    }
}

int main()
{
    TestSlice();
    TestTuning();
    TestCrumbleTimer();
    TestGiant();
    TestReach();
    TestSweep();
    TestLavaSpawn();
    TestWill();
    TestCinder();
    TestIntro();
    TestHandAndRanged();
    return Report("brd_incendius_hard_mode_test");
}
