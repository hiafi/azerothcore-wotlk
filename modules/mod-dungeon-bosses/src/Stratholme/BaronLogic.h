/*
 * mod-dungeon-bosses, Stratholme S14: Baron Rivendare (10440), the pure, host-testable part (no engine headers): the
 * spell ids, the per-difficulty tuning, the never-paused fight timeline, the Raise Dead walls and cap, the Unholy Aura
 * percent, the bone pile rules (the rot's raise reach, the bot tank's reposition) and the stock leash. Build spec: ST
 * 3842-3906 (build spec), ST 3487-3841 (design: pitch B "Lord of the Dead", the core loop "pick a graveyard", rulings
 * 55-59); handoff section 3.4 rows BR, section 3.5 row S14, section 3.6 (normal 250k, heroic 300k), section 3.8 (the
 * room). The hard mode (the Ultimatum, HM1-HM4) is WP-S15's, on top of this AI through BaronFight.h.
 *
 * Damage percentages are of the reference health row (normal 3,670 non-tank / 3,710 tank, heroic 4,120 / 4,110 at
 * level 60, the MapLevels pin 329:60): the build spec gives N / H percents, and the row makes the rest of the
 * difference.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARON_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARON_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace StratBaron
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using StratholmeRework::Point3;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`). The hard
    // mode's own ids are kSpellsUltimatum (206720-206734, S15).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBaron;

    // Declared in apps/dbc-tools source/npcs/stratholme/baron_rivendare.py (same ids).
    enum BaronSpells : std::uint32_t
    {
        SPELL_BR_UNHOLY_AURA        = 206705,   // BR4 the aura on him: triggers the pulse every 2 s (17467's shape)
        SPELL_BR_UNHOLY_PULSE       = 206706,   // BR4 the 2 s Shadow pulse on everyone in his fight within 100 yd
        SPELL_BR_RISE               = 206707,   // BR1 / BR2 the rising look on a skeleton (Raise Dead 17475's SV 634)
        SPELL_BR_DEATH_AND_DECAY    = 206708,   // BR3 the 3 s mark on the target (the circle follows them)
        SPELL_BR_ROT                = 206709,   // BR3 the rot's 1 s tick: resolve copy (Shadow)
        SPELL_BR_ROT_LOOK           = 206710,   // BR3 the rot on the stalker's spot (Death and Decay 49936's SV 9735)
        SPELL_BR_SKELETON_STRIKE    = 206711,   // BR1 the skeletons' 2 s strike on their victim (percent spell)
        // 206712-206719 spare (206720-206734 are S15's, the Ultimatum)
    };
    static_assert(kSpellSlice.Contains(SPELL_BR_UNHOLY_AURA), "Baron spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_BR_SKELETON_STRIKE), "Baron spells sit in his slice");
    static_assert(!StratholmeRework::kSpellsUltimatum.Contains(SPELL_BR_SKELETON_STRIKE), "S15 keeps its ids");

    // Registry tags (the build spec's BR numbers). S15 tags its own mechanics from kHardModeTagBase.
    enum BaronTags : std::uint32_t
    {
        TAG_DEATH_AND_DECAY = 3,    // BR3 the following circle (telegraph only; the rot below owns the damage)
        TAG_ROT             = 4,    // BR3 the rot's persistent zone
        TAG_PARK            = 5,    // BR2 the bot tank's reposition off the piles (bots only)
    };
    std::uint32_t constexpr kHardModeTagBase = 10;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Build spec" and "Tuning starting points", approved 2026-11-05)
    // ----------------------------------------------------------------------------------------------------------------

    // BR1 Raise Dead: 3 Mindless Skeletons 11197 at the three stock points of one wall, walls alternating; first at
    // 6 s, then every 20 s. Normal caps the living pile at 6 (a wave that would pass it rises short); heroic has no
    // cap (the soft enrage). Health: normal 6,000 (the DT file's HealthModifier), heroic 7,500 (WP-H's heroic copy).
    std::uint32_t constexpr kRaiseDeadFirstMs = 6000;
    std::uint32_t constexpr kRaiseDeadEveryMs = 20000;
    std::uint32_t constexpr kWaveSize = 3;
    inline constexpr NH<std::uint32_t> kSkeletonCap{ 6, 0 };            // 0: no cap
    inline constexpr NH<std::uint32_t> kSkeletonHealth{ 6000, 7500 };   // mirrored for the tests (the data sets it)
    // The skeletons' melee: about 1% / 1.25% of the tank reference row per second on their victim, as one strike every
    // 2 s (SPELL_BR_SKELETON_STRIKE: 2% / 2.5%, hundredths in the spell's value and MiscValueB, the kit's
    // spell_dungeon_refflat_damage). No auto attack: the strike is the swing, so both difficulties are exact.
    std::uint32_t constexpr kSkeletonSwingMs = 2000;
    std::uint32_t constexpr kSkeletonFirstSwingMs = 1000;
    inline constexpr NH<float> kSkeletonStrikePct{ 2.0f, 2.5f };
    // The opening threat a new skeleton puts on the Baron's victim, so it runs at the tank first ("on normal threat":
    // any player who out-threatens it takes it).
    float constexpr kSkeletonOpeningThreat = 10.f;
    // Its corpse goes soon after the pile appears under it.
    std::uint32_t constexpr kSkeletonCorpseMs = 1500;

    // BR2 Bone piles: one where each skeleton dies, until raised (heroic) or the fight ends. The summoned object's
    // respawn timer only bounds a pile the fight somehow forgot.
    std::uint32_t constexpr kPileLifeSecs = 3600;
    // The drop spot's avoid circle around a pile (a point on the floor; the landing's own radius counts, X2).
    float constexpr kPileAvoidRadius = 1.f;
    // The drop spot's room (X2 `Room`): a circle inside the oval room (48 x 40 yd, x 4008-4056, y -3327 to -3369;
    // handoff section 3.8), so the edge candidates stay on the floor; the leash circle (r 25) reaches into the walls.
    inline constexpr Vec2 kDropRoomCenter{ 4032.0f, -3348.0f };
    float constexpr kDropRoomRadius = 20.f;
    // A pile and a rot share the floor when their heights differ by at most this.
    float constexpr kPileZBand = 4.f;

    // BR3 Death and Decay: a 6 yd circle follows a random non-tank for 3 s (emote line 10), then the ground rots
    // where they stand: 10 s / 15 s (the hard mode 45 s, S15's hook), 4% / 5% Shadow per second, one Weakened per
    // player per rot, 1 s grace. Heroic: every pile inside rises, at the landing and every second while it lasts.
    // First at 12 s, then every 15 s.
    std::uint32_t constexpr kDeathAndDecayFirstMs = 12000;
    std::uint32_t constexpr kDeathAndDecayEveryMs = 15000;
    std::uint32_t constexpr kDeathAndDecayWarnMs = 3000;
    float constexpr kRotRadius = 6.f;
    inline constexpr NH<std::uint32_t> kRotLifeMs{ 10000, 15000 };
    inline constexpr NH<float> kRotPct{ 4.f, 5.f };
    std::uint32_t constexpr kRotGraceMs = 1000;         // the first tick, one tick after the landing
    std::uint32_t constexpr kRotTickMs = 1000;
    // The look (SPELL_BR_ROT_LOOK) is a 45 s area aura (the longest rot); a shorter rot's stalker despawns with it.
    std::uint32_t constexpr kRotLookMs = 45000;
    static_assert(kRotLifeMs.heroic <= kRotLookMs && kRotGraceMs < kRotLifeMs.normal, "the look covers every rot");

    // BR4 Unholy Aura: 100 yd, every 2 s, 1% / 1.5% Shadow base, +0.5% per living servant.
    std::uint32_t constexpr kUnholyAuraPeriodMs = 2000;
    float constexpr kUnholyAuraRadius = 100.f;
    inline constexpr NH<float> kUnholyAuraBasePct{ 1.f, 1.5f };
    float constexpr kUnholyAuraPerServantPct = 0.5f;

    // BR5 the stock tank kit (DD scales the stock spells on heroic): Shadow Bolt 17393 (a 2 s cast on his victim,
    // every 6 to 9 s; it waits for his other casts, CastQueue), Mortal Strike 15708 every 9 to 15 s, Cleave 15284 every
    // 7 to 11 s (both instant, in melee range).
    std::uint32_t constexpr kShadowBoltFirstMs = 5000;
    std::uint32_t constexpr kShadowBoltMinMs = 6000;
    std::uint32_t constexpr kShadowBoltMaxMs = 9000;
    std::uint32_t constexpr kShadowBoltCastMs = 2000;
    std::uint32_t constexpr kMortalStrikeFirstMs = 9000;
    std::uint32_t constexpr kMortalStrikeMinMs = 9000;
    std::uint32_t constexpr kMortalStrikeMaxMs = 15000;
    std::uint32_t constexpr kCleaveFirstMs = 5000;
    std::uint32_t constexpr kCleaveMinMs = 7000;
    std::uint32_t constexpr kCleaveMaxMs = 11000;
    std::uint32_t constexpr kRetryMs = 2000;            // nobody to target, or out of reach: try again this soon
    std::uint32_t constexpr kMeleeRetryMs = 1000;

    // The cast queue (DungeonKit::CastQueue): his casts with a cast bar never overlap. S14's own id is the Shadow Bolt
    // (priority 0, a filler that never delays a mechanic); S15's hard mode casts use ids from kHardModeCastBase.
    enum BaronCasts : std::uint32_t
    {
        CAST_SHADOW_BOLT    = 1,
    };
    std::uint32_t constexpr kHardModeCastBase = 100;
    std::uint64_t constexpr kCastSpacingMs = 500;       // between two spaced casts (the hard mode's)

    // BR2 for the bots (ST "Bots": "the bot tank steps him a few yards off the piles after each wave"): when a pile
    // lies within kParkTriggerYd of him, a hidden Park zone (tank only) on a clean floor spot kParkMinYd..kParkMaxYd
    // away, at least kParkClearYd from every pile and outside every rot, holds him there for kParkHoldMs.
    float constexpr kParkTriggerYd = 4.f;
    float constexpr kParkClearYd = 4.f;
    float constexpr kParkMinYd = 6.f;
    float constexpr kParkMaxYd = 14.f;
    float constexpr kParkRadius = 4.f;
    std::uint32_t constexpr kParkHoldMs = 6000;
    std::uint32_t constexpr kParkCooldownMs = 4000;
    std::uint32_t constexpr kParkCheckMs = 1000;

    // The stock leash (smart_scripts 10440 rows 17-18 and their `conditions` rows, kept: ST "Stock kit"): he evades
    // within 21 yd of Ramstein's door 175405, or within 4 yd of his own door 175796 while more than 13 yd from
    // Menethil's Gift 176631.
    float constexpr kLeashRamsteinDoorYd = 21.f;
    float constexpr kLeashOwnDoorYd = 4.f;
    float constexpr kLeashGiftYd = 13.f;
    std::uint32_t constexpr kLeashCheckMs = 1000;

    // Melee: DamageModifier 8 on normal (the stock value, set by the DT file); heroic is the heroic template's tier.

    // ----------------------------------------------------------------------------------------------------------------
    // BR1 Raise Dead: walls and the cap
    // ----------------------------------------------------------------------------------------------------------------

    // The two rows of stock Raise Dead points (StratholmeRework.h kRaiseDeadPoints: south row first, then north).
    enum class Wall : std::uint8_t
    {
        South = 0,
        North = 1,
    };

    constexpr Wall OtherWall(Wall w)
    {
        return w == Wall::South ? Wall::North : Wall::South;
    }

    constexpr char const* WallName(Wall w)
    {
        return w == Wall::South ? "south" : "north";
    }

    // The wall's three points, in the stock order.
    inline std::array<Point3, kWaveSize> WallPoints(Wall w)
    {
        std::size_t const first = w == Wall::South ? 0 : kWaveSize;
        return { StratholmeRework::kRaiseDeadPoints[first], StratholmeRework::kRaiseDeadPoints[first + 1],
            StratholmeRework::kRaiseDeadPoints[first + 2] };
    }

    // How many skeletons a wave raises with `alive` already up (normal: up to the cap of 6; heroic: all three).
    constexpr std::uint32_t WaveCount(std::uint32_t alive, bool heroic)
    {
        std::uint32_t const cap = kSkeletonCap(heroic);
        if (!cap)
            return kWaveSize;
        return alive >= cap ? 0 : std::min(kWaveSize, cap - alive);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BR4 Unholy Aura
    // ----------------------------------------------------------------------------------------------------------------

    // The percent of the reference row one pulse deals with `servants` living servants.
    constexpr float UnholyAuraPct(bool heroic, std::uint32_t servants)
    {
        return kUnholyAuraBasePct(heroic) + kUnholyAuraPerServantPct * float(servants);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BR2 / BR3 piles and rots
    // ----------------------------------------------------------------------------------------------------------------

    // A pile at `pile` lies inside a rot of `radius` at `rot`: within the radius on the plane and on the same floor.
    inline bool PileInRot(Point3 pile, Point3 rot, float radius)
    {
        return DungeonKit::Distance(pile.XY(), rot.XY()) <= radius && std::fabs(pile.z - rot.z) <= kPileZBand;
    }

    // The indices of the piles inside a rot (the ones it raises).
    inline std::vector<std::size_t> PilesInRot(std::vector<Point3> const& piles, Point3 rot, float radius)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < piles.size(); ++i)
            if (PileInRot(piles[i], rot, radius))
                out.push_back(i);
        return out;
    }

    // The distance from `p` to the nearest pile on the plane (infinity without piles).
    inline float NearestPileYd(Vec2 p, std::vector<Point3> const& piles)
    {
        float best = std::numeric_limits<float>::infinity();
        for (Point3 const& pile : piles)
            best = std::min(best, DungeonKit::Distance(p, pile.XY()));
        return best;
    }

    // BR2 for the bots: the tank walks him off when a pile lies this close to him.
    inline bool ShouldPark(Vec2 boss, std::vector<Point3> const& piles)
    {
        return NearestPileYd(boss, piles) <= kParkTriggerYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stock leash
    // ----------------------------------------------------------------------------------------------------------------

    // True: he evades (the plane distances from him to Ramstein's door, his own door and Menethil's Gift).
    constexpr bool StockLeashBreached(float toRamsteinDoor, float toOwnDoor, float toGift)
    {
        return toRamsteinDoor <= kLeashRamsteinDoorYd || (toOwnDoor <= kLeashOwnDoorYd && toGift > kLeashGiftYd);
    }

    inline bool StockLeashBreached(Vec2 at)
    {
        return StockLeashBreached(DungeonKit::Distance(at, StratholmeRework::kRamsteinDoor.XY()),
            DungeonKit::Distance(at, StratholmeRework::kBaronDoor.XY()),
            DungeonKit::Distance(at, StratholmeRework::kMenethilsGift.XY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). Raise Dead and Death
    // and Decay have no cast bar, so they fire on time even while he casts; Mortal Strike and Cleave wait for the cast
    // to end and for melee range. The Shadow Bolt and the hard mode's casts go through the cast queue instead.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        RaiseDead = 0,
        DeathAndDecay = 1,
        MortalStrike = 2,
        Cleave = 3,
    };
    std::size_t constexpr kBeatCount = 4;

    struct Timeline
    {
        std::uint64_t now = 0;                          // ms since the pull
        std::array<std::uint64_t, kBeatCount> next{ { kRaiseDeadFirstMs, kDeathAndDecayFirstMs, kMortalStrikeFirstMs,
            kCleaveFirstMs } };

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        bool Due(Beat b) const
        {
            return now >= next[static_cast<std::size_t>(b)];
        }

        std::uint64_t NextAt(Beat b) const
        {
            return next[static_cast<std::size_t>(b)];
        }

        // Fired: the next one `everyMs` from now.
        void Done(Beat b, std::uint32_t everyMs)
        {
            next[static_cast<std::size_t>(b)] = now + everyMs;
        }

        // Fired: the next one the beat's fixed cooldown from now (Raise Dead, Death and Decay).
        void Done(Beat b)
        {
            Done(b, Every(b));
        }

        // Nobody to target, or out of reach: try again shortly instead of a full cooldown.
        void Retry(Beat b, std::uint32_t inMs = kRetryMs)
        {
            next[static_cast<std::size_t>(b)] = now + inMs;
        }

        // The fixed cooldowns; the stock kit's beats draw theirs from a range (the AI passes it to Done).
        static constexpr std::uint32_t Every(Beat b)
        {
            switch (b)
            {
                case Beat::RaiseDead: return kRaiseDeadEveryMs;
                case Beat::DeathAndDecay: return kDeathAndDecayEveryMs;
                case Beat::MortalStrike: return kMortalStrikeMinMs;
                case Beat::Cleave: return kCleaveMinMs;
            }
            return kRaiseDeadEveryMs;
        }
    };
}

#endif
