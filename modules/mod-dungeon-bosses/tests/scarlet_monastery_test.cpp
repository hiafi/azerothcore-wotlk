// Host tests for the Scarlet Monastery skeleton (WP-S0): ScarletMonasteryRework.h (the 18 boss states, every stock data
// id on its stock number, the Horseman quirk, the Cathedral pair split and its mirrors, the Chapel Door start and the
// crossing restart, the Ashbringer guard and sweep, Herod's Door and lever, the hard mode triggers, entries, the wave
// switch, slices, measured points, wings, Finder sections, wing portals, arenas, encounter bits, texts, the save string
// and its stock reader). DB positions (spawns, objects, triggers) are exact; the rest is the NAVMESH report's.
#include "HaldenLogic.h"
#include "HerodLogic.h"
#include "IronspineLogic.h"
#include "ScarletMonasteryRework.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace ScarletMonasteryRework;
namespace State = DungeonKit::State;

namespace
{
    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    float Distance2(Vec2 a, Vec2 b)
    {
        return std::hypot(a.x - b.x, a.y - b.y);
    }

    struct BossSpot
    {
        std::uint32_t boss;
        Point3 at;
    };

    // Where each boss stands at the pull (stock spawns, or the build's spots for the new and moved ones).
    std::vector<BossSpot> const kSpots{
        { BOSS_VISHAS, kVishasSpawn }, { BOSS_IRONSPINE, kIronspineHome }, { BOSS_COUNCIL, kCouncilLawn },
        { BOSS_THALNOS, kThalnosSpawn }, { BOSS_DESECRATION, kThalnosSpawn }, { BOSS_DESECRATION, kCouncilLawn },
        { BOSS_LOKSEY, kLokseySpawn }, { BOSS_KELL, kKellSpot }, { BOSS_HOLLIS_GREY, kHollisGreySpot },
        { BOSS_DOAN, kDoanSpawn }, { BOSS_CRELL, kCrellAnvil }, { BOSS_HALDEN, kHaldenSpot },
        { BOSS_HEROD, kHerodSpawn }, { BOSS_THORNE, kThorneSpot }, { BOSS_LAST_STAND, kMograineSpawn },
        { BOSS_LAST_STAND, kMograineBody }, { BOSS_WHITEMANE, kWhitemaneSpawn }, { BOSS_WHITEMANE, kWhitemaneVigil },
        { BOSS_THE_TRUTH, kWhitemaneVigil } };

    void TestBossStates()
    {
        CHECK(kBossCount == 18);
        CHECK(kEncounterCount == 14);
        // Slots 0-6 are the stock DungeonEncounter bits (444-450, read from the DBC 2026-11-20), Fairbanks's bit 5
        // re-pointed to the Last Stand; 7-13 FD-SM's new rows; 14-17 the hard mode kills.
        CHECK(BOSS_VISHAS == 0 && BOSS_THALNOS == 1 && BOSS_LOKSEY == 2 && BOSS_DOAN == 3 && BOSS_HEROD == 4);
        CHECK(BOSS_LAST_STAND == 5 && BOSS_WHITEMANE == 6 && BOSS_IRONSPINE == 7 && BOSS_COUNCIL == 8);
        CHECK(BOSS_KELL == 9 && BOSS_HOLLIS_GREY == 10 && BOSS_CRELL == 11 && BOSS_HALDEN == 12 && BOSS_THORNE == 13);
        CHECK(BOSS_DESECRATION == 14 && BOSS_HERESY == 15 && BOSS_CALL_TO_ARMS == 16 && BOSS_THE_TRUTH == 17);
        for (std::uint32_t id = 0; id < kBossCount; ++id)
        {
            CHECK(kBossNames[id] != nullptr && std::string(kBossNames[id]).size() > 3);
            CHECK(IsEncounterSlot(id) == (id < 14));
            CHECK(IsHardModeSlot(id) == (id >= 14));
            CHECK(SectionOf(id) >= 1 && SectionOf(id) <= 4);
        }
        CHECK(SectionOf(kBossCount) == 0);
        // The hard modes sit on the four end bosses, both ways round.
        std::array<std::uint32_t, 4> const ends{ { BOSS_THALNOS, BOSS_DOAN, BOSS_HEROD, BOSS_WHITEMANE } };
        std::array<std::uint32_t, 4> const kills{ { BOSS_DESECRATION, BOSS_HERESY, BOSS_CALL_TO_ARMS,
            BOSS_THE_TRUTH } };
        std::array<std::uint32_t, 4> const flags{ { DATA_HARD_MODE_THALNOS, DATA_HARD_MODE_DOAN, DATA_HARD_MODE_HEROD,
            DATA_HARD_MODE_WHITEMANE } };
        for (std::size_t i = 0; i < 4; ++i)
        {
            CHECK(HardModeKillSlot(ends[i]) == kills[i]);
            CHECK(HardModeBoss(kills[i]) == ends[i]);
            CHECK(HardModeFlagData(kills[i]) == flags[i]);
            CHECK(SectionOf(kills[i]) == SectionOf(ends[i]));
            CHECK(kSections[i].endSlot == ends[i]);
        }
        CHECK(HardModeKillSlot(BOSS_VISHAS) == kBossCount);
        CHECK(HardModeBoss(BOSS_VISHAS) == kBossCount);
        CHECK(HardModeFlagData(BOSS_VISHAS) == 0);
        // Sections: the Graveyard 4 encounters, the Library 4, the Armory 3, the Cathedral 3.
        std::array<int, 5> perSection{};
        for (std::uint32_t id = 0; id < kEncounterCount; ++id)
            ++perSection[SectionOf(id)];
        CHECK(perSection[1] == 4 && perSection[2] == 4 && perSection[3] == 3 && perSection[4] == 3);
    }

