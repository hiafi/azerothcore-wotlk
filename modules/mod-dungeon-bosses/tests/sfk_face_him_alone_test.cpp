// Host tests for Arugal's hard mode "Face Him Alone" (WP-S10): FaceHimAloneLogic.h. The choice rule (heroic only,
// once, only before the fight), the gossip ids, the loot-mode arithmetic of the kill, and the build spec's hard mode
// budget (SK 1500-1509) on Arugal's real heroic numbers and timeline (ArugalLogic.h).
#include "FaceHimAloneLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstdio>
#include <cstring>

using namespace ShadowfangKeepRework;
using namespace FaceHimAlone;

namespace
{
    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    void TestSlice()
    {
        CHECK(kSpellsArugal.Contains(kSlice.first));
        CHECK(kSpellsArugal.Contains(kSlice.last));
        CHECK(kSlice.Size() == 5);
        // S9's ids stay below the slice (S9's last one is the 80+ tint).
        CHECK(!kSlice.Contains(Arugal::SPELL_ARUGAL_CURSE_TINT));
        CHECK(Arugal::SPELL_ARUGAL_CURSE_TINT < kSlice.first);
    }

    // Every condition met: the prisoner waits by the door on heroic, Arugal not pulled, nothing chosen yet.
    ChoiceInputs Ready()
    {
        ChoiceInputs in;
        in.instance = true;
        in.heroic = true;
        in.lairPrisoner = true;
        in.prisonerWaiting = true;
        in.chosen = false;
        in.arugal = Encounter::NotStarted;
        in.arugalFighting = false;
        in.playerAlive = true;
        return in;
    }

    void TestChoiceRule()
    {
        CHECK(CanChoose(Ready()) == Refusal::None);
        CHECK(Offered(Ready()));

        // Heroic only (empowered heroic runs on the heroic difficulty).
        ChoiceInputs in = Ready();
        in.heroic = false;
        CHECK(CanChoose(in) == Refusal::NotHeroic);
        CHECK(!Offered(in));

        // Once: a lit flag is never offered again.
        in = Ready();
        in.chosen = true;
        CHECK(CanChoose(in) == Refusal::AlreadyChosen);
        CHECK(!Offered(in));

        // Only before the fight: open on NOT_STARTED, FAIL and a fresh instance's TO_BE_DECIDED; shut while he fights
        // (IN_PROGRESS, SPECIAL, or in combat / evading by the creature itself) and once he is dead.
        for (Encounter open : { Encounter::NotStarted, Encounter::Fail, Encounter::ToBeDecided })
        {
            in = Ready();
            in.arugal = open;
            CHECK(CanChoose(in) == Refusal::None);
        }
        for (Encounter fighting : { Encounter::InProgress, Encounter::Special })
        {
            in = Ready();
            in.arugal = fighting;
            CHECK(CanChoose(in) == Refusal::ArugalFighting);
        }
        in = Ready();
        in.arugalFighting = true;
        CHECK(CanChoose(in) == Refusal::ArugalFighting);
        in = Ready();
        in.arugal = Encounter::Done;
        CHECK(CanChoose(in) == Refusal::ArugalDead);

        // The prisoner must be waiting by the door (stepping in, posted, leaving: no gossip flag).
        in = Ready();
        in.prisonerWaiting = false;
        CHECK(CanChoose(in) == Refusal::PrisonerBusy);
        in = Ready();
        in.lairPrisoner = false;
        CHECK(CanChoose(in) == Refusal::NotLairPrisoner);
        in = Ready();
        in.instance = false;
        CHECK(CanChoose(in) == Refusal::NoInstance);
        in = Ready();
        in.playerAlive = false;
        CHECK(CanChoose(in) == Refusal::PlayerDead);

        // Precedence: a normal map refuses before anything else about the encounter; a chosen flag before his state.
        in = Ready();
        in.heroic = false;
        in.chosen = true;
        in.arugal = Encounter::Done;
        CHECK(CanChoose(in) == Refusal::NotHeroic);
        in = Ready();
        in.chosen = true;
        in.arugal = Encounter::InProgress;
        CHECK(CanChoose(in) == Refusal::AlreadyChosen);

        // A stale menu after a wipe and a re-choice: the second select is refused.
        in = Ready();
        CHECK(CanChoose(in) == Refusal::None);
        in.chosen = true;                       // what the first select did
        in.arugal = Encounter::NotStarted;      // a wipe later
        CHECK(CanChoose(in) == Refusal::AlreadyChosen);

        // The player-facing refusals have a notice; the internal ones say nothing.
        for (Refusal r : { Refusal::AlreadyChosen, Refusal::ArugalDead, Refusal::ArugalFighting, Refusal::NotHeroic })
            CHECK(std::strlen(Notice(r)) > 0);
        for (Refusal r : { Refusal::None, Refusal::NoInstance, Refusal::NotLairPrisoner, Refusal::PrisonerBusy })
            CHECK(std::strlen(Notice(r)) == 0);
        for (Refusal r : { Refusal::None, Refusal::NoInstance, Refusal::NotLairPrisoner, Refusal::NotHeroic,
                 Refusal::AlreadyChosen, Refusal::ArugalDead, Refusal::ArugalFighting, Refusal::PrisonerBusy,
                 Refusal::PlayerDead })
            CHECK(std::strcmp(RefusalName(r), "?") != 0);
    }

