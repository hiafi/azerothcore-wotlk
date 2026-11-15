// Host tests for the Blackrock Spire skeleton (WP-S0): BlackrockSpireRework.h (the 28 boss states with every stock
// slot on its stock number, data ids, entries, the wave switch, slices, measured points, arenas, the rune room rules,
// the Urok pile, the Solakar event, the hard mode and insult rules, flex pairs, the save string and its stock "BRS"
// reader). DB positions (spawns, objects, triggers) are exact; the rest is the NAVMESH report's.
#include "BlackrockSpireRework.h"
#include "check.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <set>
#include <string>
#include <vector>

using namespace BlackrockSpireRework;
namespace State = DungeonKit::State;

namespace
{
    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    struct BossSpot
    {
        std::uint32_t boss;
        Point3 at;
    };

    // Where each fighting boss stands at the pull (spawned bosses: their spawn; summoned: their summon or arrival).
    std::vector<BossSpot> const kSpots{
        { BOSS_OMOKK, kOmokkSpawn }, { BOSS_VOSHGAJIN, kVoshgajinSpawn }, { BOSS_VOONE, kVooneSpawn },
        { BOSS_SMOLDERWEB, kSmolderwebSpawn }, { BOSS_UROK, kUrokSummon.P3() }, { BOSS_ZIGRIS, kZigrisSpawn },
        { BOSS_HALYCON, kHalyconSpawn }, { BOSS_GIZRUL, { kHalyconDenMouth.x, kHalyconDenMouth.y, 64.f } },
        { BOSS_WYRMTHALAK, kWyrmthalakSpawn }, { BOSS_EMBERSEER, kEmberseerSpawn },
        { BOSS_SOLAKAR, kSolakarPosBoss.P3() }, { BOSS_REND, kStadiumTrigger }, { BOSS_GYTH, kGythHoverGround },
        { BOSS_BEAST, kBeastSpawn }, { BOSS_DRAKKISATH, kDrakkisathSpawn } };

    void TestBossStates()
    {
        CHECK(kBossCount == 28);
        CHECK(kStockEncounterCount == 23);
        // Stock numbers (blackrock_spire.h DataTypes), the ones stock scripts and mod-dungeon-clear write and read.
        CHECK(BOSS_OMOKK == 0 && BOSS_VOSHGAJIN == 1 && BOSS_VOONE == 2 && BOSS_SMOLDERWEB == 3);
        CHECK(BOSS_UROK == 4 && BOSS_ZIGRIS == 5 && BOSS_GIZRUL == 6 && BOSS_HALYCON == 7 && BOSS_WYRMTHALAK == 8);
        CHECK(BOSS_EMBERSEER == 9 && BOSS_REND == 10 && BOSS_GYTH == 11 && BOSS_BEAST == 12);
        CHECK(BOSS_DRAKKISATH == 13 && BOSS_VALTHALAK == 14 && BOSS_DRAGONSPIRE_ROOM == 15);
        for (std::uint32_t i = 0; i < kHallRuneCount; ++i)
            CHECK(BOSS_HALL_RUNE_1 + i == 16 + i);
        CHECK(BOSS_SOLAKAR == 23 && BOSS_MOR_GRAYHOOF == 24 && BOSS_VAELASTRASZ_SLOT == 25);
        CHECK(DATA_VAELASTRASZ == 25 && DATA_SOLAKAR_EVENT == 23);
        CHECK(BOSS_WAR_HORN == 26 && BOSS_GENERALS_ARMY == 27);
        CHECK(IsHardModeSlot(26) && IsHardModeSlot(27) && !IsHardModeSlot(8) && !IsHardModeSlot(13));
        CHECK(IsStockBossSlot(BOSS_VALTHALAK) && IsStockBossSlot(BOSS_MOR_GRAYHOOF) && !IsStockBossSlot(BOSS_OMOKK));
        for (std::uint32_t id = 15; id <= 22; ++id)
            CHECK(IsRoomSlot(id));
        CHECK(!IsRoomSlot(14) && !IsRoomSlot(23));
        for (char const* name : kBossNames)
            CHECK(name && *name);
        // The encounter slots: the 14 DungeonEncounter bosses (Solakar is 23).
        std::uint32_t encounters = 0;
        for (std::uint32_t id = 0; id < kBossCount; ++id)
            encounters += IsEncounterSlot(id) ? 1 : 0;
        CHECK(encounters == 15);       // 0-13 and 23 (Gyth's 11 has no DungeonEncounter row of its own)
        CHECK(IsEncounterSlot(BOSS_SOLAKAR) && !IsEncounterSlot(BOSS_MOR_GRAYHOOF) && !IsEncounterSlot(BOSS_WAR_HORN));
    }