    void TestStockDataIds()
    {
        // Every stock data id of instance_scarlet_monastery.cpp keeps its number (also static_asserted).
        CHECK(TYPE_MOGRAINE_AND_WHITE_EVENT == 1 && TYPE_ASHBRINGER_EVENT == 2 && DATA_MOGRAINE == 3);
        CHECK(DATA_WHITEMANE == 4 && DATA_DOOR_WHITEMANE == 5 && DATA_HORSEMAN_EVENT == 6 && DATA_VORREL == 7);
        CHECK(DATA_ARCANIST_DOAN == 8 && DATA_DOOR_CHAPEL == 9 && GAMEOBJECT_PUMPKIN_SHRINE == 10);
        // hallows_end.cpp's Horseman id is 5: GetData(5) answers 0 whatever SetData(5) received (live behavior).
        CHECK(kHallowsEndHorsemanData == 5);
        for (std::uint32_t v : { State::NotStarted, State::InProgress, State::Fail, State::Done, State::Special })
            CHECK(HorsemanGetData(v) == 0);
        // New data ids clear the stock ones and the boss guid keys.
        std::set<std::uint32_t> const ids{ DATA_HORSEMAN_PRIVATE, DATA_LAST_STAND, DATA_CATHEDRAL_STAGE,
            DATA_CHAPEL_DOOR_OPENED, DATA_DESECRATION_TOUCH, DATA_DESECRATION_RESULT, DATA_HARD_MODE_THALNOS,
            DATA_DOAN_PAGE_READ, DATA_HARD_MODE_DOAN, DATA_HARD_MODE_HEROD, DATA_HARD_MODE_WHITEMANE, DATA_PORTALS,
            DATA_DOAN_PAGES_MASK, DATA_ASHBRINGER_REFUSED, DATA_GM_SLOT_WRITE, DATA_GM_PORTAL, DATA_GM_HARD_MODE };
        CHECK(ids.size() == 17);
        for (std::uint32_t id : ids)
            CHECK(id > GAMEOBJECT_PUMPKIN_SHRINE && id < kGuidBossBase);
        CHECK(kGuidBossBase + kBossCount <= kGuidAzshir && kGuidAzshir < kGuidFairbanks);
    }

    void TestCathedral()
    {
        // GetData(1) / GetData(6) once wave 2 binds: one stock value for the pair.
        CHECK(CathedralMirror(State::NotStarted, State::NotStarted) == State::NotStarted);
        CHECK(CathedralMirror(State::InProgress, State::NotStarted) == State::InProgress);
        CHECK(CathedralMirror(State::Done, State::NotStarted) == State::NotStarted);
        CHECK(CathedralMirror(State::Done, State::InProgress) == State::InProgress);
        CHECK(CathedralMirror(State::Done, State::Done) == State::Done);
        CHECK(CathedralMirror(State::Fail, State::NotStarted) == State::NotStarted);

        // The stage a cold load restores (a reload with the Last Stand DONE: Mograine fallen, Whitemane at her vigil).
        CHECK(CathedralStageFor(State::NotStarted, State::NotStarted) == CathedralStage::BeforeStand);
        CHECK(CathedralStageFor(State::InProgress, State::NotStarted) == CathedralStage::StandRunning);
        CHECK(CathedralStageFor(State::Done, State::NotStarted) == CathedralStage::Vigil);
        CHECK(CathedralStageFor(State::Done, State::InProgress) == CathedralStage::Vigil);
        CHECK(CathedralStageFor(State::Done, State::Done) == CathedralStage::Done);
        // A save never holds IN_PROGRESS: the Last Stand DONE reloads as the vigil.
        CHECK(CathedralStageFor(DungeonKit::SanitizeLoadedState(State::Done),
            DungeonKit::SanitizeLoadedState(State::InProgress)) == CathedralStage::Vigil);

        // The Chapel Door starts the stand only once wave 2 binds, never after the Ashbringer, from NOT_STARTED / FAIL.
        CHECK(LastStandStartAllowed(State::NotStarted, false, true));
        CHECK(LastStandStartAllowed(State::Fail, false, true));
        CHECK(!LastStandStartAllowed(State::NotStarted, false, false));
        CHECK(!LastStandStartAllowed(State::NotStarted, true, true));
        CHECK(!LastStandStartAllowed(State::InProgress, false, true));
        CHECK(!LastStandStartAllowed(State::Done, false, true));

        // The crossing restart re-arms only with the door open and slot 5 NOT_STARTED.
        CHECK(CrossingRestartArmed(State::NotStarted, true, false, true));
        CHECK(!CrossingRestartArmed(State::NotStarted, false, false, true));
        CHECK(!CrossingRestartArmed(State::InProgress, true, false, true));
        CHECK(!CrossingRestartArmed(State::Done, true, false, true));
        CHECK(!CrossingRestartArmed(State::NotStarted, true, true, true));
        CHECK(!CrossingRestartArmed(State::NotStarted, true, false, false));
        // The line: inside the door, across the opening; not outside, not deep in the nave.
        CHECK(InCrossingLine({ 1078.f, 1399.f }, 30.9f));
        CHECK(!InCrossingLine({ 1066.f, 1399.f }, 30.9f));          // the landing outside
        CHECK(!InCrossingLine({ 1104.8f, 1399.2f }, 30.9f));        // the nave's second disc
        CHECK(!InCrossingLine({ 1078.f, 1399.f }, 20.f));           // under the nave
        CHECK(kCrossingMinX > kChapelDoor.x);

        // Whitemane's slot opens only after the Last Stand.
        CHECK(!WhitemaneWriteAccepted(State::InProgress, State::NotStarted, true));
        CHECK(!WhitemaneWriteAccepted(State::Done, State::InProgress, true));
        CHECK(WhitemaneWriteAccepted(State::InProgress, State::Done, true));
        CHECK(WhitemaneWriteAccepted(State::Done, State::Done, true));
        CHECK(WhitemaneWriteAccepted(State::NotStarted, State::NotStarted, true));
        CHECK(WhitemaneWriteAccepted(State::InProgress, State::NotStarted, false));     // stock while wave 2 is unbound

        // The vigil sits on the crossing beside Mograine's body, both on the stand's floor.
        CHECK(Distance2(kWhitemaneVigil.XY(), kMograineBody.XY()) < 10.f);
        CHECK(In(LastStandArena(), kWhitemaneVigil) && In(LastStandArena(), kMograineBody));
    }

