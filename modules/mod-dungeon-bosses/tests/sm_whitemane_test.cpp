// Host tests for WhitemaneLogic.h (D14: High Inquisitor Whitemane, with Mograine risen, "Till Death").
// The slice and the texts, the place (the vigil, the body, the floor, the arena), the build spec's numbers, the save
// rules both ways (normal's two-save cap, heroic uncapped, the pair's death, her real death last), the kill order by
// stage, Penance's picks (never the tank), the Vigil Flame's split, partner and carrier picks, a simulated flame loop
// (four, three and two non-tanks; the tank as the backup), Seared's fade against the flare, and rule 20's window
// numbers.
#include "WhitemaneLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <map>
#include <optional>
#include <set>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmWhitemane;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A deterministic "random" pick: always the first of the pool.
    std::uint32_t First(std::uint32_t /*n*/)
    {
        return 0;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 213150 && kSpellSlice.last == 213189);
        std::uint32_t const spells[] = { SPELL_WM_DEEP_SLEEP, SPELL_WM_RAISE, SPELL_WM_RESURRECTION,
            SPELL_WM_RISE_LOOK, SPELL_WM_LAY_ON_HANDS, SPELL_WM_LAY_ON_HANDS_LOOK, SPELL_WM_LANE_HIT,
            SPELL_WM_CHARGE_LOOK, SPELL_WM_BODY_SHIELD, SPELL_WM_PENANCE_MARK, SPELL_WM_PENANCE_HIT,
            SPELL_WM_PENANCE_STRIKE, SPELL_WM_PENANCE_PILLAR, SPELL_WM_PENANCE_HANDS, SPELL_WM_HEAL,
            SPELL_WM_POWER_WORD_SHIELD, SPELL_WM_HOLY_SMITE, SPELL_WM_VIGIL_FLAME, SPELL_WM_VIGIL_FLARE,
            SPELL_WM_SEARED, SPELL_WM_FLAME_PASS };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == expected - 1);
        // The retired stock casts are never ours: Dominate Mind 14515, the stock Heal 12039, Shield 22187, Smite 9481.
        for (std::uint32_t const stock : { 14515u, 12039u, 22187u, 9481u, 9256u, 9232u, 9257u })
            CHECK(!kSpellSlice.Contains(stock));
        // The hard mode's slice is D14H's, right after ours.
        CHECK(kSpellsTheTruth.first == kSpellSlice.last + 1);
        // Tags are distinct.
        std::set<std::uint32_t> const tags{ TAG_WM_LANE, TAG_WM_PENANCE, TAG_WM_FLAME, TAG_WM_SEARED_OFF };
        CHECK(tags.size() == 4);
    }

    void TestTexts()
    {
        TextRange const* her = nullptr;
        TextRange const* him = nullptr;
        for (TextRange const& r : kTextRanges)
        {
            if (r.entry == NPC_WHITEMANE)
                her = &r;
            if (r.entry == NPC_MOGRAINE)
                him = &r;
        }
        CHECK(her && him);
        if (!her || !him)
            return;
        // Hers: 0-2 stock (1 the kill line, 2 the rising), 3-5 and 7 new (D14), 6 D14H's.
        CHECK(her->firstNew == 3 && her->last == 7);
        for (std::uint8_t const g : { SAY_WHITEMANE_FALLEN, SAY_WHITEMANE_NOT_YET, SAY_WHITEMANE_TOGETHER,
                 EMOTE_WHITEMANE_FLAME })
            CHECK(g >= her->firstNew && g <= her->last);
        CHECK(SAY_WHITEMANE_KILL < her->firstNew && SAY_WHITEMANE_ARISE < her->firstNew);
        CHECK(SAY_WHITEMANE_LIES == 6);
        CHECK(kFirstOwnText == 3 && kLastOwnText == 7);
        // His: 2 stock ("At your side, milady!"), 12-13 D14's (D13 owns 7-11).
        CHECK(SAY_MOGRAINE_AT_YOUR_SIDE == 2 && SAY_MOGRAINE_AT_YOUR_SIDE < him->firstNew);
        CHECK(SAY_MOGRAINE_NOT_WHILE == 12 && SAY_MOGRAINE_MILADY == 13 && him->last == 13);
    }

    void TestPlace()
    {
        Point4 const v = VigilSpot();
        CHECK(Near(v.x, 1146.f) && Near(v.y, 1398.f) && Near(v.z, 32.1f));
        // She faces his body (north, a hair west): 0 < o < 0.1.
        CHECK(v.o > 0.f && v.o < 0.1f);
        CHECK(Near(FacingTo({ 0.f, 0.f }, { 1.f, 0.f }), 0.f));
        CHECK(Near(FacingTo({ 0.f, 0.f }, { 0.f, 1.f }), DungeonKit::kPi / 2.f));
        CHECK(Near(FacingTo({ 0.f, 0.f }, { 0.f, -1.f }), DungeonKit::kPi * 1.5f));
        // The vigil, his body and her chamber spawn are on her arena; the vigil and the body on the fight's floor.
        CHECK(WhitemaneArena().Contains(kWhitemaneVigil.XY(), kWhitemaneVigil.z));
        CHECK(WhitemaneArena().Contains(kMograineBody.XY(), kMograineBody.z));
        CHECK(WhitemaneArena().Contains(kWhitemaneSpawn.XY(), kWhitemaneSpawn.z));
        CHECK(ArenaFor(BOSS_WHITEMANE).Contains(kWhitemaneVigil.XY(), kWhitemaneVigil.z));
        CHECK(OnFloor(kWhitemaneVigil.XY(), kWhitemaneVigil.z));
        CHECK(OnFloor(kMograineBody.XY(), kMograineBody.z));
        CHECK(!OnFloor(kWhitemaneSpawn.XY(), kWhitemaneSpawn.z));      // her chamber is not the fight's floor
        CHECK(!OnFloor({ 1060.f, 1400.f }, 31.f));                       // the landing before the Chapel Door
        CHECK(!OnFloor(kMograineBody.XY(), 40.f));                       // the z band
        // The vigil is 8 yd from his body (section 7 #33 A).
        CHECK(Near(Distance2d(kWhitemaneVigil.XY(), kMograineBody.XY()), 8.01f, 0.05f));
        // Every floor box lies inside S0's arena box (the arena's first box: x 1072-1173, y 1330-1468).
        for (Box const& b : kFloorBoxes)
        {
            CHECK(WhitemaneArena().Contains({ b.minX + 0.5f, b.minY + 0.5f }, 31.f));
            CHECK(WhitemaneArena().Contains({ b.maxX - 0.5f, b.maxY - 0.5f }, 31.f));
        }
        // The rising: she kneels 2.5 yd short of him.
        Vec2 const raise = ShortOf(kWhitemaneVigil.XY(), kMograineBody.XY(), kRaiseStandoffYd);
        CHECK(Near(Distance2d(raise, kMograineBody.XY()), kRaiseStandoffYd, 0.01f));
        CHECK(Near(Distance2d(kWhitemaneVigil.XY(), raise) + kRaiseStandoffYd,
            Distance2d(kWhitemaneVigil.XY(), kMograineBody.XY()), 0.01f));
        // Already that close: where she stands.
        Vec2 const close = ShortOf({ 0.f, 0.f }, { 1.f, 0.f }, 2.f);
        CHECK(Near(close.x, 0.f) && Near(close.y, 0.f));
        CHECK(OnFloor(raise, kMograineBody.z));
    }

    void TestLaneGeometry()
    {
        // He arrives 3 yd from her on his side; the lane runs from him to there.
        Vec2 const her{ 1146.f, 1398.f };
        Vec2 const him{ 1146.f, 1420.f };
        Vec2 const end = LaneArrival(her, him);
        CHECK(Near(Distance2d(end, her), kLaneBesideYd));
        CHECK(Near(Distance2d(end, him), 22.f - kLaneBesideYd));
        CHECK(end.y > her.y);       // on his side
        // On top of her: her own spot; closer than 3 yd: his own spot.
        Vec2 const same = LaneArrival(her, her);
        CHECK(Near(same.x, her.x) && Near(same.y, her.y));
        Vec2 const near = LaneArrival(her, { 1146.f, 1400.f });
        CHECK(Near(near.y, 1400.f));
        // The charge at 30 yd/s: 19 yd = 633 ms.
        CHECK(ChargeFlightMs(19.f) == 633);
        CHECK(ChargeFlightMs(0.f) == 0 && ChargeFlightMs(-3.f) == 0);
        CHECK(kLaneMinYd > kLaneBesideYd);
    }

    void TestNumbers()
    {
        // Health (handoff 3.6): 50k / 220k her, 45k / 200k him at the rising; a save returns 50%.
        CHECK(kWhitemaneHealth(false) == 50000 && kWhitemaneHealth(true) == 220000);
        CHECK(kMograineRisenHealth(false) == 45000 && kMograineRisenHealth(true) == 200000);
        CHECK(Near(kSaveReturnPct, 50.f));
        // The normal template: 40.783 x 1,226 (the level 40 paladin base) = 50k.
        CHECK(std::fabs(std::ceil(40.783 * 1226.0) - 50000.0) <= 2.0);
        // WM1: P + 15 s, a 3 s sleep within 100 yd, a 2 s raise.
        CHECK(kRisingAtMs == 15000 && kDeepSleepMs == 3000 && Near(kDeepSleepRadiusYd, 100.f) && kRaiseCastMs == 2000);
        // WM1a / WM1b windows 10 / 8 s and 6 / 5 s; two saves each on normal, uncapped on heroic.
        CHECK(kHerSaveMs(false) == 10000 && kHerSaveMs(true) == 8000);
        CHECK(kHisSaveMs(false) == 6000 && kHisSaveMs(true) == 5000);
        CHECK(kSaveCap(false) == 2 && kSaveCap(true) == 0);
        // From R: Heal 5, Shield 8, Penance 10, Storm 12, the lane and the flame 20.
        CHECK(kHealFirstMs == 5000 && kShieldFirstMs == 8000 && kPenanceFirstMs == 10000);
        CHECK(kStormFromRisingMs == 12000 && kLaneFirstMs == 20000 && kFlameFirstMs == 20000);
        // Cadences: Heal 15, Shield 20, Penance 20, Storm 15, the lane 25, the flare 10, Seared 19.
        CHECK(kHealEveryMs == 15000 && kShieldEveryMs == 20000 && kPenanceEveryMs == 20000);
        CHECK(kStormEveryMs == 15000 && kLaneEveryMs == 25000 && kFlameEveryMs == 10000 && kSearedMs == 19000);
        // Damage (percent of the reference row).
        CHECK(Near(kLanePct(false), 30.f) && Near(kLanePct(true), 45.f));
        CHECK(Near(kPenanceMarkedPct(false), 20.f) && Near(kPenanceMarkedPct(true), 30.f));
        CHECK(Near(kPenanceOthersPct(false), 30.f) && Near(kPenanceOthersPct(true), 45.f));
        CHECK(kPenanceCount(false) == 2 && kPenanceCount(true) == 3);
        CHECK(Near(kSmitePct(false), 10.f) && Near(kSmitePct(true), 15.f));
        CHECK(Near(kFlareTotalPct, 110.f));
        // Heal 6% normal (hub ruling 54), 20% heroic; the shield 5% of his health.
        CHECK(kHealPct(false) == 6 && kHealPct(true) == 20 && Near(kShieldPct, 5.f));
        // Warnings: the lane 2 s, Penance 3 s; widths and radii.
        CHECK(kLaneWarnMs == 2000 && kPenanceWarnMs == 3000 && kHealCastMs == 3000 && kSmiteCastMs == 2500);
        CHECK(Near(kLaneWidthYd, 4.f) && Near(kPenanceRadiusYd, 6.f) && Near(kFlameRadiusYd, 6.f));
        // WM2a: 6 s, half to him.
        CHECK(kBodyShieldMs == 6000 && Near(kBodyShieldShare, 0.5f));
        // Gap 20: Holy Smite every 4 s when nothing else is casting.
        CHECK(kSmiteGapMs == 4000);
        // The interrupt list: Heal a reward on normal, expected on heroic, above Holy Smite.
        CHECK(kHealKickPriority(false) > kSmiteKickPriority && kHealKickPriority(true) > kHealKickPriority(false));
        CHECK(Near(kKillTogetherPct, 10.f));
    }

    void TestSaves()
    {
        std::uint8_t const normal = kSaveCap(false);
        std::uint8_t const heroic = kSaveCap(true);
        CHECK(SaveLeft(0, normal) && SaveLeft(1, normal) && !SaveLeft(2, normal) && !SaveLeft(5, normal));
        CHECK(SaveLeft(0, heroic) && SaveLeft(200, heroic));

        // His lethal hit.
        CHECK(OnHisLethal(PairStage::Pair, 0, normal) == Lethal::Save);
        CHECK(OnHisLethal(PairStage::Pair, 1, normal) == Lethal::Save);
        CHECK(OnHisLethal(PairStage::Pair, 2, normal) == Lethal::Through);   // her saves spent: he dies for real
        CHECK(OnHisLethal(PairStage::Pair, 50, heroic) == Lethal::Save);
        CHECK(OnHisLethal(PairStage::HerSave, 1, normal) == Lethal::Save);   // down: absorbed
        CHECK(OnHisLethal(PairStage::HisSave, 0, normal) == Lethal::PairDeath);
        CHECK(OnHisLethal(PairStage::HerSpent, 2, normal) == Lethal::PairDeath);
        CHECK(OnHisLethal(PairStage::HisDead, 2, normal) == Lethal::Through);

        // Her lethal hit.
        CHECK(OnHerLethal(PairStage::Pair, 0, normal, true) == Lethal::Save);
        CHECK(OnHerLethal(PairStage::Pair, 1, normal, true) == Lethal::Save);
        CHECK(OnHerLethal(PairStage::Pair, 2, normal, true) == Lethal::Spent);   // she lies; he fights alone
        CHECK(OnHerLethal(PairStage::Pair, 99, heroic, true) == Lethal::Save);
        CHECK(OnHerLethal(PairStage::Pair, 0, normal, false) == Lethal::Through);
        CHECK(OnHerLethal(PairStage::HerSave, 0, normal, false) == Lethal::PairDeath);
        CHECK(OnHerLethal(PairStage::HerSave, 0, heroic, false) == Lethal::PairDeath);
        CHECK(OnHerLethal(PairStage::HisDead, 2, normal, false) == Lethal::Through);
        CHECK(OnHerLethal(PairStage::Alone, 0, normal, false) == Lethal::PairDeath);
        CHECK(OnHerLethal(PairStage::Rising, 0, heroic, false) == Lethal::PairDeath);
        CHECK(OnHerLethal(PairStage::HisSave, 0, normal, true) == Lethal::Spent);
        CHECK(OnHerLethal(PairStage::HerSpent, 2, normal, true) == Lethal::Spent);

        // His real death: she follows him while she lies (his save, spent) or he was down over her save.
        CHECK(HisDeathEndsHer(PairStage::HisSave) && HisDeathEndsHer(PairStage::HerSpent));
        CHECK(HisDeathEndsHer(PairStage::HerSave));
        CHECK(!HisDeathEndsHer(PairStage::Pair) && !HisDeathEndsHer(PairStage::HisDead));

        // Her real death always comes last: no stage lets her die (Through) while he can still stand.
        for (PairStage const s : { PairStage::Alone, PairStage::Rising, PairStage::Pair, PairStage::HerSave,
                 PairStage::HisSave, PairStage::HerSpent })
            for (std::uint8_t used = 0; used < 4; ++used)
            {
                CHECK(OnHerLethal(s, used, normal, true) != Lethal::Through);
                CHECK(OnHerLethal(s, used, heroic, true) != Lethal::Through);
            }

        // A normal fight's longest path: she raises him twice, he lays hands on her twice, then the vow is spent.
        std::uint8_t her = 0;
        std::uint8_t his = 0;
        int herRaises = 0;
        int hisHands = 0;
        for (int round = 0; round < 6; ++round)
        {
            if (OnHisLethal(PairStage::Pair, her, normal) == Lethal::Save)
            {
                ++her;
                ++herRaises;
            }
            if (OnHerLethal(PairStage::Pair, his, normal, true) == Lethal::Save)
            {
                ++his;
                ++hisHands;
            }
        }
        CHECK(herRaises == 2 && hisHands == 2);
        CHECK(OnHisLethal(PairStage::Pair, her, normal) == Lethal::Through);
        CHECK(OnHerLethal(PairStage::Pair, his, normal, true) == Lethal::Spent);

        CHECK(LethalName(Lethal::PairDeath)[0] == 'p' && StageName(PairStage::HerSave)[0] == 'h');
        CHECK(StateName(WhitemaneState::Vigil)[0] == 'v');
    }

    void TestKillOrder()
    {
        KillOrder const pair = KillOrderFor(PairStage::Pair);
        CHECK(pair.together && pair.whitemane && pair.mograine && pair.tankOnMograine);
        // Her save: he is down; the channeler first.
        KillOrder const herSave = KillOrderFor(PairStage::HerSave);
        CHECK(!herSave.together && herSave.whitemane && !herSave.mograine);
        // His save: she is a body; the channeler first, the tank keeps him.
        KillOrder const hisSave = KillOrderFor(PairStage::HisSave);
        CHECK(!hisSave.together && !hisSave.whitemane && hisSave.mograine && hisSave.tankOnMograine);
        CHECK(KillOrderFor(PairStage::HerSpent).mograine && !KillOrderFor(PairStage::HerSpent).whitemane);
        CHECK(KillOrderFor(PairStage::HisDead).whitemane && !KillOrderFor(PairStage::HisDead).mograine);
        CHECK(KillOrderFor(PairStage::Alone).whitemane && !KillOrderFor(PairStage::Alone).mograine);
        KillOrder const over = KillOrderFor(PairStage::Over);
        CHECK(!over.whitemane && !over.mograine);
    }

    void TestPenance()
    {
        std::vector<PenanceCandidate> const group{ { 1, true, true }, { 2, false, true }, { 3, false, true },
            { 4, false, true }, { 5, false, false } };
        std::uint32_t seed = 0;
        auto rand = [&seed](std::uint32_t n) { return n ? (seed++ * 7u) % n : 0u; };
        for (int round = 0; round < 200; ++round)
            for (std::uint32_t count : { 2u, 3u })
            {
                std::vector<std::uint64_t> const picks = PickPenance(group, count, rand);
                CHECK(picks.size() == count);
                std::set<std::uint64_t> const unique(picks.begin(), picks.end());
                CHECK(unique.size() == picks.size());
                CHECK(!unique.count(1));        // never the tank
                CHECK(!unique.count(5));        // never the dead
            }
        // Fewer non-tanks than marks: as many as there are, still never the tank.
        std::vector<PenanceCandidate> const small{ { 1, true, true }, { 2, false, true } };
        std::vector<std::uint64_t> const picks = PickPenance(small, 3, First);
        CHECK(picks.size() == 1 && picks[0] == 2);
        CHECK(PickPenance(std::vector<PenanceCandidate>{ { 1, true, true } }, 2, First).empty());
    }

    void TestFlareSplit()
    {
        FlareShares const shared = FlareSplit(true, false, false);
        CHECK(Near(shared.carrierPct, 55.f) && Near(shared.partnerPct, 55.f));
        FlareShares const alone = FlareSplit(false, false, false);
        CHECK(Near(alone.carrierPct, 110.f) && Near(alone.partnerPct, 0.f));
        FlareShares const searedPartner = FlareSplit(true, false, true);
        CHECK(Near(searedPartner.carrierPct, 55.f) && Near(searedPartner.partnerPct, 110.f));
        FlareShares const searedCarrier = FlareSplit(true, true, false);
        CHECK(Near(searedCarrier.carrierPct, 110.f) && Near(searedCarrier.partnerPct, 55.f));
        // Lethal unshared or Seared (hub ruling 50): 110% of the row is more than a full health bar.
        CHECK(alone.carrierPct > 100.f && searedPartner.partnerPct > 100.f);
        CHECK(shared.carrierPct < 75.f);
    }

    void TestPartnerAndCarrier()
    {
        // The partner is the nearest living player within 6 yd, Seared or tank included.
        std::vector<FlameCandidate> others{ { 1, true, false, false, 7.f }, { 2, true, true, false, 3.f },
            { 3, true, false, true, 4.f }, { 4, false, false, false, 1.f } };
        std::optional<std::size_t> partner = FlarePartner(others);
        CHECK(partner && *partner == 1);                // the Seared one at 3 yd (it doubles)
        CHECK(!PartnerCarriesOn(others[*partner]));     // Seared: the flame cannot go to them
        others[1].distanceYd = 9.f;
        partner = FlarePartner(others);
        CHECK(partner && *partner == 2);                // the tank at 4 yd
        CHECK(PartnerCarriesOn(others[*partner]));
        others[2].distanceYd = 6.5f;
        partner = FlarePartner(others);
        CHECK(!partner);                                // nobody within 6 yd: unshared
        CHECK(FlarePartner({}) == std::nullopt);
        // The edge counts.
        CHECK(FlarePartner({ { 9, true, false, false, kFlameRadiusYd } }).has_value());

        // A fresh carrier: an unseared living non-tank; the tank only when no one else can.
        std::vector<FlameCandidate> pool{ { 1, true, false, true, 0.f }, { 2, true, true, false, 0.f },
            { 3, false, false, false, 0.f }, { 4, true, false, false, 0.f } };
        std::optional<std::size_t> pick = PickCarrier(pool, First);
        CHECK(pick && *pick == 3);
        pool[3].seared = true;
        pick = PickCarrier(pool, First);
        CHECK(pick && *pick == 0);                      // the tank, the backup
        pool[0].seared = true;
        CHECK(!PickCarrier(pool, First));
    }

    // The flame's loop over a group: every 10 s a flare, the partner the soak's pick (an unseared non-carrier, the
    // tank last), Seared 19 s. Returns the flares the tank had to share and the unshared or Seared hits.
    struct LoopResult
    {
        int tankShares = 0;
        int failures = 0;
    };

    LoopResult RunLoop(int nonTanks, std::uint32_t everyMs, std::uint32_t searedMs, int flares)
    {
        // ids 1..nonTanks are the non-tanks, 100 the tank.
        std::map<std::uint64_t, std::uint32_t> searedUntil;
        std::uint64_t carrier = 1;
        LoopResult out;
        std::uint32_t now = 0;
        for (int k = 0; k < flares; ++k, now += everyMs)
        {
            std::vector<std::uint64_t> ids;
            for (int i = 1; i <= nonTanks; ++i)
                ids.push_back(static_cast<std::uint64_t>(i));
            ids.push_back(100);
            auto seared = [&](std::uint64_t id) { return searedUntil.count(id) && searedUntil[id] > now; };
            // The soak's eligible claimer: an unseared non-carrier, non-tanks first, then the tank (roleLast); the
            // claimer stands within 6 yd, so the flare's partner is that claimer.
            std::optional<std::uint64_t> claimer;
            for (std::uint64_t id : ids)
                if (id != carrier && id != 100 && !seared(id) && !claimer)
                {
                    // the next in the loop: the lowest id after the carrier, wrapping
                    claimer = id;
                }
            std::optional<std::uint64_t> next;
            for (int step = 1; step <= nonTanks && !next; ++step)
            {
                std::uint64_t const id = static_cast<std::uint64_t>((static_cast<int>(carrier) - 1 + step) % nonTanks
                    + 1);
                if (id != carrier && !seared(id))
                    next = id;
            }
            if (next)
                claimer = next;
            if (!claimer && carrier != 100 && !seared(100))
            {
                claimer = 100;
                ++out.tankShares;
            }
            std::vector<FlameCandidate> others;
            for (std::uint64_t id : ids)
                if (id != carrier)
                    others.push_back({ id, true, seared(id), id == 100, id == *claimer ? 2.f : 20.f });
            std::optional<std::size_t> const partner = claimer ? FlarePartner(others) : std::nullopt;
            FlareShares const shares = FlareSplit(partner.has_value(), seared(carrier),
                partner && others[*partner].seared);
            if (shares.carrierPct > 100.f || shares.partnerPct > 100.f)
                ++out.failures;
            if (!partner)
                break;
            searedUntil[carrier] = now + searedMs;
            carrier = others[*partner].id;
        }
        return out;
    }

    void TestFlameLoop()
    {
        // WM5: four non-tanks loop with no tank and no failure (1+2, 2+3, 3+4 as 1's Seared fades, 4+1, ...).
        LoopResult const four = RunLoop(4, kFlameEveryMs, kSearedMs, 30);
        CHECK(four.tankShares == 0 && four.failures == 0);
        // Three still work (3 and 1 share as 1's Seared fades).
        LoopResult const three = RunLoop(3, kFlameEveryMs, kSearedMs, 30);
        CHECK(three.tankShares == 0 && three.failures == 0);
        // Two non-tanks: the tank must be the backup every other flare.
        LoopResult const two = RunLoop(2, kFlameEveryMs, kSearedMs, 30);
        CHECK(two.tankShares > 0 && two.failures == 0);
        // The Truth's phase 1: the flare every 8 s, Seared 15 s; the loop still runs with four.
        LoopResult const truth = RunLoop(4, 8000, 15000, 30);
        CHECK(truth.tankShares == 0 && truth.failures == 0);
        // Seared fades before the flare after next, and not before the next one.
        CHECK(SearedFadesInTime(kSearedMs, kFlameEveryMs));
        CHECK(SearedFadesInTime(15000, 8000));
        CHECK(!SearedFadesInTime(9000, 10000) && !SearedFadesInTime(21000, 10000));
    }

    void TestWindows()
    {
        // The spec's math (944 effective DPS on normal, 3,145 heroic): she must be under about 19% / 11% when he
        // falls, he under about 13% / 8% when she falls.
        CHECK(Near(WindowPct(kWhitemaneHealth(false), kHerSaveMs(false), 944.f), 18.88f, 0.05f));
        CHECK(Near(WindowPct(kWhitemaneHealth(true), kHerSaveMs(true), 3145.f), 11.44f, 0.05f));
        CHECK(Near(WindowPct(kMograineRisenHealth(false), kHisSaveMs(false), 944.f), 12.59f, 0.05f));
        CHECK(Near(WindowPct(kMograineRisenHealth(true), kHisSaveMs(true), 3145.f), 7.86f, 0.05f));
        // Rule 20, bots at about half: about 9.4% / 5.7% (her) and 6.3% / 3.9% (him).
        CHECK(Near(WindowPct(kWhitemaneHealth(false), kHerSaveMs(false), 472.f), 9.44f, 0.05f));
        CHECK(Near(WindowPct(kWhitemaneHealth(true), kHerSaveMs(true), 1572.f), 5.72f, 0.05f));
        CHECK(Near(WindowPct(kMograineRisenHealth(false), kHisSaveMs(false), 472.f), 6.29f, 0.05f));
        CHECK(Near(WindowPct(kMograineRisenHealth(true), kHisSaveMs(true), 1572.f), 3.93f, 0.05f));
        CHECK(WindowPct(0, 1000, 100.f) == 0.f);
        // The kill-together target keeps the pair within 10%: wider than any bot window, so a save or two happens
        // before the pair dies together (designer question in the report).
        CHECK(kKillTogetherPct > WindowPct(kWhitemaneHealth(false), kHerSaveMs(false), 472.f));
    }

    void TestStage()
    {
        CHECK(AtVigilForStage(CathedralStage::Vigil));
        CHECK(!AtVigilForStage(CathedralStage::BeforeStand) && !AtVigilForStage(CathedralStage::StandRunning));
        CHECK(!AtVigilForStage(CathedralStage::Done));
        // The instance's guard: her slot opens only after the Last Stand (wave 2 bound).
        CHECK(!WhitemaneWriteAccepted(DungeonKit::State::InProgress, DungeonKit::State::NotStarted, true));
        CHECK(WhitemaneWriteAccepted(DungeonKit::State::InProgress, DungeonKit::State::Done, true));
        CHECK(IsWave2Boss(BOSS_WHITEMANE));
        CHECK(HardModeKillSlot(BOSS_WHITEMANE) == BOSS_THE_TRUTH);
    }
}

