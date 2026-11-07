// Host tests for the shared kit's pure part: DeadminesKitMath.h (tuning pattern, reference health, geometry, the save
// string) and DeadminesRework.h (ids, slices, measured frames).
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace DeadminesKit;
using namespace DeadminesRework;

namespace
{
    float constexpr kPi = 3.14159265f;

    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    float Deg(float degrees)
    {
        return degrees * kPi / 180.f;
    }

    void TestTuningPattern()
    {
        NH<float> constexpr pct{ 20.f, 35.f };
        static_assert(pct.Get(false) == 20.f && pct.Get(true) == 35.f, "NH picks by difficulty at compile time");
        CHECK(pct(false) == 20.f);
        CHECK(pct(true) == 35.f);
        NH<int> constexpr ms{ 2500, 2000 };
        CHECK(ms(true) == 2000);
    }

    void TestRefFlat()
    {
        // Live rows (conf/mod_boss_mechanics.conf.dist): normal 20:1300:1290, heroic 60h:4120:4110.
        CHECK(RefFlatValue(1300, 1290, 15.f, false) == 195u);
        CHECK(RefFlatValue(4120, 4110, 15.f, false) == 618u);
        CHECK(RefFlatValue(1300, 1290, 30.f, true) == 387u);
        CHECK(RefFlatValue(4120, 4110, 40.f, false) == 1648u);
        CHECK(RefFlatValue(1300, 1290, 0.f, false) == 0u);
        CHECK(RefFlatValue(1300, 1290, -5.f, false) == 0u);
        CHECK(RefFlatValue(1300, 1290, 20.f, false) == 260u);
        CHECK(RefFlatValue(0, 0, 50.f, true) == 0u);
    }

    void TestGeometry()
    {
        std::array<Vec2, 4> constexpr square{ { { 0.f, 0.f }, { 10.f, 0.f }, { 10.f, 10.f }, { 0.f, 10.f } } };
        CHECK(PointInPolygon(square, { 5.f, 5.f }));
        CHECK(!PointInPolygon(square, { 15.f, 5.f }));
        CHECK(!PointInPolygon(square, { -1.f, -1.f }));
        auto const hit = RayToPolygonEdge(square, { 5.f, 5.f }, 0.f);
        CHECK(hit && Near(*hit, 5.f, 1e-3f));
        auto const diagonal = RayToPolygonEdge(square, { 5.f, 5.f }, kPi / 4.f);
        CHECK(diagonal && Near(*diagonal, std::sqrt(50.f), 1e-3f));
        CHECK(!RayToPolygonEdge(square, { 20.f, 5.f }, 0.f));     // outside, looking away
        CHECK(Near(BearingTo({ 0.f, 0.f }, { 0.f, 1.f }), kPi / 2.f, 1e-5f));
        CHECK(Near(BearingTo({ 0.f, 0.f }, { 0.f, -1.f }), 3.f * kPi / 2.f, 1e-5f));
        Vec2 const p = Advance({ 1.f, 1.f }, kPi, 2.f);
        CHECK(Near(p.x, -1.f, 1e-5f) && Near(p.y, 1.f, 1e-5f));
        auto const end = LaneEndAtWall(square, { 5.f, 5.f }, { 7.f, 5.f }, 0.5f);
        CHECK(end && Near(end->x, 9.5f, 1e-3f) && Near(end->y, 5.f, 1e-3f));
        Box2 constexpr box{ -1.f, 1.f, -2.f, 2.f };
        CHECK(box.Contains({ 0.f, 0.f }) && !box.Contains({ 0.f, 3.f }));
    }

