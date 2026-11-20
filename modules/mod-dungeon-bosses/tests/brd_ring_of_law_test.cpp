// Host tests for RingOfLawLogic.h (D4: the Ring of Law's frame, Grimstone and the waves).
// The slice, the binding switch and the texts; Crowd Favor's arithmetic, bands, cues and the banner; the run's steps;
// the wave table against the stock RingMobs and the build spec's health; the tuning table; the floor polygon against
// NM's bearing table and the DB's gate spots; Trial by Fire's wedges.
#include "RingOfLawLogic.h"
#include "check.h"
#include <cmath>
#include <optional>
#include <set>
#include <string>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdRingOfLaw;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float BearingDeg(Vec2 from, Vec2 to)
    {
        return Degrees(DungeonKit::BearingTo(from, to));
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, contiguous from its first id.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210810 && kSpellSlice.last == 210869);
        std::uint32_t const spells[] = { SPELL_RL_CROWD_FAVOR, SPELL_RL_CROWD_GIFT, SPELL_RL_ROAR_OF_THE_CROWD,
            SPELL_RL_GIFT_TOSS, SPELL_RL_JEER, SPELL_RL_JEER_BOTTLE, SPELL_RL_JEER_APPLE, SPELL_RL_JEER_BANANA,
            SPELL_RL_TRIAL_BY_FIRE, SPELL_RL_TRIAL_BY_FIRE_BAR, SPELL_RL_TRIAL_BURST, SPELL_RW_BURROW,
            SPELL_RW_BURROW_SINK, SPELL_RW_BURROW_ERUPT, SPELL_RW_TAIL_STING_BAR, SPELL_RW_TAIL_STING,
            SPELL_RW_TAIL_STING_POISON, SPELL_RW_SCREECH, SPELL_RW_THUNDERCLAP_BAR, SPELL_RW_THUNDERCLAP,
            SPELL_RW_THUNDERCLAP_SLOW, SPELL_RW_VENOM_SPIT, SPELL_RW_VENOM_SPIT_POOL, SPELL_RW_ACID_BURST,
            SPELL_RW_ACID_SWELL, SPELL_RW_ACID_BURST_LOOK, SPELL_RW_WORM_POISON, SPELL_RW_WORM_VENOM_SPIT,
            SPELL_RW_LIZARD_BOLT };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == SPELL_RW_LIZARD_BOLT);
        // No other WP's slice holds any of them.
        CHECK(!kSpellsRingChampions.Contains(kLastSpell) && !kSpellsGrebmar.Contains(kSpellSlice.first));
        // Bound together with ring_of_law.py and the SQL rev (the DT test pins the other two).
        CHECK(kBound);
    }

    void TestTexts()
    {
        // S0's range for 10096: 0-14, 0-5 stock.
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_GRIMSTONE)
            {
                found = true;
                CHECK(r.first == SAY_GRIM_RING_CENTER && r.last == kGrimstoneLastText && r.firstNew == 6);
            }
        CHECK(found);
        CHECK(kGrimstoneLastText == 14);
        // The stock groups keep their meaning (S1 "Text"): 4 start, 0 center, 1 wave, 5 gap, 2 challenger, 3 the win.
        CHECK(SAY_GRIM_SENTENCED == 4 && SAY_GRIM_RING_CENTER == 0 && SAY_GRIM_WAVE == 1 && SAY_GRIM_GAP == 5);
        CHECK(SAY_GRIM_FIRST_CHAMPION == 2 && SAY_GRIM_WON == 3);
        // The new ones.
        CHECK(SentenceText(Sentence::Fire) == 6 && SentenceText(Sentence::Beasts) == 7);
        CHECK(SentenceText(Sentence::Crowd) == 8);
        CHECK(SAY_GRIM_SECOND_CHAMPION == 9 && EMOTE_GRIM_BANNER == 10 && SAY_GRIM_BANNER_BURNED == 11);
        CHECK(SAY_GRIM_ENCORE == 12 && EMOTE_GRIM_ROAR == 13 && EMOTE_GRIM_JEER == 14);
        // The Sentence roll (DATA_RING_SENTENCE, 0-based).
        CHECK(SentenceOf(0) == Sentence::Fire && SentenceOf(1) == Sentence::Beasts && SentenceOf(2) == Sentence::Crowd);
        CHECK(SentenceOf(7) == Sentence::Fire);
    }

    void TestFavor()
    {
        // RL1: 0-10 from 5.
        CHECK(kFavorStart == 5 && kFavorMax == 10);
        CHECK(AfterResolve(5, 0, Sentence::Fire) == 6);        // clean: +1
        CHECK(AfterResolve(5, 1, Sentence::Fire) == 4);        // -1 per player hit
        CHECK(AfterResolve(5, 3, Sentence::Beasts) == 2);
        CHECK(AfterResolve(10, 0, Sentence::Fire) == 10);      // capped
        CHECK(AfterResolve(1, 5, Sentence::Fire) == 0);        // floored
        // RL6: the Crowd doubles every loss, never a gain.
        CHECK(AfterResolve(5, 1, Sentence::Crowd) == 3);
        CHECK(AfterResolve(5, 0, Sentence::Crowd) == 6);
        CHECK(AfterLoss(9, kFavorPerDeath, Sentence::Fire) == 6);      // a death: -3
        CHECK(AfterLoss(9, kFavorPerDeath, Sentence::Crowd) == 3);     // x2
        CHECK(AfterGain(4, kFavorWave) == 6);                           // the wave within 30 s: +2
        CHECK(AfterGain(9, kFavorWave) == 10);
        CHECK(ClampFavor(-4) == 0 && ClampFavor(42) == 10);
        // Bands: the gift at 8-10, Roar of the Crowd at 10, the jeers at 0-2 (the Crowd: always).
        CHECK(!Roars(7) && Roars(8) && Roars(10));
        CHECK(!RoarOfTheCrowd(9) && RoarOfTheCrowd(10));
        CHECK(Jeers(0, Sentence::Fire) && Jeers(2, Sentence::Beasts) && !Jeers(3, Sentence::Fire));
        for (std::uint32_t f = 0; f <= kFavorMax; ++f)
            CHECK(Jeers(f, Sentence::Crowd));
        // The emotes on crossing into a band, not on moving inside one.
        CHECK(CueFor(7, 8) == FavorCue::Roar && CueFor(5, 10) == FavorCue::Roar);
        CHECK(CueFor(8, 9) == FavorCue::None && CueFor(9, 7) == FavorCue::None);
        CHECK(CueFor(3, 2) == FavorCue::Jeer && CueFor(8, 0) == FavorCue::Jeer);
        CHECK(CueFor(2, 1) == FavorCue::None && CueFor(1, 3) == FavorCue::None);
        // EN1: the banner at 10, heroic only, once per run.
        CHECK(ThrowsBanner(10, true, false));
        CHECK(!ThrowsBanner(10, false, false));
        CHECK(!ThrowsBanner(10, true, true));
        CHECK(!ThrowsBanner(9, true, false));
        // The instance's own guard agrees (BlackrockDepthsRework.h).
        CHECK(BannerThrowAllowed(1, true, DungeonKit::State::InProgress));
        CHECK(!BannerThrowAllowed(1, false, DungeonKit::State::InProgress));
        CHECK(!BannerThrowAllowed(1, true, DungeonKit::State::Done));
        // RL2 / RL3 numbers (S1 frame, Build spec).
        CHECK(kGiftEveryMs == 15000 && Near(kGiftHealPct, 10.f) && kGiftMs == 10000 && kGiftDamagePct == 10);
        CHECK(kRoarDamagePct == 10);
        CHECK(kJeerEveryMs == 8000 && kJeerCount == 3 && Near(kJeerRadius, 3.f) && kJeerWarnMs == 1500);
        CHECK(Near(kJeerPct(false), 10.f) && Near(kJeerPct(true), 20.f));
        CHECK(kGiftFirstMs == kGiftEveryMs / 2 && kJeerFirstMs == kJeerEveryMs / 2);
    }

    void TestVolley()
    {
        // A volley of three: +1 only once, at its last circle, and only when none hit.
        VolleyJudge clean{ 3, 0, 0 };
        CHECK(!clean.Resolve(0));
        CHECK(!clean.Resolve(0));
        CHECK(clean.Resolve(0));
        VolleyJudge dirty{ 3, 0, 0 };
        CHECK(!dirty.Resolve(0));
        CHECK(!dirty.Resolve(2));
        CHECK(!dirty.Resolve(0));
        VolleyJudge none{};
        CHECK(!none.Resolve(0));       // nothing registered: never a gain
    }

    void TestRun()
    {
        // Ruling 25: wave -> gap -> challenger -> interlude -> title holder -> credit (or the Encore).
        CHECK(AfterKill(Step::Opener, false) == Step::Gap);
        // User ruling 2026-11-17: only a wipe in the beat or the Encore puts the banner out
        CHECK(WipeUnlightsBanner(Step::EncoreBeat) && WipeUnlightsBanner(Step::Encore));
        for (Step const s : { Step::Idle, Step::Entry, Step::Sentence, Step::ToCorner, Step::Opener, Step::Gap,
            Step::Challenger, Step::Interlude, Step::TitleHolder, Step::Done })
            CHECK(!WipeUnlightsBanner(s));
        CHECK(WipeUnlightsBanner(AfterKill(Step::TitleHolder, true)));
        CHECK(AfterKill(Step::Challenger, false) == Step::Interlude);
        CHECK(AfterKill(Step::TitleHolder, false) == Step::Done);
        CHECK(AfterKill(Step::TitleHolder, true) == Step::EncoreBeat);
        CHECK(AfterKill(Step::Encore, true) == Step::Done);
        CHECK(AfterKill(Step::Gap, true) == Step::Gap);
        // Trial by Beasts only while a champion (or the Encore) fights; Trial by Fire from the challenger to the credit.
        CHECK(ChampionFights(Step::Challenger) && ChampionFights(Step::TitleHolder) && ChampionFights(Step::Encore));
        CHECK(!ChampionFights(Step::Opener) && !ChampionFights(Step::Interlude) && !ChampionFights(Step::EncoreBeat));
        CHECK(FireRuns(Step::Challenger) && FireRuns(Step::Interlude) && FireRuns(Step::Encore));
        CHECK(!FireRuns(Step::Opener) && !FireRuns(Step::Gap) && !FireRuns(Step::Done));
        CHECK(FrameRuns(Step::Opener) && FrameRuns(Step::EncoreBeat) && !FrameRuns(Step::ToCorner));
        CHECK(!FrameRuns(Step::Done));
        CHECK(WipeWatched(Step::Entry) && WipeWatched(Step::Encore) && !WipeWatched(Step::Idle));
        CHECK(!WipeWatched(Step::Done));
        // The beats (rulings 25, 26, 30): 10 s gap, ~5 s interlude, 15 s Encore beat, +2 within 30 s.
        CHECK(kGapMs == 10000 && kInterludeMs == 5000 && kEncoreBeatMs == 15000 && kWaveFavorWindowMs == 30000);
        CHECK(kEastGateLeadMs < kGapMs);
        // The entry's fixed beats leave the ~20 s entry room for the two walks (25 yd and 30 yd at a walk).
        CHECK(kEntryFirstBeatMs + kSentenceDelayMs + kToCornerDelayMs + kWaveDelayMs <= 12000);
        for (Step s : { Step::Idle, Step::Entry, Step::Sentence, Step::ToCorner, Step::Opener, Step::Gap,
            Step::Challenger, Step::Interlude, Step::TitleHolder, Step::EncoreBeat, Step::Encore, Step::Done })
            CHECK(std::string(StepName(s)) != "?");
    }

    void TestWaves()
    {
        // The stock RingMobs order and amounts (BlackrockDepthsRework.h kRingWaveMobs / kRingWaveCounts).
        CHECK(kWaveTypes.size() == kRingWaveMobs.size());
        std::set<Signature> signatures;
        for (std::size_t i = 0; i < kWaveTypes.size(); ++i)
        {
            WaveKind const& w = kWaveTypes[i];
            CHECK(w.entry == kRingWaveMobs[i]);
            CHECK(w.count == kRingWaveCounts[i]);
            CHECK(WaveIndexOf(w.entry) == i);
            signatures.insert(w.signature);
            // Health: the template's level 51 value is the build spec's (ceil, as the core rounds).
            CHECK(static_cast<std::uint32_t>(std::ceil(kWaveBaseHealth * w.healthModifier)) == w.normalHealth);
            // Sized for a 25 s clear: about 53,000 a wave on normal, 83,000 on heroic (S1 Build spec).
            std::uint32_t const total = w.normalHealth * w.count;
            CHECK(total >= 50000 && total <= 56000);
            std::uint32_t const heroicTotal = w.heroicHealth * w.count;
            CHECK(heroicTotal >= 80000 && heroicTotal <= 86000);
            // The opening debuff is the stock one (none for a Trial by Beasts add: the script's rule).
            CHECK(w.openingDebuff != 0);
            // Every stock cast kept is a copy in the slice or one of the stock ids kept as is.
            for (StockCast const& c : w.casts)
                CHECK(c.spell == 0 || kSpellSlice.Contains(c.spell) || c.spell == SPELL_STOCK_CLEAVE
                    || c.spell == SPELL_STOCK_PIERCE_ARMOR);
        }
        CHECK(signatures.size() == 6);
        CHECK(!WaveIndexOf(NPC_GRIMSTONE));
        // Per S1: 3-mob waves 18k, Thundersnouts 26k, Beetles 9k (heroic 28k / 42k / 14k).
        CHECK(kWaveTypes[0].normalHealth == 18000 && kWaveTypes[3].normalHealth == 26000);
        CHECK(kWaveTypes[5].normalHealth == 9000 && kWaveTypes[5].heroicHealth == 14000);
        CHECK(kWaveTypes[3].heroicHealth == 42000 && kWaveTypes[1].heroicHealth == 28000);
        // Group signatures (one beast at a time, Grimstone's clock) and per-beast ones; first casts at half the cooldown.
        CHECK(kWaveTypes[0].signature == Signature::Burrow && !kWaveTypes[0].perBeast);
        CHECK(kWaveTypes[0].everyMs == 12000 && kWaveTypes[0].firstMs == 6000);
        CHECK(kWaveTypes[1].signature == Signature::TailSting && !kWaveTypes[1].perBeast);
        CHECK(kWaveTypes[1].everyMs == 10000 && kWaveTypes[1].firstMs == 5000);
        CHECK(kWaveTypes[2].signature == Signature::Screech && kWaveTypes[2].perBeast);
        CHECK(kWaveTypes[3].signature == Signature::Thunderclap && kWaveTypes[3].perBeast);
        CHECK(kWaveTypes[3].everyMs == 8000);                  // stock 8 s
        CHECK(kWaveTypes[4].signature == Signature::VenomSpit && !kWaveTypes[4].perBeast);
        CHECK(kWaveTypes[4].everyMs == 10000 && kWaveTypes[4].firstMs == 5000);
        CHECK(kWaveTypes[5].signature == Signature::AcidBurst && kWaveTypes[5].everyMs == 0);
        // Screeches stagger: three bats never open together.
        CHECK(FirstSignatureMs(kWaveTypes[2], 0) != FirstSignatureMs(kWaveTypes[2], 1));
        CHECK(FirstSignatureMs(kWaveTypes[0], 2) == kWaveTypes[0].firstMs);
        // The retired stock casts are gone (Sonic Burst 8281, Web 745, Thunderclap 15548).
        for (WaveKind const& w : kWaveTypes)
            for (StockCast const& c : w.casts)
                CHECK(c.spell != 8281 && c.spell != 745 && c.spell != 15548);
        // The wave stands in its stock row behind the south gate: outside the floor (it walks in).
        for (std::uint32_t i = 0; i < 6; ++i)
            CHECK(!OnFloorPlane(WaveSpawn(i).XY()));
        CHECK(Near(WaveSpawn(2).x - WaveSpawn(0).x, 0.8f));
    }

    void TestTuning()
    {
        // The build spec's N / H percents (S1 RW1-RW6, RL3, RL4; ruling 31).
        CHECK(Near(kBurrowPct(false), 25.f) && Near(kBurrowPct(true), 40.f) && Near(kBurrowRadius, 5.f));
        CHECK(kBurrowWarnMs == 2000);
        CHECK(Near(kTailStingPct(false), 20.f) && Near(kTailStingPct(true), 35.f) && kTailStingWarnMs == 2000);
        CHECK(Near(kTailStingRange, 15.f));
        CHECK(Near(kScreechPct(false), 10.f) && Near(kScreechPct(true), 15.f) && kScreechCastMs == 2000);
        CHECK(Near(kScreechRadius, 10.f) && kScreechSilenceMs == 2000);
        CHECK(Near(kThunderclapPct(false), 20.f) && Near(kThunderclapPct(true), 35.f));
        CHECK(Near(kThunderclapRadius, 10.f) && kThunderclapWarnMs == 2000);
        CHECK(Near(kVenomSpitPct(false), 4.f) && Near(kVenomSpitPct(true), 6.f) && Near(kVenomSpitRadius, 4.f));
        CHECK(kVenomSpitWarnMs == 1500 && kVenomSpitLifeMs == 12000 && kVenomSpitTickMs == 1000);
        // RW5: 1 to 2 pools down at once (S1): one spit every 10 s, each 13.5 s from its spit.
        CHECK((kVenomSpitWarnMs + kVenomSpitLifeMs + kWaveTypes[4].everyMs - 1) / kWaveTypes[4].everyMs <= 2);
        CHECK(Near(kAcidBurstPct(false), 15.f) && Near(kAcidBurstPct(true), 25.f) && Near(kAcidBurstRadius, 4.f));
        CHECK(kAcidSwellMs == 2000 && kAcidBodyHoldMs > kAcidSwellMs);   // the burst resolves before the body dies
        CHECK(Near(kTrialFirePct(false), 30.f) && Near(kTrialFirePct(true), 45.f));
        CHECK(kTrialFireEveryMs == 30000 && kTrialFireWarnMs == 3000 && Near(kTrialFireAngleDeg, 90.f));
        CHECK(kBeastsEveryMs == 20000 && kBeastsCap == 3);
        // Every heroic hit at least the normal one.
        for (NH<float> const& nh : { kJeerPct, kTrialFirePct, kBurrowPct, kTailStingPct, kTailStingPoisonPct,
            kScreechPct, kThunderclapPct, kVenomSpitPct, kAcidBurstPct, kWormPoisonPct, kWormVenomSpitPct,
            kLizardBoltPct })
            CHECK(nh(true) >= nh(false) && nh(false) > 0.f);
    }

    void TestFloor()
    {
        std::vector<Vec2> const floor = RingFloor();
        CHECK(floor.size() == kRingWall.size());
        // Bearings strictly increase around the ring.
        for (std::size_t i = 1; i < kRingWall.size(); ++i)
            CHECK(kRingWall[i].bearingDeg > kRingWall[i - 1].bearingDeg);
        Vec2 const c = kRingCenter.XY();
        // NM: 38-43 yd on the cardinals, 23-26 yd on the diagonals (+0.5 yd pad).
        for (float deg : { 45.f, 225.f, 235.f })
        {
            std::optional<float> const d = WallDistance(c, Radians(deg));
            CHECK(d && *d >= 23.f && *d <= 27.f);
        }
        for (float deg : { 0.f, 90.f, 300.f })
        {
            std::optional<float> const d = WallDistance(c, Radians(deg));
            CHECK(d && *d >= 35.f && *d <= 44.f);
        }
        // The floor's area is about NM's 3,800 sq yd (shoelace).
        double area = 0.0;
        for (std::size_t i = 0, j = floor.size() - 1; i < floor.size(); j = i++)
            area += double(floor[j].x) * floor[i].y - double(floor[i].x) * floor[j].y;
        area = std::fabs(area) / 2.0;
        CHECK(area > 3500.0 && area < 4300.0);
        // The gates [db]: each alcove sample sits on its gate's own bearing and distance.
        struct Gate
        {
            Vec2 at;
            float bearing;
        };
        for (Gate const& g : { Gate{ { 637.6f, -177.8f }, kEastGateBearingDeg },
            Gate{ { 585.7f, -147.8f }, kNorthGateBearingDeg }, Gate{ { 555.8f, -199.7f }, kWestGateBearingDeg },
            Gate{ { 607.7f, -229.7f }, kSouthGateBearingDeg } })
            CHECK(Near(BearingDeg(c, g.at), g.bearing, 0.6f));
        // Where things are: the center, AT 1526, Grimstone's summon, his two spots on the floor; the champions and
        // the wave behind their gates.
        CHECK(OnFloor(c, kRingCenter.z));
        CHECK(OnFloor(kRingAreaTrigger.XY(), -53.9f));
        CHECK(OnFloor(kGrimstoneSummon.XY(), kGrimstoneSummon.z));
        CHECK(OnFloor(kGrimstoneCenter.XY(), kGrimstoneCenter.z));
        CHECK(OnFloor(kGrimstoneCorner.XY(), kGrimstoneCorner.z));
        CHECK(WellInside(kGrimstoneCenter.XY(), 10.f));
        CHECK(!OnFloorPlane(kRingChampionSummon.XY()));
        CHECK(!OnFloorPlane(kRingWaveSummon.XY()));
        // R-1-RING MN-1: the opening debuff waits for the opener to be inside the floor (not in the south alcove)
        CHECK(!OpeningDebuffDue(true, WaveSpawn(0).XY()));
        CHECK(!OpeningDebuffDue(true, WaveSpawn(4).XY()));
        CHECK(OpeningDebuffDue(true, kGrimstoneCenter.XY()));
        CHECK(OpeningDebuffDue(true, c));
        CHECK(!OpeningDebuffDue(false, c));
        CHECK(!OnFloor(c, -36.f));                              // the gallery is not the floor
        CHECK(RingFloorArena().Contains(c, kRingCenter.z));
        CHECK(!RingFloorArena().Contains(kRingChampionSummon.XY(), kRingChampionSummon.z));
        // S0's stub frame still holds what it held.
        CHECK(RingOfLawArena().Contains(kGrimstoneSummon.P3().XY(), kGrimstoneSummon.P3().z));
        CHECK(ArenaFor(BOSS_RING_OF_LAW).Contains(kRingAreaTrigger.XY(), kRingAreaTrigger.z));
        // "To the wall": a line from the center through a point stops on the floor, short of the wall.
        std::optional<Vec2> const end = WallEnd(c, Vec2{ c.x + 5.f, c.y + 5.f });
        CHECK(end && OnFloorPlane(*end) && DungeonKit::Distance(c, *end) > 20.f);
        std::optional<Vec2> const toEast = WallEnd(c, Vec2{ c.x + 10.f, c.y });
        CHECK(toEast && DungeonKit::Distance(c, *toEast) > 35.f);
    }

    void TestTrialByFire()
    {
        // Four consecutive wedges turn a quarter clockwise each and cover the floor once.
        std::set<int> quadrants;
        for (std::uint32_t n = 0; n < 4; ++n)
        {
            float const f = WedgeFacing(1, n);
            quadrants.insert(static_cast<int>(std::lround(Degrees(f))) % 360);
            float const len = WedgeLength(f);
            CHECK(len >= 23.f && len <= kTrialFireMaxLength);
            std::vector<Vec2> const spots = WedgeBurstSpots(f, len);
            CHECK(spots.size() >= 3);
            for (Vec2 const& p : spots)
                CHECK(OnFloorPlane(p));
        }
        CHECK(quadrants.size() == 4);
        CHECK(Near(Degrees(WedgeFacing(0, 1)), 270.f, 0.1f));    // clockwise from north is toward the east (-y)
        CHECK(Near(Degrees(WedgeFacing(2, 0)), 180.f, 0.1f));
        CHECK(Near(WedgeFacing(3, 4), WedgeFacing(3, 0), 0.001f));
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestFavor();
    TestVolley();
    TestRun();
    TestWaves();
    TestTuning();
    TestFloor();
    TestTrialByFire();
    return Report("brd_ring_of_law_test");
}
