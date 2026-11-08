/*
 * mod-dungeon-bosses, Shadowfang Keep: Baron Silverlaine (WP-S3), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, the echo clock, target and point picks. Build spec: SK 578-621 (build
 * spec), SK 483-577 (design), BS1-BS7; handoff section 3.5 rows BS, section 3.6 row S3.
 *
 * User ruling (handoff section 10, section 7 #21): the echoes come on timers, not at 75 / 50 / 25% health: the first
 * at 15 s, then one every 25 s, in kill order. Kill order is not recorded by the instance (it keeps boss states only),
 * so it is the build spec's: Rethilgore, Razorclaw, Odo, then round again. The heroic 10% Night Ends stays a health
 * threshold (a one-off transition).
 *
 * The echoes reuse the other bosses' mechanics (handoff section 3.3 item 3), never copies of them:
 *   - Echo of Rethilgore: SoulDrain.h (S1) and Rethilgore's spells 205913-205917;
 *   - Echo of Razorclaw: MeatHook.h (S2) with Razorclaw::HookFor(false) and the shared 205930-205932;
 *   - Echo of Odo: Hunt.h (S5) with SfkHunt::kEchoHunt, Odo's howl 205990, Hunted 205991 and catch 205992, plus this
 *     slice's own lighter Maul (spell_sfk_hunt_maul).
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum
 * (apps/dbc-tools source/npcs/shadowfang_keep/baron_silverlaine.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the same on both difficulties:
 * the reference row (normal 1,300 / heroic 4,120) makes the difference. Tested by tests/sfk_silverlaine_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_SILVERLAINE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_SILVERLAINE_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "HuntLogic.h"
#include "RazorclawLogic.h"
#include "RethilgoreLogic.h"
#include "ShadowfangKeepRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace Silverlaine
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsSilverlaine;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/baron_silverlaine.py. Visual ids from WP-V's _visuals.py
    // (copied, the stock spells are never cast).
    enum SilverlaineSpells : std::uint32_t
    {
        SPELL_ACCURSED_VEIL         = 205945,   // BS6: the 1.5 s interruptible cast and the curse it applies (Curse,
                                                // 12 s, 3% Shadow per 2 s via spell_sfk_silverlaine_accursed_veil,
                                                // healing received -50%; Veil of Shadow's SV 561)
        SPELL_ACCURSED_VEIL_SPREAD  = 205946,   // BS6: the pulse Spread's resolve copy (Shadow, no damage: catching
                                                // the curse is the penalty)
        SPELL_ECHO_MAUL             = 205947,   // BS5: the Echo of Odo's Maul, 1.5 s stun + 20% bleed over 1.5 s
                                                // (spell_sfk_hunt_maul, S5's generic script)
        SPELL_SPECTRAL_ECHO         = 205948,   // BS1: the echoes' spectral look (Ghost Visual 9617's SV 886), aura
        SPELL_ECHO_ARRIVAL          = 205949,   // BS1: the burst into the hall (Spirit Particles SV 4490), visual
        // 205950-205964 spare
    };
    static_assert(kSlice.Contains(SPELL_ACCURSED_VEIL) && kSlice.Contains(SPELL_ECHO_ARRIVAL),
        "Silverlaine's spells stay inside his slice");

    // Registry tags (ledger and failure listing): the build spec's mechanic numbers.
    inline constexpr std::uint32_t kTagEchoFragment = 3;    // BS3
    inline constexpr std::uint32_t kTagEchoHook = 4;        // BS4
    inline constexpr std::uint32_t kTagEchoHunt = 5;        // BS5
    inline constexpr std::uint32_t kTagAccursedVeil = 6;    // BS6

    // Each echo's own text (creature_text group 0 on 300503 / 300504 / 300505, a boss emote naming the player).
    inline constexpr std::uint8_t EMOTE_ECHO_MOVE = 0;

    // ----------------------------------------------------------------------------------------------------------------
    // The echoes (BS1-BS5, BS7)
    // ----------------------------------------------------------------------------------------------------------------

    enum class EchoKind : std::uint8_t
    {
        Rethilgore = 0,
        Razorclaw = 1,
        Odo = 2,
    };
    inline constexpr std::size_t kEchoKinds = 3;

    // The build spec's kill order (the instance does not record the group's).
    inline constexpr std::array<EchoKind, kEchoKinds> kKillOrder{ { EchoKind::Rethilgore, EchoKind::Razorclaw,
        EchoKind::Odo } };

    constexpr std::uint8_t Bit(EchoKind kind)
    {
        return static_cast<std::uint8_t>(1u << static_cast<std::uint8_t>(kind));
    }

    constexpr std::uint32_t EchoEntry(EchoKind kind)
    {
        using namespace ShadowfangKeepRework;
        return kind == EchoKind::Rethilgore ? std::uint32_t(NPC_SFK_ECHO_OF_RETHILGORE)
            : kind == EchoKind::Razorclaw ? std::uint32_t(NPC_SFK_ECHO_OF_RAZORCLAW)
            : std::uint32_t(NPC_SFK_ECHO_OF_ODO);
    }

    constexpr std::optional<EchoKind> KindOfEntry(std::uint32_t entry)
    {
        using namespace ShadowfangKeepRework;
        if (entry == NPC_SFK_ECHO_OF_RETHILGORE)
            return EchoKind::Rethilgore;
        if (entry == NPC_SFK_ECHO_OF_RAZORCLAW)
            return EchoKind::Razorclaw;
        if (entry == NPC_SFK_ECHO_OF_ODO)
            return EchoKind::Odo;
        return std::nullopt;
    }

    // Silverlaine's yell naming the echo (SK "Text" lines 1-3).
    constexpr std::uint8_t EchoYell(EchoKind kind)
    {
        using namespace ShadowfangKeepRework;
        return kind == EchoKind::Rethilgore ? std::uint8_t(YELL_SILVERLAINE_ECHO_RETHILGORE)
            : kind == EchoKind::Razorclaw ? std::uint8_t(YELL_SILVERLAINE_ECHO_RAZORCLAW)
            : std::uint8_t(YELL_SILVERLAINE_ECHO_ODO);
    }

    constexpr char const* EchoName(EchoKind kind)
    {
        return kind == EchoKind::Rethilgore ? "rethilgore" : kind == EchoKind::Razorclaw ? "razorclaw" : "odo";
    }

    // BS1 timing (user ruling: timers). Normal: one echo alive at most, a due echo waits for the live one; each fades
    // after 12 s. Heroic (Lingering Echoes): echoes never fade and several live together; a due echo whose kind is
    // still alive gives its turn to the next kind not alive, and all three alive wait.
    inline constexpr std::uint32_t kEchoFirstMs = 15000;
    inline constexpr std::uint32_t kEchoEveryMs = 25000;
    inline constexpr NH<std::uint32_t> kEchoLifeMs{ 12000, 0 };        // 0: until killed
    inline constexpr NH<bool> kEchoesTogether{ false, true };
    // Health (normal: HealthModifier 2.4793 on the level 20 warrior base 484 = 1,200; heroic: WP-H's 20,000 override).
    inline constexpr NH<std::uint32_t> kEchoHealth{ 1200, 20000 };
    inline constexpr float kEchoHealthModifier = 2.4793f;
    inline constexpr std::uint32_t kWarriorBaseHealthL20 = 484;

    // BS7 The Night Ends (heroic): at 10%, every echo not alive returns at once (once per pull).
    inline constexpr NH<bool> kNightEnds{ false, true };
    inline constexpr float kNightEndsPct = 10.f;

    // The echo clock: which echo is due, given the kinds alive now (a mask of Bit(kind)).
    class EchoClock
    {
    public:
        void Start()
        {
            _untilMs = kEchoFirstMs;
            _next = 0;
        }

        // The echo to summon now (then call Summoned), or nullopt (not due yet, or due and waiting).
        std::optional<EchoKind> Update(std::uint32_t diff, std::uint8_t aliveMask, bool heroic)
        {
            _untilMs = diff >= _untilMs ? 0 : _untilMs - diff;
            if (_untilMs)
                return std::nullopt;
            return Due(aliveMask, heroic);
        }

        // The echo that would come now if the clock were due.
        std::optional<EchoKind> Due(std::uint8_t aliveMask, bool heroic) const
        {
            if (!kEchoesTogether(heroic))
                return aliveMask ? std::nullopt : std::optional<EchoKind>(kKillOrder[_next]);
            for (std::size_t i = 0; i < kEchoKinds; ++i)
            {
                EchoKind const kind = kKillOrder[(_next + i) % kEchoKinds];
                if (!(aliveMask & Bit(kind)))
                    return kind;
            }
            return std::nullopt;
        }

        // `kind` came: the next turn is the kind after it in kill order, kEchoEveryMs from now.
        void Summoned(EchoKind kind)
        {
            for (std::size_t i = 0; i < kEchoKinds; ++i)
                if (kKillOrder[i] == kind)
                    _next = (i + 1) % kEchoKinds;
            _untilMs = kEchoEveryMs;
        }

        std::uint32_t UntilMs() const { return _untilMs; }
        EchoKind NextKind() const { return kKillOrder[_next]; }

    private:
        std::uint32_t _untilMs = kEchoFirstMs;
        std::size_t _next = 0;
    };

    // BS7: the echoes The Night Ends brings back (every kind not alive, in kill order).
    inline std::vector<EchoKind> NightEndsReturns(std::uint8_t aliveMask)
    {
        std::vector<EchoKind> out;
        for (EchoKind const kind : kKillOrder)
            if (!(aliveMask & Bit(kind)))
                out.push_back(kind);
        return out;
    }

    // BS7 fires on the hit that takes him to kNightEndsPct or below, once, on heroic only.
    constexpr bool NightEndsDue(bool heroic, bool alreadyFired, float pctAfter)
    {
        return kNightEnds(heroic) && !alreadyFired && pctAfter <= kNightEndsPct;
    }

    // A normal echo fades once its life is up and its current move is done (a hook line in flight lands first); a
    // heroic echo (life 0) never fades.
    constexpr bool EchoFades(std::uint32_t ageMs, std::uint32_t lifeMs, bool busy)
    {
        return lifeMs && ageMs >= lifeMs && !busy;
    }

    // Where each echo bursts into the hall (the report's map: u right, v up from Silverlaine, keep grid): the hall's
    // near half, clear of the alcove and 3+ yd from the table holes, 16-28 yd from him.
    inline Vec2 EchoSpawn(EchoKind kind)
    {
        using namespace ShadowfangKeepRework;
        switch (kind)
        {
            case EchoKind::Rethilgore:
                return ReportPoint(kSilverlaineSpawn.XY(), kKeepUp, -5.f, 16.f);
            case EchoKind::Razorclaw:
                return ReportPoint(kSilverlaineSpawn.XY(), kKeepUp, 5.f, 18.f);
            default:
                return ReportPoint(kSilverlaineSpawn.XY(), kKeepUp, 0.f, 28.f);
        }
    }

    // ---- BS2 / BS3 Echo of Rethilgore -------------------------------------------------------------------------------

    // The drain (Rethilgore's channel and 5% tick, SoulDrain.h) every 2 s on a random non-tank; one fragment per tick,
    // at most six per echo (SK: "capped at 18% per echo, a growing problem, never an uncapped one"). The drain itself
    // lasts 12 s, six ticks, on both difficulties (user ruling 2026-11-07, designer question 4): the normal echo's
    // whole life, and on heroic, where the echo lives until killed, it then only melees.
    inline constexpr std::uint32_t kEchoDrainTickMs = 2000;
    inline constexpr std::uint32_t kEchoDrainTicks = 6;
    inline constexpr std::uint32_t kEchoFragmentsPerEcho = 6;
    inline constexpr std::uint32_t kEchoFragmentLifeMs = 6000;
    inline constexpr float kEchoFragmentRadius = 1.5f;
    inline constexpr float kEchoFragmentHealPct = Rethilgore::kFragmentHealPct;    // a catch: the drained player, 5%
    inline constexpr float kEchoFeastPct = 3.f;                 // a miss: Silverlaine, 3% of his max health
    inline constexpr float kEchoFragmentRingYd = 4.5f;          // RG5's 3 to 6 yd, around the drained player
    inline constexpr std::size_t kEchoFragmentBearings = 8;
    inline constexpr float kEchoFragmentMinGap = Rethilgore::kFragmentMinGap;
    inline constexpr float kEchoPickRange = 40.f;

    // Another drain tick comes after `ticksSoFar` (the 12 s cap, both difficulties).
    constexpr bool EchoDrainGoesOn(std::uint32_t ticksSoFar)
    {
        return ticksSoFar < kEchoDrainTicks;
    }

    // A fragment comes with this tick (1 = the first) while the echo has spawned fewer than the cap.
    constexpr bool EchoFragmentOnTick(std::uint32_t fragmentsSoFar)
    {
        return fragmentsSoFar < kEchoFragmentsPerEcho;
    }

    // The most one echo can heal him: every fragment missed.
    constexpr float EchoFeastCapPct()
    {
        return kEchoFeastPct * static_cast<float>(kEchoFragmentsPerEcho);
    }

    // The fragment points around the drained player at `center` (height `z`): kEchoFragmentBearings points on a
    // kEchoFragmentRingYd ring, those inside `arena` only. Pick a free one with Rethilgore::PickFreePoint.
    inline std::vector<Vec2> EchoFragmentPoints(Vec2 center, float z, DungeonKit::Arena const& arena)
    {
        std::vector<Vec2> out;
        for (std::size_t i = 0; i < kEchoFragmentBearings; ++i)
        {
            float const bearing = DungeonKit::kPi * 2.f * static_cast<float>(i)
                / static_cast<float>(kEchoFragmentBearings);
            Vec2 const p = DungeonKit::Advance(center, bearing, kEchoFragmentRingYd);
            if (arena.Contains(p, z))
                out.push_back(p);
        }
        return out;
    }

    // ---- BS4 Echo of Razorclaw --------------------------------------------------------------------------------------

    // RC1 with no twin line and no bleed on both difficulties (HookFor(false)), under the echo's own tag. On arrival,
    // then every 5 s while it lives; three at most on normal (its 12 s life), until killed on heroic.
    inline constexpr std::uint32_t kEchoHookEveryMs = 5000;
    inline constexpr std::uint32_t kEchoHookRetryMs = 1000;         // nobody 8+ yd away: try again soon
    inline constexpr NH<std::uint32_t> kEchoHooks{ 3, 0 };          // 0: no cap

    constexpr Razorclaw::HookTuning EchoHook()
    {
        Razorclaw::HookTuning t = Razorclaw::HookFor(false);
        t.tag = kTagEchoHook;
        return t;
    }

    constexpr bool EchoMayHook(bool heroic, std::uint32_t thrown)
    {
        return !kEchoHooks(heroic) || thrown < kEchoHooks(heroic);
    }

    // ---- BS5 Echo of Odo --------------------------------------------------------------------------------------------

    // S5's kEchoHunt (80%, 2 s howl, 8 s, 3 yd). One Hunt per echo on arrival (SK: count 1 / 1, no bells here); the
    // echo then melees until it fades (normal) or dies (heroic).
    inline constexpr SfkHunt::HuntTuning kEchoHunt = SfkHunt::kEchoHunt;
    inline constexpr float kEchoMaulPct = 20.f;                     // over the Maul's 1.5 s, 0.5 s ticks
    inline constexpr std::uint32_t kEchoMaulMs = 1500;
    inline constexpr std::uint32_t kEchoMaulTickMs = 500;
    inline constexpr std::uint32_t kEchoHuntRetryMs = 1000;         // nobody to hunt: try again soon

    // ----------------------------------------------------------------------------------------------------------------
    // BS6 Accursed Veil
    // ----------------------------------------------------------------------------------------------------------------

    // A real 1.5 s cast (interruptible: a kick is the reward) on a random non-tank; the curse lasts 12 s: 3% Shadow of
    // the non-tank row every 2 s, healing received -50%, Curse (removable). Every 2 s it pulses: a fresh 4 yd Spread
    // around every cursed player (handoff section 7 #18), and anyone else inside catches it with their own 12 s, the
    // tank included. First at 6 s, then every 20 s.
    inline constexpr std::uint32_t kVeilFirstMs = 6000;
    inline constexpr std::uint32_t kVeilEveryMs = 20000;
    inline constexpr std::uint32_t kVeilRetryMs = 1000;
    inline constexpr std::uint32_t kVeilCastMs = 1500;
    inline constexpr std::uint32_t kVeilDurationMs = 12000;
    inline constexpr std::uint32_t kVeilTickMs = 2000;
    inline constexpr float kVeilTickPct = 3.f;
    inline constexpr float kVeilHealingTakenPct = -50.f;
    inline constexpr float kVeilSpreadYd = 4.f;
    inline constexpr std::uint32_t kVeilPulseMs = 2000;
    inline constexpr std::uint32_t kVeilWarnMs = 2000;
    inline constexpr float kVeilRange = 40.f;

    // The curse's total over its life (SK: "about 18% over its life").
    constexpr float VeilTotalPct()
    {
        return kVeilTickPct * static_cast<float>(kVeilDurationMs / kVeilTickMs);
    }

    // A pulse hit copies the curse only onto a player who does not carry it yet (a carrier keeps its own 12 s).
    constexpr bool VeilCatches(bool hitIsPlayer, bool alreadyCursed)
    {
        return hitIsPlayer && !alreadyCursed;
    }
}

#endif
