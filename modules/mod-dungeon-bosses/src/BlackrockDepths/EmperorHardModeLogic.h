/*
 * mod-dungeon-bosses, Blackrock Depths D24:
 * The Emperor's hard mode, the Avatar of Ragnaros (heroic, "Dagran first"), the pure, host-testable part (no engine
 * headers). Build spec S4 "Hard mode" (docs/dungeons/blackrock-depths-4-imperial-seat.md, EM11-EM13; rulings 77-81,
 * 88), handoff sections 3.6 (Avatar 260k), 3.7 row D24, 3.10 (the Avatar's scale), 7 #19. It fights on D23's AI
 * through EmperorFight.h (D23 owns the lethal hit, the cage, the adds leaving, Firestorm, the kill and the cleanup).
 * Tested by tests/brd_emperor_hard_mode_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsAvatar (211660-211709), declared in apps/dbc-tools
 *                source/npcs/blackrock_depths/emperor_hard_mode.py
 *   The rise     the throne spot (his spawn), the Avatar's display, scale, reach and 260k, the knockback
 *   EM12         Magma Clap: every 20 s a 3 s cast, then everyone takes damage falling off with distance from him
 *   EM13         Volcanic Blast: every 25 s a player is marked; 5 s later 80% split among everyone within 8 yd, and a
 *                Volcanic Stone (5 yd, 30 s, 8% a second) where the mark stood
 *   The clock    the two casts never overlap (a cast that comes due while the other's window is open waits), and
 *                D23's Firestorm waits out both windows (EmperorFight::HoldBeats)
 *   Rule 10      the rooted Avatar answers a victim out of his reach (outside the two casts' windows and the walk
 *                back after each) with Magma Blast every 2 s (the Roccor precedent)
 *
 * Every value is heroic (hard modes are heroic only, section 7 #15): plain constants, no NH<>.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_EMPEROR_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_EMPEROR_HARD_MODE_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace BrdAvatar
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsAvatar;

    enum EmperorHardModeSpells : std::uint32_t
    {
        SPELL_AV_MAGMA_CLAP_CAST     = kSpellSlice.first + 0,    // 211660 EM12 the 3 s bar (Fire, not interruptible)
        SPELL_AV_MAGMA_CLAP          = kSpellSlice.first + 1,    // 211661 EM12 a player's hit (exact, by distance)
        SPELL_AV_MAGMA_CLAP_RING     = kSpellSlice.first + 2,    // 211662 look: the Fire Nova ring at his feet
        SPELL_AV_VOLCANIC_MARK       = kSpellSlice.first + 3,    // 211663 EM13 the 5 s mark (orange ring, a debuff)
        SPELL_AV_VOLCANIC_BLAST      = kSpellSlice.first + 4,    // 211664 EM13 a share of the 80% (exact)
        SPELL_AV_VOLCANIC_STONE      = kSpellSlice.first + 5,    // 211665 EM13 the stone's tick (resolve copy, Fire)
        SPELL_AV_VOLCANIC_STONE_LOOK = kSpellSlice.first + 6,    // 211666 look: the 5 yd lava pool (stalker aura)
        SPELL_AV_AWAKENS_PILLAR      = kSpellSlice.first + 7,    // 211667 look: Pillar of Fire at the throne (EM11)
        SPELL_AV_AWAKENS_ERUPTION    = kSpellSlice.first + 8,    // 211668 look: Massive Eruption at the throne (rise)
        SPELL_AV_MAGMA_BLAST         = kSpellSlice.first + 9,    // 211669 rule 10: his victim out of reach (20%)
        // 211670-211709 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_AV_MAGMA_BLAST;
    static_assert(kLastSpell <= kSpellSlice.last, "the Avatar's spells must stay in his slice");

    // Registry tags: the encounter is Dagran's (D23 uses 1-5 and 21); the Avatar's start at 31.
    enum AvatarTags : std::uint32_t
    {
        TAG_AV_MAGMA_CLAP       = 31,   // EM12 the RunOut from him (telegraph and bots; the script deals the falloff)
        TAG_AV_VOLCANIC_BLAST   = 32,   // EM13 the Stack on the marked player (the script splits the 80%)
        TAG_AV_VOLCANIC_STONE   = 33,   // EM13 the stone's persistent Zone
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The rise (EM11; D23 runs the transition, these are the Avatar's numbers)
    // ----------------------------------------------------------------------------------------------------------------

    // S4 "Hard mode": he rises at 260,000 (handoff section 3.6; about 69 s at the hard mode's 4,440 group DPS).
    inline constexpr std::uint32_t kAvatarHealth = 260000;
    // The Avatar's look: CDI 11121 (Ragnaros.mdx, 31.4 x 36.9 x 57.9 yd at scale 1; _visuals.py AVATAR_SCALE_RANGE
    // 0.12-0.18 fits the 21 yd dais). 0.15: about 4.7 x 5.5 x 8.7 yd.
    inline constexpr std::uint32_t kAvatarDisplay = 11121;
    inline constexpr float kAvatarScaleMin = 0.12f;
    inline constexpr float kAvatarScaleMax = 0.18f;
    inline constexpr float kAvatarScale = 0.15f;
    static_assert(kAvatarScale >= kAvatarScaleMin && kAvatarScale <= kAvatarScaleMax, "VR's Avatar scale range");
    // Combat reach, set after the swap (handoff 3.10): the model's own 20 yd at 1.0 gives 3 yd at 0.15; half his
    // width plus a step, so melee standing at his body connects.
    inline constexpr float kAvatarReachYd = 3.5f;

    // The throne spot: his spawn on the dais ([db] guid 47613, the stock home), facing into the room. D24 jumps him
    // there at the awakening and roots him there at the rise; the runtime uses his home position, this is the
    // fallback and the test's reference.
    inline constexpr BlackrockDepthsRework::Point3 kThroneSpot = BlackrockDepthsRework::kEmperorSpawn;
    inline constexpr float kThroneFacing = 1.32645f;
    // The jump to the throne (DungeonKit::JumpTo): 5 yd up from the floor, about 14 yd from the tank's Spot.
    inline constexpr float kJumpSpeedXY = 20.f;
    inline constexpr float kJumpMinSpeedZ = 12.f;
    // At the rise, farther than this from the throne (the jump fell short): placed there.
    inline constexpr float kThroneSnapYd = 3.f;

    // The awakening's knockback (S4: "a plain knockback, a scripted transition"): every player of the fight is thrown
    // this far from where he stood (Unit::KnockbackFrom; distance = 2 x speedXY x speedZ / g).
    inline constexpr float kKnockbackYd = 15.f;
    inline constexpr float kKnockbackSpeedZ = 8.f;
    inline constexpr float kGravity = 19.29110527038574f;  // Movement::gravity
    constexpr float KnockbackSpeedXY(float distanceYd, float speedZ = kKnockbackSpeedZ)
    {
        return speedZ > 0.f ? distanceYd * kGravity / (2.f * speedZ) : 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM12 Magma Clap
    // ----------------------------------------------------------------------------------------------------------------

    // First 10 s after the rise, then every 20 s: a 3 s cast (boss emote 11), then everyone of the fight (the tank too)
    // takes damage falling off with the distance from him: 70% within 10 yd, linear down to 15% at 40 yd and beyond.
    // Kind: RunOut (30 yd) from him, the bots' telegraph; the script deals the falloff to everyone. No Weakened (the
    // spec names none: the falloff is the cost).
    inline constexpr std::uint32_t kClapFirstMs = 10000;
    inline constexpr std::uint32_t kClapEveryMs = 20000;
    inline constexpr std::uint32_t kClapCastMs = 3000;
    inline constexpr float kClapRunOutYd = 30.f;
    inline constexpr float kClapNearYd = 10.f;
    inline constexpr float kClapFarYd = 40.f;
    inline constexpr float kClapNearPct = 70.f;
    inline constexpr float kClapFarPct = 15.f;
    // After the hit the tank walks back to the rooted Avatar (30 yd at 7 yd a second): rule 10's answer waits.
    inline constexpr std::uint32_t kClapWalkBackMs = 5000;

    // The percent of the row a player `distanceYd` from him takes.
    constexpr float MagmaClapPct(float distanceYd)
    {
        if (distanceYd <= kClapNearYd)
            return kClapNearPct;
        if (distanceYd >= kClapFarYd)
            return kClapFarPct;
        float const t = (distanceYd - kClapNearYd) / (kClapFarYd - kClapNearYd);
        return kClapNearPct + (kClapFarPct - kClapNearPct) * t;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM13 Volcanic Blast and the Volcanic Stone
    // ----------------------------------------------------------------------------------------------------------------

    // First 15 s after the rise, then every 25 s: a player (the tank too, ruling 88) is marked (boss emote 12 names
    // them); 5 s later 80% of the row is split evenly among everyone within 8 yd of the mark (the marked player
    // included; 3 or more: about 27% each, alone: 80%). Where the mark stood a Volcanic Stone stays 30 s: 5 yd, 8% a
    // second. With a 30 s stone every 25 s, at most 2 stand at once.
    inline constexpr std::uint32_t kBlastFirstMs = 15000;
    inline constexpr std::uint32_t kBlastEveryMs = 25000;
    inline constexpr std::uint32_t kBlastMarkMs = 5000;
    inline constexpr float kBlastRadiusYd = 8.f;
    inline constexpr float kBlastZBandYd = 5.f;
    inline constexpr float kBlastTotalPct = 80.f;
    inline constexpr float kStoneRadiusYd = 5.f;
    inline constexpr std::uint32_t kStoneMs = 30000;
    inline constexpr std::uint32_t kStoneTickMs = 1000;
    inline constexpr float kStonePct = 8.f;

    // Each taker's share of the 80% (even split), 0 with nobody.
    constexpr float BlastSharePct(std::size_t takers)
    {
        return takers ? kBlastTotalPct / static_cast<float>(takers) : 0.f;
    }

    // The most stones standing at once: a stone lives kStoneMs, a new one comes every kBlastEveryMs or later.
    constexpr std::uint32_t MaxStones()
    {
        return (kStoneMs + kBlastEveryMs - 1) / kBlastEveryMs;
    }

    // The stone never lands in the rooted Avatar's melee ring (orchestrator default to R-2-C m4): the ring is the
    // core's melee range against a player (Unit::GetMeleeRange: both combat reaches + 4/3, at least 5 yd), and the
    // stone's whole circle stays outside it. The mark itself (the 80% split) still lands where the mark stood.
    inline constexpr float kPlayerReachYd = 1.5f;       // DEFAULT_PLAYER_COMBAT_REACH
    constexpr float AvatarMeleeRingYd()
    {
        return std::max(kAvatarReachYd + kPlayerReachYd + 4.f / 3.f, 5.f);
    }
    inline constexpr float kStoneClearYd = AvatarMeleeRingYd() + kStoneRadiusYd;

    // The stone's center: the mark's spot if it is far enough from the Avatar, else pushed out along the bearing from
    // him to the mark to kStoneClearYd (a mark on top of him: in front, along his facing).
    inline Vec2 StoneSpot(Vec2 avatar, float facing, Vec2 mark, float clear = kStoneClearYd)
    {
        float const distance = DungeonKit::Distance(avatar, mark);
        if (distance >= clear)
            return mark;
        float const bearing = distance < 0.1f ? facing : DungeonKit::BearingTo(avatar, mark);
        return DungeonKit::Advance(avatar, bearing, clear);
    }

    // The indexes of `points` within `radius` of `at` on the plane (the takers of a blast).
    inline std::vector<std::size_t> WithinRadius(Vec2 at, float radius, std::vector<Vec2> const& points)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < points.size(); ++i)
            if (DungeonKit::Distance(at, points[i]) <= radius)
                out.push_back(i);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 10: the rooted Avatar answers a victim out of his reach
    // ----------------------------------------------------------------------------------------------------------------

    // His victim out of his melee reach for 3 s (outside a grace: the Magma Clap's cast and the walk back after it; a
    // Volcanic Blast's mark and the walk back after it): Magma Blast on it every 2 s, 20% of its row.
    inline constexpr std::uint32_t kOutOfReachMs = 3000;
    inline constexpr std::uint32_t kMagmaBlastEveryMs = 2000;
    inline constexpr float kMagmaBlastPct = 20.f;

    // ----------------------------------------------------------------------------------------------------------------
    // The clock (on EmperorFight::FightMs)
    // ----------------------------------------------------------------------------------------------------------------

    // A cast's window stays closed to the other cast this long after its hit (a breath between them).
    inline constexpr std::uint32_t kBetweenCastsMs = 1000;

    enum class Cast : std::uint8_t
    {
        None,
        Clap,
        Blast,
    };

    struct AvatarClock
    {
        std::uint64_t clapAt = 0;           // the next Magma Clap (0: off)
        std::uint64_t blastAt = 0;          // the next Volcanic Blast mark (0: off)
        std::uint64_t clapEndsAt = 0;       // the current (or last) Magma Clap's hit
        std::uint64_t blastEndsAt = 0;      // the current (or last) Volcanic Blast's hit
        std::uint64_t outOfReachSince = 0;  // rule 10: his victim left his reach (0: in reach, or in a grace)
        std::uint64_t magmaBlastAt = 0;     // rule 10: the next Magma Blast

        // The rise: Magma Clap 10 s, Volcanic Blast 15 s later.
        void Rise(std::uint64_t now)
        {
            *this = AvatarClock{};
            clapAt = now + kClapFirstMs;
            blastAt = now + kBlastFirstMs;
        }

        // A cast's window is open from its start to its hit plus the breath.
        bool ClapOpen(std::uint64_t now) const
        {
            return clapEndsAt && now + kClapCastMs >= clapEndsAt && now < clapEndsAt + kBetweenCastsMs;
        }
        bool BlastOpen(std::uint64_t now) const
        {
            return blastEndsAt && now + kBlastMarkMs >= blastEndsAt && now < blastEndsAt + kBetweenCastsMs;
        }

        // What starts now: the Magma Clap first when both are due; neither while the other's window is open.
        Cast Due(std::uint64_t now) const
        {
            bool const busy = ClapOpen(now) || BlastOpen(now);
            if (busy)
                return Cast::None;
            if (clapAt && now >= clapAt)
                return Cast::Clap;
            if (blastAt && now >= blastAt)
                return Cast::Blast;
            return Cast::None;
        }

        // A cast started: its hit is due, the next one a cadence after it was due (a wait never shifts the cadence
        // unless it was longer than one).
        void ClapStarted(std::uint64_t now)
        {
            clapEndsAt = now + kClapCastMs;
            clapAt = std::max<std::uint64_t>((clapAt ? clapAt : now) + kClapEveryMs, now + 1);
        }
        void BlastStarted(std::uint64_t now)
        {
            blastEndsAt = now + kBlastMarkMs;
            blastAt = std::max<std::uint64_t>((blastAt ? blastAt : now) + kBlastEveryMs, now + 1);
        }

        // Rule 10's grace: the Magma Clap's cast and the walk back after it; a Volcanic Blast's mark and the walk back
        // after it (the tank may join the stack: more shares, smaller hits).
        bool ReachGrace(std::uint64_t now) const
        {
            if (clapEndsAt && now + kClapCastMs >= clapEndsAt && now < clapEndsAt + kClapWalkBackMs)
                return true;
            return blastEndsAt && now + kBlastMarkMs >= blastEndsAt && now < blastEndsAt + kClapWalkBackMs;
        }

        // Rule 10, a tick: is a Magma Blast due on his victim now (`inReach`: the victim stands in his melee reach).
        // The answer starts kOutOfReachMs after the victim left his reach (outside a grace), then every 2 s.
        bool MagmaBlastDue(std::uint64_t now, bool inReach, bool grace)
        {
            if (inReach || grace)
            {
                outOfReachSince = 0;
                magmaBlastAt = 0;
                return false;
            }
            if (!outOfReachSince)
            {
                outOfReachSince = now;
                magmaBlastAt = now + kOutOfReachMs;
                return false;
            }
            if (now < magmaBlastAt)
                return false;
            magmaBlastAt = now + kMagmaBlastEveryMs;
            return true;
        }
    };
}

#endif