    void TestAshbringer()
    {
        // Refused while a Cathedral slot fights; stock while wave 2 is unbound also refuses during the stock pair.
        CHECK(AshbringerAllowed(State::NotStarted, State::NotStarted, State::NotStarted, 0, true));
        CHECK(AshbringerAllowed(State::Done, State::Done, State::Done, 0, true));
        // ... and once the Last Stand is DONE while Whitemane lives (R-2-FW MN-3: it would despawn her at her vigil).
        CHECK(!AshbringerAllowed(State::Done, State::NotStarted, State::Done, 0, true));
        CHECK(!AshbringerAllowed(State::Done, State::Fail, State::NotStarted, 0, true));
        CHECK(!AshbringerAllowed(State::InProgress, State::NotStarted, State::NotStarted, 0, true));
        CHECK(!AshbringerAllowed(State::Done, State::InProgress, State::NotStarted, 0, true));
        CHECK(!AshbringerAllowed(State::NotStarted, State::NotStarted, State::InProgress, 0, true));
        CHECK(!AshbringerAllowed(State::NotStarted, State::NotStarted, State::NotStarted, State::InProgress, false));
        CHECK(AshbringerAllowed(State::NotStarted, State::NotStarted, State::NotStarted, State::Done, false));
        // A reload after the event keeps the sweep (R-1-KIT m-2): swept and alive only, and only once it ran.
        std::uint32_t const cathedral = WingOf(kMograineSpawn.XY());
        CHECK(cathedral == kAshbringerWing && WingOf(kWhitemaneSpawn.XY()) == cathedral);
        CHECK(AshbringerKeepsFriendly(true, NPC_SCARLET_MONK, true, true, cathedral));
        CHECK(!AshbringerKeepsFriendly(false, NPC_SCARLET_MONK, true, true, cathedral));
        CHECK(!AshbringerKeepsFriendly(true, NPC_SCARLET_MONK, false, true, cathedral));
        CHECK(!AshbringerKeepsFriendly(true, NPC_VISHAS, true, true, cathedral));
        // ... and only the Cathedral's own spawns (RF-1 m-1): no summon, nothing of another wing (Loksey, Doan, Herod
        // and his trainees), even after a grid loads late.
        CHECK(!AshbringerKeepsFriendly(true, NPC_SCARLET_MONK, true, false, cathedral));
        CHECK(!AshbringerKeepsFriendly(true, NPC_LOKSEY, true, true, WingOf(kSections[1].start.XY())));
        CHECK(!AshbringerKeepsFriendly(true, NPC_DOAN, true, true, 2));
        CHECK(!AshbringerKeepsFriendly(true, NPC_HEROD, true, true, WingOf(kHerodSpawn.XY())));
        CHECK(!AshbringerKeepsFriendly(true, NPC_SCARLET_TRAINEE, true, false, WingOf(kHerodSpawn.XY())));
        CHECK(!AshbringerKeepsFriendly(true, NPC_SCARLET_MONK, true, true, 0));
        CHECK(AshbringerSweepsUnit(NPC_MOGRAINE, true, cathedral));
        CHECK(AshbringerSweepsUnit(NPC_FAIRBANKS, true, cathedral));
        CHECK(!AshbringerSweepsUnit(NPC_LOKSEY, true, 2) && !AshbringerSweepsUnit(NPC_HIGHLORD_MOGRAINE, false, 4));
        // The sweep: the stock Graveyard list and every rework entry stay hostile; the Cathedral and the rest turn.
        for (std::uint32_t entry : { 721u, 3983u, 4075u, 4283u, 4293u, 4308u, 4306u, 6426u, 6427u, 6488u, 4543u,
            6547u })
            CHECK(!AshbringerSweeps(entry));
        for (std::uint32_t entry = kGearCreaturesFirst; entry <= kCreaturesLast; ++entry)
            CHECK(!AshbringerSweeps(entry));
        for (std::uint32_t entry : { 3976u, 3977u, 4542u, 3975u, 3974u, 6487u, 4301u, 4540u, 16062u })
            CHECK(AshbringerSweeps(entry));
    }

