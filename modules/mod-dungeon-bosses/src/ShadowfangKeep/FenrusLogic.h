/*
 * mod-dungeon-bosses, Shadowfang Keep: Fenrus the Devourer (WP-S7), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, the phase rules, the Void Pulse clock, the Shadow Scar factor and
 * the strike point picks. Build spec: SK 1183-1234 (build spec), SK 1087-1182 (design), FN1-FN9; handoff section 3.5
 * rows FN, section 3.6 row S7, section 7 #15 (the fake death).
 *
 * Percentages are of the reference health row (normal 1,300 / heroic 4,120 non-tank): the same percent on both
 * difficulties, the row makes the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_FENRUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_FENRUS_LOGIC_H

#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace Fenrus
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using Ms = std::chrono::milliseconds;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsFenrus;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/fenrus_the_devourer.py (same ids).
    enum FenrusSpells : std::uint32_t
    {
        SPELL_FENRUS_ARUGALS_LIGHTNING      = 206020,   // FN1 the strike (resolve copy, Nature)
        SPELL_FENRUS_LIGHTNING_ARRIVAL      = 206021,   // FN1 / FN2 the bolt on the voidwalker stepping out (look)
        SPELL_FENRUS_VOID_PULSE             = 206022,   // FN3 the voidwalker's 1.5 s interruptible cast (Shadow)
        SPELL_FENRUS_SHADOW_FENRUS          = 206023,   // FN5 heroic: the shadow wolf look, cast at the raise
        SPELL_FENRUS_SHADOW_LEAP_CAST       = 206024,   // FN6 heroic: the 2 s crouch (cast bar)
        SPELL_FENRUS_SHADOW_LEAP            = 206025,   // FN6 heroic: the landing (resolve copy, Shadow, x Scar)
        SPELL_FENRUS_SHADOW_SCAR            = 206026,   // FN7 heroic: the stacking debuff (Bait rule and rider)
        SPELL_FENRUS_SHADOW_LIGHTNING       = 206027,   // FN8 heroic: the strike (resolve copy, Shadow)
        SPELL_FENRUS_SHADOW_LIGHTNING_LOOK  = 206028,   // FN8 heroic: the bolt on the strike stalker (look)
        // 206029-206039 spare
    };
    static_assert(kSlice.Contains(SPELL_FENRUS_ARUGALS_LIGHTNING), "Fenrus spells sit in his slice");
    static_assert(kSlice.Contains(SPELL_FENRUS_SHADOW_LIGHTNING_LOOK), "Fenrus spells sit in his slice");

    // Registry tags (the build spec's FN numbers).
    enum FenrusTags : std::uint32_t
    {
        TAG_ARUGALS_LIGHTNING   = 1,
        TAG_SHADOW_LEAP         = 6,
        TAG_SHADOW_LIGHTNING    = 8,
    };

    // The fight's phases. Rising is the heroic fake death: one second of stillness at 1 health (handoff s7 #15).
    enum class Phase : std::uint8_t
    {
        One,
        Rising,
        Two,
    };

    // Descriptor phases (Mechanic::SetPhase).
    std::uint32_t constexpr kDescriptorPhaseOne = 1;
    std::uint32_t constexpr kDescriptorPhaseTwo = 2;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SK build spec, "Mechanics" and "Tuning starting points")
    // ----------------------------------------------------------------------------------------------------------------

    // FN1 Arugal's Lightning: a 3 yd circle on a room-edge point, 2 s warning, 20% Nature + Weakened; first at 10 s,
    // then every 20 s (the knob, Dungeon ruling 9). Phase one only.
    inline constexpr Ms kLightningFirst{ 10000 };
    inline constexpr Ms kLightningEvery{ 20000 };
    inline constexpr Ms kLightningWarn{ 2000 };
    float constexpr kLightningRadius = 3.f;
    inline constexpr NH<float> kLightningPct{ 20.f, 20.f };

    // FN3 Void Pulse: a 1.5 s cast (DBC), then a 1.5 s pause: a pulse every 3 s. 4% Shadow to every player; heroic
    // Rising Pulse adds 1% per landed pulse, up to 10% (an interrupted pulse does not count).
    inline constexpr Ms kVoidPulseFirst{ 1500 };            // after the voidwalker steps out
    inline constexpr Ms kVoidPulseCast{ 1500 };
    inline constexpr Ms kVoidPulsePause{ 1500 };
    inline constexpr Ms kVoidPulseEvery = kVoidPulseCast + kVoidPulsePause;
    inline constexpr Ms kVoidPulseRetry{ 250 };             // stunned, silenced or locked out: try again
    float constexpr kVoidPulseBasePct = 4.f;
    inline constexpr NH<float> kRisingPulseStepPct{ 0.f, 1.f };
    float constexpr kRisingPulseCapPct = 10.f;

    // FN4 Toxic Saliva (stock 7125): a random player within 5 yd, 1-7 s, then every 22-45 s.
    inline constexpr Ms kSalivaFirstMin{ 1000 };
    inline constexpr Ms kSalivaFirstMax{ 7000 };
    inline constexpr Ms kSalivaEveryMin{ 22000 };
    inline constexpr Ms kSalivaEveryMax{ 45000 };
    inline constexpr Ms kSalivaRetry{ 1000 };
    float constexpr kSalivaRange = 5.f;

    // FN5 Shadow Fenrus (heroic): one second still at 1 health, then he rises with 40% of his health.
    inline constexpr Ms kStillness{ 1000 };
    std::uint32_t constexpr kPhaseTwoHealthPct = 40;

    // FN6 Shadow Leap (heroic): 5 s into phase two, then every 10 s; 2 s crouch; 25% Shadow in 6 yd of the landing;
    // the others stay within 12 yd of him (the Bait's othersRange).
    inline constexpr Ms kLeapFirst{ 5000 };
    inline constexpr Ms kLeapEvery{ 10000 };
    inline constexpr Ms kLeapWarn{ 2000 };
    float constexpr kLeapRadius = 6.f;
    float constexpr kLeapOthersRange = 12.f;
    inline constexpr NH<float> kLeapPct{ 25.f, 25.f };
    float constexpr kLeapJumpSpeedXY = 30.f;
    float constexpr kLeapJumpMinSpeedZ = 6.f;

    // FN7 Shadow Scar: +200% Shadow Leap damage taken per stack, for the rest of the fight.
    float constexpr kScarBonusPerStack = 2.f;
    std::uint32_t constexpr kScarMaxStacks = 99;            // CumulativeAura

    // FN8 Shadow Lightning (heroic): a 3 yd circle under a random player, 1 s warning, 15% Shadow, no Weakened
    // (Dungeon ruling 10); 2 s into phase two, then every 3 s.
    inline constexpr Ms kShadowLightningFirst{ 2000 };
    inline constexpr Ms kShadowLightningEvery{ 3000 };
    inline constexpr Ms kShadowLightningWarn{ 1000 };
    float constexpr kShadowLightningRadius = 3.f;
    inline constexpr NH<float> kShadowLightningPct{ 15.f, 15.f };
    float constexpr kShadowLightningRange = 60.f;
    inline constexpr Ms kStrikeLookLife{ 3000 };            // the strike stalker carrying the FN8 bolt

    // Voidwalkers: summoned at the strike point, corpse gone 5 s after death; they pick the nearest player first.
    inline constexpr Ms kVoidwalkerCorpse{ 5000 };
    float constexpr kVoidwalkerAggroRange = 60.f;

    // The arena guard's landing: inside this radius of the room center (the walls stand 12.5-16.6 yd out).
    float constexpr kGripLandRadius = 11.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Rules
    // ----------------------------------------------------------------------------------------------------------------

    // FN3: a pulse's percent, given the pulses this voidwalker landed before it.
    constexpr float VoidPulsePct(bool heroic, std::uint32_t landedBefore)
    {
        float const pct = kVoidPulseBasePct + kRisingPulseStepPct(heroic) * static_cast<float>(landedBefore);
        return pct < kRisingPulseCapPct ? pct : kRisingPulseCapPct;
    }

    // FN7: the Shadow Leap damage factor for a player with `stacks` Shadow Scars (before this landing's own stack).
    constexpr float ScarFactor(std::uint32_t stacks)
    {
        return 1.f + kScarBonusPerStack * static_cast<float>(stacks);
    }

    // The scaled hit, rounded; never below the base hit.
    inline std::uint32_t ScarredDamage(std::uint32_t base, std::uint32_t stacks)
    {
        double const v = static_cast<double>(base) * static_cast<double>(ScarFactor(stacks));
        return std::max<std::uint32_t>(base, static_cast<std::uint32_t>(v + 0.5));
    }

    // FN5: the fake death applies on heroic, until phase two has begun (handoff s7 #15): no kill, loot or credit.
    constexpr bool InterceptsLethal(bool heroic, Phase phase)
    {
        return heroic && phase != Phase::Two;
    }

    // FN2: a lightning strike brings a voidwalker in phase one only ("the strikes stop bringing new ones").
    constexpr bool StrikeSummons(Phase phase)
    {
        return phase == Phase::One;
    }

    // Toxic Saliva and the melee wait while he lies still.
    constexpr bool MayAct(Phase phase)
    {
        return phase != Phase::Rising;
    }

    // FN5: his health when he rises (40% of the maximum, at least 1).
    constexpr std::uint32_t PhaseTwoHealth(std::uint32_t maxHealth)
    {
        std::uint64_t const v = static_cast<std::uint64_t>(maxHealth) * kPhaseTwoHealthPct / 100;
        return v ? static_cast<std::uint32_t>(v) : 1u;
    }

    // FN1: a random strike point, never the one used last (when there is another). `rand(n)` returns [0, n).
    template <class Rand>
    std::size_t PickStrikeIndex(std::size_t count, std::optional<std::size_t> last, Rand&& rand)
    {
        if (count <= 1)
            return 0;
        if (!last || *last >= count)
            return static_cast<std::size_t>(rand(static_cast<std::uint32_t>(count))) % count;
        std::size_t const pick = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(count - 1))) % (count - 1);
        return pick >= *last ? pick + 1 : pick;
    }

    // The strike point nearest `p` (`.sfktest fenrus lightning`: the one a GM stands by).
    inline std::size_t NearestStrikeIndex(Vec2 p)
    {
        auto const& points = ShadowfangKeepRework::kFenrusStrikePoints;
        std::size_t best = 0;
        for (std::size_t i = 1; i < points.size(); ++i)
            if (DungeonKit::Distance(points[i], p) < DungeonKit::Distance(points[best], p))
                best = i;
        return best;
    }

    // The arena guard's landing for a unit gripped back from `from`: on the line from the room center toward it, at
    // most `maxRadius` from the center (a unit in a doorway lands just inside the room).
    inline Vec2 GripLanding(Vec2 center, Vec2 from, float maxRadius)
    {
        float const d = DungeonKit::Distance(center, from);
        if (d <= maxRadius || d < 0.01f)
            return from;
        float const k = maxRadius / d;
        return { center.x + (from.x - center.x) * k, center.y + (from.y - center.y) * k };
    }

    // Phase one strikes in a fight of `fight` (SK tuning: about 3 in the 62 s normal fight).
    constexpr std::uint32_t StrikesBy(Ms fight)
    {
        if (fight < kLightningFirst)
            return 0;
        return static_cast<std::uint32_t>((fight - kLightningFirst) / kLightningEvery) + 1;
    }

    // One voidwalker's Void Pulse clock (FN3): its own time since it stepped out, the next cast and the landed count
    // that Rising Pulse reads. The AI feeds it; the pulse spell's script reads Pct().
    class PulseClock
    {
    public:
        void Start(Ms now)
        {
            _next = now + kVoidPulseFirst;
            _landed = 0;
        }

        bool Due(Ms now) const { return now >= _next; }

        // The cast landed (the AI's OnSpellCast, after the hits): Rising Pulse counts it, the pause follows.
        void Landed(Ms now)
        {
            ++_landed;
            _next = now + kVoidPulsePause;
        }

        // Interrupted (or failed mid-cast): not counted; the next one follows the pause.
        void Interrupted(Ms now) { _next = now + kVoidPulsePause; }

        // Could not start (stunned, silenced, a school lockout): try again shortly.
        void Blocked(Ms now) { _next = now + kVoidPulseRetry; }

        std::uint32_t LandedCount() const { return _landed; }
        Ms Next() const { return _next; }
        float Pct(bool heroic) const { return VoidPulsePct(heroic, _landed); }

    private:
        Ms _next{ kVoidPulseFirst };
        std::uint32_t _landed = 0;
    };
}

#endif
