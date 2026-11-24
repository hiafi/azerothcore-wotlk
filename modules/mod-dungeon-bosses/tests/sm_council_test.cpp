// Host tests for CouncilLogic.h (D3: Azshir the Sleepless and the Fallen Champion, the council): the slice, the lawn
// spots and the arena, the seal cycle, the Last Vigil's raises and Grief, Holy Light's pick, Execution Sentence's
// burst, Avenger's Shield's chain and the cadence.
#include "CouncilLogic.h"
#include "check.h"
#include <cmath>

using namespace ScarletMonasteryRework;
using namespace SmCouncil;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation, below the slice's end.
    CHECK(kSpellsReservation.Contains(SmCouncil::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmCouncil::kSpellSlice.last));
    CHECK(SPELL_CV_HOLY_SHOCK == 212390);
    CHECK(kLastSpell == 212415);
    CHECK(kSpellSlice.Contains(kLastSpell));
    // The credit spell is the instance's, never one of ours.
    CHECK(!kSpellSlice.Contains(kSpellCouncilCredit));

    // Section 7 #18 A: both fight on the lawn disc, Azshir 3 yd behind the Champion (the Champion faces south).
    Arena const arena = FightArena();
    CHECK(arena.Contains(kCouncilLawn.XY(), kCouncilLawn.z));
    CHECK(arena.Contains(kChampionLawnSpot.XY(), kChampionLawnSpot.z));
    CHECK(arena.Contains(kAzshirLawnSpot.XY(), kAzshirLawnSpot.z));
    CHECK(Near(DungeonKit::Distance(kChampionLawnSpot.XY(), kAzshirLawnSpot.XY()), kAzshirBehindYd));
    // Behind: Azshir is opposite the Champion's facing.
    float const toAzshir = DungeonKit::BearingTo(kChampionLawnSpot.XY(), kAzshirLawnSpot.XY());
    CHECK(Near(std::fabs(std::remainder(toAzshir - kChampionLawnSpot.o, DungeonKit::kTwoPi)), DungeonKit::kPi));
    // Neither old spot is in the fight's frame (the grave's dais has no walk route; Azshir's post is 53 yd away).
    CHECK(!arena.Contains(kAzshirSpawn.XY(), kAzshirSpawn.z));
    // The lawn disc is the S0 leash frame's disc too (the shared arena keeps its extra regions until trimmed).
    CHECK(CouncilArena().Contains(kChampionLawnSpot.XY(), kChampionLawnSpot.z));
    CHECK(ArenaFor(BOSS_COUNCIL).Contains(kAzshirLawnSpot.XY(), kAzshirLawnSpot.z));
    // The crypt below (Thalnos) and its z 0 court are outside the frame.
    CHECK(!arena.Contains(kThalnosSpawn.XY(), kThalnosSpawn.z));
    CHECK(!arena.Contains({ 1788.5f, 1417.f }, 0.3f));
    // Holy Wrath's 10 yd ring around Azshir reaches the Champion's spot: the tank drags or parks him (CV4).
    CHECK(DungeonKit::Distance(kAzshirLawnSpot.XY(), kChampionLawnSpot.XY()) < kHolyWrathRadiusYd);
    // Exorcism's 40 yd line fits the disc's floor (NM: 48 yd free); the spot bounds sit inside the arena.
    CHECK(kExorcismLengthYd <= 2.f * kArenaRadiusYd);
    CHECK(kSpotBoundsYd < kArenaRadiusYd);
    // RF-1 m-4: the disc is cut at y 1317 on Ironspine's side (his yard's north edge): nothing of the frame is within
    // 31 yd of his home, the bots' 30 yd bounds stay inside the cut, and the rest of the disc keeps its 40 yd.
    CHECK(Near(kArenaSouthCutY, kIronspineYardNorthY));
    CHECK(kCouncilLawn.y - kArenaSouthCutY > kSpotBoundsYd);
    for (std::uint32_t i = 0; i < 360; ++i)
    {
        float const bearing = DungeonKit::kTwoPi * static_cast<float>(i) / 360.f;
        for (float r = 0.f; r <= kArenaRadiusYd + 1.f; r += 0.5f)
        {
            Vec2 const p = DungeonKit::Advance(kCouncilLawn.XY(), bearing, r);
            if (!arena.Contains(p, kCouncilLawn.z))
                continue;
            CHECK(p.y >= kArenaSouthCutY - 0.01f);
            CHECK(DungeonKit::Distance(p, kIronspineHome.XY()) > 31.f);
        }
    }
    CHECK(!arena.Contains({ kCouncilLawn.x, kArenaSouthCutY - 1.f }, kCouncilLawn.z));
    CHECK(arena.Contains({ kCouncilLawn.x, kArenaSouthCutY + 1.f }, kCouncilLawn.z));
    CHECK(arena.Contains({ kCouncilLawn.x, kCouncilLawn.y + kArenaRadiusYd - 1.f }, kCouncilLawn.z));
    CHECK(arena.Contains({ kCouncilLawn.x + kSpotBoundsYd, kCouncilLawn.y }, kCouncilLawn.z));
    CHECK(arena.Contains({ kCouncilLawn.x, kCouncilLawn.y - kSpotBoundsYd }, kCouncilLawn.z));
    // The shared guard's frame is the same cut disc.
    CHECK(!CouncilArena().Contains({ kCouncilLawn.x, kArenaSouthCutY - 1.f }, kCouncilLawn.z));
    CHECK(!IronspineArena().Contains({ kCouncilLawn.x, kArenaSouthCutY + 1.f }, kCouncilLawn.z));
    // Wave 1.
    CHECK(!IsWave2Boss(BOSS_COUNCIL));

    // CV6: Command, Righteousness, Justice, repeat; each seal its emote, aura and rider.
    CHECK(SealAt(0) == Seal::Command);
    CHECK(SealAt(1) == Seal::Righteousness);
    CHECK(SealAt(2) == Seal::Justice);
    CHECK(SealAt(3) == Seal::Command);
    CHECK(SealAt(7) == Seal::Righteousness);
    CHECK(SealEmote(Seal::Command) == EMOTE_CHAMPION_COMMAND);
    CHECK(SealEmote(Seal::Righteousness) == EMOTE_CHAMPION_RIGHTEOUSNESS);
    CHECK(SealEmote(Seal::Justice) == EMOTE_CHAMPION_JUSTICE);
    CHECK(SealAura(Seal::Command) == SPELL_CV_SEAL_OF_COMMAND);
    CHECK(SealAura(Seal::Righteousness) == SPELL_CV_SEAL_OF_RIGHTEOUSNESS);
    CHECK(SealAura(Seal::Justice) == SPELL_CV_SEAL_OF_JUSTICE);
    CHECK(RiderOf(Seal::Command) == Rider::None);
    CHECK(RiderOf(Seal::Righteousness) == Rider::Brand);
    CHECK(RiderOf(Seal::Justice) == Rider::Mark);
    // Normal: 20 s seals and 10 s Judgements: two spread rounds and two stacks a minute (the Judgement on a seal change
    // carries the new seal: the script changes the seal first).
    {
        std::uint32_t brands = 0;
        std::uint32_t marks = 0;
        for (std::uint32_t t = kJudgementFirstMs; t <= 60000; t += kJudgementEveryMs)
        {
            Rider const r = RiderOf(SealAt(t / kSealEveryMs(false)));
            brands += r == Rider::Brand ? 1 : 0;
            marks += r == Rider::Mark ? 1 : 0;
        }
        CHECK(brands == 2);
        CHECK(marks == 2);
    }
    CHECK(kSealEveryMs(false) == 20000 && kSealEveryMs(true) == 15000);
    CHECK(kBrandCount(false) == 2 && kBrandCount(true) == 3);

    // CV1: normal raises twice (40%, then 20%); heroic twice too at 50% (HANDOFF s10 add sizing C: the spec's
    // uncapped heroic raises capped at 2 per fight).
    CHECK(RaiseAllowed(false, 0));
    CHECK(RaiseAllowed(false, 1));
    CHECK(!RaiseAllowed(false, 2));
    CHECK(RaiseAllowed(true, 0));
    CHECK(RaiseAllowed(true, 1));
    CHECK(!RaiseAllowed(true, 2));
    CHECK(!RaiseAllowed(true, 40));
    CHECK(kMaxRaises(false) == 2 && kMaxRaises(true) == 2);
    CHECK(Near(RiseHealthPct(false, 1), 40.f));
    CHECK(Near(RiseHealthPct(false, 2), 20.f));
    CHECK(Near(RiseHealthPct(true, 1), 50.f));
    CHECK(Near(RiseHealthPct(true, 7), 50.f));
    // Grief: +20% a stack; five stacks on normal double his damage at 25 s.
    CHECK(Near(GriefDamageFactor(0), 1.f));
    CHECK(Near(GriefDamageFactor(1), 1.2f));
    CHECK(Near(GriefDamageFactor(kGriefMaxStacks(false)), 2.f));
    CHECK(kGriefMaxStacks(false) * kGriefEveryMs == 25000);
    CHECK(kGriefMaxStacks(true) > kGriefMaxStacks(false));
    // The channel is the window: the watchdog only settles after it.
    CHECK(kVigilChannelMs == 8000);
    CHECK(kVigilWatchdogMs > kVigilChannelMs);

    // CV3: the brother with the lower percent; the fallen Champion is never healed.
    CHECK(HolyLightTarget(30.f, 80.f, true) == Brother::Champion);
    CHECK(HolyLightTarget(80.f, 30.f, true) == Brother::Azshir);
    CHECK(HolyLightTarget(50.f, 50.f, true) == Brother::Champion);
    CHECK(HolyLightTarget(1.f, 90.f, false) == Brother::Azshir);
    CHECK(Near(kHolyLightHealPct(false), 10.f) && Near(kHolyLightHealPct(true), 25.f));
    CHECK(kHolyLightKickPriority(true) > kHolyLightKickPriority(false));

    // CV8: 10% + 5% a whole second; 50% at 8 s on its own; a miss is exactly the cap.
    CHECK(Near(ExecutionBurstPct(0, false), 10.f));
    CHECK(Near(ExecutionBurstPct(999, false), 10.f));
    CHECK(Near(ExecutionBurstPct(1000, false), 15.f));
    CHECK(Near(ExecutionBurstPct(3500, false), 25.f));
    CHECK(Near(ExecutionBurstPct(7999, false), 45.f));
    CHECK(Near(ExecutionBurstPct(20000, false), 50.f));
    CHECK(Near(ExecutionBurstPct(0, true), 50.f));
    CHECK(Near(ExecutionBurstPct(kExecutionMs, false), kExecutionFullPct));

    // CV5: the line's facing from Azshir through the spot; none on the same spot.
    {
        std::optional<float> const north = LineFacing({ 0.f, 0.f }, { 5.f, 0.f });
        CHECK(north && Near(*north, 0.f));
        std::optional<float> const west = LineFacing({ 0.f, 0.f }, { 0.f, 5.f });
        CHECK(west && Near(*west, DungeonKit::kPi / 2.f));
        CHECK(!LineFacing({ 1.f, 1.f }, { 1.f, 1.05f }));
    }

    // CV7: the chain bounces to the nearest unhit player within 8 yd of the last hit, up to the cap.
    {
        std::vector<Vec2> const pts{ { 0.f, 0.f }, { 5.f, 0.f }, { 9.f, 0.f }, { 30.f, 0.f }, { 3.f, 0.f } };
        std::vector<std::size_t> const three = ShieldChain(pts, 0, kShieldBounceYd, kShieldHits(false));
        CHECK(three.size() == 3);
        CHECK(three.size() == 3 && three[0] == 0 && three[1] == 4 && three[2] == 1);
        std::vector<std::size_t> const five = ShieldChain(pts, 0, kShieldBounceYd, kShieldHits(true));
        CHECK(five.size() == 4);        // 30 yd away is never reached
        CHECK(five.size() == 4 && five[3] == 2);
        std::vector<std::size_t> const lone = ShieldChain(pts, 3, kShieldBounceYd, kShieldHits(true));
        CHECK(lone.size() == 1 && lone[0] == 3);
        CHECK(ShieldChain(pts, 9, kShieldBounceYd, 3).empty());
        CHECK(ShieldChain(pts, 0, kShieldBounceYd, 0).empty());
    }
    CHECK(kShieldMinRangeYd > kShieldBounceYd);

    // Numbers: the spec's normal / heroic pairs.
    CHECK(Near(kHolyShockPct(false), 12.f) && Near(kHolyShockPct(true), 18.f));
    CHECK(Near(kHolyWrathPct(false), 35.f) && Near(kHolyWrathPct(true), 45.f));
    CHECK(Near(kExorcismPct(false), 35.f) && Near(kExorcismPct(true), 45.f));
    CHECK(Near(kJudgementTankPct(false), 25.f) && Near(kJudgementTankPct(true), 35.f));
    CHECK(Near(kCommandPct(false), 30.f) && Near(kCommandPct(true), 45.f));
    CHECK(Near(kRighteousnessPct(false), 35.f) && Near(kRighteousnessPct(true), 45.f));
    CHECK(Near(kJusticeTotalPct(false), 150.f) && Near(kJusticeTotalPct(true), 250.f));
    CHECK(Near(kJusticeShareCapPct(false), 75.f) && Near(kJusticeShareCapPct(true), 0.f));
    CHECK(Near(kShieldFirstPct(false), 20.f) && Near(kShieldFirstPct(true), 25.f));
    CHECK(Near(kShieldBouncePct(false), 30.f) && Near(kShieldBouncePct(true), 40.f));
    // Every hit stays inside the 40% ladder on normal (a lone Justice share capped at 75% over 5 s, a soak).
    for (float pct : { kHolyShockPct(false), kHolyWrathPct(false), kExorcismPct(false), kCommandPct(false),
        kRighteousnessPct(false), kShieldFirstPct(false), kShieldBouncePct(false) })
        CHECK(pct <= 40.f);
    // Heroic group hits stay under 50% so Weakened holds.
    for (float pct : { kHolyWrathPct(true), kExorcismPct(true), kCommandPct(true), kRighteousnessPct(true),
        kShieldBouncePct(true), kExecutionFullPct })
        CHECK(pct <= 50.f);

    // Cadence: from the planned time, skipping missed turns.
    CHECK(NextDue(8000, 12000, 8500) == 20000);
    CHECK(NextDue(8000, 12000, 21000) == 32000);
    CHECK(NextDue(8000, 12000, 20000) == 32000);
    CHECK(NextDue(0, 0, 5) == 0);

    return Report("sm_council_test");
}
