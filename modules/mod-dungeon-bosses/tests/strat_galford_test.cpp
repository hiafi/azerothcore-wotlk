// Host tests for GalfordLogic.h (S6: Archivist Galford (10811)): the ids, the build spec numbers (ST 1707-1765), the
// union tick and Scorched (crossing one puddle about 18%, eight seconds in fire kills), Kindled on Pyroblast, the walls
// (the Pyre and the north wall keep 5 yd off the archive, the tank spots and the grip landings; they seal the hall
// ends), the hall outline, the gust cut short of the Pyre, the puddle looks, the tank rule and the cast queue.
#include "DungeonKitFlow.h"
#include "GalfordLogic.h"
#include "check.h"
#include <cmath>
#include <optional>
#include <span>
#include <vector>

using namespace StratholmeRework;
using namespace StratGalford;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float PolygonArea(std::span<Vec2 const> poly)
    {
        float twice = 0.f;
        for (std::size_t i = 0; i < poly.size(); ++i)
        {
            Vec2 const& a = poly[i];
            Vec2 const& b = poly[(i + 1) % poly.size()];
            twice += a.x * b.y - b.x * a.y;
        }
        return std::fabs(twice) * 0.5f;
    }

    struct Start
    {
        std::uint32_t cast;
        std::uint64_t at;
    };

    // Plays his cast queue for `endMs` the way the AI drives it (one decision every 100 ms; a started cast reschedules
    // itself at its cadence and holds him for its cast time).
    std::vector<Start> Simulate(bool heroic, std::uint64_t endMs)
    {
        DungeonKit::CastQueue queue;
        queue.Schedule(CAST_PYROBLAST, kPyroFirstMs, kPriorityPyro);
        queue.Schedule(CAST_NOVA, kNovaFirstMs, kPriorityNova);
        if (heroic)
            queue.Schedule(CAST_WINDS, kWindsFirstMs, kPriorityWinds);
        std::vector<Start> out;
        for (std::uint64_t now = 0; now <= endMs; now += 100)
        {
            std::optional<std::uint32_t> const next = queue.Next(now);
            if (!next)
                continue;
            out.push_back({ *next, now });
            switch (*next)
            {
                case CAST_PYROBLAST:
                    queue.Started(CAST_PYROBLAST, now, kPyroCastMs);
                    queue.Schedule(CAST_PYROBLAST, now + kPyroEveryMs, kPriorityPyro);
                    break;
                case CAST_NOVA:
                    queue.Started(CAST_NOVA, now, kNovaCastMs);
                    queue.Schedule(CAST_NOVA, now + kNovaEveryMs, kPriorityNova);
                    break;
                case CAST_WINDS:
                    queue.Started(CAST_WINDS, now, kWindsCastMs);
                    queue.Schedule(CAST_WINDS, now + kWindsEveryMs, kPriorityWinds);
                    break;
                default:
                    break;
            }
        }
        return out;
    }

    std::uint32_t CastMs(std::uint32_t cast)
    {
        return cast == CAST_PYROBLAST ? kPyroCastMs : cast == CAST_NOVA ? kNovaCastMs : kWindsCastMs;
    }
}