    void TestHerodsDoor()
    {
        CHECK(HerodsDoorMoveFor(State::NotStarted, State::InProgress) == DoorMove::Close);
        CHECK(HerodsDoorMoveFor(State::InProgress, State::Done) == DoorMove::Open);
        CHECK(HerodsDoorMoveFor(State::InProgress, State::NotStarted) == DoorMove::Open);
        CHECK(HerodsDoorMoveFor(State::InProgress, State::Fail) == DoorMove::Open);
        CHECK(HerodsDoorMoveFor(State::NotStarted, State::NotStarted) == DoorMove::None);
        CHECK(!HerodsLeverUsable(State::InProgress));
        CHECK(HerodsLeverUsable(State::NotStarted) && HerodsLeverUsable(State::Done));
        CHECK(AttemptEnded(State::InProgress, State::Fail) && !AttemptEnded(State::NotStarted, State::NotStarted));
        CHECK(SettledSlotState(State::ToBeDecided) == State::NotStarted);
        CHECK(SettledSlotState(State::Done) == State::Done);
    }

    void TestHardModeTriggers()
    {
        // The Desecration: heroic, Thalnos idle, the council DONE, not lit.
        CHECK(DesecrationTouchAllowed(true, State::NotStarted, State::Done, false));
        CHECK(!DesecrationTouchAllowed(false, State::NotStarted, State::Done, false));
        CHECK(!DesecrationTouchAllowed(true, State::InProgress, State::Done, false));
        CHECK(!DesecrationTouchAllowed(true, State::Done, State::Done, false));
        CHECK(!DesecrationTouchAllowed(true, State::NotStarted, State::NotStarted, false));
        CHECK(!DesecrationTouchAllowed(true, State::NotStarted, State::Done, true));
        CHECK(JudgeDesecration({ { 0, 1, 2, 3 } }) == DesecrationVerdict::Right);
        CHECK(JudgeDesecration({ { 1, 0, 2, 3 } }) == DesecrationVerdict::Wrong);
        CHECK(JudgeDesecration({ { 3, 2, 1, 0 } }) == DesecrationVerdict::Wrong);
        CHECK(GO_SM_GRAVESTONE_GALVAR + 3 == GO_SM_GRAVESTONE_GOODCHILDE);

        // The Heresy: four pages, each once, heroic, Doan idle.
        CHECK(DoanPageAllowed(true, State::NotStarted, 0, 0));
        CHECK(!DoanPageAllowed(true, State::NotStarted, 1, 0));
        CHECK(DoanPageAllowed(true, State::NotStarted, 1, 3));
        CHECK(!DoanPageAllowed(true, State::NotStarted, 0, 4));
        CHECK(!DoanPageAllowed(false, State::NotStarted, 0, 0));
        CHECK(!DoanPageAllowed(true, State::InProgress, 0, 0));
        CHECK(!DoanPageAllowed(true, State::Done, 0, 0));
        CHECK(DoanPagesRead(0) == 0 && DoanPagesRead(0b1010) == 2 && DoanPagesRead(kDoanPagesAll) == 4);
        CHECK(kDoanPagesAll == 0xF);

        // Call to Arms: heroic, wave 2 bound, Herod idle.
        CHECK(HerodTauntAllowed(true, State::NotStarted, false, true));
        CHECK(HerodTauntAllowed(true, State::Fail, false, true));
        CHECK(!HerodTauntAllowed(true, State::NotStarted, false, false));
        CHECK(!HerodTauntAllowed(false, State::NotStarted, false, true));
        CHECK(!HerodTauntAllowed(true, State::InProgress, false, true));
        CHECK(!HerodTauntAllowed(true, State::NotStarted, true, true));

        // The Truth (section 7 #21 A): heroic, the Last Stand DONE, Whitemane not pulled.
        CHECK(TorchAllowed(true, State::Done, State::NotStarted, false, true));
        CHECK(!TorchAllowed(true, State::NotStarted, State::NotStarted, false, true));
        CHECK(!TorchAllowed(true, State::Done, State::InProgress, false, true));
        CHECK(!TorchAllowed(true, State::Done, State::Done, false, true));
        CHECK(!TorchAllowed(false, State::Done, State::NotStarted, false, true));
        CHECK(!TorchAllowed(true, State::Done, State::NotStarted, false, false));
    }

