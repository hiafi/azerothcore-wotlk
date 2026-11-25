/*
 * mod-dungeon-bosses, Ragefire Chasm D3:
 * Bazzalan (11519), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/ragefire-chasm-rework.md "Bazzalan" (BZ1-BZ8), handoff section 3.5 row D3, 3.6, 3.8 (his ridge), 3.12.
 * Tested by tests/rfc_bazzalan_test.cpp. The numbers are RagefireChasmRework::Bazzalan (`Tune` below): never restated
 * here; a number the spec does not give is a constant of this file, marked so.
 *
 *   Spells       the WP's ids, inside kSpellsBazzalan (213610-213649), declared in apps/dbc-tools
 *                source/npcs/ragefire_chasm/bazzalan.py
 *   Finishers    which difficulty uses which, which are kickable, the normal shuffled bag and the heroic alternation
 *   Cadence      the Sinister Strike clock around a finisher and the fight's nominal finisher times
 *   Shadowstep   the chain's times, the landing behind a player and the return to the tank, on the ridge polygon
 *   Envenom      the percent by Deadly Poison stacks
 *   Reach        his arena and the rim band he reaches from its edge (ReachArena, EdgeSpot, JumpGrace)
 *   Outsiders    who the random picks skip
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_BAZZALAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_RFC_BAZZALAN_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "RagefireChasmRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace RfcBazzalan
{
    namespace Tune = RagefireChasmRework::Bazzalan;

    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (RagefireChasmRework.h; ids.yaml reservation `ragefire_chasm`).
    inline constexpr RagefireChasmRework::IdSlice kSpellSlice = RagefireChasmRework::kSpellsBazzalan;

    enum BazzalanSpells : std::uint32_t
    {
        SPELL_BZ_SINISTER_STRIKE    = kSpellSlice.first + 0,    // 213610 BZ1 a swing plus kStrikeBonus, triggered
        SPELL_BZ_COMBO_POINTS       = kSpellSlice.first + 1,    // 213611 BZ1 the stacking aura on him (1 to 5)
        SPELL_BZ_EVISCERATE         = kSpellSlice.first + 2,    // 213612 BZ3 the kickable 2 s cast (Physical)
        SPELL_BZ_RUPTURE_CAST       = kSpellSlice.first + 3,    // 213613 BZ4 the 2 s bar (Shadow)
        SPELL_BZ_RUPTURE_LOOK       = kSpellSlice.first + 4,    // 213614 BZ4 the cut on the player (look only)
        SPELL_BZ_RUPTURE            = kSpellSlice.first + 5,    // 213615 BZ4 normal: the 12 s bleed
        SPELL_BZ_RUPTURE_HEROIC     = kSpellSlice.first + 6,    // 213616 BZ4 heroic: the bleed to the end of the fight
        SPELL_BZ_FAN_CAST           = kSpellSlice.first + 7,    // 213617 BZ5 and each BZ7 spin: the 2 s bar (Shadow)
        SPELL_BZ_FAN                = kSpellSlice.first + 8,    // 213618 BZ5 / BZ7 the hit (resolve copy, Physical)
        SPELL_BZ_ENVENOM            = kSpellSlice.first + 9,    // 213619 BZ6 the kickable 2 s cast (Nature, heroic)
        SPELL_BZ_SHADOWSTEP_CAST    = kSpellSlice.first + 10,   // 213620 BZ7 the 2 s bar (Shadow, heroic)
        SPELL_BZ_SHADOWSTEP_LOOK    = kSpellSlice.first + 11,   // 213621 BZ7 the smoke, leaving and landing
        SPELL_BZ_DEADLY_POISON      = kSpellSlice.first + 12,   // 213622 BZ8 the copy of 2818
        SPELL_BZ_WOUND_POISON       = kSpellSlice.first + 13,   // 213623 BZ8 heroic
        SPELL_BZ_CRIPPLING_POISON   = kSpellSlice.first + 14,   // 213624 BZ7 heroic: the spin's rider
        // 213625-213649 spare
    };
    static_assert(SPELL_BZ_CRIPPLING_POISON <= kSpellSlice.last, "Bazzalan's spells must stay in his slice");

    // Stock spells of 11519 retired from the kit (both carry live rogue rework rows): never cast by the rework.
    inline constexpr std::uint32_t SPELL_STOCK_SINISTER_STRIKE = 14873;
    inline constexpr std::uint32_t SPELL_STOCK_DEADLY_POISON = 2818;

    // Registry tags: the drill's (BM MechanicDrill.h kRfcTagFan, kRfcTagStepFan; section 3.5 rule 34).
    enum BazzalanTags : std::uint32_t
    {
        TAG_BZ_FAN          = 8,    // BZ5 the 8 yd Fan of Knives
        TAG_BZ_STEP_FAN     = 9,    // BZ7 the 6 yd spin after each Shadowstep
    };

    // ----------------------------------------------------------------------------------------------------------------
    // BZ1 Sinister Strike, BZ2 the cadence around a finisher
    // ----------------------------------------------------------------------------------------------------------------

    // The live 14873's flat bonus on top of his weapon damage (BasePoints 0 + DieSides 1).
    inline constexpr std::uint32_t kStrikeBonus = 1;

    // The first Sinister Strike after a finisher, from the finisher's nominal end (not in the spec as a number: it is
    // what its two cycles come to, 5 x 3 s + 2 s = about 17 s on normal and 4 x 2 s + 2 s = 10 s on heroic).
    inline constexpr NH<std::uint32_t> kStrikeAfterFinisherMs{ 3000, 0 };

    // The bar's nominal start of the first finisher and the start-to-start time of two 2 s finishers.
    constexpr std::uint32_t FirstFinisherMs(bool heroic)
    {
        return Tune::kStrikeFirstMs + (Tune::kComboMax - 1) * Tune::kStrikeEveryMs(heroic);
    }

    constexpr std::uint32_t FinisherCycleMs(bool heroic)
    {
        return Tune::kFinisherCastMs + kStrikeAfterFinisherMs(heroic)
            + (Tune::kComboMax - 1) * Tune::kStrikeEveryMs(heroic);
    }

    // Until the bar of the next finisher starts, with `points` up and the next Sinister Strike `strikeInMs` away.
    constexpr std::uint32_t NextFinisherInMs(bool heroic, std::uint32_t points, std::uint32_t strikeInMs)
    {
        if (points >= Tune::kComboMax)
            return 0;
        return strikeInMs + (Tune::kComboMax - points - 1) * Tune::kStrikeEveryMs(heroic);
    }

    // The fight's Sinister Strike clock: a due strike stays due (he strikes only in melee range, and never while a
    // finisher runs).
    class StrikeClock
    {
    public:
        void Start(std::uint64_t atMs)
        {
            _on = true;
            _dueMs = atMs;
        }

        void Stop() { _on = false; }
        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time, never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

        std::uint32_t InMs(std::uint64_t nowMs) const
        {
            return _on && _dueMs > nowMs ? static_cast<std::uint32_t>(_dueMs - nowMs) : 0;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // BZ2 the finisher bag
    // ----------------------------------------------------------------------------------------------------------------

    enum class Finisher : std::uint8_t
    {
        None,
        Eviscerate,     // BZ3
        Rupture,        // BZ4
        Fan,            // BZ5, normal only
        Envenom,        // BZ6, heroic only
        Shadowstep,     // BZ7, heroic only
    };

    constexpr char const* NameOf(Finisher f)
    {
        switch (f)
        {
            case Finisher::Eviscerate:
                return "eviscerate";
            case Finisher::Rupture:
                return "rupture";
            case Finisher::Fan:
                return "fan";
            case Finisher::Envenom:
                return "envenom";
            case Finisher::Shadowstep:
                return "shadowstep";
            default:
                return "none";
        }
    }

    constexpr bool Kickable(Finisher f)
    {
        return f == Finisher::Eviscerate || f == Finisher::Envenom;
    }

    constexpr bool UsedOn(Finisher f, bool heroic)
    {
        switch (f)
        {
            case Finisher::Eviscerate:
            case Finisher::Rupture:
                return true;
            case Finisher::Fan:
                return !heroic;
            case Finisher::Envenom:
            case Finisher::Shadowstep:
                return heroic;
            default:
                return false;
        }
    }

    inline constexpr std::array<Finisher, 3> kNormalBag{ { Finisher::Eviscerate, Finisher::Rupture, Finisher::Fan } };
    inline constexpr std::array<Finisher, 2> kHeroicKickable{ { Finisher::Eviscerate, Finisher::Envenom } };
    inline constexpr std::array<Finisher, 2> kHeroicOther{ { Finisher::Rupture, Finisher::Shadowstep } };

    // Normal: a shuffled bag of the three, each once before any repeats. Heroic (section 7 #34 A): a kickable one, then
    // one that is not, at random within each half, starting with the kickable half. `rand(n)` returns [0, n).
    class FinisherBag
    {
    public:
        void Reset(bool heroic)
        {
            _heroic = heroic;
            _kickableNext = true;
            _bag.clear();
        }

        template <class Rand>
        Finisher Draw(Rand&& rand)
        {
            if (_heroic)
            {
                auto const& half = _kickableNext ? kHeroicKickable : kHeroicOther;
                _kickableNext = !_kickableNext;
                return half[static_cast<std::size_t>(rand(2u)) % half.size()];
            }
            if (_bag.empty())
                _bag.assign(kNormalBag.begin(), kNormalBag.end());
            std::size_t const i = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(_bag.size()))) % _bag.size();
            Finisher const f = _bag[i];
            _bag.erase(_bag.begin() + static_cast<std::ptrdiff_t>(i));
            return f;
        }

    private:
        bool _heroic = false;
        bool _kickableNext = true;
        std::vector<Finisher> _bag;
    };

    // What to try for a drawn finisher, in order. A kickable one only itself: a refused cast (a silence) is tried
    // again, never swapped. A Rupture or a Shadowstep nobody can take now (everyone bleeds, everyone stands at a rim)
    // gives way to the rest of its half, then to the others, so the points are never stuck. (Heroic: a kickable one can
    // then follow a kickable one, only once everyone bleeds and nobody can be stepped to: five Ruptures, about 225 s.)
    inline std::vector<Finisher> AttemptOrder(Finisher drawn, bool heroic)
    {
        std::vector<Finisher> order{ drawn };
        if (Kickable(drawn))
            return order;
        auto add = [&order](Finisher f)
        {
            if (std::find(order.begin(), order.end(), f) == order.end())
                order.push_back(f);
        };
        if (heroic)
        {
            for (Finisher f : kHeroicOther)
                add(f);
            for (Finisher f : kHeroicKickable)
                add(f);
        }
        else
            for (Finisher f : { Finisher::Fan, Finisher::Eviscerate })
                add(f);
        return order;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ3, BZ6 the interrupt list; BZ8 the dispel list
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<std::uint8_t> kKickPriority{ 2, 4 };    // a reward on normal, expected on heroic (SM's scale)
    inline constexpr std::uint32_t kKickEveryHeroicMs = 20000;  // the bag's order: never two in a row
    inline constexpr std::uint8_t kDispelPriority = 1;          // poisons: a reward on every difficulty
    inline constexpr std::uint8_t kCripplingDispelPriority = 2; // it makes the next spin hit

    // BZ6: the percent of the tank row for `stacks` Deadly Poison consumed (at most kDeadlyStacks).
    constexpr float EnvenomPctTank(std::uint32_t stacks)
    {
        return Tune::kEnvenomPctPerStackTank * float(std::min(stacks, Tune::kDeadlyStacks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ7 Shadowstep and Fan of Knives
    // ----------------------------------------------------------------------------------------------------------------

    // The bar, then a landing every kShadowstepEveryMs (STAGE-G1 Q4: 2 to 2.5 s, never faster than the ring), then back
    // to the tank kShadowstepEveryMs after the last landing: the chain is SP's "about 7.5 sec".
    inline constexpr std::uint32_t kShadowstepEveryMs = 2500;
    static_assert(kShadowstepEveryMs >= Tune::kShadowstepWarnMs, "a ring resolves before the next step");

    constexpr std::uint32_t ShadowstepChainMs(std::uint32_t steps = Tune::kShadowstepCount)
    {
        return steps * kShadowstepEveryMs;
    }

    // A landing farther than this from its player (the polygon's clamp on a spur or in the neck) threatens nobody: that
    // player is not picked.
    inline constexpr float kLandingMaxOffYd = Tune::kShadowstepRadius - 1.f;
    // The floor under a landing must be this near the player's own height.
    inline constexpr float kLandingZBandYd = 4.f;

    // Where he appears behind a player at `player` facing `facing`: kShadowstepBehindYd behind, snapped into the ridge
    // arena (4 yd inside every edge, section 7 #23 A). Nothing for a player within kRimSkipYd of a rim, off the ridge,
    // or whose landing the clamp moves too far away.
    inline std::optional<Vec2> ShadowstepLanding(Vec2 player, float facing)
    {
        if (RagefireChasmRework::RimDistance(player) < Tune::kRimSkipYd)
            return std::nullopt;
        std::span<Vec2 const> const arena(RagefireChasmRework::kRidgeArenaPolygon);
        Vec2 const behind = DungeonKit::Advance(player, facing, -Tune::kShadowstepBehindYd);
        Vec2 const landing = RagefireChasmRework::StandSpot(arena, behind);
        if (DungeonKit::Distance(landing, player) > kLandingMaxOffYd)
            return std::nullopt;
        return landing;
    }

    // Back to the tank: kShadowstepBehindYd from it on the side he left from, on the arena.
    inline Vec2 ReturnSpot(Vec2 tank, Vec2 from)
    {
        std::span<Vec2 const> const arena(RagefireChasmRework::kRidgeArenaPolygon);
        Vec2 const beside = DungeonKit::Distance(tank, from) > 0.1f
            ? DungeonKit::Advance(tank, DungeonKit::BearingTo(tank, from), Tune::kShadowstepBehindYd) : tank;
        return RagefireChasmRework::StandSpot(arena, beside);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Where he fights, and who the random picks may take
    // ----------------------------------------------------------------------------------------------------------------

    // He stays on his arena (4 yd inside the rims, section 7 #23 A), but a target on the rim band is still his: he
    // stands at his edge and reaches it (RagefireChasmRework.h EdgeReachArena: 4.5 yd, melee range 5 yd, 3D). Off the
    // grown arena a target is out of his reach (the neck, a spur's tip, the hall below) and he turns to someone inside.
    //
    // East of the arena (the notch and the shelf past it: edges 13 to 20 of kRidgeArenaPolygon) the floor climbs up to
    // 0.8 yd per yd, to z 13: a target high on it is out of melee range from his edge, however near on the plane (RF-1
    // RF-M3). One floor for all eight (8.1 to 9.5 along them): every cell of the live navmesh tested.
    inline std::optional<float> ClimbFloor(std::size_t edge)
    {
        return edge >= 13 && edge <= 20 ? std::optional<float>(9.f) : std::nullopt;
    }

    inline DungeonKit::Arena ReachArena()
    {
        return RagefireChasmRework::EdgeReachArena(RagefireChasmRework::BazzalanArena(),
            RagefireChasmRework::kRidgeArenaPolygon, RagefireChasmRework::kRidgeZMin, RagefireChasmRework::kRidgeZMax,
            ClimbFloor);
    }

    // The height caps of the climb are for where a target stands: a jump (apex 1.64 yd, 0.83 s) on the level floor
    // beside it leaves the cap for a check or two, and the guard would turn him on someone else (RF-2 RF2-m1). So the
    // guard is not asked while his victim is in the air, kJumpAirMs at most: time on the ground earns it back tick for
    // tick, so a victim that keeps jumping out of his reach is judged all the same.
    inline constexpr std::uint32_t kJumpAirMs = 1000;

    class JumpGrace
    {
    public:
        // Every tick: true when the reach guard is not to be asked now.
        bool Skip(bool inAir, std::uint32_t diff)
        {
            _airMs = inAir ? std::min(_airMs + diff, kJumpAirMs + 1) : _airMs - std::min(_airMs, diff);
            return inAir && _airMs <= kJumpAirMs;
        }

        void Reset() { _airMs = 0; }

    private:
        std::uint32_t _airMs = 0;
    };

    // Where on his arena he stands for a target at `p`: strictly inside it.
    inline Vec2 EdgeSpot(Vec2 p)
    {
        return RagefireChasmRework::StandSpot(RagefireChasmRework::kRidgeArenaPolygon, p);
    }

    // The players a random pick skips, from (guid, on the ridge): whoever is off it, unless nobody is on it.
    inline std::vector<std::uint64_t> Outsiders(std::vector<std::pair<std::uint64_t, bool>> const& players)
    {
        std::vector<std::uint64_t> out;
        for (auto const& [guid, inside] : players)
            if (!inside)
                out.push_back(guid);
        return out.size() == players.size() ? std::vector<std::uint64_t>() : out;
    }

    // A slowed player's walk out of the spin (SP: 3.5 yd a second, 6 yd in 2 s).
    constexpr float SlowedReachYd(std::uint32_t ms)
    {
        return DungeonKit::kPlayerRunYdPerSec * (1.f - Tune::kCripplingSlowPct / 100.f) * float(ms) / 1000.f;
    }
}

#endif
