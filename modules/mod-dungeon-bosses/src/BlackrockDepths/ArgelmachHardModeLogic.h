/*
 * mod-dungeon-bosses, Blackrock Depths D16:
 * Golem Lord Argelmach's hard mode, the Prototype, the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/blackrock-depths-3-manufactory.md "Hard mode" and "Build spec" (AR4, AR11-AR13; rulings 57, 58, 88),
 * handoff sections 3.6, 3.7 row D16, 3.8 (P4 and the console spot), 7 #15. Tested by
 * tests/brd_argelmach_hard_mode_test.cpp; apps/dbc-tools source/npcs/blackrock_depths/argelmach_hard_mode.py declares
 * the same ids. It builds on D15's ArgelmachLogic.h (the golems, the pedestals, the chamber, Beat).
 *
 *   Spells    the WP's ids, inside kSpellsPrototype (211370-211409)
 *   Tuning    the hard mode's health, wake thresholds, Incineration, the Flamethrower
 *   Wrecks    the four wrecks (the three golems and Magmatron) and their Salvaged Cores' half-rate signatures
 *   Console   the Activation Console's refusals and spot
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_ARGELMACH_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_ARGELMACH_HARD_MODE_LOGIC_H

#include "ArgelmachLogic.h"
#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace BrdPrototype
{
    using BlackrockDepthsRework::Point3;
    using BrdArgelmach::Golem;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsPrototype;

    enum ArgelmachHardModeSpells : std::uint32_t
    {
        SPELL_PT_INCINERATION           = kSpellSlice.first + 0,    // 211370 AR11 the 3 s bar (Fire, not kickable)
        SPELL_PT_INCINERATION_HIT       = kSpellSlice.first + 1,    // 211371 AR11 15% to everyone (resolve copy)
        SPELL_PT_INCINERATION_LOOK      = kSpellSlice.first + 2,    // 211372 AR11 the fire ring (look)
        SPELL_PT_CLOUD_BURST            = kSpellSlice.first + 3,    // 211373 AR11 30% + Weakened by a cloud (resolve)
        SPELL_PT_FLAMETHROWER           = kSpellSlice.first + 4,    // 211374 AR12 the 2 s bar (Fire, not kickable)
        SPELL_PT_FLAMETHROWER_HIT       = kSpellSlice.first + 5,    // 211375 AR12 35% + Weakened (resolve copy)
        SPELL_PT_FLAMETHROWER_LOOK      = kSpellSlice.first + 6,    // 211376 AR12 the breath (look)
        SPELL_PT_SALVAGED_CORE          = kSpellSlice.first + 7,    // 211377 AR13 the running core (look, a state)
        // 211378-211409 spare
    };
    static_assert(SPELL_PT_SALVAGED_CORE <= kSpellSlice.last, "the Prototype's spells must stay in its slice");

    // Registry tags (D15 reserved 6 and 7 for these in ArgelmachLogic.h).
    inline constexpr std::uint32_t kTagIncineration = BrdArgelmach::TAG_AR_INCINERATION;
    inline constexpr std::uint32_t kTagFlamethrower = BrdArgelmach::TAG_AR_FLAMETHROWER;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Hard mode" and the tuning table; damage = % of the reference row, H: level 60 heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // Health (handoff section 3.6): him 500k, each golem 50k (set as it wakes), Magmatron 100k (WP-H's heroic row,
    // 310413, and the script at the wake).
    inline constexpr std::uint32_t kBossHealth = 500000;
    inline constexpr std::uint32_t kGolemHealth = 50000;
    inline constexpr std::uint32_t kMagmatronHealth = 100000;

    // AR4 (hard): Magmatron wakes at the pull, Toxitron at 80%, Electron at 60%, Arcanoton at 40%.
    inline constexpr std::array<float, BrdArgelmach::kGolemCount> kWakePct{ 80.f, 60.f, 40.f };

    constexpr float WakePct(Golem g)
    {
        return kWakePct[BrdArgelmach::IndexOf(g)];
    }

    // AR11 Incineration (Magmatron): 10 s after the pull, then every 25 s (the wreck's core: every 50 s): a 3 s bar
    // (emote line 5), then 15% to everyone. At the bar's start every Chemical Bomb cloud on the floor ignites (the
    // cloud is gone, an 8 yd circle shows): when the bar ends, 30% and Weakened to anyone within 8 yd of one.
    inline constexpr std::uint32_t kIncinerationFirstMs = 10000;
    inline constexpr std::uint32_t kIncinerationEveryMs = 25000;
    inline constexpr std::uint32_t kIncinerationCastMs = 3000;
    inline constexpr float kIncinerationPct = 15.f;
    inline constexpr float kBurstRadiusYd = 8.f;
    inline constexpr float kBurstPct = 30.f;
    inline constexpr std::uint32_t kBurstLookMs = 2000;     // the ring's stalker at each cloud

    // AR12 Flamethrower (Magmatron): 6 s after the pull, then every 15 s: a 60 degree, 25 yd cone from Magmatron
    // toward a random player (the tank too, ruling 88), fixed at the 2 s marker; 35% and Weakened; it burns off
    // Poison Mist (handoff 7 #21: "Flamethrower 60 degrees / 25 yd").
    inline constexpr std::uint32_t kFlameFirstMs = 6000;
    inline constexpr std::uint32_t kFlameEveryMs = 15000;
    inline constexpr std::uint32_t kFlameWarnMs = 2000;
    inline constexpr float kFlameAngleDeg = 60.f;
    inline constexpr float kFlameLengthYd = 25.f;
    inline constexpr float kFlamePct = 35.f;

    // A bar refused (the caster busy with the other one): the beat tries again this soon.
    inline constexpr std::uint32_t kRetryMs = 1000;

    // Inside the Flamethrower: the cone from `apex` facing `bearing` (the kit's frontal-cone test).
    inline bool InFlamethrower(Vec2 apex, float bearing, Vec2 p)
    {
        return DungeonKit::InFrontalCone(apex, bearing, p, kFlameAngleDeg, kFlameLengthYd);
    }

    // Within a cloud's burst (on the plane, the edge inclusive).
    inline bool InBurst(Vec2 cloud, Vec2 p)
    {
        return DungeonKit::Distance(cloud, p) <= kBurstRadiusYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR13 the wrecks and their Salvaged Cores (hard mode only)
    // ----------------------------------------------------------------------------------------------------------------

    // The four units that leave a wreck: the three golems (D15's Golem order) and Magmatron.
    enum class Wreck : std::uint8_t
    {
        Toxitron = 0,
        Electron = 1,
        Arcanoton = 2,
        Magmatron = 3,
    };
    inline constexpr std::size_t kWreckCount = 4;
    inline constexpr std::array<Wreck, kWreckCount> kWrecks{ Wreck::Toxitron, Wreck::Electron, Wreck::Arcanoton,
        Wreck::Magmatron };

    constexpr std::size_t IndexOf(Wreck w)
    {
        return static_cast<std::size_t>(w);
    }

    constexpr Wreck WreckOf(Golem g)
    {
        return static_cast<Wreck>(BrdArgelmach::IndexOf(g));
    }

    constexpr std::optional<Golem> GolemOf(Wreck w)
    {
        if (w == Wreck::Magmatron)
            return std::nullopt;
        return static_cast<Golem>(IndexOf(w));
    }

    constexpr char const* NameOf(Wreck w)
    {
        switch (w)
        {
            case Wreck::Toxitron:   return "toxitron";
            case Wreck::Electron:   return "electron";
            case Wreck::Arcanoton:  return "arcanoton";
            case Wreck::Magmatron:  return "magmatron";
        }
        return "?";
    }

    // The pedestal the wreck stands on: P1-P3 for the golems, P4 for Magmatron.
    constexpr Point3 PedestalOf(Wreck w)
    {
        if (std::optional<Golem> const g = GolemOf(w))
            return BrdArgelmach::PedestalOf(*g);
        return BrdArgelmach::kPedestal4;
    }

    // The core's half rate (S3 AR13): Chemical Bomb on 1 player every 30 s, Lethal Attraction every 30 s, an orb every
    // 30 s, Incineration every 50 s (still detonating the clouds). No second attack. The first firing comes
    // kCoreFirstMs after the death (gap 36: the spec names no first time).
    inline constexpr std::uint32_t kCoreFirstMs = 10000;
    inline constexpr std::uint32_t kCoreBombMarks = 1;

    constexpr std::uint32_t CoreEveryMs(Wreck w)
    {
        switch (w)
        {
            case Wreck::Toxitron:   return 30000;
            case Wreck::Electron:   return 30000;
            case Wreck::Arcanoton:  return 30000;
            case Wreck::Magmatron:  return 50000;
        }
        return 30000;
    }

    // Magmatron on the fourth pedestal looks at the chamber's middle, like the other three.
    inline float MagmatronFacing()
    {
        return DungeonKit::BearingTo(BrdArgelmach::kPedestal4.XY(), BrdArgelmach::kChamberMiddle);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Activation Console (GO 301284; heroic only by its spawn mask; per pull)
    // ----------------------------------------------------------------------------------------------------------------

    // By the passage mouth (NAVMESH 3.2), outside the chamber, about 12 yd from the fourth pedestal.
    inline constexpr Point3 kConsole{ 832.2f, 12.8f, -53.7f };
    inline constexpr std::uint32_t kConsolePollMs = 1000;
    inline constexpr std::uint32_t kStatueCheckMs = 1000;   // the idle hook's statue check
    inline constexpr float kStatueSearchYd = 40.f;          // the console's search for a statue left after the kill

    // A Magmatron statue is dormant by its own state (alive, out of combat, still not selectable), never by its look:
    // a look that fails to land must not make the idle hook replace the statue every check (R-2-A MA-1). The pull and
    // a wake make it selectable, so an awake, fighting or dead Magmatron is never taken for the statue.
    constexpr bool StatueDormant(bool alive, bool inCombat, bool notSelectable)
    {
        return alive && !inCombat && notSelectable;
    }

    // The console faces the fourth pedestal.
    inline float ConsoleFacing()
    {
        return DungeonKit::BearingTo(kConsole.XY(), BrdArgelmach::kPedestal4.XY());
    }

    enum class ConsoleRefusal : std::uint8_t
    {
        None,
        NotHeroic,          // heroic only (section 7 #15)
        NotBound,           // wave 2 is not bound yet (kWave2Bound): the stock Argelmach has no hard mode
        ArgelmachGone,      // he is dead (or missing)
        ArgelmachFighting,  // he is in combat, evading, or his encounter is in progress
        Armed,              // already armed for the next pull
    };

    struct ConsoleCheck
    {
        bool heroic = false;
        bool wave2Bound = false;
        bool armed = false;
        bool argelmachAlive = false;
        bool argelmachBusy = false;         // engaged, in combat or evading
        std::uint32_t argelmachState = 0;   // his boss slot (BOSS_ARGELMACH)
    };

    constexpr ConsoleRefusal ConsoleRefusalFor(ConsoleCheck const& c)
    {
        if (!c.heroic)
            return ConsoleRefusal::NotHeroic;
        if (!c.wave2Bound)
            return ConsoleRefusal::NotBound;
        if (!c.argelmachAlive || c.argelmachState == DungeonKit::State::Done)
            return ConsoleRefusal::ArgelmachGone;
        if (c.argelmachBusy || c.argelmachState == DungeonKit::State::InProgress)
            return ConsoleRefusal::ArgelmachFighting;
        if (c.armed)
            return ConsoleRefusal::Armed;
        return ConsoleRefusal::None;
    }

    constexpr char const* ConsoleRefusalText(ConsoleRefusal r)
    {
        switch (r)
        {
            case ConsoleRefusal::None:              return "";
            case ConsoleRefusal::NotHeroic:         return "The console is dead. The prototype only stirs on heroic.";
            case ConsoleRefusal::NotBound:          return "The console does not answer.";
            case ConsoleRefusal::ArgelmachGone:     return "Golem Lord Argelmach is gone: the console is dead.";
            case ConsoleRefusal::ArgelmachFighting: return "Not while Golem Lord Argelmach is fighting.";
            case ConsoleRefusal::Armed:             return "The prototype is already armed.";
        }
        return "";
    }
}

#endif
