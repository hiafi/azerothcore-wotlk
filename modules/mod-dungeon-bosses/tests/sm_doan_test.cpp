// Host tests for DoanLogic.h (D8: Arcanist Doan).
#include "DoanLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace ScarletMonasteryRework;
using namespace SmDoan;

namespace
{
    float Dist(Vec2 a, Vec2 b)
    {
        return std::hypot(a.x - b.x, a.y - b.y);
    }

    constexpr float kPi = 3.14159265358979f;

    // The bearing of `p` from `from` in degrees, 0-360 (measured from +x toward +y).
    float BearingDeg(Vec2 from, Vec2 p)
    {
        float deg = std::atan2(p.y - from.y, p.x - from.x) * 180.f / kPi;
        return deg < 0.f ? deg + 360.f : deg;
    }

    bool Near(float a, float b, float tol)
    {
        return std::fabs(a - b) <= tol;
    }
}

int main()
{
    // ---- the slice, the ids, the wave -------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(SmDoan::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmDoan::kSpellSlice.last));
    CHECK(SmDoan::kSpellSlice.first == 212670 && SmDoan::kSpellSlice.last == 212709);
    CHECK(SPELL_DN_ARCANE_BUBBLE == 212670);
    CHECK(SPELL_DN_FLAMESTRIKE == 212686);
    CHECK(SPELL_DN_FLAMESTRIKE - SPELL_DN_ARCANE_BUBBLE == 16);     // seventeen spells, contiguous from the slice start
    CHECK(SPELL_DN_MARK == 212680 && SPELL_DN_POOL == 212684 && SPELL_DN_DETONATION_CAST == 212671);
    CHECK(SPELL_DN_DETONATION_CAST_HEROIC == 212687 && kSpellSlice.Contains(SPELL_DN_DETONATION_CAST_HEROIC));
    // Arcanist Doan spawns kDoanSpawn, inside the arena.
    CHECK(DoanArena().Contains(kDoanSpawn.XY(), kDoanSpawn.z));
    CHECK(ArenaFor(BOSS_DOAN).Contains(kDoanSpawn.XY(), kDoanSpawn.z));
    CHECK(!IsWave2Boss(BOSS_DOAN));
    CHECK(HardModeKillSlot(BOSS_DOAN) == BOSS_HERESY);
    // His ids are the header's (S0): the anchor, the seal.
    CHECK(NPC_DOAN == 6487 && NPC_SM_ARCANE_ANCHOR == 300919 && GO_SM_CHAMBER_SEAL == 301319);

    // ---- texts: 0-1 stock, 2-3 D8H's, 4-5 this WP's (the range in the shared header must reach 5) -------------------
    CHECK(SAY_AGGRO == 0 && SAY_BUBBLE == 1 && SAY_HERESY == 2 && SAY_RISE_PURGED == 3);
    CHECK(EMOTE_SEAL == 4 && EMOTE_OVERLOADED == 5);

    // ---- the chamber ------------------------------------------------------------------------------------------------
    // The outline is convex and clockwise, about 990 sq yd (1,164 of floor less the 1.5 yd inset).
    {
        float area2 = 0.f;
        for (std::size_t i = 0; i < kChamberOutline.size(); ++i)
        {
            Vec2 const a = kChamberOutline[i];
            Vec2 const b = kChamberOutline[(i + 1) % kChamberOutline.size()];
            area2 += a.x * b.y - b.x * a.y;
            Vec2 const c = kChamberOutline[(i + 2) % kChamberOutline.size()];
            CHECK((b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x) <= 0.f);      // a right turn at every corner
        }
        CHECK(area2 < 0.f);
        CHECK(Near(-area2 / 2.f, 986.f, 1.f));
        // every outline corner is in the arena (the leash frame holds the whole floor)
        for (Vec2 const& p : kChamberOutline)
            CHECK(DoanArena().Contains(p, kChamberCenter.z));
    }
    CHECK(InChamberOutline(kChamberCenter.XY()));
    CHECK(InChamberOutline(kDoanSpawn.XY()));
    CHECK(DoanArena().Contains(kChamberCenter.XY(), kChamberCenter.z));
    // P2 (the instance's Library -> Armory portal) stands inside the chamber, clear of his corpse (F-1a moved it off
    // the center after R-1-KIT m-3: kPortalBossClearance from his spawn).
    CHECK(InChamberOutline(kPortals[2].spot.XY()));
    CHECK(Dist(kPortals[2].spot.XY(), kDoanSpawn.XY()) >= kPortalBossClearance);
    CHECK(kPortals[2].openSlot == BOSS_DOAN);
    // The outside of the outline is outside: the doorway, the outer hall, behind the walls.
    CHECK(!InChamberOutline({ 170.f, -429.f }));
    CHECK(!InChamberOutline({ 148.f, -405.f }));
    CHECK(!InChamberOutline({ 148.f, -452.f }));
    CHECK(!InChamberOutline({ 128.f, -429.f }));

    // ---- DN1 the anchor spots ---------------------------------------------------------------------------------------
    // The first three are the NAVMESH spots (section 3.5 row D8, 3.8).
    CHECK(Near(kAnchorSpots[0].x, 148.3f, 0.01f) && Near(kAnchorSpots[0].y, -413.7f, 0.01f));
    CHECK(Near(kAnchorSpots[1].x, 135.3f, 0.01f) && Near(kAnchorSpots[1].y, -436.2f, 0.01f));
    CHECK(Near(kAnchorSpots[2].x, 161.3f, 0.01f) && Near(kAnchorSpots[2].y, -436.2f, 0.01f));
    for (std::uint32_t i = 0; i < kAnchorSpotCount; ++i)
    {
        Point3 const& s = kAnchorSpots[i];
        // on the chamber floor and in the arena
        CHECK(InChamberOutline(s.XY()));
        CHECK(DoanArena().Contains(s.XY(), s.z));
        // the outer ring at 15 yd, the inner at 9 yd, round his spawn
        float const ring = i < 6 ? kAnchorRingYd : kAnchorInnerRingYd;
        CHECK(Near(Dist(s.XY(), kDoanSpawn.XY()), ring, 0.1f));
        // apart from every other spot by more than a body and a melee reach
        for (std::uint32_t j = i + 1; j < kAnchorSpotCount; ++j)
            CHECK(Dist(s.XY(), kAnchorSpots[j].XY()) > 8.f);
    }
    // 120 degrees apart (90, 210, 330), then 270, 30, 150 (the ring of six at 60 degrees)
    {
        float const expected[6] = { 90.f, 210.f, 330.f, 270.f, 30.f, 150.f };
        for (std::uint32_t i = 0; i < 6; ++i)
            CHECK(Near(BearingDeg(kDoanSpawn.XY(), kAnchorSpots[i].XY()), expected[i], 0.6f));
        for (std::uint32_t i = 6; i < 12; ++i)
            CHECK(Near(BearingDeg(kDoanSpawn.XY(), kAnchorSpots[i].XY()), float(i - 6) * 60.f, 0.6f)
                || Near(BearingDeg(kDoanSpawn.XY(), kAnchorSpots[i].XY()), 360.f, 0.6f));
    }

    // ---- DN0 the seal -----------------------------------------------------------------------------------------------
    // The seal stands in the doorway (outside the arena box, x 169-172), the entry spot inside the arena, 5 yd in.
    CHECK(!DoanArena().Contains(kSealSpot.XY(), kSealSpot.z));
    CHECK(kSealSpot.x > 169.f && kSealSpot.x < 172.f);
    CHECK(kSealSpot.y > -431.f && kSealSpot.y < -428.f);
    CHECK(DoanArena().Contains(kSealEntry.XY(), kSealEntry.z));
    CHECK(Near(Dist(kSealSpot.XY(), kSealEntry.XY()), 5.3f, 0.1f));
    CHECK(WingOf(kSealSpot.XY()) == 2 && WingOf(kSealEntry.XY()) == 2 && WingOf(kDoanSpawn.XY()) == 2);
    // about 4 yd wide and tall (GODI 523 is 9.5 wide and 9.2 tall at size 1); the doorway is 1.5-2.8 yd
    CHECK(kSealSize * 9.5f > 3.5f && kSealSize * 9.5f < 4.5f);
    CHECK(kSealSize * 9.2f > 3.5f && kSealSize * 9.2f < 4.5f);
    CHECK(kSealDisplay == 523);
    // the entry faces into the chamber (south, -x)
    CHECK(Near(kSealEntryFacing, kPi, 0.01f));
    // Library section 2 ends on Doan; its door list names the seal
    CHECK(kSections[1].endSlot == BOSS_DOAN && kSections[1].doors[0] == GO_SM_CHAMBER_SEAL);

    // ---- the beats --------------------------------------------------------------------------------------------------
    CHECK(kBubbleBeat(false).firstMs == 20000 && kBubbleBeat(false).everyMs == 35000);
    CHECK(kBubbleBeat(true).firstMs == 20000 && kBubbleBeat(true).everyMs == 30000);
    CHECK(kExplosionBeat(false).firstMs == 8000 && kExplosionBeat(false).everyMs == 12000);
    CHECK(kExplosionBeat(true).firstMs == 8000 && kExplosionBeat(true).everyMs == 12000);
    CHECK(kMarkBeat(false).firstMs == 15000 && kMarkBeat(false).everyMs == 20000);
    CHECK(kMarkBeat(true).firstMs == 15000 && kMarkBeat(true).everyMs == 20000);
    CHECK(kFlamestrikeBeat.firstMs == 10000 && kFlamestrikeBeat.everyMs == 15000);
    // F-1d n5: a refused Flamestrike retries on a short beat, not every map tick.
    CHECK(kFlamestrikeRetryMs >= 500 && kFlamestrikeRetryMs * 5 <= kFlamestrikeBeat.everyMs);
    // The build spec's fight: normal about 74 s holds two bubbles (20, 55 s); heroic about 89 s three (20, 50, 80 s).
    CHECK(kBubbleBeat(false).firstMs + kBubbleBeat(false).everyMs < 74000);
    CHECK(kBubbleBeat(false).firstMs + 2 * kBubbleBeat(false).everyMs > 74000);
    CHECK(kBubbleBeat(true).firstMs + 2 * kBubbleBeat(true).everyMs < 89000);
    // a bubble's window and Overloaded end before the next bubble
    CHECK(DetonationCastMsFor(false) + kOverloadedMs < kBubbleBeat(false).everyMs);
    CHECK(DetonationCastMsFor(true) + kOverloadedMs < kBubbleBeat(true).everyMs);
    // HANDOFF s10 option D: heroic's bar is 14 s on its own spell, normal keeps 10 s on 212671.
    CHECK(DetonationCastMsFor(false) == 10000 && DetonationCastMsFor(true) == 14000);
    CHECK(DetonationBarSpellFor(false) == SPELL_DN_DETONATION_CAST);
    CHECK(DetonationBarSpellFor(true) == SPELL_DN_DETONATION_CAST_HEROIC);

    // ---- the tuning -------------------------------------------------------------------------------------------------
    CHECK(kDetonationCastMs == 10000 && kExplosionCastMs == 2000 && kFlamestrikeCastMs == 2500 && kMarkMs == 5000);
    CHECK(kDetonationPct(false) == 75.f && kDetonationPct(true) == 130.f);
    CHECK(kExplosionPct(false) == 30.f && kExplosionPct(true) == 45.f && kExplosionRadiusYd == 10.f);
    CHECK(kMarkOthersPct(false) == 35.f && kMarkOthersPct(true) == 45.f);
    CHECK(kMarkSelfPct(false) == 15.f && kMarkSelfPct(true) == 20.f);
    CHECK(kMarkCount(false) == 2 && kMarkCount(true) == 3 && kMarkRadiusYd == 8.f);
    CHECK(kScorchedPct(false) == 6.f && kScorchedPct(true) == 10.f && kScorchedRadiusYd == 5.f);
    CHECK(kPoolPct == 10.f && kPoolRadiusYd == 3.f && kPoolLifeMs == 30000 && kPoolFormMs == 1000);
    CHECK(kFlamestrikePct == 40.f);
    CHECK(kOverloadedMs == 10000 && kOverloadedDamageTakenPct == 50.f);
    // A failure is survivable at full health on normal (75%), lethal on heroic (130%, hub ruling 28).
    CHECK(kDetonationPct(false) < 100.f && kDetonationPct(true) > 100.f);
    // Hits against their warnings (shared doc ladder): the Explosion 30% on a 2 s bar, the Mark 35% on 5 s.
    CHECK(kExplosionPct(false) <= 40.f);

    // ---- rules ------------------------------------------------------------------------------------------------------
    // DN1 anchors: 3 (heroic 4), +1 per miss, normal cap 5, heroic none; the hard mode's extras count; never past
    // the spots.
    CHECK(AnchorCount(false, 0, 0) == 3);
    CHECK(AnchorCount(false, 1, 0) == 4);
    CHECK(AnchorCount(false, 2, 0) == 5);
    CHECK(AnchorCount(false, 5, 0) == 5);
    CHECK(AnchorCount(true, 0, 0) == 4);
    CHECK(AnchorCount(true, 2, 0) == 6);
    CHECK(AnchorCount(true, 1, 3) == 8);
    CHECK(AnchorCount(true, 6, 6) == kAnchorSpotCount);
    // DN1a patches: 2 per miss, normal cap 4.
    CHECK(PatchesToLay(false, 0) == 2);
    CHECK(PatchesToLay(false, 2) == 2);
    CHECK(PatchesToLay(false, 3) == 1);
    CHECK(PatchesToLay(false, 4) == 0);
    CHECK(PatchesToLay(true, 0) == 2 && PatchesToLay(true, 10) == 2);
    // The bubble and Overloaded hold the other beats.
    CHECK(BeatsHeld(true, false) && BeatsHeld(false, true) && BeatsHeld(true, true) && !BeatsHeld(false, false));
    // The bubble breaks only when every anchor it raised is dead.
    CHECK(BubbleBroken(3, 0) && !BubbleBroken(3, 1) && !BubbleBroken(0, 0) && BubbleBroken(5, 0));
    // Space math (normal worst case: 4 patches of 78.5 sq yd, about 27% of the chamber's 1,164).
    CHECK(Near(4.f * kPi * kScorchedRadiusYd * kScorchedRadiusYd / 1164.f, 0.27f, 0.01f));
    // The patch ring stays inside the chamber's 15 yd clear radius.
    CHECK(kScorchedMaxRangeYd + 0.f <= 15.f && kScorchedMinRangeYd < kScorchedMaxRangeYd);

    // ---- rule 20: the anchor window against the group's damage ------------------------------------------------------
    // HANDOFF s10 option D (pending the user): normal 3 x 1.2k = 3.6k at the effective 666 is about 5.4 s of the 10 s
    // bar; bots at about half need about 10.8 s (plus walking: still short, designer question in the F-2w report).
    CHECK(kAnchorHealthNormal == 1200 && kAnchorHealthHeroic == 5000);
    CHECK(Near(AnchorSeconds(false, kEffectiveDpsNormal), 5.41f, 0.05f));
    CHECK(AnchorSeconds(false, kEffectiveDpsNormal) < DetonationCastMsFor(false) / 1000.f);
    CHECK(Near(AnchorSeconds(false, kEffectiveDpsNormal / 2), 10.81f, 0.05f));
    // Heroic: 4 x 5k = 20k at the effective 3,145 is about 6.4 s of the 14 s bar (no walking counted); bots at about
    // 700 on adds need about 28.6 s.
    CHECK(Near(AnchorSeconds(true, kEffectiveDpsHeroic), 6.36f, 0.05f));
    CHECK(AnchorSeconds(true, kEffectiveDpsHeroic) < DetonationCastMsFor(true) / 1000.f);
    CHECK(Near(AnchorSeconds(true, kBotAddDpsHeroic), 28.57f, 0.05f));
    CHECK(AnchorSeconds(true, 0) == 0.f);

    // ---- the clock --------------------------------------------------------------------------------------------------
    {
        BeatClock clock;
        CHECK(!clock.On() && !clock.Due(100000));
        clock.Start(0, 20000);
        CHECK(!clock.Due(19999) && clock.Due(20000));
        clock.Fired(21500, 35000);      // a bubble held 1.5 s by an Explosion bar keeps its cadence
        CHECK(clock.DueMs() == 55000);
        clock.Fired(200000, 35000);     // never in the past
        CHECK(clock.DueMs() == 235000);
        clock.Stop();
        CHECK(!clock.Due(300000));
    }

    return Report("sm_doan_test");
}