    void TestData()
    {
        // New data ids clear every stock SetData type (1, 4, 14, 23, 25) and area trigger 2046.
        std::set<std::uint32_t> const stock{ DATA_AREATRIGGER, DATA_UROK_EVENT, DATA_VALTHALAK_DONE,
            DATA_SOLAKAR_EVENT, DATA_VAELASTRASZ };
        CHECK(stock == (std::set<std::uint32_t>{ 1, 4, 14, 23, 25 }));
        for (std::uint32_t d : { DATA_NEF_INSULTED, DATA_UROK_PILE, DATA_SOLAKAR_FLAME, DATA_WAR_HORN,
            DATA_GENERALS_ARMY, DATA_HALL_RUNES_DONE, DATA_ROOM_CHECK })
        {
            CHECK(d >= 30 && d < 100);
            CHECK(!stock.count(d));
            CHECK(d != kAreaTriggerDragonspireHall);
        }
        CHECK(kAreaTriggerDragonspireHall == 2046 && kAreaTriggerBlackrockStadium == 2026);
        CHECK(kEventBlackrockAltar == 4884 && kEventUrokPile == 4845);
    }

    void TestEntries()
    {
        // Every boss entry maps to its slot and back.
        for (std::uint32_t id = 0; id < kBossCount; ++id)
        {
            std::uint32_t const entry = EntryOfBoss(id);
            if (!entry || IsStockBossSlot(id))
                continue;
            CHECK(BossOfEntry(entry) == id);
        }
        CHECK(BossOfEntry(NPC_HALYCON) == BOSS_HALYCON && BossOfEntry(NPC_GIZRUL) == BOSS_GIZRUL);
        CHECK(!BossOfEntry(NPC_VALTHALAK) && !BossOfEntry(NPC_CHROMATIC_ELITE_GUARD));
        CHECK(IsSummonedBoss(NPC_UROK) && IsSummonedBoss(NPC_GIZRUL) && IsSummonedBoss(NPC_GYTH));
        CHECK(IsSummonedBoss(NPC_SOLAKAR) && !IsSummonedBoss(NPC_HALYCON));
        CHECK(IsBrsNefarius(10162) && IsBrsNefarius(NPC_BRS_NEFARIUS) && !IsBrsNefarius(NPC_REND));
        // New creatures and objects sit in the reservation; every wave 1 add below every wave 2 add (mint order).
        for (std::uint32_t c = NPC_BRS_BRAWL_FAN; c <= NPC_BRS_STALKER; ++c)
            CHECK(kCreaturesWave1.Contains(c));
        for (std::uint32_t c = NPC_BRS_BINDING_POST; c <= NPC_BRS_CHALLENGE_RING; ++c)
            CHECK(kCreaturesWave2.Contains(c));
        CHECK(kCreaturesWave1.last + 1 == kCreaturesWave2.first);
        CHECK(kCreaturesReservation.first == kCreaturesWave1.first);
        CHECK(kCreaturesReservation.last == kCreaturesWave2.last);
        for (std::uint32_t g = GO_BRS_STUCK_AXE; g <= GO_BRS_WAR_HORN; ++g)
            CHECK(kGameObjectsReservation.Contains(g));
        // The hall runes in stock order.
        CHECK(kHallRunes[0] == 175197 && kHallRunes[6] == 175194);
        for (std::uint32_t i = 0; i < kHallRuneCount; ++i)
            CHECK(HallRuneIndex(kHallRunes[i]) == i);
        CHECK(!HallRuneIndex(GO_EMBERSEER_RUNE_1));
    }

