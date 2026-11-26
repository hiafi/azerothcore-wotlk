// Host tests for BlyCrewLogic.h (CR: Sergeant Bly's crew): the slice, the factions and react states by mode, the rest
// spots by mode and stage (cross-checked against the instance's CrewModeFor), the crew's points on their rooms, the
// prisoner machine, Weegli's door walk, the floors, Murta's healing picks, the pool arrival and the timers; plus a
// scan of BlyCrew.cpp for the rules the engine half must keep (no assist timer, the betrayal as gossip option 0, every
// stock text group named, the crew's scripts registered).
#include "BlyCrewLogic.h"
#include "check.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace ZulFarrakRework;
using namespace ZfCrew;

namespace
{
    std::string ReadFile(std::filesystem::path const& path)
    {
        std::ifstream in(path);
        std::stringstream text;
        text << in.rdbuf();
        return text.str();
    }

    std::filesystem::path SourceDir()
    {
        return std::filesystem::path(__FILE__).parent_path().parent_path() / "src" / "ZulFarrak";
    }

    bool Near(Point3 const& a, Point3 const& b)
    {
        return a.x == b.x && a.y == b.y && a.z == b.z;
    }

    CrewContext Ctx(std::uint32_t stage, bool cages, std::uint32_t slot = DungeonKit::State::NotStarted,
        std::uint32_t path = CREW_PATH_OPEN)
    {
        CrewContext c;
        c.stage = stage;
        c.cagesOpen = cages;
        c.crewSlot = slot;
        c.path = path;
        return c;
    }
}

