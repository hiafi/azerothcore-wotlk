/*
 * mod-dungeon-bosses, Scarlet Monastery D14H: High Inquisitor Whitemane's hard mode, The Truth (heroic only), the pure,
 * host-testable part (no engine headers). Build spec: docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor
 * Fairbanks" (the Torch), "Hard mode (approved 2026-11-19, pitch B)" and "Hard mode: The Truth" (HM0-HM5, the rows,
 * the texts); handoff section 3.7, 3.5 row D14H, section 7 #21 A (the Torch's timing), #33 A (the spots, the Verdict's
 * far end) and #16 A (the Ashbringer sweep leaves the new units out: S0's AshbringerSweeps). Tested by
 * tests/sm_whitemane_hard_mode_test.cpp; the spell ids and numbers are pinned against apps/dbc-tools
 * source/npcs/scarlet_monastery/whitemane_hard_mode.py by lib/test_scarlet_monastery_whitemane_hard_mode.py.
 *
 * The engine side is whitemane_hard_mode.cpp: the Torch (go_sm_torch), the vigil Fairbanks (npc_sm_vigil_fairbanks),
 * the spirit of Alexandros (npc_sm_alexandros_spirit) and the per-pull hard mode on D14's WhitemaneFight.h hooks.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_WHITEMANE_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_WHITEMANE_HARD_MODE_LOGIC_H

#include "ScarletMonasteryRework.h"
#include "WhitemaneLogic.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace SmTheTruth
{
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;
    using ScarletMonasteryRework::Point4;
    using SmWhitemane::PairStage;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsTheTruth;

    enum TheTruthSpells : std::uint32_t
    {
        SPELL_TT_TORCH_FEAR         = kSpellSlice.first + 0,    // HM0 the stock Fairbanks fears the door's players 5 s
        SPELL_TT_TELEPORT_OUT       = kSpellSlice.first + 1,    // HM0 he leaves (a 3 s look aura: "leaving")
        SPELL_TT_TELEPORT_IN        = kSpellSlice.first + 2,    // HM0 the vigil Fairbanks appears beside her
        SPELL_TT_WARD               = kSpellSlice.first + 3,    // HM1 Inquisitor's Ward's look on the pair
        SPELL_TT_CURSE              = kSpellSlice.first + 4,    // HM1a Curse of Blood: 2 s cast, a Curse, 12 s DoT
        SPELL_TT_CURSE_MARK         = kSpellSlice.first + 5,    // HM1a the red mark while the curse lasts (look)
        SPELL_TT_SHIELD             = kSpellSlice.first + 6,    // HM1b his Power Word: Shield (purgeable)
        SPELL_TT_HEAL               = kSpellSlice.first + 7,    // HM1c his 3 s Heal (interruptible)
        SPELL_TT_SPIRIT_GLOW        = kSpellSlice.first + 8,    // HM2 the spirit's glow (look)
        SPELL_TT_LIGHT_CAST         = kSpellSlice.first + 9,    // HM3 the spirit marks the light (look)
        SPELL_TT_LIGHT_HIT          = kSpellSlice.first + 10,   // HM3 the light's hit (resolve copy, Holy)
        SPELL_TT_LIGHT_PILLAR       = kSpellSlice.first + 11,   // HM3 the falling-light pillar (look)
        SPELL_TT_VERDICT_RAISE      = kSpellSlice.first + 12,   // HM3a the spirit raises the Ashbringer (look)
        SPELL_TT_VERDICT_SWING      = kSpellSlice.first + 13,   // HM3a the swing along the line (missile look)
        SPELL_TT_VERDICT_HIT        = kSpellSlice.first + 14,   // HM3a the Verdict's hit (resolve copy, Holy)
        SPELL_TT_VERDICT_IMPACT     = kSpellSlice.first + 15,   // HM3a the impact on Renault and Whitemane (look)
        SPELL_TT_SHAME              = kSpellSlice.first + 16,   // HM2 / HM3 Renault kneels in shame (look)
        SPELL_TT_SPIRIT_FADE        = kSpellSlice.first + 17,   // HM5 the spirit fades (look)
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_TT_SPIRIT_FADE;
    static_assert(kSpellSlice.Contains(kLastSpell), "the Truth's spells stay in its slice");

    // creature_text groups (ScarletMonasteryRework.h kTextRanges: the vigil Fairbanks 0, the spirit 0-1 (group 2 is a
    // shared-file request: the range must grow to 0-2), Whitemane 6 (SmWhitemane::SAY_WHITEMANE_LIES), Mograine's
    // stock 4-5).
    enum VigilFairbanksTexts : std::uint8_t
    {
        SAY_FAIRBANKS_TRUTH     = 0,    // "Ask him... how his father died." (HM2, at his death)
    };
    enum SpiritTexts : std::uint8_t
    {
        SAY_SPIRIT_RENAULT      = 0,    // "Renault..." (HM2; Highlord Mograine 16062's line 0)
        SAY_SPIRIT_FORGIVEN     = 1,    // "You are forgiven..." (HM5; 16062's line 2)
        EMOTE_SPIRIT_RAISES     = 2,    // "%s raises the Ashbringer!" (HM3a, raid emote)
    };
    enum MograineTruthTexts : std::uint8_t
    {
        SAY_MOGRAINE_FATHER     = 4,    // stock "Father... But... How?" (HM2)
        SAY_MOGRAINE_FORGIVE    = 5,    // stock "Forgive me, father! Please..." (HM2)
    };

    // Registry tags (beside D14's 1-4 and D13's on the same owners).
    inline constexpr std::uint32_t TAG_TT_LIGHT = 21;           // HM3 the light (the non-tanks: Weakened)
    inline constexpr std::uint32_t TAG_TT_LIGHT_TANK = 22;      // HM3 the tank light (park; no Renault: Weakened)
    inline constexpr std::uint32_t TAG_TT_VERDICT = 23;         // HM3a

    // ----------------------------------------------------------------------------------------------------------------
    // HM0 the Torch (section 7 #21 A)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TorchAnswer : std::uint8_t
    {
        Stock,      // normal (or wave 2 unbound): the Torch opens the Secret Door as stock
        Trigger,    // heroic, the Last Stand DONE, Whitemane not pulled: HM0
        Refused,    // heroic, too early or too late: "The Torch will not move." and nothing happens
        AlreadyLit, // heroic, the hard mode is lit already: the door is open, nothing more
    };

    inline constexpr char const* TorchAnswerName(TorchAnswer a)
    {
        switch (a)
        {
            case TorchAnswer::Stock:      return "stock";
            case TorchAnswer::Trigger:    return "trigger";
            case TorchAnswer::Refused:    return "refused";
            case TorchAnswer::AlreadyLit: return "lit";
        }
        return "?";
    }

    // What a use of the Torch does. The instance still judges the flag itself (S0's TorchAllowed on SetData).
    inline constexpr TorchAnswer TorchAnswerFor(bool heroic, std::uint32_t lastStand, std::uint32_t whitemane,
        bool lit, bool wave2Bound = ScarletMonasteryRework::kWave2Bound)
    {
        if (!wave2Bound || !heroic)
            return TorchAnswer::Stock;
        if (lit)
            return TorchAnswer::AlreadyLit;
        return ScarletMonasteryRework::TorchAllowed(heroic, lastStand, whitemane, lit, wave2Bound)
            ? TorchAnswer::Trigger : TorchAnswer::Refused;
    }

    inline constexpr char const* kTorchRefusedText = "The Torch will not move.";

    inline constexpr std::uint32_t kFearMs = 5000;              // the stock Fairbanks's fear on the door's players
    inline constexpr float kFearRadiusYd = 30.f;                // from the Secret Door
    inline constexpr float kFearZBandYd = 10.f;
    inline constexpr std::uint32_t kLeaveMs = 2000;             // his teleport look, then he is gone
    inline constexpr std::uint32_t kLeaveLookMs = 3000;         // the "leaving" aura outlasts the despawn
    inline constexpr std::uint32_t kLockoutRespawnSeconds = 7 * 24 * 3600;   // gone for the lockout (a week)
    inline constexpr std::uint32_t kTorchPollMs = 1000;         // the Torch keeps its pulled state while lit
    inline constexpr std::uint32_t kIdlePollMs = 1000;          // the idle hook's own pace
    static_assert(kLeaveLookMs > kLeaveMs, "the idle hook never takes a leaving Fairbanks for a respawned one");

    // The Secret Door (GO 97700, guid 11876, FACTS-STOCK 3.3).
    inline constexpr Point3 kSecretDoor{ 1167.79f, 1347.26f, 31.55f };

    inline float Distance2d(Vec2 a, Vec2 b)
    {
        return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
    }

    // A player the stock Fairbanks's fear takes (within 30 yd of the Secret Door).
    inline bool InFearRange(Vec2 p, float z)
    {
        return Distance2d(p, kSecretDoor.XY()) <= kFearRadiusYd && std::fabs(z - kSecretDoor.z) <= kFearZBandYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The units and their places (section 7 #33 A)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kWhitemaneHealth = 340000;   // hard mode, set at the Torch and at every pull
    inline constexpr std::uint32_t kMograineHealth = 280000;    // at the rising (D14's RisenMaxHealth hook)
    inline constexpr std::uint32_t kFairbanksHealth = 130000;   // the vigil Fairbanks (his template; H's override)

    // The vigil Fairbanks kneels 4 yd beside her at the vigil, on the Secret Door's side (toward the south arm, his
    // room), facing Mograine's body as she does.
    inline constexpr float kVigilFairbanksBesideYd = 4.f;
    inline Point4 VigilFairbanksSpot()
    {
        Point4 const v = SmWhitemane::VigilSpot();
        return { v.x, v.y - kVigilFairbanksBesideYd, v.z, v.o };
    }
    inline constexpr float kVigilSearchYd = 60.f;               // his (re)find around her
    inline constexpr float kVigilPlacedYd = 3.f;                // farther than this from his spot: walked back

    // The stock Fairbanks's own weapon (creature_equip_template 4542: item 2182), in the vigil Fairbanks's hand.
    inline constexpr std::uint32_t kItemFairbanksWeapon = 2182;

    // The spirit's Corrupted Ashbringer (equipment of Highlord Mograine 16062; V's ITEM_ALEXANDROS_BLADE).
    inline constexpr std::uint32_t kItemAlexandrosBlade = 22709;

    // The spirit hovers over the altar platform (x 1151-1172), facing the nave and the crossing.
    inline constexpr float kPlatformTopZ = 34.3f;               // NAVMESH "Whitemane": the platform tops out at 34.3
    inline constexpr float kSpiritHoverYd = 2.5f;
    inline constexpr Point4 kSpiritSpot{ 1166.f, 1398.f, kPlatformTopZ + kSpiritHoverYd, DungeonKit::kPi };
    inline constexpr std::uint32_t kSpiritFadeMs = 4000;        // HM5: his line, the fade, then gone

    // ----------------------------------------------------------------------------------------------------------------
    // The phases
    // ----------------------------------------------------------------------------------------------------------------

    enum class Phase : std::uint8_t
    {
        One,        // HM1: from the pull to Fairbanks's death
        Truth,      // HM2: the transition (her kit held, Renault kneels)
        Two,        // HM3 / HM4: the father's judgment
    };

    inline constexpr char const* PhaseName(Phase p)
    {
        switch (p)
        {
            case Phase::One:   return "one";
            case Phase::Truth: return "truth";
            case Phase::Two:   return "two";
        }
        return "?";
    }

    // HM1 Inquisitor's Ward: while Fairbanks lives (phase 1) the pair takes 50% less damage.
    inline constexpr bool WardActive(Phase p)
    {
        return p == Phase::One;
    }
    inline constexpr std::uint32_t WardedDamage(std::uint32_t damage)
    {
        return damage - damage / 2;     // half, rounded up (a 1-point hit still lands)
    }

    // HM1 his kit (heroic values; the hard mode is heroic only). Times from the pull.
    inline constexpr std::uint32_t kShieldFirstMs = 3000;       // HM1b
    inline constexpr std::uint32_t kShieldEveryMs = 12000;
    inline constexpr float kShieldPct = 10.f;                   // of its target's maximum health
    inline constexpr std::uint32_t kShieldAuraMs = 30000;
    inline constexpr std::uint32_t kCurseFirstMs = 5000;        // HM1a
    inline constexpr std::uint32_t kCurseEveryMs = 15000;
    inline constexpr std::uint32_t kCurseCastMs = 2000;
    inline constexpr std::uint32_t kCurseTickMs = 1000;
    inline constexpr std::uint32_t kCurseMs = 12000;
    inline constexpr float kCursePct = 4.f;                     // of the reference row per second (the tank row)
    inline constexpr std::uint32_t kHealFirstMs = 10000;        // HM1c
    inline constexpr std::uint32_t kHealEveryMs = 20000;
    inline constexpr std::uint32_t kHealCastMs = 3000;
    inline constexpr std::uint32_t kHealPct = 15;               // of its target's maximum health
    inline constexpr float kCastRangeYd = 40.f;
    inline constexpr std::uint32_t kRetryMs = 1000;
    inline constexpr std::uint32_t kMarkPollMs = 500;           // the curse's mark follows the curse
    inline constexpr std::uint32_t kWardPollMs = 1000;          // the ward's look stays on the pair in phase 1

    // HM1d / HM4 (D14's tuning hooks). Phase 1: To Her Side every 20 s, the flare every 8 s; Seared 15 s throughout.
    inline constexpr std::uint32_t kLaneEveryPhaseOneMs = 20000;
    inline constexpr std::uint32_t kFlameEveryPhaseOneMs = 8000;
    inline constexpr std::uint32_t kSearedMs = 15000;
    inline constexpr std::uint32_t kHerSavePhaseTwoMs = 6000;   // HM4 her channel
    inline constexpr std::uint32_t kHisSavePhaseTwoMs = 4000;   // HM4 his channel
    inline constexpr std::uint32_t kStormEveryPhaseTwoMs = 10000;   // HM4 his Divine Storm, from the Truth
    static_assert(SmWhitemane::SearedFadesInTime(kSearedMs, kFlameEveryPhaseOneMs), "HM1d: 15 s against 8 s");
    static_assert(SmWhitemane::SearedFadesInTime(kSearedMs, SmWhitemane::kFlameEveryMs), "HM4: 15 s against 10 s");

    // `mograineFallen`: her channel over him (WM1a); else his over her (WM1b).
    inline constexpr std::optional<std::uint32_t> SaveWindowFor(Phase p, bool mograineFallen)
    {
        if (p == Phase::One)
            return std::nullopt;        // heroic 8 s / 5 s
        return mograineFallen ? kHerSavePhaseTwoMs : kHisSavePhaseTwoMs;
    }

    inline constexpr std::optional<std::uint32_t> LaneEveryFor(Phase p)
    {
        return p == Phase::One ? std::optional<std::uint32_t>(kLaneEveryPhaseOneMs) : std::nullopt;
    }

    inline constexpr std::optional<std::uint32_t> FlameEveryFor(Phase p)
    {
        return p == Phase::One ? std::optional<std::uint32_t>(kFlameEveryPhaseOneMs) : std::nullopt;
    }

    // The descriptor: Fairbanks first while he lives (above D14's pair 1, channeler 2, the tank's Mograine 3); his
    // Heal after her heroic Heal, before Holy Smite; the curse a decurse; both shields purges.
    inline constexpr std::int8_t kFairbanksTargetPriority = 5;
    inline constexpr std::uint8_t kFairbanksHealKickPriority = 3;
    inline constexpr std::uint8_t kCurseDispelPriority = 2;
    inline constexpr std::uint8_t kShieldPurgePriority = 2;
    static_assert(kFairbanksHealKickPriority < SmWhitemane::kHealKickPriority.heroic
        && kFairbanksHealKickPriority > SmWhitemane::kSmiteKickPriority, "his Heal after hers, before Holy Smite");

    // ----------------------------------------------------------------------------------------------------------------
    // HM2 the Truth (at Fairbanks's death)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kTruthMs = 3000;             // her kit held, Renault kneels (no mechanic fires)
    inline constexpr std::uint32_t kTruthSecondLineMs = 1500;   // Renault's second line
    inline constexpr std::uint32_t kSpiritFirstCastMs = 8000;   // the spirit's casts start at T + 8 s
    static_assert(kSpiritFirstCastMs > kTruthMs, "the father judges after the transition");
    static_assert(kStormEveryPhaseTwoMs > kTruthMs, "the first storm of phase 2 comes after the kneel");

    // ----------------------------------------------------------------------------------------------------------------
    // HM3 the father's judgment: every 8 s from T + 8 s, the light twice, then the Verdict (ruling 52)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kJudgmentEveryMs = 8000;
    inline constexpr std::uint32_t kVerdictEvery = 3;
    inline constexpr std::uint32_t kJudgmentGapMinMs = 4000;    // a delayed Verdict never crowds the next cast

    enum class Judgment : std::uint8_t
    {
        Light,
        Verdict,
    };

    inline constexpr char const* JudgmentName(Judgment j)
    {
        return j == Judgment::Verdict ? "verdict" : "light";
    }

    // The `n`th cast of phase 2 (0-based): every third is the Verdict.
    inline constexpr Judgment JudgmentFor(std::uint32_t n)
    {
        return n % kVerdictEvery == kVerdictEvery - 1 ? Judgment::Verdict : Judgment::Light;
    }

    // HM3 the light: a 6 yd circle at a random player's spot (tank included), 2.5 s marker.
    inline constexpr float kLightRadiusYd = 6.f;
    inline constexpr std::uint32_t kLightWarnMs = 2500;
    inline constexpr float kLightPct = 45.f;                    // + Weakened (the non-tanks)
    inline constexpr float kLightTankPct = 25.f;                // the tank holding Renault in it: no Weakened
    inline constexpr float kLightRenaultPct = 4.f;              // of his maximum health (ruling 53)
    inline constexpr std::uint32_t kLightKneelMs = 2000;
    inline constexpr float kZBandYd = 5.f;                      // Renault "in it": the altar steps are 1.5-3.5 yd up

    // HM3: "Weakened (players other than a tank holding Renault in it: a correctly done job)". The tank in the light
    // takes its 25% either way; Weakened too unless Renault stood (risen, not down) in the circle as it fell.
    inline constexpr bool LightWeakensTank(bool renaultInside)
    {
        return !renaultInside;
    }

    // HM3a the Verdict: a 6 yd line from the spirit through Renault to the far wall, 3.5 s marker.
    inline constexpr float kVerdictWidthYd = 6.f;
    inline constexpr std::uint32_t kVerdictWarnMs = 3500;
    inline constexpr float kVerdictPct = 55.f;                  // tank included, no Weakened (50% or more)
    inline constexpr float kVerdictRenaultPct = 6.f;            // of his maximum health (ruling 53)
    inline constexpr std::uint32_t kVerdictKneelMs = 3000;
    inline constexpr float kVerdictWhitemanePct = 5.f;          // of her maximum health; her cast breaks
    inline constexpr std::uint32_t kVerdictHoldGraceMs = 500;   // his root outlasts the marker by this much
    inline constexpr std::uint32_t kVerdictLaneWaitMs = 4000;   // a Verdict waits out a running To Her Side charge
    inline constexpr float kSwingSpeedYd = 60.f;                // the swing's missile (the DT spell's Speed)
    static_assert(kVerdictWarnMs + kVerdictHoldGraceMs < kJudgmentEveryMs, "the root ends before the next cast");
    static_assert(kLightWarnMs < kJudgmentGapMinMs && kVerdictWarnMs < kJudgmentGapMinMs, "one marker at a time");

    // The swing leaves this long before the line resolves, so the blade crosses the line as it lands.
    inline std::uint32_t SwingLeadMs(float lengthYd)
    {
        float const ms = std::max(0.f, lengthYd) / kSwingSpeedYd * 1000.f;
        return std::min(kVerdictWarnMs, static_cast<std::uint32_t>(ms));
    }

    // The fight's floor in the map plane (D14's nave, crossing with both arms and the altar platform).
    inline constexpr bool OnFloorPlane(Vec2 p)
    {
        for (SmWhitemane::Box const& b : SmWhitemane::kFloorBoxes)
            if (b.Contains(p))
                return true;
        return false;
    }

    struct LinePath
    {
        Vec2 from;
        Vec2 end;
        float facing = 0.f;
        float length = 0.f;
    };

    inline constexpr float kVerdictStepYd = 0.25f;
    inline constexpr float kVerdictInsetYd = 0.5f;
    inline constexpr float kVerdictMaxYd = 150.f;

    // HM3a: from the spirit through `through` to the floor's far edge (the nave's west wall about 94 yd off, or an
    // arm's end about 60 yd off: section 7 #33 A), `inset` short of it. A target on top of the spirit aims down the
    // nave.
    inline LinePath VerdictPathFor(Vec2 spirit, Vec2 through, float inset = kVerdictInsetYd)
    {
        LinePath path;
        path.from = spirit;
        path.end = spirit;
        path.facing = Distance2d(spirit, through) > 0.01f ? SmWhitemane::FacingTo(spirit, through) : DungeonKit::kPi;
        if (!OnFloorPlane(spirit))
            return path;
        float inside = 0.f;
        for (float d = kVerdictStepYd; d <= kVerdictMaxYd; d += kVerdictStepYd)
        {
            if (!OnFloorPlane(DungeonKit::Advance(spirit, path.facing, d)))
                break;
            inside = d;
        }
        path.length = std::max(0.f, inside - inset);
        path.end = DungeonKit::Advance(spirit, path.facing, path.length);
        return path;
    }

    // Inside the line (`halfWidth` either side, along its length).
    inline bool OnLine(Vec2 p, LinePath const& line, float halfWidth)
    {
        float const dx = p.x - line.from.x;
        float const dy = p.y - line.from.y;
        float const along = dx * std::cos(line.facing) + dy * std::sin(line.facing);
        float const across = -dx * std::sin(line.facing) + dy * std::cos(line.facing);
        return along >= 0.f && along <= line.length && std::fabs(across) <= halfWidth;
    }

    inline bool InCircle(Vec2 p, float z, Vec2 center, float centerZ, float radius)
    {
        return Distance2d(p, center) <= radius && std::fabs(z - centerZ) <= kZBandYd;
    }

    // Whitemane in the Verdict: hit (5%, her cast breaks) only while she stands or channels her save; a body (his save,
    // her vow spent) is skipped.
    inline constexpr bool VerdictTakesHer(PairStage stage)
    {
        return stage != PairStage::HisSave && stage != PairStage::HerSpent && stage != PairStage::Over;
    }

    // Renault's kneel in shame (the light, the Verdict, the Truth) only when nothing else drives him: not in a save
    // (down, or channeling Lay on Hands under D14's hold) and not in To Her Side (D14's hold and charge).
    inline constexpr bool KneelAllowed(bool saveInProgress, bool laneInProgress)
    {
        return !saveInProgress && !laneInProgress;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    struct PlayerCandidate
    {
        std::uint64_t id = 0;
        bool alive = true;
        bool usable = true;     // in range and in sight of the caster (the curse); always true for the light
    };

    // A random living usable candidate, tank included (the light, the curse). `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickAny(std::vector<PlayerCandidate> const& candidates, Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].alive && candidates[i].usable)
                pool.push_back(i);
        if (pool.empty())
            return std::nullopt;
        std::size_t k = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())));
        if (k >= pool.size())
            k = 0;
        return pool[k];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 20 (bot throughput, LESSONS 4.2-4.3): the hard mode's numbers at the spec's and the bots' group DPS
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kSpecGroupDps = 3774.f;              // hard mode effective (handoff 3.6)
    inline constexpr float kBotGroupDps = kSpecGroupDps / 2.f;  // about half the spec (LESSONS 4.2)

    // Seconds a group at `groupDps` needs for `health`.
    inline constexpr float KillSeconds(std::uint32_t health, float groupDps)
    {
        return groupDps <= 0.f ? 0.f : static_cast<float>(health) / groupDps;
    }
}

#endif