    void TestWaveSwitch()
    {
        CHECK(!kWave2Bound);
        for (std::uint32_t id : { BOSS_EMBERSEER, BOSS_REND, BOSS_GYTH, BOSS_BEAST, BOSS_DRAKKISATH, BOSS_SOLAKAR,
            BOSS_GENERALS_ARMY })
        {
            CHECK(IsWave2Boss(id));
            CHECK(!IsReworkBound(id, false));
            CHECK(IsReworkBound(id, true));
        }
        for (std::uint32_t id = BOSS_OMOKK; id <= BOSS_WYRMTHALAK; ++id)
        {
            CHECK(!IsWave2Boss(id));
            CHECK(IsReworkBound(id, false));
        }
        CHECK(IsReworkBound(BOSS_WAR_HORN, false));
        for (std::uint32_t id : { BOSS_VALTHALAK, BOSS_MOR_GRAYHOOF, BOSS_DRAGONSPIRE_ROOM, BOSS_HALL_RUNE_3,
            BOSS_VAELASTRASZ_SLOT })
            CHECK(!IsReworkBound(id, true));
    }

    void TestSlices()
    {
        // The slices tile the reservation in order, no gap, no overlap.
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        CHECK(kSpellSlices.back().last == kSpellsReservation.last);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        CHECK(kSpellsOmokk.first == 210020 && kSpellsWarHorn.last == 210339 && kSpellsEmberseer.first == 210350);
        CHECK(kSpellsGeneralsArmy.last == 210619 && kSpellsReservation.last == 210699);
        // Text ranges: one per boss entry, stock groups below firstNew.
        for (TextRange const& t : kTextRanges)
        {
            CHECK(t.first <= t.last);
            CHECK(t.firstNew <= t.last + 1);
        }
    }

    void TestArenas()
    {
        for (BossSpot const& s : kSpots)
        {
            CHECK(In(ArenaFor(s.boss), s.at));
            if (!In(ArenaFor(s.boss), s.at))
                std::printf("  boss %u (%s) is outside its arena\n", s.boss, kBossNames[s.boss]);
        }
        // Summoned and balcony starts that lie outside their arena (they walk or jump in).
        CHECK(!In(HalyconGizrulArena(), kGizrulSpawn));
        CHECK(!In(RendGythArena(), kRendSpawn));
        CHECK(!In(RendGythArena(), kGythSummon.P3()));
        // The hard mode slots fight in their boss's arena; stock and room slots have none.
        CHECK(In(ArenaFor(BOSS_WAR_HORN), kWyrmthalakSpawn));
        CHECK(In(ArenaFor(BOSS_GENERALS_ARMY), kDrakkisathSpawn));
        CHECK(ArenaFor(BOSS_VALTHALAK).Empty() && ArenaFor(BOSS_HALL_RUNE_1).Empty());
        // Omokk's showdown spots are on his arena's bridge; Voone's charge spot on his.
        for (Point3 const& p : kOmokkLandings)
            CHECK(In(OmokkArena(), p));
        CHECK(In(OmokkArena(), kOmokkShowdownLanding));
        CHECK(In(OmokkArena(), kOmokkHaulUpWest) && In(OmokkArena(), kOmokkHaulUpEast));
        CHECK(kOmokkPitDropZ < kOmokkBridgeDeckZ && kOmokkPitFloorZ < kOmokkPitDropZ);
        CHECK(In(VooneArena(), kVooneChargeSpot));
        for (Vec2 const& egg : kSmolderwebEggSpots)
            CHECK(SmolderwebArena().Contains(egg, 9.f));
        for (Vec2 const& crate : kZigrisCrates)
            CHECK(ZigrisArena().Contains(crate, 88.f));
        CHECK(In(UrokArena(), kUrokPile));
        for (Vec2 const& post : kEmberseerPosts)
            CHECK(EmberseerArena().Contains(post, 92.f));
        CHECK(In(EmberseerArena(), kBlackrockAltar));
        CHECK(In(SolakarArena(), kSolakarPosLeft.P3()) && In(SolakarArena(), kSolakarPosRight.P3()));
    }

