// Host tests for ZulFarrakRework.h (WP-S0, the Zul'Farrak skeleton): slots and data ids, the id slices, the Pyramid's
// stage machine (starts, wins, wipes, snapshots and restores of the crew mask, the Offerings and the Blood Price), the
// wipe rule, the crew's modes, the paths and the Test, the End Door, the pool and the hard mode, the "ZFR" save with
// the stock "Z F" reader, the rooms' points against their arenas, the health table, and every boss file's NoAssist
// call (section 3.5 rule 27).
#include "ZulFarrakRework.h"
#include "check.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <string>

using namespace ZulFarrakRework;
namespace S = DungeonKit::State;

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

    std::size_t Count(std::string const& text, std::string const& what)
    {
        std::size_t n = 0;
        for (std::size_t at = text.find(what); at != std::string::npos; at = text.find(what, at + what.size()))
            ++n;
        return n;
    }

    // ceil(base x HealthModifier) in float, as CreatureBaseStats::GenerateHealth does.
    std::uint32_t EngineHealth(std::uint32_t base, float modifier)
    {
        return std::uint32_t(std::ceil(float(base) * modifier));
    }

    void TestSlotsAndIds()
    {
        CHECK(kBossCount == 9);
        CHECK(kEncounterBossCount == 8);
        // slot = DungeonEncounter bit (593 bit 0 Velratha ... 600 bit 7 Ukorz), slot 8 has no row
        CHECK(BOSS_VELRATHA == 0 && BOSS_GAHZRILLA == 1 && BOSS_ANTUSUL == 2 && BOSS_THEKA == 3);
        CHECK(BOSS_ZUMRAH == 4 && BOSS_PYRAMID == 5 && BOSS_CREW == 6 && BOSS_UKORZ == 7);
        CHECK(BOSS_CREW_AT_THE_POOL == 8);
        // stock data ids keep their numbers
        CHECK(DATA_PYRAMID == 0 && DATA_GAHZRILLA == 1 && DATA_END_DOOR == 2);
        // every data id distinct, none inside the crew mode block
        std::set<std::uint32_t> const ids{ DATA_PYRAMID, DATA_GAHZRILLA, DATA_END_DOOR, DATA_PYRAMID_STAGE,
            DATA_PYRAMID_RUNNING, DATA_PYRAMID_CAGES, DATA_OFFERINGS, DATA_BLOOD_PRICE, DATA_PYRAMID_START,
            DATA_PYRAMID_COMPLETE, DATA_PYRAMID_FAIL, DATA_CREW_ALIVE, DATA_CREW_PATH, DATA_CREW_DONE, DATA_CREW_FIGHT,
            DATA_CREW_LOST, DATA_CREW_AT_POOL, DATA_CREW_AT_END, DATA_TEST_KEY, DATA_GONG_STRUCK, DATA_HARD_MODE,
            DATA_HARD_MODE_KILLED, DATA_HARD_MODE_KEY, DATA_GM_STAGE, DATA_GM_CREW_MASK, DATA_GM_DOOR,
            DATA_GM_TEST_ARM, DATA_GM_HARD_MODE };
        CHECK(ids.size() == 28);
        for (std::uint32_t id : ids)
            CHECK(id < DATA_CREW_MODE_BASE || id >= DATA_CREW_MODE_BASE + kCrewCount);
        // guid keys: bosses by slot, the rest apart
        std::set<std::uint32_t> const guids{ kGuidBossBase + BOSS_VELRATHA, kGuidBossBase + BOSS_GAHZRILLA,
            kGuidBossBase + BOSS_CREW_AT_THE_POOL, kGuidExecutioner, kGuidRuuzlu, kGuidGahzrilla, kGuidSezzziz,
            kGuidNekrum, kGuidCrewBase, kGuidCrewBase + kCrewCount - 1, kGuidEndDoor, kGuidGong };
        CHECK(guids.size() == 12);
        // the crew
        CHECK(kCrewAll == 0x1F && kCrewFighters == 0x17);
        CHECK(CrewIndexOf(NPC_WEEGLI) == std::optional<std::uint32_t>(CREW_WEEGLI));
        CHECK(!CrewIndexOf(NPC_EXECUTIONER));
        CHECK(kCrewEntries[CREW_MURTA] == NPC_MURTA);
    }

    void TestSlices()
    {
        // the slices tile the reservation in order
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        CHECK(kSpellSlices.back().last + 1 == kSpellsSpare.first);
        CHECK(kSpellsSpare.last == kSpellsReservation.last);
        CHECK(kSpellsShared.Contains(SPELL_ZF_PYRAMID_CREDIT) && kSpellsShared.Contains(SPELL_ZF_CREW_CREDIT));
        CHECK(kSpellsShared.Contains(kSpellsCrewAlly.first) && kSpellsShared.Contains(kSpellsCrewAlly.last));
        CHECK(!kSpellsCrewAlly.Contains(SPELL_ZF_WEAKENED_COPY));
        // the build creatures and gameobjects inside theirs
        for (std::uint32_t entry : { NPC_ZF_PERSECUTOR_SWARM, NPC_ZF_EMPTY_VESSEL,
            NPC_ZF_GRAVE_STALKER, NPC_ZF_SANDFURY_BERSERKER, NPC_ZF_PYRAMID_STALKER, NPC_ZF_QUICKSAND,
            NPC_ZF_CREEPING_SANDS, NPC_ZF_PUDDLE, NPC_ZF_STRIKE_STALKER, NPC_ZF_ENTRANCE_GOBLIN })
            CHECK(kCreaturesReservation.Contains(entry));
        CHECK(kGameObjectsReservation.Contains(GO_ZF_CREW_STASH));
        CHECK(kGameObjectsReservation.Contains(GO_ZF_CREW_STASH_HEROIC));
        CHECK(IsTrollCage(141070) && IsTrollCage(141074) && !IsTrollCage(146084));
    }

    void TestStageMachine()
    {
        PyramidState s;
        CHECK(s.InPlay() == PYRAMID_STAGE_BLOCK);
        // the cages and the stair are refused before the Block is won
        CHECK(!PyramidOpenCages(s));
        CHECK(PyramidStart(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Refused);
        CHECK(PyramidStart(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Refused);
        CHECK(PyramidStart(s, 0) == PyramidVerdict::Refused);
        CHECK(PyramidStart(s, 5) == PyramidVerdict::Refused);

        // stage 1: the Executioner's pull, a prisoner lost (normal), a wipe restores it
        CHECK(PyramidStart(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Started);
        CHECK(s.running && s.stage == PYRAMID_STAGE_BLOCK);
        CHECK(PyramidStart(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Refused);       // already running
        CrewLoss loss = PyramidCrewLost(s, CREW_ORO, false);
        CHECK(loss.counted && loss.offerings == 1 && loss.bloodPrice == 0);
        CHECK(s.crewAlive == (kCrewAll & ~CrewBit(CREW_ORO)) && s.offerings == 1);
        CHECK(!PyramidCrewLost(s, CREW_ORO, false).counted);                         // twice: once
        CHECK(!PyramidCrewLost(s, CREW_WEEGLI, false).counted);                      // Weegli never
        CHECK(!PyramidCrewLost(s, 7, false).counted);
        // a save while it runs keeps the snapshot (the loss is not permanent yet)
        CHECK(s.Saved().crewAlive == kCrewAll && s.Saved().offerings == 0);
        CHECK(PyramidWiped(s.running, 0) && !PyramidWiped(s.running, 1) && !PyramidWiped(false, 0));
        CHECK(PyramidWipe(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Refused);       // not the running one
        CHECK(PyramidWipe(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Wiped);
        CHECK(!s.running && s.stage == PYRAMID_STAGE_BLOCK && s.crewAlive == kCrewAll && s.offerings == 0);
        CHECK(PyramidWipe(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Refused);       // not running
        // the restart; losses up to the cap; the win makes them permanent
        CHECK(PyramidStart(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Restarted);
        for (std::uint32_t m : { CREW_BLY, CREW_RAVEN, CREW_ORO, CREW_MURTA })
            PyramidCrewLost(s, m, false);
        CHECK(s.offerings == kOfferingsCap && s.crewAlive == kCrewWeegliBit);
        CHECK(PyramidComplete(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Refused);
        CHECK(PyramidComplete(s, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Completed);
        CHECK(!s.running && s.stage == PYRAMID_STAGE_STAIR && !s.cagesOpen);
        CHECK(s.Saved().crewAlive == kCrewWeegliBit && s.Saved().offerings == kOfferingsCap);
        CHECK(StockPyramidPhase(s, false) == 0);

        // stage 2: the cages open it; a wipe waits for the landing; a loss there adds no Offering
        CHECK(PyramidStart(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Refused);      // cages closed
        CHECK(!StairRestartWaits(s));
        CHECK(PyramidOpenCages(s) && !PyramidOpenCages(s));
        CHECK(PyramidStart(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Started);
        CHECK(StockPyramidPhase(s, false) == 3);
        CHECK(PyramidWipe(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Wiped);
        CHECK(StairRestartWaits(s));
        CHECK(PyramidStart(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Restarted);
        CHECK(PyramidComplete(s, PYRAMID_STAGE_STAIR) == PyramidVerdict::Completed);
        CHECK(s.stage == PYRAMID_STAGE_ALTAR && !s.running && !StairRestartWaits(s));
        CHECK(StockPyramidPhase(s, false) == 7);
        // R-1-FW m3 / R-1-B mn-4: a loss in the descent's 5 s (no stage running) counts nothing, the bit stays
        {
            PyramidState gap = s;
            gap.crewAlive = kCrewAll;           // (a fresh mask for the check)
            CrewLoss const lost = PyramidCrewLost(gap, CREW_RAVEN, true);
            CHECK(!lost.counted && gap.crewAlive == kCrewAll);
            CHECK(PyramidStart(gap, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Started
                && (gap.snapshot.crewAlive & CrewBit(CREW_RAVEN)));
        }

        // stage 3: a crew death adds nothing but the bit; a wipe brings it back
        CHECK(PyramidStart(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Started);
        s.crewAlive = kCrewAll;                 // (a fresh mask for the check)
        s.snapshot = s.Live();
        loss = PyramidCrewLost(s, CREW_MURTA, false);
        CHECK(loss.counted && loss.offerings == 0 && s.offerings == kOfferingsCap);
        CHECK(PyramidWipe(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Wiped && s.crewAlive == kCrewAll);
        CHECK(PyramidStart(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Restarted);
        CHECK(PyramidComplete(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Completed);
        CHECK(s.stage == PYRAMID_STAGE_DONE && !s.running);
        CHECK(PyramidStart(s, PYRAMID_STAGE_ALTAR) == PyramidVerdict::Refused);
        CHECK(StockPyramidPhase(s, false) == 9 && StockPyramidPhase(s, true) == 12);

        // heroic: a Block loss is Blood Price, uncapped
        PyramidState h;
        PyramidStart(h, PYRAMID_STAGE_BLOCK);
        h.bloodPrice = 12;                      // the owners' per-second ticks
        loss = PyramidCrewLost(h, CREW_BLY, true);
        CHECK(loss.bloodPrice == kBloodPricePerCrew && h.bloodPrice == 12 + kBloodPricePerCrew && h.offerings == 0);
        PyramidCrewLost(h, CREW_RAVEN, true);
        CHECK(h.bloodPrice == 12 + 2 * kBloodPricePerCrew);
        CHECK(PyramidWipe(h, PYRAMID_STAGE_BLOCK) == PyramidVerdict::Wiped && h.bloodPrice == 0);
        // outside a running stage nothing counts, not even the bit (a reload's settle, an idle stage: R-1-FW m3)
        PyramidState idle;
        loss = PyramidCrewLost(idle, CREW_BLY, true);
        CHECK(!loss.counted && loss.bloodPrice == 0 && idle.bloodPrice == 0 && idle.crewAlive == kCrewAll);
        // the Blood Price's ticks while a stage runs never save (the snapshot is what a save keeps: D4a's note)
        CHECK(!BloodPriceWriteSaves(true) && BloodPriceWriteSaves(false));

        // the Altar's win
        CHECK(AltarCleared(true, false, true, false));
        CHECK(!AltarCleared(true, true, true, false) && !AltarCleared(true, false, false, false));
        CHECK(!AltarCleared(false, false, false, false));
    }

    void TestCrewModes()
    {
        CrewContext c;
        CHECK(CrewModeFor(c) == CrewMode::Caged);
        c.stage = PYRAMID_STAGE_BLOCK;
        CHECK(CrewModeFor(c) == CrewMode::Caged);
        c.stage = PYRAMID_STAGE_STAIR;
        CHECK(CrewModeFor(c) == CrewMode::Caged);       // the Block won, the cages still shut
        c.cagesOpen = true;
        CHECK(CrewModeFor(c) == CrewMode::Ally);
        c.stage = PYRAMID_STAGE_ALTAR;
        CHECK(CrewModeFor(c) == CrewMode::Ally);
        c.stage = PYRAMID_STAGE_DONE;
        CHECK(CrewModeFor(c) == CrewMode::Gather);
        c.crewSlot = S::InProgress;
        CHECK(CrewModeFor(c) == CrewMode::Gather);      // the fight's Boss mode is set live by the instance
        c.crewSlot = S::Done;
        c.path = CREW_PATH_BETRAYAL;
        CHECK(CrewModeFor(c) == CrewMode::Gone);
        c.path = CREW_PATH_TEST;
        CHECK(CrewModeFor(c) == CrewMode::PoolAlly);

        // who must stand: the mask in the Pyramid, all five for Bly's fight, the Test's at the pool, nobody after the
        // betrayal
        CrewContext p;
        p.stage = PYRAMID_STAGE_STAIR;
        p.cagesOpen = true;
        std::uint32_t const twoLost = kCrewAll & ~CrewBit(CREW_ORO) & ~CrewBit(CREW_BLY);
        CHECK(!CrewMemberStands(p, twoLost, CREW_ORO) && CrewMemberStands(p, twoLost, CREW_RAVEN));
        p.stage = PYRAMID_STAGE_DONE;
        CHECK(CrewMemberStands(p, twoLost, CREW_ORO));  // section 7 #12 A
        p.crewSlot = S::Done;
        p.path = CREW_PATH_BETRAYAL;
        CHECK(!CrewMemberStands(p, kCrewAll, CREW_WEEGLI));
        p.path = CREW_PATH_TEST;
        CHECK(CrewMemberStands(p, kCrewAll, CREW_WEEGLI) && !CrewMemberStands(p, twoLost, CREW_BLY));

        for (std::uint32_t m = 0; m < kCrewModeCount; ++m)
            CHECK(ValidCrewMode(m));
        CHECK(!ValidCrewMode(kCrewModeCount));
        CHECK(std::string(kCrewModeNames[std::uint32_t(CrewMode::PoolAlly)]) == "poolally");
    }

    void TestPathsAndTest()
    {
        // the Test: heroic, the Pyramid won with all five, the fight neither running nor done
        CHECK(TestAllowed(true, PYRAMID_STAGE_DONE, kCrewAll, S::NotStarted));
        CHECK(!TestAllowed(false, PYRAMID_STAGE_DONE, kCrewAll, S::NotStarted));
        CHECK(!TestAllowed(true, PYRAMID_STAGE_ALTAR, kCrewAll, S::NotStarted));
        CHECK(!TestAllowed(true, PYRAMID_STAGE_DONE, kCrewAll & ~CrewBit(CREW_RAVEN), S::NotStarted));
        CHECK(!TestAllowed(true, PYRAMID_STAGE_DONE, kCrewAll, S::InProgress));
        CHECK(!TestAllowed(true, PYRAMID_STAGE_DONE, kCrewAll, S::Done));

        CHECK(CrewPathAllowed(CREW_PATH_BETRAYAL, false, PYRAMID_STAGE_DONE, 0, S::NotStarted));
        CHECK(!CrewPathAllowed(CREW_PATH_BETRAYAL, false, PYRAMID_STAGE_ALTAR, 0, S::NotStarted));
        CHECK(!CrewPathAllowed(CREW_PATH_TEST, false, PYRAMID_STAGE_DONE, kCrewAll, S::NotStarted));
        CHECK(CrewPathAllowed(CREW_PATH_TEST, true, PYRAMID_STAGE_DONE, kCrewAll, S::NotStarted));
        CHECK(!CrewPathAllowed(CREW_PATH_BETRAYAL, true, PYRAMID_STAGE_DONE, kCrewAll, S::InProgress));
        CHECK(!CrewPathAllowed(CREW_PATH_OPEN, true, PYRAMID_STAGE_DONE, kCrewAll, S::Done));
        CHECK(!CrewPathAllowed(3, true, PYRAMID_STAGE_DONE, kCrewAll, S::NotStarted));

        CHECK(CrewFightStartAllowed(PYRAMID_STAGE_DONE, CREW_PATH_BETRAYAL, S::NotStarted));
        CHECK(!CrewFightStartAllowed(PYRAMID_STAGE_DONE, CREW_PATH_OPEN, S::NotStarted));
        CHECK(!CrewFightStartAllowed(PYRAMID_STAGE_ALTAR, CREW_PATH_BETRAYAL, S::NotStarted));
        CHECK(!CrewFightStartAllowed(PYRAMID_STAGE_DONE, CREW_PATH_TEST, S::Done));

        // the betrayal's fallback end by deaths; the Test only by D5
        CHECK(CrewFightOverByDeaths(S::InProgress, CREW_PATH_BETRAYAL, kCrewWeegliBit));
        CHECK(!CrewFightOverByDeaths(S::InProgress, CREW_PATH_BETRAYAL, kCrewWeegliBit | CrewBit(CREW_MURTA)));
        CHECK(!CrewFightOverByDeaths(S::InProgress, CREW_PATH_TEST, 0));
        CHECK(!CrewFightOverByDeaths(S::NotStarted, CREW_PATH_BETRAYAL, 0));
    }

    void TestDoorAndPool()
    {
        CHECK(SanitizeDoorState(S::Done) == S::Done && SanitizeDoorState(S::InProgress) == S::NotStarted);
        CHECK(!EndDoorFallbackDue(S::Done, S::NotStarted, kEndDoorFallbackMs - 1));
        CHECK(EndDoorFallbackDue(S::Done, S::NotStarted, kEndDoorFallbackMs));
        CHECK(EndDoorFallbackDue(S::Done, S::InProgress, kEndDoorFallbackMs));  // Weegli stuck on his way
        CHECK(!EndDoorFallbackDue(S::Done, S::Done, kEndDoorFallbackMs));
        CHECK(!EndDoorFallbackDue(S::InProgress, S::NotStarted, kEndDoorFallbackMs));

        // the hard mode's key and arming
        CHECK(HardModeKey(true, CREW_PATH_TEST, S::Done, kCrewAll, S::NotStarted));
        CHECK(!HardModeKey(false, CREW_PATH_TEST, S::Done, kCrewAll, S::NotStarted));
        CHECK(!HardModeKey(true, CREW_PATH_BETRAYAL, S::Done, kCrewAll, S::NotStarted));
        CHECK(!HardModeKey(true, CREW_PATH_TEST, S::Done, kCrewAll & ~CrewBit(CREW_WEEGLI), S::NotStarted));
        CHECK(!HardModeKey(true, CREW_PATH_TEST, S::Done, kCrewAll, S::Done));
        CHECK(HardModeArmAllowed(true, CREW_PATH_TEST, S::Done, kCrewAll, S::NotStarted, S::NotStarted));
        CHECK(!HardModeArmAllowed(true, CREW_PATH_TEST, S::Done, kCrewAll, S::InProgress, S::NotStarted));
        CHECK(!HardModeArmAllowed(true, CREW_PATH_TEST, S::Done, kCrewAll, S::Done, S::NotStarted));
        CHECK(GmHardModeAllowed(true, S::NotStarted, 1) && !GmHardModeAllowed(false, S::NotStarted, 1));
        CHECK(GmHardModeAllowed(false, S::NotStarted, 0) && !GmHardModeAllowed(true, S::InProgress, 0));
        // F-1 MA-1: only a strike whose pull built the packages (2) arms; the key alone at the gong (1) never does
        CHECK(GongArmsHardMode(kGongDataHardMode, true));
        CHECK(!GongArmsHardMode(kGongDataPlain, true));                 // key shut at her pull, open at the gong
        CHECK(!GongArmsHardMode(kGongDataHardMode, false) && !GongArmsHardMode(0, true) && !GongArmsHardMode(3, true));
        CHECK(HardModeLootLit(1, S::InProgress) && !HardModeLootLit(1, S::Done) && !HardModeLootLit(0, S::NotStarted));

        // the pool's wipes and the slot pairing (section 7 #43 h A)
        CHECK(PoolWiped(BOSS_GAHZRILLA, S::InProgress, S::NotStarted) && PoolWiped(BOSS_VELRATHA, S::InProgress,
            S::Fail));
        CHECK(!PoolWiped(BOSS_GAHZRILLA, S::NotStarted, S::NotStarted) && !PoolWiped(BOSS_GAHZRILLA, S::InProgress,
            S::Done));
        CHECK(!PoolWiped(BOSS_UKORZ, S::InProgress, S::NotStarted));
        CHECK(PoolWipeReopensVelratha(BOSS_GAHZRILLA, S::InProgress, S::NotStarted, S::Done));
        // D5's note: the stash comes back after a reload unless it was emptied
        CHECK(StashRestoreDue(S::Done, 0, false, true, kStashRestoreMs));
        CHECK(!StashRestoreDue(S::Done, 1, false, true, kStashRestoreMs));
        CHECK(!StashRestoreDue(S::Done, 0, true, true, kStashRestoreMs));
        CHECK(!StashRestoreDue(S::Done, 0, false, false, kStashRestoreMs));
        CHECK(!StashRestoreDue(S::Done, 0, false, true, kStashRestoreMs - 1));
        CHECK(!StashRestoreDue(S::InProgress, 0, false, true, kStashRestoreMs));
        CHECK(kEndDoorFallbackMs >= kStashRestoreMs);   // a reload's watch counts as long ago for both
        CHECK(PoolReloadReopensVelratha(S::Done, S::NotStarted) && PoolReloadReopensVelratha(S::Done, S::InProgress));
        CHECK(!PoolReloadReopensVelratha(S::Done, S::Done) && !PoolReloadReopensVelratha(S::NotStarted, S::NotStarted));
        CHECK(!PoolWipeReopensVelratha(BOSS_GAHZRILLA, S::InProgress, S::NotStarted, S::NotStarted));
        CHECK(!PoolWipeReopensVelratha(BOSS_VELRATHA, S::InProgress, S::NotStarted, S::Done));
    }

    void TestSave()
    {
        ZfrSave s;
        s.states[BOSS_THEKA] = S::Done;
        s.states[BOSS_PYRAMID] = S::Done;
        s.states[BOSS_CREW] = S::Done;
        s.states[BOSS_GAHZRILLA] = S::Done;
        s.states[BOSS_CREW_AT_THE_POOL] = S::Done;
        s.pyramidStage = PYRAMID_STAGE_DONE;
        s.cagesOpen = 1;
        s.crewAlive = kCrewAll & ~CrewBit(CREW_RAVEN);
        s.offerings = 2;
        s.bloodPrice = 77;
        s.crewAtEnd = kCrewAll;
        s.crewPath = CREW_PATH_TEST;
        s.endDoor = S::Done;
        s.hardMode = 1;
        s.crewAtPool = 1;
        s.stashLooted = 1;
        std::string const text = FormatZfrSave(s);
        CHECK(text.rfind("Z F R ", 0) == 0);
        ZfrSave r;
        CHECK(ParseZfrSave(text, r));
        CHECK(r.states == s.states && r.pyramidStage == s.pyramidStage && r.cagesOpen == 1);
        // R-1-FW M1: Raven died at the pool (Test path, slot 6 DONE): a reload ends the attempt, all five stand
        CHECK(r.crewAlive == kCrewAll && r.offerings == 2 && r.bloodPrice == 77 && r.crewAtEnd == kCrewAll);
        CHECK(r.crewPath == CREW_PATH_TEST && r.endDoor == S::Done && r.hardMode == 1 && r.crewAtPool == 1);
        CHECK(r.stashLooted == 1);
        // the betrayal keeps its fallen down
        {
            ZfrSave b = s;
            b.crewPath = CREW_PATH_BETRAYAL;
            b.crewAlive = 0;
            CHECK(ParseZfrSave(FormatZfrSave(b), r) && r.crewAlive == kCrewWeegliBit);
        }
        // R-1-FW M2 / R-1-C MA-2: Velratha DONE, Gahz'rilla not: slot 0 reopens; both DONE stay DONE
        {
            ZfrSave p;
            p.states[BOSS_VELRATHA] = S::Done;
            CHECK(ParseZfrSave(FormatZfrSave(p), r) && r.states[BOSS_VELRATHA] == S::NotStarted);
            p.states[BOSS_GAHZRILLA] = S::Done;
            CHECK(ParseZfrSave(FormatZfrSave(p), r) && r.states[BOSS_VELRATHA] == S::Done);
            // the stash flag needs slot 6 DONE
            p.stashLooted = 1;
            CHECK(ParseZfrSave(FormatZfrSave(p), r) && r.stashLooted == 0);
        }

        // sanitized: IN_PROGRESS goes; slot 8 needs slot 1 DONE and the flag; the path, the door and the pool line
        // need slot 6 DONE; the stage follows slot 5; Weegli is always alive; the Offerings cap
        ZfrSave m;
        m.states[BOSS_UKORZ] = S::InProgress;
        m.states[BOSS_CREW_AT_THE_POOL] = S::Done;
        m.pyramidStage = 9;
        m.crewAlive = 0;
        m.offerings = 40;
        m.crewPath = CREW_PATH_TEST;
        m.endDoor = S::InProgress;
        m.crewAtPool = 1;
        m.crewAtEnd = kCrewAll;
        CHECK(ParseZfrSave(FormatZfrSave(m), r));
        CHECK(r.states[BOSS_UKORZ] == S::NotStarted && r.states[BOSS_CREW_AT_THE_POOL] == S::NotStarted);
        CHECK(r.pyramidStage == PYRAMID_STAGE_ALTAR && r.cagesOpen == 1 && r.crewAtEnd == 0);
        CHECK(r.crewAlive == kCrewWeegliBit && r.offerings == kOfferingsCap);
        CHECK(r.crewPath == CREW_PATH_OPEN && r.endDoor == S::NotStarted && r.crewAtPool == 0);
        // slot 6 DONE forces slot 5 DONE, the door blown and a path
        ZfrSave d;
        d.states[BOSS_CREW] = S::Done;
        CHECK(ParseZfrSave(FormatZfrSave(d), r));
        CHECK(r.states[BOSS_PYRAMID] == S::Done && r.pyramidStage == PYRAMID_STAGE_DONE);
        CHECK(r.endDoor == S::Done && r.crewPath == CREW_PATH_BETRAYAL);
        // stage 2 with its cages shut stays shut
        ZfrSave c;
        c.pyramidStage = PYRAMID_STAGE_STAIR;
        CHECK(ParseZfrSave(FormatZfrSave(c), r) && r.cagesOpen == 0);
        // an older build's shorter tail loads (the defaults fill it)
        CHECK(ParseZfrSave("Z F R 0 0 0 3 0 0 0 0 0", r) && r.states[BOSS_THEKA] == S::Done
            && r.crewAlive == kCrewWeegliBit);

        // the stock save: "Z F <phase> <gahz'rilla> [<door>]" (c9315e3ec), with the completed-encounter mask
        CHECK(ParseZfrSave("Z F 12 4 3", r, (1u << BOSS_THEKA) | (1u << BOSS_VELRATHA)));
        CHECK(r.states[BOSS_PYRAMID] == S::Done && r.states[BOSS_CREW] == S::Done);
        CHECK(r.states[BOSS_GAHZRILLA] == S::Done);
        CHECK(r.states[BOSS_THEKA] == S::Done && r.states[BOSS_VELRATHA] == S::Done);
        CHECK(r.pyramidStage == PYRAMID_STAGE_DONE && r.endDoor == S::Done && r.crewPath == CREW_PATH_BETRAYAL);
        CHECK(r.crewAtEnd == 0 && r.hardMode == 0);
        CHECK(ParseZfrSave("Z F 9 0", r));                      // an older two-field stock save
        CHECK(r.states[BOSS_PYRAMID] == S::Done && r.states[BOSS_CREW] == S::NotStarted && r.endDoor == S::NotStarted);
        CHECK(r.states[BOSS_GAHZRILLA] == S::NotStarted && r.crewPath == CREW_PATH_OPEN);
        CHECK(ParseZfrSave("Z F 11 0", r) && r.endDoor == S::Done);     // phase 11: the door derived
        CHECK(ParseZfrSave("Z F 5 0 0", r));                    // mid-waves: the Stair replays with its cages open
        CHECK(r.pyramidStage == PYRAMID_STAGE_STAIR && r.cagesOpen == 1 && r.states[BOSS_PYRAMID] == S::NotStarted);
        CHECK(ParseZfrSave("Z F 0 0 0", r) && r.pyramidStage == PYRAMID_STAGE_NONE && r.crewAlive == kCrewAll);
        CHECK(ParseZfrSave("Z F 0 3 0", r) && r.states[BOSS_GAHZRILLA] == S::Done);  // the comment's 3
        // anything else is ignored
        CHECK(!ParseZfrSave("Z F", r));
        CHECK(!ParseZfrSave("R F C 3 3 3 3 0 0", r));
        CHECK(!ParseZfrSave("", r));
    }

    void TestGeometry()
    {
        // spawns and spots on their rooms
        CHECK(CourtyardArena().Contains(kThekaSpawn.XY(), kThekaSpawn.z));
        for (Point3 const& p : kThekaRisePoints)
            CHECK(CourtyardArena().Contains(p.XY(), p.z));
        for (Point3 const& p : kThekaRiseAlternates)
            CHECK(CourtyardArena().Contains(p.XY(), p.z));
        CHECK(DenArena().Contains(kAntusulSpawn.XY(), kAntusulSpawn.z));
        CHECK(DenArena().Contains(kAntusulChamber.XY(), kAntusulChamber.z));
        CHECK(DenArena().Contains(kDenMouth.XY(), kDenMouth.z));
        for (Point3 const& p : kServantRisePoints)
            CHECK(DenArena().Contains(p.XY(), p.z));
        CHECK(BowlArena().Contains(kZumrahSpawn.XY(), kZumrahSpawn.z));
        CHECK(BowlArena().Contains(kCauldron.XY(), kCauldron.z));
        CHECK(BowlArena().Contains(kBoundDeadOverflow.XY(), kBoundDeadOverflow.z));
        CHECK(BowlArena().Contains(kCheckpoint.XY(), kCheckpoint.z));
        for (Point3 const& p : kBoundDeadSpots)
            CHECK(BowlArena().Contains(p.XY(), p.z));
        CHECK(PyramidTopArena().Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
        CHECK(PyramidTopArena().Contains(kLanding.XY(), kLanding.z));
        CHECK(LandingArena().Contains(kLanding.XY(), kLanding.z));
        CHECK(!LandingArena().Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
        for (Point3 const& p : kCages)
            CHECK(PyramidTopArena().Contains(p.XY(), p.z));
        CHECK(StairArena().Contains(kStairFoot.XY(), kStairFoot.z) && StairArena().Contains(kStairLip.XY(),
            kStairLip.z));
        CHECK(kStairLaneYMax < kLandingYMin && kStairLaneYMin < kStairLaneYMax);
        CHECK(PlazaArena().Contains(kPlazaCenter.XY(), kPlazaCenter.z));
        CHECK(PlazaArena().Contains(kPlazaDisc.XY(), kPlazaDisc.z));
        for (Point3 const& p : kSezzzizAddPoints)
            CHECK(PlazaArena().Contains(p.XY(), p.z));
        CHECK(MesaArena().Contains(kUkorzSpawn.XY(), kUkorzSpawn.z) && MesaArena().Contains(kRuuzluSpawn.XY(),
            kRuuzluSpawn.z));
        CHECK(MesaArena().Contains(kMesaDonutCenter.XY(), kMesaDonutCenter.z));
        CHECK(MesaArena().Contains(kMesaRampHead.XY(), kMesaRampHead.z));
        CHECK(PoolArena().Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
        CHECK(PoolArena().Contains(kGong.XY(), kGong.z));
        CHECK(PoolArena().Contains(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
        CHECK(PoolWater().Contains(kGahzrillaSummon.XY(), kGahzrillaSummon.z));
        CHECK(PoolArena().Contains(kGahzrillaSummon.XY(), kGahzrillaSummon.z));     // a swimmer is on the arena
        CHECK(!PoolWater().Contains(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
        for (Point3 const& p : kShoreDiscs)
            CHECK(PoolArena().Contains(p.XY(), p.z));
        // the slots' arenas
        CHECK(ArenaFor(BOSS_THEKA).Contains(kThekaSpawn.XY(), kThekaSpawn.z));
        CHECK(ArenaFor(BOSS_PYRAMID).Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
        CHECK(ArenaFor(BOSS_CREW).Contains(kCrewGatherPoints[CREW_BLY].XY(), kCrewGatherPoints[CREW_BLY].z));
        CHECK(ArenaFor(BOSS_CREW_AT_THE_POOL).Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
        CHECK(ArenaFor(kBossCount).Empty());

        // the Pyramid's region holds every place of the event, and nothing of the other rooms
        for (Point3 const& p : { kExecutionerSpawn, kLanding, kStairFoot, kStairLip, kPlazaCenter, kWeegliDoorSpot,
            kEndDoor })
            CHECK(InPyramidRegion(p.XY()));
        for (WaveSpawn const& w : kWaveSpawns)
        {
            CHECK(InPyramidRegion(w.at.XY()));
            // the 8 points under the ramp are on the stair's foot, the rest on the plaza's floor
            CHECK(PlazaArena().Contains(w.at.XY(), w.at.z) || StairArena().Contains(w.at.XY(), w.at.z)
                || w.at.z > 10.f);
        }
        for (Point3 const& p : { kZumrahSpawn, kUkorzSpawn, kVelrathaSpawn, kThekaSpawn })
            CHECK(!InPyramidRegion(p.XY()));
        // the wave tables: 23 + 24 + 7 (five trolls, Sezz'ziz, Nekrum), Sezz'ziz and Nekrum last, facing the stair
        std::array<std::uint32_t, 4> count{};
        for (WaveSpawn const& w : kWaveSpawns)
            ++count[w.wave];
        CHECK(count[1] == 23 && count[2] == 24 && count[3] == 7);
        CHECK(kWaveSpawns[52].entry == NPC_SEZZZIZ && kWaveSpawns[53].entry == NPC_NEKRUM);
        CHECK(kWaveSpawns[52].at.o == kAltarFacing && kWaveSpawns[0].at.o == kWaveFacing);
        // the crew's points
        for (std::uint32_t m = 0; m < kCrewCount; ++m)
        {
            CHECK(PyramidTopArena().Contains(kCrewSpawns[m].XY(), kCrewSpawns[m].z));
            CHECK(PyramidTopArena().Contains(kCrewStairPoints[m].XY(), kCrewStairPoints[m].z));
            CHECK(PlazaArena().Contains(kCrewGatherPoints[m].XY(), kCrewGatherPoints[m].z));
        }
        // section 7 #33 A: the four fighters 8 yd west (+y) of the stock spots, Weegli where he was
        CHECK(std::fabs(kCrewGatherPoints[CREW_BLY].y - 1200.83f - 8.f) < 0.01f);
        CHECK(std::fabs(kCrewGatherPoints[CREW_WEEGLI].y - 1199.63f) < 0.01f);
    }

    void TestHealth()
    {
        // normal = the engine's ceil(base x HealthModifier) of the DT rows (section 3.6, x1.6)
        CHECK(Health::kTheka.normal == EngineHealth(1919, 91.7f));
        CHECK(Health::kAntusul.normal == EngineHealth(1535, 104.2f));
        CHECK(Health::kZumrah.normal == EngineHealth(1535, 114.7f));
        CHECK(Health::kExecutioner.normal == EngineHealth(1919, 70.9f));
        CHECK(Health::kSezzziz.normal == EngineHealth(1535, 62.5f));
        CHECK(Health::kNekrum.normal == EngineHealth(1848, 26.0f));
        CHECK(Health::kUkorz.normal == EngineHealth(1919, 75.0f));
        CHECK(Health::kRuuzlu.normal == EngineHealth(1848, 69.3f));
        CHECK(Health::kVelratha.normal == EngineHealth(1343, 83.4f));
        CHECK(Health::kGahzrilla.normal == EngineHealth(1919, 108.4f));
        // the hard mode at least the heroic (the shared rule)
        CHECK(Health::kHardModeVelratha >= Health::kVelratha.heroic);
        CHECK(Health::kHardModeGahzrilla >= Health::kGahzrilla.heroic);
        // about x1.6 of the spec (110,000 Theka) and x4/3 of the heroic spec (279,900)
        CHECK(Health::kTheka.normal > 175000 && Health::kTheka.normal < 177000);
        CHECK(Health::kTheka.heroic > 372000 && Health::kTheka.heroic < 374000);
    }

    // Section 3.5 rule 27 (LESSONS L1): every `struct boss_` of a boss file calls ZulFarrak::NoAssist(me) in its
    // UpdateAI before UpdateVictim(); every boss_*.cpp of the folder is listed in kBossFiles.
    void TestNoAssistInEveryBossFile()
    {
        std::filesystem::path const dir = SourceDir();
        CHECK(std::filesystem::is_directory(dir));
        std::set<std::string> listed;
        for (char const* file : kBossFiles)
        {
            listed.insert(file);
            std::string const text = ReadFile(dir / file);
            CHECK(!text.empty());
            std::size_t const bosses = Count(text, "\nstruct boss_");
            CHECK(bosses >= 1);
            std::size_t checked = 0;
            for (std::size_t at = text.find("\nstruct boss_"); at != std::string::npos;
                at = text.find("\nstruct boss_", at + 1))
            {
                std::size_t const next = text.find("\nstruct ", at + 1);
                std::string const body = text.substr(at, next == std::string::npos ? std::string::npos : next - at);
                std::size_t const update = body.find("void UpdateAI(");
                CHECK(update != std::string::npos);
                if (update == std::string::npos)
                    continue;
                std::size_t const victim = body.find("UpdateVictim()", update);
                CHECK(victim != std::string::npos);
                std::size_t const call = body.find("ZulFarrak::NoAssist(me);", update);
                CHECK(call != std::string::npos && call < victim);
                ++checked;
            }
            CHECK(checked == bosses);
        }
        for (auto const& entry : std::filesystem::directory_iterator(dir))
        {
            std::string const name = entry.path().filename().string();
            if (name.rfind("boss_", 0) == 0 && entry.path().extension() == ".cpp")
                CHECK(listed.count(name) == 1);
        }
    }
}

int main()
{
    TestSlotsAndIds();
    TestSlices();
    TestStageMachine();
    TestCrewModes();
    TestPathsAndTest();
    TestDoorAndPool();
    TestSave();
    TestGeometry();
    TestHealth();
    TestNoAssistInEveryBossFile();
    return Report("zul_farrak_test");
}
