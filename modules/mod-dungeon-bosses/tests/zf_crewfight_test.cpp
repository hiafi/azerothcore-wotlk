// Host tests for CrewFightLogic.h (D5: Sergeant Bly's crew as a boss): the slice, the tags, Gang Up and heroic Focus
// Fire / Singled Out, Bodyguard's pick and split, Murta's two big casts, the fight's book (falls, yields, deaths,
// Avenge, the Soulstone's clock, Resurrection's pick, the end) and the stash; plus a scan of bly_crew_fight_rework.cpp
// for the rules the engine half must keep (handlers on Boss and Yielded for the four fighters only, no faction or
// template writes, every spell id used, the stash of both difficulties) and of its SQL rev and DT file.
#include "CrewFightLogic.h"
#include "check.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace ZulFarrakRework;
using namespace ZfCrewFight;

namespace
{
    std::string ReadFile(std::filesystem::path const& path)
    {
        std::ifstream in(path);
        std::stringstream text;
        text << in.rdbuf();
        return text.str();
    }

    std::filesystem::path ModuleDir()
    {
        return std::filesystem::absolute(std::filesystem::path(__FILE__)).parent_path().parent_path();
    }

    std::filesystem::path CoreDir()
    {
        return ModuleDir().parent_path().parent_path();
    }