    void TestDragonspireHall()
    {
        // The seven hall runes [db] and the area trigger's own spot lie in the self-start box.
        std::vector<Point3> const runes{ { 192.74f, -258.394f, 76.8603f }, { 124.779f, -298.037f, 70.8526f },
            { 228.803f, -301.542f, 76.8812f }, { 125.358f, -340.465f, 70.8752f }, { 215.157f, -334.733f, 76.8124f },
            { 155.334f, -353.045f, 70.8337f }, { 155.321f, -286.074f, 70.8763f } };
        for (Point3 const& r : runes)
            CHECK(InDragonspireHall(r.x, r.y, r.z));
        CHECK(InDragonspireHall(102.43f, -319.167f, 65.4635f));
        // Not Emberseer's hall above, not the Rookery, not the LBRS entrance.
        CHECK(!InDragonspireHall(kEmberseerSpawn.x, kEmberseerSpawn.y, kEmberseerSpawn.z));
        CHECK(!InDragonspireHall(144.0f, -260.0f, 92.0f));
        CHECK(!InDragonspireHall(kFatherFlame.x, kFatherFlame.y, kFatherFlame.z));
        CHECK(!InDragonspireHall(78.51f, -225.04f, 49.84f));
        // K-m3: the Upper Spire Finder start / checkpoint stands inside the box (the self-start fires on arrival, by
        // design), 0.25 yd from its west edge; DT test_blackrock_spire_kit checks the two data copies match it.
        CHECK(InDragonspireHall(kUbrsFinderStart.x, kUbrsFinderStart.y, kUbrsFinderStart.z));
        CHECK(kUbrsFinderStart.x - kDragonspireHall.minX > 0.2f && kUbrsFinderStart.x - kDragonspireHall.minX < 0.3f);

        // STORE: a DONE rune is never snapshotted again; an unloaded grid waits.
        CHECK(RuneShouldSnapshot(State::NotStarted, true));
        CHECK(!RuneShouldSnapshot(State::Done, true));
        CHECK(!RuneShouldSnapshot(State::NotStarted, false));
        // CHECK: only a snapshotted, lit rune on a loaded grid with its pack dead closes.
        CHECK(RuneShouldClose(State::NotStarted, true, true, true, false));
        CHECK(!RuneShouldClose(State::NotStarted, true, true, true, true));      // a pack member alive
        CHECK(!RuneShouldClose(State::NotStarted, false, true, true, false));    // never snapshotted
        CHECK(!RuneShouldClose(State::NotStarted, true, false, true, false));    // already out
        CHECK(!RuneShouldClose(State::NotStarted, true, true, false, false));    // grid unloaded
        CHECK(!RuneShouldClose(State::Done, true, true, true, false));
        // The self-start: room not DONE, a player in the hall, a rune still lacking its snapshot.
        CHECK(RoomNeedsSelfStart(State::NotStarted, true, true));
        CHECK(!RoomNeedsSelfStart(State::Done, true, true));
        CHECK(!RoomNeedsSelfStart(State::NotStarted, false, true));
        CHECK(!RoomNeedsSelfStart(State::NotStarted, true, false));
        std::array<std::uint32_t, kHallRuneCount> runeStates{};
        runeStates.fill(State::Done);
        CHECK(AllRunesDone(runeStates));
        runeStates[3] = State::NotStarted;
        CHECK(!AllRunesDone(runeStates));
    }

    void TestUrokPile()
    {
        // Locked while Omokk lives; ready once he is DONE; in use during the challenge; ready again after a wipe;
        // spent once Urok is DONE (ruling 39).
        CHECK(UrokPileState(State::NotStarted, State::NotStarted, false) == PILE_LOCKED);
        CHECK(UrokPileState(State::Done, State::NotStarted, false) == PILE_READY);
        CHECK(UrokPileState(State::Done, State::InProgress, true) == PILE_IN_USE);
        CHECK(UrokPileState(State::Done, State::NotStarted, false) == PILE_READY);     // the wipe re-arms it
        CHECK(UrokPileState(State::Done, State::Done, false) == PILE_SPENT);
        CHECK(UrokPileState(State::NotStarted, State::Done, true) == PILE_SPENT);
        CHECK(UrokPileUsable(PILE_READY));
        CHECK(!UrokPileUsable(PILE_LOCKED) && !UrokPileUsable(PILE_IN_USE) && !UrokPileUsable(PILE_SPENT));
    }

