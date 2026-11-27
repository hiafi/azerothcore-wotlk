/*
 * mod-dungeon-bosses, Gnomeregan D2: Viscous Fallout (7079), the pure, host-testable part (no engine headers). The
 * spell ids, the registry tags (shared with BM's gnomeregan-shapes drill), the texts, the tuning (`namespace Tune`,
 * handoff section 3.5 rule 24), the fight's clocks, the pools (PoolSet), the percents, and the DoseField machine's pure
 * half (DoseLedger: the dose arithmetic, the one halving rule, the drain, Leaking and Meltdown thresholds) that the
 * boss and the hard mode (D6Ha, MT17-MT20) share. Build spec: SP 748-801 (VF1-VF9), design SP 585-747, rulings 14-20;
 * handoff section 3.5 row D2, sections 3.6, 3.8 (area C), 3.9 rows 3-4, section 7 #19 A, #36-#38 A, section 10.
 * Tested by tests/gnomer_fallout_test.cpp. Health is GnomereganRework.h Health: never restated here.
 *
 * Damage percents are of the reference health row (90:28 = 1,694 non-tank / 1,707 tank, 90h:60 = 4,120 / 4,110,
 * section 7 #4 A); every hit that can reach the tank uses the tank row on the tank (rule 17).
 *
 * THE HALVING RULE (STAGE-S0 Q10, stated here once for both callers, Half-Life VF9 and the hard mode's plate MT4 /
 * MT18): a halved dose LOSES half, ROUNDED UP, so it KEEPS half rounded down: Halve(d) = d / 2 (integer division).
 * 9 -> 4 (5 shed), 10 -> 5, 1 -> 0, 0 -> 0. Shed(d) = d - Halve(d) is what Half-Life's heal counts.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_VISCOUS_FALLOUT_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_VISCOUS_FALLOUT_LOGIC_H

#include "DungeonKitMath.h"
#include "GnomereganRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <utility>
#include <vector>

namespace GnomerFallout
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsFallout;

    // Declared in apps/dbc-tools source/npcs/gnomeregan/viscous_fallout.py (same ids).
    enum FalloutSpells : std::uint32_t
    {
        SPELL_VF_IRRADIATED         = kSpellSlice.first + 0,    // VF1 the dose: +3% damage and healing done a stack
        SPELL_VF_DOSE_GLOW          = kSpellSlice.first + 1,    // VF1 the bright glow at kGlowAt (hidden look)
        SPELL_VF_SICKNESS           = kSpellSlice.first + 2,    // VF2 the hit on the sick player: resolve copy
        SPELL_VF_SICKNESS_PULSE     = kSpellSlice.first + 3,    // VF2 the 8 yd pulse on allies: resolve copy
        SPELL_VF_SICKNESS_STUN      = kSpellSlice.first + 4,    // VF2 the 2 s stun (the vomit)
        SPELL_VF_TOXIC_VOLLEY       = kSpellSlice.first + 5,    // VF3 the hit: resolve copy (Nature)
        SPELL_VF_VOLLEY_POISON      = kSpellSlice.first + 6,    // VF3 the Poison rider (dispel reward)
        SPELL_VF_FALLOUT_POOL       = kSpellSlice.first + 7,    // VF3-VF7 the pool tick: resolve copy
        SPELL_VF_SLOUGH             = kSpellSlice.first + 8,    // VF4 the swell (a look on him)
        SPELL_VF_SATURATED          = kSpellSlice.first + 9,    // VF5 on him while he stands in an armed pool
        SPELL_VF_OOZE_LOB           = kSpellSlice.first + 10,   // VF6 the lobbed glob (a missile look)
        SPELL_VF_CORROSIVE_OOZE     = kSpellSlice.first + 11,   // VF6 the hit: resolve copy
        SPELL_VF_HALF_LIFE          = kSpellSlice.first + 12,   // VF9 the 3 s bar (not interruptible)
        SPELL_VF_HALF_LIFE_HEAL     = kSpellSlice.first + 13,   // VF9 his heal (script base point)
        SPELL_VF_MELTDOWN           = kSpellSlice.first + 14,   // VF8 the tick: resolve copy
        SPELL_VF_MELTDOWN_AURA      = kSpellSlice.first + 15,   // VF8 the carrier's debuff (the read)
        SPELL_VF_VOLLEY_LOOK        = kSpellSlice.first + 16,   // VF3 the Volley's look on him
        // kSpellSlice.first + 17 .. last: spare
    };
    static_assert(kSpellSlice.Contains(SPELL_VF_IRRADIATED), "Fallout's spells sit in its slice");
    static_assert(kSpellSlice.Contains(SPELL_VF_VOLLEY_LOOK), "Fallout's spells sit in its slice");

    // Stock, kept: his Frost immunity (Immunity: Frost, his stock addon aura; the stock -232 set went to 1972).
    std::uint32_t constexpr SPELL_FROST_IMMUNITY = 7940;

    // WP-V's picks (_visuals.py; the DT test pins them): the geiger click (VF_CLICK, SoundEntries, stock) and the pool
    // disc (VF_POOL_DISC = DISPLAY_NATURE_DISC on the pool stalker 301130, scale = radius / DISC_QUAD_RADIUS).
    std::uint32_t constexpr kSoundGeiger = 11757;
    std::uint32_t constexpr kDisplayPoolDisc = 90850;
    float constexpr kDiscQuadRadius = 4.8f;

    // Registry tags: the build spec's VF numbers in BM's Gnomeregan drill block (MechanicDrill.h kGnTag*, Fallout
    // 20-39; LESSONS A.3 #4: the drill and the live code keep one table, diffed by the host test and at WP close).
    enum FalloutTags : std::uint32_t
    {
        TAG_VF_SLOUGH           = 20,   // VF4 / VF6: the lasting pools (Slough, the glob's)
        TAG_VF_SATURATED        = 21,   // VF5: judged by the script, no shape (the drill's OffSpot on the tank)
        TAG_VF_VOLLEY_POOL      = 22,   // VF3: the 4 yd pool under every player
        TAG_VF_OOZE             = 23,   // VF6: the 5 yd glob
        TAG_VF_LEAKING          = 24,   // VF7 heroic: the Leaking pools
        TAG_VF_MELTDOWN         = 25,   // VF8 heroic: the 6 yd lasting spread of a 20+ carrier
        TAG_VF_HALF_LIFE        = 26,   // VF9 heroic: the 10 yd Stack for kHalfLifeBotStacks and up
        TAG_VF_HALF_LIFE_OUT    = 27,   // VF9 heroic: the keep-out for the rest
        TAG_VF_SICKNESS         = 30,   // VF2: the script's hits (RegistryHit), not drilled
        TAG_VF_VOLLEY           = 31,   // VF3: the Volley's hits (RegistryHit), not drilled
        TAG_VF_POOL_TICK        = 32,   // VF3-VF7: the pool ticks (RegistryHit), not drilled
    };
    // The drilled tags (MechanicDrill.h kGnTagSlough .. kGnTagHalfLifeOut): the host test pins them.
    inline constexpr std::array<std::uint32_t, 8> kDrillTags{ { TAG_VF_SLOUGH, TAG_VF_SATURATED, TAG_VF_VOLLEY_POOL,
        TAG_VF_OOZE, TAG_VF_LEAKING, TAG_VF_MELTDOWN, TAG_VF_HALF_LIFE, TAG_VF_HALF_LIFE_OUT } };

    // Texts (creature_text 7079, all new: he has no stock text; groups as SP prints them, rule 35). Emotes (type 41).
    enum FalloutTexts : std::uint8_t
    {
        EMOTE_SLOUGH    = 0,    // "%s sloughs off a pool of fallout!"
        EMOTE_SICKNESS  = 1,    // "$n is overcome by Radiation Sickness!"
        EMOTE_HALF_LIFE = 2,    // "%s begins to decay. Stand close to shed your dose!" (heroic)
        EMOTE_LEAKING   = 3,    // "$n is leaking fallout!" (heroic, once per player per pull)
        EMOTE_MELTDOWN  = 4,    // "$n is melting down!" (heroic, once per player per pull)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 748-801 and "Tuning starting points"; section 7 #37 A: the guesses as written, #38 A (b),
    // (c); section 3.5 rule 24: every percent here, timers against the 1.5 s warning floor)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // VF1 the dose: 3% damage and healing done a stack (the aura's base points, Irradiated 214340).
        std::uint32_t constexpr kDosePctPerStack = 3;
        // The client stack counter caps at 255 (rule 25): the aura shows at most this; the count itself goes on.
        std::uint32_t constexpr kAuraStackLimit = 255;
        // Normal: Radiation Sickness at 10 (ruling 15), heroic no cap (ruling 18).
        inline constexpr NH<std::uint32_t> kSicknessAt{ 10, 0 };
        // Normal: out of every armed pool, 1 dose per 3 s; heroic never drains.
        inline constexpr NH<std::uint32_t> kDrainEveryMs{ 3000, 0 };
        // Heroic: Leaking at 10 (a 4 yd pool every 10 s), Meltdown at 20 (ruling 15).
        inline constexpr NH<std::uint32_t> kLeakAt{ 0, 10 };
        std::uint32_t constexpr kLeakEveryMs = 10000;
        inline constexpr NH<std::uint32_t> kMeltdownAt{ 0, 20 };
        // The bright glow (the dose look's second tier): normal near the cliff, heroic at Leaking.
        inline constexpr NH<std::uint32_t> kGlowAt{ 7, 10 };
        // The geiger click speeds up with the dose: every kGeigerSlowMs at 1 dose, kGeigerStepMs faster a dose, never
        // faster than kGeigerFastMs.
        std::uint32_t constexpr kGeigerSlowMs = 3000;
        std::uint32_t constexpr kGeigerStepMs = 250;
        std::uint32_t constexpr kGeigerFastMs = 500;
        // The machine's poll and the aura reassert (rule 25: every 1 s and on every change).
        std::uint32_t constexpr kPollMs = 250;
        std::uint32_t constexpr kReassertMs = 1000;

        // VF2 Radiation Sickness (normal): 40% plus Weakened, 20% to allies within 8 yd, a 2 s stun, dose to 0.
        float constexpr kSicknessPct = 40.f;
        float constexpr kSicknessPulsePct = 20.f;
        float constexpr kSicknessPulseYd = 8.f;
        std::uint32_t constexpr kSicknessStunMs = 2000;

        // VF3 Toxic Volley and VF4 Slough share one beat (ruling 17): every 15 s normal, 12 s heroic, from the same.
        inline constexpr NH<std::uint32_t> kBeatFirstMs{ 15000, 12000 };
        inline constexpr NH<std::uint32_t> kBeatEveryMs{ 15000, 12000 };
        float constexpr kVolleyPct = 10.f;
        float constexpr kVolleyPctPerDoseH = 3.f;       // heroic: +3% per dose carried, no cap (ruling 18)
        std::int32_t constexpr kVolleyDose = 2;
        float constexpr kVolleyRangeYd = 45.f;          // the stock Toxic Volley's reach
        float constexpr kVolleyPoolYd = 4.f;
        std::uint32_t constexpr kVolleyPoolArmMs = 1500;
        inline constexpr NH<std::uint32_t> kVolleyPoolLifeMs{ 20000, 30000 };
        // The Poison rider (a dispel reward, Poison): 1.00% of the reference row every 3 s for 15 s (unruled: the
        // stock 5 per 3 s scaled to the stock hit's share; a named switch, rule 24).
        std::uint32_t constexpr kVolleyPoisonHundredths = 100;
        std::uint32_t constexpr kVolleyPoisonTickMs = 3000;
        std::uint32_t constexpr kVolleyPoisonMs = 15000;

        // VF4 Slough: a 2 s swell (the pool's warning), 7 yd, the fight; heroic grows 1 yd per 10 s, no cap (ruling
        // 19).
        float constexpr kSloughYd = 7.f;
        std::uint32_t constexpr kSloughSwellMs = 2000;
        float constexpr kSloughGrowYdH = 1.f;
        std::uint32_t constexpr kSloughGrowEveryMsH = 10000;
        std::uint32_t constexpr kSloughGrowWarnMs = 1000;   // a grown ring's own warning; the old one ticks till then

        // Every armed pool: 8% a second and 1 dose a second (all pools, however many overlap).
        float constexpr kPoolPct = 8.f;
        std::int32_t constexpr kPoolDose = 1;
        std::uint32_t constexpr kPoolTickMs = 1000;
        float constexpr kPoolZBandYd = 4.f;             // a pool counts within this height of its floor

        // VF5 Saturated (section 7 #38 A (b): judged every 0.5 s on armed pools only): +50% damage dealt (his melee by
        // the aura; his script hits by kSaturatedScalesHits), +2 dose on his Volley; heroic 1 dose to everyone per 2 s.
        float constexpr kSaturatedDamagePct = 50.f;
        bool constexpr kSaturatedScalesHits = true;     // designer question: SP "he deals 50% more damage"
        std::int32_t constexpr kSaturatedVolleyDose = 2;
        std::uint32_t constexpr kSaturatedPollMs = 500;
        std::uint32_t constexpr kSaturatedPulseEveryMsH = 2000;
        std::int32_t constexpr kSaturatedPulseDoseH = 1;

        // VF6 Corrosive Ooze: a lobbed glob at a random player (tank included), 2 s, 5 yd; heroic two players.
        std::uint32_t constexpr kOozeFirstMs = 5000;    // (guess, section 7 #37 A)
        std::uint32_t constexpr kOozeEveryMs = 10000;
        std::uint32_t constexpr kOozeWarnMs = 2000;
        float constexpr kOozeYd = 5.f;
        inline constexpr NH<std::uint32_t> kOozeCount{ 1, 2 };
        inline constexpr NH<float> kOozePct{ 40.f, 60.f };
        inline constexpr NH<std::int32_t> kOozeDose{ 3, 5 };
        float constexpr kOozePoolYd = 5.f;
        std::uint32_t constexpr kOozePoolArmMs = 1500;
        std::uint32_t constexpr kOozePoolLifeMs = 30000;
        float constexpr kGlobMissileSpeed = 20.f;       // yd/s (the lob spell's Speed): launched to land at the end

        // VF7 Leaking (heroic): a 4 yd pool at the carrier's feet, armed after 1.5 s, for the fight.
        float constexpr kLeakPoolYd = 4.f;
        std::uint32_t constexpr kLeakPoolArmMs = 1500;

        // VF8 Meltdown (heroic): 5% a second to the carrier and to everyone within 6 yd (carriers stack).
        float constexpr kMeltdownPct = 5.f;
        float constexpr kMeltdownYd = 6.f;
        std::uint32_t constexpr kMeltdownTickMs = 1000;
        std::uint32_t constexpr kMeltdownWarnMs = 1500;

        // VF9 Half-Life (heroic): a 3 s bar every 30 s from 30 s, 10 yd; inside at its end loses half (the halving
        // rule above), he heals 0.5% of his maximum health per dose shed (section 7 #38 A (c)).
        std::uint32_t constexpr kHalfLifeFirstMs = 30000;
        std::uint32_t constexpr kHalfLifeEveryMs = 30000;
        std::uint32_t constexpr kHalfLifeCastMs = 3000;
        std::uint32_t constexpr kHalfLifeRetryMs = 1000;    // a refused bar is tried again (rule 15)
        float constexpr kHalfLifeYd = 10.f;
        float constexpr kHalfLifeHealPctPerDose = 0.5f;
        // Bots: the Stack for kHalfLifeBotStacks and up, a keep-out for the rest (section 7 #37 A, the guess 8).
        std::uint8_t constexpr kHalfLifeBotStacks = 8;

        // A shape's height tolerance on the cave floor.
        float constexpr kZToleranceYd = 6.f;
        // A fight-long pool's registry ring and look last this long (the whole fight; Clear ends them first).
        std::uint32_t constexpr kWholeFightMs = 4u * 3600u * 1000u;

        // Section 3.5 rule 24, SYS 4: no hit under a 1.5 s warning.
        static_assert(kVolleyPoolArmMs >= GnomereganRework::kWarningFloorMs, "VF3 pool warning");
        static_assert(kSloughSwellMs >= GnomereganRework::kWarningFloorMs, "VF4 swell");
        static_assert(kOozeWarnMs >= GnomereganRework::kWarningFloorMs, "VF6 glob warning");
        static_assert(kOozePoolArmMs >= GnomereganRework::kWarningFloorMs, "VF6 pool warning");
        static_assert(kLeakPoolArmMs >= GnomereganRework::kWarningFloorMs, "VF7 pool warning");
        static_assert(kMeltdownWarnMs >= GnomereganRework::kWarningFloorMs, "VF8 warning");
        static_assert(kHalfLifeCastMs >= GnomereganRework::kWarningFloorMs, "VF9 bar");
        // RB-29 drill hygiene: a cadence of at least the warning plus 0.5 s.
        static_assert(kOozeEveryMs >= kOozeWarnMs + 500, "VF6 cadence");
        static_assert(kBeatEveryMs.heroic >= kSloughSwellMs + 500, "VF3/VF4 cadence");
        static_assert(kHalfLifeEveryMs >= kHalfLifeCastMs + 500, "VF9 cadence");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The dose arithmetic (VF1; the DoseField machine's pure half, GnomereganMachines.h)
    // ----------------------------------------------------------------------------------------------------------------

    // THE halving rule (see the file header): keeps half rounded down, so it sheds half rounded up.
    constexpr std::uint32_t Halve(std::uint32_t dose)
    {
        return dose / 2;
    }

    constexpr std::uint32_t Shed(std::uint32_t dose)
    {
        return dose - Halve(dose);
    }

    // `dose` + `delta`, floored at 0, at most `cap` when cap > 0.
    constexpr std::uint32_t ApplyDelta(std::uint32_t dose, std::int32_t delta, std::uint32_t cap)
    {
        std::int64_t v = std::int64_t(dose) + delta;
        if (v < 0)
            v = 0;
        if (cap && v > std::int64_t(cap))
            v = cap;
        return static_cast<std::uint32_t>(std::min<std::int64_t>(v, 0xFFFFFFFFll));
    }

    // +1 when `from` -> `to` crosses `at` upward (to >= at > from), -1 downward, 0 otherwise or when `at` is 0 (off).
    constexpr int Crossing(std::uint32_t from, std::uint32_t to, std::uint32_t at)
    {
        if (!at)
            return 0;
        if (from < at && to >= at)
            return 1;
        if (from >= at && to < at)
            return -1;
        return 0;
    }

    // The aura's shown stack count for a dose (0 removes the aura).
    constexpr std::uint32_t ShownStacks(std::uint32_t dose)
    {
        return std::min(dose, Tune::kAuraStackLimit);
    }

    // The geiger click's period for a dose (0: silent).
    constexpr std::uint32_t GeigerEveryMs(std::uint32_t dose)
    {
        if (!dose)
            return 0;
        std::uint64_t const faster = std::uint64_t(Tune::kGeigerStepMs) * (dose - 1);
        if (faster >= Tune::kGeigerSlowMs - Tune::kGeigerFastMs)
            return Tune::kGeigerFastMs;
        return Tune::kGeigerSlowMs - std::uint32_t(faster);
    }

    // The rules a DoseField runs on (the machine's DoseSpec, numbers only).
    struct DoseRules
    {
        std::uint32_t capAt = 0;            // 0: no cap
        std::uint32_t drainEveryMs = 0;     // 0: never drains
        std::uint32_t leakAt = 0;           // 0: no Leaking
        std::uint32_t leakEveryMs = 10000;
        std::uint32_t meltdownAt = 0;       // 0: no Meltdown
    };

    // What one change or one tick of a carrier asks the engine half to do (in its next Update: never inside a
    // registry callback, rule 11).
    struct DoseEvents
    {
        bool cap = false;           // reached capAt: the caller's Sickness, then the dose goes to 0
        int meltdown = 0;           // +1 crossed meltdownAt upward, -1 fell below it
        bool leakEmote = false;     // crossed leakAt upward for the first time this pull
        bool meltdownEmote = false; // crossed meltdownAt upward for the first time this pull
        bool leakDrop = false;      // a Leaking drop is due (every leakEveryMs at leakAt and up)
        bool drained = false;       // lost one to the drain

        bool Any() const { return cap || meltdown || leakEmote || meltdownEmote || leakDrop || drained; }
    };

    // Every carrier's dose and clocks, keyed by the player's raw guid. The engine half (ViscousFalloutMachine.cpp) owns
    // one, applies the aura from it and runs the events.
    class DoseLedger
    {
    public:
        struct Entry
        {
            std::uint32_t dose = 0;
            std::uint32_t drainMs = 0;      // time out of every pool towards the next drain
            std::uint32_t leakMs = 0;       // time at leakAt and up towards the next drop
            bool capPending = false;        // the cap fired; the dose sits at capAt until the engine runs Sickness
            bool leakEmoted = false;        // once per player per pull
            bool meltdownEmoted = false;
        };

        explicit DoseLedger(DoseRules rules = {}) : _rules(rules) { }

        DoseRules const& Rules() const { return _rules; }

        // +delta (or -delta), floored at 0 and capped at capAt. A carrier waiting for its Sickness takes nothing more.
        DoseEvents Add(std::uint64_t player, std::int32_t delta)
        {
            Entry& e = _entries[player];
            if (e.capPending)
                return {};
            DoseEvents const events = Change(e, ApplyDelta(e.dose, delta, _rules.capAt));
            Prune(player);
            return events;
        }

        // A dose set outright (a GM, a reset): reaching capAt fires the cap as an Add would.
        DoseEvents Set(std::uint64_t player, std::uint32_t dose)
        {
            Entry& e = _entries[player];
            e.capPending = false;
            DoseEvents const events = Change(e, _rules.capAt ? std::min(dose, _rules.capAt) : dose);
            Prune(player);
            return events;
        }

        // The halving rule; returns the events and writes the dose shed into `shed`.
        DoseEvents Halve(std::uint64_t player, std::uint32_t& shed)
        {
            shed = 0;
            auto it = _entries.find(player);
            if (it == _entries.end() || it->second.capPending)
                return {};
            shed = GnomerFallout::Shed(it->second.dose);
            DoseEvents const events = Change(it->second, GnomerFallout::Halve(it->second.dose));
            Prune(player);
            return events;
        }

        // One poll of a carrier: `elapsedMs` since the last, `drains` the caller's rule (out of every armed pool).
        DoseEvents Tick(std::uint64_t player, std::uint32_t elapsedMs, bool drains)
        {
            auto it = _entries.find(player);
            if (it == _entries.end() || it->second.capPending)
                return {};
            Entry& e = it->second;
            DoseEvents events;
            if (_rules.drainEveryMs && e.dose && drains)
            {
                e.drainMs += elapsedMs;
                if (e.drainMs >= _rules.drainEveryMs)
                {
                    e.drainMs -= _rules.drainEveryMs;
                    events = Change(e, e.dose - 1);
                    events.drained = true;
                }
            }
            else
                e.drainMs = 0;
            if (_rules.leakAt && _rules.leakEveryMs && e.dose >= _rules.leakAt)
            {
                e.leakMs += elapsedMs;
                if (e.leakMs >= _rules.leakEveryMs)
                {
                    e.leakMs -= _rules.leakEveryMs;
                    events.leakDrop = true;
                }
            }
            else
                e.leakMs = 0;
            Prune(player);
            return events;
        }

        // The cap's Sickness ran: the dose goes to 0.
        DoseEvents ResolveCap(std::uint64_t player)
        {
            auto it = _entries.find(player);
            if (it == _entries.end())
                return {};
            it->second.capPending = false;
            DoseEvents const events = Change(it->second, 0);
            Prune(player);
            return events;
        }

        bool CapPending(std::uint64_t player) const
        {
            auto it = _entries.find(player);
            return it != _entries.end() && it->second.capPending;
        }

        std::uint32_t Dose(std::uint64_t player) const
        {
            auto it = _entries.find(player);
            return it == _entries.end() ? 0 : it->second.dose;
        }

        Entry const* Find(std::uint64_t player) const
        {
            auto it = _entries.find(player);
            return it == _entries.end() ? nullptr : &it->second;
        }

        // Every carrier above 0, the highest dose first (ties by guid, so the order is stable).
        std::vector<std::pair<std::uint64_t, std::uint32_t>> Carriers() const
        {
            std::vector<std::pair<std::uint64_t, std::uint32_t>> out;
            for (auto const& [guid, e] : _entries)
                if (e.dose)
                    out.emplace_back(guid, e.dose);
            std::sort(out.begin(), out.end(), [](auto const& a, auto const& b)
            {
                return a.second != b.second ? a.second > b.second : a.first < b.first;
            });
            return out;
        }

        // Everyone the ledger knows (carriers, and players at 0 who hold an emote latch of this pull).
        std::vector<std::uint64_t> Known() const
        {
            std::vector<std::uint64_t> out;
            for (auto const& entry : _entries)
                out.push_back(entry.first);
            return out;
        }

        void Forget(std::uint64_t player) { _entries.erase(player); }
        void Clear() { _entries.clear(); }
        std::size_t Size() const { return _entries.size(); }

    private:
        DoseEvents Change(Entry& e, std::uint32_t to)
        {
            DoseEvents events;
            std::uint32_t const from = e.dose;
            e.dose = to;
            if (_rules.capAt && to >= _rules.capAt && from < _rules.capAt)
            {
                e.capPending = true;
                events.cap = true;
            }
            events.meltdown = Crossing(from, to, _rules.meltdownAt);
            if (events.meltdown > 0 && !e.meltdownEmoted)
            {
                e.meltdownEmoted = true;
                events.meltdownEmote = true;
            }
            int const leak = Crossing(from, to, _rules.leakAt);
            if (leak)
                e.leakMs = 0;       // the drop clock starts at the crossing (the first drop a full period later)
            if (leak > 0 && !e.leakEmoted)
            {
                e.leakEmoted = true;
                events.leakEmote = true;
            }
            if (!to)
                e.drainMs = 0;
            return events;
        }

        // An entry at 0 is kept while it holds an emote latch (once per player per pull), else dropped.
        void Prune(std::uint64_t player)
        {
            auto it = _entries.find(player);
            if (it != _entries.end() && !it->second.dose && !it->second.capPending && !it->second.leakEmoted
                && !it->second.meltdownEmoted)
                _entries.erase(it);
        }

        DoseRules _rules;
        std::map<std::uint64_t, Entry> _entries;
    };

    // The DoseRules of Fallout's own field by difficulty.
    inline DoseRules FalloutDoseRules(bool heroic)
    {
        DoseRules r;
        r.capAt = Tune::kSicknessAt(heroic);
        r.drainEveryMs = Tune::kDrainEveryMs(heroic);
        r.leakAt = Tune::kLeakAt(heroic);
        r.leakEveryMs = Tune::kLeakEveryMs;
        r.meltdownAt = Tune::kMeltdownAt(heroic);
        return r;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Percents
    // ----------------------------------------------------------------------------------------------------------------

    // VF5: his script hits while Saturated (kSaturatedScalesHits).
    constexpr float SaturatedFactor(bool saturated)
    {
        return saturated && Tune::kSaturatedScalesHits ? 1.f + Tune::kSaturatedDamagePct / 100.f : 1.f;
    }

    // VF3: normal 10%; heroic 10% plus 3% per dose carried, no cap (ruling 18).
    constexpr float VolleyPct(bool heroic, std::uint32_t dose, bool saturated)
    {
        float const base = Tune::kVolleyPct + (heroic ? Tune::kVolleyPctPerDoseH * float(dose) : 0.f);
        return base * SaturatedFactor(saturated);
    }

    // VF3 + VF5: the dose a Volley gives.
    constexpr std::int32_t VolleyDose(bool saturated)
    {
        return Tune::kVolleyDose + (saturated ? Tune::kSaturatedVolleyDose : 0);
    }

    constexpr float OozePct(bool heroic, bool saturated)
    {
        return Tune::kOozePct(heroic) * SaturatedFactor(saturated);
    }

    // VF9: his heal for `shed` doses (0.5% of his maximum health each), rounded.
    inline std::uint32_t HalfLifeHeal(std::uint32_t maxHealth, std::uint32_t shed)
    {
        double const v = double(maxHealth) * Tune::kHalfLifeHealPctPerDose / 100.0 * double(shed);
        return static_cast<std::uint32_t>(std::max<long>(0, std::lround(v)));
    }

    // VF9 (RF-1 Minor-2): the bots' Stack and keep-out warn for the bar's own cast time, so they resolve when the
    // halving does (OnSpellCast): a cast slow (Curse of Tongues, Mind-numbing Poison, Slow) stretches the 3 s bar to
    // about 4.5-4.8 s. A bar that reports no cast time keeps the nominal one.
    constexpr std::uint32_t HalfLifeBarMs(std::int32_t castMs)
    {
        return castMs > 0 ? std::uint32_t(castMs) : Tune::kHalfLifeCastMs;
    }

    // The pool disc's object scale for a radius (the nature disc is a 9.6 yd quad at scale 1).
    constexpr float DiscScale(float radiusYd)
    {
        return radiusYd / kDiscQuadRadius;
    }

    // VF6: when to launch the glob so it lands as the warning ends (at once when it cannot).
    inline std::uint32_t GlobLaunchDelayMs(float distanceYd, float speed = Tune::kGlobMissileSpeed,
        std::uint32_t warnMs = Tune::kOozeWarnMs)
    {
        if (speed <= 0.f)
            return 0;
        double const flightMs = std::max(0.f, distanceYd) / speed * 1000.0;
        return flightMs >= double(warnMs) ? 0u : static_cast<std::uint32_t>(double(warnMs) - flightMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's clocks (rule 11, RB-17: a beat that fires late never starves the next: max(due + period, now +
    // period / 2))
    // ----------------------------------------------------------------------------------------------------------------
    struct Beat
    {
        std::uint64_t due = 0;
        std::uint32_t every = 0;
        bool on = false;

        void Start(std::uint64_t now, std::uint32_t firstMs, std::uint32_t everyMs)
        {
            due = now + firstMs;
            every = everyMs;
            on = true;
        }

        bool Due(std::uint64_t now) const { return on && now >= due; }

        // The beat fired at `now`: the next one.
        void Fired(std::uint64_t now)
        {
            due = std::max<std::uint64_t>(due + every, now + every / 2);
        }

        // A refused firing (a bar the engine refused): again in `ms`.
        void Retry(std::uint64_t now, std::uint32_t ms) { due = now + ms; }

        void Stop() { on = false; }
        std::uint64_t InMs(std::uint64_t now) const { return on && due > now ? due - now : 0; }
    };

    // How many times each beat fires in `fightMs` (the host test's timeline check: no beat is starved).
    struct BeatCounts
    {
        std::uint32_t volleys = 0;
        std::uint32_t oozes = 0;
        std::uint32_t halfLifes = 0;
    };

    inline BeatCounts SimulateBeats(bool heroic, std::uint64_t fightMs, std::uint32_t stepMs = 100)
    {
        Beat volley;
        Beat ooze;
        Beat halfLife;
        volley.Start(0, Tune::kBeatFirstMs(heroic), Tune::kBeatEveryMs(heroic));
        ooze.Start(0, Tune::kOozeFirstMs, Tune::kOozeEveryMs);
        if (heroic)
            halfLife.Start(0, Tune::kHalfLifeFirstMs, Tune::kHalfLifeEveryMs);
        BeatCounts counts;
        for (std::uint64_t now = 0; now <= fightMs; now += stepMs)
        {
            if (volley.Due(now))
            {
                ++counts.volleys;
                volley.Fired(now);
            }
            if (ooze.Due(now))
            {
                ++counts.oozes;
                ooze.Fired(now);
            }
            if (halfLife.Due(now))
            {
                ++counts.halfLifes;
                halfLife.Fired(now);
            }
        }
        return counts;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pools (VF3 Volley, VF4 Slough, VF6 glob, VF7 Leaking): one union, judged by the script (telegraph-only
    // registry rings for the bots). A pool arms `armMs` after it lands and lives `lifeMs` after that (0: the fight). A
    // heroic Slough grows by hand (Grow): its new radius counts once the grown ring is live.
    // ----------------------------------------------------------------------------------------------------------------
    enum class PoolKind : std::uint8_t
    {
        Volley  = 0,
        Slough  = 1,
        Ooze    = 2,
        Leak    = 3,
    };
    inline constexpr std::array<char const*, 4> kPoolKindNames{ { "volley", "slough", "ooze", "leak" } };

    struct Pool
    {
        std::uint32_t id = 0;
        PoolKind kind = PoolKind::Volley;
        Vec2 center;
        float z = 0.f;
        float radius = 0.f;
        std::uint64_t armAt = 0;
        std::uint64_t expireAt = 0;         // 0: never
        bool grows = false;
        std::uint64_t nextGrowAt = 0;       // a growing pool's next step

        bool Armed(std::uint64_t now) const { return now >= armAt; }
        bool Expired(std::uint64_t now) const { return expireAt && now >= expireAt; }
    };

    inline float PoolArea(float radius)
    {
        return DungeonKit::kPi * radius * radius;
    }

    // The tag of a pool's registry ring (the drill's table).
    constexpr std::uint32_t PoolTag(PoolKind kind)
    {
        switch (kind)
        {
            case PoolKind::Volley:
                return TAG_VF_VOLLEY_POOL;
            case PoolKind::Leak:
                return TAG_VF_LEAKING;
            case PoolKind::Slough:
            case PoolKind::Ooze:
            default:
                return TAG_VF_SLOUGH;
        }
    }

    class PoolSet
    {
    public:
        explicit PoolSet(float zBand = Tune::kPoolZBandYd) : _zBand(zBand) { }

        std::uint32_t Add(std::uint64_t now, PoolKind kind, Vec2 center, float z, float radius, std::uint32_t armMs,
            std::uint32_t lifeMs, std::uint32_t growEveryMs = 0)
        {
            Pool p;
            p.id = _nextId++;
            p.kind = kind;
            p.center = center;
            p.z = z;
            p.radius = std::max(0.f, radius);
            p.armAt = now + armMs;
            p.expireAt = lifeMs ? now + armMs + lifeMs : 0;
            p.grows = growEveryMs > 0;
            p.nextGrowAt = p.grows ? p.armAt + growEveryMs : 0;
            _pools.push_back(p);
            return p.id;
        }

        // The pools due a growth step at `now` (heroic Slough); the caller grows each and re-registers its ring.
        std::vector<std::uint32_t> GrowthDue(std::uint64_t now) const
        {
            std::vector<std::uint32_t> due;
            for (Pool const& p : _pools)
                if (p.grows && !p.Expired(now) && now >= p.nextGrowAt)
                    due.push_back(p.id);
            return due;
        }

        // A growth step was taken at `now` (its grown ring registered): the next one `everyMs` after the one due, never
        // sooner than half a period from now (RB-17). The radius changes when the grown ring is live (SetRadius).
        bool Grew(std::uint32_t id, std::uint64_t now, std::uint32_t everyMs)
        {
            for (Pool& p : _pools)
                if (p.id == id)
                {
                    p.nextGrowAt = std::max<std::uint64_t>(p.nextGrowAt + everyMs, now + everyMs / 2);
                    return true;
                }
            return false;
        }

        // The radius the script judges from now on (a pool never shrinks).
        bool SetRadius(std::uint32_t id, float radius)
        {
            for (Pool& p : _pools)
                if (p.id == id)
                {
                    p.radius = std::max(p.radius, radius);
                    return true;
                }
            return false;
        }

        // The armed pool holding (p, z) now, the first added wins; nullopt: none.
        std::optional<std::uint32_t> PoolAt(std::uint64_t now, Vec2 p, float z) const
        {
            for (Pool const& q : _pools)
                if (!q.Expired(now) && q.Armed(now) && std::fabs(q.z - z) <= _zBand
                    && DungeonKit::Distance(q.center, p) <= q.radius)
                    return q.id;
            return std::nullopt;
        }

        bool Contains(std::uint64_t now, Vec2 p, float z) const { return PoolAt(now, p, z).has_value(); }

        std::vector<std::uint32_t> Prune(std::uint64_t now)
        {
            std::vector<std::uint32_t> gone;
            std::erase_if(_pools, [now, &gone](Pool const& p)
            {
                if (!p.Expired(now))
                    return false;
                gone.push_back(p.id);
                return true;
            });
            return gone;
        }

        Pool const* Find(std::uint32_t id) const
        {
            for (Pool const& p : _pools)
                if (p.id == id)
                    return &p;
            return nullptr;
        }

        std::size_t Count(PoolKind kind) const
        {
            return std::size_t(std::count_if(_pools.begin(), _pools.end(),
                [kind](Pool const& p) { return p.kind == kind; }));
        }

        // The sum of the pools' areas (overlaps counted twice: the space math's upper bound).
        float AreaSum() const
        {
            float sum = 0.f;
            for (Pool const& p : _pools)
                sum += PoolArea(p.radius);
            return sum;
        }

        std::vector<Pool> const& All() const { return _pools; }
        std::size_t Size() const { return _pools.size(); }
        void Clear() { _pools.clear(); }

    private:
        float _zBand;
        std::vector<Pool> _pools;
        std::uint32_t _nextId = 1;
    };
}

#endif
