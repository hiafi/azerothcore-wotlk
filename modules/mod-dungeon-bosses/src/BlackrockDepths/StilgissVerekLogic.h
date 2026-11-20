/*
 * mod-dungeon-bosses, Blackrock Depths D8:
 * Warder Stilgiss (9041) and Verek (9042), "The Antiquarian of Blackrock City": the pure, host-testable part (no
 * engine headers). Build spec SP 353-407 (docs/dungeons/blackrock-depths-2-shadowforge-city.md, rulings 40, 41, 88),
 * handoff section 3.4 rows D8, section 3.5 row D8, section 3.6. Tested by tests/brd_stilgiss_verek_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsStilgissVerek (211050-211089), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/stilgiss_verek.py
 *   Tuning         NH<> constants: one number per difficulty, straight from the build spec (percents of the reference
 *                  row: N level 54, H level 60)
 *   Coffer engine  SV1: no repeats until all five artifacts have been drawn; at most 2 (heroic 3) active, the oldest
 *                  dropped; the draw avoids an artifact he still holds when a new cycle starts (designer default)
 *   Rim            the twelve Relic Coffer Doors [db] and the spot he stands on to open each one
 *   Wand           SV5: three 3 yd chords across the hall, 60 degrees apart
 *   Bindings       SV3: the chained pair is hurt while more than 8 yd apart
 *   Black Blood    SV6: a pool is live from its marker's end for 30 s; Verek heals 2% a second inside one
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_STILGISS_VEREK_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_STILGISS_VEREK_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace BrdStilgissVerek
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsStilgissVerek;

    enum StilgissVerekSpells : std::uint32_t
    {
        SPELL_SV_OPEN_COFFER        = kSpellSlice.first + 0,    // 211050 SV1 the 2 s opening (a cast bar, Physical)
        SPELL_SV_EYE_HIT            = kSpellSlice.first + 1,    // 211051 SV2 Eye of Kajal's beam (resolve copy, Shadow)
        SPELL_SV_BINDINGS           = kSpellSlice.first + 2,    // 211052 SV3 the 8 s DUMMY debuff on both of the pair
        SPELL_SV_BINDINGS_TICK      = kSpellSlice.first + 3,    // 211053 SV3 4% (heroic 6%) a second while apart
        SPELL_SV_BINDINGS_CHAIN     = kSpellSlice.first + 4,    // 211054 SV3 the chain look (a channel, from a stalker)
        SPELL_SV_MAGMA_CAST         = kSpellSlice.first + 5,    // 211055 SV4 the 2.5 s bar (Fire)
        SPELL_SV_MAGMA_HIT          = kSpellSlice.first + 6,    // 211056 SV4 the band's hit (resolve copy, Fire)
        SPELL_SV_WAND_HIT           = kSpellSlice.first + 7,    // 211057 SV5 a line's hit (resolve copy, Holy)
        SPELL_SV_BLOOD_HIT          = kSpellSlice.first + 8,    // 211058 SV6 a pool's tick (resolve copy, Shadow)
        SPELL_SV_BLOOD_HEAL         = kSpellSlice.first + 9,    // 211059 SV6 Verek's 2% heal in a pool
        SPELL_SV_NOVA_CAST          = kSpellSlice.first + 10,   // 211060 SV7 the 1.5 s bar (Arcane: see the notes)
        SPELL_SV_NOVA_HIT           = kSpellSlice.first + 11,   // 211061 SV7 the nova's hit (resolve copy, Frost)
        SPELL_SV_NOVA_ROOT          = kSpellSlice.first + 12,   // 211062 SV7 the 2 s root (the rider)
        SPELL_SV_FROSTBOLT          = kSpellSlice.first + 13,   // 211063 SV8 his 3 s interruptible bolt (Frost)
        SPELL_SV_CURSE_OF_BLOOD     = kSpellSlice.first + 14,   // 211064 SV9 Verek's curse: +10% physical taken, 30 s
        SPELL_SV_BLOOD_LOOK         = kSpellSlice.first + 15,   // 211065 SV6 the pool's dark patch (a stalker state)
        // 211066-211089 spare
    };
    static_assert(SPELL_SV_BLOOD_LOOK <= kSpellSlice.last, "the D8 spells must stay in their slice");

    // Stock spells the fight keeps as they are (the spec's "Keep"): Frost Armor (out of combat, chills melee) and
    // Verek's Enrage (+10% physical damage and +30% attack speed, Enrage dispel type).
    inline constexpr std::uint32_t SPELL_STOCK_FROST_ARMOR = 12544;
    inline constexpr std::uint32_t SPELL_STOCK_ENRAGE = 8599;

    // creature_text groups of 9041 (SP "Text"; kTextRanges 0-6 in BlackrockDepthsRework.h) and of 9042 (group 0 stock).
    enum StilgissTexts : std::uint8_t
    {
        YELL_ST_PULL        = 0,    // "Thieves, in my Vault? ..."
        EMOTE_ST_EYE        = 1,    // "%s draws the Eye of Kajal from a coffer!" (boss emote, 41)
        EMOTE_ST_BINDINGS   = 2,
        EMOTE_ST_MAGMA      = 3,
        EMOTE_ST_WAND       = 4,
        EMOTE_ST_BLOOD      = 5,
        YELL_ST_DEATH       = 6,    // "My... collection..."
    };
    inline constexpr std::uint8_t EMOTE_VK_ENRAGE = 0;     // Verek's stock group 0 "%s becomes enraged!" (now type 41)

    // Registry tags (the failure ledger and the playtest greps key on them).
    enum StilgissVerekTags : std::uint32_t
    {
        TAG_SV_EYE          = 1,    // SV2
        TAG_SV_BINDINGS     = 2,    // SV3
        TAG_SV_MAGMA        = 3,    // SV4
        TAG_SV_WAND         = 4,    // SV5
        TAG_SV_BLOOD        = 5,    // SV6
        TAG_SV_NOVA         = 6,    // SV7
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The artifacts and the collection (SV1)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Artifact : std::uint8_t
    {
        Eye = 0,            // Eye of Kajal: a beam through a random player
        Bindings = 1,       // Black Steel Bindings: two players chained
        Magma = 2,          // Magma Forged Band: a band round him
        Wand = 3,           // Wand of Eternal Light: three lines across the hall
        BlackBlood = 4,     // Black Blood of the Tormented: pools
    };
    inline constexpr std::uint8_t kArtifactCount = 5;
    inline constexpr std::uint8_t kAllDrawnMask = 0x1F;
    inline constexpr std::uint8_t kMaxCollection = 3;       // the heroic cap; normal holds 2

    constexpr std::uint8_t BitOf(Artifact a) { return static_cast<std::uint8_t>(1u << static_cast<unsigned>(a)); }

    constexpr char const* ArtifactName(Artifact a)
    {
        switch (a)
        {
            case Artifact::Eye:         return "eye";
            case Artifact::Bindings:    return "bindings";
            case Artifact::Magma:       return "magma";
            case Artifact::Wand:        return "wand";
            case Artifact::BlackBlood:  return "blood";
        }
        return "?";
    }

    // The emote line of a draw (SV1 "emote lines 1 to 5").
    constexpr std::uint8_t EmoteOf(Artifact a)
    {
        return static_cast<std::uint8_t>(EMOTE_ST_EYE + static_cast<unsigned>(a));
    }

    // SV1: the coffer engine. First at 8 s, then every 25 s (heroic 20 s); the opening takes 2 s; an artifact's first
    // use is 3 s after its draw. Up to 2 (heroic 3) artifacts are active at once.
    inline constexpr std::uint32_t kCofferFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kCofferEveryMs{ 25000, 20000 };
    inline constexpr NH<std::uint8_t> kMaxActive{ 2, 3 };
    inline constexpr std::uint32_t kOpenMs = 2000;
    inline constexpr std::uint32_t kFirstAfterDrawMs = 3000;
    inline constexpr std::uint32_t kWalkTimeoutMs = 9000;      // a walk that never arrives opens where he stands

    // The start of the next beat on a fixed cadence (start to start): never earlier than 1 ms from now.
    constexpr std::uint64_t NextDue(std::uint64_t plannedMs, std::uint32_t everyMs, std::uint64_t nowMs)
    {
        return std::max<std::uint64_t>(plannedMs + everyMs, nowMs + 1);
    }

    // The artifact drawn next. `drawnMask` holds the artifacts of the current cycle already drawn; once all five are
    // out the cycle restarts. A new cycle skips an artifact he still holds (`activeMask`) so a draw is never a copy of
    // one already out, unless that leaves nothing. `roll` picks among the candidates (any number: taken modulo).
    struct Draw
    {
        Artifact artifact = Artifact::Eye;
        std::uint8_t drawnMask = 0;     // the cycle's mask after this draw
    };

    constexpr Draw DrawNext(std::uint8_t drawnMask, std::uint8_t activeMask, std::uint32_t roll)
    {
        if ((drawnMask & kAllDrawnMask) == kAllDrawnMask)
            drawnMask = 0;
        std::uint8_t candidates = static_cast<std::uint8_t>(~drawnMask & kAllDrawnMask);
        std::uint8_t const fresh = static_cast<std::uint8_t>(candidates & ~activeMask);
        if (fresh != 0)
            candidates = fresh;
        std::uint32_t count = 0;
        for (std::uint8_t i = 0; i < kArtifactCount; ++i)
            if (candidates & (1u << i))
                ++count;
        std::uint32_t pick = roll % count;
        for (std::uint8_t i = 0; i < kArtifactCount; ++i)
        {
            if (!(candidates & (1u << i)))
                continue;
            if (pick == 0)
                return { static_cast<Artifact>(i), static_cast<std::uint8_t>(drawnMask | (1u << i)) };
            --pick;
        }
        return { Artifact::Eye, drawnMask };    // unreachable: count >= 1
    }

    // What he holds, oldest first. Add drops the oldest past the cap and returns it.
    struct Collection
    {
        std::array<Artifact, kMaxCollection> kinds{};
        std::uint8_t count = 0;
        std::uint8_t drawnMask = 0;

        bool Has(Artifact a) const
        {
            for (std::uint8_t i = 0; i < count; ++i)
                if (kinds[i] == a)
                    return true;
            return false;
        }

        std::uint8_t ActiveMask() const
        {
            std::uint8_t mask = 0;
            for (std::uint8_t i = 0; i < count; ++i)
                mask = static_cast<std::uint8_t>(mask | BitOf(kinds[i]));
            return mask;
        }

        std::optional<Artifact> Add(Artifact a, std::uint8_t cap)
        {
            cap = std::min<std::uint8_t>(std::max<std::uint8_t>(cap, 1), kMaxCollection);
            std::optional<Artifact> dropped;
            while (count >= cap)
            {
                dropped = kinds[0];
                for (std::uint8_t i = 1; i < count; ++i)
                    kinds[i - 1] = kinds[i];
                --count;
            }
            kinds[count++] = a;
            return dropped;
        }

        void Clear()
        {
            kinds = {};
            count = 0;
            drawnMask = 0;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The artifacts' numbers (SP "New mechanics": damage N / H as a percent of the reference row)
    // ----------------------------------------------------------------------------------------------------------------

    // How often each one fires once drawn (the first use is kFirstAfterDrawMs after the draw).
    constexpr std::uint32_t ArtifactEveryMs(Artifact a)
    {
        switch (a)
        {
            case Artifact::Eye:         return 10000;
            case Artifact::Bindings:    return 15000;
            case Artifact::Magma:       return 15000;
            case Artifact::Wand:        return 12000;
            case Artifact::BlackBlood:  return 15000;
        }
        return 15000;
    }

    // SV2 Eye of Kajal: a 4 yd line from him through a random player to the wall, 2 s marker, 25% (heroic 40%) +
    // Weakened.
    inline constexpr float kEyeWidth = 4.f;
    inline constexpr float kEyeOverrunYd = 60.f;               // far past the player: the arena clips it at the wall
    inline constexpr std::uint32_t kEyeWarnMs = 2000;
    inline constexpr NH<float> kEyePct{ 25.f, 40.f };

    // SV3 Black Steel Bindings: two random players chained 8 s; while more than 8 yd apart both take 4% (heroic 6%)
    // a second (a script tick on the AI's own clock, the registry Stacks are the telegraph and the bots' job).
    inline constexpr float kBindingsRangeYd = 8.f;
    inline constexpr float kBindingsZBandYd = 6.f;
    inline constexpr std::uint32_t kBindingsMs = 8000;
    // The registry Stacks resolve this much before the pair ends (R-1-A n6: at exactly 8 s the pair's end cancelled
    // them in the tick the registry judged them, so the MissedStack ledger was racy).
    inline constexpr std::uint32_t kBindingsStackMs = kBindingsMs - 500;
    inline constexpr std::uint32_t kBindingsTickMs = 1000;
    inline constexpr NH<float> kBindingsPct{ 4.f, 6.f };

    // SV4 Magma Forged Band: a 2.5 s bar, then the band 4 to 9 yd round him burns 30% (heroic 45%) + Weakened.
    inline constexpr std::uint32_t kMagmaCastMs = 2500;
    inline constexpr float kMagmaInnerYd = 4.f;
    inline constexpr float kMagmaOuterYd = 9.f;
    inline constexpr NH<float> kMagmaPct{ 30.f, 45.f };

    // SV5 Wand of Eternal Light: three 3 yd lines across the hall, 2 s marker, 20% (heroic 35%) + Weakened.
    inline constexpr std::uint8_t kWandLines = 3;
    inline constexpr float kWandWidth = 3.f;
    inline constexpr std::uint32_t kWandWarnMs = 2000;
    inline constexpr NH<float> kWandPct{ 20.f, 35.f };
    inline constexpr float kWandRingYd = 11.5f;                // chord ends: inside the hall's smallest radius (12.2)
    inline constexpr float kWandMaxOffsetYd = 6.f;             // how far a line may run from the middle

    // SV6 Black Blood of the Tormented: a 3 yd pool where a random player stood, 2 s marker, then 30 s; 4% (heroic 6%)
    // a second; Verek heals 2% of his health a second while he stands in one.
    inline constexpr float kBloodRadiusYd = 3.f;
    inline constexpr std::uint32_t kBloodWarnMs = 2000;
    inline constexpr std::uint32_t kBloodLifeMs = 30000;
    inline constexpr std::uint32_t kBloodTickMs = 1000;
    inline constexpr NH<float> kBloodPct{ 4.f, 6.f };
    inline constexpr float kBloodHealPct = 2.f;
    inline constexpr float kBloodZBandYd = 6.f;

    // SV7 Frost Nova: a 1.5 s bar when 2 or more players are within 10 yd; 10% (heroic 14%) Frost and a 2 s root on
    // everyone inside; 15 s apart, the first no sooner than 8 s (the stock event's 7 to 9 s).
    inline constexpr std::uint32_t kNovaCastMs = 1500;
    inline constexpr float kNovaRadiusYd = 10.f;
    inline constexpr std::uint8_t kNovaMinPlayers = 2;
    inline constexpr std::uint32_t kNovaFirstMs = 8000;
    inline constexpr std::uint32_t kNovaEveryMs = 15000;
    inline constexpr std::uint32_t kNovaRootMs = 2000;
    inline constexpr NH<float> kNovaPct{ 10.f, 14.f };

    // SV8 Frostbolt: his stock 3 s bolt at a random player, every 2.4 to 3.8 s counted from the start of the last
    // one; 8% (heroic 10%) and the stock -50% for 4 s. A reward to interrupt.
    inline constexpr std::uint32_t kFrostboltCastMs = 3000;
    inline constexpr std::uint32_t kFrostboltGapMinMs = 2400;
    inline constexpr std::uint32_t kFrostboltGapMaxMs = 3800;
    inline constexpr NH<float> kFrostboltPct{ 8.f, 10.f };
    inline constexpr std::uint32_t kFrostboltSlowMs = 4000;

    // SV9 / SV10 Verek: Curse of Blood on his victim 3 to 5 s in, then every 30 to 45 s (stock): +10% physical damage
    // taken for 30 s (a Curse: the dispel is a reward). Enrage once below 30% (the stock spell and emote).
    inline constexpr std::uint32_t kCurseFirstMinMs = 3000;
    inline constexpr std::uint32_t kCurseFirstMaxMs = 5000;
    inline constexpr std::uint32_t kCurseEveryMinMs = 30000;
    inline constexpr std::uint32_t kCurseEveryMaxMs = 45000;
    inline constexpr std::uint32_t kCurseMs = 30000;
    inline constexpr float kCursePhysicalPct = 10.f;
    inline constexpr float kEnrageBelowPct = 30.f;

    constexpr bool EnrageDue(float healthPct, bool alreadyEnraged)
    {
        return !alreadyEnraged && healthPct < kEnrageBelowPct;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hall: the twelve Relic Coffer Doors and where he stands to open one
    // ----------------------------------------------------------------------------------------------------------------

    // [db] the Relic Coffer Door spawns (gameobject 174554-174564 and 174566, map 230), 12.8 to 16.6 yd from the hall's
    // center. Index order: by entry.
    inline constexpr std::array<Point3, 12> kCofferDoors{ {
        { 802.021f, -353.522f, -49.342f },      // 174554
        { 797.782f, -349.003f, -49.342f },      // 174555
        { 797.862f, -343.729f, -49.342f },      // 174556
        { 802.325f, -339.540f, -49.342f },      // 174557
        { 811.128f, -331.380f, -49.342f },      // 174558
        { 806.742f, -358.630f, -49.342f },      // 174559
        { 810.909f, -363.110f, -49.342f },      // 174560
        { 816.412f, -363.597f, -49.342f },      // 174561
        { 820.844f, -359.464f, -49.342f },      // 174562
        { 825.268f, -355.339f, -49.342f },      // 174563
        { 829.574f, -351.323f, -49.342f },      // 174564
        { 806.764f, -335.402f, -49.342f },      // 174566
    } };
    inline constexpr std::array<std::uint32_t, 12> kCofferDoorEntries{ {
        174554, 174555, 174556, 174557, 174558, 174559, 174560, 174561, 174562, 174563, 174564, 174566 } };

    inline constexpr float kStandInsetYd = 3.f;                // he stands this far in from the door, toward the middle
    inline constexpr float kStandDropYd = 0.8f;                // the doors' origin sits this far above the floor

    // The spot he stands on to open `door`: `kStandInsetYd` from it toward the hall's center, at floor height.
    inline Point3 StandPointFor(Point3 const& door, Vec2 center = BlackrockDepthsRework::kVaultCenter)
    {
        float const dx = center.x - door.x;
        float const dy = center.y - door.y;
        float const len = std::hypot(dx, dy);
        if (len < 0.01f)
            return { door.x, door.y, door.z - kStandDropYd };
        return { door.x + dx / len * kStandInsetYd, door.y + dy / len * kStandInsetYd, door.z - kStandDropYd };
    }

    // The next door: any but the last one he used (`previous` < 0: any), picked by `roll`.
    constexpr std::size_t NextDoor(int previous, std::uint32_t roll)
    {
        std::size_t const n = kCofferDoors.size();
        if (previous < 0 || static_cast<std::size_t>(previous) >= n)
            return roll % n;
        return (static_cast<std::size_t>(previous) + 1 + roll % (n - 1)) % n;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Wand of Eternal Light: three chords across the hall
    // ----------------------------------------------------------------------------------------------------------------

    struct Chord
    {
        Vec2 from;
        Vec2 to;
    };

    // Three lines whose directions are `baseAngle`, +60 and +120 degrees, line i running `offsets[i]` yd (at most
    // kWandMaxOffsetYd either way) from the hall's middle; both ends sit on the ring of radius kWandRingYd.
    inline std::array<Chord, kWandLines> WandChords(float baseAngle, std::array<float, kWandLines> const& offsets,
        Vec2 center = BlackrockDepthsRework::kVaultCenter)
    {
        std::array<Chord, kWandLines> out{};
        for (std::size_t i = 0; i < kWandLines; ++i)
        {
            float const angle = baseAngle + static_cast<float>(i) * DungeonKit::kPi / 3.f;
            float const ux = std::cos(angle);
            float const uy = std::sin(angle);
            float const off = std::clamp(offsets[i], -kWandMaxOffsetYd, kWandMaxOffsetYd);
            float const half = std::sqrt(std::max(0.f, kWandRingYd * kWandRingYd - off * off));
            float const cx = center.x - uy * off;      // the line's closest point to the middle
            float const cy = center.y + ux * off;
            out[i] = { { cx - ux * half, cy - uy * half }, { cx + ux * half, cy + uy * half } };
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bindings and Black Blood
    // ----------------------------------------------------------------------------------------------------------------

    // SV3: the pair is "apart" when more than 8 yd on the plane, or on another floor (the registry's own height band).
    inline bool BindingsApart(Vec2 a, float za, Vec2 b, float zb)
    {
        return DungeonKit::Distance(a, b) > kBindingsRangeYd || std::fabs(za - zb) > kBindingsZBandYd;
    }

    // SV6: a pool placed at `startMs` has its marker for kBloodWarnMs, then burns for kBloodLifeMs.
    constexpr bool BloodLive(std::uint64_t startMs, std::uint64_t nowMs)
    {
        return nowMs >= startMs + kBloodWarnMs && nowMs < startMs + kBloodWarnMs + kBloodLifeMs;
    }

    // Is a unit at `at` (height `z`) in a pool centered on `center` (height `cz`)? Verek's body counts by its center.
    inline bool InBloodPool(Vec2 center, float cz, Vec2 at, float z)
    {
        return DungeonKit::Distance(center, at) <= kBloodRadiusYd && std::fabs(z - cz) <= kBloodZBandYd;
    }

    // SV7: Frost Nova is cast when this many players or more are within its radius of him.
    constexpr bool NovaWanted(std::uint32_t playersInside)
    {
        return playersInside >= kNovaMinPlayers;
    }
}

#endif