int main()
{
    // --- Ids ---------------------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(SPELL_GF_HOLY_FIRE == 206520);
    CHECK(SPELL_GF_WALL_LOOK == 206535);
    for (std::uint32_t id = SPELL_GF_HOLY_FIRE; id <= SPELL_GF_WALL_LOOK; ++id)
        CHECK(kSpellsGalford.Contains(id));
    CHECK(!kSpellsGalford.Contains(SPELL_ST_CROSSED_THE_LINE));     // the strike is the shared one
    CHECK(kSpellsShared.Contains(SPELL_ST_CROSSED_THE_LINE));
    CHECK(kCreaturesWave2.Contains(NPC_ST_HOLY_FIRE_PUDDLE) && kCreaturesWave2.Contains(NPC_ST_PYRE_WALL));
    CHECK(BossOfEntry(NPC_GALFORD) == std::optional<std::uint32_t>(BOSS_GALFORD));

    // --- Build spec numbers ------------------------------------------------------------------------------------------
    CHECK(kHolyFireFirstMs == 5000 && kHolyFireEveryMs(false) == 8000 && kHolyFireEveryMs(true) == 12000);
    CHECK(kHolyFireCount(false) == 1 && kHolyFireCount(true) == 3);
    CHECK(kHolyFireBurnMs == 6000 && Near(kHolyFireRadius, 4.f) && Near(kHolyFireLandingPct, 30.f));
    CHECK(Near(kHolyFireTickHundredths * (kHolyFireBurnMs / kHolyFireTickMs) / 100.f, kHolyFireBurnPct, 0.05f));
    CHECK(kPyroFirstMs == 15000 && kPyroEveryMs == 20000 && kPyroCastMs == 4000);
    CHECK(Near(kPyroPct(false), 35.f) && Near(kPyroPct(true), 45.f));
    CHECK(Near(kPyroPuddleRadius(false), 6.f) && Near(kPyroPuddleRadius(true), 8.f));
    CHECK(kNovaFirstMs == 12000 && kNovaEveryMs == 15000 && kNovaCastMs == 2000);
    CHECK(Near(kNovaRadius, 10.f) && Near(kNovaPct, 30.f) && Near(kNovaPuddleRadius, 5.f));
    CHECK(kWindsFirstMs == 20000 && kWindsEveryMs == 25000 && kWindsCastMs == 2000 && Near(kWindsPushYd, 8.f));
    CHECK(kFireArmMs == 1000 && kFireTickMs == 1000 && kScorchedFadeMs == 4000);

    // --- GF7 / GF8 the union tick and Scorched -----------------------------------------------------------------------
    CHECK(Near(FireTickPct(0), 8.f));
    CHECK(Near(FireTickPct(1), 10.f));
    CHECK(Near(FireTickPct(4), 16.f));
    CHECK(Near(FireBurnPct(2), 18.f));                  // ST: crossing one puddle costs about 18%
    CHECK(FireBurnPct(7) < 100.f);                      // seven seconds in fire: still standing
    CHECK(FireBurnPct(8) >= 100.f);                     // ST: standing in fire for 8 s kills
    CHECK(Near(FireTickPct(kScorchedMaxStacks + 5), FireTickPct(kScorchedMaxStacks)));     // the cap holds

    // --- GF9 Kindled -------------------------------------------------------------------------------------------------
    CHECK(Near(PyroPct(false, false), 35.f));
    CHECK(Near(PyroPct(false, true), 43.75f));
    CHECK(Near(PyroPct(true, true), 56.25f));
    CHECK(Near(kKindledDamageTakenPct, -50.f) && Near(kKindledDamageDonePct, 25.f));
    CHECK(kKindledPollMs < kKindledAuraMs);             // refreshed well before it runs out while he stands in fire

    // --- GF10 the walls ----------------------------------------------------------------------------------------------
    WallLine const pyre = PyreLine();
    WallLine const north = NorthLine();
    CHECK(Near(pyre.from.x, 3444.f) && Near(pyre.to.x, 3444.f));
    CHECK(Near(pyre.from.y, -3074.5f) && Near(pyre.to.y, -3101.5f));
    CHECK(Near(north.from.x, 3500.f) && Near(north.from.y, -3064.5f) && Near(north.to.y, -3101.5f));
    CHECK(Near(pyre.width, 2.f) && Near(north.width, 2.f));
    std::vector<KeepClear> const keep = WallKeepClear();
    CHECK(keep.size() == 2 + kTankSpots.size() + kGripLandings.size());
    CHECK(DungeonKit::KeepsClear(pyre, keep));          // the placement rule: 5 yd off the archive and tank spots
    CHECK(DungeonKit::KeepsClear(north, keep));
    // The measured line (x 3446) would not keep the archive's door clear: why the Pyre is drawn 2 yd south.
    WallLine const measured{ kGalfordPyre[0], kGalfordPyre[1], kWallWidthYd };
    CHECK(!DungeonKit::KeepsClear(measured, keep));
    CHECK(DungeonKit::CheckPlacement(pyre, keep).minYd >= 5.f);
    // Galford's spawn and the archive are on the fight's side of the Pyre, the north wall north of everything.
    CHECK(DungeonKit::WallClearance(pyre, kGalfordSpawn.XY()) > 5.f);
    CHECK(kGalfordSpawn.x > pyre.from.x && kGalfordSpawn.x < north.from.x);
    // The Pyre is crossed by a walk from the hall into Dathrohan's chamber; the arena's spots never stand in a strip.
    CHECK(DungeonKit::CrossesWall(pyre, { 3450.f, -3085.f }, { 3438.f, -3077.f }));
    CHECK(DungeonKit::CrossesWall(north, { 3495.f, -3080.f }, { 3505.f, -3080.f }));
    for (Vec2 const& p : kGripLandings)
        CHECK(!DungeonKit::InsideWall(pyre, p) && !DungeonKit::InsideWall(north, p));
    // The fire stalkers: one every 6 yd or less, along the line, inside its length.
    std::vector<Vec2> const pyreSpots = WallStalkerSpots(pyre);
    std::vector<Vec2> const northSpots = WallStalkerSpots(north);
    CHECK(pyreSpots.size() == 5);                       // 27 yd
    CHECK(northSpots.size() == 7);                      // 37 yd
    for (Vec2 const& p : pyreSpots)
        CHECK(DungeonKit::InsideWall(pyre, p));
    for (Vec2 const& p : northSpots)
        CHECK(DungeonKit::InsideWall(north, p));
    CHECK(Near(DungeonKit::Distance(pyreSpots[0], pyreSpots[1]), 27.f / 5.f));
    CHECK(WallStalkerSpots(WallLine{ { 0.f, 0.f }, { 0.f, 0.f }, 2.f }).empty());

    // --- The arena, the hall and the grip ----------------------------------------------------------------------------
    DungeonKit::Arena const guard = GuardArena();
    CHECK(guard.Contains(kGalfordSpawn.XY(), kGalfordSpawn.z));
    CHECK(GalfordArena().Contains(kGalfordSpawn.XY(), kGalfordSpawn.z));
    CHECK(!guard.Contains({ 3499.5f, -3080.f }, 135.4f));      // in the north wall's strip: gripped out at the pull
    CHECK(!guard.Contains({ 3444.f, -3085.f }, 135.2f));       // in the Pyre's strip
    CHECK(!guard.Contains({ 3423.47f, -3055.73f }, 136.8f));   // Dathrohan's chamber
    for (Vec2 const& p : kGripLandings)
    {
        CHECK(guard.Contains(p, kHallFloorZ));
        CHECK(InHallRoom(p));
        CHECK(DungeonKit::WallClearance(pyre, p) >= 5.f && DungeonKit::WallClearance(north, p) >= 5.f);
    }
    CHECK(Near(GripLanding({ 3510.f, -3080.f }).x, 3492.f));   // from the north: the north stand
    CHECK(Near(GripLanding({ 3423.f, -3055.f }).x, 3452.5f));  // from Dathrohan's chamber: the archive's mouth
    float const hallArea = PolygonArea(std::span<Vec2 const>(kHallRoom));
    CHECK(hallArea > 900.f && hallArea < 1400.f);              // the sealed floor is 1,439 with the archive and alcove
    for (Vec2 const& p : kHallRoom)
    {
        CHECK(DungeonKit::WallClearance(pyre, p) >= 1.9f);     // the room keeps 2 yd off both strips
        CHECK(DungeonKit::WallClearance(north, p) >= 1.9f);
        CHECK(guard.Contains(p, kHallFloorZ));
    }
    CHECK(!InHallRoom(kScarletArchive.XY()));
    CHECK(kArchiveRoom.Contains(kScarletArchive.XY()) && kArchiveRoom.Contains(kGalfordSpawn.XY()));
    CHECK(OnFightFloor(kGalfordSpawn.XY()));                   // the archive's drop area holds his spawn
    CHECK(OnFightFloor({ 3475.f, -3092.f }));                  // the alcove
    CHECK(!OnFightFloor({ 3438.f, -3077.f }));                 // Dathrohan's door
    for (Vec2 const& c : { Vec2{ kArchiveDrop.minX, kArchiveDrop.minY }, Vec2{ kArchiveDrop.maxX, kArchiveDrop.maxY },
        Vec2{ kAlcoveDrop.minX, kAlcoveDrop.minY }, Vec2{ kAlcoveDrop.maxX, kAlcoveDrop.maxY } })
        CHECK(guard.Contains(c, 136.8f));                      // both drop areas lie on the arena

    // --- GF11 the gust -----------------------------------------------------------------------------------------------
    CHECK(Near(GustDistance(3480.f), 8.f));                    // mid hall: the full throw
    CHECK(Near(GustDistance(3452.f), 5.f));                    // 7 yd north of the strip: cut to 5
    CHECK(Near(GustDistance(3448.f), 1.f));
    CHECK(Near(GustDistance(3447.5f), 0.f));                   // too close: no throw
    for (float x = 3445.5f; x <= 3500.f; x += 0.5f)
    {
        float const d = GustDistance(x);
        CHECK(d <= kWindsPushYd);
        if (d > 0.f)
        {
            Vec2 const from{ x, -3085.f };
            Vec2 const to{ x - d, -3085.f };
            CHECK(!DungeonKit::CrossesWall(pyre, from, to));   // never thrown across the Pyre (KT-2's finding)
            CHECK(DungeonKit::WallClearance(pyre, to) >= kGustMarginYd - 0.01f);
        }
    }
    CHECK(Near(KnockbackDistance(KnockbackSpeedXY(8.f)), 8.f));
    CHECK(Near(KnockbackDistance(KnockbackSpeedXY(3.f)), 3.f));
    CHECK(Near(KnockbackFlightS(), 1.f, 0.01f));               // the 1 s loss of control

    // --- GF7 the looks, GF9 the tank rule ----------------------------------------------------------------------------
    CHECK(PuddleLookFor(kHolyFireRadius) == SPELL_GF_PUDDLE_LOOK_4);
    CHECK(PuddleLookFor(kNovaPuddleRadius) == SPELL_GF_PUDDLE_LOOK_5);
    CHECK(PuddleLookFor(kPyroPuddleRadius(false)) == SPELL_GF_PUDDLE_LOOK_6);
    CHECK(PuddleLookFor(kPyroPuddleRadius(true)) == SPELL_GF_PUDDLE_LOOK_8);
    std::vector<PuddleSpot> const puddles{ { { 3470.f, -3070.f }, 5.f } };
    CHECK(ShouldPark({ 3470.f, -3070.f }, puddles));           // in it
    CHECK(ShouldPark({ 3476.4f, -3070.f }, puddles));          // 1.4 yd off its edge
    CHECK(!ShouldPark({ 3477.f, -3070.f }, puddles));
    CHECK(!ShouldPark({ 3470.f, -3070.f }, std::vector<PuddleSpot>{}));
    CHECK(kParkMinYd < kParkMaxYd && kParkHoldMs > kParkCheckMs);

    // --- The cast queue: never two casts at once, each on its cadence ------------------------------------------------
    for (bool const heroic : { false, true })
    {
        std::vector<Start> const starts = Simulate(heroic, 120000);
        CHECK(!starts.empty());
        for (std::size_t i = 1; i < starts.size(); ++i)
            CHECK(starts[i].at >= starts[i - 1].at + CastMs(starts[i - 1].cast));
        std::uint32_t pyro = 0;
        std::uint32_t nova = 0;
        std::uint32_t winds = 0;
        for (Start const& s : starts)
        {
            pyro += s.cast == CAST_PYROBLAST;
            nova += s.cast == CAST_NOVA;
            winds += s.cast == CAST_WINDS;
        }
        CHECK(pyro >= 5 && pyro <= 6);                         // every 20 s from 15 s
        CHECK(nova >= 6 && nova <= 8);                         // every 15 s from 12 s
        CHECK(heroic ? (winds >= 4 && winds <= 5) : winds == 0);
        CHECK(starts.front().cast == CAST_NOVA && starts.front().at == kNovaFirstMs);
    }
    CHECK(PyroYells(1) && !PyroYells(2) && PyroYells(3));

    return Report("strat_galford_test");
}