    void TestWaveSwitch()
    {
        CHECK(kWave2Bound);     // both waves bound (W2-SETUP 2026-11-20); the gate stays to check wave 1 alone
        for (std::uint32_t id : { BOSS_VISHAS, BOSS_THALNOS, BOSS_LOKSEY, BOSS_DOAN, BOSS_IRONSPINE, BOSS_COUNCIL,
            BOSS_KELL, BOSS_HOLLIS_GREY, BOSS_DESECRATION, BOSS_HERESY })
            CHECK(!IsWave2Boss(id));
        for (std::uint32_t id : { BOSS_HEROD, BOSS_LAST_STAND, BOSS_WHITEMANE, BOSS_CRELL, BOSS_HALDEN, BOSS_THORNE,
            BOSS_CALL_TO_ARMS, BOSS_THE_TRUTH })
            CHECK(IsWave2Boss(id));
        // Who writes a slot: the reworked BossAIs of a bound wave; the instance the council, the Last Stand, the
        // hard mode kills and (wave 2 unbound) the stock deaths.
        CHECK(SlotWrittenByScript(BOSS_VISHAS, false) && SlotWrittenByScript(BOSS_IRONSPINE, false));
        CHECK(!SlotWrittenByScript(BOSS_COUNCIL, true) && !SlotWrittenByScript(BOSS_LAST_STAND, true));
        CHECK(!SlotWrittenByScript(BOSS_HEROD, false) && SlotWrittenByScript(BOSS_HEROD, true));
        CHECK(!SlotWrittenByScript(BOSS_WHITEMANE, false) && SlotWrittenByScript(BOSS_WHITEMANE, true));
        for (std::uint32_t id = BOSS_DESECRATION; id < kBossCount; ++id)
            CHECK(!SlotWrittenByScript(id, true));
    }

    void TestIds()
    {
        // The spell slices tile the reservation 212300-213499, below the item-copy pool 219000.
        CHECK(kSpellsReservation.first == 212300 && kSpellsReservation.last == 213499);
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        CHECK(kSpellSlices.back().last == kSpellsReservation.last);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        CHECK(kSpellsReservation.last < 219000);
        CHECK(kSpellsSpareWave1.last == 212899 && kSpellsCrell.first == 212900);
        CHECK(kSpellCouncilCredit == 212300 && kSpellLastStandCredit == 212301);

        // Creatures: wave 1 below wave 2 (the heroic mint order).
        std::vector<std::uint32_t> const wave1{ NPC_SM_IRONSPINE_FIST, NPC_SM_IRONSPINE_RIBCAGE, NPC_SM_IRONSPINE_EYE,
            NPC_SM_GALVAR, NPC_SM_FAIRBELL, NPC_SM_VOSS, NPC_SM_GOODCHILDE, NPC_SM_RALLYING_BANNER,
            NPC_SM_TRACKING_HOUND, NPC_SM_KENNEL_PUP, NPC_SM_KELL, NPC_SM_RELIC_TRIGGER, NPC_SM_GALLERY_SKELETON,
            NPC_SM_HOLLIS_GREY, NPC_SM_CURSED_BOOK, NPC_SM_INFERNAL, NPC_SM_SPIDERLING, NPC_SM_SPECTRAL_TROLL,
            NPC_SM_PHANTOM_GRUNT, NPC_SM_ARCANE_ANCHOR, NPC_SM_PHYLACTERY_SHARD, NPC_SM_RISEN_PURGED, NPC_SM_STALKER };
        std::vector<std::uint32_t> const wave2{ NPC_SM_CRELL, NPC_SM_SCARLET_RECRUIT, NPC_SM_HALDEN,
            NPC_SM_DRILL_RECRUIT, NPC_SM_GARRISON_TRAINEE, NPC_SM_PLANTED_RAVAGER, NPC_SM_THORNE, NPC_SM_SEEDLING,
            NPC_SM_BRIAR, NPC_SM_BLESSED_BRAMBLE, NPC_SM_CHAPEL_GUARD_CHAMPION, NPC_SM_CAPTAIN_OF_THE_GUARD,
            NPC_SM_COMPANY_CHAPLAIN, NPC_SM_COMPANY_MONK, NPC_SM_COMPANY_WIZARD, NPC_SM_COMPANY_ABBOT,
            NPC_SM_VIGIL_FAIRBANKS, NPC_SM_ALEXANDROS_SPIRIT, NPC_SM_STALKER_WAVE2 };
        CHECK(wave1.size() == 23 && wave2.size() == 19);
        for (std::size_t i = 0; i < wave1.size(); ++i)
            CHECK(wave1[i] == 300900 + i && kCreaturesWave1.Contains(wave1[i]));
        for (std::size_t i = 0; i < wave2.size(); ++i)
            CHECK(wave2[i] == 300940 + i && kCreaturesWave2.Contains(wave2[i]));
        CHECK(kCreaturesWave1.last + 1 == kCreaturesWave2.first);
        CHECK(kCreaturesReservation.first == 300900 && kCreaturesReservation.last == 300979);

        // Gameobjects 301310-301331 in the reservation 301310-301339.
        for (std::uint32_t go = GO_SM_GRAVESTONE_GALVAR; go <= GO_SM_LAST_STAND_CHEST_H; ++go)
            CHECK(kGameObjectsReservation.Contains(go));
        CHECK(GO_SM_WING_PORTAL == 301324 && GO_SM_CHAMBER_SEAL == 301319);

        // Boss entries map to their slots; the council's two entries share one.
        CHECK(*BossOfEntry(NPC_AZSHIR) == BOSS_COUNCIL && *BossOfEntry(NPC_FALLEN_CHAMPION) == BOSS_COUNCIL);
        CHECK(*BossOfEntry(NPC_MOGRAINE) == BOSS_LAST_STAND && *BossOfEntry(NPC_WHITEMANE) == BOSS_WHITEMANE);
        CHECK(*BossOfEntry(NPC_SM_THORNE) == BOSS_THORNE && !BossOfEntry(NPC_FAIRBANKS));
        std::set<std::uint32_t> slots;
        for (std::uint32_t entry : { 3983u, 4543u, 3974u, 6487u, 3975u, 3976u, 3977u, 6489u, 6490u, 300910u,
            300913u, 300940u, 300942u, 300946u })
            slots.insert(*BossOfEntry(entry));
        CHECK(slots.size() == kEncounterCount);
    }

