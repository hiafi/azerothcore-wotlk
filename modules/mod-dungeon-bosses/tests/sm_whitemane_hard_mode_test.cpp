// Host tests for WhitemaneHardModeLogic.h (D14H: High Inquisitor Whitemane's hard mode, The Truth): the slice and
// texts, the Torch's rule (section 7 #21 A), the places (section 7 #33 A), the phases' tuning, the father's judgment
// (the cycle, the Verdict's line to the floor's far edge, the light's circle), the picks and the rule 20 numbers.
#include "WhitemaneHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <optional>
#include <set>
#include <string>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmTheTruth;
using DungeonKit::State::Done;
using DungeonKit::State::Fail;
using DungeonKit::State::InProgress;
using DungeonKit::State::NotStarted;

namespace
{
    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    TextRange const* RangeOf(std::uint32_t entry)
    {
        for (TextRange const& t : kTextRanges)
            if (t.entry == entry)
                return &t;
        return nullptr;
    }

    void TestSliceAndIds()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation; 18 distinct ids, the first at its start.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 213190u && kSpellSlice.last == 213239u);
        std::uint32_t const ids[] = { SPELL_TT_TORCH_FEAR, SPELL_TT_TELEPORT_OUT, SPELL_TT_TELEPORT_IN, SPELL_TT_WARD,
            SPELL_TT_CURSE, SPELL_TT_CURSE_MARK, SPELL_TT_SHIELD, SPELL_TT_HEAL, SPELL_TT_SPIRIT_GLOW,
            SPELL_TT_LIGHT_CAST, SPELL_TT_LIGHT_HIT, SPELL_TT_LIGHT_PILLAR, SPELL_TT_VERDICT_RAISE,
            SPELL_TT_VERDICT_SWING, SPELL_TT_VERDICT_HIT, SPELL_TT_VERDICT_IMPACT, SPELL_TT_SHAME,
            SPELL_TT_SPIRIT_FADE };
        std::set<std::uint32_t> seen;
        for (std::size_t i = 0; i < sizeof(ids) / sizeof(ids[0]); ++i)
        {
            CHECK(ids[i] == kSpellSlice.first + i);
            CHECK(kSpellSlice.Contains(ids[i]));
            seen.insert(ids[i]);
        }
        CHECK(seen.size() == 18);
        CHECK(kLastSpell == kSpellSlice.first + 17);

        // The hard mode's kill slot is its own, fights in its boss's arena, and the instance owns its flag.
        CHECK(IsHardModeSlot(BOSS_THE_TRUTH));
        CHECK(!ArenaFor(BOSS_THE_TRUTH).Empty());
        CHECK(HardModeFlagData(BOSS_THE_TRUTH) == DATA_HARD_MODE_WHITEMANE);
        CHECK(HardModeBoss(BOSS_THE_TRUTH) == BOSS_WHITEMANE);

        // The units and objects (S0's header, FACTS-STOCK).
        CHECK(NPC_SM_VIGIL_FAIRBANKS == 300956u);
        CHECK(NPC_SM_ALEXANDROS_SPIRIT == 300957u);
        CHECK(NPC_FAIRBANKS == 4542u);
        CHECK(GO_TORCH == 97701u);
        CHECK(GO_SECRET_DOOR == 97700u);
        CHECK(kCreaturesWave2.Contains(NPC_SM_VIGIL_FAIRBANKS) && kCreaturesWave2.Contains(NPC_SM_ALEXANDROS_SPIRIT));

        // Section 7 #16 A: the Ashbringer event's friendly sweep leaves both new units out (S0's list).
        CHECK(!AshbringerSweeps(NPC_SM_VIGIL_FAIRBANKS));
        CHECK(!AshbringerSweeps(NPC_SM_ALEXANDROS_SPIRIT));

        // The registry tags stay clear of D14's 1-4 and are distinct.
        CHECK(TAG_TT_LIGHT > SmWhitemane::TAG_WM_SEARED_OFF);
        CHECK(TAG_TT_LIGHT != TAG_TT_LIGHT_TANK && TAG_TT_LIGHT_TANK != TAG_TT_VERDICT);
    }

    void TestTexts()
    {
        // The vigil Fairbanks's line 0 and the spirit's lines 0-1 are inside S0's ranges; the raid emote (2) is the
        // shared-file request (the spirit's range grows to 0-2): one past S0's end until it lands, inside after.
        TextRange const* fairbanks = RangeOf(NPC_SM_VIGIL_FAIRBANKS);
        CHECK(fairbanks && fairbanks->first <= SAY_FAIRBANKS_TRUTH && SAY_FAIRBANKS_TRUTH <= fairbanks->last);
        TextRange const* spirit = RangeOf(NPC_SM_ALEXANDROS_SPIRIT);
        CHECK(spirit && spirit->first <= SAY_SPIRIT_RENAULT && SAY_SPIRIT_FORGIVEN <= spirit->last);
        CHECK(spirit && EMOTE_SPIRIT_RAISES <= spirit->last + 1);
        // Whitemane's 6 is D14H's (D14 named it), inside her range and past her stock groups.
        TextRange const* whitemane = RangeOf(NPC_WHITEMANE);
        CHECK(SmWhitemane::SAY_WHITEMANE_LIES == 6);
        CHECK(whitemane && whitemane->firstNew <= 6 && 6 <= whitemane->last);
        // Mograine's 4-5 are his stock Ashbringer lines (below the first new group).
        TextRange const* mograine = RangeOf(NPC_MOGRAINE);
        CHECK(mograine && SAY_MOGRAINE_FATHER == 4 && SAY_MOGRAINE_FORGIVE == 5);
        CHECK(mograine && SAY_MOGRAINE_FORGIVE < mograine->firstNew);
    }

    void TestTorch()
    {
        // Section 7 #21 A: normal (or wave 2 unbound) as stock; heroic only once the Last Stand is DONE and before
        // Whitemane is pulled; a lit Torch does nothing more.
        CHECK(TorchAnswerFor(false, Done, NotStarted, false, true) == TorchAnswer::Stock);
        CHECK(TorchAnswerFor(false, NotStarted, NotStarted, false, true) == TorchAnswer::Stock);
        CHECK(TorchAnswerFor(true, Done, NotStarted, false, false) == TorchAnswer::Stock);   // unbound: as stock
        CHECK(TorchAnswerFor(true, Done, NotStarted, false, true) == TorchAnswer::Trigger);
        CHECK(TorchAnswerFor(true, Done, Fail, false, true) == TorchAnswer::Trigger);         // after a wipe
        CHECK(TorchAnswerFor(true, NotStarted, NotStarted, false, true) == TorchAnswer::Refused);
        CHECK(TorchAnswerFor(true, InProgress, NotStarted, false, true) == TorchAnswer::Refused);
        CHECK(TorchAnswerFor(true, Fail, NotStarted, false, true) == TorchAnswer::Refused);
        CHECK(TorchAnswerFor(true, Done, InProgress, false, true) == TorchAnswer::Refused);   // she is pulled
        CHECK(TorchAnswerFor(true, Done, Done, false, true) == TorchAnswer::Refused);         // she is dead
        CHECK(TorchAnswerFor(true, Done, NotStarted, true, true) == TorchAnswer::AlreadyLit);
        CHECK(TorchAnswerFor(true, Done, Done, true, true) == TorchAnswer::AlreadyLit);
        // The trigger answer is exactly the instance's own judge (S0's TorchAllowed).
        for (std::uint32_t ls : { NotStarted, InProgress, Done, Fail })
            for (std::uint32_t wm : { NotStarted, InProgress, Done, Fail })
                CHECK((TorchAnswerFor(true, ls, wm, false, true) == TorchAnswer::Trigger)
                    == TorchAllowed(true, ls, wm, false, true));
        CHECK(std::string(kTorchRefusedText) == "The Torch will not move.");
        CHECK(std::string(TorchAnswerName(TorchAnswer::Trigger)) == "trigger");

        // HM0: the fear takes everyone within 30 yd of the Secret Door (the Torch is 2 yd from it).
        CHECK(InFearRange(kSecretDoor.XY(), kSecretDoor.z));
        CHECK(InFearRange({ 1169.03f, 1345.63f }, 33.05f));                          // the Torch [db]
        CHECK(InFearRange({ kSecretDoor.x + 29.f, kSecretDoor.y }, kSecretDoor.z));
        CHECK(!InFearRange({ kSecretDoor.x + 31.f, kSecretDoor.y }, kSecretDoor.z));
        CHECK(!InFearRange(kSecretDoor.XY(), kSecretDoor.z + 12.f));
        CHECK(InFearRange(kFairbanksSpawn.XY(), kFairbanksSpawn.z));                 // his room
        // The vigil (45+ yd away) is out of the fear.
        CHECK(!InFearRange(kWhitemaneVigil.XY(), kWhitemaneVigil.z));
        CHECK(kFearMs == 5000 && kLeaveMs < kLeaveLookMs);
        CHECK(kLockoutRespawnSeconds >= 86400u);                                     // longer than any lockout
    }

    void TestPlaces()
    {
        // Section 7 #33 A: the vigil Fairbanks 4 yd beside her at the vigil, facing his body as she does.
        Point4 const vigil = SmWhitemane::VigilSpot();
        Point4 const beside = VigilFairbanksSpot();
        CHECK(Near(Distance2d(vigil.XY(), beside.XY()), 4.f, 0.01f));
        CHECK(Near(beside.o, vigil.o, 0.001f));
        CHECK(Near(beside.z, vigil.z, 0.001f));
        CHECK(SmTheTruth::OnFloorPlane(beside.XY()));
        CHECK(WhitemaneArena().Contains(beside.XY(), beside.z));
        // On the Secret Door's side (toward his room), clear of Mograine's body, the Last Stand's chest and the
        // crossing restart strip.
        CHECK(Distance2d(beside.XY(), kSecretDoor.XY()) < Distance2d(vigil.XY(), kSecretDoor.XY()));
        CHECK(Distance2d(beside.XY(), kMograineBody.XY()) > 5.f);
        CHECK(Distance2d(beside.XY(), { 1158.f, 1391.f }) > 5.f);
        CHECK(!InCrossingLine(beside.XY(), beside.z));
        // The spirit over the altar platform (1166, 1398), hovering above its top, facing the nave.
        SmWhitemane::Box const platform = SmWhitemane::kPlatformBox;
        CHECK(platform.Contains(kSpiritSpot.XY()));
        CHECK(Near(kSpiritSpot.x, 1166.f, 0.01f) && Near(kSpiritSpot.y, 1398.f, 0.01f));
        CHECK(kSpiritSpot.z > kPlatformTopZ && kSpiritSpot.z < kPlatformTopZ + 5.f);
        CHECK(Near(kSpiritSpot.o, DungeonKit::kPi, 0.001f));
        CHECK(kItemAlexandrosBlade == 22709u);
        CHECK(kItemFairbanksWeapon == 2182u);
    }

    void TestPhases()
    {
        // HM1 the ward: half while Fairbanks lives (phase 1 only).
        CHECK(WardActive(Phase::One) && !WardActive(Phase::Truth) && !WardActive(Phase::Two));
        CHECK(WardedDamage(100) == 50);
        CHECK(WardedDamage(101) == 51);
        CHECK(WardedDamage(1) == 1);
        CHECK(WardedDamage(0) == 0);

        // HM1d / HM4 through D14's tuning hooks.
        CHECK(!SaveWindowFor(Phase::One, true) && !SaveWindowFor(Phase::One, false));
        CHECK(SaveWindowFor(Phase::Two, true) == std::optional<std::uint32_t>(6000));
        CHECK(SaveWindowFor(Phase::Two, false) == std::optional<std::uint32_t>(4000));
        CHECK(SaveWindowFor(Phase::Truth, true) == std::optional<std::uint32_t>(6000));
        CHECK(LaneEveryFor(Phase::One) == std::optional<std::uint32_t>(20000));
        CHECK(!LaneEveryFor(Phase::Two) && !LaneEveryFor(Phase::Truth));             // back to heroic 25 s
        CHECK(FlameEveryFor(Phase::One) == std::optional<std::uint32_t>(8000));
        CHECK(!FlameEveryFor(Phase::Two));                                            // back to heroic 10 s
        CHECK(kSearedMs == 15000);
        CHECK(SmWhitemane::kLaneEveryMs == 25000 && SmWhitemane::kFlameEveryMs == 10000);
        // The hard mode windows are shorter than heroic's (8 s / 5 s): "her saves faster".
        CHECK(kHerSavePhaseTwoMs < SmWhitemane::kHerSaveMs.heroic);
        CHECK(kHisSavePhaseTwoMs < SmWhitemane::kHisSaveMs.heroic);
        CHECK(kStormEveryPhaseTwoMs < SmWhitemane::kStormEveryMs);

        // HM1 his kit, the spec's starting values.
        CHECK(kShieldFirstMs == 3000 && kShieldEveryMs == 12000 && Near(kShieldPct, 10.f, 0.001f));
        CHECK(kCurseFirstMs == 5000 && kCurseEveryMs == 15000 && kCurseMs == 12000 && Near(kCursePct, 4.f, 0.001f));
        CHECK(kCurseCastMs == 2000 && kCurseTickMs == 1000);
        CHECK(Near(kCursePct * static_cast<float>(kCurseMs / kCurseTickMs), 48.f, 0.01f));   // 48% if left
        CHECK(kHealFirstMs == 10000 && kHealEveryMs == 20000 && kHealCastMs == 3000 && kHealPct == 15);
        CHECK(kCurseEveryMs > kCurseMs);                                              // one curse at a time

        // The descriptor: Fairbanks above everything D14 lists.
        CHECK(kFairbanksTargetPriority > 3);
        CHECK(kFairbanksHealKickPriority == 3 && kCurseDispelPriority == 2 && kShieldPurgePriority == 2);

        // The health of the three.
        CHECK(kWhitemaneHealth == 340000 && kMograineHealth == 280000 && kFairbanksHealth == 130000);
        CHECK(kWhitemaneHealth > SmWhitemane::kWhitemaneHealth.heroic);
        CHECK(kMograineHealth > SmWhitemane::kMograineRisenHealth.heroic);

        // HM2: the transition, then the father from T + 8 s.
        CHECK(kTruthSecondLineMs < kTruthMs && kTruthMs < kSpiritFirstCastMs);
        CHECK(std::string(PhaseName(Phase::Truth)) == "truth");
    }

    void TestJudgment()
    {
        // Ruling 52: two lights, then the Verdict, every 8 s.
        Judgment const expected[] = { Judgment::Light, Judgment::Light, Judgment::Verdict, Judgment::Light,
            Judgment::Light, Judgment::Verdict, Judgment::Light };
        for (std::uint32_t n = 0; n < 7; ++n)
            CHECK(JudgmentFor(n) == expected[n]);
        CHECK(kJudgmentEveryMs * kVerdictEvery == 24000);                             // "every 24 s"
        // The first Verdict at T + 24 s.
        CHECK(kSpiritFirstCastMs + 2 * kJudgmentEveryMs == 24000);
        // Over the spec's 125 s phase 2: five Verdicts (ruling 53's math) and ten lights.
        std::uint32_t verdicts = 0;
        std::uint32_t lights = 0;
        std::uint32_t n = 0;
        for (std::uint32_t t = kSpiritFirstCastMs; t <= 125000; t += kJudgmentEveryMs, ++n)
            (JudgmentFor(n) == Judgment::Verdict ? verdicts : lights) += 1;
        CHECK(verdicts == 5);
        CHECK(lights == 10);

        // The light: 45% + Weakened, the tank 25% without; Renault 4% and 2 s; never over 75% (hub ruling 50).
        CHECK(Near(kLightPct, 45.f, 0.001f) && Near(kLightTankPct, 25.f, 0.001f));
        CHECK(Near(kLightRenaultPct, 4.f, 0.001f) && kLightKneelMs == 2000);
        CHECK(Near(kLightRadiusYd, 6.f, 0.001f) && kLightWarnMs == 2500);
        // The Verdict: 55% (no Weakened at 50% or more), Renault 6% and 3 s, Whitemane 5%.
        CHECK(Near(kVerdictPct, 55.f, 0.001f) && kVerdictPct >= 50.f && kVerdictPct <= 75.f);
        CHECK(Near(kVerdictRenaultPct, 6.f, 0.001f) && kVerdictKneelMs == 3000);
        CHECK(Near(kVerdictWhitemanePct, 5.f, 0.001f));
        CHECK(Near(kVerdictWidthYd, 6.f, 0.001f) && kVerdictWarnMs == 3500);
        // Ruling 53: the father's hits on Renault stay well under half his health over phase 2 (five Verdicts and four
        // landed lights: about 46%, the spec's "about 42%" with its 43% lure rate).
        CHECK(5.f * kVerdictRenaultPct + 4.f * kLightRenaultPct < 50.f);
        CHECK(std::string(JudgmentName(Judgment::Verdict)) == "verdict");
        // HM3 (R-2-CATH m-1): the tank in the light is Weakened too unless Renault stood in it ("players other than a
        // tank holding Renault in it").
        CHECK(!LightWeakensTank(true));
        CHECK(LightWeakensTank(false));
    }

    void TestVerdictLine()
    {
        Vec2 const spirit = kSpiritSpot.XY();
        // Through Renault at the vigil: west down the nave to its far wall (section 7 #33 A: about 94 yd).
        LinePath const nave = VerdictPathFor(spirit, kWhitemaneVigil.XY());
        CHECK(Near(nave.facing, DungeonKit::kPi, 0.01f));
        CHECK(nave.length > 88.f && nave.length < 95.f);
        CHECK(Near(nave.end.x, SmWhitemane::kNaveBox.minX + kVerdictInsetYd, 0.5f));
        CHECK(SmTheTruth::OnFloorPlane(nave.end));
        // Through his body on the platform: the same line (the body is on the nave's axis).
        LinePath const body = VerdictPathFor(spirit, kMograineBody.XY());
        CHECK(body.length > 88.f);
        CHECK(OnLine(kWhitemaneVigil.XY(), body, kVerdictWidthYd / 2.f));      // her vigil lies on it: aimable
        // Toward an arm: shorter, stopped at the floor's edge (section 7 #33 A: about 60 yd).
        LinePath const arm = VerdictPathFor(spirit, { 1146.f, 1420.f });
        CHECK(arm.length > 40.f && arm.length < 70.f);
        CHECK(SmTheTruth::OnFloorPlane(arm.end));
        CHECK(!SmTheTruth::OnFloorPlane(DungeonKit::Advance(arm.end, arm.facing, kVerdictInsetYd + 0.5f)));
        // A target on top of the spirit aims down the nave; a spirit off the floor draws nothing.
        CHECK(Near(VerdictPathFor(spirit, spirit).facing, DungeonKit::kPi, 0.001f));
        CHECK(VerdictPathFor({ 1300.f, 1398.f }, kWhitemaneVigil.XY()).length == 0.f);

        // Inside the line: 3 yd either side, along its length, never behind the spirit.
        CHECK(OnLine(kWhitemaneVigil.XY(), nave, 3.f));
        CHECK(OnLine({ 1120.f, 1400.9f }, nave, 3.f));
        CHECK(!OnLine({ 1120.f, 1401.2f }, nave, 3.f));
        CHECK(!OnLine({ 1170.f, 1398.f }, nave, 3.f));                          // behind the spirit
        CHECK(!OnLine({ nave.end.x - 2.f, 1398.f }, nave, 3.f));               // past the far end

        // The swing leaves so the blade crosses the line as it lands.
        CHECK(SwingLeadMs(0.f) == 0);
        CHECK(SwingLeadMs(60.f) == 1000);
        CHECK(SwingLeadMs(93.f) > 1500 && SwingLeadMs(93.f) < 1600);
        CHECK(SwingLeadMs(1000.f) == kVerdictWarnMs);

        // Whitemane in the line: while she stands or channels; never as a body.
        CHECK(VerdictTakesHer(PairStage::Alone) && VerdictTakesHer(PairStage::Pair));
        CHECK(VerdictTakesHer(PairStage::HerSave));                             // her save restarts (D14 BreakCast)
        CHECK(VerdictTakesHer(PairStage::HisDead));
        CHECK(!VerdictTakesHer(PairStage::HisSave) && !VerdictTakesHer(PairStage::HerSpent));
        CHECK(!VerdictTakesHer(PairStage::Over));
        // Renault kneels only when nothing else drives him.
        CHECK(KneelAllowed(false, false));
        CHECK(!KneelAllowed(true, false) && !KneelAllowed(false, true));
    }

    void TestLightCircle()
    {
        // The light's 6 yd circle with a 5 yd height band (the altar steps are 1.5-3.5 yd up).
        Vec2 const c{ 1140.f, 1398.f };
        CHECK(InCircle({ 1140.f, 1398.f }, 31.f, c, 31.f, kLightRadiusYd));
        CHECK(InCircle({ 1145.9f, 1398.f }, 31.f, c, 31.f, kLightRadiusYd));
        CHECK(!InCircle({ 1146.1f, 1398.f }, 31.f, c, 31.f, kLightRadiusYd));
        CHECK(InCircle({ 1142.f, 1398.f }, 34.f, c, 31.f, kLightRadiusYd));      // on the steps
        CHECK(!InCircle({ 1142.f, 1398.f }, 37.f, c, 31.f, kLightRadiusYd));
    }

    void TestPicks()
    {
        auto first = [](std::uint32_t) { return 0u; };
        auto last = [](std::uint32_t n) { return n ? n - 1 : 0u; };
        auto wild = [](std::uint32_t n) { return n + 7; };
        CHECK(!PickAny({}, first));
        std::vector<PlayerCandidate> c = { { 1, false, true }, { 2, true, false }, { 3, true, true }, { 4, true, true },
            { 5, false, false } };
        CHECK(PickAny(c, first) == std::optional<std::size_t>(2));
        CHECK(PickAny(c, last) == std::optional<std::size_t>(3));
        CHECK(PickAny(c, wild) == std::optional<std::size_t>(2));                // out of range: the first
        std::vector<PlayerCandidate> none = { { 1, false, true }, { 2, true, false } };
        CHECK(!PickAny(none, first));
    }

    void TestRule20()
    {
        // Fairbanks 130k: about 34 s at the spec's 3,774 (the hard mode math), about 69 s at the bots' half.
        CHECK(Near(KillSeconds(kFairbanksHealth, kSpecGroupDps), 34.4f, 0.2f));
        CHECK(Near(KillSeconds(kFairbanksHealth, kBotGroupDps), 68.9f, 0.3f));
        // Phase 2 windows (ruling 53): her 6 s channel asks her under about 6.7%; his 4 s, him under about 5.4%.
        CHECK(Near(SmWhitemane::WindowPct(kWhitemaneHealth, kHerSavePhaseTwoMs, kSpecGroupDps), 6.66f, 0.05f));
        CHECK(Near(SmWhitemane::WindowPct(kMograineHealth, kHisSavePhaseTwoMs, kSpecGroupDps), 5.39f, 0.05f));
        // Bots at about half: 3.3% and 2.7% (the kill-together's 10% band is wide for them: designer question).
        CHECK(Near(SmWhitemane::WindowPct(kWhitemaneHealth, kHerSavePhaseTwoMs, kBotGroupDps), 3.33f, 0.05f));
        CHECK(Near(SmWhitemane::WindowPct(kMograineHealth, kHisSavePhaseTwoMs, kBotGroupDps), 2.70f, 0.05f));
        // Phase 2 at the spec's DPS (468k of player damage needed, ruling 53): about 125 s.
        CHECK(Near(KillSeconds(468000, kSpecGroupDps), 124.f, 1.f));
    }
}

int main()
{
    TestSliceAndIds();
    TestTexts();
    TestTorch();
    TestPlaces();
    TestPhases();
    TestJudgment();
    TestVerdictLine();
    TestLightCircle();
    TestPicks();
    TestRule20();
    return Report("sm_whitemane_hard_mode_test");
}
