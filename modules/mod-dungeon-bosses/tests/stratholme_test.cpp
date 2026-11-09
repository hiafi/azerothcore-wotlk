// Host tests for the Stratholme skeleton (WP-S0): StratholmeRework.h (boss states with Jarien and Sothos on their stock
// slots, data ids, entries, the wave switch, slices, measured points, arenas, the ziggurat softlock fix, the slaughter
// event without the Mindless stage, the Ultimatum and Grand Lie rules, the save string and its stock "STR" reader).
// DB positions (spawns, gates) are exact; the rest is the NAVMESH-REPORT's.
#include "StratholmeRework.h"
#include "check.h"
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace StratholmeRework;
namespace State = DungeonKit::State;

namespace
{
    bool In(Arena const& arena, Point4 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    // The fighting bosses (not the event or hard mode slots) and where each stands at the pull. Ramstein is summoned
    // in his pen and walks in to his stop.
    struct BossSpot
    {
        std::uint32_t boss;
        Point3 at;
    };

    std::vector<BossSpot> const kSpots{
        { BOSS_UNFORGIVEN, kUnforgivenSpawn.P3() }, { BOSS_FORRESTEN, kForrestenSpawn.P3() },
        { BOSS_TIMMY, kTimmySpawn.P3() }, { BOSS_WILLEY, kWilleySpawn.P3() }, { BOSS_MALOR, kMalorSpawn.P3() },
        { BOSS_GALFORD, kGalfordSpawn.P3() }, { BOSS_BALNAZZAR, kDathrohanSpawn.P3() },
        { BOSS_BARONESS, kBaronessSpawn.P3() }, { BOSS_NERUBENKAN, kNerubenkanSpawn.P3() },
        { BOSS_MALEKI, kMalekiSpawn.P3() }, { BOSS_BARTHILAS, kBarthilasSpawn.P3() },
        { BOSS_RAMSTEIN, kRamsteinStop }, { BOSS_BARON, kBaronSpawn.P3() } };

    void TestBossStates()
    {
        CHECK(kBossCount == 17);
        // The stock event bosses' BossAI slots (stratholme.h DATA_JARIEN 2, DATA_SOTHOS 3).
        CHECK(BOSS_JARIEN == 2);
        CHECK(BOSS_SOTHOS == 3);
        CHECK(IsStockEventBoss(2) && IsStockEventBoss(3));
        std::set<std::uint32_t> const ids{ BOSS_UNFORGIVEN, BOSS_FORRESTEN, BOSS_JARIEN, BOSS_SOTHOS, BOSS_TIMMY,
            BOSS_WILLEY, BOSS_MALOR, BOSS_GALFORD, BOSS_BALNAZZAR, BOSS_BARONESS, BOSS_NERUBENKAN, BOSS_MALEKI,
            BOSS_BARTHILAS, BOSS_RAMSTEIN, BOSS_BARON, BOSS_GRAND_LIE, BOSS_ULTIMATUM };
        CHECK(ids.size() == kBossCount);
        CHECK(*ids.rbegin() == kBossCount - 1);
        for (char const* name : kBossNames)
            CHECK(name && *name);
        CHECK(IsHardModeSlot(BOSS_GRAND_LIE) && IsHardModeSlot(BOSS_ULTIMATUM));
        CHECK(!IsHardModeSlot(BOSS_BARON));

        // No boss entry maps to the event slots; both Dathrohan and Balnazzar map to one encounter.
        for (std::uint32_t entry : { 10516u, 10558u, 10808u, 11032u, 10997u, 10811u, 10812u, 10813u, 10435u, 10436u,
            10437u, 10438u, 10439u, 10440u })
        {
            CHECK(IsStratBossEntry(entry));
            CHECK(!IsStockEventBoss(*BossOfEntry(entry)));
            CHECK(!IsHardModeSlot(*BossOfEntry(entry)));
        }
        CHECK(*BossOfEntry(NPC_DATHROHAN) == BOSS_BALNAZZAR);
        CHECK(*BossOfEntry(NPC_BALNAZZAR) == BOSS_BALNAZZAR);
        CHECK(!BossOfEntry(NPC_JARIEN) && !BossOfEntry(NPC_SOTHOS) && !BossOfEntry(NPC_YSIDA));
        CHECK(!BossOfEntry(NPC_MINDLESS_UNDEAD) && !BossOfEntry(NPC_BLACK_GUARD));
    }

    void TestDataIds()
    {
        // The stock ids the stock SmartAI and mod-dungeon-clear use keep their values.
        CHECK(DATA_BARON_RUN == 0);
        CHECK(DATA_ZIGGURAT1 == 1 && DATA_ZIGGURAT2 == 2 && DATA_ZIGGURAT3 == 3);
        CHECK(DATA_BARON_FIGHT == 4);
        CHECK(DATA_MALLOW == 5);
        CHECK(DATA_BARTHILAS_RUN == 6);
        CHECK(DATA_SCARLET_THREAD_LOOTED == 7);
        std::set<std::uint32_t> const data{ DATA_BARON_RUN, DATA_ZIGGURAT1, DATA_ZIGGURAT2, DATA_ZIGGURAT3,
            DATA_BARON_FIGHT, DATA_MALLOW, DATA_BARTHILAS_RUN, DATA_SCARLET_THREAD_LOOTED, DATA_ULTIMATUM,
            DATA_GRAND_LIE, DATA_SLAUGHTER_STAGE, DATA_BARON_RUN_MINUTES, DATA_ZIGGURAT_PENDING, DATA_YSIDA_FATE };
        CHECK(data.size() == 14);
        std::set<std::uint32_t> const guids{ DATA_UNFORGIVEN_GUID, DATA_FORRESTEN_GUID, DATA_TIMMY_GUID,
            DATA_WILLEY_GUID, DATA_MALOR_GUID, DATA_GALFORD_GUID, DATA_DATHROHAN_GUID, DATA_BARONESS_GUID,
            DATA_NERUBENKAN_GUID, DATA_MALEKI_GUID, DATA_BARTHILAS_GUID, DATA_BARON_GUID, DATA_YSIDA_GUID,
            DATA_YSIDA_CAGE_GUID, DATA_EXIT_GATE_GUID, DATA_RAMSTEIN_GUID };
        CHECK(guids.size() == 16);
        for (std::uint32_t g : guids)
            CHECK(!data.count(g));
    }

    void TestWaveSwitch()
    {
        CHECK(kWave2Bound);        // wave 2 bound
        std::set<std::uint32_t> const wave2{ BOSS_UNFORGIVEN, BOSS_FORRESTEN, BOSS_TIMMY, BOSS_WILLEY, BOSS_MALOR,
            BOSS_GALFORD, BOSS_BALNAZZAR, BOSS_GRAND_LIE };
        for (std::uint32_t id = 0; id < kBossCount; ++id)
        {
            CHECK(IsWave2Boss(id) == (wave2.count(id) != 0));
            if (IsStockEventBoss(id))
            {
                CHECK(!IsReworkBound(id, false) && !IsReworkBound(id, true));
                continue;
            }
            CHECK(IsReworkBound(id, true));
            CHECK(IsReworkBound(id, false) == !wave2.count(id));
        }
        CHECK(!IsReworkBound(kBossCount, true));
    }

    void TestIds()
    {
        // The spell slices tile the reservation in order, with no gap.
        CHECK(kSpellSlices.front().first == kSpellsReservation.first);
        CHECK(kSpellSlices.back().last == kSpellsReservation.last);
        for (std::size_t i = 1; i < kSpellSlices.size(); ++i)
            CHECK(kSpellSlices[i].first == kSpellSlices[i - 1].last + 1);
        // S14 and S15 split the handoff's 206705-206734 between them.
        CHECK(kSpellsBaron.first == 206705 && kSpellsUltimatum.last == 206734);
        CHECK(kSpellsUltimatum.first == kSpellsBaron.last + 1);

        // The boss-kit creature ids: wave 1 below every wave 2 id (the heroic mint order).
        std::vector<std::uint32_t> const wave1{ NPC_ST_GRAIN_PILE, NPC_ST_WARD, NPC_ST_WEB_COCOON, NPC_ST_WEB_PATCH,
            NPC_ST_ICE_TOMB, NPC_ST_EYE, NPC_ST_HALF_DIGESTED_CORPSE, NPC_ST_GUT_PUDDLE, NPC_ST_ROT,
            NPC_ST_YSIDA_RISEN };
        std::vector<std::uint32_t> const wave2{ NPC_ST_SPECTRAL_FOOTMAN, NPC_ST_HOUSE_FIRE, NPC_ST_GUTTER_RAT,
            NPC_ST_HEARTH, NPC_ST_PLAYMATE, NPC_ST_MEDALLION, NPC_ST_HOLY_FIRE_PUDDLE, NPC_ST_PYRE_WALL,
            NPC_ST_INFERNAL, NPC_ST_SWARM };
        for (std::uint32_t id : wave1)
            CHECK(kCreaturesWave1.Contains(id) && kCreaturesReservation.Contains(id));
        for (std::uint32_t id : wave2)
            CHECK(kCreaturesWave2.Contains(id) && kCreaturesReservation.Contains(id));
        CHECK(kCreaturesWave1.last < kCreaturesWave2.first);
        CHECK(kCreaturesWave1.first == kCreaturesReservation.first);
        CHECK(kCreaturesWave2.last == kCreaturesReservation.last);
        for (std::uint32_t id : { GO_ST_MERCY, GO_ST_ZEAL, GO_ST_CANNONBALL, GO_ST_LETTER_OF_PROOF,
            GO_ST_SCARLET_STANDARD, GO_ST_MEDALLION_LIGHT, GO_ST_BLESSED_CRATE, GO_ST_BONE_PILE })
            CHECK(kGameObjectsReservation.Contains(id));
        for (std::uint32_t id : { ITEM_ST_LETTER_OF_PROOF, ITEM_ST_SCARLET_STANDARD, ITEM_ST_BLESSED_HOLY_WATER,
            ITEM_ST_RELIC_OF_THE_MEDALLION })
            CHECK(kRelicItems.Contains(id));
    }

    void TestArenas()
    {
        // Every fighting boss stands in his own arena at the pull, and in no other boss's.
        for (BossSpot const& s : kSpots)
        {
            CHECK(In(ArenaFor(s.boss), s.at));
            for (BossSpot const& other : kSpots)
                if (other.boss != s.boss)
                    CHECK(!In(ArenaFor(other.boss), s.at));
        }
        // The event slots have no arena; the hard mode slots share their boss's.
        CHECK(ArenaFor(BOSS_JARIEN).Empty() && ArenaFor(BOSS_SOTHOS).Empty());
        CHECK(In(ArenaFor(BOSS_ULTIMATUM), kBaronSpawn) && In(ArenaFor(BOSS_GRAND_LIE), kDathrohanSpawn));
        // Ramstein is summoned in his pen, outside the square's circle, and walks in.
        CHECK(!In(RamsteinArena(), kRamsteinSummon));
        // The Baron's room holds Ysida, her cage and the six Raise Dead points; his door is its edge.
        CHECK(In(BaronArena(), kYsidaSpawn));
        CHECK(In(BaronArena(), kYsidaCage));
        for (Point3 const& p : kRaiseDeadPoints)
            CHECK(DungeonKit::InsideFrame(kBaronRoom, p.XY()));
        // Barthilas: the ward anchor and both spawn wards are in his yard.
        CHECK(In(BarthilasArena(), kBarthilasWardAnchor));
        for (Point3 const& p : kBarthilasSpawnWards)
            CHECK(In(BarthilasArena(), p));
        // Maleki's eye centers are in his arena, 11-13 yd from him.
        for (Point3 const& p : kMalekiEyeCenters)
        {
            CHECK(In(MalekiArena(), p));
            float const d = DungeonKit::Distance(p.XY(), kMalekiSpawn.XY());
            CHECK(d >= 10.5f && d <= 13.5f);
        }
        // The Service Entrance Gate and the Gauntlet Gate are in no arena.
        for (BossSpot const& s : kSpots)
        {
            CHECK(!In(ArenaFor(s.boss), kServiceEntranceGate));
            CHECK(!In(ArenaFor(s.boss), kGauntletGate));
        }
        // Willey's ranks stand inside his hall frame, at its far end.
        for (Point3 const& p : kWilleyRank3)
            CHECK(In(WilleyArena(), Point3{ p.x, p.y, 125.3f }));
        // The Unforgiven's lanes meet on the plaza; the fire spots lie in it.
        for (Vec2 const& f : kUnforgivenFireSpots)
            CHECK(UnforgivenArena().Contains(f, 132.f));
    }

    void TestZiggurats()
    {
        // Stock order: the boss dies (1), then the crystal breaks (2).
        Ziggurat z;
        z = ZigguratAfterWrite(z, 1);
        CHECK(z.state == 1 && !z.pending);
        z = ZigguratAfterWrite(z, 2);
        CHECK(z.state == 2 && !z.pending);
        // Repeats change nothing.
        CHECK(ZigguratAfterWrite(z, 1) == z);
        CHECK(ZigguratAfterWrite(z, 2) == z);

        // The softlock (ST note 1): the crystal breaks first. Stock lost it; now it waits for the boss.
        Ziggurat s;
        s = ZigguratAfterWrite(s, 2);
        CHECK(s.state == 0 && s.pending);
        s = ZigguratAfterWrite(s, 2);
        CHECK(s.state == 0 && s.pending);
        s = ZigguratAfterWrite(s, 1);
        CHECK(s.state == 2 && !s.pending);

        // Junk writes are ignored.
        Ziggurat j;
        CHECK(ZigguratAfterWrite(j, 0) == j);
        CHECK(ZigguratAfterWrite(j, 3) == j);
        j.state = 2;
        CHECK(ZigguratAfterWrite(j, 3) == j);

        std::array<Ziggurat, kZigguratCount> all{};
        CHECK(!AllZigguratsBroken(all));
        all[0].state = all[1].state = 2;
        all[2].state = 1;
        all[2].pending = true;      // cannot happen (1 + pending is 2), but the test is on the state only
        CHECK(!AllZigguratsBroken(all));
        all[2] = ZigguratAfterWrite(Ziggurat{ 1, false }, 2);
        CHECK(AllZigguratsBroken(all));

        CHECK(*ZigguratOfBoss(BOSS_BARONESS) == 0);
        CHECK(*ZigguratOfBoss(BOSS_NERUBENKAN) == 1);
        CHECK(*ZigguratOfBoss(BOSS_MALEKI) == 2);
        CHECK(!ZigguratOfBoss(BOSS_BARON));
        CHECK(ZigguratPendingMask(std::array<Ziggurat, 3>{ { { 0, true }, { 2, false }, { 0, true } } }) == 5u);
    }

    void TestSlaughter()
    {
        // ST 3395-3400: Ramstein's death goes straight to the Black Guards.
        CHECK(NextSlaughterStage(SLAUGHTER_ABOMINATIONS) == SLAUGHTER_RAMSTEIN);
        CHECK(NextSlaughterStage(SLAUGHTER_RAMSTEIN) == SLAUGHTER_BLACK_GUARD);
        CHECK(NextSlaughterStage(SLAUGHTER_BLACK_GUARD) == SLAUGHTER_COMPLETE);
        CHECK(NextSlaughterStage(SLAUGHTER_COMPLETE) == SLAUGHTER_COMPLETE);
        // A stock save in the retired Mindless stage moves on to the Black Guards; junk is complete.
        CHECK(SanitizeSlaughterStage(SLAUGHTER_MINDLESS_UNDEAD) == SLAUGHTER_BLACK_GUARD);
        CHECK(NextSlaughterStage(SLAUGHTER_MINDLESS_UNDEAD) == SLAUGHTER_COMPLETE);
        CHECK(SanitizeSlaughterStage(9) == SLAUGHTER_COMPLETE);
        // The side gate: from the Black Guards on (stock: from the Mindless stage).
        CHECK(!SideGateOpen(SLAUGHTER_ABOMINATIONS) && !SideGateOpen(SLAUGHTER_RAMSTEIN));
        CHECK(SideGateOpen(SLAUGHTER_MINDLESS_UNDEAD) && SideGateOpen(SLAUGHTER_BLACK_GUARD));
        CHECK(SideGateOpen(SLAUGHTER_COMPLETE));
        // The Baron's door: open once the guards are dead, closed while he fights.
        CHECK(!BaronDoorOpen(SLAUGHTER_BLACK_GUARD, false));
        CHECK(BaronDoorOpen(SLAUGHTER_COMPLETE, false));
        CHECK(!BaronDoorOpen(SLAUGHTER_COMPLETE, true));
    }

    void TestHardModes()
    {
        // The Ultimatum: heroic, the clock running, the Baron neither fighting nor dead.
        CHECK(UltimatumChangeAllowed(1, true, 45, State::NotStarted));
        CHECK(UltimatumChangeAllowed(1, true, 1, State::NotStarted));
        CHECK(!UltimatumChangeAllowed(1, false, 45, State::NotStarted));
        CHECK(!UltimatumChangeAllowed(1, true, 0, State::NotStarted));
        CHECK(!UltimatumChangeAllowed(1, true, 30, State::InProgress));
        CHECK(!UltimatumChangeAllowed(1, true, 30, State::Done));
        CHECK(UltimatumChangeAllowed(0, false, 0, State::NotStarted));
        CHECK(!UltimatumChangeAllowed(0, true, 30, State::InProgress));
        // A loading state (TO_BE_DECIDED) is not a fight.
        CHECK(UltimatumChangeAllowed(1, true, 30, State::ToBeDecided));

        // The Grand Lie: heroic, wave 2 bound, Balnazzar neither fighting nor dead.
        CHECK(GrandLieChangeAllowed(1, true, true, State::NotStarted));
        CHECK(!GrandLieChangeAllowed(1, true, false, State::NotStarted));     // wave 1: off
        CHECK(!GrandLieChangeAllowed(1, false, true, State::NotStarted));
        CHECK(!GrandLieChangeAllowed(1, true, true, State::InProgress));
        CHECK(!GrandLieChangeAllowed(1, true, true, State::Done));
        CHECK(GrandLieChangeAllowed(0, true, false, State::NotStarted));
        CHECK(!GrandLieChangeAllowed(0, true, true, State::InProgress));

        // The exit gate opens on the Baron's death only when Ysida is dead (ST note 9).
        CHECK(ExitGateOpensOnBaronDeath(false));
        CHECK(!ExitGateOpensOnBaronDeath(true));
        // Her saved fate decides first (R-1-B B-2): a fallen or executed Ysida opens it even if a respawned creature
        // stands alive.
        CHECK(!ExitGateOpensOnBaronDeath(true, YSIDA_ALIVE));
        CHECK(ExitGateOpensOnBaronDeath(true, YSIDA_FALLEN));
        CHECK(ExitGateOpensOnBaronDeath(true, YSIDA_EXECUTED));
        CHECK(ExitGateOpensOnBaronDeath(false, YSIDA_ALIVE));
        CHECK(kBaronRunMinutes == 45);
    }

    void TestYsidaFate()
    {
        // R-1-B B-2 / F-1 ruling: the instance keeps her fate; the hard mode may write FALLEN and ALIVE only.
        CHECK(YsidaFateChangeAllowed(YSIDA_ALIVE, YSIDA_FALLEN, State::InProgress));
        CHECK(YsidaFateChangeAllowed(YSIDA_FALLEN, YSIDA_ALIVE, State::NotStarted));     // a wipe restores her
        CHECK(YsidaFateChangeAllowed(YSIDA_FALLEN, YSIDA_ALIVE, State::InProgress));
        CHECK(!YsidaFateChangeAllowed(YSIDA_ALIVE, YSIDA_EXECUTED, State::NotStarted));  // the instance's alone
        CHECK(!YsidaFateChangeAllowed(YSIDA_EXECUTED, YSIDA_ALIVE, State::NotStarted));  // final
        CHECK(!YsidaFateChangeAllowed(YSIDA_EXECUTED, YSIDA_FALLEN, State::InProgress));
        CHECK(!YsidaFateChangeAllowed(YSIDA_FALLEN, YSIDA_ALIVE, State::Done));          // settled with his death
        CHECK(!YsidaFateChangeAllowed(YSIDA_ALIVE, 7, State::NotStarted));

        CHECK(SanitizeYsidaFate(YSIDA_FALLEN, State::NotStarted) == YSIDA_ALIVE);       // a restart mid-attempt
        CHECK(SanitizeYsidaFate(YSIDA_FALLEN, State::Done) == YSIDA_FALLEN);
        CHECK(SanitizeYsidaFate(YSIDA_EXECUTED, State::NotStarted) == YSIDA_EXECUTED);
        CHECK(SanitizeYsidaFate(9, State::NotStarted) == YSIDA_ALIVE);

        // The execution a restart interrupted is still owed (the clock out, not executed, the Baron alive).
        CHECK(ExecutionOwed(1, 0, YSIDA_ALIVE, State::NotStarted));
        CHECK(ExecutionOwed(1, 0, YSIDA_FALLEN, State::NotStarted));
        CHECK(!ExecutionOwed(1, 0, YSIDA_EXECUTED, State::NotStarted));
        CHECK(!ExecutionOwed(1, 5, YSIDA_ALIVE, State::NotStarted));
        CHECK(!ExecutionOwed(0, 0, YSIDA_ALIVE, State::NotStarted));
        CHECK(!ExecutionOwed(1, 0, YSIDA_ALIVE, State::Done));

        CHECK(std::string(YsidaFateName(YSIDA_ALIVE)) == "alive");
        CHECK(std::string(YsidaFateName(YSIDA_FALLEN)) == "fallen");
        CHECK(std::string(YsidaFateName(YSIDA_EXECUTED)) == "executed");

        // Saved and read back; an older 14-extra save reads ALIVE.
        StratSave s;
        s.baronRunProgress = 1;
        s.ysidaFate = YSIDA_EXECUTED;
        StratSave back;
        CHECK(ParseStratSave(FormatStratSave(s), back));
        CHECK(back.ysidaFate == YSIDA_EXECUTED);
        std::string older = FormatStratSave(s);
        older.erase(older.rfind(' '));
        CHECK(ParseStratSave(older, back));
        CHECK(back.ysidaFate == YSIDA_ALIVE);
        s.ysidaFate = YSIDA_FALLEN;
        CHECK(ParseStratSave(FormatStratSave(s), back));
        CHECK(back.ysidaFate == YSIDA_ALIVE);
        s.states[BOSS_BARON] = State::Done;
        CHECK(ParseStratSave(FormatStratSave(s), back));
        CHECK(back.ysidaFate == YSIDA_FALLEN);
    }

    StratSave SampleSave()
    {
        StratSave s;
        s.states[BOSS_BARTHILAS] = State::Done;
        s.states[BOSS_JARIEN] = State::Done;
        s.states[BOSS_BARONESS] = State::Done;
        s.baronRunProgress = 1;
        s.baronRunMinutes = 31;
        s.ziggurats[0] = { 2, false };
        s.ziggurats[1] = { 0, true };
        s.ziggurats[2] = { 1, false };
        s.slaughter = SLAUGHTER_RAMSTEIN;
        s.postboxes = 2;
        s.barthilasRun = 3;
        s.scarletThreads = 5;
        s.gateTrapEnd = { { 1794000000u, 1794000100u } };
        s.ultimatum = 1;
        s.grandLie = 0;
        return s;
    }

    void TestSaveRoundTrip()
    {
        // The header must not be a prefix of the stock "S T R", or a stock save would never reach the legacy reader.
        CHECK(std::string(kSaveHeader).rfind("ST", 0) != 0);
        StratSave const s = SampleSave();
        std::string const text = FormatStratSave(s);
        CHECK(text.rfind("S R ", 0) == 0);
        StratSave back;
        CHECK(ParseStratSave(text, back));
        CHECK(back.states == s.states);
        CHECK(back.baronRunProgress == 1 && back.baronRunMinutes == 31);
        CHECK(back.ziggurats[0] == (Ziggurat{ 2, false }));
        CHECK(back.ziggurats[1] == (Ziggurat{ 0, true }));
        CHECK(back.ziggurats[2] == (Ziggurat{ 1, false }));
        CHECK(back.slaughter == SLAUGHTER_RAMSTEIN && back.postboxes == 2 && back.barthilasRun == 3);
        CHECK(back.scarletThreads == 5);
        CHECK(back.gateTrapEnd[0] == 1794000000u && back.gateTrapEnd[1] == 1794000100u);
        CHECK(back.ultimatum == 1 && back.grandLie == 0);
        // An own save never takes the encounter mask.
        StratSave masked;
        CHECK(ParseStratSave(text, masked, 0x1FFF));
        CHECK(masked.states[BOSS_BARON] == State::NotStarted);

        // Loaded states are sanitized (IN_PROGRESS back to NOT_STARTED), flags clamped.
        StratSave hot = s;
        hot.states[BOSS_BARON] = State::InProgress;
        hot.ultimatum = 7;
        hot.ziggurats[2].state = 9;
        hot.slaughter = SLAUGHTER_MINDLESS_UNDEAD;
        hot.baronRunMinutes = 99;
        StratSave cooled;
        CHECK(ParseStratSave(FormatStratSave(hot), cooled));
        CHECK(cooled.states[BOSS_BARON] == State::NotStarted);
        CHECK(cooled.ultimatum == 1);
        CHECK(cooled.ziggurats[2].state == 2);
        CHECK(cooled.slaughter == SLAUGHTER_BLACK_GUARD);
        CHECK(cooled.baronRunMinutes == kBaronRunMinutes);

        // No clock, no Ultimatum; a dead Baron or Balnazzar has no lit flag.
        StratSave noClock = s;
        noClock.baronRunMinutes = 0;
        StratSave out;
        CHECK(ParseStratSave(FormatStratSave(noClock), out));
        CHECK(out.ultimatum == 0);
        StratSave dead = s;
        dead.states[BOSS_BARON] = State::Done;
        dead.states[BOSS_BALNAZZAR] = State::Done;
        dead.grandLie = 1;
        CHECK(ParseStratSave(FormatStratSave(dead), out));
        CHECK(out.ultimatum == 0 && out.grandLie == 0);
        // R-1-KIT F3: the clock ends with the Baron (s has 31 minutes left).
        CHECK(out.baronRunMinutes == 0 && out.baronRunProgress == 1);

        // A short tail (an older build of this script) keeps the defaults.
        CHECK(ParseStratSave("S R 3 0 0", out));
        CHECK(out.states[0] == State::Done && out.states[3] == State::NotStarted && out.ultimatum == 0);

        // Junk is ignored.
        CHECK(!ParseStratSave("", out));
        CHECK(!ParseStratSave("X Y 1 2 3", out));
        CHECK(!ParseStratSave("S R", out));
    }

    void TestStockSave()
    {
        // The stock save (9ce0f3dcc WriteSaveDataMore): "S T R " then 8 integers, the thread mask and two trap ends.
        std::string const full = "S T R 1 22 2 1 2 1 3 0 9 1794000000 0";
        StratSave s;
        CHECK(ParseStratSave(full, s, 0));
        CHECK(s.baronRunProgress == 1 && s.baronRunMinutes == 22);
        CHECK(s.ziggurats[0].state == 2 && s.ziggurats[1].state == 1 && s.ziggurats[2].state == 2);
        CHECK(s.slaughter == SLAUGHTER_RAMSTEIN);
        CHECK(s.postboxes == 3 && s.barthilasRun == 0);
        CHECK(s.scarletThreads == 9);
        CHECK(s.gateTrapEnd[0] == 1794000000u && s.gateTrapEnd[1] == 0);
        // A ziggurat at 1 or 2 is its boss dead; the slaughter at Ramstein is not his death yet.
        CHECK(s.states[BOSS_BARONESS] == State::Done);
        CHECK(s.states[BOSS_NERUBENKAN] == State::Done);
        CHECK(s.states[BOSS_MALEKI] == State::Done);
        CHECK(s.states[BOSS_RAMSTEIN] == State::NotStarted);
        CHECK(s.ultimatum == 0 && s.grandLie == 0);
        for (Ziggurat const& z : s.ziggurats)
            CHECK(!z.pending);

        // The completed-encounter mask fills in the bosses it records (bit 10 Barthilas, 12 the Baron, 6 Balnazzar).
        StratSave masked;
        CHECK(ParseStratSave(full, masked, (1u << 10) | (1u << 12) | (1u << 6)));
        CHECK(masked.states[BOSS_BARTHILAS] == State::Done);
        CHECK(masked.states[BOSS_BARON] == State::Done);
        CHECK(masked.baronRunMinutes == 0);     // stock kept 22 minutes after his kill (R-1-KIT F3)
        CHECK(s.ysidaFate == YSIDA_ALIVE);
        CHECK(masked.states[BOSS_BALNAZZAR] == State::Done);
        CHECK(masked.states[BOSS_UNFORGIVEN] == State::NotStarted);
        CHECK(masked.states[BOSS_JARIEN] == State::NotStarted);

        // The older layouts: 8 integers only; 8 + the thread mask; 8 + the two trap ends.
        StratSave eight;
        CHECK(ParseStratSave("S T R 0 0 0 0 0 0 0 0", eight));
        CHECK(eight.scarletThreads == 0 && eight.gateTrapEnd[0] == 0);
        StratSave nine;
        CHECK(ParseStratSave("S T R 0 0 0 0 0 0 0 0 6", nine));
        CHECK(nine.scarletThreads == 6 && nine.gateTrapEnd[0] == 0);
        StratSave ten;
        CHECK(ParseStratSave("S T R 0 0 0 0 0 0 0 0 1794000000 1794000500", ten));
        CHECK(ten.scarletThreads == 0);
        CHECK(ten.gateTrapEnd[0] == 1794000000u && ten.gateTrapEnd[1] == 1794000500u);
        // A thread field out of range is not a mask (stock: ignored).
        StratSave badMask;
        CHECK(ParseStratSave("S T R 0 0 0 0 0 0 0 0 99", badMask));
        CHECK(badMask.scarletThreads == 0);

        // The retired Mindless stage loads as the Black Guards, and records Ramstein dead.
        StratSave mindless;
        CHECK(ParseStratSave("S T R 1 10 2 2 2 2 0 0", mindless));
        CHECK(mindless.slaughter == SLAUGHTER_BLACK_GUARD);
        CHECK(mindless.states[BOSS_RAMSTEIN] == State::Done);

        // Too short a stock save is ignored.
        StratSave shortStock;
        CHECK(!ParseStratSave("S T R 1 10 2", shortStock));

        // A stock save round-trips into this script's own string.
        StratSave again;
        CHECK(ParseStratSave(FormatStratSave(s), again));
        CHECK(again.states == s.states && again.ziggurats[1].state == 1 && again.baronRunMinutes == 22);
    }
}

int main()
{
    TestBossStates();
    TestDataIds();
    TestWaveSwitch();
    TestIds();
    TestArenas();
    TestZiggurats();
    TestSlaughter();
    TestHardModes();
    TestYsidaFate();
    TestSaveRoundTrip();
    TestStockSave();

    return Report("stratholme_test");
}