    void TestTexts()
    {
        std::set<std::uint32_t> entries;
        for (TextRange const& t : kTextRanges)
        {
            CHECK(t.first <= t.last);
            CHECK(t.firstNew >= t.first && t.firstNew <= t.last + 1);
            CHECK(entries.insert(t.entry).second);
        }
        CHECK(entries.count(NPC_VISHAS) && entries.count(NPC_THALNOS) && entries.count(NPC_MOGRAINE)
            && entries.count(NPC_WHITEMANE) && entries.count(NPC_HEROD) && entries.count(NPC_DOAN));
    }

    void TestSectionsAndWings()
    {
        std::array<std::uint32_t, 4> const lfg{ { 18, 165, 163, 164 } };
        for (std::size_t i = 0; i < kSections.size(); ++i)
        {
            FinderSection const& s = kSections[i];
            CHECK(s.number == i + 1);
            CHECK(SectionByNumber(s.number) == &s);
            CHECK(s.lfgNormal == lfg[i]);
            CHECK(s.lfgHeroic == 314 + i);
            // The start, its exit trigger and the end boss sit in the section's own wing.
            CHECK(WingOf(s.start.XY()) == s.number);
            CHECK(WingOf(s.exitTrigger.XY()) == s.number);
            CHECK(SectionOf(s.endSlot) == s.number);
            // The start is clear of its exit trigger (r 8: the stock rows are 12-18 yd apart).
            CHECK(Distance2(s.start.XY(), s.exitTrigger.XY()) > kExitTriggerRadius + 4.f);
        }
        CHECK(SectionByNumber(0) == nullptr && SectionByNumber(5) == nullptr);
        // Each boss spot is in its section's wing; wings do not overlap (one wing per spot).
        for (BossSpot const& b : kSpots)
            CHECK(WingOf(b.at.XY()) == SectionOf(b.boss));
        CHECK(WingOf({ 0.f, 0.f }) == 0);
        // The doors on the path: the Library's seal, Herod's Door, the Chapel and High Inquisitor's doors.
        CHECK(kSections[1].doors[0] == GO_SM_CHAMBER_SEAL);
        CHECK(kSections[2].doors[0] == GO_HERODS_DOOR);
        CHECK(kSections[3].doors[0] == GO_CHAPEL_DOOR && kSections[3].doors[1] == GO_HIGH_INQUISITOR_DOOR);
        CHECK(kSections[0].doors[0] == 0);
        CHECK(WingOf(kChapelDoor.XY()) == 4 && WingOf(kHerodsDoor.XY()) == 3);
    }

    void TestPortals()
    {
        // P1 / P1h from the Graveyard, P2 from the Library, P3 from the Armory; none after Whitemane.
        CHECK(kPortals.size() == 4);
        for (WingPortal const& p : kPortals)
        {
            CHECK(PortalById(p.id) == &p);
            CHECK(PortalBit(p.id) != 0);
            FinderSection const* from = SectionByNumber(SectionOf(p.openSlot));
            CHECK(from != nullptr);
            CHECK(WingOf(p.spot.XY()) == from->number);
            CHECK(p.toSection == from->number + 1);
            CHECK(from->endSlot == p.openSlot);
            // At least 8 yd (plus margin) from every exit trigger, and its landing too.
            for (FinderSection const& s : kSections)
                CHECK(Distance2(p.spot.XY(), s.exitTrigger.XY()) > kExitTriggerRadius);
            CHECK(PortalNear(p.spot.XY()) == &p);
        }
        CHECK(PortalById(0) == nullptr && PortalById(5) == nullptr && PortalBit(0) == 0 && PortalBit(5) == 0);
        CHECK(PortalNear({ 1.f, 1.f }) == nullptr);
        // P1h stands where the hard mode lands (the lawn), P1 in the crypt.
        CHECK(In(ThalnosArena(), kPortals[0].spot.P3()) && !In(ThalnosArena(), kPortals[1].spot.P3()));
        CHECK(In(DesecrationArena(), kPortals[1].spot.P3()));
        CHECK(In(DoanArena(), kPortals[2].spot.P3()) && In(HerodArena(), kPortals[3].spot.P3()));
        // P2 / P3 stand clear of the end boss's corpse (a misclick while looting is a group teleport).
        CHECK(Distance2(kPortals[2].spot.XY(), kDoanSpawn.XY()) >= kPortalBossClearance);
        CHECK(Distance2(kPortals[3].spot.XY(), kHerodSpawn.XY()) >= kPortalBossClearance);
        CHECK(!PortalHasVariant(kPortals[2]) && !PortalHasVariant(kPortals[3]));
        CHECK(PortalHasVariant(kPortals[0]) && PortalHasVariant(kPortals[1]));

        // From the slots (restored on a reload).
        std::array<std::uint32_t, kBossCount> states{};
        CHECK(PortalsOpenMask(states) == 0);
        states[BOSS_THALNOS] = State::Done;
        CHECK(PortalsOpenMask(states) == PortalBit(1));
        states[BOSS_DESECRATION] = State::Done;
        CHECK(PortalsOpenMask(states) == PortalBit(2));
        states[BOSS_DOAN] = State::Done;
        states[BOSS_HEROD] = State::Done;
        states[BOSS_WHITEMANE] = State::Done;
        CHECK(PortalsOpenMask(states) == (PortalBit(2) | PortalBit(3) | PortalBit(4)));
        states[BOSS_HEROD] = State::InProgress;
        CHECK(PortalsOpenMask(states) == (PortalBit(2) | PortalBit(3)));
        // A hard mode kill of Doan or Herod still stands P2 / P3 (they have no hard mode variant: R-1-KIT M-1).
        states[BOSS_HEROD] = State::Done;
        states[BOSS_HERESY] = State::Done;
        states[BOSS_CALL_TO_ARMS] = State::Done;
        CHECK(PortalsOpenMask(states) == (PortalBit(2) | PortalBit(3) | PortalBit(4)));
        std::array<std::uint32_t, kBossCount> hardOnly{};
        hardOnly[BOSS_DOAN] = State::Done;
        hardOnly[BOSS_HERESY] = State::Done;
        CHECK(PortalsOpenMask(hardOnly) == PortalBit(3));
        hardOnly[BOSS_HEROD] = State::Done;
        hardOnly[BOSS_CALL_TO_ARMS] = State::Done;
        CHECK(PortalsOpenMask(hardOnly) == (PortalBit(3) | PortalBit(4)));

        // Who goes along: alive, out of combat, within 20 yd.
        CHECK(PortalTakesAlong(20.f, true, false));
        CHECK(!PortalTakesAlong(20.5f, true, false));
        CHECK(!PortalTakesAlong(5.f, false, false));
        CHECK(!PortalTakesAlong(5.f, true, true));
    }