    void TestSolakarEvent()
    {
        // Stock start, the note 1 fix (a FAIL ends NOT_STARTED), DONE is final.
        CHECK(SolakarEventAfterWrite(State::NotStarted, State::InProgress) == State::InProgress);
        CHECK(SolakarEventStarts(State::NotStarted, State::InProgress));
        CHECK(SolakarEventAfterWrite(State::InProgress, State::InProgress) == State::InProgress);
        CHECK(!SolakarEventStarts(State::InProgress, State::InProgress));
        CHECK(SolakarEventAfterWrite(State::InProgress, State::Fail) == State::NotStarted);
        // ... so Father Flame starts it again.
        std::uint32_t const afterFail = SolakarEventAfterWrite(State::InProgress, State::Fail);
        CHECK(SolakarEventAfterWrite(afterFail, State::InProgress) == State::InProgress);
        CHECK(SolakarEventStarts(afterFail, State::InProgress));
        CHECK(SolakarEventAfterWrite(State::InProgress, State::Done) == State::Done);
        CHECK(SolakarEventAfterWrite(State::Done, State::InProgress) == State::Done);
        CHECK(SolakarEventAfterWrite(State::Done, State::Fail) == State::Done);
    }

    void TestHardModes()
    {
        // The war horn: heroic, out of combat, before the kill; never cleared mid-fight.
        CHECK(WarHornChangeAllowed(1, true, State::NotStarted));
        CHECK(WarHornChangeAllowed(1, true, State::Fail));
        CHECK(!WarHornChangeAllowed(1, false, State::NotStarted));
        CHECK(!WarHornChangeAllowed(1, true, State::InProgress));
        CHECK(!WarHornChangeAllowed(1, true, State::Done));
        CHECK(WarHornChangeAllowed(0, false, State::NotStarted));
        CHECK(!WarHornChangeAllowed(0, true, State::InProgress));
        // The insult: refused while wave 2 is unbound; kept through wipes (only a 0 clears it).
        CHECK(!InsultChangeAllowed(1, false, State::NotStarted));
        CHECK(InsultChangeAllowed(1, true, State::NotStarted));
        CHECK(InsultChangeAllowed(1, true, State::Fail));
        CHECK(!InsultChangeAllowed(1, true, State::Done));
        CHECK(!InsultChangeAllowed(1, true, State::InProgress));
        // The General's Army: heroic, wave 2, the insult saved, Drakkisath idle.
        CHECK(GeneralsArmyChangeAllowed(1, true, true, true, State::NotStarted));
        CHECK(!GeneralsArmyChangeAllowed(1, true, true, false, State::NotStarted));
        CHECK(!GeneralsArmyChangeAllowed(1, true, false, true, State::NotStarted));
        CHECK(!GeneralsArmyChangeAllowed(1, false, true, true, State::NotStarted));
        CHECK(!GeneralsArmyChangeAllowed(1, true, true, true, State::InProgress));
        CHECK(!GeneralsArmyChangeAllowed(1, true, true, true, State::Done));
        // The per-pull flags end with the attempt (a wipe), not with a reset before the pull.
        CHECK(AttemptEnded(State::InProgress, State::NotStarted));
        CHECK(AttemptEnded(State::InProgress, State::Fail));
        CHECK(!AttemptEnded(State::NotStarted, State::NotStarted));
        CHECK(!AttemptEnded(State::InProgress, State::Done));
        CHECK(!AttemptEnded(State::Fail, State::NotStarted));
    }

    void TestFlex()
    {
        // a / b pairs: a at 5 (and "not held", 0), b from 6; the taunt swap only at 10; two loot rolls at 10.
        FlexAB constexpr dolls{ 1, 2 };
        CHECK(dolls.At(0) == 1 && dolls.At(5) == 1);
        CHECK(dolls.At(6) == 2 && dolls.At(10) == 2 && dolls.At(15) == 2);
        CHECK(!DungeonKit::Flex::TankSwapOn(9) && DungeonKit::Flex::TankSwapOn(10));
        CHECK(DungeonKit::Flex::LootRolls(9) == 1 && DungeonKit::Flex::LootRolls(10) == 2);
    }

    BrsSave RoundTrip(BrsSave const& in, std::uint32_t mask = 0)
    {
        BrsSave out;
        CHECK(ParseBrsSave(FormatBrsSave(in), out, mask));
        return out;
    }

