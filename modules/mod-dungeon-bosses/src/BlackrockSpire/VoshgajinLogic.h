/*
 * mod-dungeon-bosses, Blackrock Spire B2:
 * Shadow Hunter Vosh'gajin (9236), "Voodoo Dolls": the pure, host-testable part (no engine headers). Build spec SP
 * 964-1021 (docs/dungeons/blackrock-spire-rework.md, rulings 24-28), handoff section 3.4 rows VG and 3.5 row B2.
 * Tested by tests/brs_voshgajin_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsVoshgajin (210060-210089), declared in apps/dbc-tools
 *                  source/npcs/blackrock_spire/voshgajin.py
 *   Tuning         NH<> constants, Cadence and FlexAB pairs: one number per difficulty, straight from the build spec
 *   Torment order  VG6: every binding runs the three torments once each in a random order in three slots (normal
 *                  4 / 10 / 16 s, heroic 3 / 8 / 13 s after the binding); from 50% on heroic the first slot shows
 *                  Needle with Flames or with Squeeze (never Flames with Squeeze) and the second slot the third alone
 *   Binding hold   VG1 / VG2: the Bound aura and the strings last 18 s, but never end before the last torment of the
 *                  binding has landed (the normal third slot lands at 19 s)
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_VOSHGAJIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_VOSHGAJIN_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace BrsVoshgajin
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point4;
    using DungeonKit::NH;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsVoshgajin;

    enum VoshgajinSpells : std::uint32_t
    {
        SPELL_VG_BIND           = kSpellSlice.first + 0,    // 210060 VG1 Puppet Strings (the doll's channel)
        SPELL_VG_BOUND          = kSpellSlice.first + 1,    // 210061 VG2 Bound: the Curse, a pin every 2 s
        SPELL_VG_DOLL_SWELL     = kSpellSlice.first + 2,    // 210062 VG6 the doll's scale aura (x2) through a tell
        SPELL_VG_FLAMES_TELL    = kSpellSlice.first + 3,    // 210063 VG3 the doll catches fire (3 s)
        SPELL_VG_NEEDLE_TELL    = kSpellSlice.first + 4,    // 210064 VG4 a crystal spike rises at the doll (3 s)
        SPELL_VG_SQUEEZE_TELL   = kSpellSlice.first + 5,    // 210065 VG5 a shadow shell closes round the doll (3 s)
        SPELL_VG_FLAMES_HIT     = kSpellSlice.first + 6,    // 210066 VG3 the burst (resolve copy, Fire)
        SPELL_VG_PATCH_HIT      = kSpellSlice.first + 7,    // 210067 VG3 the patch's tick (resolve copy, Fire)
        SPELL_VG_NEEDLE_HIT     = kSpellSlice.first + 8,    // 210068 VG4 the needle (resolve copy, Physical)
        SPELL_VG_SQUEEZE_HIT    = kSpellSlice.first + 9,    // 210069 VG5 the squeeze (resolve copy, Shadow)
        SPELL_VG_HEXED          = kSpellSlice.first + 10,   // 210070 VG5 / VG7 the 2 s hex (the rider)
        SPELL_VG_HEX_OF_AGONY   = kSpellSlice.first + 11,   // 210071 VG7 heroic: the Magic DoT, 8 s
        SPELL_VG_HEX_BURST_HIT  = kSpellSlice.first + 12,   // 210072 VG7 heroic: the expiry burst (resolve copy)
        SPELL_VG_PIN            = kSpellSlice.first + 13,   // 210073 VG2 the pin's look, one per tick (no effect)
        SPELL_VG_NEEDLE_FLIGHT  = kSpellSlice.first + 14,   // 210074 VG4 the needle's flight down the string (look)
        SPELL_VG_HEX_SKULL      = kSpellSlice.first + 15,   // 210075 VG7 the skull re-cast every 3 s (look)
        // 210076-210089 spare
    };
    static_assert(SPELL_VG_HEX_SKULL <= kSpellSlice.last, "Vosh'gajin's spells must stay in her slice");

    // creature_text groups of 9236 (SP "Text"; kTextRanges 0-3 in BlackrockSpireRework.h).
    enum VoshgajinTexts : std::uint8_t
    {
        YELL_VG_PULL    = 0,    // the pull yell
        EMOTE_VG_BIND   = 1,    // "%s binds the doll to $n!" (boss emote, 41)
        YELL_VG_TWIN    = 2,    // heroic, 50%: the twin torments begin
        YELL_VG_DEATH   = 3,
    };

    // Registry tags (the failure ledger and the playtest greps key on them).
    enum VoshgajinTags : std::uint32_t
    {
        TAG_VG_FLAMES       = 1,    // VG3 the burst
        TAG_VG_PATCH        = 2,    // VG3 the patch
        TAG_VG_NEEDLE       = 3,    // VG4
        TAG_VG_SQUEEZE      = 4,    // VG5
        TAG_VG_HEX_BURST    = 5,    // VG7
        TAG_VG_BOUND_HIT    = 6,    // VG3 / VG4 the Bound player's own 10%
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP 964-1021; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // First start and cadence of a beat, in ms since the pull (SP "First, cooldown"). Cadences count start to start.
    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    // VG1 Bind: 8 s, then every 25 s (heroic 20 s); one Bound player and doll at 5 players, two at 6 or more.
    inline constexpr std::uint32_t kBindFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kBindEveryMs{ 25000, 20000 };
    inline constexpr FlexAB kBindCount{ 1, 2 };

    // VG2 Bound: the Curse, 18 s, a pin every 2 s for 5% of the non-tank row (a Curse dispel stops the pins, the
    // strings stay).
    inline constexpr std::uint32_t kBoundMs = 18000;
    inline constexpr std::uint32_t kBoundTailMs = 500;      // the hold ends this long after the last torment lands
    inline constexpr std::uint32_t kPinEveryMs = 2000;
    inline constexpr float kPinPct = 5.f;

    // VG6: the torment slots, ms after the binding: a tell starts (3 s on the doll), the hit lands kTellMs later.
    inline constexpr std::uint32_t kTellMs = 3000;
    inline constexpr std::array<std::uint32_t, 3> kSlotsNormal{ 4000, 10000, 16000 };
    inline constexpr std::array<std::uint32_t, 3> kSlotsHeroic{ 3000, 8000, 13000 };
    inline constexpr float kTwinFromHealthPct = 50.f;       // heroic: the twin torments from 50% health

    // VG3 Voodoo Flames: an 8 yd burst round the Bound player, others 30% (heroic 35%) Fire + Weakened, the Bound
    // player 10%; then a 5 yd patch for 20 s, 10% a second, one Weakened per player per patch.
    inline constexpr float kFlamesRadius = 8.f;
    inline constexpr NH<float> kFlamesPct{ 30.f, 35.f };
    inline constexpr float kFlamesBoundPct = 10.f;
    inline constexpr float kPatchRadius = 5.f;
    inline constexpr std::uint32_t kPatchMs = 20000;
    inline constexpr std::uint32_t kPatchTickMs = 1000;
    inline constexpr float kPatchPct = 10.f;

    // VG4 Needle: a 4 yd line from the doll to the Bound player, others 40% (heroic 50%) Physical, no Weakened (its
    // own penalty), the Bound player 10% (and never on the line: the zero-stack eligibility on kNeedleSkipAura).
    // The skip keys on Puppet Strings, which stays for the whole binding (not dispellable): Bound is a Curse the group
    // is meant to dispel, and a cured player still stands at the line's far end (R-1-A M2).
    inline constexpr std::uint32_t kNeedleSkipAura = SPELL_VG_BIND;
    inline constexpr float kNeedleWidth = 4.f;
    inline constexpr NH<float> kNeedlePct{ 40.f, 50.f };
    inline constexpr float kNeedleBoundPct = 10.f;

    // VG5 Squeeze: a donut 5 to 25 yd round the Bound player, 25% (heroic 30%) Shadow + Weakened + a 2 s hex.
    inline constexpr float kSqueezeInner = 5.f;
    inline constexpr float kSqueezeOuter = 25.f;
    inline constexpr NH<float> kSqueezePct{ 25.f, 30.f };
    inline constexpr std::uint32_t kHexedMs = 2000;

    // VG7 Hex of Agony (heroic): 15 s, then every 20 s, 1 random non-tank (2 at 6 or more) carries it 8 s: 4% a
    // second Shadow, a Magic dispel; expired, it bursts 8 yd (40% Shadow + the 2 s hex, the carrier spared).
    inline constexpr Cadence kHexOfAgony{ 15000, 20000 };
    inline constexpr FlexAB kHexOfAgonyCount{ 1, 2 };
    inline constexpr std::uint32_t kHexOfAgonyMs = 8000;
    inline constexpr float kHexOfAgonyPct = 4.f;
    inline constexpr float kHexBurstRadius = 8.f;
    inline constexpr float kHexBurstPct = 40.f;
    inline constexpr std::uint32_t kHexSkullEveryMs = 3000;     // the skull look is a 3 s impact: re-cast over the 8 s
    inline constexpr std::uint32_t kHexDispelledBeforeMs = 400; // an aura gone this long before its end was dispelled

    // The Voodoo Doll 300703 (display 25017, scale 1; the swell aura x2 through a tell): doll 1 and, at 6 or more
    // players, doll 2, on the dais (SP ruling 26).
    inline constexpr std::array<Point4, 2> kDollSpots{ {
        { -124.30f, -483.93f, 25.55f, 0.f },
        { -124.50f, -480.05f, 25.62f, 0.f },
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // VG6 The torment order
    // ----------------------------------------------------------------------------------------------------------------

    enum class Torment : std::uint8_t
    {
        Flames,     // VG3
        Needle,     // VG4
        Squeeze,    // VG5
    };

    inline constexpr char const* TormentName(Torment t)
    {
        return t == Torment::Flames ? "flames" : (t == Torment::Needle ? "needle" : "squeeze");
    }

    // One slot: the tell(s) start at `atMs` after the binding, the hits land kTellMs later. A pair shows two tells on
    // the doll at once.
    struct Step
    {
        std::uint32_t atMs = 0;
        std::array<Torment, 2> torments{ Torment::Flames, Torment::Flames };
        std::uint8_t count = 0;

        constexpr bool Has(Torment t) const
        {
            for (std::uint8_t i = 0; i < count; ++i)
                if (torments[i] == t)
                    return true;
            return false;
        }
    };

    struct Schedule
    {
        std::array<Step, 3> steps{};
        std::uint8_t count = 0;
    };

    // The six orders of the three torments.
    inline constexpr std::size_t kOrderCount = 6;
    inline constexpr std::array<std::array<Torment, 3>, kOrderCount> kOrders{ {
        { Torment::Flames, Torment::Needle, Torment::Squeeze },
        { Torment::Flames, Torment::Squeeze, Torment::Needle },
        { Torment::Needle, Torment::Flames, Torment::Squeeze },
        { Torment::Needle, Torment::Squeeze, Torment::Flames },
        { Torment::Squeeze, Torment::Flames, Torment::Needle },
        { Torment::Squeeze, Torment::Needle, Torment::Flames },
    } };

    inline constexpr std::array<std::uint32_t, 3> const& Slots(bool heroic)
    {
        return heroic ? kSlotsHeroic : kSlotsNormal;
    }

    // Twin torments: heroic and at 50% health or less.
    inline constexpr bool TwinOn(bool heroic, float healthPct)
    {
        return heroic && healthPct <= kTwinFromHealthPct;
    }

    // `orderRoll` picks one of the six orders (taken modulo 6); `pairRoll` (twin only, modulo 2) picks the torment
    // that pairs with the Needle: 0 Flames, 1 Squeeze. A twin binding has two steps: the Needle with its mate at the
    // first slot, the third alone at the second slot (SP "two slots").
    inline Schedule BuildSchedule(bool heroic, bool twin, std::uint32_t orderRoll, std::uint32_t pairRoll)
    {
        Schedule out;
        std::array<std::uint32_t, 3> const& slots = Slots(heroic);
        if (!twin)
        {
            std::array<Torment, 3> const& order = kOrders[orderRoll % kOrderCount];
            for (std::size_t i = 0; i < 3; ++i)
            {
                out.steps[i].atMs = slots[i];
                out.steps[i].torments[0] = order[i];
                out.steps[i].count = 1;
            }
            out.count = 3;
            return out;
        }
        Torment const mate = (pairRoll % 2) == 0 ? Torment::Flames : Torment::Squeeze;
        Torment const alone = mate == Torment::Flames ? Torment::Squeeze : Torment::Flames;
        out.steps[0].atMs = slots[0];
        out.steps[0].torments = { Torment::Needle, mate };
        out.steps[0].count = 2;
        out.steps[1].atMs = slots[1];
        out.steps[1].torments[0] = alone;
        out.steps[1].count = 1;
        out.count = 2;
        return out;
    }

    // The ms after the binding when its last torment has landed.
    inline std::uint32_t LastLandsMs(Schedule const& schedule)
    {
        std::uint32_t last = 0;
        for (std::uint8_t i = 0; i < schedule.count; ++i)
            last = std::max(last, schedule.steps[i].atMs + kTellMs);
        return last;
    }

    // How long the Bound aura and the strings stay: 18 s, or until just past the last torment's landing when that is
    // later (the normal third slot lands at 19 s; a torment must not meet a player whose Bound has fallen off).
    inline std::uint32_t BindHoldMs(Schedule const& schedule)
    {
        return std::max(kBoundMs, LastLandsMs(schedule) + kBoundTailMs);
    }

    // The next binding's start from the planned one: the cadence counts start to start, never before `nowMs`.
    inline std::uint64_t NextBindMs(std::uint64_t plannedMs, bool heroic, std::uint64_t nowMs)
    {
        std::uint64_t const next = plannedMs + kBindEveryMs(heroic);
        return std::max<std::uint64_t>(next, nowMs + 1);
    }

    // A binding must be over before the next one starts (the strings never overlap two bindings on one doll).
    inline bool BindingFitsCadence(bool heroic, bool twin)
    {
        return BindHoldMs(BuildSchedule(heroic, twin, 0, 0)) < kBindEveryMs(heroic);
    }
}

#endif
