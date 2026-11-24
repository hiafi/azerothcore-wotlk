/*
 * mod-dungeon-bosses, Scarlet Monastery D14: High Inquisitor Whitemane, with Mograine risen ("Till Death"), the pure,
 * host-testable part (no engine headers). Build spec: docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor
 * Whitemane, with Mograine risen" (WM0-WM6, LS5; normal and heroic), handoff section 3.5 row D14, section 3.6, section
 * 3.8 row D14 and section 7 #33 A (the vigil and the fight on the crossing before the altar). Tested by
 * tests/sm_whitemane_test.cpp; the spell ids and numbers are pinned against apps/dbc-tools
 * source/npcs/scarlet_monastery/whitemane.py by lib/test_scarlet_monastery_whitemane.py.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_WHITEMANE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_WHITEMANE_LOGIC_H

#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace SmWhitemane
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;
    using ScarletMonasteryRework::Point4;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsWhitemane;

    enum WhitemaneSpells : std::uint32_t
    {
        SPELL_WM_DEEP_SLEEP         = kSpellSlice.first + 0,    // WM1 the rising: 3 s sleep, damage wakes
        SPELL_WM_RAISE              = kSpellSlice.first + 1,    // WM1 the 2 s rising cast (Physical, must-play)
        SPELL_WM_RESURRECTION       = kSpellSlice.first + 2,    // WM1a her save channel (Physical, not interruptible)
        SPELL_WM_RISE_LOOK          = kSpellSlice.first + 3,    // WM1 / WM1a Mograine rises (SV 1443)
        SPELL_WM_LAY_ON_HANDS       = kSpellSlice.first + 4,    // WM1b his save channel (Physical, not interruptible)
        SPELL_WM_LAY_ON_HANDS_LOOK  = kSpellSlice.first + 5,    // WM1b she rises (SV 132)
        SPELL_WM_LANE_HIT           = kSpellSlice.first + 6,    // WM2 the lane's hit (resolve copy, Physical)
        SPELL_WM_CHARGE_LOOK        = kSpellSlice.first + 7,    // WM2 his charge (SV 867)
        SPELL_WM_BODY_SHIELD        = kSpellSlice.first + 8,    // WM2a heroic: 6 s, half her damage goes to him
        SPELL_WM_PENANCE_MARK       = kSpellSlice.first + 9,    // WM3 the 3 s mark on a player
        SPELL_WM_PENANCE_HIT        = kSpellSlice.first + 10,   // WM3 the pillar on the others (resolve copy, Holy)
        SPELL_WM_PENANCE_STRIKE     = kSpellSlice.first + 11,   // WM3 the marked player's own hit (script)
        SPELL_WM_PENANCE_PILLAR     = kSpellSlice.first + 12,   // WM3 the pillar's look on a marked player
        SPELL_WM_PENANCE_HANDS      = kSpellSlice.first + 13,   // WM3 her hands as she marks (SV 10980)
        SPELL_WM_HEAL               = kSpellSlice.first + 14,   // WM4 the 3 s Heal on Mograine (interruptible)
        SPELL_WM_POWER_WORD_SHIELD  = kSpellSlice.first + 15,   // WM4a his shield, 5% of his health (purgeable)
        SPELL_WM_HOLY_SMITE         = kSpellSlice.first + 16,   // WM6 her 2.5 s filler (interruptible, script)
        SPELL_WM_VIGIL_FLAME        = kSpellSlice.first + 17,   // WM5 heroic: the flame on its carrier
        SPELL_WM_VIGIL_FLARE        = kSpellSlice.first + 18,   // WM5 a share of the flare (script)
        SPELL_WM_SEARED             = kSpellSlice.first + 19,   // WM5a the old carrier, 19 s
        SPELL_WM_FLAME_PASS         = kSpellSlice.first + 20,   // WM5 the pass's look on the new carrier (SV 3400)
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_WM_FLAME_PASS;
    static_assert(kSpellSlice.Contains(kLastSpell), "Whitemane's spells stay in her slice");

    // creature_text groups (ScarletMonasteryRework.h kTextRanges: Whitemane 0-7 with 0-2 stock and 6 D14H's; Mograine
    // 12-13 D14's, 2 stock).
    enum WhitemaneTexts : std::uint8_t
    {
        SAY_WHITEMANE_INTRO_STOCK   = 0,    // stock "Mograine has fallen! ... Arise, my champion! Arise!" (unused)
        SAY_WHITEMANE_KILL          = 1,    // stock "The Light has spoken!"
        SAY_WHITEMANE_ARISE         = 2,    // stock "Arise, my champion!" (WM1)
        SAY_WHITEMANE_FALLEN        = 3,    // "Mograine has fallen! You shall pay for this treachery!" (WM0)
        SAY_WHITEMANE_NOT_YET       = 4,    // "Not yet, my love. The Light is not done with you." (WM1a)
        SAY_WHITEMANE_TOGETHER      = 5,    // "Together... always..." (the pair's death)
        SAY_WHITEMANE_LIES          = 6,    // D14H: "Lies! He is the Crusade's champion!" (HM2)
        EMOTE_WHITEMANE_FLAME       = 7,    // "The Vigil Flame passes to $n!" (WM5, heroic; raid emote)
    };
    enum MograineFinaleTexts : std::uint8_t
    {
        SAY_MOGRAINE_AT_YOUR_SIDE   = 2,    // stock "At your side, milady!" (WM1)
        SAY_MOGRAINE_NOT_WHILE      = 12,   // "Not while I stand, milady!" (WM1b)
        SAY_MOGRAINE_MILADY         = 13,   // "Milady!" (WM2)
    };
    inline constexpr std::uint8_t kFirstOwnText = SAY_WHITEMANE_FALLEN;
    inline constexpr std::uint8_t kLastOwnText = EMOTE_WHITEMANE_FLAME;

    // Registry tags (one per mechanic; the bots and `.mech` read them).
    inline constexpr std::uint32_t TAG_WM_LANE = 1;         // WM2
    inline constexpr std::uint32_t TAG_WM_PENANCE = 2;      // WM3
    inline constexpr std::uint32_t TAG_WM_FLAME = 3;        // WM5: the 1-body soak on the carrier
    inline constexpr std::uint32_t TAG_WM_SEARED_OFF = 4;   // WM5a: the Seared keep off the carrier (no damage)

    // ----------------------------------------------------------------------------------------------------------------
    // Her states (out of combat) and the pair's stage (in combat)
    // ----------------------------------------------------------------------------------------------------------------

    enum class WhitemaneState : std::uint8_t
    {
        Chamber,    // before the Last Stand is DONE: behind her door, passive, immune to players
        Walking,    // out to the vigil (the Last Stand's end, a cold load)
        Vigil,      // kneels over Mograine at the vigil: passive, attackable (WM0); damage or a cast pulls her
        Fight,      // her encounter
        Dead,
    };

    inline constexpr char const* StateName(WhitemaneState s)
    {
        switch (s)
        {
            case WhitemaneState::Chamber: return "chamber";
            case WhitemaneState::Walking: return "walking";
            case WhitemaneState::Vigil:   return "vigil";
            case WhitemaneState::Fight:   return "fight";
            case WhitemaneState::Dead:    return "dead";
        }
        return "?";
    }

    // Where a (re)loaded Whitemane belongs: the vigil while the Last Stand is DONE and she is not; else her chamber.
    inline constexpr bool AtVigilForStage(ScarletMonasteryRework::CathedralStage stage)
    {
        return stage == ScarletMonasteryRework::CathedralStage::Vigil;
    }

    // The pair inside the fight.
    enum class PairStage : std::uint8_t
    {
        Alone,      // from the pull to the rising: she fights alone, he lies before the altar
        Rising,     // WM1: Deep Sleep, the run, the 2 s raise
        Pair,       // both up
        HerSave,    // WM1a: he fell, she channels at his body (he is down: not selectable, immune)
        HisSave,    // WM1b: she fell (a held body), he channels Lay on Hands over her
        HerSpent,   // she fell with his saves spent: she lies until he dies (he fights on alone)
        HisDead,    // he died with her saves spent: she fights on alone
        Over,       // the pair died (or the attempt ended)
    };

    inline constexpr char const* StageName(PairStage s)
    {
        switch (s)
        {
            case PairStage::Alone:    return "alone";
            case PairStage::Rising:   return "rising";
            case PairStage::Pair:     return "pair";
            case PairStage::HerSave:  return "her-save";
            case PairStage::HisSave:  return "his-save";
            case PairStage::HerSpent: return "her-spent";
            case PairStage::HisDead:  return "his-dead";
            case PairStage::Over:     return "over";
        }
        return "?";
    }

    // What a lethal hit on one of the pair does (WM1, "Till Death"): each saves the other when one falls, so they must
    // die close together. Her real death always comes last (her death carries the encounter's credit, row 450).
    enum class Lethal : std::uint8_t
    {
        Through,    // a real death (the damage goes through)
        Save,       // held at 1 health: the other's save starts (or he is down already: absorbed)
        Spent,      // (her only) held as a body: the vow is spent, she lies until he dies; he fights on alone
        PairDeath,  // both die now: him first, then her
    };

    inline constexpr char const* LethalName(Lethal l)
    {
        switch (l)
        {
            case Lethal::Through:   return "through";
            case Lethal::Save:      return "save";
            case Lethal::Spent:     return "spent";
            case Lethal::PairDeath: return "pair-death";
        }
        return "?";
    }

    // Saves each: 2 on normal (the group-failure cap below level 60), uncapped on heroic (0 = no cap).
    inline constexpr NH<std::uint8_t> kSaveCap{ 2, 0 };

    inline constexpr bool SaveLeft(std::uint8_t used, std::uint8_t cap)
    {
        return cap == 0 || used < cap;
    }

    // His lethal hit. `herSavesUsed`: raises she started this pull.
    inline constexpr Lethal OnHisLethal(PairStage stage, std::uint8_t herSavesUsed, std::uint8_t cap)
    {
        switch (stage)
        {
            case PairStage::Pair:
                return SaveLeft(herSavesUsed, cap) ? Lethal::Save : Lethal::Through;
            case PairStage::HerSave:
                return Lethal::Save;        // he is down: nothing reaches him (absorbed)
            case PairStage::HisSave:        // he dies over her body: both stay dead
            case PairStage::HerSpent:       // the last one standing falls
                return Lethal::PairDeath;
            default:
                return Lethal::Through;
        }
    }

    // Her lethal hit. `hisSavesUsed`: Lay on Hands he started this pull. `mograineUp`: alive, risen and not down.
    inline constexpr Lethal OnHerLethal(PairStage stage, std::uint8_t hisSavesUsed, std::uint8_t cap, bool mograineUp)
    {
        switch (stage)
        {
            case PairStage::Alone:
            case PairStage::Rising:
                return Lethal::PairDeath;   // before he rose (a GM burst): the vigil ends with both dead
            case PairStage::Pair:
                if (!mograineUp)
                    return Lethal::Through;
                return SaveLeft(hisSavesUsed, cap) ? Lethal::Save : Lethal::Spent;
            case PairStage::HerSave:
                return Lethal::PairDeath;   // she dies over his body: both stay dead
            case PairStage::HisSave:
            case PairStage::HerSpent:
                return Lethal::Spent;       // she is a body already (absorbed)
            case PairStage::HisDead:
            case PairStage::Over:
                return Lethal::Through;
        }
        return Lethal::Through;
    }

    // His real death: she follows him (she lies as a body, or he was down over her save).
    inline constexpr bool HisDeathEndsHer(PairStage stage)
    {
        return stage == PairStage::HisSave || stage == PairStage::HerSpent || stage == PairStage::HerSave;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (CATH "Tuning starting points" and "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<std::uint32_t> kWhitemaneHealth{ 50000, 220000 };      // handoff 3.6 (heroic: WP-H's override)
    inline constexpr NH<std::uint32_t> kMograineRisenHealth{ 45000, 200000 };  // at the rising (MograineFight::Rise)
    inline constexpr float kSaveReturnPct = 50.f;                               // a save returns the fallen at 50%

    // Times from the pull (P) or from the rising (R = P + 15 s).
    inline constexpr std::uint32_t kRisingAtMs = 15000;             // WM1: P + 15 s
    inline constexpr std::uint32_t kDeepSleepMs = 3000;             // up to 3 s, damage wakes
    inline constexpr float kDeepSleepRadiusYd = 100.f;
    inline constexpr std::uint32_t kRaiseCastMs = 2000;             // the 2 s rising cast
    inline constexpr std::uint32_t kRaiseRunGiveUpMs = 4000;        // the run to his body: then she casts where she is
    inline constexpr std::uint32_t kRaiseGiveUpMs = 9000;           // from the Deep Sleep: he rises whatever happened
    inline constexpr float kRaiseStandoffYd = 2.5f;                 // she raises him from this far

    inline constexpr NH<std::uint32_t> kHerSaveMs{ 10000, 8000 };   // WM1a her channel
    inline constexpr NH<std::uint32_t> kHisSaveMs{ 6000, 5000 };    // WM1b his channel
    inline constexpr std::uint32_t kSaveRunGiveUpMs = 3000;         // the run to the fallen: then the channel starts
    inline constexpr float kSaveStandoffYd = 2.f;

    inline constexpr std::uint32_t kLaneFirstMs = 20000;            // WM2: R + 20 s
    inline constexpr std::uint32_t kLaneEveryMs = 25000;
    inline constexpr std::uint32_t kLaneWarnMs = 2000;
    inline constexpr std::uint32_t kLaneNoSightGiveUpMs = 5000;     // no sight that long: the cycle is skipped
    inline constexpr NH<float> kLanePct{ 30.f, 45.f };
    inline constexpr float kLaneWidthYd = 4.f;
    inline constexpr float kLaneMinYd = 8.f;                        // closer than this: no lane (he is at her side)
    inline constexpr float kLaneBesideYd = 3.f;                     // he arrives this far from her, on his side
    inline constexpr float kChargeSpeed = 30.f;                     // yd/s (the companies' charge)
    inline constexpr std::uint32_t kChargeGraceMs = 1500;           // the arrival, past the charge's flight time
    inline constexpr std::uint32_t kBodyShieldMs = 6000;            // WM2a heroic: after each arrival
    inline constexpr float kBodyShieldShare = 0.5f;                 // half the damage she takes goes to him

    inline constexpr std::uint32_t kPenanceFirstMs = 10000;         // WM3: R + 10 s
    inline constexpr std::uint32_t kPenanceEveryMs = 20000;
    inline constexpr std::uint32_t kPenanceWarnMs = 3000;
    inline constexpr NH<std::uint32_t> kPenanceCount{ 2, 3 };
    inline constexpr float kPenanceRadiusYd = 6.f;
    inline constexpr NH<float> kPenanceMarkedPct{ 20.f, 30.f };
    inline constexpr NH<float> kPenanceOthersPct{ 30.f, 45.f };

    inline constexpr std::uint32_t kHealFirstMs = 5000;             // WM4: R + 5 s
    inline constexpr std::uint32_t kHealEveryMs = 15000;
    inline constexpr std::uint32_t kHealCastMs = 3000;
    inline constexpr NH<std::uint32_t> kHealPct{ 6, 20 };           // of his maximum health (hub ruling 54)
    inline constexpr std::uint32_t kShieldFirstMs = 8000;           // WM4a: R + 8 s
    inline constexpr std::uint32_t kShieldEveryMs = 20000;
    inline constexpr float kShieldPct = 5.f;                        // absorbs 5% of his maximum health
    inline constexpr std::uint32_t kShieldAuraMs = 30000;

    inline constexpr std::uint32_t kSmiteFirstMs = 1000;            // WM6: P + 1 s
    inline constexpr std::uint32_t kSmiteGapMs = 4000;              // every 4 s when nothing else is casting (gap 20)
    inline constexpr std::uint32_t kSmiteCastMs = 2500;
    inline constexpr NH<float> kSmitePct{ 10.f, 15.f };
    inline constexpr float kCastRangeYd = 40.f;
    inline constexpr float kChaseRangeYd = 25.f;                    // she holds her ground within this of her target

    inline constexpr std::uint32_t kStormFromRisingMs = 12000;      // LS5: R + 12 s (D13's risen kit, re-paced)
    inline constexpr std::uint32_t kStormEveryMs = 15000;

    inline constexpr std::uint32_t kFlameFirstMs = 20000;           // WM5 heroic: the carrier at R + 20 s
    inline constexpr std::uint32_t kFlameEveryMs = 10000;           // then a flare every 10 s
    inline constexpr std::uint32_t kSearedMs = 19000;               // WM5a
    inline constexpr float kFlameRadiusYd = 6.f;
    inline constexpr float kFlareTotalPct = 110.f;                  // heroic; split between two: 55% each
    inline constexpr std::uint32_t kFlameAuraMs = 60000;            // the carrier's flame (moved by the script)

    inline constexpr std::uint32_t kKillLineCooldownMs = 8000;
    inline constexpr std::uint32_t kVigilWalkGiveUpMs = 30000;      // the walk out: then she is placed at the vigil
    inline constexpr std::uint32_t kWipeWatchMs = 3000;             // a held body sees no player left: the wipe
    inline constexpr std::uint32_t kRetryMs = 1000;

    // Boss data (the descriptor).
    inline constexpr NH<std::uint8_t> kHealKickPriority{ 2, 4 };    // a reward on normal, expected on heroic
    inline constexpr std::uint8_t kSmiteKickPriority = 1;
    inline constexpr std::uint8_t kShieldPurgePriority = 2;
    inline constexpr float kKillTogetherPct = 10.f;                 // target priority by percent of health (as CV1)

    // WM5a: Seared fades before the flare after next (19 s against a 10 s flare; the hard mode's 15 s against 8 s), so
    // the flame runs a loop and never goes straight back.
    inline constexpr bool SearedFadesInTime(std::uint32_t searedMs, std::uint32_t flareEveryMs)
    {
        return searedMs > flareEveryMs && searedMs < 2 * flareEveryMs;
    }
    static_assert(SearedFadesInTime(kSearedMs, kFlameEveryMs), "WM5a: Seared outlasts one flare, not two");
    static_assert(SearedFadesInTime(15000, 8000), "the Truth's phase 1: Seared 15 s, the flare every 8 s");

    // The transition hold (D14H HM2: "no mechanic fires during the transition", "no pause in her casting"): Penance,
    // To Her Side and the flare wait; Smite, Heal and Shield go on. On release a carried flame's flare comes no sooner
    // than kFlameRewarnMs from now, and its soak is registered again for that time (the old one resolved on the old
    // timing while the hold ran).
    inline constexpr std::uint32_t kFlameRewarnMs = 3000;
    inline constexpr std::uint64_t FlareAfterHold(std::uint64_t nextFlame, std::uint64_t now)
    {
        return nextFlame == 0 ? 0 : std::max<std::uint64_t>(nextFlame, now + kFlameRewarnMs);
    }

    // The registry owner of the pair's mechanics, whose victim the role provider names the tank: Mograine while he is
    // risen and alive, down in her save included (no victim then: the provider falls back to the real tank, never her
    // top-threat player); her once he is dead or not risen.
    inline constexpr bool MograineOwnsMechanics(bool mograineAlive, bool mograineRisen)
    {
        return mograineAlive && mograineRisen;
    }

    // A wipe (not her death) with Mograine dead for good (her saves spent on normal): he is respawned, lies at his body
    // for the vigil, and the next pull raises him again ("a wipe returns ... Mograine to his body").
    inline constexpr bool MograineRespawnsOnWipe(bool herDeath, bool mograineAlive)
    {
        return !herDeath && !mograineAlive;
    }

    // How the wipe respawn reaches him (RF-2 mi-3). Every spawn on this server runs in dynamic respawn mode, so his
    // dead object leaves the map when the corpse decays (300 s, 30 s once looted): with the object still there,
    // Respawn(true) on it; with it gone, Map::ForceCreatureRespawn on his spawn id (the respawn queue makes him anew,
    // and skips the spawn if a live Mograine already stands).
    enum class MograineRespawn : std::uint8_t { None, Object, SpawnId };

    inline constexpr MograineRespawn MograineRespawnRoute(bool herDeath, bool hasObject, bool mograineAlive)
    {
        if (!MograineRespawnsOnWipe(herDeath, hasObject && mograineAlive))
            return MograineRespawn::None;
        return hasObject ? MograineRespawn::Object : MograineRespawn::SpawnId;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The place (section 7 #33 A: the vigil and the fight on the crossing; her chamber cannot hold Penance or the
    // Truth)
    // ----------------------------------------------------------------------------------------------------------------

    // Axes: +x north, +y west; orientation 0 looks north.
    inline float FacingTo(Vec2 from, Vec2 to)
    {
        float o = std::atan2(to.y - from.y, to.x - from.x);
        if (o < 0.f)
            o += 2.f * DungeonKit::kPi;
        return o;
    }

    // The vigil (section 7 #33 A) faces Mograine's body on the platform.
    inline Point4 VigilSpot()
    {
        Point3 const v = ScarletMonasteryRework::kWhitemaneVigil;
        return { v.x, v.y, v.z, FacingTo(v.XY(), ScarletMonasteryRework::kMograineBody.XY()) };
    }

    inline float Distance2d(Vec2 a, Vec2 b)
    {
        return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
    }

    // A point `standoff` yd short of `to` on the way from `from` (where she kneels to raise him; where he kneels to lay
    // hands on her). Already that close: `from` itself.
    inline Vec2 ShortOf(Vec2 from, Vec2 to, float standoff)
    {
        float const d = Distance2d(from, to);
        if (d <= standoff || d <= 0.001f)
            return from;
        float const k = (d - standoff) / d;
        return { from.x + (to.x - from.x) * k, from.y + (to.y - from.y) * k };
    }

    // WM2: he arrives `beside` yd from her, on his side of her (the lane runs from him to there).
    inline Vec2 LaneArrival(Vec2 her, Vec2 him, float beside = kLaneBesideYd)
    {
        float const d = Distance2d(her, him);
        if (d <= 0.001f)
            return her;
        float const k = std::min(beside, d) / d;
        return { her.x + (him.x - her.x) * k, her.y + (him.y - her.y) * k };
    }

    inline std::uint32_t ChargeFlightMs(float lengthYd)
    {
        return static_cast<std::uint32_t>(std::max(0.f, lengthYd) / kChargeSpeed * 1000.f);
    }

    // The fight's floor (the bots' bounds): the nave, the crossing with both arms and the altar platform, z 28-37 (NM
    // "Whitemane"; the platform 1.5-3.5 yd up, it tops out at 34.3). The landing before the Chapel Door stays out.
    struct Box
    {
        float minX;
        float maxX;
        float minY;
        float maxY;

        constexpr bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
    };
    inline constexpr float kFloorZMin = 28.f;
    inline constexpr float kFloorZMax = 37.f;
    inline constexpr Box kNaveBox{ 1073.f, 1131.f, 1366.f, 1428.f };
    inline constexpr Box kCrossingBox{ 1131.f, 1151.f, 1333.f, 1465.f };
    inline constexpr Box kPlatformBox{ 1151.f, 1172.f, 1366.f, 1428.f };
    inline constexpr std::array<Box, 3> kFloorBoxes{ { kNaveBox, kCrossingBox, kPlatformBox } };

    inline constexpr bool OnFloor(Vec2 p, float z)
    {
        if (z < kFloorZMin || z > kFloorZMax)
            return false;
        for (Box const& b : kFloorBoxes)
            if (b.Contains(p))
                return true;
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM3 Penance: 2 / 3 random players marked, never the tank (a 6 yd spread on the tank would push the melee off
    // Mograine: the shared doc's spread exemption)
    // ----------------------------------------------------------------------------------------------------------------

    struct PenanceCandidate
    {
        std::uint64_t id = 0;
        bool tank = false;
        bool alive = true;
    };

    // Up to `count` distinct living non-tank candidates. `rand(n)` returns [0, n).
    template <class Rand>
    std::vector<std::uint64_t> PickPenance(std::vector<PenanceCandidate> const& candidates, std::uint32_t count,
        Rand&& rand)
    {
        std::vector<std::uint64_t> pool;
        for (PenanceCandidate const& c : candidates)
            if (c.alive && !c.tank)
                pool.push_back(c.id);
        std::vector<std::uint64_t> out;
        while (!pool.empty() && out.size() < count)
        {
            std::size_t k = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())));
            if (k >= pool.size())
                k = 0;
            out.push_back(pool[k]);
            pool.erase(pool.begin() + static_cast<std::ptrdiff_t>(k));
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM5 the Vigil Flame (heroic): a vigil candle passed hand to hand, shared by two
    // ----------------------------------------------------------------------------------------------------------------

    struct FlareShares
    {
        float carrierPct = 0.f;
        float partnerPct = 0.f;     // 0 without a partner
    };

    // The flare's 110% split between the carrier and the nearest other player within 6 yd (55% each); unshared, the
    // carrier takes all of it; a Seared player takes double their share (110%, lethal: hub ruling 50).
    inline constexpr FlareShares FlareSplit(bool partner, bool carrierSeared, bool partnerSeared,
        float totalPct = kFlareTotalPct)
    {
        float const share = partner ? totalPct / 2.f : totalPct;
        return { carrierSeared ? share * 2.f : share, partner ? (partnerSeared ? share * 2.f : share) : 0.f };
    }

    struct FlameCandidate
    {
        std::uint64_t id = 0;
        bool alive = true;
        bool seared = false;
        bool tank = false;
        float distanceYd = 0.f;     // from the carrier
    };

    // The partner: the nearest other living player within the flame's 6 yd (Seared or not, the tank too: the flare
    // hits whoever stands there). nullopt: nobody, the flare is unshared.
    inline std::optional<std::size_t> FlarePartner(std::vector<FlameCandidate> const& others,
        float radiusYd = kFlameRadiusYd)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < others.size(); ++i)
        {
            FlameCandidate const& c = others[i];
            if (!c.alive || c.distanceYd > radiusYd)
                continue;
            if (!best || c.distanceYd < others[*best].distanceYd)
                best = i;
        }
        return best;
    }

    // The flame passes to the partner when the partner can carry it (alive, not Seared); else PickCarrier.
    inline constexpr bool PartnerCarriesOn(FlameCandidate const& partner)
    {
        return partner.alive && !partner.seared;
    }

    // Who carries the flame when the partner cannot (the first carrier, no partner, a Seared or dead partner): a random
    // unseared living non-tank, else the unseared tank (the backup, hub ruling 50), else nobody. `rand(n)` returns
    // [0, n).
    template <class Rand>
    std::optional<std::size_t> PickCarrier(std::vector<FlameCandidate> const& others, Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < others.size(); ++i)
            if (others[i].alive && !others[i].seared && !others[i].tank)
                pool.push_back(i);
        if (pool.empty())
            for (std::size_t i = 0; i < others.size(); ++i)
                if (others[i].alive && !others[i].seared)
                    pool.push_back(i);
        if (pool.empty())
            return std::nullopt;
        std::size_t k = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())));
        if (k >= pool.size())
            k = 0;
        return pool[k];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor's kill order (target priority by percent of health, as the council's CV1; the channeler first in
    // a save window; the tank keeps Mograine)
    // ----------------------------------------------------------------------------------------------------------------

    struct KillOrder
    {
        bool together = false;      // both by percent of health (KillTogether)
        bool whitemane = false;     // she is a target
        bool mograine = false;      // he is a target
        bool tankOnMograine = false;
    };

    inline constexpr KillOrder KillOrderFor(PairStage stage)
    {
        switch (stage)
        {
            case PairStage::Pair:
                return { true, true, true, true };
            case PairStage::HerSave:            // he is down: the channeler first
            case PairStage::HisDead:
            case PairStage::Alone:
            case PairStage::Rising:
                return { false, true, false, false };
            case PairStage::HisSave:            // she is a body: the channeler first
            case PairStage::HerSpent:
                return { false, false, true, true };
            case PairStage::Over:
                return {};
        }
        return {};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 20 (bot throughput, LESSONS 4.2-4.3): what a save window asks of a group
    // ----------------------------------------------------------------------------------------------------------------

    // The percent of `health` the one still standing must be under when the other falls, to die inside `windowMs` at
    // `groupDps`.
    inline constexpr float WindowPct(std::uint32_t health, std::uint32_t windowMs, float groupDps)
    {
        return health == 0 ? 0.f
            : groupDps * static_cast<float>(windowMs) / 1000.f / static_cast<float>(health) * 100.f;
    }
}

#endif