    void TestArenas()
    {
        for (BossSpot const& b : kSpots)
        {
            CHECK(In(ArenaFor(b.boss), b.at));
            CHECK(WingOf(b.at.XY()) == SectionOf(b.boss));
        }
        for (std::uint32_t id = 0; id < kBossCount; ++id)
            CHECK(!ArenaFor(id).Empty());
        CHECK(ArenaFor(kBossCount).Empty());
        // The Herod arena holds the lever (the spur) and the door's inside, not the cross hall outside the door.
        CHECK(In(HerodArena(), kHerodsLever));
        CHECK(!In(HerodArena(), { 1924.f, -431.f, 18.f }));
        // R-2-ARM M-3: the doorway itself (x 1932-1933.7, just outside the door) is outside, so the seal pulls a
        // straggler standing there in; the march's first point and the hall entry stay inside.
        CHECK(!HerodArena().Contains({ 1932.f, -431.6f }, 18.7f));
        CHECK(!HerodArena().Contains(kHerodsDoor.XY(), kHerodsDoor.z));
        CHECK(In(HerodArena(), SmHerod::kGarrisonMarch[0]) && In(HerodArena(), SmHerod::kHallEntry));
        // Ironspine and the council fight on the lawn disc only (D2 / D3 moved their spawns there).
        CHECK(!In(IronspineArena(), kIronspineStockSpawn));
        CHECK(!In(CouncilArena(), kFallenChampionSpawn) && !In(CouncilArena(), kAzshirSpawn));
        // Crell's arena holds the south lobe (y -419: D9).
        CHECK(In(CrellArena(), { 1790.f, -419.f, 8.f }));
        // Halden's arena is D10's mesh boxes (SmHalden::RoomsArena()): the same answer on a 1 yd grid.
        Arena const rooms = SmHalden::RoomsArena();
        Arena const halden = HaldenArena();
        bool same = true;
        for (float x = 1835.f; x <= 1920.f; x += 1.f)
            for (float y = -445.f; y <= -350.f; y += 1.f)
                for (float z : { 15.5f, 19.f, 23.5f })
                    if (rooms.Contains({ x, y }, z) != halden.Contains({ x, y }, z))
                        same = false;
        CHECK(same);
        // Ironspine's arena is D2's cut yard (SmIronspine::FightArena()): the same answer on a 1 yd grid.
        Arena const yard = SmIronspine::FightArena();
        Arena const ironspine = IronspineArena();
        bool sameYard = true;
        for (float x = 1750.f; x <= 1842.f; x += 1.f)
            for (float y = 1240.f; y <= 1330.f; y += 1.f)
                if (yard.Contains({ x, y }, 18.f) != ironspine.Contains({ x, y }, 18.f))
                    sameYard = false;
        CHECK(sameYard);
        CHECK(!In(IronspineArena(), kCouncilLawn));
        // RF-1 m-4: the council's and the Desecration's lawn stop at the yard's north edge (y 1317), so the two never
        // overlap and the lawn stays 31.5 yd from Ironspine's home; the bots' 30 yd bounds stay inside the cut.
        bool overlap = false;
        bool boundsInside = true;
        for (float x = 1750.f; x <= 1842.f; x += 1.f)
            for (float y = 1240.f; y <= 1395.f; y += 1.f)
            {
                Vec2 const p{ x, y };
                if (ironspine.Contains(p, 18.f) && CouncilArena().Contains(p, 18.f) && y < kCouncilLawnSouthY)
                    overlap = true;
                if (Distance2(p, kCouncilLawn.XY()) <= 30.f && !CouncilArena().Contains(p, 18.f))
                    boundsInside = false;
            }
        CHECK(!overlap && boundsInside);
        CHECK(!In(CouncilArena(), { 1798.5f, 1310.f, 18.f }) && !In(DesecrationArena(), { 1798.5f, 1310.f, 18.f }));
        CHECK(In(DesecrationArena(), { 1798.5f, 1320.f, 18.f }) && In(DesecrationArena(), kCouncilLawn));
        CHECK(Distance2(kIronspineHome.XY(), { kCouncilLawn.x, kCouncilLawnSouthY }) > 30.f);
    }