    // Gilnid's foundry (handoff section 3.8, NAVMESH-REPORT section 1): the polygon matches the measured rays.
    void TestFoundry()
    {
        CHECK(PointInPolygon(kFoundryWalls, kGilnidSpawn));
        CHECK(PointInPolygon(kFoundryWalls, kPotCenter));
        CHECK(kPotBlock.Contains(kPotCenter));
        for (Vec2 const pot : kPots)
        {
            CHECK(PointInPolygon(kFoundryWalls, pot));
            // the navmesh hole is the pot block; the pots stand on its rim (within 1 yd of it)
            Box2 const rim{ kPotBlock.minX - 1.f, kPotBlock.maxX + 1.f, kPotBlock.minY - 1.f, kPotBlock.maxY + 1.f };
            CHECK(rim.Contains(pot));
            CHECK(Distance(pot, kPotCenter) < 5.f);
        }
        CHECK(!kPotBlock.Contains(kGilnidSpawn));
        // pots to Gilnid: 28.7 yd on a bearing of about 9.6 deg; the lane through him meets the wall at 36.0 yd
        CHECK(Near(Distance(kPotCenter, kGilnidSpawn), 28.7f, 0.2f));
        CHECK(Near(BearingTo(kPotCenter, kGilnidSpawn), Deg(9.6f), Deg(0.5f)));
        auto const throughGilnid = RayToPolygonEdge(kFoundryWalls, kPotCenter, BearingTo(kPotCenter, kGilnidSpawn));
        CHECK(throughGilnid && Near(*throughGilnid, 36.0f, 1.0f));
        // lanes aimed north through west: 34 to 37.5 yd; east or south: 8 to 17 yd
        for (float degrees : { 0.f, 15.f, 30.f, 45.f, 60.f, 75.f, 90.f })
        {
            auto const d = RayToPolygonEdge(kFoundryWalls, kPotCenter, Deg(degrees));
            CHECK(d && *d >= 33.5f && *d <= 38.f);
        }
        for (float degrees : { 180.f, 270.f, 300.f })
        {
            auto const d = RayToPolygonEdge(kFoundryWalls, kPotCenter, Deg(degrees));
            CHECK(d && *d >= 8.f && *d <= 17.f);
        }
        // a lane end through any floor point stays inside the floor
        for (Vec2 const target : { kGilnidSpawn, Vec2{ -190.f, -560.f }, Vec2{ -210.f, -555.f } })
        {
            auto const end = LaneEndAtWall(kFoundryWalls, kPotCenter, target);
            CHECK(end && PointInPolygon(kFoundryWalls, *end));
        }
    }

    // The Juggernaut's deck frame: a corner origin, X toward the bow (-x), Y toward -y.
    void TestDeck()
    {
        Vec2 const xAxis{ std::cos(kDeckAngle), std::sin(kDeckAngle) };
        Vec2 const yAxis{ std::cos(kDeckAngle + kPi / 2.f), std::sin(kDeckAngle + kPi / 2.f) };
        auto const toFrame = [&](Vec2 p)
        {
            float const dx = p.x - kDeckOrigin.x;
            float const dy = p.y - kDeckOrigin.y;
            return Vec2{ dx * xAxis.x + dy * xAxis.y, dx * yAxis.x + dy * yAxis.y };
        };
        auto const inFrame = [&](Vec2 p)
        {
            Vec2 const f = toFrame(p);
            return f.x >= 0.f && f.x <= kDeckLength && f.y >= 0.f && f.y <= kDeckWidth;
        };
        CHECK(Near(xAxis.x, -1.f, 1e-4f));      // toward the bow
        CHECK(Near(yAxis.y, -1.f, 1e-4f));      // across, west rail to east rail
        Vec2 const center = toFrame(kDeckSternCenter);
        CHECK(Near(center.x, 0.f, 1e-3f) && Near(center.y, kDeckWidth / 2.f, 1e-3f));
        CHECK(Near(toFrame(kDeckBowTip).x, kDeckLength, 0.1f));
        CHECK(inFrame(kGreenskinSpawn));
        CHECK(inFrame(kVanCleefSpawn));
        CHECK(!inFrame(kPowderKegSpot));       // playtest 1: the keg is on the stern walkway, aft of the frame
        CHECK(toFrame(kPowderKegSpot).x > -15.f && toFrame(kPowderKegSpot).x < 0.f);
        CHECK(Near(Distance(kGreenskinSpawn, kVanCleefSpawn), 27.8f, 0.2f));
        // the fire front: 16 stripes by 2:40 leave about 10 yd of bow (section 3.8)
        float const faceToBow = kDeckSternCenter.x - kDeckBowTip.x;
        CHECK(Near(faceToBow - 16.f * kFireFrontStripeDepth, 10.f, 1.5f));
    }

