/*
 * mod-dungeon-bosses, Scholomance S10: Lady Illucia Barov (10502), the pure, host-testable part (no engine headers):
 * the spell ids, the per-difficulty tuning, the never-paused fight timeline, the Foresight chain schedule, the motion
 * track's sampling, the Memory trail's tuning and the Fear's run. Build spec: SC 2695-2741 (build spec), SC 2548-2694
 * (design: pitch A "Foresight", round 4 and the side questions), IB1-IB5; handoff section 3.4 rows IB, section 3.5 row
 * S10, section 3.6 (normal 160k, heroic 250k, examiner 80k), section 3.7 (the Shadow Vault's solo lesson), section 3.8
 * (the fight belongs in the hall, section 7 #14).
 *
 * MotionTrack / PredictSpot (handoff section 3.2 kit #5, MotionSampler) and TrailRecorder (kit #6) are generic: they
 * live in the shared kit (DungeonKitLogic.h, moved by F-B4); this file names Illucia's tuning for them.
 *
 * Damage percentages are of the reference health row (normal 3,670 / heroic 4,120 non-tank at level 60).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_ILLUCIA_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_ILLUCIA_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include "SoloLessonLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace ScholoIllucia
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsIllucia;

    // Declared in apps/dbc-tools source/npcs/scholomance/lady_illucia_barov.py (same ids).
    enum IlluciaSpells : std::uint32_t
    {
        SPELL_IB_FORESIGHT_CAST     = 206315,   // IB1 the 1.5 s cast bar on the read player (names them)
        SPELL_IB_READ               = 206316,   // IB1 the read debuff for the chain (Mind Vision's eyes)
        SPELL_IB_FORESIGHT          = 206317,   // IB1 a marker's hit: resolve copy (Shadow)
        SPELL_IB_MEMORY             = 206318,   // IB2 the trail's 1 s tick: resolve copy (Shadow)
        SPELL_IB_FEAR               = 206319,   // IB3 the 1.5 s interruptible cast: 2 s fear, the scripted run
        SPELL_IB_FEAR_END           = 206320,   // IB3 the end marker's hit: resolve copy (Shadow)
        // 206321-206329 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_IB_FORESIGHT_CAST), "Illucia spells sit in her slice");
    static_assert(kSpellSlice.Contains(SPELL_IB_FEAR_END), "Illucia spells sit in her slice");

    // Registry tags (the build spec's IB numbers; the lesson's markers keep IB1's).
    enum IlluciaTags : std::uint32_t
    {
        TAG_FORESIGHT       = 1,    // IB1
        TAG_MEMORY          = 2,    // IB2 (heroic)
        TAG_FEAR_END        = 3,    // IB3
    };

    // The Graduate Examiner (S13, heroic hard mode only): this AI in examiner mode, bound to the entry
    // NPC_SC_EXAMINER_ILLUCIA (300554) by S13's data. Registered once wave C binds (kWaveCBound).
    char constexpr kExaminerScriptName[] = "npc_sc_examiner_illucia";
    std::uint32_t constexpr kExaminerHealth = 80000;        // handoff section 3.6, SC "Hard mode": 80k each

    // The examiner fights both mechanics at heroic values on any map (SC: "both mechanics at H values").
    constexpr bool HeroicValues(bool heroicMap, bool examiner)
    {
        return heroicMap || examiner;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC "Side questions" and the build spec table, approved 2026-10-31)
    // ----------------------------------------------------------------------------------------------------------------

    // IB1 Foresight: a 1.5 s cast names the read player(s); 4 yd markers, 1.5 s each, the first on the player, every
    // next one where they will be 1.5 s later (on them when still); 30% / 40% Shadow and Weakened per marker (ruling
    // 20, both difficulties). Normal 1 player x 3 markers, heroic 2 x 5. Any player, the tank included. 8 s, then
    // every 20 s.
    std::uint32_t constexpr kForesightFirstMs = 8000;
    std::uint32_t constexpr kForesightEveryMs = 20000;
    std::uint32_t constexpr kForesightCastMs = 1500;
    std::uint32_t constexpr kForesightMarkerMs = 1500;      // each marker's warning, and the lead of its prediction
    float constexpr kForesightRadius = 4.f;
    inline constexpr NH<float> kForesightPct{ 30.f, 40.f };
    inline constexpr NH<std::uint32_t> kForesightReads{ 1, 2 };
    inline constexpr NH<std::uint8_t> kForesightMarkers{ 3, 5 };

    // IB2 Memory trail (heroic): a read player's path during their chain lingers, 3 yd wide, 4 s, 10% Shadow a second
    // (a persistent Zone: no Weakened). Laid in kTrailSegmentYd pieces once the player is kTrailClearYd past a piece
    // (a piece never appears under its own maker); a piece's first tick lands a second after it appears.
    inline constexpr NH<bool> kMemoryTrail{ false, true };
    float constexpr kTrailWidth = 3.f;
    std::uint32_t constexpr kTrailLingerMs = 4000;
    std::uint32_t constexpr kTrailTickMs = 1000;
    float constexpr kTrailPct = 10.f;
    float constexpr kTrailSegmentYd = 4.f;
    float constexpr kTrailClearYd = 2.5f;                   // > kTrailWidth / 2: the maker stands off the piece
    float constexpr kTrailMaxStepYd = 12.f;                 // farther between two 200 ms samples: a teleport or a
                                                            // knockback; the trail starts over
    static_assert(kTrailClearYd > kTrailWidth / 2.f, "a new trail piece never lies under the player who made it");

    // IB3 Fear: a 1.5 s interruptible cast on a random non-tank not being read; a 2 s fear (the shared loss of control
    // limit; stock Fear 12542 was 4 s), a scripted straight run away from her; a 4 yd marker lands at the run's end as
    // the fear ends: 15% (no Weakened: the terrified player could not dodge) / 50% (heroic expects the interrupt or
    // the dispel; no Weakened, ruling 21). 18 s, every 20 s (between Foresights).
    std::uint32_t constexpr kFearFirstMs = 18000;
    std::uint32_t constexpr kFearEveryMs = 20000;
    std::uint32_t constexpr kFearCastMs = 1500;
    std::uint32_t constexpr kFearMs = 2000;
    float constexpr kFearRadius = 4.f;
    inline constexpr NH<float> kFearEndPct{ 15.f, 50.f };
    float constexpr kFearRange = 40.f;                      // the hall: the gate end is 32 yd from her step-out point
    float constexpr kFearMaxRunYd = 20.f;                   // a sprinting player still stops in the hall

    // IB4 Shadow Shock (stock 19460) on the tank: 1 to 2 s, then every 10 s (the stock timers).
    std::uint32_t constexpr kShadowShockFirstMinMs = 1000;
    std::uint32_t constexpr kShadowShockFirstMaxMs = 2000;
    std::uint32_t constexpr kShadowShockEveryMs = 10000;
    // IB5 Curse of Agony (stock 18266) on a random player in reach and in sight (the spell's 30 yd): 1 to 10 s, then
    // every 14 to 24 s (the stock timers).
    float constexpr kCurseRange = 30.f;
    std::uint32_t constexpr kCurseFirstMinMs = 1000;
    std::uint32_t constexpr kCurseFirstMaxMs = 10000;
    std::uint32_t constexpr kCurseEveryMinMs = 14000;
    std::uint32_t constexpr kCurseEveryMaxMs = 24000;

    // Melee: DamageModifier 3.5 on normal (the stock value, set by the DT file); heroic is the heroic template's
    // (WP-T).

    // The Shadow Vault (handoff section 3.8, section 7 #14): her inner room (x 257.5 to 273) joins the hall through a
    // 4 to 5 yd neck (x 251.5 to 257.5). Pulled in there, she steps out to ScholomanceRework::kIlluciaHallPoint before
    // she fights; a step that has not arrived after kStepOutTimeoutMs gives up and she fights where she is.
    float constexpr kInnerRoomMinX = 251.5f;
    std::uint32_t constexpr kStepOutTimeoutMs = 8000;

    // She stands in her inner room or its neck: she steps out to the hall on the pull.
    constexpr bool InInnerRoom(Vec2 p)
    {
        return p.x >= kInnerRoomMinX;
    }

    // The Shadow Vault's solo lesson (SC 2960-2971, handoff section 3.7): the vault reads the lone student, one
    // Foresight chain of 3 / 5 markers (no Memory trail: the SC lesson table names only the chain); any marker hit
    // fails it (15% / 25% plus Weakened, SoloLessonLogic.h). The read debuff goes on at the landing and the first
    // marker appears kLessonReadAtMs later (her cast's length), so the chain ends 6 s / 9 s in, inside the 15 s.
    std::uint32_t constexpr kLessonReadAtMs = 1500;
    inline constexpr NH<std::uint8_t> kLessonMarkers{ 3, 5 };

    constexpr float LessonMarkerPct(bool heroic)
    {
        return ScholomanceRework::LessonFailurePct(heroic);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). A beat that comes due
    // while she casts stays due until the cast ends.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        Foresight = 0,
        Fear = 1,
        ShadowShock = 2,
        Curse = 3,
    };
    std::size_t constexpr kBeatCount = 4;
    std::uint32_t constexpr kRetryMs = 2000;                // no target, or the cast failed: try again this soon

    struct Timeline
    {
        std::uint32_t now = 0;                              // ms since the pull
        std::array<std::uint32_t, kBeatCount> next{ { kForesightFirstMs, kFearFirstMs, kShadowShockFirstMinMs,
            kCurseFirstMinMs } };

        // The stock spells' first casts are random inside their windows: the caller passes its rolls.
        void Start(std::uint32_t shadowShockFirst, std::uint32_t curseFirst)
        {
            now = 0;
            next = { { kForesightFirstMs, kFearFirstMs, shadowShockFirst, curseFirst } };
        }

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        bool Due(Beat b) const
        {
            return now >= next[static_cast<std::size_t>(b)];
        }

        // Fired: the next one is `every` from now.
        void Done(Beat b, std::uint32_t every)
        {
            next[static_cast<std::size_t>(b)] = now + every;
        }

        void Retry(Beat b)
        {
            next[static_cast<std::size_t>(b)] = now + kRetryMs;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // IB1: one read player's chain, on the chain engine's own clock
    // ----------------------------------------------------------------------------------------------------------------

    // Marker k (0-based) is placed at start + k x interval and lands one interval later, as marker k + 1 is placed;
    // the chain ends as its last marker lands.
    struct ChainSchedule
    {
        std::uint32_t start = 0;
        std::uint32_t interval = kForesightMarkerMs;
        std::uint8_t total = 0;
        std::uint8_t placed = 0;

        // The next marker should be placed now.
        bool PlaceDue(std::uint32_t now) const
        {
            return placed < total && now >= start + std::uint32_t(placed) * interval;
        }

        std::uint32_t EndAt() const
        {
            return start + std::uint32_t(total) * interval;
        }

        bool Ended(std::uint32_t now) const
        {
            return placed >= total && now >= EndAt();
        }

        // The first marker goes on the player, every later one where they are going.
        bool NextIsPredicted() const
        {
            return placed > 0;
        }
    };

    // The read debuff's length: the cast plus the chain (the AI removes it when the chain ends).
    constexpr std::uint32_t ReadAuraMs(std::uint8_t markers)
    {
        return kForesightCastMs + std::uint32_t(markers) * kForesightMarkerMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The motion track, its prediction and the Memory trail recorder live in the shared kit (DungeonKitLogic.h:
    // MotionTrack, PredictSpot, TrailRecorder); Illucia samples every kSampleEveryMs.
    // ----------------------------------------------------------------------------------------------------------------

    using DungeonKit::MotionTrack;
    using DungeonKit::PredictSpot;
    using DungeonKit::Prediction;
    using DungeonKit::TrailRecorder;
    using DungeonKit::TrailSegment;
    std::uint32_t constexpr kSampleEveryMs = DungeonKit::kMotionSampleEveryMs;

    // The Memory trail's recorder: kTrailSegmentYd pieces, released kTrailClearYd behind the player, restarted by a
    // jump over kTrailMaxStepYd.
    inline TrailRecorder MemoryTrailRecorder()
    {
        return TrailRecorder(kTrailSegmentYd, kTrailClearYd, kTrailMaxStepYd);
    }

    // The trail pieces one read player keeps alive at once: one every kTrailSegmentYd at `speed` yd/s, each living
    // kTrailLingerMs (the registry budget: heroic, two players at 7 yd/s, 7 each).
    inline std::uint32_t PeakTrailPieces(float speed, std::uint32_t lingerMs = kTrailLingerMs,
        float segment = kTrailSegmentYd)
    {
        if (speed <= 0.f || segment <= 0.f)
            return 0;
        return std::uint32_t(std::ceil(speed / segment * float(lingerMs) / 1000.f));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IB3: the Fear's straight run
    // ----------------------------------------------------------------------------------------------------------------

    // The run's length: 2 s at the player's run speed, at most kFearMaxRunYd.
    inline float FearRunYd(float runSpeed, std::uint32_t fearMs = kFearMs)
    {
        return std::clamp(runSpeed * float(fearMs) / 1000.f, 0.f, kFearMaxRunYd);
    }

    // The direction of the run: straight away from her; a player on top of her runs along her facing.
    inline float FearRunBearing(Vec2 caster, Vec2 target, float casterFacing)
    {
        if (DungeonKit::Distance(caster, target) < 0.2f)
            return casterFacing;
        return DungeonKit::BearingTo(caster, target);
    }
}

#endif