    void TestEncounterBits()
    {
        for (std::uint32_t i = 0; i < kEncounterCount; ++i)
        {
            CHECK(kEncounterBits[i].first == i);
            CHECK(kEncounterBits[i].second == i);     // slot = bit (section 7 #1 A)
        }
        CHECK(DungeonEncounterIdOfBit(0) == 444 && DungeonEncounterIdOfBit(6) == 450);
        CHECK(DungeonEncounterIdOfBit(7) == 1074 && DungeonEncounterIdOfBit(13) == 1080);
        std::array<std::uint32_t, kBossCount> states{};
        ApplyEncounterMask((1u << 1) | (1u << 5) | (1u << 13), states);
        CHECK(states[BOSS_THALNOS] == State::Done && states[BOSS_LAST_STAND] == State::Done);
        CHECK(states[BOSS_THORNE] == State::Done && states[BOSS_VISHAS] == State::NotStarted);
    }

    void TestSave()
    {
        // The header is neither a prefix of the stock "SM" nor prefixed by it.
        std::string const header(kSaveHeader);
        std::string const stock(kStockSaveHeader);
        CHECK(header.rfind(stock, 0) != 0 && stock.rfind(header, 0) != 0);

        // Round trip with every flag and the page mask.
        SmSave s;
        s.states[BOSS_VISHAS] = State::Done;
        s.states[BOSS_THALNOS] = State::Done;
        s.states[BOSS_DESECRATION] = State::Done;
        s.states[BOSS_LAST_STAND] = State::Done;
        s.states[BOSS_COUNCIL] = State::Done;
        s.desecration = 1;
        s.doanPages = 0b0101;
        s.herodTaunted = 1;
        s.torchPulled = 1;
        s.ashbringer = 1;
        std::string const text = FormatSmSave(s);
        CHECK(text.rfind("S C R ", 0) == 0);
        SmSave back;
        CHECK(ParseSmSave(text, back));
        CHECK(back.states == s.states);
        CHECK(back.desecration == 1 && back.doanPages == 0b0101 && back.heresy == 0);
        CHECK(back.herodTaunted == 1 && back.torchPulled == 1 && back.ashbringer == 1);
        CHECK(DoanPagesRead(back.doanPages) == 2);

        // All four pages: the Heresy follows from the mask.
        s.doanPages = kDoanPagesAll;
        CHECK(ParseSmSave(FormatSmSave(s), back) && back.heresy == 1);

        // IN_PROGRESS never survives a reload; a hard mode kill needs its boss DONE; flags go back to 0 / 1.
        s = SmSave{};
        s.states[BOSS_LAST_STAND] = State::InProgress;
        s.states[BOSS_HERESY] = State::Done;            // Doan not DONE
        s.desecration = 7;
        s.doanPages = 0xFF;
        CHECK(ParseSmSave(FormatSmSave(s), back));
        CHECK(back.states[BOSS_LAST_STAND] == State::NotStarted);
        CHECK(back.states[BOSS_HERESY] == State::NotStarted);
        CHECK(back.desecration == 1 && back.doanPages == kDoanPagesAll && back.heresy == 1);

        // A short (older) save keeps the defaults.
        CHECK(ParseSmSave("S C R 3 3", back));
        CHECK(back.states[BOSS_VISHAS] == State::Done && back.states[BOSS_THALNOS] == State::Done);
        CHECK(back.states[BOSS_LOKSEY] == State::NotStarted && back.ashbringer == 0);

        // The stock save ("S M", no data) loads as an empty run, with the completed-encounter mask applied.
        CHECK(ParseSmSave("S M ", back));
        for (std::uint32_t id = 0; id < kBossCount; ++id)
            CHECK(back.states[id] == State::NotStarted);
        CHECK(ParseSmSave("S M", back, (1u << 0) | (1u << 6)));
        CHECK(back.states[BOSS_VISHAS] == State::Done && back.states[BOSS_WHITEMANE] == State::Done);
        CHECK(back.desecration == 0 && back.ashbringer == 0);
        CHECK(ReadStockSave("S M") && !ReadStockSave("S C R 1") && !ReadStockSave("D E 3 3"));

        // Anything else is ignored.
        CHECK(!ParseSmSave("D E 3 3", back));
        CHECK(!ParseSmSave("garbage", back));
    }
}

int main()
{
    TestBossStates();
    TestStockDataIds();
    TestCathedral();
    TestAshbringer();
    TestHerodsDoor();
    TestHardModeTriggers();
    TestWaveSwitch();
    TestIds();
    TestTexts();
    TestSectionsAndWings();
    TestPortals();
    TestArenas();
    TestEncounterBits();
    TestSave();

    return Report("scarlet_monastery_test");
}