int main()
{
    // --- the slice ---
    CHECK(kSpellsShared.Contains(kSpellSlice.first));
    CHECK(kSpellsShared.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 213845 && kSpellSlice.last == 213859);

    // --- factions and react states (section 3.12) ---
    CHECK(FactionFor(CrewMode::Caged) == 35);
    CHECK(FactionFor(CrewMode::Prisoner) == 35);
    CHECK(FactionFor(CrewMode::Ally) == 495);
    CHECK(FactionFor(CrewMode::Gather) == 35);
    CHECK(FactionFor(CrewMode::Boss) == 41);
    CHECK(FactionFor(CrewMode::Yielded) == 35);
    CHECK(FactionFor(CrewMode::PoolAlly) == 35);
    CHECK(FactionFor(CrewMode::Gone) == 35);
    CHECK(FightsIn(CrewMode::Ally) && FightsIn(CrewMode::Boss));
    for (CrewMode mode : { CrewMode::Caged, CrewMode::Prisoner, CrewMode::Gather, CrewMode::Yielded,
        CrewMode::PoolAlly, CrewMode::Gone })
        CHECK(!FightsIn(mode));
    // Bly and Weegli talk until the fight; the others never
    CHECK(GossipIn(CREW_BLY, CrewMode::Gather) && GossipIn(CREW_WEEGLI, CrewMode::Caged));
    CHECK(GossipIn(CREW_BLY, CrewMode::Ally) && GossipIn(CREW_BLY, CrewMode::Caged));
    CHECK(!GossipIn(CREW_BLY, CrewMode::Boss) && !GossipIn(CREW_BLY, CrewMode::PoolAlly));
    CHECK(!GossipIn(CREW_WEEGLI, CrewMode::Gone) && !GossipIn(CREW_BLY, CrewMode::Yielded));
    for (std::uint32_t m : { CREW_RAVEN, CREW_ORO, CREW_MURTA })
        for (std::uint32_t mode = 0; mode < kCrewModeCount; ++mode)
            CHECK(!GossipIn(m, CrewMode(mode)));

    // --- rest spots ---
    CHECK(RestSpotFor(CrewMode::Caged, PYRAMID_STAGE_BLOCK) == CrewSpot::Cage);
    CHECK(RestSpotFor(CrewMode::Ally, PYRAMID_STAGE_STAIR) == CrewSpot::Stair);
    CHECK(RestSpotFor(CrewMode::Ally, PYRAMID_STAGE_ALTAR) == CrewSpot::Descent);
    CHECK(RestSpotFor(CrewMode::Gather, PYRAMID_STAGE_DONE) == CrewSpot::Gather);
    CHECK(RestSpotFor(CrewMode::Boss, PYRAMID_STAGE_DONE) == CrewSpot::Gather);
    CHECK(RestSpotFor(CrewMode::Yielded, PYRAMID_STAGE_DONE) == CrewSpot::Gather);
    CHECK(RestSpotFor(CrewMode::PoolAlly, PYRAMID_STAGE_DONE) == CrewSpot::Pool);
    CHECK(RestSpotFor(CrewMode::Prisoner, PYRAMID_STAGE_BLOCK) == CrewSpot::None);
    CHECK(RestSpotFor(CrewMode::Gone, PYRAMID_STAGE_DONE) == CrewSpot::None);

    // The instance's resting modes through a whole run land on the stock walks: cages, stair, foot, gather, pool.
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_NONE, false)), PYRAMID_STAGE_NONE) == CrewSpot::Cage);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_BLOCK, false)), PYRAMID_STAGE_BLOCK) == CrewSpot::Cage);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_STAIR, false)), PYRAMID_STAGE_STAIR) == CrewSpot::Cage);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_STAIR, true)), PYRAMID_STAGE_STAIR) == CrewSpot::Stair);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_ALTAR, true)), PYRAMID_STAGE_ALTAR) == CrewSpot::Descent);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_DONE, true)), PYRAMID_STAGE_DONE) == CrewSpot::Gather);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_DONE, true, DungeonKit::State::Done, CREW_PATH_TEST)),
        PYRAMID_STAGE_DONE) == CrewSpot::Pool);
    CHECK(RestSpotFor(CrewModeFor(Ctx(PYRAMID_STAGE_DONE, true, DungeonKit::State::Done, CREW_PATH_BETRAYAL)),
        PYRAMID_STAGE_DONE) == CrewSpot::None);

    // Every spot of every member is the stock point of its set, and on its room.
    for (std::uint32_t m = 0; m < kCrewCount; ++m)
    {
        CHECK(Near(SpotPoint(CrewSpot::Cage, m), kCrewSpawns[m]));
        CHECK(Near(SpotPoint(CrewSpot::Stair, m), kCrewStairPoints[m]));
        CHECK(Near(SpotPoint(CrewSpot::Descent, m), kCrewDescentPoints[m]));
        CHECK(Near(SpotPoint(CrewSpot::Gather, m), kCrewGatherPoints[m]));
        CHECK(Near(SpotPoint(CrewSpot::Pool, m), kCrewPoolSpots[m]));
        CHECK(Near(SpotPoint(CrewSpot::None, m), Point3{}));

        CHECK(PyramidTopArena().Contains(kCrewSpawns[m].XY(), kCrewSpawns[m].z));
        CHECK(PyramidTopArena().Contains(kCrewStairPoints[m].XY(), kCrewStairPoints[m].z));
        CHECK(LandingArena().Contains(kCrewStairPoints[m].XY(), kCrewStairPoints[m].z));
        CHECK(PlazaArena().Contains(kCrewGatherPoints[m].XY(), kCrewGatherPoints[m].z));
        CHECK(InPyramidRegion(kCrewDescentPoints[m].XY()));
        // the pool spots: on the shore, out of the water, within 5 yd of the disc's centre, at least 2 yd apart
        Point3 const p = kCrewPoolSpots[m];
        CHECK(PoolArena().Contains(p.XY(), p.z));
        CHECK(!PoolWater().Contains(p.XY(), p.z));
        float const dx = p.x - kPoolWaitCenter.x;
        float const dy = p.y - kPoolWaitCenter.y;
        CHECK(dx * dx + dy * dy <= 25.f);
        for (std::uint32_t o = m + 1; o < kCrewCount; ++o)
        {
            float const ox = p.x - kCrewPoolSpots[o].x;
            float const oy = p.y - kCrewPoolSpots[o].y;
            CHECK(ox * ox + oy * oy >= 4.f);
        }
        // 20+ yd from Velratha's spawn (not in her pull) and off the Gahz'rilla landing disc
        float const vx = p.x - kVelrathaSpawn.x;
        float const vy = p.y - kVelrathaSpawn.y;
        CHECK(vx * vx + vy * vy >= 400.f);
    }
    CHECK(SpotPoint(CrewSpot::Cage, kCrewCount).x == 0.f);
    // section 7 #33 A: the four fighters 8 yd west of the stock gather points, Weegli at his stock spot
    CHECK(kCrewGatherPoints[CREW_WEEGLI].y == 1199.63f);
    CHECK(kCrewGatherPoints[CREW_BLY].y == 1200.83f + 8.f);

    CHECK(TravelTo(CrewSpot::Cage) == SpotTravel::Jump);
    CHECK(TravelTo(CrewSpot::Pool) == SpotTravel::Depart);
    CHECK(TravelTo(CrewSpot::Stair) == SpotTravel::Walk && TravelTo(CrewSpot::Descent) == SpotTravel::Walk);
    CHECK(TravelTo(CrewSpot::Gather) == SpotTravel::Walk);

    // --- the prisoner machine (D4a) ---
    {
        PrisonerState s = PrisonerState::Free;
        // soaked: torn, chained, returning, home
        s = PrisonerNext(s, PrisonerEvent::Take);
        CHECK(s == PrisonerState::Torn);
        CHECK(PrisonerNext(s, PrisonerEvent::Take) == PrisonerState::Torn);     // one take at a time
        CHECK(PrisonerNext(s, PrisonerEvent::Home) == PrisonerState::Torn);
        s = PrisonerNext(s, PrisonerEvent::Arrived);
        CHECK(s == PrisonerState::Chained);
        s = PrisonerNext(s, PrisonerEvent::Spare);
        CHECK(s == PrisonerState::Returning);
        CHECK(PrisonerNext(s, PrisonerEvent::Execute) == PrisonerState::Returning);     // spared stays spared
        s = PrisonerNext(s, PrisonerEvent::Home);
        CHECK(s == PrisonerState::Free);
        // not soaked: executed, which only a reset (a respawn) undoes
        s = PrisonerNext(PrisonerNext(PrisonerNext(s, PrisonerEvent::Take), PrisonerEvent::Arrived),
            PrisonerEvent::Execute);
        CHECK(s == PrisonerState::Executed);
        CHECK(PrisonerNext(s, PrisonerEvent::Spare) == PrisonerState::Executed);
        CHECK(PrisonerNext(s, PrisonerEvent::Take) == PrisonerState::Executed);
        CHECK(PrisonerNext(s, PrisonerEvent::Reset) == PrisonerState::Free);
        // the axe may fall on a prisoner still in the air (the jump's landing late)
        CHECK(PrisonerNext(PrisonerState::Torn, PrisonerEvent::Execute) == PrisonerState::Executed);
        CHECK(PrisonerNext(PrisonerState::Torn, PrisonerEvent::Spare) == PrisonerState::Returning);
        // spare / execute refused on a free member
        CHECK(PrisonerNext(PrisonerState::Free, PrisonerEvent::Spare) == PrisonerState::Free);
        CHECK(PrisonerNext(PrisonerState::Free, PrisonerEvent::Execute) == PrisonerState::Free);
        for (PrisonerState any : { PrisonerState::Free, PrisonerState::Torn, PrisonerState::Chained,
            PrisonerState::Returning, PrisonerState::Executed })
            CHECK(PrisonerNext(any, PrisonerEvent::Reset) == PrisonerState::Free);
    }
    CHECK(PrisonerEligible(CREW_BLY, true, CrewMode::Caged, PrisonerState::Free));
    CHECK(PrisonerEligible(CREW_MURTA, true, CrewMode::Caged, PrisonerState::Free));
    CHECK(!PrisonerEligible(CREW_WEEGLI, true, CrewMode::Caged, PrisonerState::Free));     // never Weegli
    CHECK(!PrisonerEligible(CREW_RAVEN, false, CrewMode::Caged, PrisonerState::Free));     // dead
    CHECK(!PrisonerEligible(CREW_ORO, true, CrewMode::Ally, PrisonerState::Free));         // freed already
    CHECK(!PrisonerEligible(CREW_ORO, true, CrewMode::Caged, PrisonerState::Returning));   // on the way home
    CHECK(!PrisonerEligible(kCrewCount, true, CrewMode::Caged, PrisonerState::Free));

    // --- Weegli's door ---
    {
        // betrayal: start, plant before the end (waits), the end lights it, blown, the escape ends
        DoorWalk s = DoorWalkNext(DoorWalk::Idle, DoorEvent::Start, false);
        CHECK(s == DoorWalk::Walking);
        CHECK(DoorWalkNext(s, DoorEvent::Start, false) == DoorWalk::Walking);
        CHECK(DoorWalkNext(s, DoorEvent::FightOver, true) == DoorWalk::Walking);       // the plant decides
        s = DoorWalkNext(s, DoorEvent::Planted, false);
        CHECK(s == DoorWalk::Planted);
        CHECK(DoorWalkNext(s, DoorEvent::Abort, false) == DoorWalk::Idle);             // a crew wipe
        s = DoorWalkNext(s, DoorEvent::FightOver, true);
        CHECK(s == DoorWalk::Fuse);
        CHECK(DoorWalkNext(s, DoorEvent::Abort, false) == DoorWalk::Fuse);             // a lit fuse burns
        s = DoorWalkNext(s, DoorEvent::Blown, true);
        CHECK(s == DoorWalk::Leaving);
        s = DoorWalkNext(s, DoorEvent::Left, true);
        CHECK(s == DoorWalk::Done);
        CHECK(DoorWalkNext(s, DoorEvent::Start, true) == DoorWalk::Done);              // once per lockout
        // the Test: he starts after the end, so the plant lights at once
        CHECK(DoorWalkNext(DoorWalk::Walking, DoorEvent::Planted, true) == DoorWalk::Fuse);
        // the instance's fallback beat him: blown from any state before Leaving
        CHECK(DoorWalkNext(DoorWalk::Idle, DoorEvent::Blown, true) == DoorWalk::Leaving);
        CHECK(DoorWalkNext(DoorWalk::Walking, DoorEvent::Blown, true) == DoorWalk::Leaving);
        CHECK(DoorWalkNext(DoorWalk::Walking, DoorEvent::Abort, false) == DoorWalk::Idle);
        CHECK(DoorWalkNext(DoorWalk::Idle, DoorEvent::Left, false) == DoorWalk::Idle);
    }

    // --- floors ---
    CHECK(FlooredDamage(1000, 300, 1) == 300);
    CHECK(FlooredDamage(1000, 5000, 1) == 999);
    CHECK(FlooredDamage(1, 5000, 1) == 0);
    CHECK(FlooredDamage(1000, 900, 300) == 700);
    CHECK(FlooredDamage(300, 10, 300) == 0);
    CHECK(PctOf(73260, Tune::kYieldPct) == 21978);
    CHECK(PctOf(1, 1.f) == 1);
    CHECK(WeegliFloorHolds(CrewMode::Ally, false) && WeegliFloorHolds(CrewMode::Gather, false));
    CHECK(WeegliFloorHolds(CrewMode::Gone, false));
    CHECK(WeegliFloorHolds(CrewMode::PoolAlly, false));        // on his way (the door, the departure)
    CHECK(!WeegliFloorHolds(CrewMode::PoolAlly, true));        // at the pool he can die (D7Ha)

    // --- Murta ---
    CHECK(!PickHealTarget({}, 80.f));
    CHECK(!PickHealTarget({ 90.f, 100.f }, 80.f));
    CHECK(PickHealTarget({ 90.f, 40.f, 60.f }, 80.f) == std::optional<std::size_t>(1));
    CHECK(PickHealTarget({ 50.f, 50.f }, 80.f) == std::optional<std::size_t>(0));
    CHECK(MurtaSpellFor(40.f, true, true) == MurtaHeal::Heal);
    CHECK(MurtaSpellFor(60.f, false, false) == MurtaHeal::Shield);
    CHECK(MurtaSpellFor(60.f, false, true) == MurtaHeal::Renew);
    CHECK(MurtaSpellFor(70.f, false, false) == MurtaHeal::Renew);
    CHECK(MurtaSpellFor(70.f, true, false) == MurtaHeal::None);
    CHECK(MurtaSpellFor(95.f, false, false) == MurtaHeal::None);
    CHECK(Tune::kHealBelowPct < Tune::kShieldBelowPct && Tune::kShieldBelowPct < Tune::kRenewBelowPct);

    // --- the pool ---
    CHECK(AllArrived(kCrewAll));
    CHECK(!AllArrived(kCrewAll & ~CrewBit(CREW_WEEGLI)));
    CHECK(!AllArrived(0));

    // --- timers ---
    CHECK(InWindow({ 3000, 5000 }, 0.f) == 3000 && InWindow({ 3000, 5000 }, 1.f) == 5000);
    CHECK(InWindow({ 3000, 5000 }, 0.5f) == 4000);
    CHECK(InWindow({ 3000, 5000 }, -1.f) == 3000 && InWindow({ 3000, 5000 }, 2.f) == 5000);
    CHECK(InWindow({ 15000, 15000 }, 0.7f) == 15000);
    // the stock betrayal: line 0 at 1.5 s, line 1 at 4.5 s, hostile at 7.5 s
    CHECK(Tune::kBetrayalLine0Ms + Tune::kBetrayalLine1Ms + Tune::kBetrayalHostileMs == 7500);
    CHECK(Tune::kBandsEscapeMs > 10000);
    CHECK(Tune::kPrisonerMoveTimeoutMs < 4000);     // the prisoner is chained well before a 4 s Behead lands

    // --- the engine half (BlyCrew.cpp / BlyCrew.h) ---
    std::string const cpp = ReadFile(SourceDir() / "BlyCrew.cpp");
    std::string const h = ReadFile(SourceDir() / "BlyCrew.h");
    CHECK(!cpp.empty() && !h.empty());
    // rule 27: the crew help each other: no assist timer
    CHECK(cpp.find("NoAssist") == std::string::npos && cpp.find("SetAssistanceTimer") == std::string::npos);
    // section 7 #18 A: the betrayal is option 0 (added first), the Test second with a confirmation
    std::size_t const betrayal = cpp.find("AddGossipItemFor(player, GOSSIP_ICON_CHAT, kGossipBetrayal");
    std::size_t const test = cpp.find("AddGossipItemFor(player, GOSSIP_ICON_CHAT, kGossipTest");
    CHECK(betrayal != std::string::npos && test != std::string::npos && betrayal < test);
    CHECK(cpp.find("kGossipTestConfirm, 0, false") != std::string::npos);
    CHECK(cpp.find("DATA_TEST_KEY") != std::string::npos && cpp.find("player->IsInCombat()") != std::string::npos);
    // the five scripts and the shell key
    for (char const* script : { "npc_bly_crew_bly", "npc_bly_crew_raven", "npc_bly_crew_oro", "npc_bly_crew_weegli",
        "npc_bly_crew_murta" })
        CHECK(cpp.find(std::string("RegisterDungeonReworkCreatureAI(") + script) != std::string::npos);
    CHECK(cpp.find("RegisterBoss(\"band\"") != std::string::npos);
    // rule 34: the text groups by name, 0-based as SP prints them
    CHECK(h.find("YELL_BLY_GANG_UP        = 3") != std::string::npos);
    CHECK(h.find("SAY_BLY_TEST_DONE       = 4") != std::string::npos);
    CHECK(h.find("YELL_BLY_BEHIND_ME      = 5") != std::string::npos);
    CHECK(h.find("YELL_WEEGLI_BARRELS     = 3") != std::string::npos);
    CHECK(h.find("YELL_WEEGLI_CHARGE      = 4") != std::string::npos);
    // RB-20 is the instance's (respawn by spawn id); CR never respawns a member itself
    CHECK(cpp.find("ForceCreatureRespawn") == std::string::npos && cpp.find("->Respawn(") == std::string::npos);

    // --- the SQL rev: the four CAN_ASSIST flags and the five new text rows ---
    std::filesystem::path const rev = SourceDir().parent_path().parent_path().parent_path().parent_path() / "data"
        / "sql" / "updates" / "pending_db_world" / "rev_crew_zul_farrak.sql";
    std::string const sql = ReadFile(rev);
    CHECK(!sql.empty());
    CHECK(sql.find("WHERE `entry` IN (7605, 7606, 7607, 7608)") != std::string::npos);
    CHECK(sql.find("`type_flags` = `type_flags` | 4096") != std::string::npos);
    for (char const* row : { "(7604, 3, 0,", "(7604, 4, 0,", "(7604, 5, 0,", "(7607, 3, 0,", "(7607, 4, 0," })
        CHECK(sql.find(row) != std::string::npos);
    CHECK(sql.find("npc_bly_crew") == std::string::npos);      // the S0 rev binds the scripts

    return Report("zf_crew_test");
}
