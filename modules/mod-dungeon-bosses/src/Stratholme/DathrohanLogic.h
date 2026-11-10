/*
 * mod-dungeon-bosses, Stratholme S7: Grand Crusader Dathrohan (10812) and Balnazzar (10813), the pure, host-testable
 * part (no engine headers): the spell ids, the per-difficulty tuning, the two stages' timelines (never paused by a cast
 * bar), the truth roll, the Sacred Ground and Judgment picks, the transform, the Carrion Swarm's carriers, the
 * Infernal's stoking Immolation, the Vampiric Aura and the chamber's bounds. Build spec: ST 2077-2166 (build spec), ST
 * 1769-2076 (design: pitch A "The Mask Slips", pitch B "The Dreadlord", rulings 27, 28 and 31); handoff section 3.4
 * rows DB and BZ, section 3.5 row S7, section 3.6 (normal 250k / 220k, heroic 340k / 300k), section 3.8 (the chamber).
 * The hard mode (the Grand Lie, S8) fights on this AI through DathrohanFight.h.
 *
 * Damage percentages are of the reference health row (normal 3,670 non-tank / 3,710 tank, heroic 4,120 / 4,110 at
 * level 60, the MapLevels pin 329:60).
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace StratDathrohan
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`). The hard
    // mode's own ids are kSpellsGrandLie (206575-206604, S8).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsDathrohan;

    // Declared in apps/dbc-tools source/npcs/stratholme/dathrohan_balnazzar.py (same ids).
    enum DathrohanSpells : std::uint32_t
    {
        SPELL_DB_SACRED_GROUND_BAR  = 206545,   // DB1 the 3 s cast bar (not interruptible: the registry owns the hit)
        SPELL_DB_TRUE_GROUND        = 206546,   // DB1 the gold ground at his feet (also the lie's on heroic)
        SPELL_DB_LIE_GROUND         = 206547,   // DB1 the lie's shadow under the gold (normal)
        SPELL_DB_HOLY_WRATH         = 206548,   // DB1 true: the bolts on the non-tanks outside 8 yd (resolve copy)
        SPELL_DB_SHADOW_ERUPTION    = 206549,   // DB1 lie: the eruption on the non-tanks inside 10 yd (resolve copy)
        SPELL_DB_JUDGMENT_MARK      = 206550,   // DB2 the gold mark, 5 s (true; the lie too on heroic)
        SPELL_DB_JUDGMENT_DARK_MARK = 206551,   // DB2 the lie's dark mark, 5 s (normal)
        SPELL_DB_JUDGMENT_SHARE     = 206552,   // DB2 true: one share of the burst (base point 0 from the script)
        SPELL_DB_JUDGMENT_BURST     = 206553,   // DB2 lie: the burst on the others within 8 yd (resolve copy)
        SPELL_DB_JUDGMENT_TARGET    = 206554,   // DB2 lie: the 15% on the marked player (the kit's percent spell)
        SPELL_DB_UNMASKING_MARK     = 206555,   // DB3 the mark on every non-tank, 5 s
        SPELL_DB_UNMASKING_BURST    = 206556,   // DB3 the burst on the others within 8 yd (resolve copy)
        SPELL_BZ_CARRION_BAR        = 206557,   // BZ1 the 2.5 s cast bar (the fan look follows his facing)
        SPELL_BZ_CARRION_HIT        = 206558,   // BZ1 the cone's hit on everyone but its target (resolve copy)
        SPELL_BZ_CARRION_TARGET     = 206559,   // BZ1 the target's 20% (base point 0 from the script)
        SPELL_BZ_INFERNO_BAR        = 206560,   // BZ2 the 3.5 s cast bar
        SPELL_BZ_INFERNO_HIT        = 206561,   // BZ2 the meteor's 8 yd hit (resolve copy)
        SPELL_BZ_INFERNO_LOOK       = 206562,   // BZ2 the falling meteor at the spot (a dest cast, 2.5 s before)
        SPELL_BZ_IMMOLATION_LOOK    = 206563,   // BZ3 the ring of flames on the Infernal
        SPELL_BZ_IMMOLATION_TICK    = 206564,   // BZ3 the 1 s tick on every player within 5 yd (script base point)
        SPELL_BZ_STOKED             = 206565,   // BZ3 heroic: a stack on the Infernal every 5 s (+1% a tick each)
        SPELL_BZ_SLEEP              = 206566,   // BZ4 the 2 s interruptible cast and its 5 s Magic sleep
        SPELL_BZ_NIGHTMARE          = 206567,   // BZ4 the DoT after the sleep (30% over 6 s, not dispellable)
        SPELL_BZ_NIGHTMARE_PULSE    = 206568,   // BZ4 heroic, a missed Sleep: 10% to every player each 2 s
        SPELL_BZ_VAMPIRIC_AURA      = 206569,   // BZ5 the passive on him (the tell; the script heals)
        SPELL_BZ_VAMPIRIC_HEAL      = 206570,   // BZ5 the heal per kit hit landed (base point 0 from the script)
        SPELL_BZ_INFERNAL_STRIKE    = 206571,   // BZ3 the Infernal's swing every 2 s (the kit's percent spell)
        // 206572-206574 spare (206575-206604 are S8's, the Grand Lie)
    };
    static_assert(kSpellSlice.Contains(SPELL_DB_SACRED_GROUND_BAR), "Dathrohan spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_BZ_INFERNAL_STRIKE), "Dathrohan spells sit in his slice");
    static_assert(!StratholmeRework::kSpellsGrandLie.Contains(SPELL_BZ_INFERNAL_STRIKE), "S8 keeps its ids");

    // Stock spells of the transform (the tank kit uses StratholmeRework.h's SPELL_CRUSADER_STRIKE, SPELL_HOLY_STRIKE
    // and SPELL_MIND_BLAST_BALNAZZAR).
    enum DathrohanStockSpells : std::uint32_t
    {
        SPELL_DB_BALNAZZAR_TRANSFORM        = 17288,    // full heal, +10,000 mana, triggers the stun below
        SPELL_DB_BALNAZZAR_TRANSFORM_STUN   = 17398,    // 5 s stun on every enemy within 100 yd
    };

    // The death skeletons (creature_summon_groups 10813 group 1, stock): kept, summoned on his death.
    std::uint32_t constexpr kDeathSummonGroup = 1;
    std::uint32_t constexpr kSkeletalGuardianEntry = 10390;
    std::uint32_t constexpr kSkeletalBerserkerEntry = 10391;

    // Registry tags (the build spec's ids). S8 tags its own mechanics from kHardModeTagBase.
    enum DathrohanTags : std::uint32_t
    {
        TAG_DB_SACRED_GROUND    = 1,    // DB1 the real answer (true: the shelter Stack; lie: the eruption circle)
        TAG_DB_JUDGMENT         = 2,    // DB2 the real answer (true: the Stack on the marked player; lie: the RunOut)
        TAG_DB_UNMASKING        = 3,    // DB3 the Spread
        TAG_DB_CLAIM            = 4,    // heroic: the claimed marker (a Decoy, drawn like the truth)
        TAG_BZ_CARRION          = 5,    // BZ1 a tracking cone
        TAG_BZ_INFERNO          = 6,    // BZ2 the meteor
        TAG_BZ_IMMOLATION       = 7,    // BZ3 the Infernal's 5 yd ring (telegraph only; the Infernal's script ticks)
        TAG_DB_HOLY_WRATH       = 8,    // DB1 true: the bolts on the players outside (RegistryHit)
        TAG_BZ_NIGHTMARE        = 9,    // BZ4 heroic: a pulse (RegistryHit)
    };
    std::uint32_t constexpr kHardModeTagBase = 20;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Build spec" and "Tuning starting points", approved 2026-11-03)
    // ----------------------------------------------------------------------------------------------------------------

    // The truth roll: every call is true or a lie on its own, even odds.
    std::uint32_t constexpr kTruthChancePct = 50;

    // DB1 Sacred Ground: first at 10 s, every 20 s (heroic 15 s, so it drifts into the Judgment); a 3 s cast. True: the
    // non-tanks inside 8 yd of him are sheltered and Holy Wrath strikes every non-tank outside for 40% / 50%. Lie: 40%
    // / 50% Shadow to every non-tank inside 10 yd. No Weakened (over 30%).
    std::uint32_t constexpr kSacredGroundFirstMs = 10000;
    inline constexpr NH<std::uint32_t> kSacredGroundEveryMs{ 20000, 15000 };
    std::uint32_t constexpr kSacredGroundCastMs = 3000;
    float constexpr kShelterRadius = 8.f;
    float constexpr kEruptionRadius = 10.f;
    inline constexpr NH<float> kSacredGroundPct{ 40.f, 50.f };
    // The ground looks last a little past the cast (area auras at his feet).
    std::uint32_t constexpr kGroundLookMs = 3500;

    // DB2 Judgment: first at 20 s, every 20 s (heroic 12 s); a 5 s mark on a random non-tank. True: 90% / 120% split
    // evenly among the non-tanks within 6 yd of the target (no Weakened on a share). Lie: 40% / 50% to every other
    // non-tank within 8 yd, and 15% to the target.
    std::uint32_t constexpr kJudgmentFirstMs = 20000;
    inline constexpr NH<std::uint32_t> kJudgmentEveryMs{ 20000, 12000 };
    std::uint32_t constexpr kJudgmentMarkMs = 5000;
    float constexpr kJudgmentShareRadius = 6.f;
    float constexpr kJudgmentBurstRadius = 8.f;
    inline constexpr NH<float> kJudgmentSharePct{ 90.f, 120.f };
    inline constexpr NH<float> kJudgmentBurstPct{ 40.f, 50.f };
    float constexpr kJudgmentTargetPct = 15.f;

    // DB3 The Unmasking: at 40% he heals to full and stuns everyone for 5 s (stock 17288 and 17398); the entry changes
    // 1.5 s in (the stock timed event), he heals into Balnazzar's own health and the reveal yell plays; as the stun
    // ends every non-tank gets the lie's mark at once: 5 s, then 30% + Weakened to every other non-tank within 8 yd.
    float constexpr kTransformHealthPct = 40.f;
    std::uint32_t constexpr kTransformEntryMs = 1500;
    std::uint32_t constexpr kTransformStunMs = 5000;
    std::uint32_t constexpr kUnmaskingMarkMs = 5000;
    float constexpr kUnmaskingRadius = 8.f;
    float constexpr kUnmaskingPct = 30.f;

    // DB4 the stock tank kit, stage 1 (SmartAI 10812 rows 2 and 4): Crusader Strike 17281 and Holy Strike 17284, each
    // first at 2 to 7 s, then every 10 to 20 s, in melee range of his victim.
    std::uint32_t constexpr kStrikeFirstMinMs = 2000;
    std::uint32_t constexpr kStrikeFirstMaxMs = 7000;
    std::uint32_t constexpr kStrikeMinMs = 10000;
    std::uint32_t constexpr kStrikeMaxMs = 20000;
    std::uint32_t constexpr kRetryMs = 2000;            // nobody to target, or out of reach: try again this soon
    std::uint32_t constexpr kMeleeRetryMs = 1000;

    // Stage 2 counts from the end of the transform stun (the players can act again).
    // BZ1 Carrion Swarm: first at 8 s, every 15 s; a 2.5 s cast on a random non-tank: a 60 degree, 30 yd cone from
    // him aimed at the target live (it tracks them through the cast). The target always takes 20% (no Weakened: it
    // cannot be dodged); everyone else inside, the tank too, 40%. Heroic: a second cone at another non-tank 1.5 s
    // after the first starts.
    std::uint32_t constexpr kCarrionFirstMs = 8000;
    std::uint32_t constexpr kCarrionEveryMs = 15000;
    std::uint32_t constexpr kCarrionCastMs = 2500;
    float constexpr kCarrionAngleDeg = 60.f;
    float constexpr kCarrionLengthYd = 30.f;
    float constexpr kCarrionTargetPct = 20.f;
    float constexpr kCarrionOthersPct = 40.f;
    inline constexpr NH<std::uint32_t> kCarrionCones{ 1, 2 };
    std::uint32_t constexpr kCarrionSecondDelayMs = 1500;

    // BZ2 Inferno: first at 20 s, every 30 s; a 3.5 s cast (yell 6) marks a random non-tank's spot at the cast start;
    // the meteor lands in 8 yd for 50% Fire (the tank too) and an Infernal rises there. The meteor's look starts 2.5 s
    // before the hit (V-2: the rock falls for 2.5 s).
    std::uint32_t constexpr kInfernoFirstMs = 20000;
    std::uint32_t constexpr kInfernoEveryMs = 30000;
    std::uint32_t constexpr kInfernoCastMs = 3500;
    std::uint32_t constexpr kMeteorFallMs = 2500;
    float constexpr kInfernoRadius = 8.f;
    float constexpr kInfernoPct = 50.f;

    // BZ3 the Infernal (300608): 12k / 18k (template and heroic copy), 25k in the hard mode (S8's tune). It goes for
    // the nearest player, strikes its victim every 2 s (4% / 5%: the kit's percent spell), and burns everyone within
    // 5 yd every second: 5%, on heroic +1% every 5 s it lives, to 12% at 35 s. It crumbles at 45 s; at most 2 stand at
    // once (a third rising takes the oldest's place).
    inline constexpr NH<std::uint32_t> kInfernalHealth{ 12000, 18000 };     // mirrored for the tests (the data sets it)
    std::uint32_t constexpr kInfernalLifeMs = 45000;
    std::uint32_t constexpr kInfernalCap = 2;
    float constexpr kImmolationRadius = 5.f;
    std::uint32_t constexpr kImmolationTickMs = 1000;
    float constexpr kImmolationBasePct = 5.f;
    float constexpr kImmolationStokePct = 1.f;
    std::uint32_t constexpr kImmolationStokeEveryMs = 5000;
    float constexpr kImmolationMaxPct = 12.f;
    std::uint32_t constexpr kInfernalSwingMs = 2000;
    std::uint32_t constexpr kInfernalFirstSwingMs = 1500;
    inline constexpr NH<float> kInfernalStrikePct{ 4.f, 5.f };
    std::uint32_t constexpr kInfernalRetargetMs = 1000;
    float constexpr kInfernalNearestYd = 60.f;

    // BZ4 Sleep: first at 14 s, every 20 s; a 2 s cast on a random non-tank (the interrupt list; a reward on normal,
    // expected on heroic). Landed: a 5 s Magic sleep that damage does not break (the dispel list), then Nightmare: 30%
    // Shadow over 6 s (5% a second), not dispellable. Heroic: a Sleep that landed (missed) also makes the sleeper's
    // Nightmare pulse 10% to every player each 2 s for 6 s.
    std::uint32_t constexpr kSleepFirstMs = 14000;
    std::uint32_t constexpr kSleepEveryMs = 20000;
    std::uint32_t constexpr kSleepCastMs = 2000;
    std::uint32_t constexpr kSleepMs = 5000;
    float constexpr kSleepRangeYd = 30.f;
    std::uint32_t constexpr kNightmareMs = 6000;
    std::uint32_t constexpr kNightmareTickMs = 1000;
    float constexpr kNightmarePct = 30.f;
    std::uint32_t constexpr kNightmarePulseEveryMs = 2000;
    std::uint32_t constexpr kNightmarePulses = 3;
    float constexpr kNightmarePulsePct = 10.f;

    // The stock tank kit, stage 2 (SmartAI 10812 row 11): Mind Blast 17287 (a 1.5 s cast) on his victim, first at 9 to
    // 11 s, then every 10 to 15 s. A filler: it never starts when a mechanic's cast falls due within its cast time.
    std::uint32_t constexpr kMindBlastFirstMinMs = 9000;
    std::uint32_t constexpr kMindBlastFirstMaxMs = 11000;
    std::uint32_t constexpr kMindBlastMinMs = 10000;
    std::uint32_t constexpr kMindBlastMaxMs = 15000;
    std::uint32_t constexpr kMindBlastCastMs = 1500;

    // BZ5 Vampiric Aura: from the transform, every hit of his kit that lands on a player heals him 1% / 2% of his
    // maximum health (the hard mode 3%, S8's tune): the cones (the target's too), the meteor, Immolation ticks, the
    // Infernal's strikes, Nightmare ticks and pulses. His melee and Mind Blast never count.
    inline constexpr NH<float> kVampiricPct{ 1.f, 2.f };

    // Melee: DamageModifier 3.5 for Dathrohan and 9 for Balnazzar on normal (the stock values, set by the DT file; the
    // live 8.5 on 10812 was a mod-progression leftover); heroic is the heroic templates' tier.

    // ----------------------------------------------------------------------------------------------------------------
    // The chamber (handoff section 3.8; NAVMESH-REPORT section 7): round, radius 19-20 yd from the brazier on the mesh,
    // floor z 136.5-138.1; the only way in is on the north-east side, 20-27 yd out. The bots' spot bounds keep inside
    // a circle a yard inside the mesh's rim, so no spot reaches the doorway (R-1-B B-1).
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kBoundsRadius = 18.5f;
    float constexpr kBoundsZMin = 135.5f;
    float constexpr kBoundsZMax = 139.5f;
    float constexpr kFloorZ = 136.8f;

    inline bool InBounds(Vec2 p)
    {
        return DungeonKit::Distance(p, StratholmeRework::kDathrohanBrazier.XY()) <= kBoundsRadius;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks and rules
    // ----------------------------------------------------------------------------------------------------------------

    enum class Truth : std::uint8_t
    {
        True = 0,
        Lie = 1,
    };

    // `roll` in [0, 100): below the chance the call is true.
    constexpr Truth RollTruth(std::uint32_t roll)
    {
        return roll < kTruthChancePct ? Truth::True : Truth::Lie;
    }

    constexpr char const* TruthName(Truth t)
    {
        return t == Truth::True ? "true" : "lie";
    }

    // The fight's stages: Dathrohan, the transform (the heal, the stun, the entry change), then Balnazzar.
    enum class Stage : std::uint8_t
    {
        Dathrohan = 0,
        Transform = 1,
        Balnazzar = 2,
    };

    constexpr char const* StageName(Stage s)
    {
        switch (s)
        {
            case Stage::Dathrohan: return "dathrohan";
            case Stage::Transform: return "transform";
            case Stage::Balnazzar: return "balnazzar";
        }
        return "?";
    }

    // He unmasks once his health is at or below 40% in stage 1.
    constexpr bool ShouldTransform(Stage stage, float healthPct)
    {
        return stage == Stage::Dathrohan && healthPct <= kTransformHealthPct;
    }

    // Stage 1 and the transform: nothing kills Dathrohan (his last 40% is never fought); a blow that would leaves him
    // at 1 health. Returns the damage to take.
    constexpr std::uint32_t ClampMaskDamage(Stage stage, std::uint32_t health, std::uint32_t damage)
    {
        if (stage == Stage::Balnazzar || damage < health)
            return damage;
        return health > 1 ? health - 1 : 0;
    }

    // DB1 true: the non-tanks Holy Wrath strikes: every alive non-tank of the fight not in `sheltered` (the registry
    // Stack's inside list). `players` and `tank` / `alive` run in parallel (ids are raw guids).
    struct Candidate
    {
        std::uint64_t id = 0;
        bool tank = false;
        bool alive = true;
    };

    inline std::vector<std::uint64_t> HolyWrathTargets(std::vector<Candidate> const& players,
        std::vector<std::uint64_t> const& sheltered)
    {
        std::vector<std::uint64_t> out;
        for (Candidate const& c : players)
        {
            if (c.tank || !c.alive)
                continue;
            if (std::find(sheltered.begin(), sheltered.end(), c.id) == sheltered.end())
                out.push_back(c.id);
        }
        return out;
    }

    // DB2 true: who shares the burst: the registry Stack's inside list (non-tanks within 6 yd of the target), plus the
    // marked player when alive (a solo test tank still takes it alone). No duplicates, inside order first.
    inline std::vector<std::uint64_t> JudgmentTakers(std::vector<std::uint64_t> const& inside, Candidate const& target)
    {
        std::vector<std::uint64_t> out = inside;
        if (target.alive && std::find(out.begin(), out.end(), target.id) == out.end())
            out.push_back(target.id);
        return out;
    }

    // BZ1: the carriers of a cone aimed at `target`: every fight player but the target (the target leads it and is
    // never hit by it; its 20% is the script's). Empty when nobody else fights: the caller then adds an empty guid (an
    // empty carrier set would mean everyone).
    inline std::vector<std::uint64_t> ConeCarriers(std::vector<std::uint64_t> const& players, std::uint64_t target)
    {
        std::vector<std::uint64_t> out;
        out.reserve(players.size());
        for (std::uint64_t id : players)
            if (id != target)
                out.push_back(id);
        return out;
    }

    // BZ3: the Immolation tick's percent after `ageMs` alive (heroic and the hard mode stoke it).
    constexpr float ImmolationPct(bool stokes, std::uint32_t ageMs)
    {
        if (!stokes)
            return kImmolationBasePct;
        float const pct = kImmolationBasePct + kImmolationStokePct * float(ageMs / kImmolationStokeEveryMs);
        return pct < kImmolationMaxPct ? pct : kImmolationMaxPct;
    }

    // BZ3: the Stoked stacks on an Infernal after `ageMs` (the visible count; ImmolationPct reads the age).
    constexpr std::uint32_t StokeStacks(bool stokes, std::uint32_t ageMs)
    {
        if (!stokes)
            return 0;
        std::uint32_t const stacks = ageMs / kImmolationStokeEveryMs;
        std::uint32_t const max = std::uint32_t((kImmolationMaxPct - kImmolationBasePct) / kImmolationStokePct);
        return stacks < max ? stacks : max;
    }

    // BZ3: with `alive` Infernals up, how many crumble (oldest first) so a new one can rise under the cap.
    constexpr std::uint32_t InfernalsToCrumble(std::uint32_t alive)
    {
        return alive >= kInfernalCap ? alive - kInfernalCap + 1 : 0;
    }

    // BZ5: the heal of one kit hit, in health points (at least 1).
    constexpr std::uint32_t VampiricHeal(std::uint32_t maxHealth, float pct)
    {
        float const heal = float(maxHealth) * pct / 100.f;
        return heal < 1.f ? 1u : std::uint32_t(heal + 0.5f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). The casts with a bar
    // (Sacred Ground, Carrion Swarm, Inferno, Sleep) and the stage 2 filler (Mind Blast) go through the cast queue; the
    // Judgment and the stage 1 strikes fire on their beats.
    // ----------------------------------------------------------------------------------------------------------------

    // The beats. Stage 1: SacredGround, Judgment, CrusaderStrike, HolyStrike. Stage 2: CarrionSwarm, Inferno, Sleep,
    // MindBlast (the hard mode's hooks name these to hold or retime S7's own stage 2 kit).
    enum class Beat : std::uint8_t
    {
        SacredGround = 0,
        Judgment = 1,
        CrusaderStrike = 2,
        HolyStrike = 3,
        CarrionSwarm = 4,
        Inferno = 5,
        Sleep = 6,
        MindBlast = 7,
    };
    std::size_t constexpr kBeatCount = 8;

    constexpr char const* BeatName(Beat b)
    {
        switch (b)
        {
            case Beat::SacredGround: return "sacred-ground";
            case Beat::Judgment: return "judgment";
            case Beat::CrusaderStrike: return "crusader-strike";
            case Beat::HolyStrike: return "holy-strike";
            case Beat::CarrionSwarm: return "carrion-swarm";
            case Beat::Inferno: return "inferno";
            case Beat::Sleep: return "sleep";
            case Beat::MindBlast: return "mind-blast";
        }
        return "?";
    }

    constexpr bool IsStageTwoBeat(Beat b)
    {
        return b == Beat::CarrionSwarm || b == Beat::Inferno || b == Beat::Sleep || b == Beat::MindBlast;
    }

    // The fixed first times (stage 1 from the pull, stage 2 from the end of the transform stun; the stock strikes and
    // Mind Blast draw theirs from a range, this is the low end).
    constexpr std::uint32_t FirstAt(Beat b)
    {
        switch (b)
        {
            case Beat::SacredGround: return kSacredGroundFirstMs;
            case Beat::Judgment: return kJudgmentFirstMs;
            case Beat::CrusaderStrike:
            case Beat::HolyStrike: return kStrikeFirstMinMs;
            case Beat::CarrionSwarm: return kCarrionFirstMs;
            case Beat::Inferno: return kInfernoFirstMs;
            case Beat::Sleep: return kSleepFirstMs;
            case Beat::MindBlast: return kMindBlastFirstMinMs;
        }
        return 0;
    }

    // The fixed cadences (the stock strikes and Mind Blast: the low end of their range).
    constexpr std::uint32_t EveryMs(Beat b, bool heroic)
    {
        switch (b)
        {
            case Beat::SacredGround: return kSacredGroundEveryMs(heroic);
            case Beat::Judgment: return kJudgmentEveryMs(heroic);
            case Beat::CrusaderStrike:
            case Beat::HolyStrike: return kStrikeMinMs;
            case Beat::CarrionSwarm: return kCarrionEveryMs;
            case Beat::Inferno: return kInfernoEveryMs;
            case Beat::Sleep: return kSleepEveryMs;
            case Beat::MindBlast: return kMindBlastMinMs;
        }
        return 0;
    }

    // The next due time of a beat that was due at `due` and fired at `now`: the cadence counts from the due time, so a
    // cast that waited for another never drifts the beat (R-1-B N-1), but never sooner than half a cadence from now.
    constexpr std::uint64_t NextDue(std::uint64_t due, std::uint64_t now, std::uint32_t every)
    {
        std::uint64_t const onCadence = due + every;
        std::uint64_t const floor = now + every / 2;
        return onCadence > floor ? onCadence : floor;
    }

    // The stage 2 filler (Mind Blast) waits for the mechanics: it never starts when one falls due within its cast time.
    constexpr bool FillerWaits(std::uint64_t now, std::uint64_t mechanicDueAt, std::uint32_t castMs = kMindBlastCastMs)
    {
        return mechanicDueAt <= now + castMs;
    }

    // The cast queue's ids (DungeonKit::CastQueue). The hard mode (S8) schedules its own from kHardModeCastBase.
    enum DathrohanCasts : std::uint32_t
    {
        CAST_SACRED_GROUND  = 1,
        CAST_CARRION_SWARM  = 2,
        CAST_INFERNO        = 3,
        CAST_SLEEP          = 4,
        CAST_MIND_BLAST     = 5,
    };
    std::uint32_t constexpr kHardModeCastBase = 100;
    std::uint64_t constexpr kCastSpacingMs = 500;

    // The queue id of a beat with a cast (0: the beat fires without one).
    constexpr std::uint32_t CastOf(Beat b)
    {
        switch (b)
        {
            case Beat::SacredGround: return CAST_SACRED_GROUND;
            case Beat::CarrionSwarm: return CAST_CARRION_SWARM;
            case Beat::Inferno: return CAST_INFERNO;
            case Beat::Sleep: return CAST_SLEEP;
            case Beat::MindBlast: return CAST_MIND_BLAST;
            default: return 0;
        }
    }

    // The beat of a queue id (S7's own ids only).
    constexpr Beat BeatOfCast(std::uint32_t cast)
    {
        switch (cast)
        {
            case CAST_CARRION_SWARM: return Beat::CarrionSwarm;
            case CAST_INFERNO: return Beat::Inferno;
            case CAST_SLEEP: return Beat::Sleep;
            case CAST_MIND_BLAST: return Beat::MindBlast;
            default: return Beat::SacredGround;
        }
    }

    // The mechanics' priority on the queue (the filler is 0): the meteor and the ground, then the cones, then Sleep.
    constexpr std::uint8_t PriorityOf(Beat b)
    {
        switch (b)
        {
            case Beat::SacredGround: return 3;
            case Beat::Inferno: return 3;
            case Beat::CarrionSwarm: return 2;
            case Beat::Sleep: return 1;
            default: return 0;
        }
    }

    // The cast time a queue id holds him (the bars and the stock Mind Blast).
    constexpr std::uint32_t CastMsOf(std::uint32_t cast)
    {
        switch (cast)
        {
            case CAST_SACRED_GROUND: return kSacredGroundCastMs;
            case CAST_CARRION_SWARM: return kCarrionCastMs;
            case CAST_INFERNO: return kInfernoCastMs;
            case CAST_SLEEP: return kSleepCastMs;
            case CAST_MIND_BLAST: return kMindBlastCastMs;
            default: return 0;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hard mode's knobs on S7's stage 2 kit (DathrohanFight.h GrandLie::TuneCarrion / TuneInferno)
    // ----------------------------------------------------------------------------------------------------------------

    // One Carrion Swarm call: how many cones (the second and later ones start `secondDelayMs` apart, each at another
    // non-tank), their percents, and a ward aura that spares its holders (their cone eligibility: maxStacks 0; a
    // warded target's own hit is skipped too). The spells are S7's; S8 may pass its own.
    struct CarrionSpec
    {
        std::uint32_t cones = 1;
        std::uint32_t secondDelayMs = kCarrionSecondDelayMs;
        float targetPct = kCarrionTargetPct;
        float othersPct = kCarrionOthersPct;
        std::uint32_t wardAura = 0;
        std::uint32_t barSpell = SPELL_BZ_CARRION_BAR;
        std::uint32_t hitSpell = SPELL_BZ_CARRION_HIT;
        std::uint32_t targetSpell = SPELL_BZ_CARRION_TARGET;
    };

    inline CarrionSpec DefaultCarrion(bool heroic)
    {
        CarrionSpec spec;
        spec.cones = kCarrionCones(heroic);
        return spec;
    }

    // One Inferno: the meteor's percent and the Infernal it raises (health 0: its template's; `stokes`: the heroic
    // Immolation that grows).
    struct InfernoSpec
    {
        float meteorPct = kInfernoPct;
        std::uint32_t infernalHealth = 0;
        bool stokes = false;
    };

    inline InfernoSpec DefaultInferno(bool heroic)
    {
        InfernoSpec spec;
        spec.stokes = heroic;
        return spec;
    }
}

#endif
