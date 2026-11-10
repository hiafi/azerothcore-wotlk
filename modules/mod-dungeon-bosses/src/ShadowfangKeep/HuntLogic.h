/*
 * mod-dungeon-bosses, Shadowfang Keep: the Hunt, the pure part (no engine headers) of the chase Odo the Blindwatcher
 * (WP-S5, OD1 / OD2) and Baron Silverlaine's Echo of Odo (WP-S3, BS5) share. The engine half is Hunt.h.
 *
 * A Hunt: the chaser howls (`warn`, standing), then stalks one player at `ratePct` % of a player's run speed for
 * `chase`, inside a registry circle of `radius` on the chaser that only the hunted player is eligible for. Every `tick`
 * the circle resolves; a pass that holds the player is the catch (the Maul), and every other pass re-aims the chaser.
 * This is exactly what mod-boss-mechanics' `sfk-hunt` drill does (MechanicDrill.h "the chase", MechanicCommand.cpp
 * RegisterHunt: the same radius, warn, tick, rate and anchor), so the drill measures what the boss does.
 *
 * Build spec (docs/dungeons/shadowfang-keep-rework.md): OD1 3 yd, 2 s howl, 10 s, 80% normal / 95% heroic; OD2 Maul
 * 3 s stun + 35% over 3 s. BS5 the echo: 3 yd, 2 s howl, 8 s, 80%; Maul 1.5 s stun + 20% over 1.5 s.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_HUNT_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_HUNT_LOGIC_H

#include "DungeonKitLogic.h"
#include <algorithm>
#include <cstdint>
#include <vector>

namespace SfkHunt
{
    // A player runs 7 yd/s, and a creature's MOVE_RUN rate 1.0 is the same 7 yd/s (DungeonKit::SpeedFor).
    inline constexpr float kPlayerRunYdS = DungeonKit::kPlayerRunYdPerSec;

    // The numbers of one Hunt. The drill's line for the same chase: `hunt <radius> <warnMs> speed=<ratePct / 100>
    // persist=<chaseMs> tick=<tickMs> pick=nontank`.
    struct HuntTuning
    {
        float ratePct = 80.f;               // % of a player's run speed while chasing
        std::uint32_t warnMs = 2000;        // the howl: the chaser stands, the circle shows
        std::uint32_t chaseMs = 10000;      // the chase (the circle's persistent passes)
        std::uint32_t tickMs = 200;         // one resolve pass (a catch check and a re-aim) every tick
        float radius = 3.f;                 // the catch circle on the chaser
    };

    // OD1, Odo the Blindwatcher: normal 80%, heroic 95% (Relentless Hunt). The drill `sfk-hunt` steps 1 and 3.
    inline constexpr HuntTuning kOdoHuntNormal{ 80.f, 2000, 10000, 200, 3.f };
    inline constexpr HuntTuning kOdoHuntHeroic{ 95.f, 2000, 10000, 200, 3.f };
    // BS5, Baron Silverlaine's Echo of Odo: 80% on both difficulties, 8 s.
    inline constexpr HuntTuning kEchoHunt{ 80.f, 2000, 8000, 200, 3.f };

    constexpr HuntTuning OdoHunt(bool heroic)
    {
        return heroic ? kOdoHuntHeroic : kOdoHuntNormal;
    }

    // The chaser's MOVE_RUN rate (SetSpeed) and its speed in yd/s.
    constexpr float RunRate(float ratePct)
    {
        return DungeonKit::SpeedFor(ratePct);
    }

    constexpr float ChaserYdS(float ratePct)
    {
        return RunRate(ratePct) * kPlayerRunYdS;
    }

    // The yards a player who walks straight away for the whole chase gains on the chaser (navmesh report: 14 yd at
    // 80% and 3.5 yd at 95% over 10 s; 11.2 yd for the echo's 8 s).
    constexpr float GainYd(HuntTuning const& t)
    {
        return (kPlayerRunYdS - ChaserYdS(t.ratePct)) * static_cast<float>(t.chaseMs) / 1000.f;
    }

    // How long a player who stands `gapYd` from the chaser when the chase starts has before the circle holds them
    // (the slack to start walking): (gap - radius) / chaser speed, in ms; 0 when already inside.
    constexpr std::uint32_t CatchSlackMs(HuntTuning const& t, float gapYd)
    {
        float const yd = gapYd - t.radius;
        float const speed = ChaserYdS(t.ratePct);
        if (yd <= 0.f || speed <= 0.f)
            return 0;
        return static_cast<std::uint32_t>(yd / speed * 1000.f);
    }

    // The whole hunt, warn included: the Hunted debuff's duration and the bell soak's window.
    constexpr std::uint32_t TotalMs(HuntTuning const& t)
    {
        return t.warnMs + t.chaseMs;
    }

    // The number of resolve passes (catch checks) of a full chase.
    constexpr std::uint32_t Passes(HuntTuning const& t)
    {
        return t.tickMs ? t.chaseMs / t.tickMs : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Maul (the catch): a stun plus a bleed whose total is a percent of reference health. The aura spell's bleed
    // effect stores the total percent in its BasePoints (calculated value); spell_sfk_hunt_maul turns it into equal
    // ticks of RefFlat(caster, total / ticks). Odo's Maul: 35% over 3 s, 1 s ticks; the echo's: 20% over 1.5 s, 0.5 s
    // ticks.
    // ----------------------------------------------------------------------------------------------------------------

    constexpr std::uint32_t MaulTicks(std::uint32_t durationMs, std::uint32_t amplitudeMs)
    {
        return amplitudeMs ? durationMs / amplitudeMs : 0;
    }

    constexpr float MaulTickPct(float totalPct, std::uint32_t durationMs, std::uint32_t amplitudeMs)
    {
        std::uint32_t const ticks = MaulTicks(durationMs, amplitudeMs);
        return ticks ? totalPct / static_cast<float>(ticks) : 0.f;
    }

    // A pass of the catch circle is the catch only when it hit the hunted player (Stratholme SWEEP-2 D5: the hunted
    // player's pet, standing on Odo where the hunt starts, ended the hunt and took the Maul). The circle is players
    // only as well (Eligibility::playersOnly), so the pet is not hit at all.
    template <class Id>
    bool IsCatch(std::vector<Id> const& hits, Id const& hunted)
    {
        return std::find(hits.begin(), hits.end(), hunted) != hits.end();
    }

    // Why a hunt ended (Hunt::Update reports it once).
    enum class HuntEnd : std::uint8_t
    {
        None = 0,       // still running, or no hunt
        Caught,         // a pass held the hunted player: the Maul landed
        Escaped,        // the chase ran its full time
        TargetLost,     // the hunted player died, left the map, or the chaser lost the player
        Stopped,        // the script ended it (a bell, the chaser's death, a reset)
    };

    inline char const* HuntEndName(HuntEnd e)
    {
        switch (e)
        {
            case HuntEnd::Caught: return "caught";
            case HuntEnd::Escaped: return "escaped";
            case HuntEnd::TargetLost: return "target-lost";
            case HuntEnd::Stopped: return "stopped";
            default: return "none";
        }
    }
}

#endif
