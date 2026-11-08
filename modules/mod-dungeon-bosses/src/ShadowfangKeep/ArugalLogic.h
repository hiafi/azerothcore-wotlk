/*
 * mod-dungeon-bosses, Shadowfang Keep: Archmage Arugal (WP-S9), the pure, host-testable part (no engine headers): spell
 * ids, per-difficulty tuning numbers, the never-paused fight timeline, the Worgen's Curse arithmetic, the Shadow Port
 * spots and the wards placed for the level he stands on. Build spec: SK 1576-1646 (build spec), SK 1394-1575
 * (design), AR1-AR10; handoff section 3.5 rows AR, section 3.6 row S9, section 7 #7, #22 and section 10.
 *
 * Percentages are of the reference health row (normal 1,300 / heroic 4,120 non-tank): the same percent on both
 * difficulties, the row makes the difference.
 *
 * The room (user rulings 2026-11-07, handoff section 10, which replace section 7 #23): Arugal keeps his stock ledge.
 * The room has three levels on the navmesh (shadowfang-keep-build.NAVMESH-REPORT.md section 9, plus S9's own
 * measurements, STAGE-S9-REPORT): the platform with the west gallery (one level, z 155.8, where he spawns), the
 * antechamber inside the lair door (z 156, the stock spot 7136) and the lower floor 10.4 yd below. The gallery's west
 * end and the antechamber's east edge are 6.8 yd apart on the mesh (about 5.7 yd of real gap, at the same height): a
 * well-timed running jump. Whoever does not make it takes the stairs: down the platform ramp, across the lower floor,
 * up the antechamber ramp (69 yd). Bots always take the stairs (their paths are PathGenerator's, on the navmesh).
 *
 * Shadow Port therefore moves him between three spots melee can reach by those rules: his spawn and the stock 7586 on
 * the platform, and the stock 7136 in the antechamber. The stock 7587 is dropped: it hangs 9.7 yd over the lower floor
 * with no floor within 27.5 yd at its height (no jump or stair reaches it).
 *
 * The wards are placed on the level he stands on: measured points of that level, within 1.6 yd of his spot's height
 * (the registry's 6 yd z band keeps the other levels out, and a bot's walkability probe finds them). The ledge has no
 * floor where a 5 yd circle fits whole 10 yd or more from him (the report's "14 sq yd"), so a full ward is clipped by
 * the ledge edge: its centre has 3 to 5.3 yd of navmesh clearance (about 0.5 yd more in the real room), 9.5 to 12.7 yd
 * from his spot. The heroic Moonrise wards (3 yd) fit whole.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_ARUGAL_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_ARUGAL_LOGIC_H

#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>
#include <vector>

namespace Arugal
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ShadowfangKeepRework::Point3;
    using Ms = std::chrono::milliseconds;

    // This boss's spell slice (handoff section 3.4); S10 (Face Him Alone) owns its last five ids.
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsArugal;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/archmage_arugal.py (same ids).
    enum ArugalSpells : std::uint32_t
    {
        SPELL_ARUGAL_WORGENS_CURSE          = 206060,   // AR1 normal: the 100-stack meter (never dispellable)
        SPELL_ARUGAL_WORGENS_CURSE_HEROIC   = 206061,   // AR1 + AR8 heroic: the meter, tooltip names Feral Power
        SPELL_ARUGAL_FERAL_POWER            = 206062,   // AR8 heroic: hidden, +2% damage and healing done per stack (9)
        SPELL_ARUGAL_THUNDERSHOCK_CAST      = 206063,   // AR2 the 2 s cast bar
        SPELL_ARUGAL_THUNDERSHOCK           = 206064,   // AR2 the resolve copy (Nature)
        SPELL_ARUGAL_THUNDERSHOCK_STUN      = 206065,   // AR2 the 1.5 s stun rider
        SPELL_ARUGAL_VOID_BOLT              = 206066,   // AR3 the 3 s interruptible cast (Shadow, RefFlat)
        SPELL_ARUGAL_ARUGALS_CURSE          = 206067,   // AR4 the instant look on the cursed player (+10 by script)
        SPELL_ARUGAL_SHADOW_PORT            = 206068,   // AR5 the 1 s flicker (cast bar), then the teleport
        SPELL_ARUGAL_TURNED                 = 206069,   // AR6 charm + Glutton transform, as long as the charm
        SPELL_ARUGAL_TURNED_BURST           = 206070,   // AR6 the morph burst as a player turns (self look)
        SPELL_ARUGAL_WARD_CAST_ASHCROMBE    = 206071,   // AR7 Ashcrombe draws the circle (look, at the ward)
        SPELL_ARUGAL_WARD_CAST_ADAMANT      = 206072,   // AR7 Adamant throws the vial (missile, at the ward)
        SPELL_ARUGAL_WARD_RUNE              = 206073,   // AR7 the arcane rune on the ward stalker (Ashcrombe)
        SPELL_ARUGAL_WARD_SMOKE             = 206074,   // AR7 the cleansing cloud on the ward stalker (Adamant)
        SPELL_ARUGAL_WARD_PULSE             = 206075,   // AR7 the cleanse on each player inside (look)
        SPELL_ARUGAL_MOONRISE_CAST          = 206076,   // AR9 heroic: the 3 s cast bar
        SPELL_ARUGAL_MOONRISE               = 206077,   // AR9 heroic: the moon on Arugal for the rest of the fight
        SPELL_ARUGAL_MOONLIGHT              = 206078,   // AR9 heroic: the moonlight shafts (on strike stalkers)
        SPELL_ARUGAL_CURSE_GLOW             = 206079,   // AR1 look at 50+ stacks (hidden aura)
        SPELL_ARUGAL_CURSE_TINT             = 206080,   // AR1 look at 80+ stacks (hidden aura)
        // 206081-206084 spare; 206085-206089 are S10's (Face Him Alone)
    };
    static_assert(kSlice.Contains(SPELL_ARUGAL_WORGENS_CURSE), "Arugal spells sit in his slice");
    static_assert(kSlice.Contains(SPELL_ARUGAL_CURSE_TINT), "Arugal spells sit in his slice");
    static_assert(!ShadowfangKeepRework::kSpellsFaceHimAlone.Contains(SPELL_ARUGAL_CURSE_TINT), "S10 keeps its ids");

    std::uint32_t constexpr SPELL_ASHCROMBES_TELEPORT = 6422;  // stock: Ashcrombe leaves (Face Him Alone, S10)

    // The curse meter's aura on this difficulty (the bots' ward eligibility and the turn check read it).
    constexpr std::uint32_t CurseSpell(bool heroic)
    {
        return heroic ? SPELL_ARUGAL_WORGENS_CURSE_HEROIC : SPELL_ARUGAL_WORGENS_CURSE;
    }

    // Registry tags (the build spec's AR numbers).
    enum ArugalTags : std::uint32_t
    {
        TAG_THUNDERSHOCK    = 2,
        TAG_WARD            = 7,
    };

    // Descriptor phases (Mechanic::SetPhase): the kill order switches at the moon.
    std::uint32_t constexpr kPhaseNormal = 1;
    std::uint32_t constexpr kPhaseMoonrise = 2;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SK "Tuning starting points" and the build spec table)
    // ----------------------------------------------------------------------------------------------------------------

    // AR1 Worgen's Curse: a 100-stack meter, +1 every 3 s for everyone (normal and heroic); Moonrise +2 every second.
    std::uint32_t constexpr kCurseMax = 100;
    std::uint32_t constexpr kTurnAt = 100;                      // AR6
    inline constexpr Ms kSeepEvery{ 3000 };
    std::uint32_t constexpr kSeepStacks = 1;
    inline constexpr Ms kMoonSeepEvery{ 1000 };
    std::uint32_t constexpr kMoonSeepStacks = 2;
    std::uint32_t constexpr kGlowAt = 50;                       // the stack looks (VISUALS-REPORT gap 21)
    std::uint32_t constexpr kTintAt = 80;

    // AR8 Feral Power (heroic): +2% damage and healing done per full 10 stacks, up to +18% at 90.
    std::uint32_t constexpr kFeralPctPerStep = 2;
    std::uint32_t constexpr kFeralStepStacks = 10;
    std::uint32_t constexpr kFeralMaxSteps = 9;

    // AR2 Thundershock: a 2 s cast, 8 yd around him, 30% Nature, +15 stacks and a 1.5 s stun on anyone still inside (no
    // Weakened, Dungeon ruling 13). Normal first at 10 s, then every 10; heroic every 5 (first at 7 s, after the first
    // Shadow Port's flicker).
    inline constexpr NH<Ms> kThundershockFirst{ Ms(10000), Ms(7000) };
    inline constexpr NH<Ms> kThundershockEvery{ Ms(10000), Ms(5000) };
    inline constexpr Ms kThundershockCast{ 2000 };
    float constexpr kThundershockRadius = 8.f;
    inline constexpr NH<float> kThundershockPct{ 30.f, 30.f };
    std::int32_t constexpr kThundershockStacks = 15;

    // AR3 Void Bolt: a real 3 s interruptible cast on his target, back to back between the other casts; 15% / 25%
    // Shadow, +3 stacks on the target when it lands.
    inline constexpr Ms kVoidBoltCast{ 3000 };
    inline constexpr NH<float> kVoidBoltPct{ 15.f, 25.f };
    std::int32_t constexpr kVoidBoltStacks = 3;
    float constexpr kVoidBoltRange = 40.f;

    // AR4 Arugal's Curse: instant, +10 stacks on a random non-tank within 30 yd. 15 s, then every 25 (normal) / 20.
    inline constexpr Ms kCurseCastFirst{ 15000 };
    inline constexpr NH<Ms> kCurseCastEvery{ Ms(25000), Ms(20000) };
    std::int32_t constexpr kCurseCastStacks = 10;
    float constexpr kCurseCastRange = 30.f;

    // AR5 Shadow Port: 5 s, then every 20 s (both difficulties): a 1 s flicker, then the next spot.
    inline constexpr Ms kPortFirst{ 5000 };
    inline constexpr Ms kPortEvery{ 20000 };
    inline constexpr Ms kPortFlicker{ 1000 };

    // AR7 Ashcrombe's Ward: 20 s, then every 20 s; 10 s life; a player inside for 3 s makes it pulse: everyone inside
    // loses 10 stacks, then it fades. Bots go at 20 stacks or more (the tank too); a turned player (100) never counts.
    inline constexpr Ms kWardFirst{ 20000 };
    inline constexpr Ms kWardEvery{ 20000 };
    inline constexpr Ms kWardLife{ 10000 };
    inline constexpr Ms kWardDwell{ 3000 };
    inline constexpr Ms kWardPoll{ 250 };
    std::int32_t constexpr kWardCleanse = -10;
    std::uint8_t constexpr kWardMinStacks = 20;
    std::uint8_t constexpr kWardMaxStacks = kTurnAt - 1;        // F1 open item 2: turned players are never eligible
    float constexpr kWardRadius = 5.f;
    float constexpr kMoonWardRadius = 3.f;                      // AR9: the Moonrise wards
    std::uint8_t constexpr kMoonWardBodies = 2;                 // the two players with the most stacks
    float constexpr kWardZBand = 3.f;                           // inside = 2D radius and |dz| at most this

    // AR9 Moonrise (heroic): at 30%, a 3 s cast; then the seep is +2 per second and he casts nothing else.
    float constexpr kMoonrisePct = 30.f;
    inline constexpr Ms kMoonriseCast{ 3000 };

    // The all-turned check (handoff section 7 #22) runs on this beat.
    inline constexpr Ms kTurnCheckEvery{ 500 };

    // ----------------------------------------------------------------------------------------------------------------
    // The room: Shadow Port spots, the wards on each spot's level, the grip landings, the prisoner's path
    // ----------------------------------------------------------------------------------------------------------------

    enum SpotId : std::uint8_t
    {
        SPOT_SPAWN = 0,     // his spawn on the platform (guid 16255)
        SPOT_7586 = 1,      // stock spot 7586 on the platform, 8.3 yd from the spawn
        SPOT_7136 = 2,      // stock spot 7136 at the top of the antechamber ramp (the other upper level)
    };
    std::size_t constexpr kSpotCount = 3;
    std::size_t constexpr kMaxWardPoints = 3;

    struct Spot
    {
        char const* name;
        Point3 pos;
        std::uint32_t stockSpell;                               // its spell_target_position spell (0: the spawn)
        std::array<Point3, kMaxWardPoints> wards;               // 5 yd wards: 9.5-12.7 yd from him, clearance 3+
        std::uint8_t wardCount;
        std::array<Point3, kMaxWardPoints> moonWards;           // 3 yd wards: 6-11 yd from him, clearance 2.3+
        std::uint8_t moonWardCount;
        Point3 landing;                                         // ArenaGuard grip landing: his level, outside his ring
    };

    // [navmesh estimate] points (S9's measurements on the map 33 tiles, the NAVMESH-REPORT method): every ward point
    // lies on its spot's level, within 1.6 yd of its height. Clearances in the comments are navmesh values.
    inline std::array<Spot, kSpotCount> constexpr kSpots{ {
        { "spawn", ShadowfangKeepRework::kArugalSpawn, 0,
            { { { -84.75f, 2157.75f, 156.22f },             // 9.6 yd, clearance 3.8 (the gallery's mouth)
                {}, {} } }, 1,
            { { { -81.75f, 2155.75f, 155.83f },             // 6.0 yd, clearance 5.6
                { -71.75f, 2155.75f, 155.83f },             // 6.0 yd, clearance 2.7 (the platform's east end)
                { -78.25f, 2158.25f, 155.83f } } }, 3,      // 6.0 yd, clearance 2.8
            { -84.75f, 2157.75f, 156.22f } },
        { "7586", ShadowfangKeepRework::kShadowPortSpots[1], 7586,
            { { { -76.25f, 2154.75f, 155.83f },             // 9.5 yd, clearance 5.3 (the open floor at his spawn)
                { -74.75f, 2151.25f, 155.71f },             // 10.2 yd, clearance 4.3
                { -72.75f, 2154.25f, 155.81f } } }, 3,      // 12.7 yd, clearance 3.6
            { { { -77.75f, 2153.75f, 155.80f },             // 7.7 yd, clearance 5.2
                { -84.75f, 2157.25f, 156.14f },             // 6.2 yd, clearance 4.1
                { -74.25f, 2154.25f, 155.81f } } }, 3,      // 11.2 yd, clearance 5.0
            { -76.25f, 2154.75f, 155.83f } },
        { "7136", ShadowfangKeepRework::kShadowPortSpots[0], 7136,
            { { { -113.75f, 2160.25f, 156.12f },            // 9.7 yd, clearance 3.7 (by the lair door)
                { -115.25f, 2160.75f, 155.83f },            // 11.2 yd, clearance 3.1
                {} } }, 2,
            { { { -111.75f, 2159.25f, 156.49f },            // 7.4 yd, clearance 5.0
                { -111.25f, 2162.75f, 156.43f },            // 9.6 yd, clearance 2.5
                { -114.25f, 2156.75f, 155.93f } } }, 3,     // 8.8 yd, clearance 2.3
            { -113.75f, 2160.25f, 156.12f } },
    } };

    // The lair prisoner's way in on the pull: from the wait point by the lair door (the instance's summon) through the
    // antechamber to the gap's edge, then a jump across onto the gallery, where it works for the rest of the fight
    // (handoff section 3.8's prisoner spot: it overlooks both upper levels, 14.6 to 24.6 yd from every ward point).
    Point3 constexpr kPrisonerJumpOff{ -103.75f, 2162.75f, 155.73f };     // the antechamber's edge at the gap
    Point3 constexpr kPrisonerPost = ShadowfangKeepRework::kLairPrisonerGallery;
    float constexpr kPrisonerJumpSpeedXY = 9.f;
    float constexpr kPrisonerJumpMinSpeedZ = 6.f;
    inline constexpr Ms kPrisonerJumpLand{ 1500 };          // after the jump: on the post
    inline constexpr Ms kPrisonerStepInTimeout{ 12000 };    // not posted by then: put on the post
    std::uint32_t constexpr kPrisonerPointJumpOff = 1;      // MovePoint ids
    std::uint32_t constexpr kPrisonerPointLeave = 2;

    // ----------------------------------------------------------------------------------------------------------------
    // Rules
    // ----------------------------------------------------------------------------------------------------------------

    // AR5: the next spot, never the one he stands on. `rand(n)` returns [0, n).
    template <class Rand>
    SpotId PickPortSpot(SpotId current, Rand&& rand)
    {
        std::uint32_t const others = static_cast<std::uint32_t>(kSpotCount - 1);
        std::uint32_t const pick = static_cast<std::uint32_t>(rand(others)) % others;
        return static_cast<SpotId>(pick >= current ? pick + 1 : pick);
    }

    // The spot nearest a point on the plane (where the boss stands: the grip landing's level).
    inline SpotId NearestSpot(Vec2 p)
    {
        std::size_t best = 0;
        for (std::size_t i = 1; i < kSpotCount; ++i)
            if (DungeonKit::Distance(kSpots[i].pos.XY(), p) < DungeonKit::Distance(kSpots[best].pos.XY(), p))
                best = i;
        return static_cast<SpotId>(best);
    }

    enum class WardKind : std::uint8_t
    {
        Normal,     // 5 yd, every player at 20 to 99 stacks (bots: Stack); none on hard mode
        FullMoon,   // heroic, as Moonrise starts: 5 yd, every player up to 99 stacks (Stack)
        Moon,       // heroic, after Moonrise: 3 yd, the two players with the most stacks (Soak, 2 bodies)
    };

    struct WardRule
    {
        float radius;
        std::uint8_t minStacks;
        std::uint8_t maxStacks;
        bool soak;                  // false: Stack (every eligible player goes in); true: Soak of `bodies`
        std::uint8_t bodies;
    };

    constexpr WardRule RuleFor(WardKind kind)
    {
        switch (kind)
        {
            case WardKind::FullMoon:
                return { kWardRadius, 0, kWardMaxStacks, false, 0 };
            case WardKind::Moon:
                return { kMoonWardRadius, 0, kWardMaxStacks, true, kMoonWardBodies };
            case WardKind::Normal:
            default:
                return { kWardRadius, kWardMinStacks, kWardMaxStacks, false, 0 };
        }
    }

    // The ward point for `kind` on `spot`'s level: a random one of its list. `rand(n)` returns [0, n).
    template <class Rand>
    Point3 PickWardPoint(SpotId spot, WardKind kind, Rand&& rand)
    {
        Spot const& s = kSpots[spot];
        bool const small = kind == WardKind::Moon;
        std::uint32_t const n = small ? s.moonWardCount : s.wardCount;
        std::uint32_t const i = n ? static_cast<std::uint32_t>(rand(n)) % n : 0;
        return small ? s.moonWards[i] : s.wards[i];
    }

    // AR9's last full ward "beside the group": the full-ward point of `spot` nearest the group's centre.
    inline Point3 WardPointNearest(SpotId spot, Vec2 groupCenter)
    {
        Spot const& s = kSpots[spot];
        std::size_t best = 0;
        for (std::size_t i = 1; i < s.wardCount; ++i)
            if (DungeonKit::Distance(s.wards[i].XY(), groupCenter)
                < DungeonKit::Distance(s.wards[best].XY(), groupCenter))
                best = i;
        return s.wards[best];
    }

    // Inside a ward: the 2D radius and the level's z band.
    constexpr bool InsideWard(float dist2d, float dz, float radius)
    {
        return dist2d <= radius && dz <= kWardZBand && dz >= -kWardZBand;
    }

    // AR1: the meter after `delta`, clamped to [0, kCurseMax].
    constexpr std::uint32_t CurseAfter(std::uint32_t current, std::int32_t delta)
    {
        std::int64_t const v = static_cast<std::int64_t>(current) + delta;
        return v <= 0 ? 0u : (v >= kCurseMax ? kCurseMax : static_cast<std::uint32_t>(v));
    }

    // AR6: the meter turns its player.
    constexpr bool Turns(std::uint32_t stacks)
    {
        return stacks >= kTurnAt;
    }

    // AR8: Feral Power's stacks (+2% each) for a curse count, on heroic only.
    constexpr std::uint32_t FeralSteps(bool heroic, std::uint32_t curse)
    {
        if (!heroic)
            return 0;
        std::uint32_t const steps = curse / kFeralStepStacks;
        return steps < kFeralMaxSteps ? steps : kFeralMaxSteps;
    }

    constexpr std::uint32_t FeralPct(bool heroic, std::uint32_t curse)
    {
        return FeralSteps(heroic, curse) * kFeralPctPerStep;
    }

    // The looks a curse count shows (the 50+ glow, the 80+ tint).
    constexpr bool ShowsGlow(std::uint32_t curse) { return curse >= kGlowAt; }
    constexpr bool ShowsTint(std::uint32_t curse) { return curse >= kTintAt; }

    // AR9: the moon rises once, on heroic, when his health falls to 30% or below.
    constexpr bool MoonriseDue(bool heroic, bool started, float healthPct)
    {
        return heroic && !started && healthPct <= kMoonrisePct;
    }

    // Handoff section 7 #22: every living player of the fight is turned (and there is at least one).
    constexpr bool AllTurned(std::uint32_t livingPlayers, std::uint32_t turned)
    {
        return livingPlayers > 0 && turned >= livingPlayers;
    }

    // Seconds until a player at `stacks` turns under a steady seep of `perTick` every `every` (no wards, no hits).
    constexpr float SecondsToTurn(std::uint32_t stacks, std::uint32_t perTick, Ms every)
    {
        if (stacks >= kTurnAt || !perTick)
            return 0.f;
        std::uint32_t const ticks = (kTurnAt - stacks + perTick - 1) / perTick;
        return static_cast<float>(ticks) * static_cast<float>(every.count()) / 1000.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's timeline: driven by the AI's diff every tick, cast bar or not (the Pilot's lesson R1 S-2), so a Void
    // Bolt never pushes a Thundershock or a Shadow Port back. The AI starts a due step when he is free; a Void Bolt
    // starts only when it ends before the next Thundershock or Shadow Port is due (heroic: Thundershock's 2 s cast plus
    // one 3 s Void Bolt fill his 5 s cycle exactly).
    // ----------------------------------------------------------------------------------------------------------------
    class Timeline
    {
    public:
        static constexpr Ms kNever{ std::numeric_limits<std::int64_t>::max() / 4 };

        void Start(bool heroic)
        {
            _heroic = heroic;
            _now = Ms(0);
            _moon = false;
            _nextSeep = kSeepEvery;
            _nextThundershock = kThundershockFirst(heroic);
            _nextCurse = kCurseCastFirst;
            _nextPort = kPortFirst;
            _nextWard = kWardFirst;
        }

        void Advance(Ms diff) { _now += diff; }
        Ms Now() const { return _now; }
        bool Heroic() const { return _heroic; }
        bool Moon() const { return _moon; }

        bool ThundershockDue() const { return _now >= _nextThundershock; }
        bool CurseDue() const { return _now >= _nextCurse; }
        bool PortDue() const { return _now >= _nextPort; }
        bool WardDue() const { return _now >= _nextWard; }

        // Each step's next time follows its own cadence from the time it was due (no drift from a late start).
        void ThundershockDone() { _nextThundershock += kThundershockEvery(_heroic); }
        void CurseDone() { _nextCurse += kCurseCastEvery(_heroic); }
        void PortDone() { _nextPort += kPortEvery; }
        void WardDone() { _nextWard += kWardEvery; }

        // A Void Bolt cast now ends before the next Thundershock and Shadow Port are due.
        bool VoidBoltFits() const
        {
            if (_moon || _nextPort >= kNever)
                return false;
            Ms const end = _now + kVoidBoltCast;
            return end <= _nextThundershock && end <= _nextPort;
        }

        // The seep stacks due now (a late tick still counts each missed tick).
        std::uint32_t TakeSeep()
        {
            std::uint32_t stacks = 0;
            Ms const every = _moon ? kMoonSeepEvery : kSeepEvery;
            std::uint32_t const per = _moon ? kMoonSeepStacks : kSeepStacks;
            while (_now >= _nextSeep)
            {
                stacks += per;
                _nextSeep += every;
            }
            return stacks;
        }

        // AR9: from the start of the cast he casts nothing else. The full ward placed as the cast starts takes the
        // ward grid's place: the next ward comes kWardEvery after it, so a grid ward due during its life never
        // replaces it before the group can pulse it (R2 S-1).
        void BeginMoonrise()
        {
            StopCasts();
            _nextWard = _now + kWardEvery;
        }

        // AR9: the cast ended: the seep turns to +2 every second, from now. The ward grid keeps the restart above.
        void MoonRisen()
        {
            StopCasts();
            _moon = true;
            _nextSeep = _now + kMoonSeepEvery;
        }

        Ms NextThundershock() const { return _nextThundershock; }
        Ms NextPort() const { return _nextPort; }
        Ms NextCurse() const { return _nextCurse; }
        Ms NextWard() const { return _nextWard; }
        Ms NextSeep() const { return _nextSeep; }

    private:
        void StopCasts()
        {
            _nextThundershock = kNever;
            _nextCurse = kNever;
            _nextPort = kNever;
        }

        bool _heroic = false;
        bool _moon = false;
        Ms _now{ 0 };
        Ms _nextSeep{ kSeepEvery };
        Ms _nextThundershock{ kNever };
        Ms _nextCurse{ kNever };
        Ms _nextPort{ kNever };
        Ms _nextWard{ kNever };
    };

    // What Arugal starts when he is free (not casting) on this tick, in priority order.
    enum class Step : std::uint8_t
    {
        None,
        ShadowPort,
        Thundershock,
        VoidBolt,
    };

    inline Step NextStep(Timeline const& t)
    {
        if (t.PortDue())
            return Step::ShadowPort;
        if (t.ThundershockDue())
            return Step::Thundershock;
        if (t.VoidBoltFits())
            return Step::VoidBolt;
        return Step::None;
    }

    // AR7: one ward's life. Feed it the players inside every poll; it pulses once someone has stood inside for the
    // dwell (then it is spent), and expires at the end of its life.
    class WardLife
    {
    public:
        enum class Event : std::uint8_t
        {
            None,
            Pulse,
            Expired,
        };

        void Start()
        {
            _live = true;
            _age = Ms(0);
            _stood.clear();
        }

        void Stop() { _live = false; _stood.clear(); }
        bool Live() const { return _live; }
        Ms Age() const { return _age; }

        // `inside` are the players inside now (raw guids; alive, not turned).
        Event Update(std::vector<std::uint64_t> const& inside, Ms diff)
        {
            if (!_live)
                return Event::None;
            _age += diff;
            std::vector<std::pair<std::uint64_t, Ms>> next;
            bool pulse = false;
            for (std::uint64_t const id : inside)
            {
                Ms stood = diff;
                for (auto const& [prev, ms] : _stood)
                    if (prev == id)
                        stood = ms + diff;
                next.emplace_back(id, stood);
                if (stood >= kWardDwell)
                    pulse = true;
            }
            _stood = std::move(next);
            if (pulse)
            {
                Stop();
                return Event::Pulse;
            }
            if (_age >= kWardLife)
            {
                Stop();
                return Event::Expired;
            }
            return Event::None;
        }

    private:
        bool _live = false;
        Ms _age{ 0 };
        std::vector<std::pair<std::uint64_t, Ms>> _stood;
    };
}

#endif
