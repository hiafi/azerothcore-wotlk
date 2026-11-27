/*
 * mod-dungeon-bosses, Gnomeregan D1: Techbot (301105), the pure, host-testable part (no engine headers). Build spec:
 * SP 525-583 (TB1-TB9), design SP 375-524 (rulings 9-13, 51, 54, 61); handoff section 3.5 row D1 and its kick and
 * dispel table, sections 3.6, 3.8, 3.9 rows 1-2, section 7 #13 A, #14 A, #36-#38 A, section 10. Tested by
 * tests/gnomer_techbot_test.cpp; the DT test (apps/dbc-tools lib/test_gnomeregan_techbot.py) pins the spell ids, the
 * text groups and every number the data repeats against this file.
 *
 * Every spell sits in kSpellsTechbot (214300-214339). Health is GnomereganRework.h Health (never restated here).
 * The Duplicator machine's pure half (GnomereganMachines.h, section 3.2 item 7) is DupRule / DupClock below: the boss
 * and the hard mode (D6Ha MT16, the bombs) share it.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_TECHBOT_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_TECHBOT_LOGIC_H

#include "DungeonKitMath.h"
#include "GnomereganRework.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace GnomerTechbot
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsTechbot;

    // apps/dbc-tools source/npcs/gnomeregan/techbot.py declares each (same ids; the DT test diffs them).
    enum TechbotSpells : std::uint32_t
    {
        SPELL_LAG_SPIKE             = 214300,   // TB1 resolve copy (Fire), 40%, Weakened
        SPELL_LAG                   = 214301,   // TB1 the lag look on the picked player (SV 68), a DUMMY aura
        SPELL_DUPLICATION           = 214302,   // TB3 normal: the bug's 3 s bar (Nature, kickable); its aura marks done
        SPELL_DUPLICATION_H         = 214303,   // TB3 heroic: the 2 s bar
        SPELL_PATCH                 = 214304,   // TB4 normal: the 8 s download (Arcane, kickable)
        SPELL_PATCH_H               = 214305,   // TB4 heroic: the 6 s download
        SPELL_SAFE_MODE             = 214306,   // TB5 +25% damage taken while the bar runs (SV 37)
        SPELL_SAFE_MODE_START       = 214307,   // TB5 look, once at the bar's start (SV 2956)
        SPELL_PATCH_DONE            = 214308,   // TB4 look as the patch lands (SV 2074)
        SPELL_VERSION               = 214309,   // TB4 heroic: +5% damage done a stack (the amount is the script's)
        SPELL_RUBBER_BAND           = 214310,   // TB6 heroic: the carrier's mark until the snap (SV 68)
        SPELL_SAVE_POINT            = 214311,   // TB6 look: the save point is set (SV 2046, the light pillar)
        SPELL_SNAP_BACK             = 214312,   // TB6 look on the carrier at the snap (SV 263)
        SPELL_RUBBER_SPIKE          = 214313,   // TB6 resolve copy (Arcane), 60%, Weakened
        SPELL_SAVE_POINT_BURST      = 214314,   // TB6 resolve copy (Arcane), 60% on everyone but the owner
        SPELL_BUG_ECHO              = 214315,   // TB7 resolve copy (Fire), 40%, Weakened
        SPELL_BATTLE_NET            = 214316,   // TB8 resolve copy (Nature), 20%, Weakened
        SPELL_BATTLE_NET_ROOT       = 214317,   // TB8 the rider: a 4 s root (Magic)
        SPELL_BATTLE_NET_THROW      = 214318,   // TB8 look: the thrown net (SV 683), boss to player
        SPELL_BUG_SPAWN             = 214319,   // TB2 / TB3 look as a bug rises (SV 2073)
        SPELL_SHUTDOWN              = 214320,   // TB9 the powered-down sparks on the body (SV 7867, death persistent)
        SPELL_AFTER_IMAGE           = 214321,   // TB1 / TB6 aura 247 (clone caster) + the ghost (SV 886)
        SPELL_LAG_SPIKE_LANDING     = 214322,   // TB1 / TB6 look where a spike lands (SV 2917), on the after-image
    };
    // 214323-214339 spare (released at the report).
    std::uint32_t constexpr kFirstSpell = SPELL_LAG_SPIKE;
    std::uint32_t constexpr kLastSpell = SPELL_LAG_SPIKE_LANDING;

    // creature_text groups (section 3.5 rule 35: 0-based as SP prints them; group 0 is the stock chatter, copied).
    enum TechbotTexts : std::uint8_t
    {
        SAY_CHATTER                 = 0,    // the 13 stock help desk lines (6231 group 0), Say
        EMOTE_LAG                   = 1,    // "$n's connection is unstable." (type 41)
        YELL_PATCH                  = 2,    // "Downloading patch. Please do not turn off your Techbot."
        YELL_PATCH_FIXED            = 3,    // "Patch complete. Known issues resolved. ..." (bugs deleted)
        YELL_PATCH_CLEAN            = 4,    // "No known issues found... zzzttt!" (no bug)
        YELL_SHUTDOWN               = 5,    // "Shutting down. Thank you for contacting Technical Support. ..."
        EMOTE_RUBBER_BAND           = 6,    // "$n is rubber-banding!" (heroic, type 41)
    };
    std::uint8_t constexpr EMOTE_DUPLICATE = 0;     // Dupe Bug 301106 group 0: "%s begins to duplicate!" (type 41)

    // Registry tags: the drill gnomeregan-shapes keeps the same table (BM MechanicDrill.h kGnTag*, Techbot 1-19;
    // LESSONS A.3 #4). 10-12 are the drill's group tags for the casts (no registry tag here).
    enum TechbotTags : std::uint32_t
    {
        TAG_LAG_SPIKE               = 1,
        TAG_RUBBER_RUN_OUT          = 2,
        TAG_SAVE_POINT              = 3,
        TAG_RUBBER_SPIKE            = 4,
        TAG_BUG_ECHO                = 5,
        TAG_BATTLE_NET              = 6,
    };

    // Bot priorities (the descriptor; BM MechanicDescriptor.h: higher first, 0 = never kick).
    std::uint8_t constexpr kKickDuplication = 3;
    std::uint8_t constexpr kKickPatch = 2;
    std::uint8_t constexpr kNeverKick = 0;
    std::int8_t constexpr kKillCastingBug = 2;
    std::int8_t constexpr kKillBug = 1;
    std::uint8_t constexpr kDispelNet = 2;

    // `.dbtest gnomer techbot <mechanic>` (DoAction) and its reads (GetData).
    enum TechbotTestActions : std::int32_t
    {
        ACTION_TEST_LAG             = 1,    // Lag Spike (normal) or Rubber Band (heroic) now
        ACTION_TEST_BUG             = 2,    // a Dupe Bug now (the normal cap still holds)
        ACTION_TEST_PATCH           = 3,    // Patch now (when not casting)
        ACTION_TEST_NET             = 4,    // Battle Net now (heroic)
    };
    enum TechbotTestData : std::uint32_t
    {
        DATA_TEST_ENGAGED           = 1,
        DATA_TEST_BUGS              = 2,
        DATA_TEST_VERSION           = 3,
        DATA_TEST_PATCHES           = 4,
        DATA_TEST_SPIKES            = 5,
    };

    // ---------------------------------------------------------------------------------------------------------------
    // Tuning (section 3.5 rule 24: every percent a constant, every timer named, the 1.5 s warning floor asserted).
    // Damage is a percent of the reference row (90:28 normal, 90h:60 heroic), the tank row on the tank (rule 17).
    // "(guess)" = an unruled starting value of SP's Build spec (gap 5; section 7 #37 A: built as written).
    // ---------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // TB1 Lag Spike (normal; heroic replaces it with TB6).
        inline constexpr std::uint32_t kLagFirstMs = 8000;              // (guess)
        inline constexpr std::uint32_t kLagEveryMs = 15000;
        inline constexpr std::uint32_t kLagWarnMs = 2000;
        inline constexpr float kLagRadiusYd = 5.f;
        inline constexpr float kLagPct = 40.f;

        // TB2 Dupe Bugs: one at the boss every 10 s / 8 s, 3 yd apart (section 7 #38 a A); normal cap 8 alive.
        inline constexpr NH<std::uint32_t> kBugFirstMs{ 10000, 8000 };
        inline constexpr NH<std::uint32_t> kBugEveryMs{ 10000, 8000 };
        inline constexpr NH<std::uint32_t> kBugCap{ 8, 0 };             // 0: no cap (ruling 12, rule 23)
        // STAGE-R-1-A DQ3: heroic's technical ceiling (a server safety net far above play, not a design cap: ruling
        // 12 stands). A group this far behind has wiped; the ceiling only stops a kite or a feign from growing the
        // bugs (and their echo circles) without end. Logged when hit.
        inline constexpr std::uint32_t kBugSafetyCeiling = 64;
        inline constexpr float kBugRiseYd = 3.f;                        // from the boss
        inline constexpr float kBugApartYd = 3.f;                       // from any other bug
        inline constexpr std::uint32_t kBugRiseTries = 12;              // 30 degree steps round the boss
        inline constexpr std::uint32_t kBugCorpseMs = 5000;
        inline constexpr float kCopyOffsetYd = 1.f;                     // the copy rises beside its source

        // TB3 Duplication (rulings 51, 54): normal once at 9 s of life, 3 s bar; heroic every 7 s of life, 2 s bar.
        inline constexpr NH<std::uint32_t> kDupCastMs{ 3000, 2000 };
        inline constexpr NH<std::uint32_t> kDupFirstMs{ 9000, 7000 };
        inline constexpr NH<std::uint32_t> kDupRepeatMs{ 0, 7000 };     // 0: once per bug
        inline constexpr std::uint32_t kDupRetryMs = 1000;              // a refused start (stunned, silenced) retries
        inline constexpr std::uint32_t kDupDoneSlackMs = 250;           // completion judged within a tick of the end

        // TB4 Patch: Backup Restore; TB5 Safe Mode.
        inline constexpr NH<std::uint32_t> kPatchFirstMs{ 45000, 35000 };
        inline constexpr NH<std::uint32_t> kPatchEveryMs{ 45000, 35000 };
        inline constexpr NH<std::uint32_t> kPatchCastMs{ 8000, 6000 };
        inline constexpr std::uint32_t kPatchRetryMs = 1000;            // a refused bar (an Arcane lock) retries
        inline constexpr NH<float> kPatchHealPctPerBug{ 3.f, 4.f };     // of his maximum health
        inline constexpr std::int32_t kSafeModeTakenPct = 25;           // both difficulties
        inline constexpr float kVersionDonePctPerStack = 5.f;           // heroic, no cap, the rest of the fight
        inline constexpr std::uint32_t kVersionShownCap = 255;          // the client counter (rule 25)
        inline constexpr std::uint32_t kReassertMs = 1000;              // rule 25: aura amounts every 1 s
        inline constexpr float kPatchBugRangeYd = 100.f;                // the kick condition: a bug alive in reach

        // TB6 Rubber Band (heroic): two players; the save point at 2 s, spikes at 2 s and 3.5 s (1.5 s each), the snap
        // at 5 s, just after the second spike has resolved (RB-29: no blink on the instant a ring resolves).
        inline constexpr std::uint32_t kBandFirstMs = 8000;             // (guess)
        inline constexpr std::uint32_t kBandEveryMs = 15000;            // (guess)
        inline constexpr std::uint32_t kBandCarriers = 2;
        inline constexpr std::uint32_t kBandSaveMs = 2000;
        inline constexpr std::uint32_t kBandSpikeOneMs = 2000;
        inline constexpr std::uint32_t kBandSpikeTwoMs = 3500;          // (guess)
        inline constexpr std::uint32_t kBandSpikeWarnMs = 1500;
        inline constexpr std::uint32_t kBandSnapMs = 5000;
        inline constexpr std::uint32_t kBandSnapAfterSpikeMs = 300;     // the snap waits for the second spike's resolve
        inline constexpr std::uint32_t kBandSnapAtMs = kBandSnapMs + kBandSnapAfterSpikeMs;
        inline constexpr std::uint32_t kBandBurstWarnMs = kBandSnapAtMs - kBandSaveMs;    // the burst lands at the snap
        inline constexpr float kBandRunOutYd = 6.f;
        inline constexpr float kBandSpikeYd = 5.f;
        inline constexpr float kBandSpikePct = 60.f;
        inline constexpr float kSavePointYd = 6.f;
        inline constexpr float kSavePointPct = 60.f;

        // TB7 bug echoes (heroic): one 4 yd circle at every living bug on each spike wave.
        inline constexpr std::uint32_t kEchoWarnMs = 2000;
        inline constexpr float kEchoRadiusYd = 4.f;
        inline constexpr float kEchoPct = 40.f;                         // (guess)

        // TB8 Battle Net (heroic).
        inline constexpr std::uint32_t kNetFirstMs = 20000;             // (guess)
        inline constexpr std::uint32_t kNetEveryMs = 25000;             // (guess)
        inline constexpr std::uint32_t kNetWarnMs = 1500;
        inline constexpr float kNetRadiusYd = 8.f;
        inline constexpr float kNetPct = 20.f;
        inline constexpr std::uint32_t kNetRootMs = 4000;

        // The stock chatter (6231 group 0), one line every 15 s in combat.
        inline constexpr std::uint32_t kChatterEveryMs = 15000;

        // TB9 the shutdown: the sparks on the body.
        inline constexpr std::uint32_t kShutdownSparksMs = 30000;

        // Picks: every random pick on the dish (rule 5) and within this of him.
        inline constexpr float kPickRangeYd = 60.f;
        inline constexpr std::uint32_t kPickPool = 40;
        inline constexpr std::uint32_t kEchoDespawnPadMs = 600;         // an after-image outlives its circle by this
        inline constexpr std::uint32_t kLandingLookLeadMs = 100;        // the landing look this early (the after-image)

        // The Dupe Bug: 300 / 4,000 (GnomereganRework.h Health::kDupeBug); melee about 3% of the tank row a swing
        // (DamageModifier 1.7 on the level 28 warrior row: 26.5-32.9 x 1.7, about 50 before armor; the DT pins it).
        inline constexpr float kBugMeleeTankPct = 3.f;
    }

    std::uint32_t constexpr kWarningFloorMs = GnomereganRework::kWarningFloorMs;
    static_assert(Tune::kLagWarnMs >= kWarningFloorMs, "SYS 4: Lag Spike's warning");
    static_assert(Tune::kBandSpikeWarnMs >= kWarningFloorMs, "SYS 4: the Rubber Band spikes' warning");
    static_assert(Tune::kBandBurstWarnMs >= kWarningFloorMs, "SYS 4: the save point's warning");
    static_assert(Tune::kEchoWarnMs >= kWarningFloorMs, "SYS 4: the bug echoes' warning");
    static_assert(Tune::kNetWarnMs >= kWarningFloorMs, "SYS 4: Battle Net's warning");
    // RB-29: a cadence at least the warning plus 0.5 s.
    static_assert(Tune::kLagEveryMs >= Tune::kLagWarnMs + 500, "RB-29");
    static_assert(Tune::kBandEveryMs >= Tune::kBandSnapAtMs + 500, "RB-29");
    static_assert(Tune::kNetEveryMs >= Tune::kNetWarnMs + 500, "RB-29");
    // The spikes chain 1.5 s apart, the second lands at 5 s and the snap comes after it.
    static_assert(Tune::kBandSpikeTwoMs - Tune::kBandSpikeOneMs == Tune::kBandSpikeWarnMs, "chained 1.5 s apart");
    static_assert(Tune::kBandSpikeTwoMs + Tune::kBandSpikeWarnMs == Tune::kBandSnapMs, "spike two lands at 5 s");
    static_assert(Tune::kBandSnapAtMs > Tune::kBandSpikeTwoMs + Tune::kBandSpikeWarnMs, "RB-29: the snap after it");
    static_assert(Tune::kBandSaveMs == Tune::kBandSpikeOneMs, "the save point and the first spike together");
    static_assert(kFirstSpell >= kSpellSlice.first && kLastSpell <= kSpellSlice.last, "the slice");

    // Heroic only? (TB6-TB8 and Version; TB1 is normal only.)
    inline bool LagSpikeOn(bool heroic) { return !heroic; }
    inline bool RubberBandOn(bool heroic) { return heroic; }
    inline bool BattleNetOn(bool heroic) { return heroic; }
    inline bool VersionOn(bool heroic) { return heroic; }

    inline std::uint32_t DuplicationSpell(bool heroic) { return heroic ? SPELL_DUPLICATION_H : SPELL_DUPLICATION; }
    inline std::uint32_t PatchSpell(bool heroic) { return heroic ? SPELL_PATCH_H : SPELL_PATCH; }

    // ---------------------------------------------------------------------------------------------------------------
    // Damage: heroic Version stacks raise his damage done (+5% a stack, ruling 12). His registry hits ignore caster
    // modifiers (rule 2), so the script scales their percent itself; the aura raises his melee.
    // ---------------------------------------------------------------------------------------------------------------
    inline float VersionMultiplier(std::uint32_t versions)
    {
        return 1.f + Tune::kVersionDonePctPerStack * float(versions) / 100.f;
    }

    inline float ScaledPct(float pct, std::uint32_t versions)
    {
        return pct * VersionMultiplier(versions);
    }

    // The Version aura: the amount (percent done) and the stacks the client shows.
    inline std::int32_t VersionAuraAmount(std::uint32_t versions)
    {
        return std::int32_t(std::lround(Tune::kVersionDonePctPerStack * float(versions)));
    }

    inline std::uint32_t VersionShownStacks(std::uint32_t versions)
    {
        return std::min(versions, Tune::kVersionShownCap);
    }

    // TB4: the heal of a completed Patch, `bugs` deleted.
    inline std::uint32_t PatchHeal(std::uint32_t maxHealth, std::uint32_t bugs, bool heroic)
    {
        double const pct = double(Tune::kPatchHealPctPerBug.Get(heroic)) * double(bugs);
        return std::uint32_t(std::llround(double(maxHealth) * pct / 100.0));
    }

    // TB2 / TB3: the most bugs alive at once: normal's cap of 8, heroic's technical ceiling (DQ3).
    inline std::uint32_t BugLimit(bool heroic)
    {
        std::uint32_t const cap = Tune::kBugCap.Get(heroic);
        return cap ? cap : Tune::kBugSafetyCeiling;
    }

    // TB2: a bug rises now unless the limit is reached. `casting` counts the Duplication bars in flight: each is a bug
    // already on its way (R-1-A m1: without them two bars at 7 alive ended at 9).
    inline bool BugMayRise(std::uint32_t alive, bool heroic, std::uint32_t casting = 0)
    {
        return alive + casting < BugLimit(heroic);
    }

    // TB2 (section 7 #38 a A): the rise point, 3 yd from the boss and 3 yd from every other bug, on the floor
    // (`onFloor`). The first of 12 bearings 30 degrees apart from the boss's facing that fits; none fits: the boss's
    // own spot.
    template <class OnFloor>
    Vec2 RisePoint(Vec2 boss, float facing, std::vector<Vec2> const& bugs, OnFloor&& onFloor)
    {
        float constexpr kStep = 6.28318530718f / float(Tune::kBugRiseTries);
        for (std::uint32_t i = 0; i < Tune::kBugRiseTries; ++i)
        {
            float const a = facing + kStep * float(i);
            Vec2 const p{ boss.x + Tune::kBugRiseYd * std::cos(a), boss.y + Tune::kBugRiseYd * std::sin(a) };
            if (!onFloor(p))
                continue;
            bool clear = true;
            for (Vec2 const& b : bugs)
                if (DungeonKit::Distance(p, b) < Tune::kBugApartYd - 0.01f)
                {
                    clear = false;
                    break;
                }
            if (clear)
                return p;
        }
        return boss;
    }

    // ---------------------------------------------------------------------------------------------------------------
    // The Duplicator's pure half (GnomereganMachines.h DuplicatorSpec): one clock per tracked unit.
    // ---------------------------------------------------------------------------------------------------------------
    struct DupRule
    {
        std::uint32_t castMs = 3000;
        std::uint32_t firstAfterMs = 9000;
        std::uint32_t repeatMs = 0;         // 0: once per unit
        std::uint32_t capAlive = 0;         // 0: no cap
    };

    // Techbot's bugs on each difficulty (the hard mode passes its own numbers through DuplicatorSpec).
    inline DupRule BugRule(bool heroic)
    {
        DupRule r;
        r.castMs = Tune::kDupCastMs.Get(heroic);
        r.firstAfterMs = Tune::kDupFirstMs.Get(heroic);
        r.repeatMs = Tune::kDupRepeatMs.Get(heroic);
        r.capAlive = BugLimit(heroic);
        return r;
    }

    struct DupClock
    {
        std::uint32_t lifeMs = 0;
        std::uint32_t nextDueMs = 0;        // the life time of the next start
        std::uint32_t starts = 0;
        std::uint32_t copies = 0;
        bool casting = false;
        bool spent = false;                 // a once-only unit whose one cast ended (landed or stopped)
    };

    inline DupClock StartClock(DupRule const& r)
    {
        DupClock c;
        c.nextDueMs = r.firstAfterMs;
        return c;
    }

    // A due cast starts now: not casting, not spent, due, and under the cap (a due cast waits at the cap). `casting`
    // counts the bars in flight on other units: each is a copy on its way (R-1-A m1).
    inline bool DueToStart(DupClock const& c, DupRule const& r, std::uint32_t alive, std::uint32_t casting = 0)
    {
        if (c.casting || c.spent || c.lifeMs < c.nextDueMs)
            return false;
        return r.capAlive == 0 || alive + casting < r.capAlive;
    }

    // A completed bar's copy rises only under the cap (a last guard: the start gate already counts the bars in
    // flight; `alive` is before the copy).
    inline bool CopyFits(DupRule const& r, std::uint32_t alive)
    {
        return r.capAlive == 0 || alive < r.capAlive;
    }

    // A copy's clock (STAGE-R-1-A DQ1): a once-only rule's copies never duplicate (normal Dupe Bugs: SP's failing path
    // math, 4 rises plus 3 copies by 45 s); a repeating rule's copies run their own clock from the copy (heroic bugs,
    // the hard mode's bombs).
    inline DupClock CopyClock(DupRule const& r)
    {
        DupClock c = StartClock(r);
        c.spent = r.repeatMs == 0;
        return c;
    }

    inline void OnCastStarted(DupClock& c)
    {
        c.casting = true;
        ++c.starts;
    }

    // The start was refused (stunned, silenced, a school lock): look again in a second; the cast is not lost.
    inline void OnCastRefused(DupClock& c, std::uint32_t retryMs = Tune::kDupRetryMs)
    {
        c.nextDueMs = c.lifeMs + retryMs;
    }

    // The bar ended: `completed` (a copy rises) or stopped (a stun or a kick: the reward, that cast is lost). Once-only
    // units are spent either way; repeating ones are due again a period after this due time, never sooner than half a
    // period from now (RB-17: no beat starves another).
    inline void OnCastEnded(DupClock& c, DupRule const& r, bool completed)
    {
        c.casting = false;
        if (completed)
            ++c.copies;
        if (r.repeatMs == 0)
        {
            c.spent = true;
            return;
        }
        c.nextDueMs = std::max(c.nextDueMs + r.repeatMs, c.lifeMs + r.repeatMs / 2);
    }

    // The bar left the unit: it completed when its aura marks it (the bar applies a short aura of itself on its
    // caster). `barMarks` (the bar spell applies an aura): the marker alone judges, so a kick or a stun in the bar's
    // last moments is a stop (R-1-A m2). A bar without its own aura falls back on the remaining time last seen
    // fitting in the time since (within the slack).
    inline bool CastCompleted(bool markerAura, std::int32_t lastRemainingMs, std::uint32_t sinceSeenMs,
        bool barMarks = false, std::uint32_t slackMs = Tune::kDupDoneSlackMs)
    {
        if (markerAura || barMarks)
            return markerAura;
        return lastRemainingMs <= std::int32_t(sinceSeenMs + slackMs);
    }

    // ---------------------------------------------------------------------------------------------------------------
    // The timeline (RB-17: max(due + period, now + period / 2)).
    // ---------------------------------------------------------------------------------------------------------------
    inline std::uint32_t NextDue(std::uint32_t due, std::uint32_t period, std::uint32_t now)
    {
        return std::max(due + period, now + period / 2);
    }

    // TB6: the Rubber Band's steps, by time since its start.
    enum class BandStep : std::uint8_t
    {
        None,
        Save,           // the save point and the first spike (and a bug echo wave)
        SpikeTwo,       // the second spike (and a bug echo wave)
        Snap,           // the carriers snap back
        Done
    };

    struct BandProgress
    {
        bool saved = false;
        bool spikeTwo = false;
        bool snapped = false;
    };

    // The next step due at `sinceStartMs` (one per call, in order).
    inline BandStep DueBandStep(BandProgress const& p, std::uint32_t sinceStartMs)
    {
        if (!p.saved)
            return sinceStartMs >= Tune::kBandSaveMs ? BandStep::Save : BandStep::None;
        if (!p.spikeTwo)
            return sinceStartMs >= Tune::kBandSpikeTwoMs ? BandStep::SpikeTwo : BandStep::None;
        if (!p.snapped)
            return sinceStartMs >= Tune::kBandSnapAtMs ? BandStep::Snap : BandStep::None;
        return BandStep::Done;
    }

    inline void MarkBandStep(BandProgress& p, BandStep step)
    {
        switch (step)
        {
            case BandStep::Save:
                p.saved = true;
                break;
            case BandStep::SpikeTwo:
                p.spikeTwo = true;
                break;
            case BandStep::Snap:
                p.snapped = true;
                break;
            default:
                break;
        }
    }
}

#endif
