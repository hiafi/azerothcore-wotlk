// Host tests for FineousLogic.h (D10: Fineous Darkvire and the Guzzler rope).
#include "FineousLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>

using namespace BlackrockDepthsRework;
using namespace BrdFineous;

namespace
{
    float Dist(Point3 a, Point3 b)
    {
        return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrdFineous::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrdFineous::kSpellSlice.last));
    CHECK(BrdFineous::kSpellSlice.first == 211120);
    CHECK(BrdFineous::kSpellSlice.last == 211139);
    CHECK(SPELL_FD_SHODDY_COLLAPSE == 211120);
    CHECK(SPELL_FD_HOLY_LIGHT == 211121);
    CHECK(SPELL_FD_PILLAR_RISE == 211122);
    CHECK(SPELL_FD_COLLAPSE_DUST == 211123);
    for (std::uint32_t id : { SPELL_FD_SHODDY_COLLAPSE, SPELL_FD_HOLY_LIGHT, SPELL_FD_PILLAR_RISE,
        SPELL_FD_COLLAPSE_DUST })
        CHECK(BrdFineous::kSpellSlice.Contains(id));
    // The stock spells he keeps are the SmartAI's.
    CHECK(SPELL_FD_DEVOTION_AURA == 8258);
    CHECK(SPELL_FD_HOLY_STRIKE == 13953);
    CHECK(SPELL_FD_KICK == 11978);
    CHECK(SPELL_FD_SEAL_OF_RECKONING == 15346);

    // His slot is the tracking one: no credit, section 2.
    CHECK(BOSS_FINEOUS == 7);
    CHECK(IsTrackingOnlySlot(BOSS_FINEOUS));
    CHECK(SectionOf(BOSS_FINEOUS) == 2);
    CHECK(ArenaFor(BOSS_FINEOUS).Contains(kFineousSpawn.XY(), kFineousSpawn.z));

    // FD1: 25% / 40%, every 15 s / 12 s, 3 s warning, 6 yd; the first comes before the first beat.
    CHECK(kShoddyPct(false) == 25.f);
    CHECK(kShoddyPct(true) == 40.f);
    CHECK(kShoddyEveryMs(false) == 15000);
    CHECK(kShoddyEveryMs(true) == 12000);
    CHECK(kShoddyWarnMs == 3000);
    CHECK(kShoddyRadiusYd == 6.f);
    CHECK(kShoddyFirstMs(false) < kShoddyEveryMs(false));
    CHECK(kShoddyFirstMs(true) < kShoddyEveryMs(true));
    CHECK(kShoddyObjectBackstopMs > kShoddyWarnMs);
    CHECK(TAG_SHODDY_CONSTRUCTION == 1);

    // The stock cadences.
    CHECK(kHolyStrikeFirstMs == 3000);
    CHECK(kHolyStrikeMinMs == 6000);
    CHECK(kHolyStrikeMaxMs == 8500);
    CHECK(kKickFirstMs == 12000);
    CHECK(kKickEveryMs == 7000);
    CHECK(KickTarget(true, 0.f));
    CHECK(KickTarget(true, 5.f));
    CHECK(!KickTarget(true, 5.1f));
    CHECK(!KickTarget(false, 2.f));
    CHECK(!KickTarget(true, -1.f));

    // FD2: Holy Light at 60% and at 40%, each once, the lower after the first; Seal at 20%, once.
    CHECK(HolyLightsDue(100.f, 0) == 0);
    CHECK(HolyLightsDue(60.1f, 0) == 0);
    CHECK(HolyLightsDue(60.f, 0) == 1);
    CHECK(HolyLightsDue(59.f, 0) == 1);
    CHECK(HolyLightsDue(40.f, 0) == 3);
    CHECK(HolyLightsDue(30.f, 1) == 2);
    CHECK(HolyLightsDue(30.f, 3) == 0);
    CHECK(HolyLightsDue(70.f, 3) == 0);
    CHECK(NextHolyLight(100.f, 0) == -1);
    CHECK(NextHolyLight(55.f, 0) == 0);
    CHECK(NextHolyLight(55.f, 1) == -1);
    CHECK(NextHolyLight(10.f, 0) == 0);     // a hit past both: the 60% one first
    CHECK(NextHolyLight(10.f, 1) == 1);
    CHECK(NextHolyLight(10.f, 3) == -1);
    CHECK(kHolyLightHealPct == 4.f);
    CHECK(kHolyLightCastMs == 2500);
    // 4% of 50,000 / 80,000 is 2,000 / 3,200: the stock 467-541 on 13,734 was 3.4-3.9%.
    CHECK(kHolyLightHealPct > 467.f / 13734.f * 100.f);
    CHECK(kHolyLightHealPct > 541.f / 13734.f * 100.f);
    CHECK(kHolyLightHealPct < 541.f / 13734.f * 100.f + 0.5f);
    CHECK(!SealDue(21.f, false));
    CHECK(SealDue(20.f, false));
    CHECK(!SealDue(5.f, true));

    // The ramp: the spawn, the whole patrol and the adds' side are inside the leash frame; the corners are inside too.
    DungeonKit::Arena const ramp = RampArena();
    CHECK(ramp.Contains(kFineousSpawn.XY(), kFineousSpawn.z));
    for (Point3 const& p : kPatrol)
        CHECK(ramp.Contains(p.XY(), p.z));
    CHECK(kPatrol.size() == 18);
    CHECK(Dist(kPatrol[0], kFineousSpawn) < 0.5f);
    // The Doomforge Craftsmen's spawns (x 969-1002, y -328 to -376, z -65 to -71) stand on it.
    CHECK(ramp.Contains({ 1002.15f, -351.5f }, -65.f));
    CHECK(ramp.Contains({ 993.4f, -375.6f }, -66.6f));
    CHECK(ramp.Contains({ 979.3f, -328.2f }, -71.1f));
    // The stub's box began at x 925 and cut the patrol's far end; the widened FineousArena() (x 888-1012) holds it.
    CHECK(FineousArena().Contains(kPatrol[8].XY(), kPatrol[8].z));
    CHECK(ramp.Contains(kPatrol[8].XY(), kPatrol[8].z));
    // Not on it: the Black Anvil's causeway (Incendius, z -72, 80 yd west), the lava, the floor above the ramp.
    CHECK(!ramp.Contains({ 893.5f, -267.1f }, -71.9f));
    CHECK(!ramp.Contains({ 963.f, -344.f }, -91.f));
    CHECK(!ramp.Contains({ 940.f, -380.f }, -30.f));
    // Patrol length, one way (waypoints 1-9): 151 yd on the waypoint chords, NAVMESH 2.4's walked 146 yd (2D).
    float length = 0.f;
    for (std::size_t i = 1; i < 9; ++i)
        length += Dist(kPatrol[i - 1], kPatrol[i]);
    CHECK(length > 140.f && length < 160.f);
    // The way back ends beside the start (the path loops there and back).
    CHECK(Dist(kPatrol[17], kPatrol[0]) < 6.f);
    // The climb is about 21.5 yd (NAVMESH 2.4: z -71.1 to -49.6).
    CHECK(std::fabs((kPatrol[8].z - kPatrol[0].z) - 21.8f) < 1.f);

    // The two narrow corners: the pillar never picks a player there.
    CHECK(OnCorner({ 978.f, -370.f }));
    CHECK(OnCorner({ 938.f, -408.f }));
    CHECK(OnCorner({ 975.f, -376.f }));
    CHECK(OnCorner({ 944.f, -412.f }));
    CHECK(!OnCorner({ 963.f, -344.f }));                // the spawn: a wide leg
    CHECK(!OnCorner({ 963.f, -395.f }));                // the middle of the second leg
    CHECK(!OnCorner({ 905.f, -382.f }));                // the far end
    CHECK(!OnCorner({ 986.f, -352.f }));
    CHECK(kCorners.size() == 2);
    // The discs cover the narrow stretches NAVMESH names (clearance under 3.3 within 8 yd of the corner points).
    CHECK(kCornerRadiusYd >= 8.f);
    // Both corners lie on the patrol's legs.
    for (CornerDisc const& c : kCorners)
    {
        float nearest = 1e9f;
        for (Point3 const& p : kPatrol)
            nearest = std::min(nearest, DungeonKit::Distance(p.XY(), c.center));
        CHECK(nearest < 12.f);
    }

    // The rope: the climb spot is Incendius's spawn; the landing is past the Bar Door.
    CHECK(kRopeClimbSpot.x == kIncendiusSpawn.x && kRopeClimbSpot.y == kIncendiusSpawn.y);
    CHECK(kRopeHang.x == kRopeClimbSpot.x && kRopeHang.y == kRopeClimbSpot.y && kRopeHang.z == kRopeClimbSpot.z);
    CHECK(kRopeLanding.x == kRopeTop.x && kRopeLanding.y == kRopeTop.y && kRopeLanding.z == kRopeTop.z);
    CHECK(kRopeLanding.z - kRopeClimbSpot.z > 21.f && kRopeLanding.z - kRopeClimbSpot.z < 23.f);     // 22 yd up
    CHECK(DungeonKit::Distance(kRopeClimbSpot.XY(), kRopeLanding.XY()) > 46.f);                        // 47 yd across
    CHECK(DungeonKit::Distance(kRopeClimbSpot.XY(), kRopeLanding.XY()) < 48.f);
    CHECK(kRopeLanding.o > 0.f && kRopeLanding.o < 6.2832f);
    // The landing is nowhere near the ramp (a different floor of the city) or the lava.
    CHECK(!ramp.Contains(kRopeLanding.XY(), kRopeLanding.z));
    // The spot is a disc on the causeway's bulge; the z tolerance excludes the lake and the walkway above.
    CHECK(kRopeSpotRadiusYd == 12.f);
    CHECK(kRopeSpotZToleranceYd < 22.f);

    // The use spell: only in the Depths, once, at the spot.
    std::uint32_t const depths = kMapBlackrockDepths;
    CHECK(RopeUseRefusal(depths, true, ROPE_NONE, 0.f, 0.f) == RopeRefusal::None);
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 11.9f, 5.9f) == RopeRefusal::None);
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 11.9f, -5.9f) == RopeRefusal::None);
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 12.1f, 0.f) == RopeRefusal::NotAtTheSpot);
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 5.f, 6.5f) == RopeRefusal::NotAtTheSpot);
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 5.f, -38.f) == RopeRefusal::NotAtTheSpot);   // down in the lava
    CHECK(RopeUseRefusal(depths, true, ROPE_DROPPED, 5.f, 22.f) == RopeRefusal::NotAtTheSpot);    // the walkway above
    CHECK(RopeUseRefusal(depths, true, ROPE_PLACED, 0.f, 0.f) == RopeRefusal::AlreadyHung);
    CHECK(RopeUseRefusal(depths, true, ROPE_PLACED, 500.f, 0.f) == RopeRefusal::AlreadyHung);
    CHECK(RopeUseRefusal(229, true, ROPE_NONE, 0.f, 0.f) == RopeRefusal::NotInDungeon);
    CHECK(RopeUseRefusal(depths, false, ROPE_NONE, 0.f, 0.f) == RopeRefusal::NotInDungeon);
    for (RopeRefusal why : { RopeRefusal::NotInDungeon, RopeRefusal::AlreadyHung, RopeRefusal::NotAtTheSpot })
        CHECK(RopeRefusalText(why)[0] != '\0');
    CHECK(RopeRefusalText(RopeRefusal::None)[0] == '\0');

    // The drop: once per instance, never while one hangs; the state moves one way only.
    CHECK(RopeDropAllowed(ROPE_NONE));
    CHECK(!RopeDropAllowed(ROPE_DROPPED));
    CHECK(!RopeDropAllowed(ROPE_PLACED));
    CHECK(RopeChangeAllowed(ROPE_NONE, ROPE_DROPPED));
    CHECK(RopeChangeAllowed(ROPE_DROPPED, ROPE_PLACED));
    CHECK(RopeChangeAllowed(ROPE_NONE, ROPE_PLACED));
    CHECK(!RopeChangeAllowed(ROPE_PLACED, ROPE_DROPPED));
    CHECK(!RopeChangeAllowed(ROPE_PLACED, ROPE_NONE));

    // The hanging rope shows and works only when placed, within reach.
    CHECK(!RopeObjectShown(ROPE_NONE));
    CHECK(!RopeObjectShown(ROPE_DROPPED));
    CHECK(RopeObjectShown(ROPE_PLACED));
    CHECK(RopeClickAllowed(ROPE_PLACED, 3.f));
    CHECK(RopeClickAllowed(ROPE_PLACED, kRopeClickRangeYd));
    CHECK(!RopeClickAllowed(ROPE_PLACED, kRopeClickRangeYd + 0.1f));
    CHECK(!RopeClickAllowed(ROPE_DROPPED, 1.f));
    CHECK(!RopeClickAllowed(ROPE_NONE, 1.f));

    // The rope item and the GOs are the reserved ids.
    CHECK(kItemGuzzlerRope == 70622);
    CHECK(GO_BRD_HANGING_ROPE == 301282);
    CHECK(GO_BRD_SHODDY_PILLAR == 301283);
    CHECK(DATA_GUZZLER_ROPE == 59);
    CHECK(NPC_FRANCLORNS_SPIRIT == 9542);
    CHECK(NPC_FINEOUS == 9056);
    CHECK(TEXT_FRANCLORN_IRONFEL == 1);
    CHECK(kFranclornLifeMs >= 8000);

    // The saved rope survives the instance's save string (the hanging rope is back after a reload).
    for (std::uint32_t state : { ROPE_NONE, ROPE_DROPPED, ROPE_PLACED })
    {
        BrdSave save;
        save.rope = state;
        BrdSave loaded;
        CHECK(ParseBrdSave(FormatBrdSave(save), loaded));
        CHECK(loaded.rope == state);
        CHECK(RopeObjectShown(loaded.rope) == (state == ROPE_PLACED));
    }

    // The beat clock: starts, fires on time, and never falls behind.
    {
        FightClock clock;
        CHECK(!clock.On());
        CHECK(!clock.Due(100000));
        clock.Start(1000, 8000);
        CHECK(clock.On());
        CHECK(!clock.Due(8999));
        CHECK(clock.Due(9000));
        clock.Fired(9000, 15000);
        CHECK(clock.DueMs() == 24000);
        CHECK(!clock.Due(23999));
        CHECK(clock.Due(24000));
        // A stall past the next beat does not fire a burst.
        clock.Fired(60000, 15000);
        CHECK(clock.DueMs() == 75000);
        clock.Stop();
        CHECK(!clock.Due(1000000));
    }

    return Report("brd_fineous_test");
}
