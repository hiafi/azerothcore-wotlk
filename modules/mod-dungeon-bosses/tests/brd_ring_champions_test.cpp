// Host tests for RingChampionsLogic.h (D5: the Ring of Law's six champions, the Risen beasts and the Risen Champion).
#include "RingChampionsLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string_view>

using namespace BlackrockDepthsRework;
using namespace BrdRingChampions;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float AngleDiff(float a, float b)
    {
        float d = std::fmod(std::fabs(a - b), DungeonKit::kTwoPi);
        return d > DungeonKit::kPi ? DungeonKit::kTwoPi - d : d;
    }

    void TestSliceAndBinding()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210870 && kSpellSlice.last == 210959);
        CHECK(SPELL_CH_TITLE_HOLDER == 210870);
        CHECK(SPELL_GO_DANCE_BAR == 210873);
        CHECK(SPELL_GZ_RUSH_BAR == 210882);
        CHECK(SPELL_EV_SPELL_EATER == 210892);
        CHECK(SPELL_OK_RUPTURE_BAR == 210899);
        CHECK(SPELL_AN_RAISE_DEAD_BAR == 210904);
        CHECK(SPELL_HE_STRANDS_BAR == 210914);
        CHECK(kLastSpell == 210923);
        CHECK(kLastSpell <= kSpellSlice.last);
        CHECK(kBound);
        // Never D4's spells (the Ring's slice) and never a retired stock id among the kept ones.
        CHECK(kSpellSlice.first > BrdRingOfLaw::kLastSpell);
        for (std::uint32_t const stock : { 15589u, 6524u, 8269u, 7121u, 14331u, 1467u, 15534u, 19137u, 15470u,
            12493u, 15471u, 3609u, 15475u, 15474u, 15245u })
        {
            CHECK(stock != SPELL_STOCK_MORTAL_STRIKE && stock != SPELL_STOCK_BLOODLUST);
            CHECK(stock != SPELL_STOCK_ARCANE_BOLT && stock != SPELL_STOCK_SHADOW_BOLT);
            CHECK(stock != SPELL_STOCK_DEMON_ARMOR);
        }
    }

    void TestTags()
    {
        // G1's drill rows (MechanicDrill.h kBrdTagAxe 6, kBrdTagAxeShown 7, kBrdTagAxeReturn 8, kBrdTagRupture 9,
        // kBrdTagRuptureHeroic 10).
        CHECK(TAG_GO_AXE == 6 && TAG_GO_AXE_SHOWN == 7 && TAG_GO_AXE_RETURN == 8);
        CHECK(TAG_OK_RUPTURE == 9 && TAG_OK_RUPTURE_HEROIC == 10);
        CHECK(RuptureTag(false) == 9 && RuptureTag(true) == 10);
        std::set<std::uint32_t> mine{ TAG_GO_AXE, TAG_GO_AXE_SHOWN, TAG_GO_AXE_RETURN, TAG_OK_RUPTURE,
            TAG_OK_RUPTURE_HEROIC, TAG_GO_DANCE_LINE, TAG_GO_DANCE_END, TAG_GZ_BULL_RUSH, TAG_GZ_STOMP,
            TAG_EV_OPEN_WOUNDS, TAG_OK_SHEEP_BOLT, TAG_AN_WEB_SPIT, TAG_AN_WEB_PATCH, TAG_HE_STRANDS, TAG_HE_STRAND_WEB,
            TAG_HE_BANEFUL_BURST };
        CHECK(mine.size() == 16);
        // Never one of the Ring's own (D4: 11-17).
        for (std::uint32_t const ring : { BrdRingOfLaw::TAG_RL_JEER, BrdRingOfLaw::TAG_RL_TRIAL_FIRE,
            BrdRingOfLaw::TAG_RW_BURROW, BrdRingOfLaw::TAG_RW_TAIL_STING, BrdRingOfLaw::TAG_RW_THUNDERCLAP,
            BrdRingOfLaw::TAG_RW_VENOM_SPIT, BrdRingOfLaw::TAG_RW_ACID_BURST })
            CHECK(mine.count(ring) == 0);
    }

    void TestChampions()
    {
        CHECK(kRingChampions.size() == 6);
        for (std::uint32_t i = 0; i < kRingChampions.size(); ++i)
        {
            std::optional<Champion> const c = ChampionOf(kRingChampions[i]);
            CHECK(c && static_cast<std::uint32_t>(*c) == i);
        }
        CHECK(!ChampionOf(NPC_GRIMSTONE));
        CHECK(std::string_view(ChampionKey(Champion::Gorosh)) == "gorosh");
        CHECK(std::string_view(ChampionKey(Champion::Okthor)) == "okthor");
        CHECK(std::string_view(ChampionKey(Champion::Hedrum)) == "hedrum");
        // The champions walk in from behind the east gate (summoned outside the floor).
        CHECK(!RingOfLawArena().Contains(kRingChampionSummon.XY(), kRingChampionSummon.z));
        CHECK(!BrdRingOfLaw::OnFloor({ kRingChampionSummon.x, kRingChampionSummon.y }, kRingChampionSummon.z));
    }

    void TestHealth()
    {
        // 90k normal on both class bases (S1 Build spec); 150k heroic is WP-H's override.
        std::uint32_t const warrior = HealthOf(kWarriorBaseHealth, kWarriorHealthModifier);
        std::uint32_t const paladin = HealthOf(kPaladinBaseHealth, kPaladinHealthModifier);
        CHECK(warrior >= kChampionNormalHealth && warrior <= kChampionNormalHealth + 10);
        CHECK(paladin >= kChampionNormalHealth - 10 && paladin <= kChampionNormalHealth + 10);
        CHECK(kChampionHeroicHealth == 150000);
        CHECK(HealthOf(kRisenBaseHealth, kRisenHealthModifier) == kRisenNormalHealth);
        std::uint32_t const risenChampion = HealthOf(kWarriorBaseHealth, kRisenChampionHealthModifier);
        CHECK(risenChampion >= kRisenChampionNormalHealth - 5 && risenChampion <= kRisenChampionNormalHealth + 5);
        CHECK(kRisenHeroicHealth == 10000 && kRisenChampionHeroicHealth == 40000);
        CHECK(Near(kChampionDamageModifier, 7.5f));
    }

    void TestTitleHolder()
    {
        CHECK(kTitleHolderDamagePct == 10);
        // The legs token's loot mode is not the Encore's hard mode bit (LootMode 2) nor the default (1).
        CHECK(kTitleHolderLootMode == 4);
        CHECK((kTitleHolderLootMode & 0x3) == 0);
        // The champion death tag never collides with a wave type's (1-6).
        CHECK(kChampionDeathTag > BrdRingOfLaw::kWaveTypes.size());
        // The player auras the champions apply (removed at a death or an evade) are all in the slice, none twice.
        std::set<std::uint32_t> const auras(kChampionPlayerAuras.begin(), kChampionPlayerAuras.end());
        CHECK(auras.size() == kChampionPlayerAuras.size());
        for (std::uint32_t const spell : kChampionPlayerAuras)
            CHECK(spell >= kSpellSlice.first && spell <= kLastSpell);
        CHECK(auras.count(SPELL_EV_OPEN_WOUNDS) && auras.count(SPELL_HE_BANEFUL_POISON));
        CHECK(!auras.count(SPELL_CH_TITLE_HOLDER));
    }

    void TestGorosh()
    {
        CHECK(kDanceEveryMs(false) == 15000 && kDanceEveryMs(true) == 12000);
        CHECK(Near(kDanceLinePct(false), 20.f) && Near(kDanceLinePct(true), 35.f));
        CHECK(Near(kDanceEndPct(false), 25.f) && Near(kDanceEndPct(true), 40.f));
        CHECK(Near(kDanceWidth, 6.f) && Near(kDanceEndRadius, 8.f));
        CHECK(DanceTravelMs(20.f) == 1000);
        CHECK(DanceTravelMs(0.f) == 0);
        Vec2 const from{ 600.f, -190.f };
        Vec2 const far{ 620.f, -190.f };
        CHECK(Near(DungeonKit::Distance(from, DanceEnd(from, far)), 20.f));
        Vec2 const close{ 601.f, -190.f };
        Vec2 const end = DanceEnd(from, close);
        CHECK(Near(DungeonKit::Distance(from, end), kDanceMinLength, 0.05f));
        CHECK(end.x > from.x);      // the same bearing
        Vec2 const same = DanceEnd(from, from);
        CHECK(Near(DungeonKit::Distance(from, same), kDanceMinLength, 0.05f));

        // GO2 matches G1's `axe-return` row: a 3 yd 2 s landing, 4 s shown, 2 s locked, 4 yd wide.
        CHECK(kAxeLandMs == 2000 && Near(kAxeLandRadius, 3.f));
        CHECK(kAxeShownMs == 4000 && kAxeLockMs == 2000 && Near(kAxeReturnWidth, 4.f));
        CHECK(AxeLockAtMs() == 6000 && AxeReturnAtMs() == 8000);
        CHECK(AxeReturnAtMs() < kAxeEveryMs);       // one axe at a time
        CHECK(Near(kAxeLandPct(false), 15.f) && Near(kAxeLandPct(true), 25.f));
        CHECK(Near(kAxeReturnPct(false), 20.f) && Near(kAxeReturnPct(true), 35.f));
    }

    void TestGrizzle()
    {
        CHECK(kRushEveryMs == 25000 && kRushWarnMs == 2000);
        CHECK(Near(kRushPct(false), 35.f) && Near(kRushPct(true), 50.f));
        CHECK(kDazedMs == 4000 && kDazedDamageTakenPct == 30);
        CHECK(kStompEveryMs == 18000 && kStompWarnMs == 2500 && Near(kStompRadius, 12.f));
        CHECK(Near(kStompPct(false), 25.f) && Near(kStompPct(true), 40.f) && kStompStunMs == 2000);
        CHECK(kFrenzyEveryMs == 15000 && kFrenzyPctPerStack == 10);
        // Cap 5 on normal, uncapped (the aura's ceiling) on heroic.
        std::uint32_t stacks = 0;
        for (int i = 0; i < 10; ++i)
            stacks = NextFrenzy(stacks, false);
        CHECK(stacks == 5);
        stacks = 0;
        for (int i = 0; i < 10; ++i)
            stacks = NextFrenzy(stacks, true);
        CHECK(stacks == 10);
        CHECK(FrenzyCap(true) > 10);    // a 45-90 s fight never reaches it
        // One stack taken by a Tranquilizing Shot: the script clears them all.
        CHECK(FrenzyDispelled(3, 2));
        CHECK(!FrenzyDispelled(3, 3));
        CHECK(!FrenzyDispelled(0, 0));
        CHECK(FrenzyDispelled(4, 0));
        // Bull Rush runs to the measured wall (NM: 23-45 yd from the center) from anywhere on the floor.
        Vec2 const c = kRingCenter.XY();
        for (int deg = 0; deg < 360; deg += 15)
        {
            std::optional<Vec2> const end = WallAlong(c, BrdRingOfLaw::Radians(static_cast<float>(deg)),
                kRushWallInset);
            CHECK(end.has_value());
            if (!end)
                continue;
            float const d = DungeonKit::Distance(c, *end);
            CHECK(d >= 21.f && d <= 46.f);
            CHECK(BrdRingOfLaw::OnFloorPlane(*end));
        }
        // The diagonals are short (23-26 yd), the cardinals long (38-43 yd).
        std::optional<Vec2> const diagonal = WallAlong(c, BrdRingOfLaw::Radians(45.f), 0.f);
        std::optional<Vec2> const north = WallAlong(c, 0.f, 0.f);
        CHECK(diagonal && DungeonKit::Distance(c, *diagonal) < 27.f);
        CHECK(north && DungeonKit::Distance(c, *north) > 37.f);
        // From off the floor (behind the east gate) there is no wall line.
        CHECK(!WallAlong(kRingChampionSummon.XY(), 0.f, 0.5f));
    }

    void TestEviscerator()
    {
        CHECK(kSpellEaterEveryMs == 25000 && kSpellEaterMs == 8000);
        std::uint32_t stacks = 0;
        for (int i = 0; i < 40; ++i)
            stacks = AddDevoured(stacks);
        CHECK(stacks == kDevouredCap && kDevouredCap == 15);
        CHECK(Near(DevouredPct(15), 30.f));
        CHECK(Near(DevouredPct(40), 30.f));
        CHECK(Near(DevouredPct(1), 2.f));
        CHECK(Near(DevouredPct(0), 0.f));
        CHECK(kOpenWoundsEveryMs == 20000 && kOpenWoundsMs == 15000 && kOpenWoundsTickMs == 3000);
        CHECK(kOpenWoundsJumps == 5 && Near(kOpenWoundsPct, 2.f) && Near(kOpenWoundsJumpYd, 5.f));
        CHECK(kVolleyEveryMs(false) == 15000 && kVolleyEveryMs(true) == 12000 && kVolleyCastMs == 3000);
        CHECK(kVolleyKickPriority(true) > kVolleyKickPriority(false));
    }

    void TestOkthor()
    {
        CHECK(kRuptureEveryMs(false) == 20000 && kRuptureEveryMs(true) == 15000 && kRuptureCastMs == 3000);
        CHECK(Near(kRuptureInner(false), 8.f) && Near(kRuptureInner(true), 6.f));
        CHECK(Near(kRupturePct(false), 30.f) && Near(kRupturePct(true), 45.f));
        // The donut reaches every point of the floor from wherever he stands on it.
        Vec2 const c = kRingCenter.XY();
        std::vector<Vec2> const& floor = BrdRingOfLaw::RingFloor();
        for (Vec2 const at : { c, Vec2{ c.x + 30.f, c.y + 5.f }, Vec2{ c.x - 20.f, c.y - 20.f },
            Vec2{ c.x + 5.f, c.y - 35.f } })
        {
            float const outer = RuptureOuter(at);
            CHECK(outer >= kRuptureMinOuter);
            for (Vec2 const& v : floor)
                CHECK(DungeonKit::Distance(at, v) < outer);
        }
        // Sheep Bolt sits between two Ruptures (never on one), heroic too.
        for (bool const heroic : { false, true })
        {
            std::uint32_t const sheep = kRuptureCastMs + kSheepAfterRuptureMs;
            CHECK(sheep + kSheepWarnMs < kRuptureEveryMs(heroic) + kRuptureCastMs);
        }
        CHECK(kSheepCount(false) == 1 && kSheepCount(true) == 2);
        CHECK(Near(kSheepPct(false), 15.f) && Near(kSheepPct(true), 25.f) && kSheepPolyMs == 2000);
        CHECK(kSlowMs == 8000 && kSlowMovePct == 60 && kSlowHastePct == 55);
    }

    void TestAnubshiah()
    {
        // One Risen entry per wave type, in the stock RingMobs order (BlackrockDepthsRework.h).
        for (std::uint32_t type = 0; type < BrdRingOfLaw::kWaveTypes.size(); ++type)
        {
            CHECK(RisenEntry(type) == NPC_BRD_RISEN_WORM + type);
            CHECK(RisenWaveType(RisenEntry(type)) == type);
            CHECK(BrdRingOfLaw::kWaveTypes[type].entry == kRingWaveMobs[type]);
        }
        CHECK(RisenEntry(4) == NPC_BRD_RISEN_CREEPER && BrdRingOfLaw::kWaveTypes[4].entry == NPC_CAVE_CREEPER);
        CHECK(RisenEntry(5) == NPC_BRD_RISEN_BEETLE && BrdRingOfLaw::kWaveTypes[5].entry == NPC_BORER_BEETLE);
        CHECK(!RisenWaveType(NPC_BRD_RISEN_CHAMPION));
        CHECK(!RisenWaveType(NPC_GOROSH));
        // Raise Dead: 1 / 2 a cast, held under the wave's size, never more than the spots left.
        CHECK(RaiseCount(false, 3, 0, 3) == 1);
        CHECK(RaiseCount(true, 3, 0, 3) == 2);
        CHECK(RaiseCount(true, 3, 2, 3) == 1);
        CHECK(RaiseCount(true, 3, 3, 3) == 0);
        CHECK(RaiseCount(true, 6, 0, 1) == 1);
        CHECK(RaiseCount(false, 2, 0, 0) == 0);
        CHECK(RaiseCount(true, 2, 5, 4) == 0);
        // The Risen Champion: heroic, the title holder, below 50%, once.
        CHECK(RaisesChampion(true, 2, 49.f, false));
        CHECK(!RaisesChampion(true, 2, 51.f, false));
        CHECK(!RaisesChampion(false, 2, 10.f, false));
        CHECK(!RaisesChampion(true, 1, 10.f, false));
        CHECK(!RaisesChampion(true, 2, 10.f, true));
        CHECK(kWebSpitEveryMs == 18000 && Near(kWebSpitRadius, 6.f) && kWebPatchMs == 20000);
        CHECK(Near(kWebSpitPct(false), 15.f) && Near(kWebSpitPct(true), 25.f) && kWebPatchSlowPct == 50);
        CHECK(kCurseMs == 15000 && kTonguesCastPct == 50 && kWeaknessPhysicalPct == 20);
    }

    void TestHedrum()
    {
        CHECK(kStrandsEveryMs == 25000 && kStrandsCount == 3 && Near(kStrandsWidth, 4.f));
        CHECK(kStrandsLifeMs(false) == 20000 && kStrandsLifeMs(true) == 30000);
        // Heroic: two sets up at once (a 30 s life on a 25 s cadence), normal one.
        CHECK(kStrandsLifeMs(true) > kStrandsEveryMs && kStrandsLifeMs(false) < kStrandsEveryMs);
        CHECK(Near(kStrandsPct(false), 20.f) && Near(kStrandsPct(true), 35.f) && kStrandsSlowPct == 30);
        std::array<float, kStrandsCount> const b = StrandBearings(0.3f);
        CHECK(Near(b[0], 0.3f));
        CHECK(Near(AngleDiff(b[0], b[1]), DungeonKit::kTwoPi / 3.f, 0.01f));
        CHECK(Near(AngleDiff(b[1], b[2]), DungeonKit::kTwoPi / 3.f, 0.01f));
        // Each strand reaches the measured wall from the center.
        Vec2 const c = kRingCenter.XY();
        for (float const bearing : StrandBearings(1.1f))
        {
            std::optional<Vec2> const end = WallAlong(c, bearing, 0.5f);
            CHECK(end && DungeonKit::Distance(c, *end) >= kStrandsMinLength);
        }
        CHECK(kReelEveryMs == 20000 && kReelCount(false) == 1 && kReelCount(true) == 2);
        CHECK(kBurstWarnMs == 3000 && Near(kBurstRadius, 10.f));
        CHECK(Near(kBurstPct(false), 30.f) && Near(kBurstPct(true), 45.f));
        CHECK(Near(kBurstPoisonPct, 2.f) && kBurstPoisonMs == 8000);
        CHECK(FirstOf(kStrandsEveryMs) == 12500 && FirstOf(kReelEveryMs) == 10000);
    }
}

int main()
{
    TestSliceAndBinding();
    TestTags();
    TestChampions();
    TestHealth();
    TestTitleHolder();
    TestGorosh();
    TestGrizzle();
    TestEviscerator();
    TestOkthor();
    TestAnubshiah();
    TestHedrum();
    return Report("brd_ring_champions_test");
}