namespace
{
    void TestHoldsAndOwner()
    {
        // The Truth's hold (R-2-CATH M-2): a flare due in or just after the hold comes kFlameRewarnMs after the release
        // (its soak registered again for then); a later one keeps its time; no flame, no flare.
        CHECK(kFlameRewarnMs == 3000);
        CHECK(FlareAfterHold(10000, 12000) == 15000);       // overdue by 2 s: 3 s from the release
        CHECK(FlareAfterHold(13000, 12000) == 15000);       // due in 1 s: still 3 s of marker
        CHECK(FlareAfterHold(20000, 12000) == 20000);       // due in 8 s: unchanged
        CHECK(FlareAfterHold(0, 12000) == 0);
        CHECK(kFlameRewarnMs < kFlameEveryMs && kFlameRewarnMs < 8000u);
        // The owner of her mechanics (R-2-CATH m-3): Mograine while risen and alive, down in her save included.
        CHECK(MograineOwnsMechanics(true, true));
        CHECK(!MograineOwnsMechanics(false, true));         // dead for good: hers
        CHECK(!MograineOwnsMechanics(true, false));         // lying at his body (before the rising, after a wipe)
        // A wipe after his real death respawns him for the next pull (R-2-CATH m-5); her death never does.
        CHECK(MograineRespawnsOnWipe(false, false));
        CHECK(!MograineRespawnsOnWipe(false, true));
        CHECK(!MograineRespawnsOnWipe(true, false));
        // With his object gone (corpse decayed or looted, dynamic respawn mode) the respawn goes by spawn id (RF-2 mi-3).
        CHECK(MograineRespawnRoute(false, true, false) == MograineRespawn::Object);
        CHECK(MograineRespawnRoute(false, false, false) == MograineRespawn::SpawnId);
        CHECK(MograineRespawnRoute(false, false, true) == MograineRespawn::SpawnId);   // no object: alive is unknowable
        CHECK(MograineRespawnRoute(false, true, true) == MograineRespawn::None);
        CHECK(MograineRespawnRoute(true, false, false) == MograineRespawn::None);
        CHECK(MograineRespawnRoute(true, true, false) == MograineRespawn::None);
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestPlace();
    TestLaneGeometry();
    TestNumbers();
    TestSaves();
    TestKillOrder();
    TestPenance();
    TestFlareSplit();
    TestPartnerAndCarrier();
    TestFlameLoop();
    TestWindows();
    TestStage();
    TestHoldsAndOwner();
    return Report("sm_whitemane_test");
}