    void TestSave()
    {
        // The header is not a prefix of the stock one, nor the stock one of it.
        CHECK(std::string(kStockSaveHeader).rfind(kSaveHeader, 0) != 0);
        CHECK(std::string(kSaveHeader).rfind(kStockSaveHeader, 0) != 0);

        // A full round trip: states, the insult, Solakar DONE; the pile is derived again.
        BrsSave s;
        s.states[BOSS_OMOKK] = State::Done;
        s.states[BOSS_WYRMTHALAK] = State::Done;
        s.states[BOSS_WAR_HORN] = State::Done;
        s.states[BOSS_SOLAKAR] = State::Done;
        s.states[BOSS_MOR_GRAYHOOF] = State::Done;
        s.states[BOSS_HALL_RUNE_2] = State::Done;
        s.nefInsulted = 1;
        s.solakarEvent = State::Done;
        s.solakarFlame = FLAME_BRAZIER;
        BrsSave r = RoundTrip(s);
        CHECK(r.states == s.states);
        CHECK(r.nefInsulted == 1);
        CHECK(r.urokPile == PILE_READY);            // Omokk DONE, Urok not
        CHECK(r.solakarEvent == State::Done);
        CHECK(r.solakarFlame == FLAME_BRAZIER);

        // Per attempt values end with a reload: in-progress fights, the pile in use, a held flame, a running event.
        s = BrsSave{};
        s.states[BOSS_OMOKK] = State::Done;
        s.states[BOSS_UROK] = State::InProgress;
        s.states[BOSS_DRAKKISATH] = State::Fail;
        s.urokPile = PILE_IN_USE;
        s.solakarEvent = State::InProgress;
        s.solakarFlame = FLAME_HOLDER;
        s.nefInsulted = 1;
        r = RoundTrip(s);
        CHECK(r.states[BOSS_UROK] == State::NotStarted);
        CHECK(r.states[BOSS_DRAKKISATH] == State::NotStarted);
        CHECK(r.urokPile == PILE_READY);            // the pile re-arms after a wipe
        CHECK(r.solakarEvent == State::NotStarted); // Solakar restarts
        CHECK(r.solakarFlame == FLAME_NONE);
        CHECK(r.nefInsulted == 1);                  // the insult persists through a wipe and a reload

        // Solakar's boss slot persists (stock never saved 23) and carries the event.
        s = BrsSave{};
        s.states[BOSS_SOLAKAR] = State::Done;
        r = RoundTrip(s);
        CHECK(r.states[BOSS_SOLAKAR] == State::Done && r.solakarEvent == State::Done);

        // The Vaelastrasz slot never holds a boss state.
        s = BrsSave{};
        s.states[BOSS_VAELASTRASZ_SLOT] = State::Done;
        r = RoundTrip(s);
        CHECK(r.states[BOSS_VAELASTRASZ_SLOT] == State::NotStarted);

        // A short save (an older build with fewer fields) leaves the rest at its defaults.
        BrsSave shortSave;
        CHECK(ParseBrsSave("B R W 3 0 0", shortSave));
        CHECK(shortSave.states[BOSS_OMOKK] == State::Done && shortSave.urokPile == PILE_READY);
        CHECK(shortSave.nefInsulted == 0);

        // Garbage is ignored.
        BrsSave junk;
        CHECK(!ParseBrsSave("", junk));
        CHECK(!ParseBrsSave("X Y Z 1 2 3", junk));
    }