    void TestGossip()
    {
        CHECK(std::strcmp(kOptionText, "Stay behind. We will face Arugal alone.") == 0);   // SK 1524
        CHECK(kOptionSender == 1);
        CHECK(kOptionAction == 1022);
        CHECK(DATA_HARD_MODE == 22);
        CHECK(SAY_PRISONER_HARD_MODE == 7);
        CHECK(std::strlen(kConfirmText) > 0);
    }

    void TestLoot()
    {
        // A normal kill (or a heroic one without the choice) rolls the default mode only: group 2 never rolls.
        CHECK(KillLootMode(false, false) == kLootModeDefault);
        CHECK(!RowRolls(kLootModeHardMode, KillLootMode(false, false)));
        // A hard mode kill rolls both bits: the hard mode group and his heroic list.
        CHECK(KillLootMode(true, false) == 3);
        CHECK(RowRolls(kLootModeHardMode, KillLootMode(true, false)));
        CHECK(RowRolls(kLootModeDefault, KillLootMode(true, false)));
        // Once DONE the bit is off again (nothing re-rolls a corpse).
        CHECK(KillLootMode(true, true) == kLootModeDefault);
        CHECK(kHardModeLootGroup == 2);
        CHECK(kArugalHeroicEntry == 310051);
        CHECK(kArugalHeroicEntry != NPC_ARUGAL);
    }

