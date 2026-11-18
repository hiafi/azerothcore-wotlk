// Host tests for EmperorHardModeLogic.h (D24: the Emperor's hard mode, the Avatar of Ragnaros): the slice and the
// kill slot, the rise's numbers (260k, the display scale in VR's range, the throne on the dais in his arena, the
// knockback), Magma Clap's falloff, Volcanic Blast's split and stones, the clock (first casts, cadences, the two
// casts never overlapping, a two-minute replay), rule 10's answer and its graces.
#include "EmperorHardModeLogic.h"
#include "EmperorLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdAvatar;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndSlot()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, clear of D23's.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211660 && kSpellSlice.last == 211709);
        CHECK(SPELL_AV_MAGMA_CLAP_CAST == 211660 && SPELL_AV_MAGMA_BLAST == 211669);
        CHECK(kLastSpell <= kSpellSlice.last);
        CHECK(SPELL_AV_MAGMA_CLAP_CAST > BrdEmperor::kSpellSlice.last);
        // Its tags never collide with D23's (one encounter, Dagran's).
        for (std::uint32_t tag : { TAG_AV_MAGMA_CLAP, TAG_AV_VOLCANIC_BLAST, TAG_AV_VOLCANIC_STONE })
            for (std::uint32_t d23 : { 1u, 2u, 3u, 4u, 5u, 21u })
                CHECK(tag != d23);
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_AVATAR));
        CHECK(!ArenaFor(BOSS_AVATAR).Empty());
        // D23 says the Avatar's two lines (gap 38).
        CHECK(BrdEmperor::EMOTE_EM_MAGMA_CLAP == 11 && BrdEmperor::EMOTE_EM_VOLCANIC_BLAST == 12);
    }

    void TestRise()
    {
        CHECK(kAvatarHealth == 260000);
        CHECK(kAvatarDisplay == 11121);
        CHECK(kAvatarScale >= 0.12f && kAvatarScale <= 0.18f);
        // 58 yd tall at 1.0: 7-10 yd on the dais.
        CHECK(57.9f * kAvatarScale >= 7.f && 57.9f * kAvatarScale <= 10.5f);
        // The reach covers half his width at this scale.
        CHECK(kAvatarReachYd >= 36.9f * kAvatarScale * 0.5f);
        // The throne is his spawn, on the dais (x 1370-1391, z -87.6), in his arena; Moira's cage 4-5 yd beside it.
        CHECK(kThroneSpot.x == kEmperorSpawn.x && kThroneSpot.y == kEmperorSpawn.y);
        CHECK(kThroneSpot.x >= 1370.f && kThroneSpot.x <= 1391.f);
        CHECK(Near(kThroneSpot.z, BrdEmperor::kDaisZ, 0.2f));
        CHECK(ArenaFor(BOSS_AVATAR).Contains(kThroneSpot.XY(), kThroneSpot.z));
        float const moira = DungeonKit::Distance(kThroneSpot.XY(), kMoiraSpawn.XY());
        CHECK(moira > 4.f && moira < 5.f);
        // The jump from the tank's Spot reaches the throne.
        CHECK(DungeonKit::Distance(BrdEmperor::kTankSpot, kThroneSpot.XY()) < 20.f);
        // The knockback: 15 yd at 8 yd/s up is about 18 yd/s out (distance = 2 x vxy x vz / g).
        float const vxy = KnockbackSpeedXY(kKnockbackYd);
        CHECK(Near(vxy, 18.09f, 0.05f));
        CHECK(Near(2.f * vxy * kKnockbackSpeedZ / kGravity, kKnockbackYd, 0.01f));
        CHECK(KnockbackSpeedXY(10.f, 0.f) == 0.f);
    }

    void TestMagmaClap()
    {
        // 70% within 10 yd, linear to 15% at 40 yd and beyond.
        CHECK(Near(MagmaClapPct(0.f), 70.f));
        CHECK(Near(MagmaClapPct(10.f), 70.f));
        CHECK(Near(MagmaClapPct(25.f), 42.5f));
        CHECK(Near(MagmaClapPct(30.f), 33.33f));
        CHECK(Near(MagmaClapPct(40.f), 15.f));
        CHECK(Near(MagmaClapPct(80.f), 15.f));
        float last = MagmaClapPct(0.f);
        for (float d = 0.f; d <= 60.f; d += 0.5f)
        {
            float const pct = MagmaClapPct(d);
            CHECK(pct <= last + 1e-4f);
            CHECK(pct >= 15.f - 1e-4f && pct <= 70.f + 1e-4f);
            last = pct;
        }
        // The RunOut's 30 yd sits inside the falloff, the cast is the spec's 3 s, first 10 s, every 20 s.
        CHECK(kClapRunOutYd > kClapNearYd && kClapRunOutYd < kClapFarYd);
        CHECK(kClapCastMs == 3000 && kClapFirstMs == 10000 && kClapEveryMs == 20000);
        // The walk back covers 30 yd at a player's 7 yd/s.
        CHECK(kClapWalkBackMs >= 30.f / 7.f * 1000.f);
    }

    void TestVolcanicBlast()
    {
        CHECK(kBlastFirstMs == 15000 && kBlastEveryMs == 25000 && kBlastMarkMs == 5000);
        CHECK(Near(BlastSharePct(1), 80.f));
        CHECK(Near(BlastSharePct(2), 40.f));
        CHECK(Near(BlastSharePct(3), 26.67f));
        CHECK(Near(BlastSharePct(5), 16.f));
        CHECK(BlastSharePct(0) == 0.f);
        // 30 s stones every 25 s: at most 2 at once (S4 "Space").
        CHECK(MaxStones() == 2);
        CHECK(kStoneRadiusYd == 5.f && kStoneMs == 30000 && kStonePct == 8.f);
        // The takers: within 8 yd of the mark on the plane.
        Vec2 const at{ 1380.f, -810.f };
        std::vector<Vec2> const points{ { 1380.f, -810.f }, { 1387.9f, -810.f }, { 1388.1f, -810.f },
            { 1380.f, -802.5f }, { 1400.f, -790.f } };
        std::vector<std::size_t> const in = WithinRadius(at, kBlastRadiusYd, points);
        CHECK(in.size() == 3);
        CHECK(in.size() == 3 && in[0] == 0 && in[1] == 1 && in[2] == 3);

        // R-2-C m4: the stone never lands in the rooted Avatar's melee ring (3.5 + 1.5 + 4/3 = 6.33 yd); its whole
        // 5 yd circle stays outside.
        CHECK(Near(AvatarMeleeRingYd(), 6.333f));
        CHECK(Near(kStoneClearYd, 11.333f));
        Vec2 const avatar{ kThroneSpot.x, kThroneSpot.y };
        Vec2 const far{ avatar.x, avatar.y + 20.f };
        Vec2 const kept = StoneSpot(avatar, kThroneFacing, far);
        CHECK(kept.x == far.x && kept.y == far.y);                          // far enough: the mark's spot
        Vec2 const tank{ avatar.x + 3.f, avatar.y };                        // the tank in his melee
        Vec2 const pushed = StoneSpot(avatar, kThroneFacing, tank);
        CHECK(Near(DungeonKit::Distance(avatar, pushed), kStoneClearYd));
        CHECK(pushed.x > tank.x && Near(pushed.y, avatar.y));              // out along the bearing
        Vec2 const onTop = StoneSpot(avatar, kThroneFacing, avatar);       // on top of him: in front
        CHECK(Near(DungeonKit::Distance(avatar, onTop), kStoneClearYd));
        CHECK(Near(DungeonKit::BearingTo(avatar, onTop), kThroneFacing));
        Vec2 const edge{ avatar.x, avatar.y + kStoneClearYd - 0.01f };      // just inside the clearance: pushed
        CHECK(Near(DungeonKit::Distance(avatar, StoneSpot(avatar, kThroneFacing, edge)), kStoneClearYd));
    }

    // A two-minute replay of the Avatar's clock at 100 ms ticks: when each cast starts.
    struct Replay
    {
        std::vector<std::uint64_t> claps;
        std::vector<std::uint64_t> blasts;
    };

    Replay Run(std::uint64_t rise, std::uint64_t until)
    {
        AvatarClock clock;
        clock.Rise(rise);
        Replay r;
        for (std::uint64_t now = rise; now <= until; now += 100)
        {
            switch (clock.Due(now))
            {
                case Cast::Clap:
                    r.claps.push_back(now);
                    clock.ClapStarted(now);
                    break;
                case Cast::Blast:
                    r.blasts.push_back(now);
                    clock.BlastStarted(now);
                    break;
                default:
                    break;
            }
        }
        return r;
    }

    void TestClock()
    {
        std::uint64_t const rise = 95000;
        Replay const r = Run(rise, rise + 120000);
        // First casts: Magma Clap 10 s, Volcanic Blast 15 s after the rise.
        CHECK(!r.claps.empty() && r.claps[0] == rise + 10000);
        CHECK(!r.blasts.empty() && r.blasts[0] == rise + 15000);
        // Magma Clap: 10, 30, 50 s; at 70 s the mark of 65 s is open (to its hit at 70 s + 1 s): it waits to 71 s;
        // the next keeps the cadence from when it was due (90 s). It goes first when both are due (90 s).
        std::vector<std::uint64_t> const claps{ rise + 10000, rise + 30000, rise + 50000, rise + 71000, rise + 90000,
            rise + 110000 };
        CHECK(r.claps == claps);
        // Volcanic Blast: 15, 40, 65 s; at 90 s Magma Clap is casting (90-93 s, +1 s): it waits to 94 s; the next
        // keeps the cadence from when it was due (115 s).
        std::vector<std::uint64_t> const blasts{ rise + 15000, rise + 40000, rise + 65000, rise + 94000,
            rise + 115000 };
        CHECK(r.blasts == blasts);
        // The two never overlap: no cast starts inside the other's window (its start to its hit + 1 s).
        for (std::uint64_t c : r.claps)
            for (std::uint64_t b : r.blasts)
            {
                CHECK(!(b >= c && b < c + kClapCastMs + kBetweenCastsMs));
                CHECK(!(c >= b && c < b + kBlastMarkMs + kBetweenCastsMs));
            }

        // A clap due during a mark waits for the mark's hit + 1 s.
        AvatarClock clock;
        clock.Rise(0);
        clock.blastAt = 9000;
        CHECK(clock.Due(9000) == Cast::Blast);
        clock.BlastStarted(9000);                   // the mark lands at 14 s
        CHECK(clock.Due(10000) == Cast::None);      // the clap's 10 s waits
        CHECK(clock.Due(14900) == Cast::None);
        CHECK(clock.Due(15000) == Cast::Clap);
        clock.ClapStarted(15000);
        CHECK(clock.clapEndsAt == 18000 && clock.clapAt == 30000);
        CHECK(clock.blastAt == 34000);
        // A forced cast (the test command) from an unscheduled clock.
        AvatarClock idle;
        idle.ClapStarted(5000);
        CHECK(idle.clapEndsAt == 8000 && idle.clapAt == 25000);
    }

    void TestRuleTen()
    {
        AvatarClock clock;
        clock.Rise(0);
        // In reach: never.
        for (std::uint64_t now = 0; now < 10000; now += 100)
            CHECK(!clock.MagmaBlastDue(now, true, false));
        // Out of reach from 10 s: the first at 13 s, then every 2 s.
        std::vector<std::uint64_t> fired;
        for (std::uint64_t now = 10000; now <= 20000; now += 100)
            if (clock.MagmaBlastDue(now, false, false))
                fired.push_back(now);
        std::vector<std::uint64_t> const expected{ 13000, 15000, 17000, 19000 };
        CHECK(fired == expected);
        // Back in reach resets it: the next absence waits 3 s again.
        CHECK(!clock.MagmaBlastDue(20100, true, false));
        CHECK(!clock.MagmaBlastDue(20200, false, false));
        CHECK(!clock.MagmaBlastDue(23100, false, false));
        CHECK(clock.MagmaBlastDue(23200, false, false));
        // A grace resets it too.
        CHECK(!clock.MagmaBlastDue(23300, false, true));
        CHECK(clock.outOfReachSince == 0);

        // The graces: the clap's cast to its hit + the walk back; the blast's mark to its hit + the walk back.
        AvatarClock g;
        g.Rise(0);
        g.ClapStarted(10000);                       // hit at 13 s
        CHECK(!g.ReachGrace(9900));
        CHECK(g.ReachGrace(10000));
        CHECK(g.ReachGrace(17900));
        CHECK(!g.ReachGrace(18000));
        g.BlastStarted(30000);                      // hit at 35 s
        CHECK(!g.ReachGrace(29900));
        CHECK(g.ReachGrace(30000));
        CHECK(g.ReachGrace(39900));
        CHECK(!g.ReachGrace(40000));
    }
}

int main()
{
    TestSliceAndSlot();
    TestRise();
    TestMagmaClap();
    TestVolcanicBlast();
    TestClock();
    TestRuleTen();
    return Report("brd_emperor_hard_mode_test");
}
