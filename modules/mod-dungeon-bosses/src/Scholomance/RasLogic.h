/*
 * mod-dungeon-bosses, Scholomance S4: Ras Frostwhisper (10508), the pure, host-testable part (no engine headers): the
 * spell ids, the per-difficulty tuning, the Chill meter and warmth rules, the never-paused fight timeline and the
 * heroic Blizzard drift. Build spec: SC 1171-1230 (build spec), SC 1000-1170 (design), RF1-RF8; handoff section 3.4
 * rows RF, section 3.5 row S4, section 3.6 (normal 195k, heroic 270k). The hard mode (RF3's permanent tomb, RF9-RF11)
 * is WP-S12's, on top of this AI through RasFight.h.
 *
 * Damage percentages are of the reference health row (normal 3,670 / heroic 4,120 non-tank at level 60): the build
 * spec gives N / H percents, and the row makes the rest of the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_LOGIC_H

#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace ScholoRas
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRas;

    // Declared in apps/dbc-tools source/npcs/scholomance/ras_frostwhisper.py (same ids).
    enum RasSpells : std::uint32_t
    {
        SPELL_RF_CHILL              = 206170,   // RF1 the 20-stack meter on every player (never dispellable)
        SPELL_RF_DEEP_CHILL         = 206171,   // RF1 the look from 12 stacks (hidden aura, Aura of Frost's SV 6778)
        SPELL_RF_WARMTH             = 206172,   // RF2 the buff while two or more allies stand within 8 yd
        SPELL_RF_ENTOMBED           = 206173,   // RF3 the 2 s freeze at 20 stacks (stun, no mechanic)
        SPELL_RF_THAW               = 206174,   // RF4 the tomb's burst: resolve copy (Frost)
        SPELL_RF_FROST_MARK         = 206175,   // RF5 the 5 s mark on a non-tank (Frost Beacon's look)
        SPELL_RF_CHILL_NOVA         = 206176,   // RF5 the mark's Nova on allies near it: resolve copy (Frost)
        SPELL_RF_CHILL_NOVA_KNOCK   = 206177,   // RF5 the Nova's rider: the knockback (stock 18099's, shortened)
        SPELL_RF_BLIZZARD_CAST      = 206178,   // RF6 the 1.5 s cast bar
        SPELL_RF_BLIZZARD           = 206179,   // RF6 the 1 s tick: resolve copy (Frost)
        SPELL_RF_BLIZZARD_LOOK      = 206180,   // RF6 the storm on a fixed anchor, 12 s (normal)
        SPELL_RF_BLIZZARD_DRIFT     = 206181,   // RF6 heroic: a 3 s storm the drifting anchor re-casts every 2 s
        SPELL_RF_FROSTBOLT_VOLLEY   = 206182,   // RF7 the 3 s interruptible volley (RefFlat at launch, slow)
        // 206183-206189 spare (206190-206204 are S12's, the hard mode)
    };
    static_assert(kSpellSlice.Contains(SPELL_RF_CHILL), "Ras spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_RF_FROSTBOLT_VOLLEY), "Ras spells sit in his slice");
    static_assert(!ScholomanceRework::kSpellsRasHardMode.Contains(SPELL_RF_FROSTBOLT_VOLLEY), "S12 keeps its ids");

    // Registry tags (the build spec's RF numbers).
    enum RasTags : std::uint32_t
    {
        TAG_CHILL           = 1,    // RF1 the self-keyed RunOut (bots step out before they freeze)
        TAG_WARMTH          = 2,    // RF2 the always-on warm Stack (Cluster)
        TAG_THAW            = 4,
        TAG_FROST_MARK      = 5,
        TAG_BLIZZARD        = 6,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC "Tuning starting points" and the build spec table, approved 2026-10-30)
    // ----------------------------------------------------------------------------------------------------------------

    // RF1 Chill: 20 stacks freeze; +1 per second cold; warm: nothing on normal, +1 per 3 s on heroic. Never melts.
    std::uint32_t constexpr kChillMax = 20;
    std::uint32_t constexpr kChillColdPerBeat = 1;
    std::uint32_t constexpr kChillBeatMs = 1000;
    inline constexpr NH<std::uint32_t> kWarmBeatsPerStack{ 0, 3 };     // 0: a warm player builds nothing
    std::uint32_t constexpr kDeepChillAt = 12;                          // the second look (VISUALS-REPORT, Ras)
    // Bots: a player at this many stacks is a self-keyed RunOut carrier (steps out to freeze alone) and leaves the
    // warm Stack's eligibility (SC "Bots": "Chill at 17 or more").
    std::uint8_t constexpr kChillRunOutAt = 17;
    float constexpr kChillRunOutRadius = 8.f;           // the thaw is 6 yd; 2 yd of margin for bodies
    // The rolling RunOut: re-registered every kRunOutRefreshMs with a kRunOutWarnMs warning, the old one cancelled
    // first, so it never resolves (no empty hits in the combat log; the kit's Pickups precedent) and bots always see
    // it.
    std::uint32_t constexpr kRunOutWarnMs = 4000;
    std::uint32_t constexpr kRunOutRefreshMs = 2000;
    static_assert(kRunOutRefreshMs < kRunOutWarnMs, "the rolling RunOut is replaced before it resolves");

    // RF2 Warmth of the living: two or more living allies within 8 yd (players; an entombed one gives no warmth).
    float constexpr kWarmRadius = 8.f;
    std::uint32_t constexpr kWarmAllies = 2;
    // Bots: the warm Stack is a Cluster of 2 at 7 yd, inside the 8 yd rule, so a bot that satisfies it is warm.
    float constexpr kWarmStackRadius = 7.f;
    std::uint32_t constexpr kWarmStackMs = 30u * 60u * 1000u;           // the whole fight (cancelled at its end)
    std::uint32_t constexpr kWarmStackTickMs = 1000;

    // RF3 Entombed / RF4 Thaw: a 2 s freeze at 20; the tomb bursts 6 yd around it (the frozen player is spared):
    // 30% / 45% Frost and 1 Weakened (ruling 21); heroic +3 Chill on everyone hit.
    std::uint32_t constexpr kTombMs = 2000;
    float constexpr kThawRadius = 6.f;
    inline constexpr NH<float> kThawPct{ 30.f, 45.f };
    inline constexpr NH<std::uint32_t> kThawChill{ 0, 3 };

    // RF5 Frost Mark: a random non-tank, 5 s; then a 10 yd Chill Nova on the marked player: allies inside take 40% /
    // 55% Frost, +5 Chill and a knockback; the marked player is not hit. 10 s, then every 15 s.
    std::uint32_t constexpr kFrostMarkFirstMs = 10000;
    std::uint32_t constexpr kFrostMarkEveryMs = 15000;
    std::uint32_t constexpr kFrostMarkWarnMs = 5000;
    float constexpr kFrostMarkRadius = 10.f;
    inline constexpr NH<float> kFrostMarkPct{ 40.f, 55.f };
    std::uint32_t constexpr kFrostMarkChill = 5;
    // The Nova's knockback (stock 18099 throws at 40 yd/s, which would clear the study): MiscValue 120 (12 yd/s) and
    // BasePoints 60 (6 yd/s up) in the rider spell, about 7 yd. Mirrored for the declaration's host test.
    std::int32_t constexpr kNovaKnockMisc = 120;
    std::int32_t constexpr kNovaKnockBasePoints = 60;

    // RF6 Blizzard: a 1.5 s cast, 6 yd on a random non-tank in the warm stack, 12 s, a tick every second: 8% / 12%
    // Frost and +2 Chill per tick. 6 s, then every 15 s. Heroic: up to 3 at once (one per non-tank picked), each
    // drifting 1.5 yd/s.
    std::uint32_t constexpr kBlizzardFirstMs = 6000;
    std::uint32_t constexpr kBlizzardEveryMs = 15000;
    std::uint32_t constexpr kBlizzardCastMs = 1500;
    std::uint32_t constexpr kBlizzardLifeMs = 12000;
    std::uint32_t constexpr kBlizzardTickMs = 1000;
    float constexpr kBlizzardRadius = 6.f;
    inline constexpr NH<float> kBlizzardPct{ 8.f, 12.f };
    std::uint32_t constexpr kBlizzardChill = 2;
    inline constexpr NH<std::uint32_t> kBlizzardCount{ 1, 3 };
    float constexpr kBlizzardDriftSpeed = 1.5f;                         // yd/s: the anchor's speed_walk 0.6 x 2.5
    float constexpr kBlizzardDriftYd = kBlizzardDriftSpeed * float(kBlizzardLifeMs) / 1000.f;   // 18 yd
    std::uint32_t constexpr kBlizzardDriftLookEveryMs = 2000;           // the drifting storm's re-cast beat
    // The anchor lives for the cast, the storm and a margin, then despawns.
    std::uint32_t constexpr kBlizzardAnchorLifeMs = kBlizzardCastMs + kBlizzardLifeMs + 1000;

    // RF7 Frostbolt Volley: a 3 s interruptible cast at everyone in the room: 15% / 40% Frost and the stock slow;
    // heroic +3 Chill on everyone hit. 15 s, then every 20 s (one interrupt per 10 s cooldown is enough).
    std::uint32_t constexpr kVolleyFirstMs = 15000;
    std::uint32_t constexpr kVolleyEveryMs = 20000;
    std::uint32_t constexpr kVolleyCastMs = 3000;
    inline constexpr NH<float> kVolleyPct{ 15.f, 40.f };
    inline constexpr NH<std::uint32_t> kVolleyChill{ 0, 3 };
    float constexpr kVolleyRadius = 40.f;                               // the whole study and the Kormok hall

    // RF8 Frost Armor (stock 18100) is re-cast out of combat on this beat when it is missing.
    std::uint32_t constexpr kFrostArmorCheckMs = 5000;

    // Melee: DamageModifier 3.5 on normal (the stock value, kept); heroic is the heroic template's tier (WP-T).

    // ----------------------------------------------------------------------------------------------------------------
    // RF1 / RF2 rules
    // ----------------------------------------------------------------------------------------------------------------

    // Warm: two or more living allies within kWarmRadius (the caller counts them).
    constexpr bool IsWarm(std::uint32_t alliesWithin)
    {
        return alliesWithin >= kWarmAllies;
    }

    // One player's Chill state between beats (the heroic warm build counts warm beats).
    struct ChillClock
    {
        std::uint32_t warmBeats = 0;

        // The stacks one beat adds: cold +1; warm nothing on normal, +1 every third warm beat on heroic. A cold beat
        // does not reset the warm count (a third of the rate over the whole fight).
        std::uint32_t Beat(bool warm, bool heroic)
        {
            if (!warm)
                return kChillColdPerBeat;
            std::uint32_t const every = kWarmBeatsPerStack(heroic);
            if (!every)
                return 0;
            if (++warmBeats < every)
                return 0;
            warmBeats = 0;
            return 1;
        }
    };

    // The meter after `delta`, clamped to [0, kChillMax].
    constexpr std::uint32_t ChillAfter(std::uint32_t current, std::int32_t delta)
    {
        std::int64_t const v = static_cast<std::int64_t>(current) + delta;
        return v <= 0 ? 0u : (v >= kChillMax ? kChillMax : static_cast<std::uint32_t>(v));
    }

    // RF3: the meter freezes its player.
    constexpr bool Freezes(std::uint32_t stacks)
    {
        return stacks >= kChillMax;
    }

    constexpr bool DeepChill(std::uint32_t stacks)
    {
        return stacks >= kDeepChillAt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). A hold (S12's
    // transition) stops the clock; a beat that comes due while Ras casts stays due until the cast ends.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        FrostMark = 0,
        Blizzard = 1,
        Volley = 2,
    };
    std::size_t constexpr kBeatCount = 3;
    std::uint32_t constexpr kRetryMs = 2000;           // nobody to target: try again this soon

    struct Timeline
    {
        std::uint32_t now = 0;                          // ms since the pull, while not held
        std::array<std::uint32_t, kBeatCount> next{ { kFrostMarkFirstMs, kBlizzardFirstMs, kVolleyFirstMs } };
        std::uint32_t chillAcc = 0;

        // `held`: the clock stands still (S12's transition): nothing comes due and Chill does not build.
        void Advance(std::uint32_t diff, bool held)
        {
            if (held)
                return;
            now += diff;
            chillAcc += diff;
        }

        // Whole Chill beats elapsed since the last call.
        std::uint32_t TakeChillBeats()
        {
            std::uint32_t const beats = chillAcc / kChillBeatMs;
            chillAcc -= beats * kChillBeatMs;
            return beats;
        }

        bool Due(Beat b) const
        {
            return now >= next[static_cast<std::size_t>(b)];
        }

        // Fired: the next one is a full cooldown from now.
        void Done(Beat b)
        {
            next[static_cast<std::size_t>(b)] = now + Every(b);
        }

        // Nobody to target: try again shortly instead of a full cooldown.
        void Retry(Beat b)
        {
            next[static_cast<std::size_t>(b)] = now + kRetryMs;
        }

        static constexpr std::uint32_t Every(Beat b)
        {
            switch (b)
            {
                case Beat::FrostMark: return kFrostMarkEveryMs;
                case Beat::Blizzard: return kBlizzardEveryMs;
                case Beat::Volley: return kVolleyEveryMs;
            }
            return kFrostMarkEveryMs;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RF6 heroic drift
    // ----------------------------------------------------------------------------------------------------------------

    // Where a Blizzard drifting `length` yd from `start` along `facing` ends, kept inside the circle (`center`,
    // `radius` - `margin`) so its whole area stays on Ras's floor. A start already outside that circle drifts toward
    // the center instead.
    inline Vec2 DriftEnd(Vec2 start, float facing, float length, Vec2 center, float radius, float margin)
    {
        float const inner = std::max(0.f, radius - margin);
        float const fromCenter = DungeonKit::Distance(start, center);
        if (fromCenter >= inner)
            return DungeonKit::Advance(start, DungeonKit::BearingTo(start, center), std::min(length, fromCenter));
        // |start + t d - center| = inner with t >= 0: where the heading leaves the circle.
        float const dx = std::cos(facing);
        float const dy = std::sin(facing);
        float const px = start.x - center.x;
        float const py = start.y - center.y;
        float const b = px * dx + py * dy;
        float const c = px * px + py * py - inner * inner;     // < 0: inside
        float const exit = -b + std::sqrt(std::max(0.f, b * b - c));
        return DungeonKit::Advance(start, facing, std::min(length, std::max(0.f, exit)));
    }

    // The circle a drift stays in: RasArena() (ScholomanceRework.h, the leash circle; the host test pins the match),
    // less the storm's own radius.
    inline constexpr Vec2 kDriftCenter{ -35.0f, 138.0f };
    float constexpr kDriftRadius = 28.f;
    float constexpr kDriftMargin = kBlizzardRadius;
}

#endif