    bool Near(float a, float b)
    {
        return std::fabs(a - b) < 0.001f;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::size_t i = 0; i < kCrewFightSpells.size(); ++i)
        {
            CHECK(kSpellSlice.Contains(kCrewFightSpells[i]));
            CHECK(kCrewFightSpells[i] == kSpellSlice.first + i);     // dense from the slice's start
        }
        // CR's ally slice and the crew's stock spells are not ours
        CHECK(!kSpellSlice.Contains(ZfCrew::kSpellSlice.first) && !kSpellSlice.Contains(ZfCrew::kSpellSlice.last));
        // G1's drill tags (row 7)
        CHECK(TAG_BC_SEED == 16 && TAG_BC_GANG_UP == 17 && TAG_BC_AMBUSH == 18 && TAG_BC_RAIN == 19);
    }

    void TestGangUp()
    {
        // BC1: normal is flat 60%; heroic Focus Fire 90, 105, 120, ..., no cap
        CHECK(Near(GangUpTotalPct(false, 0), 60.f));
        CHECK(Near(GangUpTotalPct(false, 7), 60.f));
        CHECK(Near(GangUpTotalPct(true, 0), 90.f));
        CHECK(Near(GangUpTotalPct(true, 1), 105.f));
        CHECK(Near(GangUpTotalPct(true, 2), 120.f));
        CHECK(Near(GangUpTotalPct(true, 4), 150.f));     // SP: Bly fought last sees calls past 150%
        CHECK(GangUpTotalPct(true, 40) > GangUpTotalPct(true, 39));
        // the split: 20% each with three (SP), 30% with two, 60% alone, nothing with nobody
        CHECK(Near(SharePct(60.f, 3), 20.f));
        CHECK(Near(SharePct(60.f, 2), 30.f));
        CHECK(Near(SharePct(60.f, 1), 60.f));
        CHECK(Near(SharePct(60.f, 0), 0.f));
        CHECK(Near(SharePct(90.f, 5), 18.f));
        // Singled Out: the farthest player outside the stack; none outside: none
        CHECK(!PickSingledOut({ false, false, false }, { 1.f, 2.f, 3.f }));
        CHECK(PickSingledOut({ true, false, true }, { 9.f, 30.f, 12.f }) == std::optional<std::size_t>(2));
        CHECK(PickSingledOut({ true, true }, { 15.f, 15.f }) == std::optional<std::size_t>(0));
        CHECK(!PickSingledOut({}, {}));
        // timers
        CHECK(Tune::kGangUpFirstMs == 8000);
        CHECK(Tune::kGangUpEveryMs.normal == 20000 && Tune::kGangUpEveryMs.heroic == 16000);
        CHECK(Tune::kGangUpWarnMs == 4000 && Tune::kSetUpWarnMs == 2000);
        CHECK(Near(Tune::kGangUpRadiusYd, 6.f));
    }

    void TestBodyguard()
    {
        std::array<float, kCrewCount> pct{ { 20.f, 70.f, 40.f, 5.f, 55.f } };
        // never Bly (20%) nor Weegli (5%): Oro is the lowest of the three
        CHECK(PickGuarded(pct, kCrewAll) == std::optional<std::uint32_t>(CREW_ORO));
        CHECK(PickGuarded(pct, CrewBit(CREW_BLY) | CrewBit(CREW_RAVEN)) == std::optional<std::uint32_t>(CREW_RAVEN));
        CHECK(!PickGuarded(pct, CrewBit(CREW_BLY) | CrewBit(CREW_WEEGLI)));
        // ties: the kill order's first (Murta)
        std::array<float, kCrewCount> tie{ { 50.f, 30.f, 30.f, 50.f, 30.f } };
        CHECK(PickGuarded(tie, kCrewFighters) == std::optional<std::uint32_t>(CREW_MURTA));
        // 75% cut, Bly a third of it
        GuardSplit const s = SplitGuarded(1000);
        CHECK(s.taken == 250 && s.blocked == 750 && s.blyShare == 250);
        GuardSplit const odd = SplitGuarded(7);
        CHECK(odd.taken + odd.blocked == 7 && odd.blyShare == odd.blocked / 3);
        CHECK(SplitGuarded(0).taken == 0 && SplitGuarded(0).blyShare == 0);
        CHECK(GuardHolds(true, 5.f) && !GuardHolds(true, 5.1f) && !GuardHolds(false, 1.f));
        CHECK(Tune::kBodyguardEveryMs.normal == 15000 && Tune::kBodyguardEveryMs.heroic == 12000);
        CHECK(Tune::kGuardedMs == 8000);
    }

    void TestMurta()
    {
        // never Greater Heal and Resurrection back to back
        CHECK(GreaterHealAllowed(LastCast::None) && GreaterHealAllowed(LastCast::Other)
            && GreaterHealAllowed(LastCast::GreaterHeal) && !GreaterHealAllowed(LastCast::Resurrection));
        CHECK(ResurrectionAllowed(LastCast::None) && ResurrectionAllowed(LastCast::Other)
            && ResurrectionAllowed(LastCast::Resurrection) && !ResurrectionAllowed(LastCast::GreaterHeal));
        // under 50%, first one at once, then 15 s (heroic 12 s)
        CHECK(GreaterHealDue(49.f, false, 0, false, LastCast::None));
        CHECK(!GreaterHealDue(50.f, false, 0, false, LastCast::None));
        CHECK(!GreaterHealDue(10.f, true, 14999, false, LastCast::Other));
        CHECK(GreaterHealDue(10.f, true, 15000, false, LastCast::Other));
        CHECK(!GreaterHealDue(10.f, true, 11999, true, LastCast::Other));
        CHECK(GreaterHealDue(10.f, true, 12000, true, LastCast::Other));
        CHECK(!GreaterHealDue(10.f, true, 60000, true, LastCast::Resurrection));
        CHECK(Tune::kGreaterHealCastMs.normal == 3000 && Tune::kGreaterHealCastMs.heroic == 2000);
        CHECK(Near(Tune::kGreaterHealPct.normal, 25.f) && Near(Tune::kGreaterHealPct.heroic, 50.f));
        // the Test's 20% window between the heal and the yield (SP)
        CHECK(Near(Tune::kGreaterHealBelowPct - Tune::kYieldPct, 20.f));
    }

    void TestBookBetrayalHeroic()
    {
        FightBook b;
        StartBook(b, true, CREW_PATH_BETRAYAL);
        CHECK(b.running && b.heroic && b.soulstoneUp && b.avenge == 0);
        CHECK(FightingMask(b) == kCrewFighters);
        CHECK(!Decided(b));
        // Weegli never goes out; a fighter going in again is no fall
        CHECK(!GoOut(b, CREW_WEEGLI, Standing::Fallen, 1000));
        CHECK(!GoOut(b, CREW_BLY, Standing::Fighting, 1000));
        // Murta falls with Oro up: the Soulstone's clock (10 s); Avenge 1
        CHECK(GoOut(b, CREW_MURTA, Standing::Fallen, 1000));
        CHECK(b.avenge == 1 && b.soulstoneDueMs == 11000 && b.falls == 1);
        CHECK(!GoOut(b, CREW_MURTA, Standing::Fallen, 1500));      // no second stack
        CHECK(!SoulstoneDue(b, 10999) && SoulstoneDue(b, 11000));
        // she rises: the clock is spent
        CHECK(Rise(b, CREW_MURTA) && b.standing[CREW_MURTA] == Standing::Fighting && b.soulstoneDueMs == 0);
        CHECK(!Rise(b, CREW_MURTA));
        // she falls again, the stone is used (no stone up): no clock
        b.soulstoneUp = false;
        CHECK(GoOut(b, CREW_MURTA, Standing::Fallen, 20000) && b.soulstoneDueMs == 0 && b.avenge == 2);
        // Oro falls within 10 s of a stoned Murta: no rise (SP: "unless Oro is dead by then")
        FightBook c;
        StartBook(c, true, CREW_PATH_BETRAYAL);
        GoOut(c, CREW_MURTA, Standing::Fallen, 0);
        CHECK(c.soulstoneDueMs == 10000);
        GoOut(c, CREW_ORO, Standing::Fallen, 5000);
        CHECK(c.soulstoneDueMs == 0 && !SoulstoneDue(c, 20000));
        // Resurrection's pick: the one out longest, never Murta
        FightBook r;
        StartBook(r, true, CREW_PATH_BETRAYAL);
        CHECK(!PickResurrection(r));
        GoOut(r, CREW_RAVEN, Standing::Fallen, 3000);
        GoOut(r, CREW_BLY, Standing::Fallen, 1000);
        CHECK(PickResurrection(r) == std::optional<std::uint32_t>(CREW_BLY));
        GoOut(r, CREW_BLY, Standing::Dead, 4000);       // a real death: nothing raises it, no second stack
        CHECK(r.avenge == 2 && PickResurrection(r) == std::optional<std::uint32_t>(CREW_RAVEN));
        GoOut(r, CREW_MURTA, Standing::Fallen, 5000);
        CHECK(PickResurrection(r) == std::optional<std::uint32_t>(CREW_RAVEN));
        // decided only once all four are down and the stone cannot raise Murta
        CHECK(!Decided(r));
        GoOut(r, CREW_ORO, Standing::Fallen, 6000);
        CHECK(r.soulstoneDueMs == 0 && Decided(r) && r.avenge == 4);
        // a stoned Murta down last with Oro up holds the decision
        FightBook d;
        StartBook(d, true, CREW_PATH_BETRAYAL);
        GoOut(d, CREW_BLY, Standing::Fallen, 0);
        GoOut(d, CREW_RAVEN, Standing::Fallen, 0);
        GoOut(d, CREW_MURTA, Standing::Fallen, 100);
        CHECK(!Decided(d) && d.soulstoneDueMs == 10100);
        // Murta's real death clears the clock
        GoOut(d, CREW_MURTA, Standing::Dead, 200);
        CHECK(d.soulstoneDueMs == 0);
    }

    void TestBookNormalAndTest()
    {
        // normal betrayal: no Avenge, no stone
        FightBook n;
        StartBook(n, false, CREW_PATH_BETRAYAL);
        CHECK(!n.soulstoneUp);
        for (std::uint32_t m : { std::uint32_t(CREW_MURTA), std::uint32_t(CREW_ORO), std::uint32_t(CREW_RAVEN),
            std::uint32_t(CREW_BLY) })
            CHECK(GoOut(n, m, Standing::Dead, 1000));
        CHECK(n.avenge == 0 && n.soulstoneDueMs == 0 && Decided(n) && n.falls == 4);
        // the Test: a yield counts for Avenge and the stone; a yielded member can rise
        FightBook t;
        StartBook(t, true, CREW_PATH_TEST);
        GoOut(t, CREW_RAVEN, Standing::Yielded, 0);
        CHECK(t.avenge == 1 && PickResurrection(t) == std::optional<std::uint32_t>(CREW_RAVEN));
        CHECK(Rise(t, CREW_RAVEN) && t.rises == 1);
        GoOut(t, CREW_RAVEN, Standing::Yielded, 5000);
        CHECK(t.avenge == 2);                       // "a second kill of the same member is paid for twice"
        GoOut(t, CREW_MURTA, Standing::Yielded, 6000);
        CHECK(t.soulstoneDueMs == 16000);
        GoOut(t, CREW_ORO, Standing::Yielded, 7000);
        GoOut(t, CREW_BLY, Standing::Yielded, 8000);
        CHECK(t.avenge == 5 && Decided(t));
        // not running: never decided
        FightBook idle;
        CHECK(!Decided(idle));
    }

    void TestTimersAndNumbers()
    {
        CHECK(Tune::kAmbushFirstMs == 12000);
        CHECK(Tune::kAmbushEveryMs.normal == 18000 && Tune::kAmbushEveryMs.heroic == 14000);
        CHECK(Tune::kAmbushWarnMs.normal == 2000 && Tune::kAmbushWarnMs.heroic == 1500);
        CHECK(Near(Tune::kAmbushPct, 40.f) && Near(Tune::kAmbushRadiusYd, 3.f));
        CHECK(Tune::kGougeMs == 2000 && Tune::kGouge.minMs == 11000 && Tune::kGouge.maxMs == 23000);
        CHECK(Tune::kRainMs / Tune::kRainTickMs == 3);
        CHECK(Near(Tune::kRainTickPct.normal, 6.f) && Near(Tune::kRainTickPct.heroic, 8.f));
        CHECK(Near(Tune::kRainRadiusYd, 8.f));
        CHECK(Tune::kSeedEveryMs == 20000 && Tune::kSeedMs == 6000 && Near(Tune::kSeedPct, 35.f));
        CHECK(Near(Tune::kSeedRadiusYd, 10.f));
        CHECK(Tune::kKidneyShotMs == 2000 && Tune::kWoundPoisonMs == 15000 && Tune::kWoundPoisonHealingPct == 50);
        CHECK(Tune::kResurrectionCastMs == 8000 && Near(Tune::kRisePct, 50.f) && Tune::kSoulstoneMs == 10000);
        CHECK(Tune::kAvengePctPerStack == 20);
        // Ruling 29 / FF 2.5: KillTogether takes a percent
        CHECK(Near(Tune::kKillTogetherPct, 10.f));
        // crew health stays in the header (never restated)
        CHECK(Health::kBly.normal == 63941 && Health::kMurta.heroic == 73260);
    }

    void TestStash()
    {
        // the chest stands on the plaza, near the gather spots
        CHECK(PlazaArena().Contains(kStashSpot.XY(), kStashSpot.z));
        float const dx = kStashSpot.x - kCrewGatherPoints[CREW_BLY].x;
        float const dy = kStashSpot.y - kCrewGatherPoints[CREW_BLY].y;
        CHECK(std::sqrt(dx * dx + dy * dy) < 10.f);
        CHECK(StashEntry(false) == GO_ZF_CREW_STASH && StashEntry(true) == GO_ZF_CREW_STASH_HEROIC);
        CHECK(GO_ZF_CREW_STASH == 301360 && GO_ZF_CREW_STASH_HEROIC == 301361);
    }

    void TestEngineFile()
    {
        std::string const cpp = ReadFile(ModuleDir() / "src" / "ZulFarrak" / "bly_crew_fight_rework.cpp");
        CHECK(!cpp.empty());
        // rule 28: never a faction, template or crew AI of its own; handlers for the four fighters only
        CHECK(cpp.find("SetFaction(") == std::string::npos);
        CHECK(cpp.find("struct npc_") == std::string::npos && cpp.find("struct boss_") == std::string::npos);
        CHECK(cpp.find("RegisterCrewModeHandler(CrewMode::Boss,") != std::string::npos);
        CHECK(cpp.find("RegisterCrewModeHandler(CrewMode::Yielded,") != std::string::npos);
        CHECK(cpp.find("kCrewFighters);") != std::string::npos);
        // bots take gossip option 0 = the betrayal: D5 keeps CR's gossip and start
        CHECK(cpp.find("SetCrewFightStarter") == std::string::npos);
        CHECK(cpp.find("sGossip") == std::string::npos);
        // slot 6 only through the instance's data
        CHECK(cpp.find("SetBossState") == std::string::npos);
        CHECK(cpp.find("SetData(DATA_CREW_FIGHT, DungeonKit::State::Done)") != std::string::npos);
        // the stash of the map's difficulty, both paths
        CHECK(cpp.find("StashEntry(DungeonKit::IsHeroicMap(") != std::string::npos);
        CHECK(cpp.find("SpawnStash(s, \"test\")") != std::string::npos);
        CHECK(cpp.find("SpawnStash(s, \"betrayal\")") != std::string::npos);
        // every spell of the slice is used by name
        for (char const* name : { "SPELL_BC_GANG_UP_MARK", "SPELL_BC_GANG_UP_SHARE", "SPELL_BC_GUARDED",
            "SPELL_BC_INTERVENE", "SPELL_BC_REFLECT", "SPELL_BC_VANISH", "SPELL_BC_AMBUSH", "SPELL_BC_GOUGE",
            "SPELL_BC_KIDNEY_SHOT", "SPELL_BC_WOUND_POISON", "SPELL_BC_RAIN_LOOK", "SPELL_BC_RAIN",
            "SPELL_BC_SEED", "SPELL_BC_SEED_BURST", "SPELL_BC_GREATER_HEAL", "SPELL_BC_GREATER_HEAL_H",
            "SPELL_BC_RESURRECTION", "SPELL_BC_SOULSTONE", "SPELL_BC_AVENGE", "SPELL_BC_WOUND_POISON_LOOK" })
            CHECK(cpp.find(name) != std::string::npos);
        // every registry shape keeps the bots on the plaza (rule 14)
        std::size_t shapes = 0;
        std::size_t within = 0;
        for (std::size_t at = cpp.find("MechanicRef ref = Mechanic::"); at != std::string::npos;
            at = cpp.find("MechanicRef ref = Mechanic::", at + 1))
            ++shapes;
        for (std::size_t at = cpp.find(".Within(PlazaFloorBounds())"); at != std::string::npos;
            at = cpp.find(".Within(PlazaFloorBounds())", at + 1))
            ++within;
        CHECK(shapes == 4 && within == shapes);
        // the descriptor: kill order with Guarded, crowd control ignored, the kicks
        CHECK(cpp.find("Condition::LacksAura(SPELL_BC_GUARDED)") != std::string::npos);
        CHECK(cpp.find("HasBreakableByDamageCrowdControlAura") != std::string::npos);
        CHECK(cpp.find("KillTogether(NPC_ORO, Tune::kKillTogetherPct)") != std::string::npos);
    }

    void TestDataFiles()
    {
        std::string const sql = ReadFile(CoreDir() / "data" / "sql" / "updates" / "pending_db_world"
            / "rev_bly_crew_fight_zul_farrak.sql");
        CHECK(!sql.empty());
        CHECK(sql.find("(301360, 3, ") != std::string::npos && sql.find(", 57, 301360, ") != std::string::npos);
        CHECK(sql.find("(301361, 3, ") != std::string::npos && sql.find(", 57, 301361, ") != std::string::npos);
        CHECK(sql.find("DELETE FROM `gameobject_template`") == std::string::npos);    // upserts only
        std::string const py = ReadFile(CoreDir() / "apps" / "dbc-tools" / "source" / "npcs" / "zul_farrak"
            / "bly_crew_fight.py");
        CHECK(!py.empty());
        for (std::uint32_t id : kCrewFightSpells)
            CHECK(py.find("_" + std::to_string(id) + " = ") != std::string::npos);
    }
}

int main()
{
    TestSlice();
    TestGangUp();
    TestBodyguard();
    TestMurta();
    TestBookBetrayalHeroic();
    TestBookNormalAndTest();
    TestTimersAndNumbers();
    TestStash();
    TestEngineFile();
    TestDataFiles();
    return Report("zf_crewfight_test");
}
