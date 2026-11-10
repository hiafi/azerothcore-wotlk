/*
 * mod-dungeon-bosses, Stratholme S5: Cannon Master Willey (10997), the pure, host-testable part (no engine headers).
 * Build spec ST 1444-1502 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows WY, 3.5 row S5, 3.6, 3.8
 * (the hall frame). Tested by tests/strat_willey_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsWilley (206500-206519), declared in apps/dbc-tools
 *                  source/npcs/stratholme/cannon_master_willey.py
 *   Tuning         NH<> constants and Cadence{first, every}, straight from the build spec
 *   DrillClock     WY1 the ranks: 6 s, then every 20 s; a due rank waits while it would push the riflemen past the cap
 *   RankCycle      WY2 / WY3 a rank's beat: formed, Aim 6 s (heroic 4 s) later, Fire 3 s (2 s) after Aim, Aim again
 *                  8 s after Fire
 *   Gun, halves    WY8 / WY9 Mercy (east half, on the stock 176216's spot) and Zeal (west half, on 176217's) on the
 *                  hall frame kWilleyHall; each lane is its half, the full length
 *   BarrageOrder   WY9 heroic: five blasts, three on one half and two on the other, in a random order, and the call
 *   ShotDamage     WY6 the loaded gun's shot at him: 5% of his maximum health, never lethal (SelfDamageCap holds
 *                  it after every damage-taken modifier)
 *   HallSpotCorners the bots' spot bounds: the hall, never the yard
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_WILLEY_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_WILLEY_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

namespace StratWilley
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsWilley;

    enum WilleySpells : std::uint32_t
    {
        SPELL_WY_AIM                = kSpellSlice.first + 0,    // 206500 WY2 the red arrow over the aimed player
        SPELL_WY_TAKING_AIM         = kSpellSlice.first + 1,    // 206501 WY2 the aiming rifleman's own aura (bots
                                                                //        kill it first)
        SPELL_WY_FIRE               = kSpellSlice.first + 2,    // 206502 WY3 the volley hit, 15% / 20% Physical
        SPELL_WY_HOLDING_CANNONBALL = kSpellSlice.first + 3,    // 206503 WY5 -30% speed, 30 s
        SPELL_WY_CANNON_SHOT        = kSpellSlice.first + 4,    // 206504 WY6 the loaded gun's shot at him (base
                                                                //        point 0 from the script)
        SPELL_WY_SHAKEN             = kSpellSlice.first + 5,    // 206505 WY7 +10% damage taken per stack, 3, 15 s
        SPELL_WY_CANNON_FIRE        = kSpellSlice.first + 6,    // 206506 WY8 the lane's hit (resolve copy, Fire)
        SPELL_WY_BARRAGE            = kSpellSlice.first + 7,    // 206507 WY9 a blast's hit (resolve copy, Fire)
        SPELL_WY_BLAST_LOOK         = kSpellSlice.first + 8,    // 206508 WY8 / WY9 a burst on the floor down a lane
        SPELL_WY_MERCY_GLOW         = kSpellSlice.first + 9,    // 206509 Mercy's gold glow ring (aura on its stalker)
        SPELL_WY_ZEAL_GLOW          = kSpellSlice.first + 10,   // 206510 Zeal's orange glow ring (aura on its stalker)
        // 206511-206519 spare
    };
    static_assert(SPELL_WY_ZEAL_GLOW <= kSpellSlice.last, "Willey's spells must stay in his slice");

    // The glow stalker under each gun (orchestrator's grant from the wave 2 spare creatures; invisible, no heroic
    // copy). Named here, not in StratholmeRework.h's creature enum, so the two can never define it twice.
    inline constexpr std::uint32_t kNpcGunGlow = 300610;

    // Stock kit (WY10), kept: Knock Away and Pummel on him, Shoot on the riflemen (DD scales them on heroic).
    inline constexpr std::uint32_t SPELL_WY_KNOCK_AWAY = 10101;
    inline constexpr std::uint32_t SPELL_WY_PUMMEL = 15615;
    inline constexpr std::uint32_t SPELL_WY_SHOOT = 17353;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum WilleyTags : std::uint32_t
    {
        TAG_CANNONBALL  = 4,    // WY4 the dropped ball (pickup Soak)
        TAG_LOAD        = 6,    // WY6 the load spot at a gun (carrier-only Soak)
        TAG_CANNON_FIRE = 8,    // WY8
        TAG_BARRAGE     = 9,    // WY9 (the stratholme-followups drill's bar tag is 9 too)
    };

    // MovePoint id: a rifleman marching from the yard opening to its spot in the rank.
    inline constexpr std::uint32_t POINT_WY_RANK = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 1444-1502; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // First start and cadence of a beat, in ms since the pull (ST "First, cooldown"). Cadences count start to start.
    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    struct MsRange
    {
        std::uint32_t min;
        std::uint32_t max;
    };

    // `r` in [0, 1): a point of the range.
    constexpr std::uint32_t PickInRange(MsRange range, float r)
    {
        float const span = static_cast<float>(range.max - range.min);
        return range.min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 1.f) * span);
    }

    // WY1 The Drill: a rank forms at 6 s, then every 20 s; 3 riflemen (heroic 4), at most 6 (heroic 8) alive. 5,000
    // (heroic 7,000) health each: the normal template's HealthModifier (dbc-tools) and the heroic template's override
    // (source/world/dungeons/stratholme.py); the script never sets it.
    inline constexpr Cadence kRankCadence{ 6000, 20000 };
    inline constexpr NH<std::uint32_t> kRankSize{ 3, 4 };
    inline constexpr NH<std::uint32_t> kRiflemanCap{ 6, 8 };
    inline constexpr NH<std::uint32_t> kRiflemanHealth{ 5000, 7000 };     // the templates' (the DT test pins it)
    // A rank marches in from the yard opening to its spots; it counts as formed this long after the summon.
    inline constexpr std::uint32_t kMarchMs = 2500;
    // The yard opening on the hall's east side (NAVMESH-REPORT section 5: from (3544.8, -2970.1) to (3536.6, -2975.9)),
    // where a rank appears; the riflemen spread along it.
    inline constexpr Vec2 kYardOpeningA{ 3544.8f, -2970.1f };
    inline constexpr Vec2 kYardOpeningB{ 3536.6f, -2975.9f };
    inline constexpr float kRankZ = 125.3f;

    // WY2 Aim, WY3 Fire: Aim 6 s (heroic 4 s) after the rank forms, Fire 3 s (heroic 2 s) after Aim, then the rank
    // reloads and aims again 8 s after Fire (an 11 s / 10 s volley cycle). 15% / 20% Physical a rifleman, not
    // avoidable: the percent rides in the Fire spell (dbc-tools, hundredths: 1500 / 2000).
    inline constexpr NH<std::uint32_t> kAimAfterFormMs{ 6000, 4000 };
    inline constexpr NH<std::uint32_t> kFireAfterAimMs{ 3000, 2000 };
    inline constexpr std::uint32_t kReaimAfterFireMs = 8000;
    inline constexpr NH<float> kVolleyPct{ 15.f, 20.f };                  // the Fire spell's (the DT test pins it)
    // The riflemen's stock Shoot 17353 between volleys: one shot every 2 s on a random player (never while aiming).
    inline constexpr std::uint32_t kShootEveryMs = 2000;
    // Willey's "Ready!" / "Aim!" / "Fire!" yells: never the same line twice within this long (two ranks on one beat).
    inline constexpr std::uint32_t kYellGapMs = 1500;

    // WY4 the Scarlet Cannonball: the last rifleman of a rank to die drops it; it lies 20 s; walking over it (1.5 yd)
    // picks it up, one ball a player (players without Holding Cannonball; never the tank: a slowed tank drags him).
    inline constexpr float kBallRadius = 1.5f;
    inline constexpr std::uint32_t kBallLifeMs = 20000;
    // WY5 Holding Cannonball: -30% speed, 30 s, then the ball is lost (the aura's own duration, dbc-tools).
    inline constexpr std::uint32_t kHoldingMs = 30000;
    // WY6 Load: a carrier inside a gun's load spot (behind its breech) for 2 s loads it.
    inline constexpr float kLoadRadius = 2.5f;
    inline constexpr std::uint32_t kLoadDwellMs = 2000;
    inline constexpr std::uint32_t kLoadSpotLifeMs = 600000;      // the fight's length: re-added after each load
    inline constexpr std::uint32_t kCarrierPollMs = 500;
    // The shot: 5% of his maximum health; WY7 Shaken +10% damage taken a stack, 3 stacks, 15 s, refreshed by a load.
    inline constexpr float kShotPct = 5.f;
    inline constexpr std::uint32_t kShakenMaxStacks = 3;
    inline constexpr float kShakenPctPerStack = 10.f;

    // WY8 Cannon Fire (normal): at 10 s, then every 12 s; a 2.5 s marker on the called gun's half, 40% Fire, no
    // Weakened, tank included.
    inline constexpr Cadence kCannonFireCadence{ 10000, 12000 };
    inline constexpr std::uint32_t kCannonFireWarnMs = 2500;
    inline constexpr float kCannonFirePct = 40.f;

    // WY9 the Barrage (heroic, replaces Cannon Fire): at 12 s, then every 20 s; the whole order is called 3 s before
    // the first blast, then a blast every 1.5 s; 30% Fire + Weakened each; no marker (ruling 23).
    inline constexpr Cadence kBarrageCadence{ 12000, 20000 };
    inline constexpr std::uint32_t kBarrageBlasts = 5;
    inline constexpr std::uint32_t kBarrageCallMs = 3000;
    inline constexpr std::uint32_t kBarrageGapMs = 1500;
    inline constexpr float kBarragePct = 30.f;

    // WY10: Knock Away on his victim, first 3-12 s, then every 11-17 s (the stock SmartAI's); Pummel on a player
    // casting within 5 yd, every 12-18 s.
    inline constexpr MsRange kKnockAwayFirst{ 3000, 12000 };
    inline constexpr MsRange kKnockAwayEvery{ 11000, 17000 };
    inline constexpr MsRange kPummelEvery{ 12000, 18000 };
    inline constexpr float kPummelRange = 5.f;

    // ----------------------------------------------------------------------------------------------------------------
    // WY1 The Drill
    // ----------------------------------------------------------------------------------------------------------------

    // A rank of `size` may come while `alive` riflemen stand: never past the cap ("a rank doesn't come while 6 stand").
    constexpr bool CanForm(std::uint32_t alive, std::uint32_t size, std::uint32_t cap)
    {
        return alive + size <= cap;
    }

    // The ranks' clock: due at kRankCadence.first; a due rank waits while it cannot form and comes as soon as it can;
    // the next one is due kRankCadence.every after the last one came.
    class DrillClock
    {
    public:
        void Reset() { _dueMs = kRankCadence.first; }
        bool Due(std::uint64_t nowMs) const { return nowMs >= _dueMs; }
        void Formed(std::uint64_t nowMs) { _dueMs = nowMs + kRankCadence.every; }
        void RetryIn(std::uint64_t nowMs, std::uint32_t ms) { _dueMs = nowMs + ms; }
        std::uint64_t DueMs() const { return _dueMs; }

    private:
        std::uint64_t _dueMs = kRankCadence.first;
    };

    // The spots of a rank (X 52 across the hall, StratholmeRework.h): 3 on normal, 4 on heroic.
    inline std::size_t RankSpotCount(bool heroic)
    {
        return heroic ? StratholmeRework::kWilleyRank4.size() : StratholmeRework::kWilleyRank3.size();
    }

    inline StratholmeRework::Point3 RankSpot(bool heroic, std::size_t index)
    {
        if (heroic)
            return StratholmeRework::kWilleyRank4[index % StratholmeRework::kWilleyRank4.size()];
        return StratholmeRework::kWilleyRank3[index % StratholmeRework::kWilleyRank3.size()];
    }

    // Where rifleman `index` of `count` appears: spread evenly along the yard opening.
    inline Vec2 MarchStart(std::size_t index, std::size_t count)
    {
        float const t = count > 1 ? static_cast<float>(index) / static_cast<float>(count - 1) : 0.5f;
        return { kYardOpeningA.x + (kYardOpeningB.x - kYardOpeningA.x) * t,
            kYardOpeningA.y + (kYardOpeningB.y - kYardOpeningA.y) * t };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY2 Aim, WY3 Fire: one rank's beat
    // ----------------------------------------------------------------------------------------------------------------

    enum class RankStep : std::uint8_t
    {
        None,
        Aim,
        Fire,
    };

    class RankCycle
    {
    public:
        // The rank was summoned at `nowMs`: it forms kMarchMs later and aims kAimAfterFormMs after that.
        void Summoned(std::uint64_t nowMs, bool heroic)
        {
            _heroic = heroic;
            _aiming = false;
            _nextMs = nowMs + kMarchMs + kAimAfterFormMs(heroic);
        }

        // Aim on the next Update (`.dbtest strat willey aim`).
        void AimNow(std::uint64_t nowMs)
        {
            _aiming = false;
            _nextMs = nowMs;
        }

        // The step due now (at most one a call).
        RankStep Update(std::uint64_t nowMs)
        {
            if (nowMs < _nextMs)
                return RankStep::None;
            if (!_aiming)
            {
                _aiming = true;
                _nextMs = nowMs + kFireAfterAimMs(_heroic);
                return RankStep::Aim;
            }
            _aiming = false;
            _nextMs = nowMs + kReaimAfterFireMs;
            return RankStep::Fire;
        }

        bool Aiming() const { return _aiming; }
        std::uint64_t NextMs() const { return _nextMs; }

    private:
        std::uint64_t _nextMs = 0;
        bool _heroic = false;
        bool _aiming = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The guns and their halves (WY8, WY9; NAVMESH-REPORT section 5 (b))
    // ----------------------------------------------------------------------------------------------------------------

    enum class Gun : std::uint8_t
    {
        Mercy,      // 301200, east half (frame Y 10..20), on the stock 176216's spot
        Zeal,       // 301201, west half (frame Y 0..10), on the stock 176217's spot
    };

    inline constexpr float kHallLength = StratholmeRework::kWilleyHall.sizeX;           // 58 yd, the full length
    inline constexpr float kHalfWidth = StratholmeRework::kWilleyHalfSplitY;            // 10 yd

    constexpr Gun OtherGun(Gun gun)
    {
        return gun == Gun::Mercy ? Gun::Zeal : Gun::Mercy;
    }

    constexpr char const* GunName(Gun gun)
    {
        return gun == Gun::Mercy ? "Mercy" : "Zeal";
    }

    // The half's middle across the hall (frame Y).
    constexpr float HalfCenterY(Gun gun)
    {
        return gun == Gun::Mercy ? StratholmeRework::kWilleyHalfSplitY + kHalfWidth * 0.5f : kHalfWidth * 0.5f;
    }

    // The lane of `gun`: from the hall's back wall (frame X 0) down the half's middle, the full length, 10 yd wide;
    // its facing is the hall's axis (Shapes::LineFacing(LaneStart(gun), kWilleyHall.angle, kHallLength, kHalfWidth)).
    inline Vec2 LaneStart(Gun gun)
    {
        return DungeonKit::FramePoint(StratholmeRework::kWilleyHall, 0.f, HalfCenterY(gun));
    }

    // A point `x` yd down the hall in the middle of `gun`'s half (the floor bursts of a blast).
    inline Vec2 LanePoint(Gun gun, float x)
    {
        return DungeonKit::FramePoint(StratholmeRework::kWilleyHall, x, HalfCenterY(gun));
    }

    // The half a map point lies in (the split line Y 10 belongs to Mercy's half).
    inline Gun HalfOf(Vec2 p)
    {
        return DungeonKit::ToFrame(StratholmeRework::kWilleyHall, p).y >= StratholmeRework::kWilleyHalfSplitY
            ? Gun::Mercy : Gun::Zeal;
    }

    // The guns stand on the stock cannons' spawns (gameobject guids 20761 / 20768, [db]); their load spots are 3.5 yd
    // behind the breech, toward him (frame X about 8.5, the gun's own Y): on open floor, off the narrow point the guns
    // stand in.
    inline constexpr StratholmeRework::Point3 kMercyAt{ 3567.81f, -2947.28f, 124.962f };
    inline constexpr StratholmeRework::Point3 kZealAt{ 3562.45f, -2939.42f, 124.962f };
    inline constexpr float kLoadSpotBehindYd = 3.5f;
    inline constexpr float kGunSearchYd = 80.f;       // he finds his guns this far from himself

    inline StratholmeRework::Point3 GunAt(Gun gun)
    {
        return gun == Gun::Mercy ? kMercyAt : kZealAt;
    }

    inline Vec2 LoadSpot(Gun gun)
    {
        Vec2 const f = DungeonKit::ToFrame(StratholmeRework::kWilleyHall, GunAt(gun).XY());
        return DungeonKit::FramePoint(StratholmeRework::kWilleyHall, f.x - kLoadSpotBehindYd, f.y);
    }

    // The glow ring of `gun`: Mercy gold (HolyZone), Zeal orange (FlameZone), on a stalker standing on the gun's spot.
    constexpr std::uint32_t GlowSpell(Gun gun)
    {
        return gun == Gun::Mercy ? SPELL_WY_MERCY_GLOW : SPELL_WY_ZEAL_GLOW;
    }

    // The floor bursts down a lane when it fires (a visible impact; the registry hit owns the damage).
    inline constexpr std::array<float, 4> kBurstX{ { 16.f, 28.f, 40.f, 52.f } };

    // WY8: the called gun from a random number (any value).
    constexpr Gun GunFromRoll(std::uint32_t roll)
    {
        return (roll & 1u) ? Gun::Zeal : Gun::Mercy;
    }

    // The bots' spot bounds (F-2): the hall frame, a yard inside each side, so no dodge from a lane plans a spot in the
    // yard (the hall's far end opens east into it at frame X 44..54, Y 20; NAVMESH-REPORT section 5). Z: the hall's
    // flat floor (125.1..126.5) with room.
    inline constexpr float kSpotInsetYd = 1.f;
    inline constexpr float kSpotZMin = 124.f;
    inline constexpr float kSpotZMax = 128.f;

    inline std::array<Vec2, 4> HallSpotCorners()
    {
        using StratholmeRework::kWilleyHall;
        float const lo = kSpotInsetYd;
        float const hiX = kWilleyHall.sizeX - kSpotInsetYd;
        float const hiY = kWilleyHall.sizeY - kSpotInsetYd;
        return { { DungeonKit::FramePoint(kWilleyHall, lo, lo), DungeonKit::FramePoint(kWilleyHall, hiX, lo),
            DungeonKit::FramePoint(kWilleyHall, hiX, hiY), DungeonKit::FramePoint(kWilleyHall, lo, hiY) } };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY9 the Barrage (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    using BarrageOrder = std::array<Gun, kBarrageBlasts>;

    // The 10 ways to place the two minority blasts among the five.
    inline constexpr std::array<std::array<std::uint8_t, 2>, 10> kMinorityPairs{ {
        { { 0, 1 } }, { { 0, 2 } }, { { 0, 3 } }, { { 0, 4 } }, { { 1, 2 } },
        { { 1, 3 } }, { { 1, 4 } }, { { 2, 3 } }, { { 2, 4 } }, { { 3, 4 } } } };
    inline constexpr std::uint32_t kBarrageOrders = 2 * kMinorityPairs.size();

    // The order from a random number (any value: taken modulo the 20 orders): the half with three blasts, then where
    // the two others fall.
    constexpr BarrageOrder MakeBarrageOrder(std::uint32_t roll)
    {
        std::uint32_t const r = roll % kBarrageOrders;
        Gun const major = r < kMinorityPairs.size() ? Gun::Mercy : Gun::Zeal;
        auto const& pair = kMinorityPairs[r % kMinorityPairs.size()];
        BarrageOrder order{};
        for (std::size_t i = 0; i < order.size(); ++i)
            order[i] = (i == pair[0] || i == pair[1]) ? OtherGun(major) : major;
        return order;
    }

    constexpr std::uint32_t CountOf(BarrageOrder const& order, Gun gun)
    {
        std::uint32_t n = 0;
        for (Gun const g : order)
            if (g == gun)
                ++n;
        return n;
    }

    // Blast `index` lands this long after the call.
    constexpr std::uint32_t BlastDelayMs(std::uint32_t index)
    {
        return kBarrageCallMs + index * kBarrageGapMs;
    }

    // The boss emote (center screen; the client puts his name for %s): "%s calls the Barrage: Mercy! Zeal! Mercy!
    // Mercy! Zeal!".
    inline std::string BarrageCall(BarrageOrder const& order)
    {
        std::string out = "%s calls the Barrage:";
        for (Gun const g : order)
        {
            out += ' ';
            out += GunName(g);
            out += '!';
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WY6 the shot, WY7 Shaken
    // ----------------------------------------------------------------------------------------------------------------

    // The shot's base point: 5% of his maximum health, divided by the Shaken he already carries (the shot lands before
    // the new stack, and Shaken's damage taken raises it), and never more than leaves him at 1 health (a gun never
    // takes the kill: the players' blow kills him). 0 when he has 1 health or less.
    constexpr std::uint32_t ShotDamage(std::uint32_t maxHealth, std::uint32_t health, std::uint32_t shakenStacks)
    {
        if (health <= 1)
            return 0;
        double const taken = 1.0 + kShakenPctPerStack / 100.0 * static_cast<double>(shakenStacks);
        auto const value = static_cast<std::uint32_t>(static_cast<double>(maxHealth) * kShotPct / 100.0 / taken + 0.5);
        auto const cap = static_cast<std::uint32_t>(static_cast<double>(health - 1) / taken);
        return value < cap ? value : cap;
    }

    // F-2: whatever else raises his damage taken (a player's curse or debuff; ShotDamage only knows Shaken), his own
    // damage (the shot is the only damage he deals himself) is held, after every modifier, to leave him at 1 health.
    constexpr std::uint32_t SelfDamageCap(std::uint32_t health, std::uint32_t damage)
    {
        if (health <= 1)
            return 0;
        return damage < health ? damage : health - 1;
    }
}

#endif