    void TestSave()
    {
        Save s;
        // a save written by the stock instance_deadmines: Rhahk'Zor DONE, the cannon DONE
        CHECK(ParseSave("D E 3 3", s));
        CHECK(s.bosses[BOSS_RHAHKZOR] == State::Done);
        CHECK(s.cannon == State::Done);
        for (std::size_t i = 1; i < kSaveBossCount; ++i)
            CHECK(s.bosses[i] == State::NotStarted);
        CHECK(s.hardMode == 0u && s.johnsonRoll == JohnsonRoll::Unrolled);
        // the stock reset rule: IN_PROGRESS comes back NOT_STARTED, for the cannon too
        CHECK(ParseSave("D E 1 1", s));
        CHECK(s.bosses[0] == State::NotStarted && s.cannon == State::NotStarted);
        // round trip; a lit hard mode never survives a reload
        Save full;
        full.bosses = { 3, 3, 3, 0, 2, 3, 3, 0, 0 };
        full.cannon = State::Done;
        full.hardMode = 1;
        full.johnsonRoll = JohnsonRoll::Absent;
        std::string const text = FormatSave(full);
        CHECK(text == "D E 3 3 3 3 0 2 3 3 0 0 1 2");
        Save back;
        CHECK(ParseSave(text, back));
        CHECK(back.bosses[BOSS_MINER_JOHNSON] == State::Done);
        CHECK(back.bosses[BOSS_SNEED] == State::Done);
        CHECK(back.bosses[BOSS_MR_SMITE] == State::NotStarted);      // FAIL sanitized
        CHECK(back.bosses[BOSS_CAPTAIN_GREENSKIN] == State::Done);
        CHECK(back.cannon == State::Done);
        CHECK(back.hardMode == 0u);
        CHECK(back.johnsonRoll == JohnsonRoll::Absent);
        // malformed
        CHECK(!ParseSave("", s));
        CHECK(!ParseSave("DM 3 3", s));
        CHECK(!ParseSave("D E 3", s));
        CHECK(!ParseSave("X E 3 3", s));
        CHECK(ParseSave("D E 3 3 3 9", s) && s.bosses[2] == State::NotStarted);    // out of range state
        CHECK(ParseSave("D E 0 0 0 0 0 0 0 0 0 0 0 7", s) && s.johnsonRoll == JohnsonRoll::Unrolled);
    }

    void TestJohnsonRoll()
    {
        CHECK(ResolveJohnsonRoll(0) == JohnsonRoll::Present);
        CHECK(ResolveJohnsonRoll(39) == JohnsonRoll::Present);
        CHECK(ResolveJohnsonRoll(40) == JohnsonRoll::Absent);
        CHECK(ResolveJohnsonRoll(99) == JohnsonRoll::Absent);
        int present = 0;
        for (std::uint32_t roll = 0; roll < 100; ++roll)
            if (ResolveJohnsonRoll(roll) == JohnsonRoll::Present)
                ++present;
        CHECK(present == 40);
    }

    void TestIds()
    {
        CHECK(kBossCount == 9u);
        CHECK(BOSS_RHAHKZOR == 0u);     // the stock save's first field
        CHECK(BOSS_BURN_IT_DOWN == kBossCount - 1);
        CHECK(DATA_CANNON == 1u);       // the cannon's SmartAI actionlist 1639800 sets instance data 1
        // spell slices: contiguous, in order, exactly 205200-205399
        std::vector<IdSlice> const slices = { kSpellsShared, kSpellsRhahkZor, kSpellsMinerJohnson, kSpellsSneed,
            kSpellsGilnid, kSpellsMrSmite, kSpellsCookie, kSpellsGreenskin, kSpellsVanCleef, kSpellsHardMode,
            kSpellsSpare };
        CHECK(slices.front().first == 205200u);
        CHECK(slices.back().last == 205399u);
        for (std::size_t i = 1; i < slices.size(); ++i)
            CHECK(slices[i].first == slices[i - 1].last + 1);
        CHECK(kSpellsShared.Contains(SPELL_DM_CAST_BAR));
        CHECK(kSpellsShared.Contains(SPELL_DM_STANDING_IN_IT));
        CHECK(kSpellsShared.Contains(SPELL_DM_HARD_MODE_TIMER));
        // boss kit creatures inside 300420-300449, gameobjects inside 301000-301099
        for (std::uint32_t entry : { NPC_DM_WATCHMAN, NPC_DM_EVOKER, NPC_DM_WORKING_MINER, NPC_DM_IRON_SHOT,
                 NPC_DM_LAND_MINE, NPC_DM_BLACKGUARD, NPC_DM_SHADOW_IMAGE, NPC_DM_POWDER_STALKER })
            CHECK(entry >= 300420u && entry <= 300449u);
        for (std::uint32_t entry : { GO_DM_POWDER_KEG, GO_DM_HARPOON_ROPE, GO_DM_MAINMAST })
            CHECK(entry >= 301000u && entry <= 301099u);
    }
}

int main()
{
    TestTuningPattern();
    TestRefFlat();
    TestGeometry();
    TestFoundry();
    TestDeck();
    TestSave();
    TestJohnsonRoll();
    TestIds();
    return Report("kit_test");
}