    // The build spec's arithmetic (SK 1500-1509), on Arugal's heroic numbers.
    void TestBudget()
    {
        // 30% of 405,840 is 121,752 (SK 1483).
        CHECK(MoonHealth() == 121752);

        // At about 3,850 group DPS the first 70% takes about 74 s and the seep alone puts everyone at about 25.
        float const toMoon = SecondsToMoon(3850.f);
        CHECK(Near(toMoon, 74.f, 0.5f));
        std::uint32_t const seep = SeepBeforeMoon(Ms(static_cast<std::int64_t>(toMoon * 1000.f)));
        CHECK(seep == 24);
        CHECK(SeepBeforeMoon(Ms(75000)) == 25);
        CHECK(SeepBeforeMoon(Ms(0)) == 0);

        // Non-tanks: three Curse casts (+10 each) among four players, about +7.5 each: about 32 at the moon, about 34 s
        // against a 31 s burn. One Thundershock failure (+15) costs 7.5 s of it.
        std::uint32_t const nonTank = seep + (3 * Arugal::kCurseCastStacks + 3) / 4;
        CHECK(nonTank == 32);
        CHECK(Near(MoonWindow(nonTank), 34.f, 0.01f));
        float const burn = BurnSeconds(3850.f);
        CHECK(Near(burn, 31.6f, 0.1f));
        CHECK(MoonWindow(nonTank) > burn);
        CHECK(Near(MoonWindow(nonTank) - MoonWindow(nonTank + Arugal::kThundershockStacks), 7.5f, 0.51f));
        CHECK(MoonWindow(nonTank + Arugal::kThundershockStacks) < burn);   // a failure there turns them first

        // The tank: under about 38 at the moon, so at most 4 Void Bolts (+3 each) may land.
        CHECK(LandedVoidBoltBudget(38, seep) == 4);
        CHECK(LandedVoidBoltBudget(20, seep) == 0);

        // At the hard mode DPS target (about 4,440 group DPS) the burn is about 27 s and non-tanks keep about 8 s.
        float const toMoonTarget = SecondsToMoon(4440.f);
        std::uint32_t const seepTarget = SeepBeforeMoon(Ms(static_cast<std::int64_t>(toMoonTarget * 1000.f)));
        std::uint32_t const nonTankTarget = seepTarget + (3 * Arugal::kCurseCastStacks + 3) / 4;
        float const margin = MoonWindow(nonTankTarget) - BurnSeconds(4440.f);
        CHECK(Near(BurnSeconds(4440.f), 27.4f, 0.1f));
        CHECK(margin >= 7.f && margin <= 10.f);

        // Every heroic number holds on hard mode (SK 1500): the moon's +2 every second, the curse at 100.
        CHECK(Arugal::kMoonSeepStacks == 2 && Arugal::kMoonSeepEvery == Ms(1000));
        CHECK(Arugal::kTurnAt == 100);
        CHECK(Arugal::kVoidBoltStacks == 3);
        CHECK(Arugal::kThundershockEvery(true) == Ms(5000));
        CHECK(Arugal::kCurseCastEvery(true) == Ms(20000));
        CHECK(Near(Arugal::kMoonrisePct, 30.f, 0.001f));
    }

    // Arugal's own heroic timeline (S9's Timeline and NextStep) over the first 70% at 3,850 DPS. SK 1505-1507 counts
    // "about 15" Void Bolts (one per 5 s cycle) and 11 to stop; the built timeline casts 11: each of the 4 Shadow Ports
    // (5 s, then every 20 s) takes its cycle's bolt (a bolt starts only when it ends before the next port), so the
    // group stops 7 of 11 (one about every 10 s). Pinned, so a timer retune shows here (reported to the designer).
    void TestVoidBoltsBeforeTheMoon()
    {
        using Arugal::Step;
        Arugal::Timeline t;
        t.Start(true);
        Ms const fight = Ms(static_cast<std::int64_t>(SecondsToMoon(3850.f) * 1000.f));
        Ms busyUntil{ 0 };
        std::uint32_t voidBolts = 0;
        std::uint32_t thundershocks = 0;
        for (Ms now{ 0 }; now <= fight; now += Ms(100))
        {
            if (now > Ms(0))
                t.Advance(Ms(100));
            if (t.Now() < busyUntil)
                continue;
            Ms length{ 0 };
            switch (Arugal::NextStep(t))
            {
                case Step::ShadowPort:
                    t.PortDone();
                    length = Arugal::kPortFlicker;
                    break;
                case Step::Thundershock:
                    t.ThundershockDone();
                    length = Arugal::kThundershockCast;
                    ++thundershocks;
                    break;
                case Step::VoidBolt:
                    length = Arugal::kVoidBoltCast;
                    ++voidBolts;
                    break;
                default:
                    continue;
            }
            busyUntil = t.Now() + length;
        }
        std::printf("hard mode: %u Void Bolts and %u Thundershocks in the first 70%% (%.1f s)\n", voidBolts,
            thundershocks, static_cast<double>(fight.count()) / 1000.0);
        CHECK(voidBolts == 11);
        CHECK(thundershocks == 14);
        std::uint32_t const mustStop = voidBolts - LandedVoidBoltBudget(38, SeepBeforeMoon(fight));
        CHECK(mustStop == 7);
        CHECK(mustStop > 0);    // Dungeon ruling 15: interrupts are required
    }
}

int main()
{
    TestSlice();
    TestChoiceRule();
    TestGossip();
    TestLoot();
    TestBudget();
    TestVoidBoltsBeforeTheMoon();
    return Report("sfk_face_him_alone_test");
}
