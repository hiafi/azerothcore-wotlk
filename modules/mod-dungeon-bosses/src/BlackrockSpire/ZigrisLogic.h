/*
 * mod-dungeon-bosses, Blackrock Spire B6:
 * Quartermaster Zigris (9736), the pure, host-testable part (no engine headers). Build spec: docs/dungeons/
 * blackrock-spire-rework.md "Quartermaster Zigris" (SP 1690-1903, ZG1-ZG8, rulings 40-43), handoff section 3.4 rows ZG,
 * 3.5 row B6, 3.6, 3.8 (the ledge and the three crate spots). Tested by tests/brs_zigris_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsZigris (210180-210209), declared in apps/dbc-tools
 *                 source/npcs/blackrock_spire/zigris.py
 *   Tuning        NH<> percents, FlexAB counts and the cadences, straight from the build spec
 *   Restock       ZG3 the gadget each landing at a crate adds (RestockFor), the crate each leap goes to (CrateFor)
 *   GadgetClock   a repeating beat on the AI's own ms clock (traps, Fall Back, keg, Mortar, sheep)
 *   Shells        ZG5 the salvo: how many, who gets which, when the missile look leaves so it lands as the circle
 *                 resolves
 *   Fall Back     ZG2 the leap's flight time and the two traps dropped where he stood
 *   Sheep         ZG6 a sheep that touches a Net Trap springs it
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_ZIGRIS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_ZIGRIS_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace BrsZigris
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsZigris;

    enum ZigrisSpells : std::uint32_t
    {
        SPELL_ZG_NET_TRAP       = kSpellSlice.first + 0,    // 210180 ZG1 a sprung trap's hit (resolve copy, Physical)
        SPELL_ZG_NETTED         = kSpellSlice.first + 1,    // 210181 ZG1 the 2 s root of a sprung trap (the rider)
        SPELL_ZG_KEG_BLAST      = kSpellSlice.first + 2,    // 210182 ZG4 the keg's hit (resolve copy, Fire)
        SPELL_ZG_KEG_STUN       = kSpellSlice.first + 3,    // 210183 ZG4 the 2 s stun of the keg (the rider)
        SPELL_ZG_FUSE           = kSpellSlice.first + 4,    // 210184 ZG4 / ZG6 the lit fuse (state aura on a stalker)
        SPELL_ZG_BLAST_LOOK     = kSpellSlice.first + 5,    // 210185 ZG4 / ZG6 the blast at a point (look only)
        SPELL_ZG_MORTAR_SHELL   = kSpellSlice.first + 6,    // 210186 ZG5 a shell's hit (resolve copy, Fire)
        SPELL_ZG_MORTAR_LOOK    = kSpellSlice.first + 7,    // 210187 ZG5 the shell in flight to a point (look only)
        SPELL_ZG_SMOKE_BOMB     = kSpellSlice.first + 8,    // 210188 ZG2 the smoke at his feet (look only)
        SPELL_ZG_LEAP           = kSpellSlice.first + 9,    // 210189 ZG2 the leap's animation (look only)
        SPELL_ZG_SHEEP_BLAST    = kSpellSlice.first + 10,   // 210190 ZG6 the sheep's hit (resolve copy, Fire)
        SPELL_ZG_SHEEP_WINDUP   = kSpellSlice.first + 11,   // 210191 ZG6 the wind-up as it is released (look only)
        // 210192-210209 spare
    };
    static_assert(SPELL_ZG_SHEEP_WINDUP <= kSpellSlice.last, "Zigris's spells must stay in his slice");

    // Stock Shoot (ZG7), kept: 215 to 289 at a target out of melee (DD scales it on heroic).
    inline constexpr std::uint32_t SPELL_ZG_SHOOT = 16496;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum ZigrisTags : std::uint32_t
    {
        TAG_TRAPS       = 1,    // ZG1 Net Traps
        TAG_KEG         = 4,    // ZG4 Powder Keg
        TAG_MORTAR      = 5,    // ZG5 Mortar shells
        TAG_SHEEP       = 6,    // ZG6 the sheep's blast
        TAG_SHEEP_RUN   = 7,    // ZG6 the bots' keep-away from the chased player (never resolves)
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_quartermaster_zigris_blackrock_spire.sql, SP "Text").
    enum ZigrisTexts : std::uint8_t
    {
        TEXT_PULL       = 0,    // yell: "Hands off the legion's stores!"
        TEXT_FALL_BACK  = 1,    // emote: "%s throws down a smoke bomb and falls back!"
        TEXT_KEG        = 2,    // emote, restock 1: "%s rolls out the powder kegs!"
        TEXT_MORTAR     = 3,    // emote, restock 2: "%s sets up a mortar on the crates!"
        TEXT_SHEEP      = 4,    // emote, restock 3 (heroic): "%s winds up the clockwork sheep!"
        TEXT_DEATH      = 5,    // yell: "That... was... signed out..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP "Build spec"; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // ZG1 Net Traps (Mine 3 yd, armed after 1 s, grace 0.5 s): one at the spot of each of 2 random non-tanks (4 at 6 or
    // more) at 8 s, then every 15 s; 20% (heroic 25%) + Weakened + a 2 s root (the Netted spell's own duration);
    // unsprung traps last 60 s; at most 8 (12 at 6 or more), heroic 10 (14), the oldest snaps shut harmlessly.
    inline constexpr std::uint32_t kTrapsFirstMs = 8000;
    inline constexpr std::uint32_t kTrapsEveryMs = 15000;
    inline constexpr FlexAB kTossTargets{ 2, 4 };
    inline constexpr float kTrapRadius = 3.f;
    inline constexpr std::uint32_t kTrapArmMs = 1000;
    inline constexpr std::uint32_t kTrapGraceMs = 500;
    inline constexpr std::uint32_t kTrapLifeMs = 60000;
    inline constexpr std::uint32_t kTrapCapGroup = 1;
    inline constexpr FlexAB kTrapCapNormal{ 8, 12 };
    inline constexpr FlexAB kTrapCapHeroic{ 10, 14 };
    inline constexpr NH<float> kTrapPct{ 20.f, 25.f };
    inline constexpr std::uint32_t kNettedMs = 2000;                // the Netted spell's duration (the DT test pins it)
    inline constexpr std::uint32_t kTrapSpringLingerMs = 700;       // a sprung trap's object closes this long

    constexpr std::uint8_t TrapCap(bool heroic, std::uint32_t players)
    {
        return (heroic ? kTrapCapHeroic : kTrapCapNormal).At(players);
    }

    // ZG2 Fall Back: first at 20 s (heroic 15 s), then every 20 s (15 s): a smoke bomb at his feet, a leap to the next
    // crate in turn, two Net Traps where he stood, and a restock when he lands.
    inline constexpr NH<std::uint32_t> kFallBackFirstMs{ 20000, 15000 };
    inline constexpr NH<std::uint32_t> kFallBackEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kFallBackTraps = 2;
    inline constexpr float kFallBackTrapOffsetYd = 2.f;             // the two traps sit this far either side
    inline constexpr float kLeapSpeedYdPerSec = 22.f;               // JumpTo's horizontal speed
    inline constexpr std::uint32_t kLeapPadMs = 250;                // the landing is judged this long after the arc

    // The crates (NM 6; kZigrisCrates holds x, y): crate 2 also carries the mortar.
    inline constexpr std::size_t kCrateCount = 3;
    inline constexpr std::size_t kMortarCrate = 1;
    inline constexpr std::array<float, kCrateCount> kCrateZ{ { 88.3f, 88.3f, 88.0f } };

    constexpr Point3 CrateSpot(std::size_t crate)
    {
        std::size_t const i = crate % kCrateCount;
        return { BlackrockSpireRework::kZigrisCrates[i].x, BlackrockSpireRework::kZigrisCrates[i].y, kCrateZ[i] };
    }

    // The crate leap number `fall` (0-based) goes to: in turn, then round again.
    constexpr std::size_t CrateFor(std::uint32_t fall)
    {
        return fall % kCrateCount;
    }

    // ZG3 Restock: the gadget each landing adds for the rest of the fight (1-based landing). Crate 1 the keg, crate 2
    // the Mortar, crate 3 the sheep on heroic (nothing on normal); later landings nothing.
    enum class Gadget : std::uint8_t
    {
        None,
        PowderKeg,
        Mortar,
        Sheep,
    };

    struct Restock
    {
        Gadget gadget = Gadget::None;
        int text = -1;      // the emote group, -1: none
    };

    constexpr Restock RestockFor(std::uint32_t landing, bool heroic)
    {
        switch (landing)
        {
            case 1:
                return { Gadget::PowderKeg, TEXT_KEG };
            case 2:
                return { Gadget::Mortar, TEXT_MORTAR };
            case 3:
                return heroic ? Restock{ Gadget::Sheep, TEXT_SHEEP } : Restock{};
            default:
                return {};
        }
    }

    // ZG4 Powder Keg: one at every size, first 4 s after the first restock lands, then every 20 s: a lit keg at a
    // random non-tank's spot, a 10 yd blast after a 4 s fuse; 30% (heroic 40%) + Weakened + a 2 s stun (the keg stun's
    // own duration).
    inline constexpr std::uint32_t kKegFirstAfterMs = 4000;
    inline constexpr std::uint32_t kKegEveryMs = 20000;
    inline constexpr std::uint32_t kKegFuseMs = 4000;
    inline constexpr float kKegRadius = 10.f;
    inline constexpr NH<float> kKegPct{ 30.f, 40.f };
    inline constexpr std::uint32_t kKegStunMs = 2000;               // the stun spell's duration (the DT test pins it)
    inline constexpr std::uint32_t kKegGoLifeSecs = 8;              // the keg object's own timed despawn (a backstop)
    inline constexpr std::uint32_t kFuseStalkerLifeMs = 6000;       // the fuse stalker's timed despawn (a backstop)

    // ZG5 Mortar: first 3 s after the second restock lands, then every 7 s: a salvo of 3 shells (6 at 6 or more), 1 s
    // apart, each at a different far-away non-tank; 5 yd, 2 s flight, 25% (heroic 30%) + Weakened.
    inline constexpr std::uint32_t kMortarFirstAfterMs = 3000;
    inline constexpr std::uint32_t kMortarEveryMs = 7000;
    inline constexpr FlexAB kShells{ 3, 6 };
    inline constexpr std::uint32_t kShellGapMs = 1000;
    inline constexpr std::uint32_t kShellFlightMs = 2000;
    inline constexpr float kShellRadius = 5.f;
    inline constexpr NH<float> kMortarPct{ 25.f, 30.f };
    inline constexpr float kShellMissileSpeed = 22.f;               // the look spell's Speed (the DT test pins it)

    // The shell `shell` (0-based) of a salvo goes at picked player `shell % picked`: every shell a different player
    // while there are enough, then the list again (6 shells at 6 players have 5 non-tanks to share).
    constexpr std::uint32_t ShellTarget(std::uint32_t shell, std::uint32_t picked)
    {
        return picked ? shell % picked : 0;
    }

    // When the missile look must leave the mortar, after the circle registers, so it lands as the circle resolves
    // (a long throw leaves at once and arrives a little early, a short one waits). Clamped to the flight time.
    inline std::uint32_t ShellLaunchDelayMs(float distanceYd)
    {
        float const flight = std::max(0.f, distanceYd) / kShellMissileSpeed * 1000.f;
        float const wait = static_cast<float>(kShellFlightMs) - std::min(flight, static_cast<float>(kShellFlightMs));
        return static_cast<std::uint32_t>(wait + 0.5f);
    }

    // ZG6 Explosive Sheep (heroic): first 3 s after the third restock lands, then every 20 s: a clockwork sheep at a
    // random non-tank (2 at 6 or more), chasing at 5 yd/s (players run 7), it explodes on reaching them or after
    // 10 s, 8 yd, 35% + Weakened; 3,000 health (the creature's own template); a sheep over a Net Trap springs it and
    // blows up there.
    inline constexpr std::uint32_t kSheepFirstAfterMs = 3000;
    inline constexpr std::uint32_t kSheepEveryMs = 20000;
    inline constexpr FlexAB kSheepCount{ 1, 2 };
    inline constexpr float kSheepSpeed = 5.f;
    inline constexpr std::uint32_t kSheepLifeMs = 10000;
    inline constexpr float kSheepReachYd = 2.f;                     // it has reached its target
    inline constexpr float kSheepBlastRadius = 8.f;
    inline constexpr float kSheepBlastPct = 35.f;
    inline constexpr std::uint32_t kSheepHealth = 3000;             // the template's 5-player value (the DT test pins)
    inline constexpr std::uint32_t kSheepDespawnMs = 600;           // after the blast: the registry resolves first
    // The registry's keep-away for the bots never resolves (it outlives the sheep by a second): the sheep's own zone is
    // the hit.
    inline constexpr std::uint32_t kSheepRunOutWarnMs = kSheepLifeMs + 1000;

    // A sheep at `sheep` touches the Net Trap at `trap` (its 3 yd hitbox).
    inline bool SheepSpringsTrap(Vec2 sheep, Vec2 trap)
    {
        return DungeonKit::Distance(sheep, trap) <= kTrapRadius;
    }

    // ZG7 Shoot, kept: every 2 s at his target while it is out of melee and in line of sight.
    inline constexpr std::uint32_t kShootEveryMs = 2000;

    // The flight time of a leap of `distanceYd` at kLeapSpeedYdPerSec, plus the padding after which he has landed.
    inline std::uint32_t LeapMs(float distanceYd)
    {
        return static_cast<std::uint32_t>(std::max(0.f, distanceYd) / kLeapSpeedYdPerSec * 1000.f + 0.5f) + kLeapPadMs;
    }

    // The two traps dropped where he stood: either side of `at`, across the leap's direction `facing` (radians).
    inline std::array<Vec2, 2> FallBackTrapSpots(Vec2 at, float facing)
    {
        float const left = facing + DungeonKit::kPi * 0.5f;
        return { { DungeonKit::Advance(at, left, kFallBackTrapOffsetYd),
                   DungeonKit::Advance(at, left + DungeonKit::kPi, kFallBackTrapOffsetYd) } };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GadgetClock: a repeating beat on the AI's own ms clock
    // ----------------------------------------------------------------------------------------------------------------

    class GadgetClock
    {
    public:
        // Starts (or restarts) the beat: due `afterMs` from `nowMs`.
        void Start(std::uint64_t nowMs, std::uint32_t afterMs)
        {
            _on = true;
            _dueMs = nowMs + afterMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time (start to start), never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
