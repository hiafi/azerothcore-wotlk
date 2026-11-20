// Host tests for the Blackrock Depths skeleton (WP-S0): BlackrockDepthsRework.h (the 24 boss states, every stock data
// id on its stock number, the TYPE mirrors, entries, the wave switch, slices, measured points, arenas, the Finder
// sections, the Ring's saved rolls, the Vault rules, the bar door, the Tomb doors, the stock-collision guard, the hard
// mode rules, the save string and its stock reader). DB positions (spawns, objects, triggers) are exact; the rest is
// the NAVMESH report's.
#include "BlackrockDepthsRework.h"
#include "RingOfLawLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <set>
#include <string>
#include <vector>

using namespace BlackrockDepthsRework;
namespace State = DungeonKit::State;

namespace
{
    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    float Distance3(Point3 const& a, Point3 const& b)
    {
        float const dx = a.x - b.x;
        float const dy = a.y - b.y;
        float const dz = a.z - b.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    struct BossSpot
    {
        std::uint32_t boss;
        Point3 at;
    };

    // Where each fighting boss stands at the pull (spawned bosses: their spawn; summoned: their summon).
    std::vector<BossSpot> const kSpots{
        { BOSS_GERSTAHN, kGerstahnSpawn }, { BOSS_ROCCOR, kRoccorSpawn }, { BOSS_GREBMAR, kGrebmarSpawn },
        { BOSS_RING_OF_LAW, kGrimstoneSummon.P3() }, { BOSS_LOREGRAIN, kLoregrainSpawn },
        { BOSS_INCENDIUS, kIncendiusSpawn }, { BOSS_STILGISS_VEREK, kStilgissSpawn },
        { BOSS_STILGISS_VEREK, kVerekSpawn }, { BOSS_FINEOUS, kFineousSpawn }, { BOSS_BAELGAR, kBaelgarSpawn },
        { BOSS_ANGERFORGE, kAngerforgeSpawn }, { BOSS_ARGELMACH, kArgelmachSpawn }, { BOSS_HURLEY, kHurleySpawn },
        { BOSS_PHALANX, kPhalanxSpawn }, { BOSS_FLAMELASH, kFlamelashSpawn }, { BOSS_THE_SEVEN, kAngerrelSpawn },
        { BOSS_THE_SEVEN, kDoomrelSpawn }, { BOSS_MAGMUS, kMagmusSpawn }, { BOSS_EMPEROR, kEmperorSpawn },
        { BOSS_EMPEROR, kMoiraSpawn }, { BOSS_VAULT, kDoomgripSummon.P3() } };

    void TestBossStates()
    {
        CHECK(kBossCount == 24);
        CHECK(kEncounterCount == 19);
        // Slots 0-18 are the DungeonEncounter bits (227-245 in id order, read from the DBC 2026-11-17).
        CHECK(BOSS_GERSTAHN == 0 && BOSS_ROCCOR == 1 && BOSS_GREBMAR == 2 && BOSS_RING_OF_LAW == 3);
        CHECK(BOSS_LOREGRAIN == 4 && BOSS_INCENDIUS == 5 && BOSS_STILGISS_VEREK == 6 && BOSS_FINEOUS == 7);
        CHECK(BOSS_BAELGAR == 8 && BOSS_ANGERFORGE == 9 && BOSS_ARGELMACH == 10 && BOSS_HURLEY == 11);
        CHECK(BOSS_PHALANX == 12 && BOSS_RIBBLY == 13 && BOSS_PLUGGER == 14 && BOSS_FLAMELASH == 15);
        CHECK(BOSS_THE_SEVEN == 16 && BOSS_MAGMUS == 17 && BOSS_EMPEROR == 18);
        CHECK(BOSS_VAULT == 19 && BOSS_ENCORE == 20 && BOSS_LORD_OF_THE_LAKE == 21 && BOSS_PROTOTYPE == 22);
        CHECK(BOSS_AVATAR == 23);
        for (std::uint32_t id = 0; id < kBossCount; ++id)
            CHECK(IsEncounterSlot(id) == (id <= 18));
        for (char const* name : kBossNames)
            CHECK(name && *name);
        // Tracking only: no credit (BD5), the client rows stay.
        CHECK(IsTrackingOnlySlot(BOSS_FINEOUS) && IsTrackingOnlySlot(BOSS_RIBBLY) && IsTrackingOnlySlot(BOSS_PLUGGER));
        CHECK(!IsTrackingOnlySlot(BOSS_GERSTAHN) && !IsTrackingOnlySlot(BOSS_VAULT));
        // The hard mode kills and their bosses.
        for (std::uint32_t id = 0; id < kBossCount; ++id)
            CHECK(IsHardModeSlot(id) == (id >= 20));
        CHECK(HardModeBoss(BOSS_ENCORE) == BOSS_RING_OF_LAW);
        CHECK(HardModeBoss(BOSS_LORD_OF_THE_LAKE) == BOSS_INCENDIUS);
        CHECK(HardModeBoss(BOSS_PROTOTYPE) == BOSS_ARGELMACH);
        CHECK(HardModeBoss(BOSS_AVATAR) == BOSS_EMPEROR);
        CHECK(HardModeBoss(BOSS_GERSTAHN) == kBossCount);
        // Sections: 1 Detention Block .. 4 Imperial Seat.
        CHECK(SectionOf(BOSS_GERSTAHN) == 1 && SectionOf(BOSS_RING_OF_LAW) == 1 && SectionOf(BOSS_ENCORE) == 1);
        CHECK(SectionOf(BOSS_BAELGAR) == 2 && SectionOf(BOSS_VAULT) == 2 && SectionOf(BOSS_LORD_OF_THE_LAKE) == 2);
        CHECK(SectionOf(BOSS_ARGELMACH) == 3 && SectionOf(BOSS_PROTOTYPE) == 3);
        CHECK(SectionOf(BOSS_EMPEROR) == 4 && SectionOf(BOSS_AVATAR) == 4 && SectionOf(BOSS_PHALANX) == 4);
        CHECK(SectionOf(kBossCount) == 0);
    }

    void TestEncounterBits()
    {
        // bit i = slot i (DungeonEncounter.dbc 227-245, Bit 0-18).
        std::set<std::uint32_t> bits;
        for (auto const& [bit, boss] : kEncounterBits)
        {
            CHECK(bit == boss);
            bits.insert(bit);
        }
        CHECK(bits.size() == kEncounterCount);
        CHECK(kDungeonEncounterFirstId == 227);
    }

    void TestStockDataIds()
    {
        // The stock DataTypes (blackrock_depths.h at 60bac7405), as stock scripts and mod-dungeon-clear use them raw.
        CHECK(TYPE_RING_OF_LAW == 1 && TYPE_VAULT == 2 && TYPE_BAR == 3 && TYPE_TOMB_OF_SEVEN == 4);
        CHECK(TYPE_LYCEUM == 5 && TYPE_IRON_HALL == 6);
        CHECK(DATA_EMPEROR == 10 && DATA_PHALANX == 11 && DATA_ARENA1 == 12 && DATA_ARENA2 == 13);
        CHECK(DATA_ARENA3 == 14 && DATA_ARENA4 == 15 && DATA_GO_BAR_KEG == 16 && DATA_GO_BAR_KEG_TRAP == 17);
        CHECK(DATA_GO_BAR_DOOR == 18 && DATA_GO_CHALICE == 19 && DATA_GOLEM_DOOR_N == 22 && DATA_GOLEM_DOOR_S == 23);
        CHECK(DATA_THRONE_DOOR == 24 && DATA_SF_BRAZIER_N == 25 && DATA_SF_BRAZIER_S == 26 && DATA_MOIRA == 27);
        CHECK(DATA_PRIESTESS == 28 && DATA_OPEN_COFFER_DOORS == 30 && DATA_GOLEM_LORD_ARGELMACH_INIT == 31);
        CHECK(DATA_GOLEM_LORD_ARGELMACH_ADDS == 32 && DATA_MAGMUS == 33 && DATA_COREN == 34);
        CHECK(DATA_ANUBSHIAH == 35 && DATA_EVISCERATOR == 36 && DATA_GOROSH == 37 && DATA_GRIZZLE == 38);
        CHECK(DATA_HEDRUM == 39 && DATA_OKTHOR == 40 && DATA_TIME_RING_FAIL == 41 && DATA_ARENA_MOBS == 42);
        CHECK(DATA_ARENA_BOSS == 43 && DATA_PHALANX_ACTIVATED == 44 && DATA_LOVE_POTION_EVENT == 45);
        // The patron keys and the protocols stock scripts send.
        CHECK(DATA_DARK_IRON_ALE == 1 && DATA_DARK_IRON_ALE_DRINK == 4 && DATA_DARK_IRON_ALE_HOME == 100);
        CHECK(DATA_DARK_IRON_ALE_REFORM == 101 && DATA_DARK_IRON_ALE_DISBAND == 102 && DATA_DARK_IRON_ALE_EMOTE == 103);
        CHECK(ACTION_PHALANX_START_ACTIVATION == 1 && DATA_EMPEROR_SENATORS_DEAD == 0 && DATA_IRONHAND_FLAMES == 0);
        CHECK(kAreaTriggerRingOfLaw == 1526);
        // New ids clear every stock one, distinct.
        std::array<std::uint32_t, 17> const fresh{ { DATA_RING_SENTENCE, DATA_RING_WAVE, DATA_RING_FIRST,
            DATA_RING_SECOND, DATA_RING_FAVOR, DATA_BANNER_THROWN, DATA_BANNER_BURNED, DATA_VAULT_TRIGGER,
            DATA_VAULT_CLOCK, DATA_GUZZLER_ROPE, DATA_CINDER_USED, DATA_MOIRA_SAVED, DATA_CONSOLE_ARMED, DATA_AVATAR,
            DATA_COFFER_DOORS_OPENED, DATA_GM_SLOT_WRITE, DATA_VAULT_RESET } };
        std::set<std::uint32_t> const unique(fresh.begin(), fresh.end());
        CHECK(unique.size() == fresh.size());
        for (std::uint32_t id : fresh)
            CHECK(id >= 50 && id < kGuidBossBase);
        // The GetGuidData keys of the boss units sit apart from the stock keys and the slots.
        CHECK(kGuidBossBase + kBossCount <= kGuidVerek && kGuidVerek < kGuidDoomgrip && kGuidDoomgrip < kGuidGrimstone);
    }

    void TestTypeMirrors()
    {
        // The TYPE_* that have an encounter mirror its slot; the bar and the Lyceum have none.
        CHECK(SlotOfType(TYPE_RING_OF_LAW) == BOSS_RING_OF_LAW);
        CHECK(SlotOfType(TYPE_VAULT) == BOSS_VAULT);
        CHECK(SlotOfType(TYPE_TOMB_OF_SEVEN) == BOSS_THE_SEVEN);
        CHECK(SlotOfType(TYPE_IRON_HALL) == BOSS_MAGMUS);
        CHECK(!SlotOfType(TYPE_BAR) && !SlotOfType(TYPE_LYCEUM) && !SlotOfType(DATA_EMPEROR));
        // DONE = 3, SPECIAL = 4 (mod-dungeon-clear's numbers).
        CHECK(State::Done == 3 && State::Special == 4 && State::InProgress == 1 && State::NotStarted == 0);
    }

    void TestEntries()
    {
        // Every encounter boss maps to its slot; the pair, the Seven and Doomgrip too.
        CHECK(BossOfEntry(NPC_GERSTAHN) == BOSS_GERSTAHN && BossOfEntry(NPC_EMPEROR) == BOSS_EMPEROR);
        CHECK(BossOfEntry(NPC_STILGISS) == BOSS_STILGISS_VEREK && BossOfEntry(NPC_VEREK) == BOSS_STILGISS_VEREK);
        CHECK(BossOfEntry(NPC_DOOMGRIP) == BOSS_VAULT);
        for (std::uint32_t entry : kTheSeven)
            CHECK(BossOfEntry(entry) == BOSS_THE_SEVEN);
        // The Ring's units belong to its event, not to a slot by death; Moira's death is not Dagran's.
        CHECK(!BossOfEntry(NPC_GRIMSTONE) && !BossOfEntry(NPC_GOROSH) && !BossOfEntry(NPC_THELDREN));
        CHECK(!BossOfEntry(NPC_MOIRA) && !BossOfEntry(NPC_PRIESTESS) && !BossOfEntry(0));
        // EntryOfBoss inverts BossOfEntry for every encounter slot.
        for (std::uint32_t id = 0; id < kEncounterCount; ++id)
        {
            std::uint32_t const entry = EntryOfBoss(id);
            if (id == BOSS_RING_OF_LAW)
                CHECK(entry == NPC_GRIMSTONE);
            else
                CHECK(BossOfEntry(entry) == id);
        }
        CHECK(EntryOfBoss(BOSS_VAULT) == NPC_DOOMGRIP && EntryOfBoss(BOSS_AVATAR) == NPC_EMPEROR);
        // The stock release order of the Seven (TombBossGUIDs[0..6]).
        CHECK(SevenIndex(NPC_ANGERREL) == 0u && SevenIndex(NPC_DOOMREL) == 6u && !SevenIndex(NPC_EMPEROR));
        // ObjectData only for spawned bosses never summoned twice.
        CHECK(IsObjectDataBoss(NPC_GERSTAHN) && IsObjectDataBoss(NPC_FLAMELASH) && IsObjectDataBoss(NPC_STILGISS));
        CHECK(!IsObjectDataBoss(NPC_GRIMSTONE) && !IsObjectDataBoss(NPC_DOOMGRIP) && !IsObjectDataBoss(NPC_MOIRA));
        CHECK(!IsObjectDataBoss(NPC_PRIESTESS) && !IsObjectDataBoss(NPC_VEREK) && !IsObjectDataBoss(NPC_GOROSH));
        // The Ring's stock orders.
        CHECK(kRingChampions[0] == NPC_GOROSH && kRingChampions[5] == NPC_HEDRUM);
        CHECK(kRingWaveMobs[3] == NPC_THUNDERSNOUT && kRingWaveCounts[3] == 2 && kRingWaveCounts[5] == 6);
        // The relic coffer doors.
        CHECK(IsRelicCofferDoor(174554) && IsRelicCofferDoor(174564) && IsRelicCofferDoor(174566));
        CHECK(!IsRelicCofferDoor(GO_DARK_COFFER_DOOR));
    }

    void TestWaveSwitch()
    {
        CHECK(kWave2Bound);     // both waves bound (W2-SETUP 2026-11-17); the gate stays to check wave 1 alone
        for (std::uint32_t id = 0; id < kBossCount; ++id)
        {
            bool const wave2 = (id >= BOSS_ANGERFORGE && id <= BOSS_EMPEROR) || id == BOSS_PROTOTYPE
                || id == BOSS_AVATAR;
            CHECK(IsWave2Boss(id) == wave2);
        }
        // Wave 1's bosses write their own slots; the Ring, the pair, the Vault are the instance's.
        CHECK(SlotWrittenByScript(BOSS_GERSTAHN, false) && SlotWrittenByScript(BOSS_BAELGAR, false));
        CHECK(!SlotWrittenByScript(BOSS_RING_OF_LAW, true) && !SlotWrittenByScript(BOSS_STILGISS_VEREK, true));
        CHECK(!SlotWrittenByScript(BOSS_VAULT, true) && !SlotWrittenByScript(BOSS_RIBBLY, true));
        CHECK(!SlotWrittenByScript(BOSS_PLUGGER, true) && !SlotWrittenByScript(BOSS_ENCORE, true));
        // A wave 2 boss's slot is the instance's until its wave binds.
        CHECK(!SlotWrittenByScript(BOSS_EMPEROR, false) && SlotWrittenByScript(BOSS_EMPEROR, true));
        CHECK(!SlotWrittenByScript(BOSS_FLAMELASH, false) && SlotWrittenByScript(BOSS_FLAMELASH, true));
        CHECK(IsReworkBound(BOSS_GERSTAHN, false) && !IsReworkBound(BOSS_MAGMUS, false));
        CHECK(IsReworkBound(BOSS_MAGMUS, true) && !IsReworkBound(BOSS_RIBBLY, true) && !IsReworkBound(kBossCount));
    }

    void TestCollisionGuard()
    {
        // The three slots the stock BossAI ids land on (Flamelash 0, Magmus 6, Dagran 10).
        CHECK(IsStockCollisionSlot(BOSS_GERSTAHN) && IsStockCollisionSlot(BOSS_STILGISS_VEREK));
        CHECK(IsStockCollisionSlot(BOSS_ARGELMACH));
        CHECK(!IsStockCollisionSlot(BOSS_FLAMELASH) && !IsStockCollisionSlot(BOSS_MAGMUS));

        SlotOwners idle;
        idle.anyFound = true;
        SlotOwners fighting = idle;
        fighting.anyInCombat = true;
        SlotOwners dead = idle;
        dead.allDead = true;
        SlotOwners missing;

        // A stock Flamelash pull (Gerstahn idle) cannot start Gerstahn's slot; Gerstahn's own pull can.
        CHECK(!SlotWriteAccepted(BOSS_GERSTAHN, State::InProgress, State::NotStarted, idle, false));
        CHECK(SlotWriteAccepted(BOSS_GERSTAHN, State::InProgress, State::NotStarted, fighting, false));
        // A stock death cannot finish it; Gerstahn's own can.
        CHECK(!SlotWriteAccepted(BOSS_GERSTAHN, State::Done, State::NotStarted, idle, false));
        CHECK(SlotWriteAccepted(BOSS_GERSTAHN, State::Done, State::InProgress, dead, false));
        CHECK(!SlotWriteAccepted(BOSS_GERSTAHN, State::Done, State::NotStarted, missing, false));
        // A stock reset never undoes a kill, and never resets a live fight.
        CHECK(!SlotWriteAccepted(BOSS_GERSTAHN, State::NotStarted, State::Done, dead, false));
        CHECK(!SlotWriteAccepted(BOSS_GERSTAHN, State::NotStarted, State::InProgress, fighting, false));
        CHECK(SlotWriteAccepted(BOSS_GERSTAHN, State::NotStarted, State::InProgress, idle, false));
        // Off the three slots, and once wave 2 binds, everything passes.
        CHECK(SlotWriteAccepted(BOSS_ROCCOR, State::Done, State::NotStarted, missing, false));
        CHECK(SlotWriteAccepted(BOSS_GERSTAHN, State::InProgress, State::NotStarted, idle, true));
    }

    void TestSlices()
    {
        // The slices tile 210700-211999 with no gap and no overlap.
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        CHECK(kSpellSlices.back().last == kSpellsReservation.last);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        for (IdSlice const& s : kSpellSlices)
            CHECK(s.first <= s.last && kSpellsReservation.Contains(s.first) && kSpellsReservation.Contains(s.last));
        CHECK(kSpellsGerstahn.first == 210720 && kSpellsSpareWave1.last == 211299);
        CHECK(kSpellsAngerforge.first == 211300 && kSpellsAvatar.last == 211709 && kSpellsSpare.first == 211710);
        CHECK(kSpellsEventItems.first == 211260 && kSpellsEventItems.last == 211269);
        // Creatures: wave 1 below wave 2 (the heroic mint order); gameobjects and items in their blocks.
        CHECK(kCreaturesWave1.last + 1 == kCreaturesWave2.first);
        std::array<std::uint32_t, 17> const wave1{ { NPC_BRD_LOOSED_EARTH, NPC_BRD_KENNEL_HOUND, NPC_BRD_RISEN_WORM,
            NPC_BRD_RISEN_STINGER, NPC_BRD_RISEN_SCREECHER, NPC_BRD_RISEN_THUNDERSNOUT, NPC_BRD_RISEN_CREEPER,
            NPC_BRD_RISEN_BEETLE, NPC_BRD_RISEN_CHAMPION, NPC_BRD_KORV_TOTEM_1, NPC_BRD_KORV_TOTEM_2,
            NPC_BRD_KORV_TOTEM_3, NPC_BRD_DEFILING_TOTEM, NPC_BRD_VAULT_SENTINEL, NPC_BRD_EMBER_OF_INCENDIUS,
            NPC_BRD_LAVA_SPAWN, NPC_BRD_STALKER } };
        for (std::uint32_t id : wave1)
            CHECK(kCreaturesWave1.Contains(id));
        std::array<std::uint32_t, 16> const wave2{ { NPC_BRD_SQUAD_OFFICER, NPC_BRD_SQUAD_RESERVIST,
            NPC_BRD_SQUAD_MEDIC, NPC_BRD_TOXITRON, NPC_BRD_ELECTRON, NPC_BRD_ARCANOTON, NPC_BRD_MAGMATRON,
            NPC_BRD_ARCANE_ORB, NPC_BRD_SALVAGED_CORE, NPC_BRD_LAGER_KEG, NPC_BRD_LAGER_PUDDLE, NPC_BRD_ROWDY_PATRON,
            NPC_BRD_PORTAL_ANCHOR, NPC_BRD_IMPERIAL_GUARD, NPC_BRD_TWILIGHT_AMBASSADOR, NPC_BRD_STALKER_WAVE_2 } };
        for (std::uint32_t id : wave2)
            CHECK(kCreaturesWave2.Contains(id));
        for (std::uint32_t go = GO_BRD_ENCORE_BANNER; go <= GO_BRD_MOLE_MACHINE; ++go)
            CHECK(kGameObjectsReservation.Contains(go));
        CHECK(kItemsReservation.Contains(kItemVaultTreasureBag) && kItemsReservation.Contains(kItemGuzzlerRope));
        CHECK(kItemCinderOfTheFirelord == 70621);
    }

    void TestTexts()
    {
        std::set<std::uint32_t> entries;
        for (TextRange const& r : kTextRanges)
        {
            CHECK(r.first <= r.last);
            CHECK(r.firstNew >= r.first && r.firstNew <= r.last + 1);
            entries.insert(r.entry);
        }
        CHECK(entries.size() == kTextRanges.size());
    }

    void TestArenas()
    {
        for (BossSpot const& s : kSpots)
        {
            CHECK(In(ArenaFor(s.boss), s.at));
            if (!In(ArenaFor(s.boss), s.at))
                std::printf("  boss %u outside its arena at (%.1f, %.1f, %.1f)\n", s.boss, s.at.x, s.at.y, s.at.z);
        }
        // The hard mode slots fight in their boss's arena; Ribbly and Plugger stay on SmartAI with none.
        for (std::uint32_t id = BOSS_ENCORE; id <= BOSS_AVATAR; ++id)
            CHECK(!ArenaFor(id).Empty());
        CHECK(ArenaFor(BOSS_RIBBLY).Empty() && ArenaFor(BOSS_PLUGGER).Empty() && ArenaFor(kBossCount).Empty());
        // The Ring: the area trigger is on the floor; the champions and the waves are summoned behind the gates.
        CHECK(In(RingOfLawArena(), kRingAreaTrigger));
        CHECK(!In(RingOfLawArena(), kRingChampionSummon.P3()) && !In(RingOfLawArena(), kRingWaveSummon));
        // The Vault: the four posts and the coffer at its rim.
        for (Point3 const& post : kVaultSentinelPosts)
        {
            CHECK(In(BlackVaultArena(), post));
            CHECK(DungeonKit::Distance(post.XY(), kVaultCenter) < kVaultWarderRadius);
        }
        // Incendius: the bulge's tips and the rope's climb spot are on his strip, the giant's spot is off it.
        CHECK(In(IncendiusArena(), kIncendiusTipWest) && In(IncendiusArena(), kIncendiusTipEast));
        CHECK(In(IncendiusArena(), kRopeClimbSpot) && !In(IncendiusArena(), kLakeLordSpot));
        // Bael'Gar: the fight spot and his spawn.
        CHECK(In(BaelgarArena(), kBaelgarFightSpot));
        // F-1a: the Ring's arena is D4's measured floor (BrdRingOfLaw::kRingWall, the same polygon and z band); the
        // 44 yd circle reached 4-20 yd past the wall on the diagonals.
        CHECK(kRingFloorWall.size() == BrdRingOfLaw::kRingWall.size());
        for (std::size_t i = 0; i < kRingFloorWall.size(); ++i)
            CHECK(kRingFloorWall[i].bearingDeg == BrdRingOfLaw::kRingWall[i].bearingDeg
                && kRingFloorWall[i].distance == BrdRingOfLaw::kRingWall[i].distance);
        CHECK(kRingFloorWallPad == BrdRingOfLaw::kRingWallPad);
        CHECK(kRingFloorArenaZMin == BrdRingOfLaw::kRingFloorZMin);
        CHECK(kRingFloorArenaZMax == BrdRingOfLaw::kRingFloorZMax);
        std::vector<Vec2> const floor = RingFloorPolygon();
        CHECK(floor.size() == BrdRingOfLaw::RingFloor().size());
        for (std::size_t i = 0; i < floor.size() && i < BrdRingOfLaw::RingFloor().size(); ++i)
            CHECK(DungeonKit::Distance(floor[i], BrdRingOfLaw::RingFloor()[i]) < 0.001f);
        Vec2 const diagonal = DungeonKit::Advance(kRingCenter.XY(), 45.f * DungeonKit::kPi / 180.f, 30.f);
        CHECK(!RingOfLawArena().Contains(diagonal, -54.f));                 // past the 24 yd diagonal wall
        CHECK(RingOfLawArena().Contains(kRingCenter.XY(), -54.f));
        // Angerforge (D14): the hall to x 650..689, y -16..62. Flamelash (D20): his fight circle, every rune inside.
        CHECK(AngerforgeArena().Contains({ 651.f, -15.f }, -58.f));
        CHECK(AngerforgeArena().Contains({ 688.f, 61.f }, -58.f));
        CHECK(!AngerforgeArena().Contains({ 649.f, 20.f }, -58.f));
        CHECK(FlamelashArena().Contains({ 1012.29f + 37.f, -241.f }, -60.f));
        CHECK(!FlamelashArena().Contains({ 1012.29f + 39.f, -241.f }, -60.f));
        // Incendius (D11): the measured bulge holds his spawn and is off the lake on both sides of the axis.
        CHECK(In(IncendiusArena(), kIncendiusSpawn));
        CHECK(!IncendiusArena().Contains({ 905.f, -255.f }, -71.9f));
        // The champions' arena is the Ring's.
        CHECK(In(ArenaFor(BOSS_ENCORE), kGrimstoneSummon.P3()));
    }

    void TestSections()
    {
        CHECK(kSections.size() == 4);
        std::set<std::uint32_t> lfg;
        for (FinderSection const& s : kSections)
        {
            CHECK(SectionByNumber(s.number) == &s);
            CHECK(SectionOf(s.endSlot) == s.number);
            CHECK(s.lfgHeroic == 309 + s.number);       // heroic 310-313, sections 1-4
            lfg.insert(s.lfgNormal);
            lfg.insert(s.lfgHeroic);
        }
        CHECK(lfg == std::set<std::uint32_t>({ 30, 308, 309, 276, 310, 311, 312, 313 }));
        CHECK(!SectionByNumber(0) && !SectionByNumber(5));
        CHECK(kSections[0].endSlot == BOSS_RING_OF_LAW && kSections[1].endSlot == BOSS_BAELGAR);
        CHECK(kSections[2].endSlot == BOSS_ARGELMACH && kSections[3].endSlot == BOSS_EMPEROR);
        // Section 2 starts clear of the arena and its area trigger (the BRS K-m3 lesson).
        Point3 const s2 = kSections[1].start.P3();
        CHECK(!In(RingOfLawArena(), s2));
        CHECK(Distance3(s2, kRingAreaTrigger) > kRingAreaTriggerRadius + 10.f);
        // Section 3 starts 8 yd from the Shadowforge Lock (615.6, -49.8) and lists it first on its path.
        CHECK(DungeonKit::Distance(kSections[2].start.XY(), { 615.6f, -49.8f }) < 9.f);
        CHECK(kSections[2].doors[0] == GO_SHADOW_LOCK);
        // Section 4 passes the Bar Door first and the throne door last.
        CHECK(kSections[3].doors[0] == GO_BAR_DOOR && kSections[3].doors[6] == GO_THRONE_ROOM);
        // R-1-KIT n1 / R-1-B n5: the starts carry the Finder rows' facing (lfg_classic_sections.py, checkpoint SQL).
        CHECK(std::fabs(kSections[1].start.o - 5.18f) < 0.001f && std::fabs(kSections[2].start.o - 6.05f) < 0.001f);
        CHECK(std::fabs(kSections[3].start.o - 4.64f) < 0.001f);
    }

    void TestRingRolls()
    {
        // Every one of the 30 ordered pairs is reachable and never a champion against himself; sentences 1-3, waves
        // 1-6.
        std::set<std::pair<std::uint32_t, std::uint32_t>> pairs;
        std::set<std::uint32_t> sentences;
        std::set<std::uint32_t> waves;
        for (std::uint32_t r3 = 0; r3 < 60; ++r3)
            for (std::uint32_t r4 = 0; r4 < 60; ++r4)
            {
                RingRolls const r = RollRing(r3, r4, r3, r4);
                CHECK(r.Rolled());
                CHECK(r.first != r.second);
                CHECK(r.first >= 1 && r.first <= 6 && r.second >= 1 && r.second <= 6);
                pairs.insert({ r.first, r.second });
                sentences.insert(r.sentence);
                waves.insert(r.wave);
            }
        CHECK(pairs.size() == 30);
        CHECK(sentences == std::set<std::uint32_t>({ 1, 2, 3 }));
        CHECK(waves.size() == 6);
        // A broken saved set rolls again.
        CHECK(!SanitizeRingRolls({ 1, 1, 2, 2 }).Rolled());
        CHECK(!SanitizeRingRolls({ 4, 1, 1, 2 }).Rolled());
        CHECK(!SanitizeRingRolls({ 1, 1, 0, 2 }).Rolled());
        CHECK(SanitizeRingRolls({ 3, 6, 6, 1 }).Rolled());
        CHECK(kRingFavorStart == 5 && kRingFavorMax == 10);
    }

    void TestVault()
    {
        // The Dark Coffer starts it only once Stilgiss and Verek are DONE, and only from NOT_STARTED.
        CHECK(!VaultTriggerAccepted(State::NotStarted, State::NotStarted));
        CHECK(!VaultTriggerAccepted(State::NotStarted, State::InProgress));
        CHECK(VaultTriggerAccepted(State::NotStarted, State::Done));
        CHECK(!VaultTriggerAccepted(State::InProgress, State::Done));
        CHECK(!VaultTriggerAccepted(State::Done, State::Done));
        // After a wipe the slot is NOT_STARTED again: the trigger works again.
        CHECK(VaultTriggerAccepted(SettledSlotState(State::NotStarted), State::Done));
        // The idle watch: never in the grace, never with every warder dead.
        CHECK(!VaultAttemptLost(kVaultGraceMs - 1, kVaultIdleMs, true));
        CHECK(!VaultAttemptLost(kVaultGraceMs, kVaultIdleMs - 1, true));
        CHECK(VaultAttemptLost(kVaultGraceMs, kVaultIdleMs, true));
        CHECK(!VaultAttemptLost(kVaultGraceMs, kVaultIdleMs, false));
        // R-1-KIT B1: the watch finishes an attempt with every warder dead (a death the instance missed), at once.
        CHECK(VaultWatchFor(kVaultWatchMs, 0, false) == VaultWatchVerdict::Done);
        CHECK(VaultWatchFor(kVaultGraceMs, kVaultIdleMs, false) == VaultWatchVerdict::Done);
        CHECK(VaultWatchFor(kVaultGraceMs, kVaultIdleMs, true) == VaultWatchVerdict::Lost);
        CHECK(VaultWatchFor(kVaultGraceMs - 1, kVaultIdleMs, true) == VaultWatchVerdict::Continue);
        // A death counts by entry or by the list, never by where it died: a sentinel gripped out of the room counts;
        // the Black Vault's unlisted 8905 trash does not.
        CHECK(CountsAsVaultWarder(NPC_BRD_VAULT_SENTINEL, false) && CountsAsVaultWarder(NPC_DOOMGRIP, false));
        CHECK(CountsAsVaultWarder(NPC_WARBRINGER_CONSTRUCT, true));
        CHECK(!CountsAsVaultWarder(NPC_WARBRINGER_CONSTRUCT, false));
        CHECK(IsVaultConstructAt(NPC_BRD_VAULT_SENTINEL, 40.f));
        CHECK(IsVaultConstructAt(NPC_WARBRINGER_CONSTRUCT, kVaultWarderRadius));
        CHECK(!IsVaultConstructAt(NPC_WARBRINGER_CONSTRUCT, kVaultWarderRadius + 0.1f));
        CHECK(!IsVaultConstructAt(NPC_DOOMGRIP, 1.f));
        // Section 10: the Dark Coffer is clickable (the key spent on nothing never) only once Stilgiss and Verek are
        // DONE.
        CHECK(!DarkCofferSelectable(State::NotStarted) && !DarkCofferSelectable(State::InProgress));
        CHECK(DarkCofferSelectable(State::Done));
        CHECK(kItemVaultTreasureBagHeroic == 70623 && kItemDarkKeeperKey == 11197);
        CHECK(kSpellsStilgissVerek.Contains(kSpellStilgissVerekCredit));
        CHECK(DATA_VAULT_DOOMGRIP_ITEM == 67 && DATA_ENCORE_WON == 68 && DATA_ENCORE_RUNNING == 69);
        CHECK(DATA_GALLERY_STOOD_DOWN == 70 && DATA_STILGISS_VEREK_FIGHT == 71);
        // The loot clock: the Cinder always; the gear before 90 s; a bag before 75 s, the last before 110 s.
        VaultSafe const none = VaultSafeFor(0);
        CHECK(!none.cinder && !none.gear && none.bags == 0);
        VaultSafe const fast = VaultSafeFor(60);
        CHECK(fast.cinder && fast.gear && fast.bags == 2);
        VaultSafe const mid = VaultSafeFor(80);
        CHECK(mid.cinder && mid.gear && mid.bags == 1);
        VaultSafe const slow = VaultSafeFor(100);
        CHECK(slow.cinder && !slow.gear && slow.bags == 1);
        VaultSafe const late = VaultSafeFor(110);
        CHECK(late.cinder && !late.gear && late.bags == 0);
    }

    void TestBarTombMoira()
    {
        // The Bar Door: the love potion or Phalanx's death open it; the ale run's end blasts it; else shut.
        CHECK(BarDoorState(false, State::NotStarted, false) == BarDoor::Closed);
        CHECK(BarDoorState(false, State::InProgress, false) == BarDoor::Closed);
        CHECK(BarDoorState(false, State::Done, false) == BarDoor::Blasted);
        CHECK(BarDoorState(true, State::NotStarted, false) == BarDoor::Open);
        CHECK(BarDoorState(false, State::NotStarted, true) == BarDoor::Open);
        CHECK(BarDoorState(false, State::Done, true) == BarDoor::Open);    // D17 / D19: Phalanx's death opens it fully
        // The Tomb's doors.
        CHECK(TombDoorsFor(State::NotStarted).enterOpen && !TombDoorsFor(State::NotStarted).exitOpen);
        CHECK(!TombDoorsFor(State::InProgress).enterOpen && !TombDoorsFor(State::InProgress).exitOpen);
        CHECK(TombDoorsFor(State::Done).enterOpen && TombDoorsFor(State::Done).exitOpen);
        // Moira stands down once Dagran is DONE, or once saved by the Avatar kill.
        CHECK(!MoiraStandsDown(State::NotStarted, false) && !MoiraStandsDown(State::InProgress, false));
        CHECK(MoiraStandsDown(State::Done, false) && MoiraStandsDown(State::NotStarted, true));
        // R-2-C m2: the princess swap waits while Dagran's fight runs.
        CHECK(!MoiraSwapAllowed(State::InProgress));
        CHECK(MoiraSwapAllowed(State::NotStarted) && MoiraSwapAllowed(State::Done) && MoiraSwapAllowed(State::Fail));
        // The rope goes one way: dropped, then placed.
        CHECK(RopeChangeAllowed(ROPE_NONE, ROPE_DROPPED) && RopeChangeAllowed(ROPE_DROPPED, ROPE_PLACED));
        CHECK(RopeChangeAllowed(ROPE_NONE, ROPE_PLACED));
        CHECK(!RopeChangeAllowed(ROPE_PLACED, ROPE_DROPPED) && !RopeChangeAllowed(ROPE_DROPPED, ROPE_DROPPED));
        CHECK(!RopeChangeAllowed(ROPE_PLACED, 3));
    }

    void TestHardModes()
    {
        // All four heroic only.
        CHECK(!BannerThrowAllowed(1, false, State::NotStarted) && BannerThrowAllowed(1, true, State::InProgress));
        CHECK(!BannerThrowAllowed(1, true, State::Done) && BannerThrowAllowed(0, false, State::Done));
        CHECK(!BannerBurnAllowed(1, true, false, State::InProgress) && BannerBurnAllowed(1, true, true,
            State::InProgress));
        CHECK(!BannerBurnAllowed(1, false, true, State::NotStarted) && !BannerBurnAllowed(1, true, true, State::Done));
        CHECK(CinderAllowed(1, true, State::NotStarted) && !CinderAllowed(1, true, State::InProgress));
        CHECK(!CinderAllowed(1, true, State::Done) && !CinderAllowed(1, false, State::NotStarted));
        CHECK(!ConsoleAllowed(1, true, false, State::NotStarted) && ConsoleAllowed(1, true, true, State::NotStarted));
        CHECK(!ConsoleAllowed(1, true, true, State::InProgress) && !ConsoleAllowed(1, false, true, State::NotStarted));
        CHECK(AvatarAllowed(1, true, true, State::InProgress) && !AvatarAllowed(1, true, true, State::NotStarted));
        CHECK(!AvatarAllowed(1, true, false, State::InProgress) && !AvatarAllowed(1, false, true, State::InProgress));
        CHECK(AvatarAllowed(0, false, false, State::Done));     // clearing is always allowed
        // The Encore's kill needs the explicit report (D4 request 2): heroic, burned, while the Ring runs.
        CHECK(EncoreWonAccepted(1, true, true, State::InProgress));
        CHECK(!EncoreWonAccepted(0, true, true, State::InProgress));
        CHECK(!EncoreWonAccepted(1, false, true, State::InProgress));
        CHECK(!EncoreWonAccepted(1, true, false, State::InProgress) && !EncoreWonAccepted(1, true, true, State::Done));
        // Section 10: a wipe in the Encore puts the banner out; a wipe before it (the banner burned, no Encore yet)
        // keeps it lit.
        CHECK(EncoreWipeUnlights(true, true) && !EncoreWipeUnlights(false, true) && !EncoreWipeUnlights(true, false));
        // The banner can be burned again after the unlit wipe (still thrown, the Ring not won).
        CHECK(BannerBurnAllowed(1, true, true, State::NotStarted));
        // An attempt ends from IN_PROGRESS only.
        CHECK(AttemptEnded(State::InProgress, State::NotStarted) && AttemptEnded(State::InProgress, State::Fail));
        CHECK(!AttemptEnded(State::InProgress, State::Done) && !AttemptEnded(State::NotStarted, State::NotStarted));
        // A cold load settles TO_BE_DECIDED to NOT_STARTED and leaves the rest.
        CHECK(SettledSlotState(State::ToBeDecided) == State::NotStarted);
        CHECK(SettledSlotState(State::Done) == State::Done && SettledSlotState(State::NotStarted) == State::NotStarted);
    }

    void TestGallery()
    {
        // Section 10 / R-1-RING MJ-1: every gallery unit, by entry, distance and height ([db] 2026-11-17: z -37 to
        // -34 at 50-67 yd, two footmen at z -46 and 71-72 yd; the depths' guardsmen and the floor are out).
        for (std::uint32_t entry : { 8916u, 8896u, 8902u, 8904u, 8892u, 8893u, 8894u, 8895u })
        {
            CHECK(IsGalleryEntry(entry));
            CHECK(IsGalleryUnit(entry, 55.f, -36.9f) && IsGalleryUnit(entry, 71.8f, -46.1f));
            CHECK(!IsGalleryUnit(entry, 83.3f, -46.2f) && !IsGalleryUnit(entry, 60.f, -83.f));
        }
        CHECK(!IsGalleryEntry(8891) && !IsGalleryEntry(NPC_GRIMSTONE) && !IsGalleryEntry(8921));
        CHECK(NPC_ANVILRAGE_FOOTMAN == 8892 && NPC_ANVILRAGE_OFFICER == 8895);
        // The trigger: a section 2 Finder group (normal or heroic), or the first entry at the S2 start.
        std::uint32_t const n = kSections[1].lfgNormal;
        std::uint32_t const h = kSections[1].lfgHeroic;
        CHECK(n == 308 && h == 311);
        CHECK(GalleryStandsDownOnEntry(false, State::NotStarted, 308, n, h, false, 900.f));
        CHECK(GalleryStandsDownOnEntry(false, State::NotStarted, 311, n, h, false, 900.f));
        CHECK(!GalleryStandsDownOnEntry(false, State::NotStarted, 30, n, h, false, 900.f));     // section 1
        CHECK(!GalleryStandsDownOnEntry(false, State::NotStarted, 0, n, h, false, 900.f));      // a full run
        CHECK(GalleryStandsDownOnEntry(false, State::NotStarted, 0, n, h, true, kGalleryStartEntryYd));   // `.dc test`
        CHECK(!GalleryStandsDownOnEntry(false, State::NotStarted, 0, n, h, true, kGalleryStartEntryYd + 1.f));
        CHECK(!GalleryStandsDownOnEntry(false, State::NotStarted, 0, n, h, false, 2.f));  // a full run back at S2
        CHECK(!GalleryStandsDownOnEntry(true, State::NotStarted, 308, n, h, true, 0.f));  // once
        CHECK(!GalleryStandsDownOnEntry(false, State::Done, 308, n, h, true, 0.f));       // the Ring's win did it
        // The S2 start (S2g, smoke-run fix 2026-11-18) is up in the gallery, off the Ring's floor, and inside the band
        // the stand-down covers, so the units around a Finder arrival are the stood-down ones.
        Point3 const s2 = kSections[1].start.P3();
        CHECK(!In(RingOfLawArena(), s2));
        CHECK(DungeonKit::Distance(s2.XY(), kRingCenter.XY()) < kGalleryRadius && s2.z > kGalleryZMin);
    }

    void TestSave()
    {
        // A full round trip keeps every saved field; per-attempt states come back NOT_STARTED.
        BrdSave s;
        s.states[BOSS_GERSTAHN] = State::Done;
        s.states[BOSS_STILGISS_VEREK] = State::Done;
        s.states[BOSS_VAULT] = State::Done;
        s.states[BOSS_INCENDIUS] = State::Done;
        s.states[BOSS_LORD_OF_THE_LAKE] = State::Done;
        s.states[BOSS_RING_OF_LAW] = State::InProgress;
        s.ring = { 2, 5, 3, 6 };
        s.bannerThrown = 1;
        s.bannerBurned = 1;
        s.rope = ROPE_PLACED;
        s.cinderUsed = 1;
        s.vaultClock = 88;
        s.moiraSaved = 1;
        s.bar = State::Done;
        s.phalanxActivated = State::Done;
        s.lovePotion = State::Done;
        s.lyceum = State::Done;
        s.galleryStoodDown = 1;
        s.doomgripItem = 72982;
        std::string const text = FormatBrdSave(s);
        CHECK(text.rfind("B D W ", 0) == 0);
        BrdSave r;
        CHECK(ParseBrdSave(text, r));
        CHECK(r.states[BOSS_GERSTAHN] == State::Done && r.states[BOSS_STILGISS_VEREK] == State::Done);
        CHECK(r.states[BOSS_VAULT] == State::Done && r.states[BOSS_LORD_OF_THE_LAKE] == State::Done);
        CHECK(r.states[BOSS_RING_OF_LAW] == State::NotStarted);       // a reload ends every fight
        CHECK(r.ring.sentence == 2 && r.ring.wave == 5 && r.ring.first == 3 && r.ring.second == 6);
        CHECK(r.bannerThrown == 1 && r.bannerBurned == 1 && r.rope == ROPE_PLACED && r.cinderUsed == 1);
        CHECK(r.vaultClock == 88 && r.moiraSaved == 1 && r.bar == State::Done && r.phalanxActivated == State::Done);
        CHECK(r.lovePotion == State::Done && r.lyceum == State::Done);
        CHECK(r.galleryStoodDown == 1 && r.doomgripItem == 72982);
        CHECK(FormatBrdSave(r) != text);    // only the Ring's IN_PROGRESS changed
        r.states[BOSS_RING_OF_LAW] = State::InProgress;
        CHECK(FormatBrdSave(r) == text);

        // Sanitizing: a burned banner needs a thrown one; a hard mode kill needs its boss DONE; the Vault's clock
        // needs the Vault DONE; an ale run in progress does not survive.
        BrdSave bad;
        bad.bannerBurned = 1;
        bad.states[BOSS_PROTOTYPE] = State::Done;
        bad.vaultClock = 70;
        bad.bar = State::Special;
        bad.rope = 9;
        bad.ring = { 1, 1, 4, 4 };
        bad.doomgripItem = 22205;          // the Vault not DONE: Doomgrip's item does not survive
        bad.galleryStoodDown = 5;
        BrdSave clean;
        CHECK(ParseBrdSave(FormatBrdSave(bad), clean));
        CHECK(clean.doomgripItem == 0 && clean.galleryStoodDown == 1);
        CHECK(clean.bannerBurned == 0 && clean.states[BOSS_PROTOTYPE] == State::NotStarted);
        CHECK(clean.vaultClock == 0 && clean.bar == State::NotStarted && clean.rope == ROPE_NONE);
        CHECK(!clean.ring.Rolled());

        // A short save from an older build of this script leaves the tail at its defaults.
        BrdSave shortSave;
        CHECK(ParseBrdSave("B D W 3 0 3", shortSave));
        CHECK(shortSave.states[BOSS_GERSTAHN] == State::Done && shortSave.states[BOSS_GREBMAR] == State::Done);
        CHECK(shortSave.states[BOSS_ROCCOR] == State::NotStarted && !shortSave.ring.Rolled());
        // The save before F-1a (24 states and 14 extras) loads with the gallery and Doomgrip's item at 0.
        BrdSave pre = s;
        std::string preText = FormatBrdSave(pre);
        for (int i = 0; i < 2; ++i)
            preText = preText.substr(0, preText.find_last_of(' '));
        BrdSave preRead;
        CHECK(ParseBrdSave(preText, preRead));
        CHECK(preRead.galleryStoodDown == 0 && preRead.doomgripItem == 0 && preRead.lyceum == State::Done);

        // Garbage and empty strings are ignored.
        BrdSave none;
        CHECK(!ParseBrdSave("", none));
        CHECK(!ParseBrdSave("X Y Z 1 2 3", none));
        CHECK(!ParseBrdSave("B D W", none));
    }

    void TestStockSave()
    {
        // The stock save (instance_blackrock_depths at 60bac7405): no header, "e0 .. e5 GhostKillCount
        // PhalanxActivationState LovePotionEventState". Ring DONE, Vault DONE, bar DONE, Tomb (7 ghosts), Lyceum
        // DONE, Iron Hall DONE, Phalanx DONE, love potion DONE.
        BrdSave s;
        CHECK(ParseBrdSave("3 3 3 0 3 3 7 3 3", s));
        CHECK(s.states[BOSS_RING_OF_LAW] == State::Done && s.states[BOSS_VAULT] == State::Done);
        CHECK(s.bar == State::Done && s.states[BOSS_THE_SEVEN] == State::Done && s.lyceum == State::Done);
        CHECK(s.states[BOSS_MAGMUS] == State::Done && s.phalanxActivated == State::Done);
        CHECK(s.lovePotion == State::Done);
        CHECK(!s.ring.Rolled() && s.bannerThrown == 0);     // stock never saved them: rolled at the first Update
        // IN_PROGRESS and a ghost count under 7 come back as NOT_STARTED (the stock Load's rule).
        BrdSave p;
        CHECK(ParseBrdSave("1 1 1 1 1 1 4 1 0", p));
        CHECK(p.states[BOSS_RING_OF_LAW] == State::NotStarted && p.states[BOSS_VAULT] == State::NotStarted);
        CHECK(p.bar == State::NotStarted && p.states[BOSS_THE_SEVEN] == State::NotStarted);
        CHECK(p.phalanxActivated == State::NotStarted && p.lovePotion == State::NotStarted);
        // The old six-field save still reads.
        BrdSave old;
        CHECK(ParseBrdSave("0 0 0 3 0 0", old));
        CHECK(old.states[BOSS_THE_SEVEN] == State::Done);
        // The completed-encounter mask fills the slots stock never wrote (bits 0, 8 and 18 here).
        BrdSave masked;
        CHECK(ParseBrdSave("3 0 0 0 0 0 0 0 0", masked, (1u << 0) | (1u << 8) | (1u << 18)));
        CHECK(masked.states[BOSS_GERSTAHN] == State::Done && masked.states[BOSS_BAELGAR] == State::Done);
        CHECK(masked.states[BOSS_EMPEROR] == State::Done && masked.states[BOSS_ROCCOR] == State::NotStarted);
        // The mask is ignored on this script's own save (it carries its own states).
        BrdSave own;
        CHECK(ParseBrdSave("B D W 0 0 0", own, 0x7FFFF));
        CHECK(own.states[BOSS_GERSTAHN] == State::NotStarted);
        // Fewer than six stock fields is not a save.
        BrdSave tooShort;
        CHECK(!ParseBrdSave("3 3 3", tooShort));
    }
}

int main()
{
    TestBossStates();
    TestEncounterBits();
    TestStockDataIds();
    TestTypeMirrors();
    TestEntries();
    TestWaveSwitch();
    TestCollisionGuard();
    TestSlices();
    TestTexts();
    TestArenas();
    TestSections();
    TestRingRolls();
    TestVault();
    TestBarTombMoira();
    TestHardModes();
    TestGallery();
    TestSave();
    TestStockSave();
    return Report("blackrock_depths_test");
}
