/*
 * mod-dungeon-bosses, Ragefire Chasm D4H: Starving, Taragaman's hard mode (heroic only), the pure, host-testable part
 * (no engine headers; tests/rfc_taragaman_hard_mode_test.cpp). The numbers of the build spec are
 * RagefireChasmRework::Taragaman (`Tune` below, its hard mode column): nothing here restates one. What is here is what
 * the spec does not set, and the rules:
 *
 *   ShrineRefusal, PourRefusal   who may draw the Hungerer's Blood and pour it (section 7 #15 A-#18 A)
 *   LineWake, FallbackDue        the Starving Feast: the 30% line and its 6 s gap, the fallback at heroic's pace
 *                                (ruling 16)
 *   ComboClock                   phase 2's Felstorm into Nova (section 7 #27 A), with a catch-up
 *   DriftClamp                   the ring's center, kept within 8 yd of his spawn (section 7 #25 A)
 *   GlobuleLeg, kGlobuleTiers    the globules' way over the plateau, and the bots' kill order by distance
 *   kBloodLakeSpots              where the lake's red look stands in phase 2
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_HARD_MODE_LOGIC_H

#include "RagefireChasmRework.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace RfcStarving
{
    namespace Tune = RagefireChasmRework::Taragaman;
    using DungeonKit::Vec2;
    using RagefireChasmRework::Mode;
    using RagefireChasmRework::Point3;

    // Every spell of this WP sits in this slice (RagefireChasmRework.h; ids.yaml reservation `ragefire_chasm`).
    inline constexpr RagefireChasmRework::IdSlice kSpellSlice = RagefireChasmRework::kSpellsStarving;

    // Declared in apps/dbc-tools source/npcs/ragefire_chasm/taragaman_hard_mode.py (the same ids, tested).
    // 213696-213719 spare.
    enum TaragamanHardModeSpells : std::uint32_t
    {
        SPELL_HM_HUNGERERS_BLOOD    = kSpellSlice.first + 0,    // 213690 the carrier's aura, 10 min
        SPELL_HM_POUR               = kSpellSlice.first + 1,    // 213691 the pour's look, a stalker at the lava
        SPELL_HM_STARVING           = kSpellSlice.first + 2,    // 213692 the hard mode's red aura on Taragaman
        SPELL_HM_BLOOD_LAKE         = kSpellSlice.first + 3,    // 213693 phase 2: the lake's look, on stalkers
        SPELL_HM_BURST              = kSpellSlice.first + 4,    // 213694 TG9 the burst's hit (resolve copy, Shadow)
        SPELL_HM_BURST_LOOK         = kSpellSlice.first + 5,    // 213695 TG9 the burst's look, the spot's stalker
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_HM_BURST_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "the hard mode's spells stay in the D4H slice");

    // Registry tag: BM's drill `ragefire-chasm-shapes` row globule-walkers (reported) uses the same one (rule 34).
    enum TaragamanHardModeTags : std::uint32_t
    {
        TAG_HM_BURST    = 17,   // TG9
    };

    // ----------------------------------------------------------------------------------------------------------------
    // What the build spec does not set
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kTriggerPollMs = 1000;          // the shrine's and the pour spot's selectable check
    std::uint32_t constexpr kPourLookMs = 5000;             // the pour's stalker
    std::uint32_t constexpr kBurstStalkerMs = 2000;         // past the burst
    std::uint32_t constexpr kGlobuleCorpseMs = 3000;
    std::uint32_t constexpr kGlobuleAimMs = 500;            // its walk is re-aimed at this rate
    float constexpr kGlobuleReaimYd = 1.f;                  // ... when its goal moved this far
    float constexpr kGlobuleReachZYd = 8.f;                 // the plateau's own height range; never a globule below it
    std::uint32_t constexpr kGlobuleOffFloorMs = 4000;      // off the plateau this long: put back on its edge
    float constexpr kGlobuleMinRate = 0.1f;                 // the slowest a slow makes it

    // Phase ids (Mechanic::SetPhase through NotePhaseChange).
    std::uint32_t constexpr kPhaseHunt = 1;
    std::uint32_t constexpr kPhaseBloodLake = 2;

    // Open lava at the four arm ends (NAVMESH-REPORT "Globule starts"), in SpikePoint's arm order: the look's stalkers.
    inline std::array<Point3, 4> constexpr kBloodLakeSpots{ {
        { -207.2f, 159.2f, -28.0f }, { -279.2f, 140.2f, -28.0f },
        { -241.8f, 190.2f, -28.0f }, { -254.8f, 110.8f, -28.0f },
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The trigger (section 7 #15 A-#18 A; the instance's HardModeChangeAllowed has the last word on the flag)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Refusal : std::uint8_t
    {
        None,
        Bot,            // silent: the hard mode is human only (#18 A)
        NotHeroic,
        Dead,           // the user is dead
        InCombat,       // the user fights
        Fighting,       // Taragaman fights
        Killed,         // Taragaman is dead
        AlreadyPoured,
        NoBlood,        // the pour: the user carries none
        Instance,       // the instance refused the flag
    };

    struct TriggerState
    {
        bool bot = false;
        bool heroic = false;
        bool alive = false;                     // the user
        bool inCombat = false;                  // the user
        bool carries = false;                   // the user has the Hungerer's Blood
        std::uint32_t taragamanState = DungeonKit::State::NotStarted;
        bool armed = false;                     // DATA_HARD_MODE
    };

    // Whether the trigger is closed for everyone (its objects are not selectable then).
    constexpr Refusal ClosedFor(bool heroic, std::uint32_t taragamanState, bool armed)
    {
        if (!heroic)
            return Refusal::NotHeroic;
        if (taragamanState == DungeonKit::State::Done)
            return Refusal::Killed;
        if (taragamanState == DungeonKit::State::InProgress)
            return Refusal::Fighting;
        return armed ? Refusal::AlreadyPoured : Refusal::None;
    }

    // Drawing the blood. Any number of players may carry it, and it may be drawn again (#17 A).
    constexpr Refusal ShrineRefusal(TriggerState const& s)
    {
        if (s.bot)
            return Refusal::Bot;
        Refusal const closed = ClosedFor(s.heroic, s.taragamanState, s.armed);
        if (closed != Refusal::None)
            return closed;
        if (!s.alive)
            return Refusal::Dead;
        return s.inCombat ? Refusal::InCombat : Refusal::None;
    }

    // Pouring it: at any gate state, out of combat.
    constexpr Refusal PourRefusal(TriggerState const& s)
    {
        Refusal const refusal = ShrineRefusal(s);
        if (refusal != Refusal::None)
            return refusal;
        return s.carries ? Refusal::None : Refusal::NoBlood;
    }

    // What the user reads; nullptr: nothing.
    constexpr char const* RefusalNotice(Refusal refusal)
    {
        switch (refusal)
        {
            case Refusal::NotHeroic:
                return "Nothing stirs.";
            case Refusal::InCombat:
                return "You cannot do that in combat.";
            case Refusal::Fighting:
                return "The Hungerer is already feeding.";
            case Refusal::Killed:
                return "The Hungerer is dead.";
            case Refusal::AlreadyPoured:
                return "The Hungerer has already tasted the blood.";
            case Refusal::NoBlood:
                return "You carry no blood to pour.";
            case Refusal::Instance:
                return "Nothing happens.";
            case Refusal::None:
            case Refusal::Bot:
            case Refusal::Dead:
                break;
        }
        return nullptr;
    }

    char constexpr kDrawnNotice[] = "You draw the Hungerer's blood. Pour it into the lava below his plateau.";

    // ----------------------------------------------------------------------------------------------------------------
    // TG1 the Starving Feast (rulings 10, 12, 16)
    // ----------------------------------------------------------------------------------------------------------------
    // Whether he Feasts on the lowest eligible player now because they are under the line. `now`: since the pull;
    // `lastFeastMs`: the last mark (0: none yet); `lowestPct`: that player's health percent. Level, not edge: a player
    // who stays under the line is hunted again after the gap. The pull counts as a phase start (no Feast in its first 2
    // s). The timeline (D4) adds the hold after a set piece, "one beat at a time" and a due set
    // piece first.
    constexpr bool LineWake(std::uint64_t now, std::uint64_t lastFeastMs, float lowestPct)
    {
        return now >= Tune::kFeastAfterPhaseMs && lowestPct < Tune::kStarvingLinePct
            && (!lastFeastMs || now >= lastFeastMs + Tune::kStarvingGapMs);
    }

    // Nobody was under the line: D4's own Feast timer (the hard mode's 15 s) runs at its own pace, in D4's queue, where
    // it holds a set piece that came due after it, as on heroic (ruling 16: never less often). A late Feast catches up
    // as heroic's does, the gap between two marks kept; "15 s since the last mark" would lock it onto the set pieces.
    constexpr bool FallbackDue(std::uint64_t now, std::uint64_t lastFeastMs)
    {
        return now >= lastFeastMs + Tune::kStarvingGapMs;
    }

    // Phase 2 starts once, at the line; his heals do not end it.
    constexpr bool Phase2Due(float healthPct)
    {
        return healthPct <= Tune::kPhase2Pct;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG7 Felstorm into Nova (phase 2; D4's own Felstorm and Nova timers are held)
    // ----------------------------------------------------------------------------------------------------------------

    // It keeps its own pace as D4's timeline does: a combo a Feast pushed back is due again kComboEveryMs after it was
    // due, half that after its bar at least (ruling 16: the mean is heroic's, whatever the Feasts do; once it runs
    // there are never two combos on end with no Feast between them). The Nova follows every spin that ends in phase 2
    // by kComboNovaAfterSpinMs. The first one is due when the phase starts, but never sooner than half a Felstorm
    // period after phase 1's last bar (D4's own rule for a late beat); a spin running then is the first one. So the gap
    // across the 30% line, once a fight, can be longer than any inside a phase: a Felstorm and a Nova of phase 1 just
    // due, then the first combo (a Feast up to 33.5 to 42.4 s, a Nova 38 to 48 s by the leaps' lengths; not on the
    // mean).
    class ComboClock
    {
    public:
        enum class Due : std::uint8_t
        {
            None,
            Felstorm,
            Nova,
        };

        // The phase starts.
        void Start(std::uint64_t now, bool spinning)
        {
            _on = true;
            if (!_seen)
                _felstormDue = now;
            else if (spinning)
                _felstormDue = _lastBar + Tune::kComboEveryMs;
            else
                _felstormDue = std::max(now, _lastBar + Tune::kFelstormEveryMs(Mode::HardMode) / 2);
        }

        // A spin started whose bar started at `barMs` (either phase, whoever started it).
        void SpinStarted(std::uint64_t barMs)
        {
            _seen = true;
            _lastBar = barMs;
            if (!_on)
                return;
            // Late: its own pace, half an interval away at least (Timeline::Advance's rule). Early (a GM's, or a bar
            // that started before the phase): from the bar.
            _felstormDue = _felstormDue > barMs ? barMs + Tune::kComboEveryMs
                : std::max<std::uint64_t>(_felstormDue + Tune::kComboEveryMs, barMs + Tune::kComboEveryMs / 2);
        }

        void SpinEnded(std::uint64_t now)
        {
            if (_on)
                _novaDue = now + Tune::kComboNovaAfterSpinMs;
        }

        // A Nova started, whoever started it.
        void NovaStarted() { _novaDue.reset(); }

        // `.dbtest`: the next combo now.
        void Hurry(std::uint64_t now)
        {
            if (_on)
                _felstormDue = now;
        }

        // What to start now (asked every tick: a refused start is asked again).
        Due At(std::uint64_t now) const
        {
            if (!_on)
                return Due::None;
            if (_novaDue)
                return now >= *_novaDue ? Due::Nova : Due::None;
            return now >= _felstormDue ? Due::Felstorm : Due::None;
        }

        bool On() const { return _on; }
        std::uint64_t FelstormDueMs() const { return _felstormDue; }

    private:
        bool _on = false;
        bool _seen = false;
        std::uint64_t _lastBar = 0;
        std::uint64_t _felstormDue = 0;
        std::optional<std::uint64_t> _novaDue;
    };

    // Whether D4's timer may start a Feast at all now. Phase 2: never in front of a due combo (rule 24). A Devour that
    // runs its full time ends inside D4's tick, after the combo was asked and refused: without this the Feast of the
    // same tick goes first and the combo is late by a whole Feast (RF-1 RF-M2).
    inline bool TimerFeastMay(std::uint64_t now, std::uint64_t lastFeastMs, ComboClock const& combo)
    {
        return FallbackDue(now, lastFeastMs) && combo.At(now) == ComboClock::Due::None;
    }

    // TG8: the waves, the first when the phase starts; a fixed pace of their own (a set piece never moves a wave).
    class WaveClock
    {
    public:
        void Start(std::uint64_t now)
        {
            _on = true;
            _due = now;
        }

        // True when a wave is due: the next one is kGlobuleEveryMs later.
        bool Take(std::uint64_t now)
        {
            if (!_on || now < _due)
                return false;
            _due += Tune::kGlobuleEveryMs;
            return true;
        }

        std::uint64_t DueMs() const { return _due; }

    private:
        bool _on = false;
        std::uint64_t _due = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TG3 the drifting ring
    // ----------------------------------------------------------------------------------------------------------------

    // `p`, or the nearest point to it within kDriftClampYd of his spawn. The whole disc is arena (host-tested), so a
    // straight line between two clamped points never leaves it.
    inline Vec2 DriftClamp(Vec2 p)
    {
        Vec2 const spawn = RagefireChasmRework::kTaragamanSpawn.XY();
        float const d = DungeonKit::Distance(spawn, p);
        if (d <= Tune::kDriftClampYd)
            return p;
        return DungeonKit::Advance(spawn, DungeonKit::BearingTo(spawn, p), Tune::kDriftClampYd);
    }

    // Where he must stand for a Felstorm's bar: nullopt where he stands when that is in the disc, else its nearest
    // point (he leaps there first: the ring's center is never outside it).
    inline std::optional<Vec2> FelstormSpotFor(Vec2 at)
    {
        Vec2 const clamped = DriftClamp(at);
        return DungeonKit::Distance(clamped, at) > 0.5f ? std::optional<Vec2>(clamped) : std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG8 the Blood Globules
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kSightStepYd = 0.5f;

    // Whether the straight line from `a` to `b` stays on the plateau's floor.
    inline bool StraightOnFloor(Vec2 a, Vec2 b)
    {
        std::span<Vec2 const> const floor(RagefireChasmRework::kPlateauFloorPolygon);
        float const length = DungeonKit::Distance(a, b);
        std::uint32_t const steps = std::max<std::uint32_t>(1, static_cast<std::uint32_t>(length / kSightStepYd));
        for (std::uint32_t i = 0; i <= steps; ++i)
        {
            float const t = static_cast<float>(i) / static_cast<float>(steps);
            if (!DungeonKit::PointInPolygon(floor, { a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t }))
                return false;
        }
        return true;
    }

    enum class Leg : std::uint8_t
    {
        ToHim,          // straight to him over the floor
        ToHub,          // he is round a corner (another arm): the hub first
        Path,           // neither line is all floor: the navmesh
    };

    inline Leg GlobuleLeg(Vec2 globule, Vec2 him)
    {
        if (StraightOnFloor(globule, him))
            return Leg::ToHim;
        Vec2 const hub = RagefireChasmRework::kHub.XY();
        if (DungeonKit::Distance(globule, hub) > 2.f * kGlobuleReaimYd && StraightOnFloor(globule, hub))
            return Leg::ToHub;
        return Leg::Path;
    }

    // Drunk: within reach of him.
    constexpr bool Drunk(float distance2d, float dz)
    {
        return distance2d <= Tune::kGlobuleReachYd && dz <= kGlobuleReachZYd && dz >= -kGlobuleReachZYd;
    }

    // The strongest slow on it (`slowPct`, negative or 0) slows its crawl; nothing speeds it up. Not its speed rate:
    // the engine also lowers that for a creature under 30% health.
    inline float GlobuleSpeed(std::int32_t slowPct)
    {
        return Tune::kGlobuleSpeed * std::clamp(1.f + static_cast<float>(slowPct) / 100.f, kGlobuleMinRate, 1.f);
    }

    // The bots' kill order: the globule nearest to him first (the descriptor has no distance sort, so bands).
    struct GlobuleTier
    {
        float withinYd;             // the globule is within this of him
        std::int8_t priority;       // he is 0
    };
    inline std::array<GlobuleTier, 4> constexpr kGlobuleTiers{ {
        { 10.f, 4 }, { 18.f, 3 }, { 26.f, 2 }, { 80.f, 1 },
    } };
}

#endif
