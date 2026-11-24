// Host tests for DoanHardModeLogic.h (D8H: Arcanist Doan's hard mode, the Kel'Thuzad Heresy).
#include "DoanHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <string>

using namespace ScarletMonasteryRework;
using namespace SmHeresy;

namespace
{
    float Dist(Point3 const& a, float x, float y)
    {
        return std::hypot(a.x - x, a.y - y);
    }

    bool Near(float a, float b, float tol)
    {
        return std::fabs(a - b) <= tol;
    }

    void TestSliceAndSlot()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 212710 && kSpellSlice.last == 212749);
        CHECK(SPELL_HERESY_ICY_DEATH == 212710);
        CHECK(SPELL_HERESY_AURA == 212711);
        CHECK(SPELL_HERESY_SHARD_WARD == 212712);
        CHECK(SPELL_HERESY_FISSURE == 212713);
        CHECK(SPELL_HERESY_FISSURE_LOOK == 212714);
        CHECK(SPELL_HERESY_RAISE_LOOK == 212715);
        CHECK(!SmDoan::kSpellSlice.Contains(SPELL_HERESY_ICY_DEATH));
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_HERESY));
        CHECK(!ArenaFor(BOSS_HERESY).Empty());
        CHECK(HardModeFlagData(BOSS_HERESY) == DATA_HARD_MODE_DOAN);
        // The ids S0 reserved for this WP.
        CHECK(NPC_SM_PHYLACTERY_SHARD == 300920);
        CHECK(NPC_SM_RISEN_PURGED == 300921);
        // Its fissure tag is not one of D8's.
        for (std::uint32_t const tag : { std::uint32_t(SmDoan::TAG_DN_DETONATION),
                 std::uint32_t(SmDoan::TAG_DN_EXPLOSION), std::uint32_t(SmDoan::TAG_DN_MARK),
                 std::uint32_t(SmDoan::TAG_DN_SCORCHED), std::uint32_t(SmDoan::TAG_DN_POOL) })
            CHECK(tag != TAG_HM_FISSURE);
        // Its texts are Doan's groups 2-3 (S0's range, D8's names).
        CHECK(SmDoan::SAY_HERESY == 2 && SmDoan::SAY_RISE_PURGED == 3);
    }

    void TestPages()
    {
        CHECK(kPageCount == 4);
        CHECK(kPages[0].entry == GO_SM_EVIDENCE_PAGE_1 && kPages[0].entry == 301320);
        CHECK(kPages[1].entry == GO_SM_EVIDENCE_PAGE_2 && kPages[1].entry == 301321);
        CHECK(kPages[2].entry == GO_SM_EVIDENCE_PAGE_3 && kPages[2].entry == 301322);
        CHECK(kPages[3].entry == GO_SM_EVIDENCE_PAGE_4 && kPages[3].entry == 301323);
        for (std::uint32_t i = 0; i < kPageCount; ++i)
        {
            CHECK(kPages[i].pageText == kPages[i].entry);
            CHECK(PageOf(kPages[i].entry) == i);
        }
        CHECK(PageOf(301319) == kPageCount);
        CHECK(PageOf(301324) == kPageCount);
        // Section 7 #27 A: page 1 the kennel hall's real north corner, page 3 the nook's floor, pages 2 and 4 kept.
        CHECK(Near(kPages[0].spot.x, 156.f, 0.01f) && Near(kPages[0].spot.y, -241.f, 0.01f)
            && Near(kPages[0].spot.z, 19.2f, 0.01f));
        CHECK(Dist(kPages[1].spot, 223.9f, -292.7f) <= 1.5f);           // the Large Solid Chest (75299, guid 11899)
        CHECK(Dist(kPages[1].spot, 223.9f, -292.7f) >= 1.0f);           // off it: a click never takes the chest
        CHECK(Near(kPages[2].spot.x, 276.2f, 0.01f) && Near(kPages[2].spot.y, -428.2f, 0.01f)
            && Near(kPages[2].spot.z, 18.7f, 0.01f));
        CHECK(Near(kPages[3].spot.x, 219.f, 0.01f) && Near(kPages[3].spot.y, -424.f, 0.01f));
        // Every page is in the Library (outside Doan's sealed chamber and arena).
        for (EvidencePage const& p : kPages)
        {
            CHECK(!SmDoan::InChamberOutline({ p.spot.x, p.spot.y }));
            CHECK(!DoanArena().Contains({ p.spot.x, p.spot.y }, p.spot.z));
        }
    }

    void TestPageRules()
    {
        std::uint32_t const states[] = { DungeonKit::State::NotStarted, DungeonKit::State::InProgress,
            DungeonKit::State::Fail, DungeonKit::State::Done };
        // The refusal agrees with the instance's own rule on every case.
        for (bool const heroic : { false, true })
            for (std::uint32_t const state : states)
                for (std::uint32_t mask = 0; mask <= kDoanPagesAll; ++mask)
                    for (std::uint32_t page = 0; page <= kPageCount; ++page)
                        CHECK((PageRefusalFor(heroic, state, mask, page) == PageRefusal::None)
                            == DoanPageAllowed(heroic, state, mask, page));
        CHECK(PageRefusalFor(false, DungeonKit::State::NotStarted, 0, 0) == PageRefusal::NotHeroic);
        CHECK(PageRefusalFor(true, DungeonKit::State::InProgress, 0, 0) == PageRefusal::DoanFighting);
        CHECK(PageRefusalFor(true, DungeonKit::State::Done, 0, 0) == PageRefusal::DoanDead);
        CHECK(PageRefusalFor(true, DungeonKit::State::NotStarted, 0b0100, 2) == PageRefusal::AlreadyRead);
        CHECK(PageRefusalFor(true, DungeonKit::State::Fail, 0b0100, 1) == PageRefusal::None);   // a wipe: read on
        CHECK(PageRefusalFor(true, DungeonKit::State::NotStarted, 0, 4) == PageRefusal::NotAPage);
        CHECK(PageRefusalNotice(PageRefusal::DoanFighting) != nullptr);
        CHECK(PageRefusalNotice(PageRefusal::AlreadyRead) == nullptr);
        CHECK(PageRefusalNotice(PageRefusal::None) == nullptr);
        // LIB "Text": the emote to the reader.
        CHECK(PageEmote(2) == "You have found evidence of heresy (2 of 4).");
        CHECK(PageEmote(4) == "You have found evidence of heresy (4 of 4).");
    }

    void TestTuning()
    {
        CHECK(kDoanHealth == 400000);
        CHECK(kDoanHealth > SmDoan::kDoanHealthHeroic);
        // The spec's 10k anchors and 25k shard on the spec's 8k heroic anchor; relative, so D8's retune (HANDOFF s10
        // option D: 5k) carries over: 6.25k anchors and a 15.6k shard.
        CHECK(HardModeAnchorHealth(8000) == 10000);
        CHECK(ShardHealth(HardModeAnchorHealth(8000)) == 25000);
        CHECK(SmDoan::kAnchorHealthHeroic == 5000);
        CHECK(HardModeAnchorHealth(SmDoan::kAnchorHealthHeroic) == 6250);
        CHECK(ShardHealth(HardModeAnchorHealth(SmDoan::kAnchorHealthHeroic)) == 15625);
        CHECK(HardModeAnchorHealth(4000) == 5000);
        CHECK(ShardHealth(5000) == 12500);
        // HM3 (F-1d n4): the shard takes the first free anchor spot, never one an anchor stands on.
        CHECK(ShardSpotIndex(0) == 0);
        CHECK(ShardSpotIndex(0b111) == 3);
        CHECK(ShardSpotIndex(0b1011) == 2);         // a refused summon left spot 2 free
        CHECK(ShardSpotIndex((1u << SmDoan::kAnchorSpotCount) - 1) == SmDoan::kAnchorSpotCount);
        for (std::uint32_t i = 0; i < SmDoan::kAnchorSpotCount; ++i)
            for (std::uint32_t j = i + 1; j < SmDoan::kAnchorSpotCount; ++j)
            {
                float const dx = SmDoan::kAnchorSpots[i].x - SmDoan::kAnchorSpots[j].x;
                float const dy = SmDoan::kAnchorSpots[i].y - SmDoan::kAnchorSpots[j].y;
                // "taken" reads one spot only: two spots are farther apart than twice the taken radius.
                CHECK(std::sqrt(dx * dx + dy * dy) > 2.f * kShardSpotTakenYd);
            }
        CHECK(kShardCrowdedStepYd > kShardSpotTakenYd);
        // DoanFight.h tuning: the hard mode's cadences against D8's heroic ones.
        CHECK(kBubbleEveryMs == 35000 && SmDoan::kBubbleBeat(true).everyMs == 30000);
        CHECK(kMarkEveryMs == 30000 && SmDoan::kMarkBeat(true).everyMs == 20000);
        CHECK(kPoolLifeMs == 0);
        CHECK(kDetonationPct == 200.f && SmDoan::kDetonationPct(true) == 130.f);
        // HM1 Icy Death: 8 s, 60% slow, 3% a second.
        CHECK(kIcyDeathMs == 8000 && kIcyDeathSlowPct == 60 && kIcyDeathTickMs == 1000 && kIcyDeathHundredths == 300);
    }

    void TestRiders()
    {
        CHECK(IcyDeathRides(RiddenHit::Explosion));
        CHECK(IcyDeathRides(RiddenHit::MarkBurst));
        CHECK(IcyDeathRides(RiddenHit::MarkSelf));
        CHECK(IcyDeathRides(RiddenHit::Pool));
        CHECK(IcyDeathRides(RiddenHit::Flamestrike));
        CHECK(!IcyDeathRides(RiddenHit::Scorched));
        CHECK(!IcyDeathRides(RiddenHit::Detonation));
    }

    void TestFissures()
    {
        CHECK(!FissuresStart(0));
        CHECK(FissuresStart(1));
        CHECK(!FissuresStart(2));
        CHECK(FissureHeld(true));
        CHECK(!FissureHeld(false));
        CHECK(kFissureEveryMs == 10000 && kFissureCount == 2 && kFissureWarnMs == 3000);
        CHECK(kFissureRadiusYd == 6.f && kFissurePct == 60.f);
        // A 3 s marker is the shared doc's 2 s warning bar for a 60% hit (heroic, ruling 54 (1)).
        CHECK(kFissureWarnMs >= 2000);
    }

    void TestRisen()
    {
        CHECK(!RisenRise(1));
        CHECK(RisenRise(2));
        CHECK(!RisenRise(3));
        CHECK(kRisenCount == 6 && kRisenSpots.size() == 6);
        CHECK(kRisenHealth == 6000);
        Point3 const doan{ 148.3f, -428.7f, 18.5f };                    // his spawn (guid 40124)
        Point3 const center = SmDoan::kChamberCenter;                  // where the tank holds him
        for (std::size_t i = 0; i < kRisenSpots.size(); ++i)
        {
            Point3 const& s = kRisenSpots[i];
            // On the chamber floor, along its south wall (low x), clear of the Strongbox corner (131.8, -432.6).
            CHECK(SmDoan::InChamberOutline({ s.x, s.y }));
            CHECK(DoanArena().Contains({ s.x, s.y }, s.z));
            CHECK(s.x < 140.f);
            CHECK(Dist(s, 131.8f, -432.6f) >= 4.f);
            // "A slow walk (about 10 s)": from the wall to him at the walk speed, his reach taken off.
            float const toSpawn = Dist(s, doan.x, doan.y) - kRisenReachYd;
            float const toCenter = Dist(s, center.x, center.y) - kRisenReachYd;
            CHECK(toSpawn / kRisenSpeedYdPerSec >= 6.f && toSpawn / kRisenSpeedYdPerSec <= 14.f);
            CHECK(toCenter / kRisenSpeedYdPerSec >= 3.f && toCenter / kRisenSpeedYdPerSec <= 12.f);
            for (std::size_t j = i + 1; j < kRisenSpots.size(); ++j)
                CHECK(Dist(s, kRisenSpots[j].x, kRisenSpots[j].y) >= 4.f);
        }
        // Arrival: within 3 yd of his edge.
        CHECK(RisenArrived(4.4f, 1.5f));
        CHECK(!RisenArrived(4.6f, 1.5f));
        CHECK(RisenArrived(0.f, 0.f));
    }

    // Rule 20: the hard mode bubble (4 anchors and the shard) inside D8's heroic bar (14 s, HANDOFF s10 option D; the
    // Heresy names no bar of its own). 4 x 6.25k + 15.6k = 40.6k is 10.8 s at the hard mode's effective 3,774 (3.2 s
    // left for walking) and 58 s at the bots' 700 (the bots still miss: designer question in the F-2w report).
    void TestWindow()
    {
        float const human = BubbleSeconds(kHardModeAnchors, SmDoan::kAnchorHealthHeroic, kEffectiveDpsHardMode);
        float const bots = BubbleSeconds(kHardModeAnchors, SmDoan::kAnchorHealthHeroic, kBotAddDps);
        float const bar = static_cast<float>(SmDoan::DetonationCastMsFor(true)) / 1000.f;
        CHECK(human > 10.7f && human < 10.8f);
        CHECK(bots > 57.9f && bots < 58.1f);
        CHECK(human < bar);                                 // the window closes for humans
        CHECK(bots > bar);                                  // and not for bots
        CHECK(BubbleSeconds(1, 1, 0) == 0.f);
    }
}

int main()
{
    TestSliceAndSlot();
    TestPages();
    TestPageRules();
    TestTuning();
    TestRiders();
    TestFissures();
    TestRisen();
    TestWindow();

    return Report("sm_doan_hard_mode_test");
}
