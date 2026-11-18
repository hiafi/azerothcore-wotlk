/*
 * mod-dungeon-bosses, Blackrock Depths D4:
 * The Ring of Law: the frame, Grimstone and the waves, the pure, host-testable part (no engine headers). Build spec S1
 * "Ring of Law" (docs/dungeons/blackrock-depths-1-detention-block.md: the frame, How it runs, Waves, Build spec RL1-RL6
 * and RW1-RW6; rulings 17-20, 25, 26, 31, 88), handoff sections 3.4 (rows D4), 3.5 (row D4), 3.6, 3.8 (NM: the floor
 * is ~3,800 sq yd and not round), 3.10, section 7 #16 (rolls saved, a wipe resets both champions and Favor to 5,
 * credit after the second champion or after the Encore when lit). Tested by tests/brd_ring_of_law_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsRingOfLaw (210810-210869), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/ring_of_law.py
 *   Tuning         NH<> constants straight from the build spec (normal / heroic); the unset cells (Tail Sting's cone
 *                  and poison, the Screech cadence, the rescaled stock wave casts) are this WP's defaults (report,
 *                  designer questions)
 *   Run            the steps of one attempt and their beats (rulings 25, 26)
 *   Favor          RL1-RL3, RL6: the meter, its bands, the losses doubled under the Crowd, the banner at 10 (heroic)
 *   Waves          RW1-RW6: per wave type its count, its health, its signature and the stock casts it keeps
 *   Geometry       the floor polygon from NM's bearing table (padded 0.5 yd), lines to the wall, Trial by Fire's wedge
 *
 * The engine half: npc_grimstone_rework.cpp (Grimstone runs the attempt; RingOfLawFight.h is what he offers the
 * champions, D5, and the Encore, D6) and npc_ring_beast_rework.cpp (the six wave mobs).
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_RING_OF_LAW_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_RING_OF_LAW_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace BrdRingOfLaw
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsRingOfLaw;

    // The binding switch (S0): Grimstone (10096) and the six wave mobs are bound to this WP's scripts by
    // apps/dbc-tools source/npcs/blackrock_depths/ring_of_law.py, and the wave mobs' SmartAI is dropped by
    // rev_ring_of_law_blackrock_depths.sql, in the same change (lib/test_blackrock_depths_ring_of_law.py pins the
    // three).
    inline constexpr bool kBound = true;

    enum RingOfLawSpells : std::uint32_t
    {
        SPELL_RL_CROWD_FAVOR        = kSpellSlice.first + 0,    // 210810 RL1 the meter: a buff, its stacks = Favor
        SPELL_RL_CROWD_GIFT         = kSpellSlice.first + 1,    // 210811 RL2 a heal (the cast's value), +10% damage
        SPELL_RL_ROAR_OF_THE_CROWD  = kSpellSlice.first + 2,    // 210812 RL2 at Favor 10: +10% damage done
        SPELL_RL_GIFT_TOSS          = kSpellSlice.first + 3,    // 210813 look: a spectator tosses roses (a missile)
        SPELL_RL_JEER               = kSpellSlice.first + 4,    // 210814 RL3 a jeer's hit (resolve copy, Physical)
        SPELL_RL_JEER_BOTTLE        = kSpellSlice.first + 5,    // 210815 look: a thrown bottle (a missile)
        SPELL_RL_JEER_APPLE         = kSpellSlice.first + 6,    // 210816 look: a rotten apple
        SPELL_RL_JEER_BANANA        = kSpellSlice.first + 7,    // 210817 look: a rotten banana
        SPELL_RL_TRIAL_BY_FIRE      = kSpellSlice.first + 8,    // 210818 RL4 the wedge's hit (resolve copy, Fire)
        SPELL_RL_TRIAL_BY_FIRE_BAR  = kSpellSlice.first + 9,    // 210819 RL4 Grimstone's 3 s cast bar (Fire)
        SPELL_RL_TRIAL_BURST        = kSpellSlice.first + 10,   // 210820 look: an eruption on a stalker in the wedge
        SPELL_RW_BURROW             = kSpellSlice.first + 11,   // 210821 RW1 the eruption's hit (resolve copy)
        SPELL_RW_BURROW_SINK        = kSpellSlice.first + 12,   // 210822 look: the worm sinks
        SPELL_RW_BURROW_ERUPT       = kSpellSlice.first + 13,   // 210823 look: the dirt burst as it comes up
        SPELL_RW_TAIL_STING_BAR     = kSpellSlice.first + 14,   // 210824 RW2 the stinger's 2 s cast bar (the look)
        SPELL_RW_TAIL_STING         = kSpellSlice.first + 15,   // 210825 RW2 the cone's hit (resolve copy, Nature)
        SPELL_RW_TAIL_STING_POISON  = kSpellSlice.first + 16,   // 210826 RW2 the poison (rider; a dispel is a reward)
        SPELL_RW_SCREECH            = kSpellSlice.first + 17,   // 210827 RW3 2 s kickable cast: 10 yd hit + silence
        SPELL_RW_THUNDERCLAP_BAR    = kSpellSlice.first + 18,   // 210828 RW4 the 2 s wind-up bar
        SPELL_RW_THUNDERCLAP        = kSpellSlice.first + 19,   // 210829 RW4 the ring's hit (resolve copy, Nature)
        SPELL_RW_THUNDERCLAP_SLOW   = kSpellSlice.first + 20,   // 210830 RW4 the slow (rider)
        SPELL_RW_VENOM_SPIT         = kSpellSlice.first + 21,   // 210831 RW5 the pool's tick (resolve copy, Nature)
        SPELL_RW_VENOM_SPIT_POOL    = kSpellSlice.first + 22,   // 210832 RW5 the pool's look (a stalker's aura)
        SPELL_RW_ACID_BURST         = kSpellSlice.first + 23,   // 210833 RW6 the burst's hit (resolve copy, Nature)
        SPELL_RW_ACID_SWELL         = kSpellSlice.first + 24,   // 210834 RW6 the fallen beetle swells (its scale)
        SPELL_RW_ACID_BURST_LOOK    = kSpellSlice.first + 25,   // 210835 look: the burst at the corpse
        SPELL_RW_WORM_POISON        = kSpellSlice.first + 26,   // 210836 Dredge Worm Poison 13298 rescaled
        SPELL_RW_WORM_VENOM_SPIT    = kSpellSlice.first + 27,   // 210837 Dredge Worm Venom Spit 6917 rescaled
        SPELL_RW_LIZARD_BOLT        = kSpellSlice.first + 28,   // 210838 Thundersnout Lizard Bolt 15611 rescaled
        // 210839-210869 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_RW_LIZARD_BOLT;
    static_assert(kLastSpell <= kSpellSlice.last, "the Ring's spells must stay in its slice");

    // Stock spells kept as they are: the opening debuffs (percent auras, nothing to rescale; S1 "Waves"), Cleave 40504
    // (a weapon percent: it follows the stinger's own damage) and Pierce Armor 6016 (an armor debuff).
    enum RingStockSpells : std::uint32_t
    {
        SPELL_STOCK_DREDGE_SICKNESS = 14535,    // Dredge Worm: -25% all stats, 30 yd, 300 s
        SPELL_STOCK_BARBED_STING    = 14534,    // Deep Stinger: -55% attack speed
        SPELL_STOCK_AURAL_SHOCK     = 14538,    // Dark Screecher: -35% cast speed
        SPELL_STOCK_DISJUNCTION     = 14533,    // Burrowing Thundersnout: +50% fire / frost / arcane damage taken
        SPELL_STOCK_CREEPER_VENOM   = 14532,    // Cave Creeper: +30% physical damage taken (2 s cast, kickable)
        SPELL_STOCK_PUTRID_ENZYME   = 14539,    // Borer Beetle: +50% nature / shadow damage taken
        SPELL_STOCK_CLEAVE          = 40504,    // Deep Stinger, kept
        SPELL_STOCK_PIERCE_ARMOR    = 6016,     // Borer Beetle, kept
    };

    // Registry tags (the fight's ledger; no G1 drill row names the Ring's frame).
    enum RingOfLawTags : std::uint32_t
    {
        TAG_RL_JEER         = 11,
        TAG_RL_TRIAL_FIRE   = 12,
        TAG_RW_BURROW       = 13,
        TAG_RW_TAIL_STING   = 14,
        TAG_RW_THUNDERCLAP  = 15,
        TAG_RW_VENOM_SPIT   = 16,
        TAG_RW_ACID_BURST   = 17,
    };

    // creature_text groups of 10096 (S1 "Text"; S0 range 0-14, 0-5 stock, 3 moved to the win). Yells (14); 10, 13 and
    // 14 are boss emotes (41).
    enum GrimstoneTexts : std::uint8_t
    {
        SAY_GRIM_RING_CENTER        = 0,    // stock "The Sons of Thaurissan shall watch you perish..." (ring center)
        SAY_GRIM_WAVE               = 1,    // stock "Unleash the fury and let it be done!" (the wave)
        SAY_GRIM_FIRST_CHAMPION     = 2,    // stock "But your real punishment lies ahead." (the challenger)
        SAY_GRIM_WON                = 3,    // stock "Good riddance!" (moved: the run is won)
        SAY_GRIM_SENTENCED          = 4,    // stock "You have been sentenced to death..." (the start)
        SAY_GRIM_GAP                = 5,    // stock "Haha! I bet you thought you were done!" (the wave is down)
        SAY_GRIM_TRIAL_BY_FIRE      = 6,    // Sentence
        SAY_GRIM_TRIAL_BY_BEASTS    = 7,    // Sentence
        SAY_GRIM_TRIAL_BY_THE_CROWD = 8,    // Sentence
        SAY_GRIM_SECOND_CHAMPION    = 9,    // the challenger falls, the title holder comes
        EMOTE_GRIM_BANNER           = 10,   // Favor 10 on heroic: the banner is thrown in
        SAY_GRIM_BANNER_BURNED      = 11,   // D6 (the banner burned; RingFrame::GrimstoneSay)
        SAY_GRIM_ENCORE             = 12,   // the Encore after its 15 s beat
        EMOTE_GRIM_ROAR             = 13,   // Favor reaches 8
        EMOTE_GRIM_JEER             = 14,   // Favor drops to 2
    };
    inline constexpr std::uint8_t kGrimstoneLastText = EMOTE_GRIM_JEER;

    // ----------------------------------------------------------------------------------------------------------------
    // The Sentences (RL4-RL6), one per instance (DATA_RING_SENTENCE, 0-based)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Sentence : std::uint8_t
    {
        Fire = 0,
        Beasts = 1,
        Crowd = 2,
    };

    inline constexpr Sentence SentenceOf(std::uint32_t data)
    {
        return data == 1 ? Sentence::Beasts : data == 2 ? Sentence::Crowd : Sentence::Fire;
    }

    inline constexpr std::uint8_t SentenceText(Sentence s)
    {
        switch (s)
        {
            case Sentence::Fire:   return SAY_GRIM_TRIAL_BY_FIRE;
            case Sentence::Beasts: return SAY_GRIM_TRIAL_BY_BEASTS;
            case Sentence::Crowd:  return SAY_GRIM_TRIAL_BY_THE_CROWD;
        }
        return SAY_GRIM_TRIAL_BY_FIRE;
    }

    inline constexpr char const* SentenceName(Sentence s)
    {
        switch (s)
        {
            case Sentence::Fire:   return "fire";
            case Sentence::Beasts: return "beasts";
            case Sentence::Crowd:  return "crowd";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The run (rulings 25, 26; S1 "Run flow")
    // ----------------------------------------------------------------------------------------------------------------
    enum class Step : std::uint8_t
    {
        Idle = 0,       // not started (the instance summons Grimstone on AT 1526)
        Entry,          // walking to the ring center
        Sentence,       // at the center: line 0, then the Sentence
        ToCorner,       // walking to his waiting corner (wp2)
        Opener,         // the one wave (and its 30 s Favor clock)
        Gap,            // 10 s from the wave's death to the challenger
        Challenger,     // champion 1
        Interlude,      // 5 s from the challenger's death to the title holder
        TitleHolder,    // champion 2 (Title Holder)
        EncoreBeat,     // 15 s after the title holder's death, the banner burned (D6)
        Encore,         // D6's five
        Done,           // credited (the slot is DONE)
    };

    inline constexpr char const* StepName(Step s)
    {
        switch (s)
        {
            case Step::Idle:        return "idle";
            case Step::Entry:       return "entry";
            case Step::Sentence:    return "sentence";
            case Step::ToCorner:    return "to-corner";
            case Step::Opener:      return "opener";
            case Step::Gap:         return "gap";
            case Step::Challenger:  return "challenger";
            case Step::Interlude:   return "interlude";
            case Step::TitleHolder: return "title-holder";
            case Step::EncoreBeat:  return "encore-beat";
            case Step::Encore:      return "encore";
            case Step::Done:        return "done";
        }
        return "?";
    }

    // A champion (or the Encore's team) fights in these steps: Trial by Beasts sends its beasts only then.
    inline constexpr bool ChampionFights(Step s)
    {
        return s == Step::Challenger || s == Step::TitleHolder || s == Step::Encore;
    }

    // The frame's meters (the gift, the jeers, the deaths) run from the wave's arrival to the credit.
    inline constexpr bool FrameRuns(Step s)
    {
        return s >= Step::Opener && s < Step::Done;
    }

    // Trial by Fire runs from the challenger's entry to the credit (S1: "from the champion's entry").
    inline constexpr bool FireRuns(Step s)
    {
        return s >= Step::Challenger && s < Step::Done;
    }

    // The wipe watch: from the entry (the entrance gate shuts at its first beat) to the credit, an arena with no living
    // player on its floor ends the attempt.
    inline constexpr bool WipeWatched(Step s)
    {
        return s >= Step::Entry && s < Step::Done;
    }

    // The step after a Ring unit died (the wave's last beast, a champion); `encoreLit` = the banner burned on heroic
    // and the Encore's script registered.
    inline constexpr Step AfterKill(Step s, bool encoreLit)
    {
        switch (s)
        {
            case Step::Opener:      return Step::Gap;
            case Step::Challenger:  return Step::Interlude;
            case Step::TitleHolder: return encoreLit ? Step::EncoreBeat : Step::Done;
            case Step::Encore:      return Step::Done;
            default:                return s;
        }
    }

    // User ruling 2026-11-17: a wipe after the title holder fell with the banner burned (the 15 s beat or the Encore
    // itself) puts the banner out (Grimstone sets DATA_ENCORE_RUNNING on these steps; the instance's FAIL then clears
    // DATA_BANNER_BURNED, saved); a wipe before that keeps it lit.
    inline constexpr bool WipeUnlightsBanner(Step s)
    {
        return s == Step::EncoreBeat || s == Step::Encore;
    }

    // Beats (ms).
    inline constexpr std::uint32_t kEntryFirstBeatMs = 1000;        // stock: line 4 and the entrance gate after 1 s
    inline constexpr std::uint32_t kWalkTimeoutMs = 14000;          // a walk that never arrives moves on
    inline constexpr std::uint32_t kSentenceDelayMs = 4000;         // line 0 at the center, then the Sentence
    inline constexpr std::uint32_t kToCornerDelayMs = 4000;         // the Sentence, then the walk to the corner
    inline constexpr std::uint32_t kWaveDelayMs = 2000;             // line 1 and the south gate, then the wave
    inline constexpr std::uint32_t kWaveFavorWindowMs = 30000;      // RL1: the wave dead within 30 s: +2
    inline constexpr std::uint32_t kGapMs = 10000;                  // ruling 25: the wave's death to the challenger
    inline constexpr std::uint32_t kEastGateLeadMs = 2000;          // the east gate opens this long before a champion
    inline constexpr std::uint32_t kInterludeMs = 5000;             // ruling 25: about 5 s to the title holder
    inline constexpr std::uint32_t kEncoreBeatMs = 15000;           // ruling 30: the beat before the Encore's leap
    inline constexpr std::uint32_t kWipeGraceMs = 3000;             // no living player on the floor this long: a wipe
    inline constexpr std::uint32_t kChampionLostMs = 5000;          // a champion gone (not dead) this long: again
    inline constexpr std::uint32_t kSouthGateCloseMs = 15000;       // the south gate shuts once the wave is in, or then
    inline constexpr float kGateClearYd = 2.f;                      // "in": this far inside the floor's edge
    inline constexpr std::uint32_t kSyncMs = 1000;                  // the Favor buff, the deaths, Grimstone's combat

    // ----------------------------------------------------------------------------------------------------------------
    // RL1-RL3, RL6: Crowd Favor
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kFavorStart = BlackrockDepthsRework::kRingFavorStart;   // 5
    inline constexpr std::uint32_t kFavorMax = BlackrockDepthsRework::kRingFavorMax;       // 10
    inline constexpr std::int32_t kFavorClean = 1;          // a dodgeable mechanic resolved with nobody hit
    inline constexpr std::int32_t kFavorWave = 2;           // the wave dead within 30 s
    inline constexpr std::int32_t kFavorPerHit = 1;         // per player hit by a dodgeable mechanic
    inline constexpr std::int32_t kFavorPerDeath = 3;       // per death
    inline constexpr std::int32_t kCrowdLossFactor = 2;     // RL6: Trial by the Crowd doubles every loss
    inline constexpr std::uint32_t kRoarFrom = 8;           // RL2: 8-10 the crowd roars (the gift)
    inline constexpr std::uint32_t kJeerUpTo = 2;           // RL3: 0-2 the crowd jeers (the Crowd: at every level)

    inline constexpr std::uint32_t ClampFavor(std::int32_t v)
    {
        return static_cast<std::uint32_t>(std::clamp<std::int32_t>(v, 0, static_cast<std::int32_t>(kFavorMax)));
    }

    // A loss of `points` (positive) under `sentence`: doubled under the Crowd.
    inline constexpr std::int32_t Loss(std::int32_t points, Sentence sentence)
    {
        return sentence == Sentence::Crowd ? points * kCrowdLossFactor : points;
    }

    inline constexpr std::uint32_t AfterGain(std::uint32_t favor, std::int32_t points)
    {
        return ClampFavor(static_cast<std::int32_t>(favor) + points);
    }

    inline constexpr std::uint32_t AfterLoss(std::uint32_t favor, std::int32_t points, Sentence sentence)
    {
        return ClampFavor(static_cast<std::int32_t>(favor) - Loss(points, sentence));
    }

    // RL1: one resolve of a dodgeable mechanic: +1 with nobody hit, else -1 per player hit (doubled under the Crowd).
    inline constexpr std::uint32_t AfterResolve(std::uint32_t favor, std::uint32_t playersHit, Sentence sentence)
    {
        return playersHit == 0 ? AfterGain(favor, kFavorClean)
            : AfterLoss(favor, static_cast<std::int32_t>(playersHit) * kFavorPerHit, sentence);
    }

    inline constexpr bool Roars(std::uint32_t favor) { return favor >= kRoarFrom; }
    inline constexpr bool RoarOfTheCrowd(std::uint32_t favor) { return favor >= kFavorMax; }
    inline constexpr bool Jeers(std::uint32_t favor, Sentence sentence)
    {
        return sentence == Sentence::Crowd || favor <= kJeerUpTo;
    }

    // The emotes: 13 as Favor reaches 8 from below, 14 as it drops to 2 from above (none for a move inside a band).
    enum class FavorCue : std::uint8_t
    {
        None,
        Roar,
        Jeer,
    };

    inline constexpr FavorCue CueFor(std::uint32_t before, std::uint32_t after)
    {
        if (before < kRoarFrom && after >= kRoarFrom)
            return FavorCue::Roar;
        if (before > kJeerUpTo && after <= kJeerUpTo)
            return FavorCue::Jeer;
        return FavorCue::None;
    }

    // EN1 (ruling 21): at Favor 10 on heroic the crowd throws the banner, once per run (the flag is saved).
    inline constexpr bool ThrowsBanner(std::uint32_t favor, bool heroic, bool alreadyThrown)
    {
        return heroic && !alreadyThrown && favor >= kFavorMax;
    }

    // RL2 the gift, RL3 the jeers.
    inline constexpr std::uint32_t kGiftEveryMs = 15000;
    inline constexpr std::uint32_t kGiftFirstMs = kGiftEveryMs / 2;     // first casts at half the cooldown (gap 17)
    inline constexpr float kGiftHealPct = 10.f;                         // % of reference health (non-tank row)
    inline constexpr std::uint32_t kGiftMs = 10000;
    inline constexpr std::int32_t kGiftDamagePct = 10;
    inline constexpr std::int32_t kRoarDamagePct = 10;
    inline constexpr std::uint32_t kJeerEveryMs = 8000;
    inline constexpr std::uint32_t kJeerFirstMs = kJeerEveryMs / 2;
    inline constexpr std::uint32_t kJeerCount = 3;
    inline constexpr float kJeerRadius = 3.f;
    inline constexpr std::uint32_t kJeerWarnMs = 1500;
    inline constexpr NH<float> kJeerPct{ 10.f, 20.f };
    inline constexpr float kThrowMissileSpeed = 28.f;                   // the crowd's missiles (yd/s, the DBC Speed)
    inline constexpr float kGalleryMinZ = -45.f;                        // a spectator above this throws (the gallery)
    inline constexpr float kThrowerSearchYd = 90.f;

    // A volley of jeers is one dodgeable mechanic: +1 only when none of its circles hit anybody; every player hit still
    // costs a point as its circle resolves.
    struct VolleyJudge
    {
        std::uint32_t expected = 0;
        std::uint32_t resolved = 0;
        std::uint32_t hits = 0;

        // One circle resolved with `playersHit`; true when this was the volley's last circle and nobody was hit (+1).
        constexpr bool Resolve(std::uint32_t playersHit)
        {
            ++resolved;
            hits += playersHit;
            return expected != 0 && resolved == expected && hits == 0;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RL4 Trial by Fire, RL5 Trial by Beasts
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kTrialFireEveryMs = 30000;
    inline constexpr std::uint32_t kTrialFireFirstMs = kTrialFireEveryMs / 2;  // from the challenger's entry
    inline constexpr std::uint32_t kTrialFireWarnMs = 3000;
    inline constexpr float kTrialFireAngleDeg = 90.f;
    inline constexpr float kTrialFireMaxLength = 45.f;      // the cone's length: the wall within its wedge, capped
    inline constexpr float kTrialFireRotateDeg = -90.f;     // each wedge turns a quarter clockwise (seen from above)
    inline constexpr NH<float> kTrialFirePct{ 30.f, 45.f }; // ruling 31
    inline constexpr std::uint32_t kTrialBurstMs = 3000;    // the eruption stalkers' life
    inline constexpr std::uint32_t kBeastsEveryMs = 20000;
    inline constexpr std::uint32_t kBeastsFirstMs = kBeastsEveryMs / 2;        // from the challenger's entry
    inline constexpr std::uint32_t kBeastsCap = 3;          // alive at once
    inline constexpr std::uint32_t kBeastsGateMs = 4000;    // the south gate stays open this long for one beast

    inline constexpr float Radians(float deg) { return deg * DungeonKit::kPi / 180.f; }
    inline constexpr float Degrees(float rad) { return rad * 180.f / DungeonKit::kPi; }

    inline float NormalizeOrientation(float o)
    {
        o = std::fmod(o, DungeonKit::kTwoPi);
        return o < 0.f ? o + DungeonKit::kTwoPi : o;
    }

    // The n-th wedge's facing (radians) from the first one's quadrant (0-3): a quarter clockwise each time.
    inline float WedgeFacing(std::uint32_t firstQuadrant, std::uint32_t n)
    {
        return NormalizeOrientation(Radians(90.f * static_cast<float>(firstQuadrant % 4)
            + kTrialFireRotateDeg * static_cast<float>(n % 4)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RW1-RW6: the waves. One wave of the rolled type at the stock count (S1 "Waves"); each type keeps its stock
    // opening debuff (the opener only; it ends when the wave dies) and gets one signature. A "group" signature fires on
    // one beast of the type at a time (Grimstone's cadence: "every 12 s a worm sinks"); a per-beast one on each beast.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Signature : std::uint8_t
    {
        Burrow = 0,         // RW1 Dredge Worm
        TailSting = 1,      // RW2 Deep Stinger
        Screech = 2,        // RW3 Dark Screecher
        Thunderclap = 3,    // RW4 Burrowing Thundersnout
        VenomSpit = 4,      // RW5 Cave Creeper
        AcidBurst = 5,      // RW6 Borer Beetle (on its death)
    };

    inline constexpr char const* SignatureName(Signature s)
    {
        switch (s)
        {
            case Signature::Burrow:      return "burrow";
            case Signature::TailSting:   return "tail-sting";
            case Signature::Screech:     return "screech";
            case Signature::Thunderclap: return "thunderclap";
            case Signature::VenomSpit:   return "venom-spit";
            case Signature::AcidBurst:   return "acid-burst";
        }
        return "?";
    }

    enum class CastTarget : std::uint8_t
    {
        None,
        Victim,         // the beast's current victim
        Random,         // a random player in its fight (the tank too)
    };

    // A stock repeating cast a beast keeps (the rescaled copy, or the stock id where nothing scales).
    struct StockCast
    {
        std::uint32_t spell = 0;
        CastTarget target = CastTarget::None;
        std::uint32_t firstMs = 0;
        std::uint32_t everyMs = 0;
    };

    struct WaveKind
    {
        std::uint32_t entry;
        std::uint8_t count;             // per wave (stock RingMobs)
        Signature signature;
        bool perBeast;                  // the signature's clock is each beast's own (else Grimstone's, one at a time)
        std::uint32_t firstMs;          // the signature's first firing (half its cooldown unless stock)
        std::uint32_t everyMs;
        std::uint32_t openingDebuff;    // stock, cast on the pull by the opener's first beast
        std::uint32_t normalHealth;     // S1 Build spec (sized for a 25 s clear)
        std::uint32_t heroicHealth;     // WP-H's overrides (source/world/dungeons/blackrock_depths.py)
        float healthModifier;           // on the level 51 warrior base 2,292 (the wave mobs are level 50-51)
        std::array<StockCast, 2> casts;
    };

    inline constexpr std::uint32_t kWaveBaseHealth = 2292;     // creature_classlevelstats level 51, class 1 [db]

    // Index = the stock RingMobs order (BlackrockDepthsRework::kRingWaveMobs, the saved roll DATA_RING_WAVE).
    inline constexpr std::array<WaveKind, 6> kWaveTypes{ {
        { BlackrockDepthsRework::NPC_DREDGE_WORM, 3, Signature::Burrow, false, 6000, 12000,
            SPELL_STOCK_DREDGE_SICKNESS, 18000, 28000, 7.853403f,
            { { { SPELL_RW_WORM_POISON, CastTarget::Random, 4000, 8000 },
                { SPELL_RW_WORM_VENOM_SPIT, CastTarget::Random, 6000, 6000 } } } },
        { BlackrockDepthsRework::NPC_DEEP_STINGER, 3, Signature::TailSting, false, 5000, 10000,
            SPELL_STOCK_BARBED_STING, 18000, 28000, 7.853403f,
            { { { SPELL_STOCK_CLEAVE, CastTarget::Victim, 4000, 5000 }, {} } } },
        { BlackrockDepthsRework::NPC_DARK_SCREECHER, 3, Signature::Screech, true, 4000, 18000,
            SPELL_STOCK_AURAL_SHOCK, 18000, 28000, 7.853403f, { { {}, {} } } },
        { BlackrockDepthsRework::NPC_THUNDERSNOUT, 2, Signature::Thunderclap, true, 4000, 8000,
            SPELL_STOCK_DISJUNCTION, 26000, 42000, 11.343804f,
            { { { SPELL_RW_LIZARD_BOLT, CastTarget::Random, 5000, 6000 }, {} } } },
        { BlackrockDepthsRework::NPC_CAVE_CREEPER, 3, Signature::VenomSpit, false, 5000, 10000,
            SPELL_STOCK_CREEPER_VENOM, 18000, 28000, 7.853403f, { { {}, {} } } },
        { BlackrockDepthsRework::NPC_BORER_BEETLE, 6, Signature::AcidBurst, true, 0, 0,
            SPELL_STOCK_PUTRID_ENZYME, 9000, 14000, 3.926701f,
            { { { SPELL_STOCK_PIERCE_ARMOR, CastTarget::Random, 4000, 45000 }, {} } } },
    } };

    inline constexpr std::optional<std::uint32_t> WaveIndexOf(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kWaveTypes.size(); ++i)
            if (kWaveTypes[i].entry == entry)
                return i;
        return std::nullopt;
    }

    // Grimstone <-> npc_ring_beast_rework: SetData(kBeastDataSlot, index + 1) marks an opener beast (0: a Trial by
    // Beasts add); GetData(kBeastDataFree) is 1 while it can take a group signature; DoAction(kBeastActionSignature)
    // fires its type's group signature on a target it picks.
    inline constexpr std::uint32_t kBeastDataSlot = 1;
    inline constexpr std::uint32_t kBeastDataFree = 2;
    inline constexpr std::int32_t kBeastActionSignature = 0x52570001;

    // A per-beast signature's first firing for the n-th beast of its wave (staggered so three Screeches do not land
    // together).
    inline constexpr std::uint32_t kPerBeastStaggerMs = 1500;
    inline constexpr std::uint32_t FirstSignatureMs(WaveKind const& w, std::uint32_t index)
    {
        return w.perBeast ? w.firstMs + kPerBeastStaggerMs * index : w.firstMs;
    }

    // The wave's spawn spots: stock, a row 0.4 yd apart in x behind the south gate (in its alcove).
    inline constexpr float kWaveSpawnStep = 0.4f;
    inline constexpr Point3 WaveSpawn(std::uint32_t index)
    {
        Point3 p = BlackrockDepthsRework::kRingWaveSummon;
        p.x += kWaveSpawnStep * static_cast<float>(index);
        return p;
    }

    // RW1 Burrow
    inline constexpr std::uint32_t kBurrowWarnMs = 2000;
    inline constexpr float kBurrowRadius = 5.f;
    inline constexpr NH<float> kBurrowPct{ 25.f, 40.f };
    // RW2 Tail Sting (the cone's angle and length are unset in S1: section 7 #21's 60 degrees / 15 yd)
    inline constexpr std::uint32_t kTailStingWarnMs = 2000;
    inline constexpr float kTailStingAngleDeg = 60.f;
    inline constexpr float kTailStingLength = 15.f;
    inline constexpr float kTailStingRange = 15.f;          // "a random player within 15 yd"
    inline constexpr NH<float> kTailStingPct{ 20.f, 35.f };
    inline constexpr NH<float> kTailStingPoisonPct{ 1.f, 1.5f };   // per tick (this WP's default)
    inline constexpr std::uint32_t kTailStingPoisonTickMs = 2000;
    inline constexpr std::uint32_t kTailStingPoisonMs = 10000;
    // RW3 Screech
    inline constexpr std::uint32_t kScreechCastMs = 2000;
    inline constexpr float kScreechRadius = 10.f;
    inline constexpr NH<float> kScreechPct{ 10.f, 15.f };
    inline constexpr std::uint32_t kScreechSilenceMs = 2000;
    // RW4 Thunderclap
    inline constexpr std::uint32_t kThunderclapWarnMs = 2000;
    inline constexpr float kThunderclapRadius = 10.f;
    inline constexpr NH<float> kThunderclapPct{ 20.f, 35.f };
    inline constexpr std::int32_t kThunderclapSlowPct = 41;         // the stock Thunderclap's movement slow
    inline constexpr std::int32_t kThunderclapAttackSlowPct = 34;   // and its attack speed slow
    inline constexpr std::uint32_t kThunderclapSlowMs = 6000;
    // RW5 Venom Spit
    inline constexpr std::uint32_t kVenomSpitWarnMs = 1500;
    inline constexpr float kVenomSpitRadius = 4.f;
    inline constexpr std::uint32_t kVenomSpitLifeMs = 12000;
    inline constexpr std::uint32_t kVenomSpitTickMs = 1000;
    inline constexpr NH<float> kVenomSpitPct{ 4.f, 6.f };          // per second
    // RW6 Acid Burst
    inline constexpr std::uint32_t kAcidSwellMs = 2000;
    inline constexpr std::uint32_t kAcidBodyHoldMs = 2500;          // the swollen body dies 0.5 s after its burst
    inline constexpr float kAcidBurstRadius = 4.f;
    inline constexpr NH<float> kAcidBurstPct{ 15.f, 25.f };
    inline constexpr std::int32_t kAcidSwellScalePct = 60;
    // The stock casts kept, rescaled (S1: "stock wave casts rescaled"; this WP's defaults, designer question).
    inline constexpr NH<float> kWormPoisonPct{ 1.f, 1.5f };         // per 3 s tick, 30 s (stock 24 a tick)
    inline constexpr std::uint32_t kWormPoisonTickMs = 3000;
    inline constexpr std::uint32_t kWormPoisonMs = 30000;
    inline constexpr NH<float> kWormVenomSpitPct{ 3.f, 4.5f };      // stock 30-50 on a 2.5 s cast
    inline constexpr std::uint32_t kWormVenomSpitCastMs = 2500;
    inline constexpr NH<float> kLizardBoltPct{ 5.f, 8.f };          // stock 36-40 on a 2 s cast
    inline constexpr std::uint32_t kLizardBoltCastMs = 2000;

    // Kick and dispel priorities (the Ring's descriptor; higher first). All rewards on both difficulties.
    inline constexpr std::uint8_t kScreechKickPriority = 2;
    inline constexpr std::uint8_t kStockKickPriority = 1;           // Lizard Bolt, Venom Spit, Creeper Venom
    inline constexpr std::uint8_t kPoisonDispelPriority = 1;        // Tail Sting's poison, the worm's Poison

    // ----------------------------------------------------------------------------------------------------------------
    // The floor (handoff section 3.8, NAVMESH-REPORT 1.4): the distance from the ring center to the wall by bearing
    // (degrees, 0 = north +x, 90 = west +y), every 10 degrees, with the four gate alcoves at the gates' own bearing
    // and distance [DB]. The floor is not round: 38-43 yd on the cardinals, 23-26 yd on the diagonals.
    // ----------------------------------------------------------------------------------------------------------------
    struct WallSample
    {
        float bearingDeg;
        float distance;
    };

    inline constexpr std::array<WallSample, 36> kRingWall{ {
        { 0.f, 38.5f }, { 11.7f, 43.2f }, { 20.f, 38.f }, { 30.f, 35.f }, { 40.f, 24.8f }, { 50.f, 24.2f },
        { 60.f, 26.f }, { 70.f, 29.f }, { 80.f, 33.f }, { 90.f, 35.f }, { 103.9f, 39.9f }, { 110.f, 36.f },
        { 120.f, 33.5f }, { 130.f, 31.f }, { 140.f, 29.5f }, { 150.f, 29.f }, { 160.f, 28.5f }, { 170.f, 27.5f },
        { 180.f, 32.f }, { 190.f, 36.f }, { 198.4f, 41.6f }, { 210.f, 37.f }, { 220.f, 23.f }, { 230.f, 23.f },
        { 240.f, 23.f }, { 250.f, 25.f }, { 260.f, 29.f }, { 270.f, 33.f }, { 280.f, 39.5f }, { 286.f, 44.9f },
        { 300.f, 40.f }, { 310.f, 41.f }, { 320.f, 42.f }, { 330.f, 38.f }, { 340.f, 37.f }, { 350.f, 37.f },
    } };
    inline constexpr float kRingWallPad = 0.5f;            // NM's floor edge sits about 0.5 yd inside the real wall
    inline constexpr float kRingFloorZMin = -60.f;         // the floor flood z -56.5 to -51.5
    inline constexpr float kRingFloorZMax = -46.f;         // the gallery (z -37 to -34) is not the floor

    // The gates' bearings (the alcove samples above) [DB positions].
    inline constexpr float kEastGateBearingDeg = 11.7f;    // 161522, where the champions come in
    inline constexpr float kNorthGateBearingDeg = 103.9f;  // 161524, the exit
    inline constexpr float kWestGateBearingDeg = 198.4f;   // 161523, the entrance
    inline constexpr float kSouthGateBearingDeg = 286.f;   // 161525, where the waves come in

    // The floor polygon (map coordinates), built once.
    inline std::vector<Vec2> const& RingFloor()
    {
        static std::vector<Vec2> const poly = []()
        {
            std::vector<Vec2> p;
            p.reserve(kRingWall.size());
            Vec2 const c = BlackrockDepthsRework::kRingCenter.XY();
            for (WallSample const& s : kRingWall)
                p.push_back(DungeonKit::Advance(c, Radians(s.bearingDeg), s.distance + kRingWallPad));
            return p;
        }();
        return poly;
    }

    inline BlackrockDepthsRework::Arena RingFloorArena()
    {
        return BlackrockDepthsRework::Arena(BlackrockDepthsRework::ArenaRegion::Polygon(RingFloor(), kRingFloorZMin,
            kRingFloorZMax));
    }

    inline bool OnFloorPlane(Vec2 p)
    {
        std::vector<Vec2> const& poly = RingFloor();
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(poly), p);
    }

    inline bool OnFloor(Vec2 p, float z)
    {
        return z >= kRingFloorZMin && z <= kRingFloorZMax && OnFloorPlane(p);
    }

    // At least `margin` yd inside the floor's edge (a unit that came through a gate and is clear of its alcove).
    inline bool WellInside(Vec2 p, float margin)
    {
        std::vector<Vec2> const& poly = RingFloor();
        std::span<Vec2 const> const s(poly);
        if (!DungeonKit::PointInPolygon(s, p))
            return false;
        for (std::size_t i = 0, j = s.size() - 1; i < s.size(); j = i++)
            if (DungeonKit::SegmentDistance(s[j], s[i], p) < margin)
                return false;
        return true;
    }

    // The opener's first beast lays its type's opening debuff once it stands kGateClearYd inside the floor
    // (orchestrator default after R-1-RING MN-1: cast from the south alcove the 30 yd aura reached nobody).
    inline bool OpeningDebuffDue(bool pending, Vec2 at)
    {
        return pending && WellInside(at, kGateClearYd);
    }

    // The wall along a ray from `origin` (on the floor) looking along `orientation`; nullopt from outside.
    inline std::optional<float> WallDistance(Vec2 origin, float orientation)
    {
        std::vector<Vec2> const& poly = RingFloor();
        return DungeonKit::RayToPolygonEdge(std::span<Vec2 const>(poly), origin, orientation);
    }

    // "To the wall" (D5's Bull Rush and Web Strands, D6's Piercing Shot): the end of a line from `origin` through
    // `through`, stopped `inset` yd short of the wall.
    inline std::optional<Vec2> WallEnd(Vec2 origin, Vec2 through, float inset = 0.5f)
    {
        std::vector<Vec2> const& poly = RingFloor();
        return DungeonKit::LaneEndAtWall(std::span<Vec2 const>(poly), origin, through, inset);
    }

    // RL4: the wedge's cone length, the farthest wall inside its 90 degrees from the center, capped.
    inline float WedgeLength(float facing)
    {
        Vec2 const c = BlackrockDepthsRework::kRingCenter.XY();
        float best = 0.f;
        for (int deg = -45; deg <= 45; deg += 5)
            if (std::optional<float> const d = WallDistance(c, facing + Radians(static_cast<float>(deg))))
                best = std::max(best, *d);
        return std::min(best, kTrialFireMaxLength);
    }

    // RL4: where the eruption stalkers stand in a wedge (on its center line and its two half-lines), the ones off the
    // floor dropped.
    inline std::vector<Vec2> WedgeBurstSpots(float facing, float length)
    {
        struct Spot
        {
            float offsetDeg;
            float frac;
        };
        Vec2 const c = BlackrockDepthsRework::kRingCenter.XY();
        std::vector<Vec2> out;
        for (Spot const s : { Spot{ 0.f, 0.25f }, Spot{ 0.f, 0.55f }, Spot{ 0.f, 0.85f }, Spot{ -25.f, 0.6f },
            Spot{ 25.f, 0.6f } })
        {
            Vec2 const p = DungeonKit::Advance(c, facing + Radians(s.offsetDeg), length * s.frac);
            if (OnFloorPlane(p))
                out.push_back(p);
        }
        return out;
    }

    // Grimstone's spots (the stock script_waypoint rows of 10096 [db]): the ring center (wp0) and his waiting corner
    // (wp2); the rest of the stock walk is cut (ruling 26).
    inline constexpr Point3 kGrimstoneCenter{ 604.8f, -191.1f, -54.1f };
    inline constexpr Point3 kGrimstoneCorner{ 621.4f, -214.5f, -52.8f };
    inline constexpr float kChampionSpawnO = 3.418f;        // the stock champion summon's orientation
    inline constexpr float kWaveSpawnO = 1.857f;            // the stock wave summon's orientation

    // The Arena Spoils chest after the Encore (stock, unchanged; section 7 #16) and the Theldren kill credit (quest
    // 9015).
    inline constexpr Point3 kArenaSpoilsSpot{ 596.48f, -187.91f, -54.14f };
    inline constexpr float kArenaSpoilsO = 4.9f;
    inline constexpr std::uint32_t kArenaSpoilsDespawnSec = 300;
    inline constexpr std::uint32_t NPC_THELDREN_KILL_CREDIT = 16166;
}

#endif
