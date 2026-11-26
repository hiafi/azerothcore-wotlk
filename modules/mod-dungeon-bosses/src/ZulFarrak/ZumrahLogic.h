/*
 * mod-dungeon-bosses, Zul'Farrak D3: Witch Doctor Zum'rah, the pure, host-testable part (no engine headers). Build
 * spec: docs/dungeons/zul-farrak-rework.md "Witch Doctor Zum'rah" (ZR1-ZR14, rulings 17-20, 45); handoff sections 3.5
 * row D3, 3.6, 3.8 (the bowl, the 40 grave sites), 3.9 rows 3 and 4, 7 #29, #30, #48 and 10. Tested by
 * tests/zf_zumrah_test.cpp; apps/dbc-tools lib/test_zul_farrak_zumrah.py pins the data against this file.
 *
 *   ZumrahSpells / ZumrahTags / ZumrahTexts   the spells (kSpellsZumrah), G1's drill tags, the text groups
 *   Tune                     every number of the fight (rule 32)
 *   Timeline                 his casts: Spirit Rend on its fixed grid and never late, the Volley never started into a
 *                            Rend, the Ward on its own clock, Shadow Bolts only where they fit before both
 *   SoulClock                a Lost Soul rises every 6 s (heroic 2 s) from the pull
 *   WardRaiser               a ward raises a Skeleton every 5 s for 20 s (four), then goes
 *   RendCandidates           everyone crosses in turn: who has not walked since the last reset of the rotation
 *   WardReductionPct         Ward of the Dead: 10% a Bound Dead to 40% (normal, capped at 4); heroic 15% each to 60%,
 *                            then each cuts 15% of what is left (ruling 45)
 *   BindsOrLost              a soul at the cauldron binds, or is lost past the normal cap
 *   BoundDeadSpot            the four spots at his feet, then the neck mouth (section 7 #30 A)
 *   kGraves / RiseGraves     the 40 grave sites; souls rise only from those within 60 yd of the cauldron (7 #29 A)
 *   GravesNear               heroic Grasping Graves: the sites within 20 yd of the walker
 *
 * Health is ZulFarrakRework.h Health: never restated here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_ZUMRAH_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_ZUMRAH_LOGIC_H

#include "DungeonKitMath.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <set>
#include <vector>

namespace ZfZumrah
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ZulFarrakRework::Point3;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsZumrah;

    // apps/dbc-tools source/npcs/zul_farrak/zumrah.py declares them.
    enum ZumrahSpells : std::uint32_t
    {
        SPELL_ZR_SPIRIT_REND        = kSpellSlice.first + 0,    // ZR1: the 2 s bar on himself (Arcane: rule 24)
        SPELL_ZR_BETWEEN_WORLDS     = kSpellSlice.first + 1,    // ZR2: the walker (type 11 detect, +40% speed, ghost)
        SPELL_ZR_EMPTY_VESSEL       = kSpellSlice.first + 2,    // ZR3: aura 247 the walker casts on the husk
        SPELL_ZR_TETHER             = kSpellSlice.first + 3,    // ZR3: the channel look, husk to walker (field only)
        SPELL_ZR_SPIRIT_WORLD       = kSpellSlice.first + 4,    // invisibility type 11: souls, Bound Dead, graves
        SPELL_ZR_LOST_SOUL          = kSpellSlice.first + 5,    // ZR4: the soul's lasting look
        SPELL_ZR_BOUND              = kSpellSlice.first + 6,    // ZR6: the binding look (self visual)
        SPELL_ZR_FREED              = kSpellSlice.first + 7,    // ZR6: freed; heroic Soul Echo's landing (self visual)
        SPELL_ZR_GATHERED_SOULS     = kSpellSlice.first + 8,    // ZR5: the walker's stack
        SPELL_ZR_WARD_OF_THE_DEAD   = kSpellSlice.first + 9,    // ZR7: his stack (amount set by script)
        SPELL_ZR_VOLLEY             = kSpellSlice.first + 10,   // ZR9: the kickable 3 s cast (normal)
        SPELL_ZR_VOLLEY_HEROIC      = kSpellSlice.first + 11,   // ZR9: the kickable 2 s cast (heroic)
        SPELL_ZR_VOLLEY_HIT         = kSpellSlice.first + 12,   // ZR9: the landed hit (script base point)
        SPELL_ZR_SHADOW_BOLT        = kSpellSlice.first + 13,   // ZR10: the copy of 12739 (script base point)
        SPELL_ZR_SKELETAL_STRIKE    = kSpellSlice.first + 14,   // ZR8: a Skeleton's hit (script base point)
        SPELL_ZR_SOUL_BURN          = kSpellSlice.first + 15,   // ZR11 heroic: a soul gathered (script base point)
        SPELL_ZR_SOUL_ECHO          = kSpellSlice.first + 16,   // ZR12 heroic: resolve copy, Shadow
        SPELL_ZR_RESTLESS_WAIL      = kSpellSlice.first + 17,   // ZR13 heroic: resolve copy, Shadow
        SPELL_ZR_GRASPING_GRAVES    = kSpellSlice.first + 18,   // ZR14 heroic: resolve copy, Shadow
        SPELL_ZR_GRAVE_ERUPTION     = kSpellSlice.first + 19,   // ZR14 heroic: the grave's look (self visual)
    };
    // 213940-213959 spare.

    // The stock Ward of Zum'rah 11086 (it summons the ward 7785 for 20 s), cast as it is. The ward's own passive 11087
    // (11088: the Skeletons as the ward's guardians, SummonProperties 61, gone with it: R-1-A M1) is cleared; he
    // raises its Skeletons himself, wild (WardRaiser).
    inline constexpr std::uint32_t SPELL_WARD_OF_ZUMRAH = 11086;

    // Registry tags: G1's zul-farrak-shapes rows 3 and 4 use the same numbers (BM MechanicDrill.h kZfTag*).
    enum ZumrahTags : std::uint32_t
    {
        TAG_ZR_SOUL     = 9,    // ZR4: a soul's Soak (a soul bound at the cauldron is the group bar)
        TAG_ZR_FREE     = 10,   // ZR6: a Bound Dead's Soak (2 Gathered Souls)
        TAG_ZR_WAIL     = 13,   // ZR13 heroic, the walker only (seen with type 11)
        TAG_ZR_GRAVE    = 14,   // ZR14 heroic, the walker only (seen with type 11)
        TAG_ZR_ECHO     = 15,   // ZR12 heroic, the living only
    };

    // creature_text 7271: 0 and 1 stock (2 repeats 1), 3 and 4 new (the core SQL rev rev_zumrah_zul_farrak.sql).
    enum ZumrahTexts : std::uint8_t
    {
        SAY_ZUMRAH_AGGRO    = 0,
        SAY_ZUMRAH_KILL     = 1,
        EMOTE_ZUMRAH_REND   = 3,    // "%s tears $n's spirit from $g his:her; body!"
        EMOTE_ZUMRAH_BOUND  = 4,    // "A lost soul is bound to %s's ward!"
    };

    // The spirit world's invisibility type (appendix B 2.3: 11 is free; _visuals.py ZR_INVIS_TYPE). Souls, Bound Dead
    // and the grave looks carry it at 1, the walker detects it at 10, the walker-only markers carry it (BM-1).
    inline constexpr std::uint8_t kSpiritWorldType = 11;
    inline constexpr std::int32_t kSpiritWorldValue = 1;        // SPELL_ZR_SPIRIT_WORLD's invisibility amount
    inline constexpr std::int32_t kSpiritSightValue = 10;       // SPELL_ZR_BETWEEN_WORLDS' detect amount
    static_assert(kSpiritSightValue >= kSpiritWorldValue);

    // The descriptor's interrupt priority: the Volley only (SP "Interrupt list: Shadow Bolt Volley").
    inline constexpr std::uint8_t kVolleyKickPriority = 2;
    // Kill order: the ward, then Skeletons on a husk (SP "Boss data").
    inline constexpr std::int8_t kWardKillPriority = 2;
    inline constexpr std::int8_t kHuskSkeletonKillPriority = 1;

    namespace Tune
    {
        // ZR1 Spirit Rend and ZR2 Between Worlds: 15 s, then every 25 s; a 2 s bar; a 15 s walk at +40% speed.
        inline constexpr std::uint32_t kRendFirstMs = 15000;
        inline constexpr std::uint32_t kRendEveryMs = 25000;
        inline constexpr std::uint32_t kRendCastMs = 2000;
        inline constexpr std::uint32_t kWalkMs = 15000;
        inline constexpr std::int32_t kWalkSpeedPct = 40;
        // ZR4 Lost Souls: from the pull, one every 6 s at 3 yd/s (heroic every 2 s at 4 yd/s); taken at 2 yd.
        inline constexpr NH<std::uint32_t> kSoulEveryMs{ 6000, 2000 };
        inline constexpr NH<float> kSoulSpeed{ 3.f, 4.f };
        inline constexpr float kSoulTouchYd = 2.f;
        inline constexpr float kSoulBindReachYd = 2.5f;     // from the cauldron: bound
        inline constexpr float kSoulScale = 1.75f;          // _visuals.py LOST_SOUL_SCALE_RANGE (1.5, 2.0)
        // ZR6 the Bound Dead: two Gathered Souls free one, within 3 yd; normal caps them at 4 (heroic none, ruling 45).
        inline constexpr std::uint32_t kSoulsToFree = 2;
        inline constexpr float kFreeRadiusYd = 3.f;
        inline constexpr std::uint32_t kBoundDeadCapNormal = 4;
        inline constexpr std::uint32_t kBoundEmoteEveryMs = 10000;
        // ZR7 Ward of the Dead: 10% (heroic 15%) less damage taken a Bound Dead; heroic past 4: x0.85 of what is left.
        inline constexpr NH<std::uint32_t> kWardPctPerBound{ 10, 15 };
        inline constexpr std::uint32_t kWardLinearStacks = 4;
        inline constexpr float kWardPastFourKeep = 0.85f;
        // ZR8 Ward of Zum'rah: 2 s, then every 30 to 36 s (heroic 25 s); Skeletons 1.5% (heroic 2.5%) a second each,
        // as a hit every 2 s. A Skeleton that rises during a walk goes for the husk with this much threat (a taunt
        // matches it; damage alone does not).
        inline constexpr std::uint32_t kWardFirstMs = 2000;
        inline constexpr NH<std::uint32_t> kWardEveryMinMs{ 30000, 25000 };
        inline constexpr NH<std::uint32_t> kWardEveryMaxMs{ 36000, 25000 };
        // A ward raises a Skeleton every 5 s for 20 s (SP: 4 a ward, as stock), then goes; the Skeletons stay until
        // killed. The ward's own 20 s timer gets a margin, so the fourth rises before it can lapse.
        inline constexpr std::uint32_t kWardRaiseEveryMs = 5000;
        inline constexpr std::uint32_t kWardSkeletons = 4;
        inline constexpr std::uint32_t kWardLifeMs = kWardRaiseEveryMs * kWardSkeletons;
        inline constexpr std::uint32_t kWardLifeMarginMs = 2000;
        inline constexpr NH<float> kSkeletonPctPerSec{ 1.5f, 2.5f };
        inline constexpr std::uint32_t kSkeletonStrikeEveryMs = 2000;
        inline constexpr float kVesselThreat = 10000.f;
        // ZR9 Shadow Bolt Volley: 8 s, then every 12 to 16 s; 3 s cast (heroic 2 s); landed 20% (heroic 35%) on
        // everyone within 30 yd but the walker.
        inline constexpr std::uint32_t kVolleyFirstMs = 8000;
        inline constexpr std::uint32_t kVolleyEveryMinMs = 12000;
        inline constexpr std::uint32_t kVolleyEveryMaxMs = 16000;
        // A Volley that waited for a Rend keeps its grid, but never comes sooner than this after the last one: paced
        // for one 10 s interrupter (SP ZR9).
        inline constexpr std::uint32_t kVolleyMinGapMs = 10000;
        inline constexpr NH<std::uint32_t> kVolleyCastMs{ 3000, 2000 };
        inline constexpr NH<float> kVolleyPct{ 20.f, 35.f };
        inline constexpr float kVolleyRangeYd = 30.f;
        // ZR10 Shadow Bolt: 1 s, then every 3 to 4 s, a 3 s cast, about 8% on his target (heroic: the same percent of
        // the heroic row, designer question 2).
        inline constexpr std::uint32_t kBoltFirstMs = 1000;
        inline constexpr std::uint32_t kBoltEveryMinMs = 3000;
        inline constexpr std::uint32_t kBoltEveryMaxMs = 4000;
        inline constexpr std::uint32_t kBoltCastMs = 3000;
        inline constexpr NH<float> kBoltPct{ 8.f, 8.f };
        // ZR11 Soul Burn (heroic): 6% Shadow on the walker for every soul gathered.
        inline constexpr float kSoulBurnPct = 6.f;
        // ZR12 Soul Echo (heroic): 5 yd under a random living player per soul gathered, 2 s, 35% and Weakened.
        inline constexpr float kEchoRadiusYd = 5.f;
        inline constexpr std::uint32_t kEchoWarnMs = 2000;
        inline constexpr float kEchoPct = 35.f;
        // ZR13 Restless Wail (heroic): every Bound Dead within 15 yd of the walker, every 4 s, 6 yd on the walker,
        // 1.5 s, 40% and Weakened. The Bound Dead are staggered a second apart.
        inline constexpr float kWailRangeYd = 15.f;
        inline constexpr std::uint32_t kWailEveryMs = 4000;
        inline constexpr std::uint32_t kWailFirstMs = 1000;
        inline constexpr std::uint32_t kWailStaggerMs = 1000;
        inline constexpr float kWailRadiusYd = 6.f;
        inline constexpr std::uint32_t kWailWarnMs = 1500;
        inline constexpr float kWailPct = 40.f;
        // ZR14 Grasping Graves (heroic): every 3 s of a walk, two graves within 20 yd of the walker, 6 yd, 1.5 s, 40%
        // and Weakened (fewer in range: only those, section 7 #29 A).
        inline constexpr std::uint32_t kGravesEveryMs = 3000;
        inline constexpr float kGravesRangeYd = 20.f;
        inline constexpr std::uint32_t kGravesCount = 2;
        inline constexpr float kGravesRadiusYd = 6.f;
        inline constexpr std::uint32_t kGravesWarnMs = 1500;
        inline constexpr float kGravesPct = 40.f;
        inline constexpr std::uint32_t kGraveLookMs = 3000;   // the grave's look stays this long after the warning
    }

    // Warnings at or over the floor (rule 32, SYS 4).
    static_assert(Tune::kEchoWarnMs >= ZulFarrakRework::kWarningFloorMs);
    static_assert(Tune::kWailWarnMs >= ZulFarrakRework::kWarningFloorMs);
    static_assert(Tune::kGravesWarnMs >= ZulFarrakRework::kWarningFloorMs);
    static_assert(Tune::kRendCastMs >= ZulFarrakRework::kWarningFloorMs);
    // One walker at a time: a walk ends before the next Rend's bar starts.
    static_assert(Tune::kRendCastMs + Tune::kWalkMs < Tune::kRendEveryMs);
    // The Volley fits between two Rends on both difficulties.
    static_assert(Tune::kVolleyCastMs.normal + Tune::kRendCastMs < Tune::kRendEveryMs);

    // A Skeleton's hit every 2 s carries two seconds of its percent.
    constexpr float SkeletonStrikePct(bool heroic)
    {
        return Tune::kSkeletonPctPerSec(heroic) * static_cast<float>(Tune::kSkeletonStrikeEveryMs) / 1000.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // His casts
    // ----------------------------------------------------------------------------------------------------------------

    enum class Act : std::uint8_t
    {
        None,
        Rend,
        Volley,
        Bolt,
    };

    // A cast the engine refused (a kick's school lockout) is tried again this soon.
    inline constexpr std::uint32_t kRetryMs = 500;
    // A cast that would end later than this before a must-start beat does not start (update ticks).
    inline constexpr std::uint32_t kBeatMarginMs = 250;

    struct Beat
    {
        std::uint64_t due = std::numeric_limits<std::uint64_t>::max();
        std::uint64_t heldUntil = 0;

        bool Running() const { return due != std::numeric_limits<std::uint64_t>::max(); }
        bool Due(std::uint64_t now) const { return Running() && now >= due && now >= heldUntil; }
        // Rule 11: the next beat keeps max(due + period, now + floor) (floor: half the period unless given), so a late
        // beat never bunches the next.
        void Done(std::uint64_t now, std::uint32_t periodMs, std::uint32_t floorMs = 0)
        {
            heldUntil = 0;
            if (!Running())
                return;
            due = std::max<std::uint64_t>(due + periodMs, now + (floorMs ? floorMs : periodMs / 2));
        }
        void Retry(std::uint64_t now) { heldUntil = now + kRetryMs; }
    };

    // Spirit Rend is never late: it keeps its own grid (15, 40, 65 ... s) and nothing starts that would still run at
    // its beat. The Volley waits for a Rend it would run into (2 s at most), never the other way. A Shadow Bolt starts
    // only where it ends before both the Rend and the Volley; one that does not fit is skipped, not delayed. The Ward
    // is an instant on its own clock (cast triggered whatever he is doing).
    class Timeline
    {
    public:
        void Start(bool heroic)
        {
            *this = Timeline();
            _heroic = heroic;
            _running = true;
            _rend.due = Tune::kRendFirstMs;
            _volley.due = Tune::kVolleyFirstMs;
            _bolt.due = Tune::kBoltFirstMs;
            _ward.due = Tune::kWardFirstMs;
        }

        bool Running() const { return _running; }
        std::uint64_t Now() const { return _now; }
        void Advance(std::uint32_t diff) { _now += diff; }

        // The Ward is due (the caller casts it and calls WardDone with the next period).
        bool WardDue() const { return _running && _ward.Due(_now); }
        void WardDone(std::uint32_t periodMs) { _ward.Done(_now, periodMs); }

        // What he starts now when he is free (the caller reports Done or Retry).
        Act Next() const
        {
            if (!_running)
                return Act::None;
            if (_rend.Due(_now))
                return Act::Rend;
            if (_volley.Due(_now) && FitsBefore(Tune::kVolleyCastMs(_heroic), _rend))
                return Act::Volley;
            if (_bolt.Due(_now) && FitsBefore(Tune::kBoltCastMs, _rend) && FitsBefore(Tune::kBoltCastMs, _volley))
                return Act::Bolt;
            return Act::None;
        }

        // A due Bolt that cannot end before the next Rend or Volley is skipped (true once per skip); while the Rend or
        // the Volley is itself due, the Bolt waits behind it instead.
        bool SkipBolt(std::uint32_t periodMs)
        {
            if (!_running || !_bolt.Due(_now) || Next() == Act::Bolt || _rend.Due(_now) || _volley.Due(_now))
                return false;
            _bolt.Done(_now, periodMs);
            return true;
        }

        // `periodMs`: the next gap (the Rend's grid is fixed; the Volley 12-16 s and the Bolt 3-4 s are rolled by the
        // caller).
        void Done(Act act, std::uint32_t periodMs = 0)
        {
            switch (act)
            {
                case Act::Rend:
                    _rend.heldUntil = 0;
                    do
                        _rend.due += Tune::kRendEveryMs;
                    while (_rend.due <= _now);
                    break;
                case Act::Volley:
                    _volley.Done(_now, periodMs, std::min(periodMs, Tune::kVolleyMinGapMs));
                    break;
                case Act::Bolt:
                    _bolt.Done(_now, periodMs);
                    break;
                case Act::None:
                    break;
            }
        }
        void Retry(Act act)
        {
            if (Beat* b = Of(act))
                b->Retry(_now);
        }

        // Milliseconds to the act's next beat (0: due or not running).
        std::uint32_t In(Act act) const
        {
            Beat const* b = Of(act);
            return b && b->Running() && b->due > _now ? static_cast<std::uint32_t>(b->due - _now) : 0;
        }
        std::uint32_t WardIn() const
        {
            return _ward.Running() && _ward.due > _now ? static_cast<std::uint32_t>(_ward.due - _now) : 0;
        }

    private:
        bool FitsBefore(std::uint32_t castMs, Beat const& next) const
        {
            return !next.Running() || _now + castMs + kBeatMarginMs <= next.due;
        }

        Beat* Of(Act act)
        {
            return const_cast<Beat*>(static_cast<Timeline const*>(this)->Of(act));
        }
        Beat const* Of(Act act) const
        {
            switch (act)
            {
                case Act::Rend:
                    return &_rend;
                case Act::Volley:
                    return &_volley;
                case Act::Bolt:
                    return &_bolt;
                case Act::None:
                    break;
            }
            return nullptr;
        }

        std::uint64_t _now = 0;
        bool _heroic = false;
        bool _running = false;
        Beat _rend;
        Beat _volley;
        Beat _bolt;
        Beat _ward;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // ZR4 Lost Souls
    // ----------------------------------------------------------------------------------------------------------------

    // One soul at the pull, then one every period, on the fight's clock whatever he casts.
    class SoulClock
    {
    public:
        void Start(bool heroic)
        {
            _every = Tune::kSoulEveryMs(heroic);
            _next = 0;
            _running = true;
        }
        void Stop() { _running = false; }
        // How many souls rise by `now` (0 or 1 a tick; more after a long one).
        std::uint32_t Rises(std::uint64_t now)
        {
            std::uint32_t n = 0;
            while (_running && now >= _next)
            {
                ++n;
                _next += _every;
            }
            return n;
        }
        std::uint32_t In(std::uint64_t now) const
        {
            return _running && _next > now ? static_cast<std::uint32_t>(_next - now) : 0;
        }

    private:
        std::uint64_t _next = 0;
        std::uint32_t _every = 0;
        bool _running = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // ZR8 a Ward of Zum'rah's Skeletons
    // ----------------------------------------------------------------------------------------------------------------

    // One ward's raises on his clock: a Skeleton 5, 10, 15 and 20 s after it rises, then it is spent (he dismisses
    // it). A ward killed earlier just stops raising (the caller drops it).
    class WardRaiser
    {
    public:
        explicit WardRaiser(std::uint64_t risenAt = 0) : _next(risenAt + Tune::kWardRaiseEveryMs) { }
        // How many Skeletons rise by `now` (0 or 1 a tick; more after a long one), never past the ward's four.
        std::uint32_t Raises(std::uint64_t now)
        {
            std::uint32_t n = 0;
            while (_raised < Tune::kWardSkeletons && now >= _next)
            {
                ++n;
                ++_raised;
                _next += Tune::kWardRaiseEveryMs;
            }
            return n;
        }
        bool Spent() const { return _raised >= Tune::kWardSkeletons; }
        std::uint32_t Raised() const { return _raised; }

    private:
        std::uint64_t _next = 0;
        std::uint32_t _raised = 0;
    };

    // The 40 grave sites (gameobject 128308, one of the two objects on each; DB positions, SELECT 2026-11-25), west to
    // east. Their distance to the cauldron runs from 19.2 to 78.5 yd (30 within 60 yd).
    inline std::array<Point3, 40> constexpr kGraves{ {
        { 1832.72f, 1032.39f, 9.45f }, { 1836.74f, 1029.36f, 9.62f }, { 1839.18f, 1036.88f, 9.35f },
        { 1839.42f, 1023.49f, 9.56f }, { 1841.08f, 1045.54f, 9.22f }, { 1841.82f, 1027.76f, 9.15f },
        { 1843.19f, 1041.16f, 8.88f }, { 1845.54f, 1024.12f, 9.08f }, { 1845.96f, 1047.25f, 8.88f },
        { 1852.41f, 1024.78f, 8.88f }, { 1858.70f, 1053.75f, 8.88f }, { 1861.12f, 1019.39f, 8.88f },
        { 1862.12f, 1050.76f, 9.06f }, { 1863.41f, 1044.78f, 8.88f }, { 1865.03f, 1012.49f, 8.88f },
        { 1866.23f, 1008.40f, 8.88f }, { 1866.33f, 1049.64f, 9.02f }, { 1867.74f, 1041.84f, 8.88f },
        { 1869.28f, 1020.08f, 8.88f }, { 1871.08f, 1046.76f, 9.03f }, { 1871.30f, 1008.32f, 8.88f },
        { 1871.85f, 994.26f, 8.88f }, { 1875.85f, 1044.26f, 9.08f }, { 1876.14f, 976.48f, 9.05f },
        { 1876.44f, 972.21f, 9.91f }, { 1879.89f, 974.65f, 8.88f }, { 1881.46f, 1041.43f, 8.88f },
        { 1881.99f, 1034.68f, 8.88f }, { 1882.70f, 971.83f, 8.88f }, { 1887.46f, 967.14f, 8.98f },
        { 1887.94f, 1029.08f, 9.15f }, { 1888.36f, 1037.00f, 8.92f }, { 1888.64f, 977.75f, 8.88f },
        { 1890.12f, 989.76f, 8.88f }, { 1890.27f, 970.86f, 9.01f }, { 1891.60f, 1023.06f, 9.37f },
        { 1892.57f, 1006.37f, 9.07f }, { 1894.39f, 977.01f, 8.93f }, { 1897.08f, 980.84f, 8.96f },
        { 1897.98f, 985.28f, 8.90f },
    } };

    // Section 7 #29 A: the graves a soul may rise from (within kGraveReachYd of the cauldron), as indices of kGraves.
    inline std::vector<std::size_t> RiseGraves()
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < kGraves.size(); ++i)
            if (DungeonKit::Distance(kGraves[i].XY(), ZulFarrakRework::kCauldron.XY())
                <= ZulFarrakRework::kGraveReachYd)
                out.push_back(i);
        return out;
    }

    // Heroic Grasping Graves: the sites within `yd` of the walker (all 40 count: a walker far out still meets them).
    inline std::vector<std::size_t> GravesNear(Vec2 walker, float yd)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < kGraves.size(); ++i)
            if (DungeonKit::Distance(kGraves[i].XY(), walker) <= yd)
                out.push_back(i);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR1 who walks
    // ----------------------------------------------------------------------------------------------------------------

    // Everyone crosses in turn (SP theme, ruling 17), the tank and the healer included: the candidates who have not
    // walked since the rotation last reset. When all have walked, the rotation resets and only the last walker sits
    // out (unless they are the only one). `candidates` are the players in the fight now (raw guids); `walked` is the
    // rotation's memory, reset here when it is spent.
    inline std::vector<std::uint64_t> RendCandidates(std::vector<std::uint64_t> const& candidates,
        std::set<std::uint64_t>& walked, std::uint64_t lastWalker)
    {
        std::vector<std::uint64_t> out;
        for (std::uint64_t const c : candidates)
            if (!walked.count(c))
                out.push_back(c);
        if (!out.empty())
            return out;
        walked.clear();
        for (std::uint64_t const c : candidates)
            if (c != lastWalker)
                out.push_back(c);
        return out.empty() ? candidates : out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR6 and ZR7 the Bound Dead and the Ward of the Dead
    // ----------------------------------------------------------------------------------------------------------------

    // The percent less damage he takes with `bound` Bound Dead standing (rounded to the aura's whole percent).
    inline std::int32_t WardReductionPct(std::uint32_t bound, bool heroic)
    {
        if (!heroic)
            return static_cast<std::int32_t>(std::min(bound, Tune::kBoundDeadCapNormal)
                * Tune::kWardPctPerBound.normal);
        std::uint32_t const linear = std::min(bound, Tune::kWardLinearStacks);
        float left = 1.f - static_cast<float>(linear * Tune::kWardPctPerBound.heroic) / 100.f;
        for (std::uint32_t i = Tune::kWardLinearStacks; i < bound; ++i)
            left *= Tune::kWardPastFourKeep;
        return static_cast<std::int32_t>(std::lround((1.f - left) * 100.f));
    }

    // A soul reaching the cauldron with `bound` Bound Dead standing: binds (true), or is lost past the normal cap.
    constexpr bool BindsOrLost(std::uint32_t bound, bool heroic)
    {
        return heroic || bound < Tune::kBoundDeadCapNormal;
    }

    // Where the Bound Dead in `slot` stands: the four spots at his feet, then (heroic, ruling 45) the neck mouth: the
    // fifth on it, the next twelve on rings of 1.5 and 3 yd around it, six to a ring, then on it again.
    inline Point3 BoundDeadSpot(std::size_t slot)
    {
        using ZulFarrakRework::kBoundDeadOverflow;
        using ZulFarrakRework::kBoundDeadSpots;
        if (slot < kBoundDeadSpots.size())
            return kBoundDeadSpots[slot];
        std::size_t const k = slot - kBoundDeadSpots.size();
        if (k == 0 || k > 12)
            return kBoundDeadOverflow;
        std::size_t const ring = (k - 1) / 6;
        float const angle = static_cast<float>((k - 1) % 6) * DungeonKit::kTwoPi / 6.f
            + static_cast<float>(ring) * DungeonKit::kPi / 6.f;
        float const r = 1.5f * static_cast<float>(ring + 1);
        Point3 p = kBoundDeadOverflow;
        p.x += r * std::cos(angle);
        p.y += r * std::sin(angle);
        return p;
    }

    // The lowest free slot (`taken[i]`: slot i stands).
    inline std::size_t FirstFreeSlot(std::vector<bool> const& taken)
    {
        for (std::size_t i = 0; i < taken.size(); ++i)
            if (!taken[i])
                return i;
        return taken.size();
    }

    // The first Wail of the Bound Dead in `slot` after a walk starts (or after it binds mid-walk).
    constexpr std::uint32_t WailFirstMs(std::size_t slot)
    {
        return Tune::kWailFirstMs + static_cast<std::uint32_t>(slot % 4) * Tune::kWailStaggerMs;
    }
}

#endif
