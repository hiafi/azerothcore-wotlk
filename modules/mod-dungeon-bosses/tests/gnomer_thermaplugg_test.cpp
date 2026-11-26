// Host tests for ThermapluggLogic.h (D6, Mekgineer Thermaplugg): the slice and the spell ids, the faces' types (ruling
// 64) and the plate ranks (SP 1704), the bomb entries (never the gear's 301100, s7 #40 A), every mode's numbers (the
// Build spec, and the hard mode at or above heroic on every value, ruling 53), the room (plates 25 yd out in line with
// each face, s7 #30 A; the bomb starts at the alcove mouths and the 8 s walk at 4.6 yd/s, s7 #31 B), the beat clock
// (RB-17), the picks, the blast reach, The Big One's split, the packages' thresholds and factors, the drill tags, and
// the boss file's registrations (the adds' scripts, the hard mode registry).
#include "ThermapluggLogic.h"
#include "check.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <string>

using namespace GnomereganRework;
using namespace GnomerThermaplugg;

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

    float BearingDeg(Vec2 from, Vec2 to)
    {
        return DungeonKit::BearingTo(from, to) * 180.f / 3.14159265f;
    }

    float AngleGap(float a, float b)
    {
        float d = std::fabs(a - b);
        while (d > 360.f)
            d -= 360.f;
        return std::min(d, 360.f - d);
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t const id : { SPELL_MT_FACE_BEAM, SPELL_MT_BOMB_MARK, SPELL_MT_BOMB_BLAST,
                SPELL_MT_BLAST_LOOK, SPELL_MT_BLAST_FLASH, SPELL_MT_LOCKED_OUT, SPELL_MT_MINE_LOB,
                SPELL_MT_MINE_BLAST, SPELL_MT_MINE_LOOK, SPELL_MT_KNOCK_AWAY, SPELL_MT_DETONATOR,
                SPELL_MT_INCENDIARY_BLAST, SPELL_MT_FIRE_PATCH,
                SPELL_MT_FIRE_PATCH_LOOK, SPELL_MT_FIRE_PATCH_CAST, SPELL_MT_FROST_BLAST, SPELL_MT_FROST_ROOT,
                SPELL_MT_RADIO_BLAST, SPELL_MT_RADIO_POISON, SPELL_MT_STICKY_BOMB, SPELL_MT_STICKY_BLAST,
                SPELL_MT_BIG_ONE_BLAST })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_MT_BIG_ONE_BLAST == kSpellSlice.first + 21);
    }

    void TestFacesAndBombs()
    {
        // Ruling 64: 01 Walking, 02 Incendiary, 03 Frost, 04 Radioactive, 05 Sticky, 06 The Big One (heroic and up).
        BombType const expected[] = { BombType::Walking, BombType::Incendiary, BombType::Frost, BombType::Radioactive,
            BombType::Sticky, BombType::BigOne };
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
        {
            CHECK(FaceBomb(Mode::Normal, face) == BombType::Walking);
            CHECK(FaceBomb(Mode::Heroic, face) == expected[face]);
            CHECK(FaceBomb(Mode::HardMode, face) == expected[face]);
        }
        CHECK(FaceBomb(Mode::Heroic, 6) == BombType::Walking);
        CHECK(kFaceEntries[0] == GO_GNOME_FACE_01 && kFaceEntries[5] == GO_GNOME_FACE_06);

        // Entries: the build's own ids, never the gear's Launched Walking Bomb (rule 32, s7 #40 A).
        CHECK(BombEntry(BombType::Walking) == 301120);
        CHECK(BombEntry(BombType::Incendiary) == 301121);
        CHECK(BombEntry(BombType::Frost) == 301122);
        CHECK(BombEntry(BombType::Radioactive) == 301123);
        CHECK(BombEntry(BombType::BigOne) == 301124);
        CHECK(BombEntry(BombType::Sticky) == 0);
        CHECK(!BombTypeOfEntry(NPC_GEAR_LAUNCHED_BOMB));
        CHECK(!BombTypeOfEntry(NPC_WALKING_BOMB_STOCK));
        CHECK(!BombTypeOfEntry(0));
        for (std::size_t i = 0; i < kBombTypeCount; ++i)
        {
            BombType const type = static_cast<BombType>(i);
            if (BombEntry(type))
                CHECK(BombTypeOfEntry(BombEntry(type)) == type);
            CHECK(kCreaturesReservation.Contains(BombEntry(type)) || type == BombType::Sticky);
        }
        for (std::uint32_t const entry : kWalkingBombEntries)
        {
            CHECK(BombTypeOfEntry(entry).has_value());
            CHECK(WalksAtPlayer(*BombTypeOfEntry(entry)));
        }
        CHECK(!WalksAtPlayer(BombType::Sticky));
        CHECK(!WalksAtPlayer(BombType::BigOne));

        // SP 1704: The Big One, Sticky, Incendiary, Frost, Radioactive, Walking last; normal plates unranked.
        std::int32_t const ranks[] = { 5, 2, 3, 4, 1, 0 };
        std::set<std::int32_t> seen;
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
        {
            CHECK(PlateRank(Mode::Normal, face) == 0);
            CHECK(PlateRank(Mode::Heroic, face) == ranks[face]);
            CHECK(PlateRank(Mode::HardMode, face) == ranks[face]);
            seen.insert(PlateRank(Mode::Heroic, face));
        }
        CHECK(seen.size() == kFaceCount);

        // The blasts' spells, schools and riders (the kick and dispel table: the Frost root and the Poison).
        CHECK(BlastOf(BombType::Walking).spellId == SPELL_MT_BOMB_BLAST && BlastOf(BombType::Walking).rider == 0);
        CHECK(BlastOf(BombType::Frost).rider == SPELL_MT_FROST_ROOT && BlastOf(BombType::Frost).school == 4);
        CHECK(BlastOf(BombType::Radioactive).rider == SPELL_MT_RADIO_POISON
            && BlastOf(BombType::Radioactive).school == 3);
        CHECK(BlastOf(BombType::Incendiary).spellId == SPELL_MT_INCENDIARY_BLAST);
        CHECK(ChuteEveryMs(BombType::BigOne) == 16000 && ChuteEveryMs(BombType::Walking) == 8000
            && ChuteEveryMs(BombType::Sticky) == 8000);
    }

    void TestModeValues()
    {
        ModeValues const n = ValuesFor(Mode::Normal);
        ModeValues const h = ValuesFor(Mode::Heroic);
        ModeValues const m = ValuesFor(Mode::HardMode);
        CHECK(ModeFor(false, false) == Mode::Normal && ModeFor(false, true) == Mode::Normal);
        CHECK(ModeFor(true, false) == Mode::Heroic && ModeFor(true, true) == Mode::HardMode);

        // SP 1632-1644 (normal and heroic)
        CHECK(n.faceEveryMs == 20000 && h.faceEveryMs == 15000);
        CHECK(n.overrideEveryMs == 45000 && h.overrideEveryMs == 45000);
        CHECK(n.overrideFaces == 3 && h.overrideFaces == 0);
        CHECK(n.bombCap == 8 && h.bombCap == 0);
        CHECK(n.bombHealth == 400 && h.bombHealth == 5000);
        CHECK(n.blastPct == 40.f && h.blastPct == 60.f);
        CHECK(!n.blowWhenKilled && h.blowWhenKilled);
        CHECK(!n.typedFaces && h.typedFaces);
        CHECK(n.mineEveryMs == 15000 && h.mineEveryMs == 15000);
        CHECK(n.mineCount == 3 && h.mineCount == 0);
        CHECK(n.mineLifeMs == 45000 && h.mineLifeMs == 60000);
        CHECK(n.minePct == 40.f && h.minePct == 60.f);
        CHECK(n.detonatorEveryMs == 0 && h.detonatorEveryMs == 25000);
        CHECK(h.stickyPct == 60.f);

        // SP 1799 and ruling 53: the hard mode at or above heroic on every value (the lockout held equal)
        CHECK(m.faceEveryMs == 12000 && m.faceEveryMs <= h.faceEveryMs);
        CHECK(m.overrideEveryMs == 35000 && m.overrideEveryMs <= h.overrideEveryMs);
        CHECK(m.overrideFaces == 0 && m.bombCap == 0);
        CHECK(m.bombHealth == 7000 && m.bombHealth >= h.bombHealth);
        CHECK(m.blastPct == 70.f && m.blastPct >= h.blastPct);
        CHECK(m.minePct == 70.f && m.mineEveryMs == 12000 && m.mineLifeMs == 75000);
        CHECK(m.mineEveryMs <= h.mineEveryMs && m.mineLifeMs >= h.mineLifeMs && m.mineCount == h.mineCount);
        CHECK(m.detonatorEveryMs == 20000 && m.detonatorEveryMs <= h.detonatorEveryMs);
        CHECK(m.stickyPct >= h.stickyPct && m.blowWhenKilled && m.typedFaces);
        CHECK(Tune::kLockedOutMs == 30000);

        // The bomb health is the header's table (never restated)
        CHECK(n.bombHealth == Health::kWalkingBomb.normal && h.bombHealth == Health::kWalkingBomb.heroic);
        CHECK(m.bombHealth == Health::kWalkingBombHardMode);

        // The warning floor (SYS 4) and the mine rings (ruling 41)
        CHECK(Tune::kMineArmMs >= kWarningFloorMs && Tune::kStickyFuseMs >= kWarningFloorMs);
        CHECK(Tune::kDetonatorCastMs >= kWarningFloorMs);
        CHECK(Tune::kMineTriggerYd == 3.f && Tune::kMineBlastYd == 6.f && Tune::kMineGraceMs == 500);
        CHECK(Tune::kBombBlastYd == 8.f && Tune::kBombReachYd == 3.f && Tune::kStickyYd == 8.f);
        CHECK(Tune::kFirePatchMs == 20000 && Tune::kFirePatchPct == 15.f && Tune::kFirePatchYd == 8.f);
        CHECK(Tune::kBigOnePct == 100.f && Tune::kBigOneSpeedYdPerSec == 3.f);
        CHECK(Tune::kKnockFirstMs == 3000 && Tune::kKnockEveryMs == 15000);
        CHECK(Tune::kFaceFirstMs == 10000 && Tune::kMineFirstMs == 8000 && Tune::kDetonatorFirstMs == 20000);
    }

    void TestRoom()
    {
        Vec2 const center = kRoomCenter.XY();
        Arena const room = ArenaFor(BOSS_THERMAPLUGG);
        CHECK(room.Contains(kThermapluggSpawn.XY(), kThermapluggSpawn.z));
        CHECK(room.Contains(kConsoleSpot.XY(), kConsoleSpot.z));
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
        {
            Vec2 const plate = kPlateSpots[face].XY();
            Vec2 const start = kBombStarts[face].XY();
            Vec2 const faceSpot = kFaceSpots[face].XY();
            // s7 #30 A: 25 yd from the center, in line with the face
            CHECK(std::fabs(DungeonKit::Distance(center, plate) - kPlateRadiusYd) < 0.2f);
            CHECK(AngleGap(BearingDeg(center, plate), BearingDeg(center, faceSpot)) < 1.5f);
            CHECK(AngleGap(BearingDeg(center, faceSpot), kFaceBearingDeg[face]) < 1.5f);
            // s7 #31: the bomb start at the alcove mouth, 37 yd out, in line with the face; the walk stays 8 s (B)
            CHECK(std::fabs(DungeonKit::Distance(center, start) - kBombStartRadiusYd) < 0.3f);
            CHECK(AngleGap(BearingDeg(center, start), BearingDeg(center, faceSpot)) < 1.5f);
            std::uint32_t const walk = WalkMs(DungeonKit::Distance(start, center) - Tune::kBombReachYd,
                Tune::kBombSpeedYdPerSec);
            CHECK(walk >= 7000 && walk <= 8500);
            // every plate and start on his arena, the plates 12 yd inside the bowl wall
            CHECK(room.Contains(plate, kPlateSpots[face].z));
            CHECK(room.Contains(start, kBombStarts[face].z));
        }
        // neighbors 21.6 to 21.8 yd apart (39.2 across the 06-01 gap)
        for (std::uint32_t face = 0; face + 1 < kFaceCount; ++face)
        {
            float const d = DungeonKit::Distance(kPlateSpots[face].XY(), kPlateSpots[face + 1].XY());
            CHECK(d > 21.f && d < 22.5f);
        }
        float const gap = DungeonKit::Distance(kPlateSpots[5].XY(), kPlateSpots[0].XY());
        CHECK(gap > 38.5f && gap < 40.f);
        // The Big One's walk from face 06's mouth at 3 yd/s
        std::uint32_t const bigOne = WalkMs(DungeonKit::Distance(kBombStarts[5].XY(), center),
            Tune::kBigOneSpeedYdPerSec);
        CHECK(bigOne > 11000 && bigOne < 13500);
        // STAGE-R-1-C Minor-2: the Stack resolves at the walk's end and the bomb blows then, never later (the old
        // Stack ran 3 s past the walk and a walk that stopped short blew at 30 s, after the Stack was gone).
        CHECK(BigOneStackMs(bigOne) == bigOne);
        CHECK(BigOneStackMs(400) == GnomereganRework::kWarningFloorMs);
        CHECK(!BigOneBlows(bigOne - 1, BigOneStackMs(bigOne)));
        CHECK(BigOneBlows(bigOne, BigOneStackMs(bigOne)));
        CHECK(BigOneBlows(30000, BigOneStackMs(bigOne)));
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
        {
            std::uint32_t const walk = WalkMs(DungeonKit::Distance(kBombStarts[face].XY(), center),
                Tune::kBigOneSpeedYdPerSec);
            CHECK(BigOneStackMs(walk) == walk);     // every face's walk is over the floor: the Stack is the walk
        }
    }

    void TestClockAndPicks()
    {
        // RB-17: one period on; a late beat never fires again within half a period
        CHECK(NextDue(10000, 20000, 10000) == 30000);
        CHECK(NextDue(10000, 20000, 35000) == 45000);
        CHECK(NextDue(0, 8000, 100) == 8000);

        FaceMask open{ { true, false, true, false, false, true } };
        CHECK(OpenCount(open) == 3);
        auto first = [](std::uint32_t) { return 0u; };
        auto last = [](std::uint32_t n) { return n - 1; };
        std::vector<std::uint32_t> one = PickClosedFaces(open, 1, first);
        CHECK(one.size() == 1 && one[0] == 1);
        one = PickClosedFaces(open, 1, last);
        CHECK(one.size() == 1 && one[0] == 4);
        std::vector<std::uint32_t> const all = PickClosedFaces(open, 0, first);
        CHECK((all == std::vector<std::uint32_t>{ 1, 3, 4 }));
        std::vector<std::uint32_t> const three = PickClosedFaces(open, 3, first);
        CHECK(three.size() == 3);
        std::vector<std::uint32_t> two = PickClosedFaces(open, 2, last);
        CHECK(two.size() == 2 && two[0] == 4 && two[1] == 3);
        FaceMask full{ { true, true, true, true, true, true } };
        CHECK(PickClosedFaces(full, 1, first).empty());
        CHECK(PickClosedFaces(full, 0, first).empty());
        // a bad rand never reads past the list
        auto wild = [](std::uint32_t) { return 99u; };
        CHECK(PickClosedFaces(open, 1, wild).size() == 1);

        CHECK(ChuteMayBuild(8, 7) && !ChuteMayBuild(8, 8) && ChuteMayBuild(0, 500));
        CHECK(MineTargets(3, 5) == 3 && MineTargets(3, 2) == 2 && MineTargets(0, 5) == 5 && MineTargets(0, 0) == 0);
        CHECK(PlateTakes(true, false) && !PlateTakes(false, false) && !PlateTakes(true, true));
    }

    void TestBlasts()
    {
        Vec2 const c{ -531.f, 670.f };
        CHECK(InBlast(c, -325.f, { -531.f, 678.f }, -325.f, 8.f, 6.f));
        CHECK(!InBlast(c, -325.f, { -531.f, 678.5f }, -325.f, 8.f, 6.f));
        CHECK(!InBlast(c, -325.f, { -531.f, 671.f }, -318.f, 8.f, 6.f));

        // The Big One: split evenly among those inside, the whole blast on everyone when nobody is
        CHECK(BigOneSharePct(1, 100.f) == 100.f);
        CHECK(BigOneSharePct(4, 100.f) == 25.f);
        CHECK(BigOneSharePct(5, 100.f) == 20.f);
        CHECK(BigOneSharePct(0, 100.f) == 100.f);

        CHECK(WalkMs(37.f, 4.6f) == 8043);
        CHECK(WalkMs(10.f, 0.f) == 0);

        CHECK(CombinedFactor({}) == 1.f);
        CHECK(std::fabs(CombinedFactor({ 1.03f, 1.1f }) - 1.133f) < 0.001f);
        CHECK(CombinedFactor({ -1.f, 2.f }) == 0.f);
    }

    void TestThresholds()
    {
        ThresholdLatch latch;
        latch.Arm({ 30.f, 90.f, 60.f, 75.f, 45.f });
        CHECK(latch.Left() == 5);
        CHECK(latch.Crossed(95.f).empty());
        std::vector<float> got = latch.Crossed(90.f);
        CHECK(got.size() == 1 && got[0] == 90.f);
        CHECK(latch.Crossed(89.f).empty());
        got = latch.Crossed(44.f);      // a big hit crosses three at once, highest first
        CHECK(got.size() == 3 && got[0] == 75.f && got[1] == 60.f && got[2] == 45.f);
        CHECK(latch.Crossed(80.f).empty());     // a heal never re-fires one
        got = latch.Crossed(0.f);
        CHECK(got.size() == 1 && got[0] == 30.f);
        CHECK(latch.Left() == 0);
        latch.Arm({ 50.f });
        latch.Clear();
        CHECK(latch.Crossed(0.f).empty());
    }

    void TestTags()
    {
        std::set<std::uint32_t> tags;
        std::set<std::string> names;
        for (DrillTag const& t : kDrillTags)
        {
            tags.insert(t.tag);
            names.insert(t.name);
            CHECK(t.tag >= 70 && t.tag < kFirstPackageTag);
        }
        // G1's block (STAGE-G1-REPORT "Bars"): 70 Stack, 71 Soak, 72-73 Zone, 74 RunOut, 75-76 Zone, 77 Soak
        CHECK(TAG_MT_BIG_ONE == 70 && TAG_MT_PLATE == 71 && TAG_MT_BOMB_RING == 72 && TAG_MT_BOMB_BLAST == 73);
        CHECK(TAG_MT_BOMB_RUN == 74 && TAG_MT_MINE == 75 && TAG_MT_MINE_RING == 76 && TAG_MT_DETONATOR == 77);
        CHECK(kFirstPackageTag == 80);
        CHECK(tags.size() == kDrillTags.size() && names.size() == kDrillTags.size());
        CHECK(kFirstPackageTextGroup == 9 && EMOTE_MT_DETONATOR == 8 && SAY_MT_KILL == 3);
    }

    void TestBossFile()
    {
        std::string const boss = ReadFile(SourceDir() / "boss_thermaplugg_rework.cpp");
        std::string const fight = ReadFile(SourceDir() / "ThermapluggFight.h");
        CHECK(!boss.empty() && !fight.empty());
        for (char const* name : { "boss_thermaplugg_rework", "npc_gnomer_walking_bomb",
                "npc_gnomer_thermaplugg_stalker" })
            CHECK(boss.find(std::string("RegisterDungeonReworkCreatureAI(") + name + ",") != std::string::npos);
        // the hard mode registry is defined here, once
        for (char const* fn : { "void RegisterThermapluggHardMode(", "CreateThermapluggHardModes(ThermapluggFight&",
                "ThermapluggFight* FindThermapluggFight(Map* map)" })
            CHECK(boss.find(fn) != std::string::npos);
        // the verdict before OnEngage, OnEnd first in the cleanup (ThermapluggFight.h's hook order)
        std::size_t const verdict = boss.find("instance->SetData(DATA_HARD_MODE_VERDICT");
        std::size_t const engage = boss.find("package->OnEngage(*this)");
        CHECK(verdict != std::string::npos && engage != std::string::npos && verdict < engage);
        std::size_t const cleanup = boss.find("void Cleanup(bool won)");
        std::size_t const onEnd = boss.find("package->OnEnd(*this, won)");
        std::size_t const despawn = boss.find("summons.DespawnAll()", cleanup);
        CHECK(cleanup != std::string::npos && onEnd > cleanup && despawn > onEnd);
        // rule 32: no victimless MoveChase on a bomb; no gear bomb entry
        CHECK(boss.find("->MoveChase(") == std::string::npos);
        CHECK(boss.find("301100") == std::string::npos);
        // every hook the header promises
        for (char const* hook : { "OnEngage", "OnUpdate", "HealthThresholds", "OnHealthPct", "OnFaceOpened",
                "OnFaceShut", "OnPlateTouched", "OnBombSpawned", "OnBombGone", "OnPlayersHit", "DamageFactor",
                "OnEnd", "DescribeExtra", "AdoptBomb", "OpenFace", "PlateAnchor" })
        {
            CHECK(fight.find(hook) != std::string::npos);
            CHECK(boss.find(hook) != std::string::npos);
        }
    }
}

int main()
{
    TestSlice();
    TestFacesAndBombs();
    TestModeValues();
    TestRoom();
    TestClockAndPicks();
    TestBlasts();
    TestThresholds();
    TestTags();
    TestBossFile();
    return Report("gnomer_thermaplugg_test");
}
