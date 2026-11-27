// Host tests for GnomereganRework.h (WP-S0, the Gnomeregan skeleton): slots and data ids, the id slices, the Workshop
// Door's states and every door state x reload pair, the End NPCs, Crowd Pummeler's chest and every chest state x
// reload pair, the hard mode's console, flag, verdict and loot bit, the Finder sections, the "GNR" save with the stock
// "G N O" reader, the rooms' points against their arenas, the health table, every boss file's NoAssist call (section
// 3.5 rule 29) and the instance's registration under the stock name (npc_kernobee's GetGnomereganAI).
#include "../src/Gnomeregan/GnomereganRework.h"
#include "check.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <string>

using namespace GnomereganRework;
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
        return std::filesystem::path(__FILE__).parent_path().parent_path() / "src" / "Gnomeregan";
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

    float Dist(Point3 const& a, Point3 const& b)
    {
        return std::hypot(a.x - b.x, a.y - b.y);
    }

    void TestSlotsAndIds()
    {
        CHECK(kBossCount == 7);
        CHECK(kEncounterBossCount == 6);
        // slot = DungeonEncounter bit (1107 bit 0, 378 bit 1, 379 bit 2, 380 bit 3, 381 bit 4, 382 bit 5); slot 6 has
        // no row
        CHECK(BOSS_ALERT_SYSTEM == 0 && BOSS_VISCOUS_FALLOUT == 1 && BOSS_TECHBOT == 2);
        CHECK(BOSS_ELECTROCUTIONER == 3 && BOSS_CROWD_PUMMELER == 4 && BOSS_THERMAPLUGG == 5);
        CHECK(BOSS_WHOLE_WORKSHOP == 6);
        CHECK(kEncounterNormal[BOSS_ALERT_SYSTEM] == 1107 && kEncounterNormal[BOSS_TECHBOT] == 379);
        CHECK(kEncounterNormal[BOSS_VISCOUS_FALLOUT] == 378 && kEncounterNormal[BOSS_THERMAPLUGG] == 382);
        std::set<std::uint32_t> const heroic(kEncounterHeroic.begin(), kEncounterHeroic.end());
        CHECK(heroic.size() == 6 && *heroic.begin() == 1108 && *heroic.rbegin() == 1113);
        // the stock data id keeps its number; every data id distinct and apart from the End NPC block
        CHECK(DATA_GRUBBIS == 0);
        std::set<std::uint32_t> const ids{ DATA_GRUBBIS, DATA_WORKSHOP_DOOR, DATA_FINAL_CHAMBER, DATA_SECTION,
            DATA_HARD_MODE, DATA_HARD_MODE_VERDICT, DATA_HARD_MODE_KILLED, DATA_HARD_MODE_KEY, DATA_PUMMELER_CHEST,
            DATA_GM_DOOR, DATA_GM_HARD_MODE, DATA_GM_CHEST, DATA_GM_END_NPC, DATA_GM_SECTION };
        CHECK(ids.size() == 14);
        for (std::uint32_t id : ids)
            CHECK(id <= DATA_END_NPC_BASE || id > DATA_END_NPC_BASE + kEndNpcCount);
        std::set<std::uint32_t> const guids{ kGuidBossBase, kGuidBossBase + BOSS_WHOLE_WORKSHOP, kGuidWorkshopDoor,
            kGuidFinalChamber, kGuidPummelerChest, kGuidEndNpcBase + 1, kGuidEndNpcBase + 2 };
        CHECK(guids.size() == 7);
        CHECK(kGuidBossBase + kBossCount <= kGuidWorkshopDoor);
        // the faces and their buttons by number (ruling 64)
        CHECK(FaceIndexOf(GO_GNOME_FACE_01) == std::optional<std::uint32_t>(0));
        CHECK(FaceIndexOf(GO_GNOME_FACE_04) == std::optional<std::uint32_t>(3));
        CHECK(FaceIndexOf(GO_BUTTON_06) == std::optional<std::uint32_t>(5));
        CHECK(!FaceIndexOf(GO_WORKSHOP_DOOR));
        CHECK(kInstanceScriptName == std::string("instance_gnomeregan"));
        CHECK(kTestCommand == std::string("dbtest gnomer"));
        CHECK(kLogDungeon == std::string("gnomer-build"));
    }

    void TestSlices()
    {
        // the ten slices tile the reservation in order
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        CHECK(kSpellSlices.back().last == kSpellsReservation.last);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        CHECK(kSpellsReservation.first == 214280 && kSpellsReservation.last == 214679);
        CHECK(kSpellsShared.Contains(kSpellWeakenedCopy));
        CHECK(kSpellsTechbot.Size() == 40 && kSpellsPummeler.Size() == 30 && kSpellsThermaplugg.Size() == 50);
        // the build's creatures and game objects sit in the reservation; the gear's bomb does not
        for (std::uint32_t entry : { NPC_TECHBOT, NPC_DUPE_BUG, NPC_LAG_ECHO, NPC_ALERT_SYSTEM, NPC_SECURITY_ASSISTANT,
            NPC_SECURITY_DEFENDER, NPC_LIGHT_STALKER, NPC_FRAME_STALKER, NPC_WALKING_BOMB, NPC_INCENDIARY_BOMB,
            NPC_FROST_BOMB, NPC_RADIOACTIVE_BOMB, NPC_THE_BIG_ONE, NPC_FACE_STALKER, NPC_MINE, NPC_ZONE_STALKER,
            NPC_POOL_STALKER, NPC_BLAST_STALKER, NPC_WANDERING_PUDDLE, NPC_PUMMELERS_FIST, NPC_ROOM_ALARM,
            NPC_VENT_STALKER, NPC_EXILE })
            CHECK(kCreaturesReservation.Contains(entry));
        CHECK(!kCreaturesReservation.Contains(NPC_GEAR_LAUNCHED_BOMB));
        for (std::uint32_t entry : { GO_PUMMELER_CHEST, GO_PUMMELER_CHEST_HEROIC, GO_CLEARANCE_CONSOLE })
            CHECK(kGameObjectsReservation.Contains(entry));
    }

    void TestWorkshopDoor()
    {
        // the slots' floor: Electrocutioner DONE unlocks, the Alert System DONE opens (section 7 #15 A)
        CHECK(WorkshopDoorFromSlots(S::NotStarted, S::NotStarted) == WORKSHOP_DOOR_SEALED);
        CHECK(WorkshopDoorFromSlots(S::InProgress, S::NotStarted) == WORKSHOP_DOOR_SEALED);
        CHECK(WorkshopDoorFromSlots(S::Done, S::NotStarted) == WORKSHOP_DOOR_UNLOCKED);
        CHECK(WorkshopDoorFromSlots(S::NotStarted, S::Done) == WORKSHOP_DOOR_OPEN);
        CHECK(WorkshopDoorFromSlots(S::Done, S::Done) == WORKSHOP_DOOR_OPEN);
        // never lower than the saved state or the slots' floor; a bad value changes nothing
        CHECK(RaiseWorkshopDoor(WORKSHOP_DOOR_OPEN, WORKSHOP_DOOR_SEALED, S::NotStarted, S::NotStarted)
            == WORKSHOP_DOOR_OPEN);
        CHECK(RaiseWorkshopDoor(WORKSHOP_DOOR_SEALED, WORKSHOP_DOOR_SEALED, S::Done, S::NotStarted)
            == WORKSHOP_DOOR_UNLOCKED);
        CHECK(RaiseWorkshopDoor(WORKSHOP_DOOR_UNLOCKED, WORKSHOP_DOOR_OPEN, S::Done, S::NotStarted)
            == WORKSHOP_DOOR_OPEN);
        CHECK(RaiseWorkshopDoor(WORKSHOP_DOOR_UNLOCKED, 7, S::Done, S::NotStarted) == WORKSHOP_DOOR_UNLOCKED);
        CHECK(RaiseWorkshopDoor(9, 9, S::NotStarted, S::NotStarted) == WORKSHOP_DOOR_OPEN);
        // section 7 #16 B: sealed is not selectable (no key, no lockpick, no blasting); a player's open counts only
        // while unlocked
        CHECK(!WorkshopDoorSelectable(WORKSHOP_DOOR_SEALED));
        CHECK(WorkshopDoorSelectable(WORKSHOP_DOOR_UNLOCKED));
        CHECK(!WorkshopDoorSelectable(WORKSHOP_DOOR_OPEN));      // latched open
        CHECK(!WorkshopDoorOpenByUseAllowed(WORKSHOP_DOOR_SEALED));
        CHECK(WorkshopDoorOpenByUseAllowed(WORKSHOP_DOOR_UNLOCKED));
        CHECK(WorkshopDoorGoState(WORKSHOP_DOOR_OPEN) == kGoStateActive);
        CHECK(WorkshopDoorGoState(WORKSHOP_DOOR_SEALED) == kGoStateReady);
        CHECK(WorkshopDoorGoState(WORKSHOP_DOOR_UNLOCKED) == kGoStateReady);

        // RB-23: every door state x slot pair survives a save and a reload as max(saved, the slots' floor)
        std::uint32_t const slotStates[] = { S::NotStarted, S::InProgress, S::Fail, S::Done, S::ToBeDecided };
        for (std::uint32_t door = 0; door <= WORKSHOP_DOOR_OPEN; ++door)
            for (std::uint32_t electro : slotStates)
                for (std::uint32_t alert : slotStates)
                {
                    GnrSave save;
                    save.states[BOSS_ELECTROCUTIONER] = electro;
                    save.states[BOSS_ALERT_SYSTEM] = alert;
                    save.workshopDoor = door;
                    GnrSave loaded;
                    CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
                    std::uint32_t const e = SettledSlotState(DungeonKit::SanitizeLoadedState(electro));
                    std::uint32_t const a = SettledSlotState(DungeonKit::SanitizeLoadedState(alert));
                    CHECK(loaded.workshopDoor == std::max(door, WorkshopDoorFromSlots(e, a)));
                    // a second reload changes nothing
                    GnrSave again;
                    CHECK(ParseGnrSave(FormatGnrSave(loaded), again));
                    CHECK(again.workshopDoor == loaded.workshopDoor);
                }
    }

    // R-1-FW B1: a model of the engine path GameObject::SetLootState -> go_gnomer_workshop_door::OnStateChanged ->
    // SetData(DATA_WORKSHOP_DOOR) -> RaiseWorkshopDoorTo -> ApplyWorkshopDoor -> OpenLatched -> SetLootState, built
    // from the helpers the instance uses, with a depth cap standing in for the stack. Each guard can be switched off.
    struct DoorLoopModel
    {
        bool latchGuard = true;         // OpenLatchSetsLootState in OpenLatched
        bool aiGuard = true;            // WorkshopDoorUseForwarded in the AI
        bool goActive = false;
        bool lootActivated = false;
        std::uint32_t door = WORKSHOP_DOOR_SEALED;
        std::uint32_t electro = S::NotStarted;
        std::uint32_t alert = S::NotStarted;
        int depth = 0;
        int lootSets = 0;
        bool overflow = false;

        void SetLootActivated()         // GameObject::SetLootState: the state first, then the AI
        {
            lootActivated = true;
            ++lootSets;
            if (depth >= 64)
            {
                overflow = true;
                return;
            }
            ++depth;
            OnStateChanged();
            --depth;
        }

        void OnStateChanged()
        {
            if (aiGuard && !WorkshopDoorUseForwarded(door))
                return;
            RaiseTo(WORKSHOP_DOOR_OPEN, true);
        }

        void RaiseTo(std::uint32_t wanted, bool byUse)
        {
            if (byUse && !WorkshopDoorOpenByUseAllowed(door))
                return;
            door = RaiseWorkshopDoor(door, wanted, electro, alert);
            Apply();
        }

        void Apply()
        {
            if (door != WORKSHOP_DOOR_OPEN)
            {
                goActive = false;
                lootActivated = false;
                return;
            }
            goActive = true;
            if (!latchGuard || OpenLatchSetsLootState(goActive, lootActivated))
                SetLootActivated();
        }

        void Click()                    // GameObject::UseDoorOrButton: only from GO_READY; switch, then the loot state
        {
            if (lootActivated)
                return;
            goActive = true;
            SetLootActivated();
        }
    };

    // Every trigger the review lists: the Alert System's death, a click on the unlocked door, `.dbtest gnomer door
    // open`, a reload with the door saved open (create, then the watch finding it shut).
    void RunDoorTriggers(bool latchGuard, bool aiGuard, bool expectEnd)
    {
        auto fresh = [&]()
        {
            DoorLoopModel m;
            m.latchGuard = latchGuard;
            m.aiGuard = aiGuard;
            return m;
        };

        DoorLoopModel alertDeath = fresh();
        alertDeath.electro = S::Done;
        alertDeath.door = WORKSHOP_DOOR_UNLOCKED;
        alertDeath.alert = S::Done;
        alertDeath.RaiseTo(WORKSHOP_DOOR_OPEN, false);

        DoorLoopModel click = fresh();
        click.electro = S::Done;
        click.door = WORKSHOP_DOOR_UNLOCKED;
        click.Click();

        DoorLoopModel gm = fresh();
        gm.door = WORKSHOP_DOOR_OPEN;
        gm.Apply();

        DoorLoopModel reload = fresh();
        reload.door = WORKSHOP_DOOR_OPEN;
        reload.Apply();                 // OnGameObjectCreate
        reload.goActive = false;        // shut by something else, then the watch
        reload.Apply();

        for (DoorLoopModel const* m : { &alertDeath, &click, &gm, &reload })
        {
            CHECK(m->overflow == !expectEnd);
            if (expectEnd)
            {
                CHECK(m->door == WORKSHOP_DOOR_OPEN && m->goActive && m->lootActivated);
                CHECK(m->lootSets <= 2);
            }
        }

        // a click on a sealed door is refused and changes nothing (the AI shuts it again)
        DoorLoopModel sealed = fresh();
        sealed.Click();
        CHECK(!sealed.overflow && sealed.door == WORKSHOP_DOOR_SEALED);
    }

    void TestWorkshopDoorLoop()
    {
        CHECK(OpenLatchSetsLootState(false, false));
        CHECK(OpenLatchSetsLootState(true, false));
        CHECK(OpenLatchSetsLootState(false, true));
        CHECK(!OpenLatchSetsLootState(true, true));
        CHECK(WorkshopDoorUseForwarded(WORKSHOP_DOOR_SEALED) && WorkshopDoorUseForwarded(WORKSHOP_DOOR_UNLOCKED));
        CHECK(!WorkshopDoorUseForwarded(WORKSHOP_DOOR_OPEN));

        RunDoorTriggers(false, false, false);   // the pre-F-1a code: every trigger recurses until the stack runs out
        RunDoorTriggers(true, false, true);     // either guard alone ends it
        RunDoorTriggers(false, true, true);
        RunDoorTriggers(true, true, true);      // as built
    }

    void TestChestAndEndNpcs()
    {
        // the chest is placed at slot 4 DONE and after a reload until looted (section 7 #38 k A, ZF RB-23 M4)
        CHECK(ChestPlaceDue(S::Done, PUMMELER_CHEST_NONE, false, true));
        CHECK(ChestPlaceDue(S::Done, PUMMELER_CHEST_PLACED, false, true));
        CHECK(!ChestPlaceDue(S::Done, PUMMELER_CHEST_PLACED, true, true));      // it stands
        CHECK(!ChestPlaceDue(S::Done, PUMMELER_CHEST_LOOTED, false, true));
        CHECK(!ChestPlaceDue(S::Done, PUMMELER_CHEST_PLACED, false, false));    // its grid is not loaded
        CHECK(!ChestPlaceDue(S::InProgress, PUMMELER_CHEST_NONE, false, true));
        CHECK(!ChestPlaceDue(S::NotStarted, PUMMELER_CHEST_PLACED, false, true));
        CHECK(ChestEntry(false) == GO_PUMMELER_CHEST && ChestEntry(true) == GO_PUMMELER_CHEST_HEROIC);
        // R-1-FW M1: an emptied chest is deleted and leaves the map, so a chest placed this load that is gone was
        // looted; a reload starts untracked, so an unlooted chest is placed again
        CHECK(ChestEmptied(true, false, false));    // consumed: deleted and removed
        CHECK(ChestEmptied(true, true, false));     // found despawned
        CHECK(!ChestEmptied(true, true, true));     // it stands
        CHECK(!ChestEmptied(false, false, false));  // nothing placed this load (a reload, or a GM removal)
        {
            // the loot, then the watches after it: looted once, never placed again
            std::uint32_t chest = PUMMELER_CHEST_PLACED;
            bool tracked = true;
            int placed = 0;
            for (int watch = 0; watch < 5; ++watch)
            {
                if (chest == PUMMELER_CHEST_LOOTED)
                    continue;
                if (ChestEmptied(tracked, false, false))
                {
                    chest = PUMMELER_CHEST_LOOTED;
                    tracked = false;
                    continue;
                }
                if (ChestPlaceDue(S::Done, chest, false, true))
                {
                    ++placed;
                    tracked = true;
                }
            }
            CHECK(chest == PUMMELER_CHEST_LOOTED && placed == 0);
            // a reload with the chest unlooted: untracked, not standing, so placed again
            CHECK(!ChestEmptied(false, false, false) && ChestPlaceDue(S::Done, PUMMELER_CHEST_PLACED, false, true));
        }
        // every chest state x slot 4 state through a reload
        std::uint32_t const slotStates[] = { S::NotStarted, S::InProgress, S::Done, S::ToBeDecided };
        for (std::uint32_t chest = 0; chest <= PUMMELER_CHEST_LOOTED; ++chest)
            for (std::uint32_t slot : slotStates)
            {
                GnrSave save;
                save.states[BOSS_CROWD_PUMMELER] = slot;
                save.pummelerChest = chest;
                GnrSave loaded;
                CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
                if (slot != S::Done)
                    CHECK(loaded.pummelerChest == PUMMELER_CHEST_NONE);
                else if (chest == PUMMELER_CHEST_LOOTED)
                    CHECK(loaded.pummelerChest == PUMMELER_CHEST_LOOTED);
                else
                    CHECK(loaded.pummelerChest == PUMMELER_CHEST_PLACED);
            }

        // the End NPCs (section 7 #24 A): normal only, once their boss is DONE
        CHECK(EndNpcSlot(1) == BOSS_ELECTROCUTIONER && EndNpcSlot(2) == BOSS_THERMAPLUGG);
        CHECK(EndNpcStands(false, S::Done));
        CHECK(!EndNpcStands(true, S::Done));
        CHECK(!EndNpcStands(false, S::InProgress) && !EndNpcStands(false, S::NotStarted));
        CHECK(EndNpcSpot(1).x == kEndNpc1Spot.x && EndNpcSpot(2).y == kEndNpc2Spot.y);
        // the summon spots are the quests WP's (section 4.Q)
        CHECK(std::abs(kEndNpc1Spot.x - -538.76f) < 0.01f && std::abs(kEndNpc2Spot.x - -607.63f) < 0.01f);
    }

    void TestHardMode()
    {
        // the console (section 3.7): heroic, not a bot, not already set, Thermaplugg not engaged or dead, out of
        // combat, the card
        CHECK(ConsoleCheck(true, false, false, true, S::NotStarted, 0) == CONSOLE_ACCEPTED);
        CHECK(ConsoleCheck(true, false, false, true, S::Fail, 0) == CONSOLE_ACCEPTED);
        CHECK(ConsoleCheck(false, false, false, true, S::NotStarted, 0) == CONSOLE_NOT_HEROIC);
        CHECK(ConsoleCheck(true, true, false, true, S::NotStarted, 0) == CONSOLE_BOT);
        CHECK(ConsoleCheck(true, false, false, true, S::NotStarted, 1) == CONSOLE_ALREADY_SET);
        CHECK(ConsoleCheck(true, false, false, true, S::InProgress, 0) == CONSOLE_BOSS_ENGAGED);
        CHECK(ConsoleCheck(true, false, false, true, S::Done, 0) == CONSOLE_BOSS_ENGAGED);
        CHECK(ConsoleCheck(true, false, true, true, S::NotStarted, 0) == CONSOLE_IN_COMBAT);
        CHECK(ConsoleCheck(true, false, false, false, S::NotStarted, 0) == CONSOLE_NO_CARD);
        // the instance's own check
        CHECK(HardModeFlagAllowed(true, S::NotStarted));
        CHECK(!HardModeFlagAllowed(false, S::NotStarted));
        CHECK(!HardModeFlagAllowed(true, S::InProgress) && !HardModeFlagAllowed(true, S::Done));
        // RB-24: the flag alone never arms; the pull's verdict must say the packages were built
        CHECK(HardModeArmed(true, 1, kVerdictArmed));
        CHECK(!HardModeArmed(true, 1, kVerdictPlain));
        CHECK(!HardModeArmed(true, 1, kVerdictNone));
        CHECK(!HardModeArmed(true, 0, kVerdictArmed));
        CHECK(!HardModeArmed(false, 1, kVerdictArmed));
        // the loot bit: armed and not dead yet (it is never touched at the death: rule 1)
        CHECK(HardModeLootLit(true, S::InProgress));
        CHECK(!HardModeLootLit(true, S::Done));
        CHECK(!HardModeLootLit(false, S::InProgress));
        // the GM's flag
        CHECK(GmHardModeAllowed(true, S::NotStarted, 1));
        CHECK(!GmHardModeAllowed(false, S::NotStarted, 1));
        CHECK(GmHardModeAllowed(false, S::NotStarted, 0));
        CHECK(!GmHardModeAllowed(true, S::InProgress, 0));
        // the kill slot: only with slot 5 DONE and the flag; the flag holds through wipes (a save keeps it)
        GnrSave save;
        save.states[BOSS_WHOLE_WORKSHOP] = S::Done;
        save.hardMode = 1;
        GnrSave loaded;
        CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
        CHECK(loaded.states[BOSS_WHOLE_WORKSHOP] == S::NotStarted);    // slot 5 not DONE
        CHECK(loaded.hardMode == 1);
        save.states[BOSS_THERMAPLUGG] = S::Done;
        CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
        CHECK(loaded.states[BOSS_WHOLE_WORKSHOP] == S::Done);
        save.hardMode = 0;
        CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
        CHECK(loaded.states[BOSS_WHOLE_WORKSHOP] == S::NotStarted);
        save.hardMode = 5;
        CHECK(ParseGnrSave(FormatGnrSave(save), loaded));
        CHECK(loaded.hardMode == 1);
    }

    void TestSections()
    {
        CHECK(SectionOfLfgDungeon(14) == 1 && SectionOfLfgDungeon(321) == 1);
        CHECK(SectionOfLfgDungeon(320) == 2 && SectionOfLfgDungeon(322) == 2);
        CHECK(SectionOfLfgDungeon(0) == 0 && SectionOfLfgDungeon(30) == 0);
        CHECK(SectionByNumber(1) && SectionByNumber(1)->endSlot == BOSS_ELECTROCUTIONER);
        CHECK(SectionByNumber(2) && SectionByNumber(2)->endSlot == BOSS_THERMAPLUGG);
        CHECK(!SectionByNumber(3));
        CHECK(SectionByNumber(2)->start.x == kSection2Start.x && SectionByNumber(1)->start.y == kSection1Start.y);
        CHECK(SectionByNumber(2)->doors[0] == GO_WORKSHOP_DOOR);
    }

    void TestSave()
    {
        // round trip
        GnrSave save;
        save.states = { S::Done, S::Done, S::NotStarted, S::Done, S::Done, S::InProgress, S::NotStarted };
        save.workshopDoor = WORKSHOP_DOOR_OPEN;
        save.hardMode = 1;
        save.pummelerChest = PUMMELER_CHEST_LOOTED;
        save.section = 2;
        std::string const text = FormatGnrSave(save);
        CHECK(text.rfind("G N R ", 0) == 0);
        GnrSave loaded;
        CHECK(ParseGnrSave(text, loaded));
        CHECK(loaded.states[BOSS_ALERT_SYSTEM] == S::Done && loaded.states[BOSS_TECHBOT] == S::NotStarted);
        CHECK(loaded.states[BOSS_THERMAPLUGG] == S::NotStarted);       // IN_PROGRESS never survives a reload
        CHECK(loaded.workshopDoor == WORKSHOP_DOOR_OPEN && loaded.hardMode == 1);
        CHECK(loaded.pummelerChest == PUMMELER_CHEST_LOOTED && loaded.section == 2);
        // TO_BE_DECIDED is written as NOT_STARTED
        GnrSave tbd;
        tbd.states[BOSS_TECHBOT] = S::ToBeDecided;
        CHECK(FormatGnrSave(tbd).find('5') == std::string::npos);

        // the stock save (section 6: the live "G N O 0" row): a fresh run, Grubbis's field dropped
        CHECK(ParseGnrSave("G N O 0", loaded));
        for (std::uint32_t s : loaded.states)
            CHECK(s == S::NotStarted);
        CHECK(loaded.workshopDoor == WORKSHOP_DOOR_SEALED && loaded.hardMode == 0 && loaded.section == 0);
        CHECK(ParseGnrSave("G N O 3", loaded));                         // Grubbis DONE: still a fresh run
        CHECK(loaded.states[BOSS_TECHBOT] == S::NotStarted);
        // a stock save with a completed-encounter mask (stock never wrote one; the mask is the map's)
        CHECK(ParseGnrSave("G N O 0", loaded, (1u << BOSS_ELECTROCUTIONER) | (1u << BOSS_ALERT_SYSTEM)));
        CHECK(loaded.states[BOSS_ELECTROCUTIONER] == S::Done && loaded.states[BOSS_ALERT_SYSTEM] == S::Done);
        CHECK(loaded.workshopDoor == WORKSHOP_DOOR_OPEN);
        // the mask is not applied to our own save
        GnrSave fresh;
        CHECK(ParseGnrSave(FormatGnrSave(fresh), loaded, 0x3F));
        CHECK(loaded.states[BOSS_THERMAPLUGG] == S::NotStarted);
        // an older save of ours with fewer extras loads them as 0
        CHECK(ParseGnrSave("G N R 3 0 0 3 0 0 0 1", loaded));
        CHECK(loaded.states[BOSS_ALERT_SYSTEM] == S::Done && loaded.states[BOSS_ELECTROCUTIONER] == S::Done);
        CHECK(loaded.workshopDoor == WORKSHOP_DOOR_OPEN && loaded.hardMode == 0 && loaded.section == 0);
        // garbage and foreign headers are ignored
        CHECK(!ParseGnrSave("", loaded));
        CHECK(!ParseGnrSave("Z F R 0 0", loaded));
        CHECK(!ParseGnrSave("G N O", loaded));
        // a section out of range is dropped
        GnrSave bad;
        bad.section = 9;
        CHECK(ParseGnrSave(FormatGnrSave(bad), loaded));
        CHECK(loaded.section == 0);
    }

    void TestGeometry()
    {
        // every boss spot on its slot's arena
        CHECK(ArenaFor(BOSS_TECHBOT).Contains(kTechbotSpawn.XY(), kTechbotSpawn.z));
        CHECK(ArenaFor(BOSS_VISCOUS_FALLOUT).Contains(kFalloutSpawn.XY(), kFalloutSpawn.z));
        CHECK(ArenaFor(BOSS_VISCOUS_FALLOUT).Contains(kFalloutStockSpawn.XY(), kFalloutStockSpawn.z));
        CHECK(ArenaFor(BOSS_ELECTROCUTIONER).Contains(kElectrocutionerSpawn.XY(), kElectrocutionerSpawn.z));
        CHECK(ArenaFor(BOSS_ALERT_SYSTEM).Contains(kAlertSystemSpawn.XY(), kAlertSystemSpawn.z));
        CHECK(ArenaFor(BOSS_CROWD_PUMMELER).Contains(kPummelerSpot.XY(), kPummelerSpot.z));
        CHECK(ArenaFor(BOSS_THERMAPLUGG).Contains(kThermapluggSpawn.XY(), kThermapluggSpawn.z));
        CHECK(ArenaFor(BOSS_WHOLE_WORKSHOP).Contains(kThermapluggSpawn.XY(), kThermapluggSpawn.z));
        CHECK(ArenaFor(kBossCount).Empty());
        // the dish ends at the Cave Ins' mouths: Emi's old spot (31 yd out, behind one) is off it
        CHECK(!DishArena().Contains(Vec2{ -514.93f, -138.54f }, -152.4f));
        // Electrocutioner: the spawn inside the pick disc, End NPC 1 and the checkpoint on the platform arena
        CHECK(PlatformPickArena().Contains(kElectrocutionerSpawn.XY(), kElectrocutionerSpawn.z));
        CHECK(PlatformArena().Contains(kEndNpc1Spot.XY(), kEndNpc1Spot.z));
        CHECK(PlatformArena().Contains(kCheckpointElectrocutioner.XY(), kCheckpointElectrocutioner.z));
        CHECK(Dist(kElectrocutionerSpawn, kPlatformCenter) < 3.f);
        // the hall: the spot inside, the Workshop Door outside (the cut is at its line), the door 35.9 yd away
        CHECK(!HallArena().Contains(kWorkshopDoorSpot.XY(), kWorkshopDoorSpot.z));
        CHECK(std::abs(Dist(kAlertSystemSpawn, kWorkshopDoorSpot) - 35.9f) < 0.2f);
        // Crowd Pummeler: the chest, the frame origin and the checkpoint on the pocket floor and in the pocket box;
        // he himself is under the floor, outside the box (the damage filter's "inside" is the players')
        for (Point3 const& p : { kPummelerChestSpot, kPummelerFrameOrigin, kCheckpointPummeler })
        {
            CHECK(PocketArena().Contains(p.XY(), p.z));
            CHECK(InPocketBox(p.x, p.y, p.z));
        }
        CHECK(!InPocketBox(kPummelerSpot.x, kPummelerSpot.y, kPummelerSpot.z));
        CHECK(!PocketArena().Contains(kPummelerSpot.XY(), kPummelerSpot.z));
        CHECK(std::abs(kPummelerSpot.z - -272.6f + 4.8f) < 0.1f);   // 4.8 yd under the floor (section 10)
        // Thermaplugg's room: the faces 49 to 51 yd out, the plates 25, the bomb starts 37 (section 7 #30 A, #31),
        // the plates and bomb starts on the room's arena, the console too
        for (std::uint32_t i = 0; i < kFaceCount; ++i)
        {
            float const face = Dist(kFaceSpots[i], kRoomCenter);
            CHECK(face > 49.f && face < 51.f);
            CHECK(std::abs(Dist(kPlateSpots[i], kRoomCenter) - kPlateRadiusYd) < 0.1f);
            CHECK(std::abs(Dist(kBombStarts[i], kRoomCenter) - kBombStartRadiusYd) < 0.1f);
            CHECK(RoomArena().Contains(kPlateSpots[i].XY(), kPlateSpots[i].z));
            CHECK(RoomArena().Contains(kBombStarts[i].XY(), kBombStarts[i].z));
            // each plate and bomb start on its face's bearing
            float const bearing = std::atan2(kPlateSpots[i].y - kRoomCenter.y, kPlateSpots[i].x - kRoomCenter.x)
                * 180.f / 3.14159265f;
            float const want = kFaceBearingDeg[i] > 180.f ? kFaceBearingDeg[i] - 360.f : kFaceBearingDeg[i];
            CHECK(std::abs(bearing - want) < 0.5f);
        }
        CHECK(RoomArena().Contains(kConsoleSpot.XY(), kConsoleSpot.z));
        CHECK(std::abs(Dist(kConsoleSpot, kRoomCenter) - 50.f) < 0.5f);
        // the checkpoint rows (section 7 #25 A): the Depot row is the Finder start of section 2
        CHECK(kCheckpointDepot.x == kSection2Start.x && kCheckpointDepot.y == kSection2Start.y);
        CHECK(kCheckpointDepotReachYd > 0.f);
        // every polygon is a ring of at least three points
        CHECK(kDishPolygon.size() >= 3 && kCavePolygon.size() >= 3 && kPlatformPolygon.size() >= 3);
        CHECK(kHallPolygon.size() >= 3 && kPocketPolygon.size() >= 3 && kRoomPolygon.size() >= 3);
    }

    void TestHealth()
    {
        // normal = the engine's ceil(853 x HealthModifier) of the DT rows (section 7 #1 A: x2.0)
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kTechbot) == Health::kTechbot.normal);
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kViscousFallout) == Health::kViscousFallout.normal);
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kElectrocutioner)
            == Health::kElectrocutioner.normal);
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kAlertSystem) == Health::kAlertSystem.normal);
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kCrowdPummeler) == Health::kCrowdPummeler.normal);
        CHECK(EngineHealth(kBaseHealthWarrior28, HealthModifier::kThermaplugg) == Health::kThermaplugg.normal);
        // x2.0 of the spec within 0.1%, x4/3 of the heroic spec
        struct Row
        {
            NH<std::uint32_t> health;
            std::uint32_t specNormal;
            std::uint32_t specHeroic;
        };
        Row const rows[] = {
            { Health::kTechbot, 30000, 250000 }, { Health::kViscousFallout, 33000, 350000 },
            { Health::kElectrocutioner, 34000, 300000 }, { Health::kAlertSystem, 28000, 250000 },
            { Health::kCrowdPummeler, 30000, 280000 }, { Health::kThermaplugg, 40000, 350000 },
        };
        for (Row const& r : rows)
        {
            CHECK(std::abs(double(r.health.normal) - 2.0 * r.specNormal) <= 0.001 * 2.0 * r.specNormal);
            CHECK(std::abs(double(r.health.heroic) - r.specHeroic * 4.0 / 3.0) <= 1.0);
        }
        // the hard mode: 600,000 x 4/3, above heroic on health (SYS: a hard mode >= its heroic)
        CHECK(Health::kWholeWorkshop == 800000);
        CHECK(Health::kWholeWorkshop > Health::kThermaplugg.heroic);
        CHECK(Health::kWalkingBombHardMode > Health::kWalkingBomb.heroic);
        CHECK(EngineHealth(kBaseHealthCaster28, 57.4f) == Health::kDarkIronAmbassador.normal);
        CHECK(kReferenceNormal.nonTank == 1694 && kReferenceHeroic.nonTank == 4120);
        CHECK(kWarningFloorMs == 1500);
    }

    // Section 3.5 rule 29 (LESSONS L1): every `struct boss_` of a boss file calls GnomereganRework::NoAssist(me) in
    // its UpdateAI before UpdateVictim(); every boss_*.cpp of the folder is listed in kBossFiles.
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
                std::size_t const call = body.find("GnomereganRework::NoAssist(me);", update);
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

    // The instance: registered under the stock name (section 7 #2 A: Kernobee), the save header, the slots, the verdict
    // gate (RB-24), slot 6 inside slot 5's DONE, the explicit saves (RB-2), the door never reset through
    // ResetDoorOrButton (LESSONS A.2 #13).
    void TestInstanceSource()
    {
        std::string const text = ReadFile(SourceDir() / "instance_gnomeregan_rework.cpp");
        CHECK(!text.empty());
        CHECK(Count(text, "InstanceMapScript(kInstanceScriptName, MAP_GNOMEREGAN)") == 1);
        CHECK(Count(text, "SetHeaders(kSaveHeader);") == 1);
        CHECK(Count(text, "SetBossNumber(kBossCount);") == 1);
        CHECK(Count(text, "ResetDoorOrButton") == 1);       // the comment that forbids it, nothing else
        CHECK(Count(text, "ForceBossState(BOSS_WHOLE_WORKSHOP, DONE);") == 1);
        CHECK(Count(text, "HardModeArmed(Heroic(), _hardMode, _verdict)") >= 2);
        CHECK(Count(text, "SaveToDB();") >= 8);
        CHECK(Count(text, "void JustDied") == 0);
        // R-1-FW B1 / M1 / m1: the loop guards, the chest rule and the exile's template guard are wired
        CHECK(Count(text, "OpenLatchSetsLootState(go->GetGoState() == GO_STATE_ACTIVE, go->getLootState() == "
            "GO_ACTIVATED)") == 1);
        CHECK(Count(text, "!WorkshopDoorUseForwarded(instance->GetData(DATA_WORKSHOP_DOOR))") == 1);
        CHECK(Count(text, "ChestEmptied(!_chest.IsEmpty(), chest != nullptr, chest && chest->isSpawned())") == 1);
        CHECK(Count(text, "sObjectMgr->GetCreatureTemplate(NPC_EXILE)") == 1);
        CHECK(Count(text, "go->SetLootState(GO_ACTIVATED);") == 1);
        CHECK(Count(text, "RegisterDungeonReworkGameObjectAI(go_gnomer_workshop_door, "
            "GnomereganRework::kInstanceScriptName);") == 1);
    }
}

int main()
{
    TestSlotsAndIds();
    TestSlices();
    TestWorkshopDoor();
    TestWorkshopDoorLoop();
    TestChestAndEndNpcs();
    TestHardMode();
    TestSections();
    TestSave();
    TestGeometry();
    TestHealth();
    TestNoAssistInEveryBossFile();
    TestInstanceSource();
    return Report("gnomeregan_test");
}