    void TestStockSave()
    {
        // instance_blackrock_spire at 8eb009fdf: "B R S " + 23 boss states (InstanceScript's own format).
        std::string stock = "B R S ";
        for (std::uint32_t i = 0; i < kStockEncounterCount; ++i)
        {
            std::uint32_t v = State::NotStarted;
            if (i == BOSS_OMOKK || i == BOSS_VOONE || i == BOSS_DRAGONSPIRE_ROOM || IsHallRuneSlot(i))
                v = State::Done;
            if (i == BOSS_EMBERSEER)
                v = State::InProgress;
            stock += std::to_string(v) + " ";
        }
        BrsSave r;
        CHECK(ParseBrsSave(stock, r));
        CHECK(r.states[BOSS_OMOKK] == State::Done && r.states[BOSS_VOONE] == State::Done);
        CHECK(r.states[BOSS_DRAGONSPIRE_ROOM] == State::Done && r.states[BOSS_HALL_RUNE_7] == State::Done);
        CHECK(r.states[BOSS_EMBERSEER] == State::NotStarted);      // sanitized
        CHECK(r.states[BOSS_SOLAKAR] == State::NotStarted);
        CHECK(r.urokPile == PILE_READY);
        CHECK(r.nefInsulted == 0);

        // The completed-encounter mask fills in the slots stock never wrote: Vosh'gajin (bit 1), Smolderweb (3) and
        // Gizrul (6) were SmartAI, Solakar (bit 10) had no saved slot; Rend is bit 11 on slot 10.
        std::uint32_t const mask = (1u << 1) | (1u << 3) | (1u << 6) | (1u << 10) | (1u << 11) | (1u << 4);
        CHECK(ParseBrsSave(stock, r, mask));
        CHECK(r.states[BOSS_VOSHGAJIN] == State::Done && r.states[BOSS_SMOLDERWEB] == State::Done);
        CHECK(r.states[BOSS_GIZRUL] == State::Done && r.states[BOSS_SOLAKAR] == State::Done);
        CHECK(r.states[BOSS_REND] == State::Done && r.states[BOSS_GYTH] == State::NotStarted);
        CHECK(r.solakarEvent == State::Done);
        CHECK(r.urokPile == PILE_SPENT);
        // The mask is not applied to a "B R W" save (it carries its own states).
        BrsSave own;
        CHECK(ParseBrsSave(FormatBrsSave(BrsSave{}), own, mask));
        CHECK(own.states[BOSS_VOSHGAJIN] == State::NotStarted);

        // A stock save with a short tail still reads.
        CHECK(ParseBrsSave("B R S 3 3", r));
        CHECK(r.states[BOSS_VOSHGAJIN] == State::Done && r.states[BOSS_VOONE] == State::NotStarted);

        // The encounter bits are the DBC's (267-280, verified): 14 bits, every encounter slot once.
        std::set<std::uint32_t> bosses;
        for (auto const& [bit, boss] : kEncounterBits)
        {
            CHECK(bit < 14);
            CHECK(IsEncounterSlot(boss));
            bosses.insert(boss);
        }
        CHECK(bosses.size() == 14);
        CHECK(!bosses.count(BOSS_VALTHALAK));
    }

    // K-m1 / R-1-B m3: slots nobody wrote settle to NOT_STARTED; written ones stay.
    void TestSlotSettle()
    {
        CHECK(SettledSlotState(State::ToBeDecided) == State::NotStarted);
        CHECK(SettledSlotState(State::NotStarted) == State::NotStarted);
        CHECK(SettledSlotState(State::InProgress) == State::InProgress);
        CHECK(SettledSlotState(State::Done) == State::Done);
        CHECK(SettledSlotState(State::Fail) == State::Fail);
        CHECK(SettledSlotState(State::Special) == State::Special);
    }

    // B7's restart soft-lock: a dead Halycon with her pair unfinished and no living Gizrul comes back.
    void TestHalyconRespawn()
    {
        CHECK(HalyconNeedsRespawn(State::NotStarted, false, false));    // the restart after she fell first
        CHECK(HalyconNeedsRespawn(State::InProgress, false, false));
        CHECK(!HalyconNeedsRespawn(State::Done, false, false));         // the pair is done
        CHECK(!HalyconNeedsRespawn(State::InProgress, false, true));    // Gizrul still fights: the attempt goes on
        CHECK(!HalyconNeedsRespawn(State::NotStarted, true, false));    // alive: she summons a new Gizrul at the pull
        CHECK(kHalyconRespawnDelayMs > 0);
    }
}

int main()
{
    TestBossStates();
    TestData();
    TestEntries();
    TestWaveSwitch();
    TestSlices();
    TestArenas();
    TestDragonspireHall();
    TestUrokPile();
    TestSolakarEvent();
    TestHardModes();
    TestFlex();
    TestSave();
    TestStockSave();
    TestSlotSettle();
    TestHalyconRespawn();

    return Report("blackrock_spire_test");
}
