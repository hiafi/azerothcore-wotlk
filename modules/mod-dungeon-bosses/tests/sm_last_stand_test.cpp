// Host tests for LastStandLogic.h (D13: the Last Stand, Scarlet Commander Mograine and the Crusade's companies).
// The slice and the texts, the states a cold load restores, the build spec's numbers, the companies (members, arms,
// the heroic five, the Last Reserve), the call clock (fallen or the 30 / 25 s timer), the descent, the reserve and the
// fall rules, the 1% floor, the heal / healer / arrival / charge picks, the hammer's throw, and the room's points.
#include "LastStandLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <map>
#include <set>
#include <string>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmLastStand;

namespace
{
    float Dist(Vec2 a, Vec2 b)
    {
        return DungeonKit::Distance(a, b);
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 213100 && kSpellSlice.last == 213149);
        std::uint32_t const spells[] = { SPELL_LS_HAMMER_THROW, SPELL_LS_HAMMER_HIT, SPELL_LS_HAMMER_STRIKE,
            SPELL_LS_HAMMER_STUN, SPELL_LS_DIVINE_STORM_CAST, SPELL_LS_DIVINE_STORM_HIT, SPELL_LS_DIVINE_STORM_TANK,
            SPELL_LS_DEVOTION_AURA, SPELL_LS_DEVOTION_PULSE, SPELL_LS_CONSECRATION_HIT, SPELL_LS_CONSECRATION_GROUND,
            SPELL_LS_FIREBALL, SPELL_LS_PURIFYING_FLAME_CAST, SPELL_LS_PURIFYING_FLAME_HIT,
            SPELL_LS_PURIFYING_FLAME_FIRE, SPELL_LS_PURIFYING_FLAME_POOL, SPELL_LS_PURIFYING_FLAME_POOL_H,
            SPELL_LS_GREATER_HEAL, SPELL_LS_GREATER_HEAL_H, SPELL_LS_GREATER_HEAL_PULSE, SPELL_LS_CHARGE_HIT,
            SPELL_LS_CHARGE_LOOK };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == expected - 1);
        // Hammer of Justice 5589 (a live player override) is never one of ours (rule 15).
        CHECK(!kSpellSlice.Contains(kStockHammerOfJustice));
        for (std::uint32_t const id : spells)
            CHECK(id != kStockHammerOfJustice);
        // The companies are S0's ids, in the wave 2 block of the reservation.
        CHECK(NPC_SM_CHAPEL_GUARD_CHAMPION == 300950 && NPC_SM_CAPTAIN_OF_THE_GUARD == 300951
            && NPC_SM_COMPANY_CHAPLAIN == 300952 && NPC_SM_COMPANY_MONK == 300953 && NPC_SM_COMPANY_WIZARD == 300954
            && NPC_SM_COMPANY_ABBOT == 300955);
        for (std::uint32_t e = 300950; e <= 300955; ++e)
        {
            CHECK(kCreaturesWave2.Contains(e));
            CHECK(IsCompanyEntry(e));
            // The Ashbringer sweep leaves the companies out (section 7 #16 A, S0's AshbringerSweeps).
            CHECK(!AshbringerSweeps(e));
        }
        CHECK(!IsCompanyEntry(300949) && !IsCompanyEntry(300956) && !IsCompanyEntry(NPC_MOGRAINE));
        CHECK(!AshbringerSweeps(NPC_SM_STALKER_WAVE2));     // the conductor
        CHECK(GO_SM_LAST_STAND_CHEST == 301330 && GO_SM_LAST_STAND_CHEST_H == 301331);
        CHECK(kGameObjectsReservation.Contains(GO_SM_LAST_STAND_CHEST));
        CHECK(kGameObjectsReservation.Contains(GO_SM_LAST_STAND_CHEST_H));
        // Slot 5, wave 2, the credit the instance sends.
        CHECK(BOSS_LAST_STAND == 5);
        CHECK(IsWave2Boss(BOSS_LAST_STAND));
        CHECK(kSpellLastStandCredit == 212301);
        CHECK(!kSpellSlice.Contains(kSpellLastStandCredit));
    }

    void TestTexts()
    {
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_MOGRAINE)
            {
                found = true;
                CHECK(r.first == 0 && r.last == 13 && r.firstNew == kFirstOwnText);
                CHECK(kFirstOwnText >= r.firstNew && kLastOwnText <= r.last);
            }
        CHECK(found);
        CHECK(SAY_MOGRAINE_AGGRO == 0 && SAY_MOGRAINE_KILL == 1 && SAY_MOGRAINE_RISEN == 2);
        CHECK(SAY_MOGRAINE_DOOR == 7 && SAY_MOGRAINE_CALL_GUARD == 8 && SAY_MOGRAINE_CALL_PYRE == 9
            && SAY_MOGRAINE_CALL_CLERGY == 10 && SAY_MOGRAINE_LAST_RESERVE == 11);
        // D14 owns 12-13: the Last Stand's lines stay below.
        CHECK(kLastOwnText < 12);
        CHECK(CallLine(Company::ChapelGuard) == 8 && CallLine(Company::PyreBrethren) == 9
            && CallLine(Company::Clergy) == 10 && CallLine(Company::LastReserve) == 11);
    }

    namespace St = DungeonKit::State;

    void TestStates()
    {
        // A cold load: slot 5 DONE lies before the altar (the vigil, and after the finale); else the altar steps.
        CHECK(StateForStage(CathedralStage::BeforeStand) == MograineState::Altar);
        CHECK(StateForStage(CathedralStage::StandRunning) == MograineState::Altar);
        CHECK(StateForStage(CathedralStage::Vigil) == MograineState::Fallen);
        CHECK(StateForStage(CathedralStage::Done) == MograineState::Fallen);
        CHECK(StateForStage(CathedralStageFor(St::NotStarted, St::NotStarted)) == MograineState::Altar);
        CHECK(StateForStage(CathedralStageFor(St::Done, St::NotStarted)) == MograineState::Fallen);
        CHECK(StateForStage(CathedralStageFor(St::Done, St::Done)) == MograineState::Fallen);
        std::set<std::string> names;
        for (MograineState s : { MograineState::Altar, MograineState::Stand, MograineState::Fight,
            MograineState::Falling, MograineState::Fallen, MograineState::Risen })
            names.insert(StateName(s));
        CHECK(names.size() == 6);
        CHECK(names.count("?") == 0);
    }

    void TestTuning()
    {
        // CATH "Tuning starting points" / "Build spec" (and handoff 3.6).
        CHECK(kMograineHealth.normal == 55000 && kMograineHealth.heroic == 250000);
        CHECK(kBigMemberHealth.normal == 4000 && kBigMemberHealth.heroic == 15000);
        CHECK(kSmallMemberHealth.normal == 3000 && kSmallMemberHealth.heroic == 12000);
        CHECK(kCallEveryMs.normal == 30000 && kCallEveryMs.heroic == 25000);
        CHECK(kDevotionPct.normal == 30 && kDevotionPct.heroic == 40 && kDevotionRadiusYd == 15.f);
        CHECK(kDevotionAuraMs > kDevotionPulseMs);      // the buff never lapses between pulses
        CHECK(kConsecrationFirstMs == 4000 && kConsecrationEveryMs == 12000 && kConsecrationMs == 8000);
        CHECK(kConsecrationRadiusYd == 6.f && kConsecrationPct.normal == 10.f && kConsecrationPct.heroic == 15.f);
        CHECK(kFireballFirstMs == 3000 && kFireballEveryMs == 8000 && kFireballCastMs == 2500);
        CHECK(kFireballPct.normal == 15.f && kFireballPct.heroic == 20.f);
        CHECK(kFlameFirstMs == 6000 && kFlameEveryMs == 12000 && kFlameCastMs == 2500 && kFlameRadiusYd == 5.f);
        CHECK(kFlamePct.normal == 30.f && kFlamePct.heroic == 45.f);
        CHECK(kFlameFireMs.normal == 6000 && kFlameFireMs.heroic == 10000);
        CHECK(kFlameFirePct.normal == 10.f && kFlameFirePct.heroic == 15.f);
        CHECK(kGreaterHealFirstMs == 5000 && kGreaterHealEveryMs == 10000 && kGreaterHealCastMs == 3000);
        CHECK(kGreaterHealPct == 30 && kMissedHealPct == 50);
        CHECK(kHammerFirstMs == 8000 && kHammerEveryMs == 20000 && kHammerWarnMs == 2000 && kHammerRadiusYd == 5.f);
        CHECK(kHammerPct.normal == 20.f && kHammerPct.heroic == 30.f);
        CHECK(kHammerTargets.normal == 1 && kHammerTargets.heroic == 2);
        CHECK(kHammerStunMs == 2000);
        CHECK(kStormFirstMs == 12000 && kStormEveryMs == 15000 && kStormCastMs == 2000);
        CHECK(kStormRadiusYd.normal == 8.f && kStormRadiusYd.heroic == 10.f);
        CHECK(kStormPct.normal == 30.f && kStormPct.heroic == 45.f);
        CHECK(kStormTankPct.normal == 15.f && kStormTankPct.heroic == 25.f);
        CHECK(kChargeWarnMs == 2000 && kChargeWidthYd == 3.f && kChargePct == 45.f);
        CHECK(kReservePct == 50.f && kFallPct == 1.f);
        // Every avoidable hit under 50% carries Weakened (the C++ sets it); the heroic hits stay at 45% or less.
        CHECK(kFlamePct.heroic < 50.f && kStormPct.heroic < 50.f && kChargePct < 50.f && kHammerPct.heroic < 50.f);
        // The normal hits against their warnings (inside the 40% ladder).
        CHECK(kFlamePct.normal <= 40.f && kStormPct.normal <= 40.f && kHammerPct.normal <= 40.f);
        // Kill order: the healers, the Captain, the Wizards, the Monks, the Champions, then Mograine (0).
        CHECK(kChaplainPriority == kAbbotPriority);
        CHECK(kAbbotPriority > kCaptainPriority && kCaptainPriority > kWizardPriority
            && kWizardPriority > kMonkPriority && kMonkPriority > kChampionPriority && kChampionPriority > 0);
        CHECK(KillPriority(NPC_MOGRAINE) == 0);
        // The interrupt list's order: Greater Heal first (heroic: the expected kick), then the flame, then Fireball.
        CHECK(kGreaterHealKickPriority.normal > kFlameKickPriority && kFlameKickPriority > kFireballKickPriority);
        CHECK(kGreaterHealKickPriority.heroic > kGreaterHealKickPriority.normal);
    }

    std::map<std::uint32_t, int> Count(std::vector<Member> const& members)
    {
        std::map<std::uint32_t, int> out;
        for (Member const& m : members)
            ++out[m.entry];
        return out;
    }

    std::set<int> Arms(Company c, bool heroic)
    {
        std::set<int> out;
        for (Member const& m : Members(c, heroic))
            out.insert(static_cast<int>(m.arm));
        return out;
    }

    std::uint32_t CompanyHealth(Company c, bool heroic)
    {
        std::uint32_t sum = 0;
        for (Member const& m : Members(c, heroic))
            sum += (m.entry == NPC_SM_COMPANY_WIZARD || m.entry == NPC_SM_COMPANY_CHAPLAIN)
                ? kSmallMemberHealth(heroic) : kBigMemberHealth(heroic);
        return sum;
    }

    void TestCompanies()
    {
        // CATH "Companies": normal / heroic.
        auto guard = Count(Members(Company::ChapelGuard, false));
        CHECK(guard[NPC_SM_CHAPEL_GUARD_CHAMPION] == 2 && guard[NPC_SM_CAPTAIN_OF_THE_GUARD] == 1
            && guard[NPC_SM_COMPANY_CHAPLAIN] == 1 && guard.size() == 3);
        auto guardH = Count(Members(Company::ChapelGuard, true));
        CHECK(guardH[NPC_SM_CHAPEL_GUARD_CHAMPION] == 3 && guardH[NPC_SM_CAPTAIN_OF_THE_GUARD] == 1
            && guardH[NPC_SM_COMPANY_CHAPLAIN] == 1 && guardH.size() == 3);
        auto pyre = Count(Members(Company::PyreBrethren, false));
        CHECK(pyre[NPC_SM_COMPANY_MONK] == 2 && pyre[NPC_SM_COMPANY_WIZARD] == 2 && pyre.size() == 2);
        auto pyreH = Count(Members(Company::PyreBrethren, true));
        CHECK(pyreH[NPC_SM_COMPANY_MONK] == 2 && pyreH[NPC_SM_COMPANY_WIZARD] == 3 && pyreH.size() == 2);
        auto clergy = Count(Members(Company::Clergy, false));
        CHECK(clergy[NPC_SM_CHAPEL_GUARD_CHAMPION] == 1 && clergy[NPC_SM_COMPANY_CHAPLAIN] == 1
            && clergy[NPC_SM_COMPANY_ABBOT] == 2 && clergy.size() == 3);
        auto clergyH = Count(Members(Company::Clergy, true));
        CHECK(clergyH[NPC_SM_CHAPEL_GUARD_CHAMPION] == 2 && clergyH[NPC_SM_COMPANY_CHAPLAIN] == 1
            && clergyH[NPC_SM_COMPANY_ABBOT] == 2 && clergyH.size() == 3);
        // The Last Reserve is the heroic Chapel Guard.
        CHECK(Count(Members(Company::LastReserve, true)) == guardH);
        // Normal four a company, heroic five.
        for (Company c : { Company::ChapelGuard, Company::PyreBrethren, Company::Clergy })
        {
            CHECK(Members(c, false).size() == 4);
            CHECK(Members(c, true).size() == 5);
        }
        CHECK(Members(Company::LastReserve, true).size() == 5);
        // The arms: the Chapel Guard north, the Pyre Brethren south, the Clergy and the Reserve both.
        for (bool heroic : { false, true })
        {
            CHECK(Arms(Company::ChapelGuard, heroic) == std::set<int>{ 0 });
            CHECK(Arms(Company::PyreBrethren, heroic) == std::set<int>{ 1 });
            CHECK(Arms(Company::Clergy, heroic) == (std::set<int>{ 0, 1 }));
        }
        CHECK(Arms(Company::LastReserve, true) == (std::set<int>{ 0, 1 }));
        // At most five units at one arm end (the column fits).
        for (Company c : { Company::ChapelGuard, Company::PyreBrethren, Company::Clergy, Company::LastReserve })
            for (bool heroic : { false, true })
            {
                int perArm[2] = { 0, 0 };
                for (Member const& m : Members(c, heroic))
                    ++perArm[static_cast<int>(m.arm)];
                CHECK(perArm[0] <= 5 && perArm[1] <= 5);
            }
        // The total health (CATH "Tuning": Guard 15k, Pyre 14k, Clergy 15k = 44k; heroic 72k / 66k / 72k / 72k).
        CHECK(CompanyHealth(Company::ChapelGuard, false) == 15000);
        CHECK(CompanyHealth(Company::PyreBrethren, false) == 14000);
        CHECK(CompanyHealth(Company::Clergy, false) == 15000);
        CHECK(CompanyHealth(Company::ChapelGuard, true) == 72000);
        CHECK(CompanyHealth(Company::PyreBrethren, true) == 66000);
        CHECK(CompanyHealth(Company::Clergy, true) == 72000);
        CHECK(CompanyHealth(Company::LastReserve, true) == 72000);
        // LS6: only the heroic Chapel Guard's and the Reserve's Champions charge.
        CHECK(ChargesOnArrival(Company::ChapelGuard, NPC_SM_CHAPEL_GUARD_CHAMPION, true));
        CHECK(ChargesOnArrival(Company::LastReserve, NPC_SM_CHAPEL_GUARD_CHAMPION, true));
        CHECK(!ChargesOnArrival(Company::ChapelGuard, NPC_SM_CHAPEL_GUARD_CHAMPION, false));
        CHECK(!ChargesOnArrival(Company::Clergy, NPC_SM_CHAPEL_GUARD_CHAMPION, true));
        CHECK(!ChargesOnArrival(Company::ChapelGuard, NPC_SM_CAPTAIN_OF_THE_GUARD, true));
        CHECK(std::string(CompanyName(Company::ChapelGuard)) == "chapel-guard");
        CHECK(std::string(MemberName(NPC_SM_COMPANY_ABBOT)) == "abbot");
    }

    void TestCallClock()
    {
        std::uint32_t const every = kCallEveryMs.normal;
        // The first call is the stand's own (2 s after the door yell), never the clock's.
        CHECK(!NextCallDue(0, true, 0, 99999, every));
        // The current company fell: the next at once, whether it arrived or not.
        CHECK(NextCallDue(1, true, 0, 1000, every));
        CHECK(NextCallDue(2, true, 5000, 6000, every));
        // Alive: 30 s after its arrival (heroic 25 s), not before; never before it arrived.
        CHECK(!NextCallDue(1, false, 0, 100000, every));
        CHECK(!NextCallDue(1, false, 10000, 39999, every));
        CHECK(NextCallDue(1, false, 10000, 40000, every));
        CHECK(!NextCallDue(1, false, 10000, 34999, kCallEveryMs.heroic));
        CHECK(NextCallDue(1, false, 10000, 35000, kCallEveryMs.heroic));
        // Capped at three: no fourth by the clock (the Last Reserve is the heroic 50%'s).
        CHECK(!NextCallDue(3, true, 10000, 999999, every));
        CHECK(!NextCallDue(3, false, 10000, 999999, every));
        // The descent: all three called and fallen, and he is not fighting yet.
        CHECK(DescentDue(3, true, false));
        CHECK(!DescentDue(2, true, false));
        CHECK(!DescentDue(3, false, false));
        CHECK(!DescentDue(3, true, true));
        // LS7: heroic only, once, at 50%.
        CHECK(ReserveDue(true, false, 50.f));
        CHECK(ReserveDue(true, false, 12.f));
        CHECK(!ReserveDue(true, false, 50.1f));
        CHECK(!ReserveDue(false, false, 10.f));
        CHECK(!ReserveDue(true, true, 10.f));
        // The fall: at the floor, every company called and dead, no reserve pending.
        CHECK(FallAllowed(true, 3, false, false));
        CHECK(!FallAllowed(false, 3, false, false));
        CHECK(!FallAllowed(true, 2, false, false));     // an early pull: the companies still come
        CHECK(!FallAllowed(true, 3, true, false));
        CHECK(!FallAllowed(true, 3, false, true));      // heroic: the Last Reserve first
        // The wipe watch.
        CHECK(!WipeDue(kWipeGraceMs - 1));
        CHECK(WipeDue(kWipeGraceMs));
        // LS5 (R-2-CATH M-1): a broken Divine Storm wind-up takes its circle (and the tank hit) with it; no other
        // failed cast of his touches the storm.
        CHECK(StormCancelledBy(SPELL_LS_DIVINE_STORM_CAST));
        CHECK(!StormCancelledBy(SPELL_LS_DIVINE_STORM_HIT) && !StormCancelledBy(SPELL_LS_DIVINE_STORM_TANK));
        CHECK(!StormCancelledBy(SPELL_LS_HAMMER_THROW) && !StormCancelledBy(0));
    }

    void TestFloor()
    {
        // 1% of 55k is 550: he never drops below it.
        CHECK(FloorHealth(55000, kFallPct) == 550);
        CHECK(FloorHealth(250000, kFallPct) == 2500);
        CHECK(FloorHealth(50, kFallPct) == 1);
        CHECK(ClampToFloor(55000, 55000, 1000, kFallPct) == 1000);
        CHECK(ClampToFloor(1000, 55000, 1000, kFallPct) == 450);
        CHECK(ClampToFloor(550, 55000, 1000, kFallPct) == 0);
        CHECK(ClampToFloor(500, 55000, 1000, kFallPct) == 0);
        CHECK(ClampToFloor(551, 55000, 1, kFallPct) == 1);
        // Never lethal, whatever the hit: what is left is the floor or more (or the health he had, when below it).
        for (std::uint32_t health : { 1u, 549u, 550u, 551u, 20000u, 55000u })
            for (std::uint32_t damage : { 0u, 1u, 100u, 54999u, 4000000000u })
            {
                std::uint32_t const taken = ClampToFloor(health, 55000, damage, kFallPct);
                CHECK(taken <= damage);
                CHECK(health - taken >= std::min(health, 550u));
            }
    }

    void TestPicks()
    {
        // LS3: the most hurt living member below 100%.
        CHECK(MostHurt({}) == -1);
        CHECK(MostHurt({ { 100.f, true }, { 100.f, true } }) == -1);
        CHECK(MostHurt({ { 90.f, true }, { 40.f, true }, { 60.f, true } }) == 1);
        CHECK(MostHurt({ { 90.f, true }, { 10.f, false }, { 60.f, true } }) == 2);
        // The healer: the Chaplain of the Chapel Guard and the Reserve; the Clergy's Abbots in turn; none in the Pyre.
        std::vector<HealerCandidate> const guard{ { NPC_SM_COMPANY_CHAPLAIN, true } };
        CHECK(PickHealer(Company::ChapelGuard, guard, 0) == 0);
        CHECK(PickHealer(Company::LastReserve, guard, 7) == 0);
        CHECK(PickHealer(Company::ChapelGuard, { { NPC_SM_COMPANY_CHAPLAIN, false } }, 0) == -1);
        std::vector<HealerCandidate> const clergy{ { NPC_SM_COMPANY_CHAPLAIN, true }, { NPC_SM_COMPANY_ABBOT, true },
            { NPC_SM_COMPANY_ABBOT, true } };
        CHECK(PickHealer(Company::Clergy, clergy, 0) == 1);
        CHECK(PickHealer(Company::Clergy, clergy, 1) == 2);
        CHECK(PickHealer(Company::Clergy, clergy, 2) == 1);
        std::vector<HealerCandidate> const oneFree{ { NPC_SM_COMPANY_CHAPLAIN, true },
            { NPC_SM_COMPANY_ABBOT, false }, { NPC_SM_COMPANY_ABBOT, true } };
        CHECK(PickHealer(Company::Clergy, oneFree, 0) == 2);
        CHECK(PickHealer(Company::Clergy, oneFree, 1) == 2);
        CHECK(PickHealer(Company::Clergy, { { NPC_SM_COMPANY_CHAPLAIN, true } }, 0) == -1);  // the Chaplain shields
        CHECK(PickHealer(Company::PyreBrethren, clergy, 0) == -1);
        // The arrival: the nearest tank first, else the nearest player, within reach.
        CHECK(PickArrival({}) == -1);
        CHECK(PickArrival({ { 10.f, false }, { 30.f, true }, { 5.f, false } }) == 1);
        CHECK(PickArrival({ { 10.f, false }, { 3.f, false } }) == 1);
        CHECK(PickArrival({ { 40.f, true }, { 20.f, true } }) == 1);
        CHECK(PickArrival({ { kArriveRangeYd + 1.f, true }, { 20.f, false } }) == 1);
        CHECK(PickArrival({ { kArriveRangeYd + 1.f, false } }) == -1);
        // LS6: in sight only, a different player for each Champion while there are enough.
        auto first = [](std::size_t) { return std::size_t(0); };
        CHECK(ChargeTargets(3, { false, false }, first).empty());
        auto picks = ChargeTargets(3, { true, false, true, true }, first);
        CHECK(picks.size() == 3);
        CHECK(std::set<std::size_t>(picks.begin(), picks.end()).size() == 3);
        for (std::size_t p : picks)
            CHECK(p != 1);
        auto wrap = ChargeTargets(3, { false, true }, first);
        CHECK(wrap.size() == 3);
        for (std::size_t p : wrap)
            CHECK(p == 1);
        std::uint32_t seed = 7;
        auto lcg = [&seed](std::size_t n)
        {
            seed = seed * 1103515245u + 12345u;
            return static_cast<std::size_t>((seed >> 8) % n);
        };
        for (int round = 0; round < 50; ++round)
        {
            auto two = ChargeTargets(2, { true, true, true, false, true }, lcg);
            CHECK(two.size() == 2 && two[0] != two[1] && two[0] != 3 && two[1] != 3);
        }
        // LS4: the throw lands as the circle resolves.
        CHECK(HammerLaunchDelayMs(0.f) == kHammerWarnMs);
        CHECK(HammerLaunchDelayMs(20.f) == 1000);
        CHECK(HammerLaunchDelayMs(40.f) == 0);
        CHECK(HammerLaunchDelayMs(80.f) == 0);
    }

    void TestGeometry()
    {
        DungeonKit::Arena const floor = StandFloor();
        // S0's checks: the spawn and the body spot inside the stub's frame too.
        CHECK(LastStandArena().Contains(kMograineSpawn.XY(), kMograineSpawn.z));
        CHECK(ArenaFor(BOSS_LAST_STAND).Contains(kMograineBody.XY(), kMograineBody.z));
        // NM: the arm ends are 65-66 yd by the mesh from the crossing center (8.2 s at 8 yd/s); straight, a little
        // less.
        for (Point3 const& end : kArmEnds)
        {
            float const d = Dist(end.XY(), kCrossingCenter.XY());
            CHECK(d > 60.f && d < 66.f);
            CHECK(floor.Contains(end.XY(), end.z));
            CHECK(kCrossingBox.Contains(end.XY()));
        }
        CHECK(ArmEnd(Arm::North).y > kCrossingCenter.y && ArmEnd(Arm::South).y < kCrossingCenter.y);
        // The mouths: where the arms meet the crossing's center span (y 1366-1430), on the floor.
        for (Arm a : { Arm::North, Arm::South })
        {
            Point3 const mouth = ArmMouth(a);
            CHECK(floor.Contains(mouth.XY(), mouth.z));
            CHECK(Dist(mouth.XY(), ArmEnd(a).XY()) < 35.f);
            CHECK(Dist(mouth.XY(), kCrossingCenter.XY()) < 35.f);
        }
        // Every column spot is on the crossing's floor (five at most an arm).
        for (Arm a : { Arm::North, Arm::South })
            for (std::uint32_t i = 0; i < 5; ++i)
            {
                Point4 const s = ColumnSpot(a, i);
                CHECK(floor.Contains(s.XY(), s.z));
                CHECK(kCrossingBox.Contains(s.XY()));
                CHECK(Dist(s.XY(), ArmEnd(a).XY()) <= 2.5f * 4 + 2.f + 0.01f);
            }
        CHECK(Dist(ColumnSpot(Arm::North, 0).XY(), ColumnSpot(Arm::North, 1).XY()) > 2.f);
        // Mograine: his spawn [db] and his body spot on the platform, inside his leash floor; the Chapel Door and the
        // instance's crossing strip on the stand's zone (the wipe watch sees a player there); the crossing center too.
        CHECK(floor.Contains(kMograineSpawn.XY(), kMograineSpawn.z));
        CHECK(floor.Contains(kMograineBody.XY(), kMograineBody.z));
        CHECK(kPlatformBox.Contains(kMograineSpawn.XY()) && kPlatformBox.Contains(kMograineBody.XY()));
        CHECK(Dist(kMograineSpawn.XY(), kMograineBody.XY()) < 1.f);
        CHECK(floor.Contains(kWhitemaneVigil.XY(), kWhitemaneVigil.z));
        CHECK(InStandZone(kChapelDoor.XY(), kChapelDoor.z));
        CHECK(InStandZone({ kCrossingMinX, kCrossingMinY }, kCrossingMinZ + 2.f));
        CHECK(InStandZone({ kCrossingMaxX, kCrossingMaxY }, kCrossingMaxZ - 2.f));
        CHECK(floor.Contains(kCrossingCenter.XY(), kCrossingCenter.z));
        // The floor's boxes join: the landing meets the nave at the door line, the nave the crossing, the crossing the
        // platform.
        CHECK(kLandingBox.maxX == kNaveBox.minX && kNaveBox.maxX == kCrossingBox.minX
            && kCrossingBox.maxX == kPlatformBox.minX);
        // Whitemane's chamber and the garden are off the stand's floor (his leash never follows a group there).
        CHECK(!floor.Contains(kWhitemaneSpawn.XY(), kWhitemaneSpawn.z));
        CHECK(!floor.Contains(kThorneSpot.XY(), kThorneSpot.z));
        CHECK(!InStandZone(kThorneSpot.XY(), kThorneSpot.z));
        // The chest: on the platform, off the vigil and his body (it never stands under them), facing the nave.
        CHECK(kPlatformBox.Contains(kChestSpot.XY()));
        CHECK(floor.Contains(kChestSpot.XY(), kChestSpot.z));
        CHECK(Dist(kChestSpot.XY(), kMograineBody.XY()) > 5.f);
        CHECK(Dist(kChestSpot.XY(), kWhitemaneVigil.XY()) > 10.f);
        CHECK(std::fabs(kChestSpot.o - DungeonKit::kPi) < 0.01f);
        // The stock nave box of section 7 #19 A (x 1073-1172) lies inside the stand's zone.
        CHECK(InStandZone({ 1073.f, 1336.f }, 30.f) && InStandZone({ 1172.f, 1463.f }, 31.f));
    }

    void TestEquipment()
    {
        CHECK(EquipmentOf(NPC_SM_CAPTAIN_OF_THE_GUARD).mainHand == 1899);
        CHECK(EquipmentOf(NPC_SM_CAPTAIN_OF_THE_GUARD).offHand == 1984);
        CHECK(EquipmentOf(NPC_SM_CHAPEL_GUARD_CHAMPION).mainHand == 5491);
        CHECK(EquipmentOf(NPC_SM_COMPANY_MONK).mainHand == 0 && EquipmentOf(NPC_SM_COMPANY_MONK).offHand == 0);
        CHECK(EquipmentOf(NPC_SM_COMPANY_WIZARD).mainHand == 1907);
        CHECK(EquipmentOf(NPC_SM_COMPANY_CHAPLAIN).mainHand == 5291);
        CHECK(EquipmentOf(NPC_SM_COMPANY_ABBOT).mainHand == 5291);
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestStates();
    TestTuning();
    TestCompanies();
    TestCallClock();
    TestFloor();
    TestPicks();
    TestGeometry();
    TestEquipment();
    // Wave 2.
    CHECK(IsWave2Boss(BOSS_LAST_STAND));
    return Report("sm_last_stand_test");
}
