/*
 * mod-dungeon-bosses, Blackrock Depths D21:
 * The Seven (Anger'rel 9035, Seeth'rel 9038, Dope'rel 9040, Gloom'rel 9037, Vile'rel 9036, Hate'rel 9034, Doom'rel
 * 9039), the pure, host-testable part (no engine headers). Build spec S4 "The Seven"
 * (docs/dungeons/blackrock-depths-4-imperial-seat.md, TS1-TS10; rulings 72-74, 88, 90, 91), handoff sections 3.4 (rows
 * D21), 3.5, 3.6 (320k / 450k shared), 3.8, 3.9 (the `loner` row of `blackrock-depths-shapes-2`, tag 22), section 7
 * #18. Tested by tests/brd_the_seven_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsTheSeven (211520-211579), declared in apps/dbc-tools
 *                source/npcs/blackrock_depths/the_seven.py; the stock kit spells kept as they are
 *   Ghosts       the rotation order (= the stock release order, BlackrockDepthsRework::kTheSeven), each ghost's mood,
 *                its rank on the kill order and the interrupt list, its texts
 *   Rotation     section 7 #18: Anger'rel alone for 0-20 s, then every 20 s the next ghost rises and the one corporeal
 *                longest fades, so each is corporeal for 40 s and Doom'rel rises at 120 s (StepAt, Rotation)
 *   GhostTurn    one ghost's corporeal turn: Gather Doom (3 s cast every 8 s, heroic 2 s every 6 s, first 3 s after it
 *                rises), its energy (three landed casts), at most one mood per turn, and which kit casts still fit
 *                before the next Gather Doom
 *   Kit          the stock kits kept (S4 "Stock kit", ruling 73), with the copies rule 15 asks for, as a timer table
 *   Picks        Furious Charge's target (the farthest player beyond 10 yd), Seething Cold's loners (not within 6 yd
 *                of 2 others: the registry's Cluster(2) rule), Dopey Haze's stumble (moved since the last second)
 *
 * Ghost index = rotation order: 0 Anger'rel, 1 Seeth'rel, 2 Dope'rel, 3 Gloom'rel, 4 Vile'rel, 5 Hate'rel, 6 Doom'rel.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_THE_SEVEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_THE_SEVEN_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdTheSeven
{
    using DungeonKit::NH;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsTheSeven;

    enum TheSevenSpells : std::uint32_t
    {
        // TS1 the rotation
        SPELL_TS_INCORPOREAL         = kSpellSlice.first + 0,   // 211520 a shade: -90% damage taken (lasting look)
        SPELL_TS_FADE_LOOK           = kSpellSlice.first + 1,   // 211521 look: the flash as a ghost fades
        // TS2 Gather Doom
        SPELL_TS_GATHER_DOOM         = kSpellSlice.first + 2,   // 211522 the 3 s interruptible cast (normal)
        SPELL_TS_GATHER_DOOM_HEROIC  = kSpellSlice.first + 3,   // 211523 the 2 s interruptible cast (heroic)
        SPELL_TS_GATHERED_DOOM       = kSpellSlice.first + 4,   // 211524 the energy: a stack per landed cast, 3 max
        // TS3 Furious Charge (Anger'rel)
        SPELL_TS_FURIOUS_CHARGE_CAST = kSpellSlice.first + 5,   // 211525 the 3 s mood bar
        SPELL_TS_FURIOUS_CHARGE_LOOK = kSpellSlice.first + 6,   // 211526 look: the charge trail at the target
        SPELL_TS_FURIOUS_CHARGE      = kSpellSlice.first + 7,   // 211527 the charge line's hit (resolve copy)
        SPELL_TS_FURIOUS_STOMP       = kSpellSlice.first + 8,   // 211528 look: the harmless stomp (nobody far)
        // TS4 Seething Cold (Seeth'rel)
        SPELL_TS_SEETHING_COLD_CAST  = kSpellSlice.first + 9,   // 211529 the 3 s mood bar
        SPELL_TS_SEETHING_COLD       = kSpellSlice.first + 10,  // 211530 a loner's tick: Frost hit and -30% speed
        // TS5 Dopey Haze (Dope'rel)
        SPELL_TS_DOPEY_HAZE_CAST     = kSpellSlice.first + 11,  // 211531 the 3 s mood bar
        SPELL_TS_DOPEY_HAZE          = kSpellSlice.first + 12,  // 211532 the 6 s haze on every player (the look)
        SPELL_TS_STUMBLE             = kSpellSlice.first + 13,  // 211533 a stumble: the Physical hit
        // TS6 Gloom (Gloom'rel)
        SPELL_TS_GLOOM_CAST          = kSpellSlice.first + 14,  // 211534 the 3 s mood bar
        SPELL_TS_GLOOM               = kSpellSlice.first + 15,  // 211535 players: -50% healing received, 12 s
        SPELL_TS_RECKLESSNESS        = kSpellSlice.first + 16,  // 211536 Gloom'rel: +50% damage done, 12 s
        // TS7 Vile Communion (Vile'rel)
        SPELL_TS_VILE_COMMUNION_CAST = kSpellSlice.first + 17,  // 211537 the 3 s mood bar
        SPELL_TS_VILE_COMMUNION      = kSpellSlice.first + 18,  // 211538 the 6 s channel, interruptible
        SPELL_TS_VILE_COMMUNION_LOOK = kSpellSlice.first + 19,  // 211539 look: the healing hands again at 3 s
        // TS8 Hatred (Hate'rel)
        SPELL_TS_HATRED_CAST         = kSpellSlice.first + 20,  // 211540 the 3 s mood bar
        SPELL_TS_HATRED_MARK         = kSpellSlice.first + 21,  // 211541 the 8 s mark on every player (the ring)
        SPELL_TS_HATRED              = kSpellSlice.first + 22,  // 211542 a tick: Shadow (resolve copy)
        // TS9 Doom (Doom'rel)
        SPELL_TS_DOOM_CAST           = kSpellSlice.first + 23,  // 211543 the 3 s mood bar
        SPELL_TS_DOOM                = kSpellSlice.first + 24,  // 211544 the 6 s mark (the skull, the debuff read)
        SPELL_TS_DOOM_RING           = kSpellSlice.first + 25,  // 211545 the 6 s mark's ring under the bearer
        SPELL_TS_DOOM_BLAST          = kSpellSlice.first + 26,  // 211546 the blast on the others (resolve copy)
        SPELL_TS_DOOM_BLAST_SELF     = kSpellSlice.first + 27,  // 211547 the blast on the marked player
        // TS10 and the kept kits' copies (rule 15)
        SPELL_TS_FROSTBOLT           = kSpellSlice.first + 28,  // 211548 Seeth'rel (stock 12675)
        SPELL_TS_CONE_OF_COLD        = kSpellSlice.first + 29,  // 211549 Seeth'rel (stock 15244)
        SPELL_TS_FROST_NOVA          = kSpellSlice.first + 30,  // 211550 Seeth'rel TS10 (stock 12674, root 2 s)
        SPELL_TS_BACKSTAB            = kSpellSlice.first + 31,  // 211551 Dope'rel (stock 15582, DD double-use)
        SPELL_TS_RUPTURE             = kSpellSlice.first + 32,  // 211552 Dope'rel (stock 15583)
        SPELL_TS_GOUGE               = kSpellSlice.first + 33,  // 211553 Dope'rel TS10 (stock 12540, 2 s)
        SPELL_TS_MIND_BLAST          = kSpellSlice.first + 34,  // 211554 Vile'rel (stock 15587)
        SPELL_TS_SHADOW_BOLT         = kSpellSlice.first + 35,  // 211555 Hate'rel (stock 15232, DD double-use)
        SPELL_TS_SHADOW_BOLT_VOLLEY  = kSpellSlice.first + 36,  // 211556 Doom'rel (stock 15245)
        SPELL_TS_IMMOLATE            = kSpellSlice.first + 37,  // 211557 Doom'rel (stock 12742)
        // 211558-211579 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_TS_IMMOLATE;
    static_assert(kLastSpell <= kSpellSlice.last, "the Seven's spells must stay in their slice");

    // Stock spells the kits keep as they are (S4 "Stock kit": the weapon strikes scale with the ghost's
    // DamageModifier, the buffs deal no damage; none is on DD's double-use list).
    enum TheSevenStockSpells : std::uint32_t
    {
        SPELL_STOCK_STRIKE          = 15580,    // Anger'rel
        SPELL_STOCK_SUNDER_ARMOR    = 11971,    // Anger'rel
        SPELL_STOCK_SHIELD_BLOCK    = 12169,    // Anger'rel
        SPELL_STOCK_SHIELD_WALL     = 15062,    // Anger'rel
        SPELL_STOCK_FROST_ARMOR     = 12544,    // Seeth'rel (out of combat and at each rise)
        SPELL_STOCK_SINISTER_STRIKE = 15581,    // Dope'rel
        SPELL_STOCK_EVASION         = 15087,    // Dope'rel
        SPELL_STOCK_PW_SHIELD       = 11974,    // Vile'rel
        SPELL_STOCK_DEMON_ARMOR     = 13787,    // Doom'rel
        SPELL_STOCK_LEARN_SMELT     = 14894,    // Gloom'rel's gossip: Smelt Dark Iron (stock boss_gloomrel)
    };

    // Registry tags. 22 is the G2 drill's `loner` row (BM MechanicDrill.h kBrd2BarTags: Stack/22, gated at 1); the
    // others are this fight's own.
    enum TheSevenTags : std::uint32_t
    {
        TAG_TS_SEETHING_COLD    = 22,   // TS4 (drill row `loner`)
        TAG_TS_FURIOUS_CHARGE   = 31,   // TS3 the charge lines
        TAG_TS_FURIOUS_STACK    = 32,   // TS3 the 10 yd collapse round Anger'rel
        TAG_TS_DOPEY_HAZE       = 33,   // TS5
        TAG_TS_HATRED           = 34,   // TS8
        TAG_TS_DOOM             = 35,   // TS9
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The ghosts
    // ----------------------------------------------------------------------------------------------------------------

    enum Ghost : std::uint8_t
    {
        GHOST_ANGERREL = 0,
        GHOST_SEETHREL = 1,
        GHOST_DOPEREL  = 2,
        GHOST_GLOOMREL = 3,
        GHOST_VILEREL  = 4,
        GHOST_HATEREL  = 5,
        GHOST_DOOMREL  = 6,
    };
    inline constexpr std::size_t kGhostCount = 7;
    static_assert(BlackrockDepthsRework::kTheSeven.size() == kGhostCount, "seven ghosts");
    static_assert(BlackrockDepthsRework::kTheSeven[GHOST_ANGERREL] == BlackrockDepthsRework::NPC_ANGERREL
        && BlackrockDepthsRework::kTheSeven[GHOST_SEETHREL] == BlackrockDepthsRework::NPC_SEETHREL
        && BlackrockDepthsRework::kTheSeven[GHOST_DOPEREL] == BlackrockDepthsRework::NPC_DOPEREL
        && BlackrockDepthsRework::kTheSeven[GHOST_GLOOMREL] == BlackrockDepthsRework::NPC_GLOOMREL
        && BlackrockDepthsRework::kTheSeven[GHOST_VILEREL] == BlackrockDepthsRework::NPC_VILEREL
        && BlackrockDepthsRework::kTheSeven[GHOST_HATEREL] == BlackrockDepthsRework::NPC_HATEREL
        && BlackrockDepthsRework::kTheSeven[GHOST_DOOMREL] == BlackrockDepthsRework::NPC_DOOMREL,
        "the rotation order is the stock release order");

    // The ghost that runs the fight (the gossip start, the rotation clock, the registry encounter and the descriptor):
    // Doom'rel, the instance's boss unit of BOSS_THE_SEVEN (GetGuidData(kGuidBossBase + 16)) and the leader.
    inline constexpr std::uint8_t kConductor = GHOST_DOOMREL;

    constexpr std::optional<Ghost> GhostOf(std::uint32_t entry)
    {
        if (std::optional<std::uint32_t> const i = BlackrockDepthsRework::SevenIndex(entry))
            return static_cast<Ghost>(*i);
        return std::nullopt;
    }

    constexpr std::uint32_t EntryOf(Ghost ghost)
    {
        return BlackrockDepthsRework::kTheSeven[ghost];
    }

    // The mood of each ghost, by ghost index (TS3-TS9).
    enum class Mood : std::uint8_t
    {
        FuriousCharge,  // Anger'rel   TS3 a Stack round him, the charges
        SeethingCold,   // Seeth'rel   TS4 an anchorless Stack, Cluster(2)
        DopeyHaze,      // Dope'rel    TS5 HoldStill
        Gloom,          // Gloom'rel   TS6 auras
        VileCommunion,  // Vile'rel    TS7 the interruptible channel
        Hatred,         // Hate'rel    TS8 Spread
        Doom,           // Doom'rel    TS9 RunOut
    };

    constexpr Mood MoodOf(Ghost ghost)
    {
        return static_cast<Mood>(ghost);
    }

    inline constexpr std::array<char const*, kGhostCount> kGhostKeys{ { "angerrel", "seethrel", "doperel",
        "gloomrel", "vilerel", "haterel", "doomrel" } };
    inline constexpr std::array<char const*, kGhostCount> kMoodKeys{ { "furious-charge", "seething-cold",
        "dopey-haze", "gloom", "vile-communion", "hatred", "doom" } };

    // The 3 s mood bar of each ghost (Physical: no interrupt school lockout ever stops it, rule 5).
    inline constexpr std::array<std::uint32_t, kGhostCount> kMoodCast{ { SPELL_TS_FURIOUS_CHARGE_CAST,
        SPELL_TS_SEETHING_COLD_CAST, SPELL_TS_DOPEY_HAZE_CAST, SPELL_TS_GLOOM_CAST, SPELL_TS_VILE_COMMUNION_CAST,
        SPELL_TS_HATRED_CAST, SPELL_TS_DOOM_CAST } };

    // The kill order and the interrupt list (S4 "Boss data"): Vile'rel, Doom'rel, Anger'rel, Dope'rel, Hate'rel,
    // Seeth'rel, Gloom'rel. RankOf: 1 (first) to 7 (last).
    inline constexpr std::array<Ghost, kGhostCount> kRankOrder{ { GHOST_VILEREL, GHOST_DOOMREL, GHOST_ANGERREL,
        GHOST_DOPEREL, GHOST_HATEREL, GHOST_SEETHREL, GHOST_GLOOMREL } };

    constexpr std::uint8_t RankOf(Ghost ghost)
    {
        for (std::size_t i = 0; i < kRankOrder.size(); ++i)
            if (kRankOrder[i] == ghost)
                return static_cast<std::uint8_t>(i + 1);
        return 0;
    }

    // Descriptor priorities (higher first): the kill order 7 (Vile'rel) .. 1 (Gloom'rel), above the owner's 0. The
    // interrupt list puts Vile Communion above every Gather Doom (kVileCommunionKick), then Gather Doom by the same
    // rank (8 .. 2). The kits' own casts are "never kick" (0), so the bots keep their kicks for the list.
    constexpr std::int8_t KillPriority(Ghost ghost)
    {
        return static_cast<std::int8_t>(kGhostCount + 1 - RankOf(ghost));
    }

    constexpr std::uint8_t GatherKickPriority(Ghost ghost)
    {
        return static_cast<std::uint8_t>(kGhostCount + 2 - RankOf(ghost));
    }

    inline constexpr std::uint8_t kVileCommunionKick = 9;
    inline constexpr std::uint8_t kDispelFrostNova = 1;     // Frost Nova's root: a reward (Magic)

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (S4 "Text"; section 8 #24: one rise line and one mood line per ghost, yells). Doom'rel's group 0 is his
    // stock challenge line ("You have challenged the Seven, and now you will die!", a say), kept at the gossip start.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint8_t SAY_DOOMREL_CHALLENGE = 0;

    constexpr std::uint8_t RiseText(Ghost ghost)
    {
        return ghost == GHOST_DOOMREL ? 1 : 0;
    }

    constexpr std::uint8_t MoodText(Ghost ghost)
    {
        return ghost == GHOST_DOOMREL ? 2 : 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "New mechanics", "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    // The shared pool (handoff 3.6): every ghost's template carries the whole pool as its own max health (normal by
    // its HealthModifier in the_seven.py, heroic by WP-H's override), so every frame reads the pool's number.
    inline constexpr NH<std::uint32_t> kPoolHealth{ 320000, 450000 };
    // A shade takes 90% less damage (TS1; the Incorporeal aura's MOD_DAMAGE_PERCENT_TAKEN).
    inline constexpr std::int32_t kShadeDamageTakenPct = -90;

    // TS1 the rotation (section 7 #18).
    inline constexpr std::uint32_t kStepMs = 20000;
    inline constexpr std::uint32_t kTurnMs = 2 * kStepMs;       // each ghost is corporeal 40 s

    // TS2 Gather Doom.
    inline constexpr NH<std::uint32_t> kGatherCastMs{ 3000, 2000 };
    inline constexpr NH<std::uint32_t> kGatherEveryMs{ 8000, 6000 };
    inline constexpr std::uint32_t kGatherFirstMs = 3000;       // after the rise
    inline constexpr std::uint32_t kEnergyFull = 3;             // landed casts that fill the energy
    inline constexpr std::uint32_t kMoodCastMs = 3000;          // the mood bar (not interruptible)

    // TS3 Furious Charge: 9 s, every 3 s a charge at the farthest player beyond 10 yd, hitting the target and anyone
    // in the 3 yd line; nobody beyond 10 yd: a harmless stomp. Each line shows 1 s before the charge.
    inline constexpr NH<float> kChargePct{ 30.f, 45.f };
    inline constexpr float kChargeSafeYd = 10.f;
    inline constexpr float kChargeWidthYd = 3.f;
    inline constexpr float kChargeOverrunYd = 2.f;              // the line runs this far past the target
    inline constexpr std::uint32_t kChargeLifeMs = 9000;
    inline constexpr std::uint32_t kChargeEveryMs = 3000;
    inline constexpr std::uint32_t kChargeCount = kChargeLifeMs / kChargeEveryMs;
    inline constexpr std::uint32_t kChargeWarnMs = 1000;
    inline constexpr float kChargeSpeed = 30.f;                 // yd/s

    // TS4 Seething Cold: 10 s, every second the players not within 6 yd of 2 others take 6% / 10% and -30% speed.
    inline constexpr NH<float> kColdPct{ 6.f, 10.f };
    inline constexpr float kColdRadiusYd = 6.f;
    inline constexpr std::uint32_t kColdMinOthers = 2;          // G2: Cluster(2), not Count(3)
    inline constexpr std::uint32_t kColdLifeMs = 10000;
    inline constexpr std::uint32_t kColdTickMs = 1000;
    inline constexpr std::uint32_t kColdTicks = kColdLifeMs / kColdTickMs;
    inline constexpr std::uint32_t kColdSlowMs = 1500;          // the slow outlasts the tick a little
    inline constexpr std::int32_t kColdSlowPct = 30;

    // TS5 Dopey Haze: 6 s, a player who moves stumbles once per second of movement: 15% / 25% + Weakened.
    inline constexpr NH<float> kStumblePct{ 15.f, 25.f };
    inline constexpr std::uint32_t kHazeLifeMs = 6000;
    inline constexpr std::uint32_t kHazeTickMs = 1000;
    inline constexpr std::uint32_t kHazeTicks = kHazeLifeMs / kHazeTickMs;
    inline constexpr float kHazeToleranceYd = 0.5f;             // the registry HoldStill's tolerance too

    // TS6 Gloom: 12 s, healing received -50% for the players; Gloom'rel +50% damage done.
    inline constexpr std::uint32_t kGloomMs = 12000;
    inline constexpr std::int32_t kGloomHealingPct = -50;
    inline constexpr std::int32_t kRecklessnessPct = 50;

    // TS7 Vile Communion: a 6 s channel that heals the shared pool by 5% / 8% (a sixth a second; a kick stops the
    // rest). The look is cast again at 3 s.
    inline constexpr NH<float> kVileHealPct{ 5.f, 8.f };
    inline constexpr std::uint32_t kVileChannelMs = 6000;
    inline constexpr std::uint32_t kVileTickMs = 1000;
    inline constexpr std::uint32_t kVileTicks = kVileChannelMs / kVileTickMs;
    inline constexpr std::uint32_t kVileLookAtMs = 3000;

    constexpr float VileTickPct(bool heroic)
    {
        return kVileHealPct(heroic) / static_cast<float>(kVileTicks);
    }

    // TS8 Hatred: 8 s, players within 6 yd of another player take 5% / 8% each second (eight Spreads a second apart).
    inline constexpr NH<float> kHatredPct{ 5.f, 8.f };
    inline constexpr float kHatredRadiusYd = 6.f;
    inline constexpr std::uint32_t kHatredLifeMs = 8000;
    inline constexpr std::uint32_t kHatredTickMs = 1000;
    inline constexpr std::uint32_t kHatredTicks = kHatredLifeMs / kHatredTickMs;

    // TS9 Doom: 1 (heroic 2) random players marked, the tank included (ruling 88); after 6 s a 10 yd blast round each:
    // the others 30% / 45% + Weakened, the marked player 20% / 30%.
    inline constexpr NH<std::uint32_t> kDoomMarks{ 1, 2 };
    inline constexpr NH<float> kDoomOthersPct{ 30.f, 45.f };
    inline constexpr NH<float> kDoomSelfPct{ 20.f, 30.f };
    inline constexpr float kDoomRadiusYd = 10.f;
    inline constexpr std::uint32_t kDoomMarkMs = 6000;

    // The kept kits' copies (rule 15; "stock rescaled", gap 36: this WP's defaults from the BRS convention, designer
    // question 2). Percent of the reference row, the tank's row on the tank (RefFlatOn).
    inline constexpr NH<float> kFrostboltPct{ 6.f, 8.f };
    inline constexpr NH<float> kConeOfColdPct{ 8.f, 10.f };
    inline constexpr NH<float> kFrostNovaPct{ 6.f, 8.f };
    inline constexpr std::uint32_t kFrostNovaRootMs = 2000;     // TS10: 8 s -> 2 s
    inline constexpr float kFrostNovaRadiusYd = 10.f;
    inline constexpr NH<float> kBackstabPct{ 12.f, 15.f };
    inline constexpr NH<float> kRupturePct{ 2.f, 3.f };         // a tick every 2 s for 10 s
    inline constexpr NH<float> kGougePct{ 3.f, 4.f };
    inline constexpr std::uint32_t kGougeMs = 2000;             // TS10: 4 s -> 2 s, any player (ruling 90)
    inline constexpr NH<float> kMindBlastPct{ 8.f, 10.f };
    inline constexpr NH<float> kShadowBoltPct{ 12.f, 15.f };
    inline constexpr NH<float> kVolleyPct{ 8.f, 10.f };
    inline constexpr float kVolleyRadiusYd = 30.f;
    inline constexpr NH<float> kImmolatePct{ 8.f, 10.f };
    inline constexpr NH<float> kImmolateTickPct{ 2.f, 3.f };    // every 3 s for 21 s

    // ----------------------------------------------------------------------------------------------------------------
    // TS1 the rotation (section 7 #18). Step n happens n x 20 s after the pull: ghost n mod 7 rises, ghost (n - 2) mod
    // 7 fades (from step 2 on). Step 0 is the pull: Anger'rel rises alone.
    // ----------------------------------------------------------------------------------------------------------------

    struct RotationStep
    {
        std::optional<Ghost> rise;
        std::optional<Ghost> fade;
    };

    constexpr RotationStep StepAt(std::uint32_t n)
    {
        RotationStep s;
        s.rise = static_cast<Ghost>(n % kGhostCount);
        if (n >= 2)
            s.fade = static_cast<Ghost>((n - 2) % kGhostCount);
        return s;
    }

    constexpr std::uint64_t StepTimeMs(std::uint32_t n)
    {
        return static_cast<std::uint64_t>(n) * kStepMs;
    }

    // Who is corporeal `elapsedMs` after the pull, by the clock alone (a fade held back by a mood bar in progress is
    // the engine's business).
    constexpr std::array<bool, kGhostCount> CorporealAt(std::uint64_t elapsedMs)
    {
        std::array<bool, kGhostCount> out{};
        std::uint64_t const n = elapsedMs / kStepMs;
        out[n % kGhostCount] = true;
        if (n >= 1)
            out[(n - 1) % kGhostCount] = true;
        return out;
    }

    // The rotation's clock: Due returns each step once, in order, when its time has come.
    class Rotation
    {
    public:
        void Start() { _next = 0; _running = true; }
        void Stop() { _running = false; }
        bool Running() const { return _running; }
        std::uint32_t Next() const { return _next; }

        // The next step if it is due at `elapsedMs` (call until it returns none).
        std::optional<RotationStep> Due(std::uint64_t elapsedMs)
        {
            if (!_running || elapsedMs < StepTimeMs(_next))
                return std::nullopt;
            return StepAt(_next++);
        }

    private:
        std::uint32_t _next = 0;
        bool _running = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TS2 one ghost's corporeal turn: Gather Doom and the energy
    // ----------------------------------------------------------------------------------------------------------------

    class GhostTurn
    {
    public:
        // The rise: energy 0 (each turn starts empty), no mood yet, the first Gather Doom 3 s later, the fade 40 s
        // later.
        void Rise(std::uint64_t now, bool heroic)
        {
            _heroic = heroic;
            _active = true;
            _energy = 0;
            _moodSpent = false;
            _gathering = false;
            _fadeAt = now + kTurnMs;
            _nextGather = now + kGatherFirstMs;
        }

        void Fade()
        {
            _active = false;
            _gathering = false;
        }

        bool Active() const { return _active; }
        bool Heroic() const { return _heroic; }
        std::uint32_t Energy() const { return _energy; }
        bool MoodSpent() const { return _moodSpent; }
        bool Gathering() const { return _gathering; }
        std::uint64_t NextGather() const { return _nextGather; }
        std::uint64_t FadeAt() const { return _fadeAt; }
        std::uint32_t CastMs() const { return kGatherCastMs(_heroic); }

        // A Gather Doom may start now: corporeal, no mood yet this turn, the energy not full, its time come, and it
        // lands before the fade (a cast the fade would cut is never started).
        bool GatherDue(std::uint64_t now) const
        {
            return _active && !_moodSpent && _energy < kEnergyFull && !_gathering && now >= _nextGather
                && now + CastMs() <= _fadeAt;
        }

        // The cast started: the next one is due one cadence after this start.
        void GatherStarted(std::uint64_t now)
        {
            _gathering = true;
            _nextGather = now + kGatherEveryMs(_heroic);
        }

        // The cast could not start (a silence, a school lockout): a blocked cast, the next one on the cadence.
        void GatherRefused(std::uint64_t now)
        {
            _gathering = false;
            _nextGather = now + kGatherEveryMs(_heroic);
        }

        // The cast landed: one energy. True when the energy is full now (the mood is due).
        bool GatherLanded()
        {
            _gathering = false;
            if (!_active || _moodSpent || _energy >= kEnergyFull)
                return false;
            ++_energy;
            return _energy >= kEnergyFull;
        }

        // The cast was interrupted (a kick, a silence mid-cast): no energy.
        void GatherInterrupted() { _gathering = false; }

        // `.dbtest brd seven mood`: the energy full now and the turn's mood not had yet (a corporeal ghost only).
        void ForceFull()
        {
            if (!_active)
                return;
            _energy = kEnergyFull;
            _moodSpent = false;
            _gathering = false;
        }

        // Full energy and no mood this turn yet (section 7 #18: at most one mood per ghost turn).
        bool MoodDue() const { return _active && !_moodSpent && _energy >= kEnergyFull; }

        // The mood bar started: the energy is spent, and the turn has had its mood.
        void MoodStarted()
        {
            _moodSpent = true;
            _energy = 0;
        }

        // A kit cast of `castMs` may start now: no Gather Doom comes due before it ends (an instant always fits; so
        // does anything once the turn has had its mood).
        bool KitCastFits(std::uint64_t now, std::uint32_t castMs) const
        {
            if (castMs == 0 || !_active || _moodSpent || _energy >= kEnergyFull)
                return true;
            return now + castMs <= _nextGather;
        }

    private:
        bool _heroic = false;
        bool _active = false;
        bool _gathering = false;
        bool _moodSpent = false;
        std::uint32_t _energy = 0;
        std::uint64_t _fadeAt = 0;
        std::uint64_t _nextGather = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The kept kits (S4 "Stock kit", ruling 73): the stock timers, from the ghost's rise. Gone: Frost Ward, Hate'rel's
    // Strike, Curse of Weakness, Summon Voidwalkers (ruling 91), Prayer of Healing and Heal (Vile Communion replaces
    // them), Hate'rel's dead self-targeted bolt row; his victim bolt repeats every 8-10 s (was 3.4-4.8 s).
    // ----------------------------------------------------------------------------------------------------------------

    enum class KitTarget : std::uint8_t
    {
        Victim,         // his victim (the tank)
        VictimBehind,   // his victim, only from behind it (Backstab)
        Self,           // himself (a buff, a nova round him, a cone in front of him, a volley)
        Random,         // a random player of the fight, the tank included (ruling 90: Gouge on anyone)
    };

    struct KitRow
    {
        Ghost ghost;
        std::uint32_t spell;
        KitTarget target;
        std::uint32_t castMs;           // 0: instant
        std::uint32_t firstMinMs;
        std::uint32_t firstMaxMs;
        std::uint32_t everyMinMs;
        std::uint32_t everyMaxMs;
    };

    inline constexpr std::array<KitRow, 19> kKit{ {
        // Anger'rel (stock SmartAI 9035): Strike, Sunder Armor, Shield Block, Shield Wall
        { GHOST_ANGERREL, SPELL_STOCK_STRIKE, KitTarget::Victim, 0, 5000, 7000, 5000, 7000 },
        { GHOST_ANGERREL, SPELL_STOCK_SUNDER_ARMOR, KitTarget::Victim, 0, 2000, 4000, 6000, 9000 },
        { GHOST_ANGERREL, SPELL_STOCK_SHIELD_BLOCK, KitTarget::Self, 0, 11000, 15000, 10000, 15000 },
        { GHOST_ANGERREL, SPELL_STOCK_SHIELD_WALL, KitTarget::Self, 0, 1000, 3000, 20000, 26000 },
        // Seeth'rel (9038): Frostbolt (3 s, repeat 3.4-4.8 s), Cone of Cold, Frost Nova (TS10: root 2 s)
        { GHOST_SEETHREL, SPELL_TS_FROSTBOLT, KitTarget::Victim, 3000, 0, 0, 3400, 4800 },
        { GHOST_SEETHREL, SPELL_TS_CONE_OF_COLD, KitTarget::Self, 0, 9000, 14000, 19000, 24000 },
        { GHOST_SEETHREL, SPELL_TS_FROST_NOVA, KitTarget::Self, 0, 12000, 16000, 20000, 23000 },
        // Dope'rel (9040): Sinister Strike, Backstab, Rupture, Gouge (TS10: 2 s, anyone), Evasion
        { GHOST_DOPEREL, SPELL_STOCK_SINISTER_STRIKE, KitTarget::Victim, 0, 5000, 7000, 5000, 7000 },
        { GHOST_DOPEREL, SPELL_TS_BACKSTAB, KitTarget::VictimBehind, 0, 3000, 7000, 5000, 9000 },
        { GHOST_DOPEREL, SPELL_TS_RUPTURE, KitTarget::Victim, 0, 2000, 4000, 14000, 16000 },
        { GHOST_DOPEREL, SPELL_TS_GOUGE, KitTarget::Random, 0, 8000, 10000, 9000, 15000 },
        { GHOST_DOPEREL, SPELL_STOCK_EVASION, KitTarget::Self, 0, 1000, 1000, 25000, 35000 },
        // Gloom'rel (9037): melee only
        // Vile'rel (9036): Mind Blast (1.5 s, repeat 3.4-4.8 s), Power Word: Shield
        { GHOST_VILEREL, SPELL_TS_MIND_BLAST, KitTarget::Victim, 1500, 0, 0, 3400, 4800 },
        { GHOST_VILEREL, SPELL_STOCK_PW_SHIELD, KitTarget::Self, 0, 20000, 30000, 60000, 120000 },
        // Hate'rel (9034): Shadow Bolt on his victim (8-10 s) and on a random player (14-17 s, then 15-20 s)
        { GHOST_HATEREL, SPELL_TS_SHADOW_BOLT, KitTarget::Victim, 3000, 0, 0, 8000, 10000 },
        { GHOST_HATEREL, SPELL_TS_SHADOW_BOLT, KitTarget::Random, 3000, 14000, 17000, 15000, 20000 },
        // Doom'rel (9039, stock boss_doomrel): Shadow Bolt Volley, Immolate (the stock rescheduling bug fixed: one
        // cast every 25 s), Demon Armor
        { GHOST_DOOMREL, SPELL_TS_SHADOW_BOLT_VOLLEY, KitTarget::Self, 3000, 10000, 10000, 12000, 12000 },
        { GHOST_DOOMREL, SPELL_TS_IMMOLATE, KitTarget::Random, 2000, 18000, 18000, 25000, 25000 },
        { GHOST_DOOMREL, SPELL_STOCK_DEMON_ARMOR, KitTarget::Self, 0, 16000, 16000, 300000, 300000 },
    } };

    // The buff a ghost keeps up out of combat and puts back at every rise (stock): Frost Armor on Seeth'rel, Demon
    // Armor on Doom'rel; 0 for the others.
    constexpr std::uint32_t ArmorOf(Ghost ghost)
    {
        switch (ghost)
        {
            case GHOST_SEETHREL: return SPELL_STOCK_FROST_ARMOR;
            case GHOST_DOOMREL:  return SPELL_STOCK_DEMON_ARMOR;
            default:             return 0;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    struct Body
    {
        std::uint64_t id = 0;
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
    };

    inline float PlaneDistance(Body const& a, Body const& b)
    {
        return std::hypot(a.x - b.x, a.y - b.y);
    }

    // TS3: the farthest body more than `minYd` from `from` on the plane (ties: the first); none when nobody is.
    inline std::optional<std::size_t> FarthestBeyond(Body const& from, std::vector<Body> const& bodies, float minYd)
    {
        std::optional<std::size_t> best;
        float bestYd = minYd;
        for (std::size_t i = 0; i < bodies.size(); ++i)
        {
            float const d = PlaneDistance(from, bodies[i]);
            if (d > bestYd)
            {
                bestYd = d;
                best = i;
            }
        }
        return best;
    }

    // TS4: the bodies with fewer than `minOthers` other bodies within `radiusYd` (on the plane, edge inclusive, within
    // `zBandYd` of height): the registry's Cluster(n) rule (Judge::ClusterMisses).
    inline std::vector<std::size_t> Loners(std::vector<Body> const& bodies, float radiusYd, std::uint32_t minOthers,
        float zBandYd = 6.f)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < bodies.size(); ++i)
        {
            std::uint32_t n = 0;
            for (std::size_t j = 0; j < bodies.size() && n < minOthers; ++j)
                if (j != i && PlaneDistance(bodies[i], bodies[j]) <= radiusYd
                    && std::fabs(bodies[i].z - bodies[j].z) <= zBandYd)
                    ++n;
            if (n < minOthers)
                out.push_back(i);
        }
        return out;
    }

    // TS5: moved farther than the tolerance on the plane since the last sample (a stumble).
    inline bool Stumbled(Body const& before, Body const& now, float toleranceYd = kHazeToleranceYd)
    {
        return PlaneDistance(before, now) > toleranceYd;
    }

    // TS3: the charge line's end, `overrunYd` past the target on the line from `from` (the target itself when the two
    // stand on top of each other).
    inline Body ChargeEnd(Body const& from, Body const& target, float overrunYd = kChargeOverrunYd)
    {
        float const d = PlaneDistance(from, target);
        if (d < 0.01f)
            return target;
        Body end = target;
        end.x = target.x + (target.x - from.x) / d * overrunYd;
        end.y = target.y + (target.y - from.y) / d * overrunYd;
        return end;
    }

    // The normal HealthModifier that gives a ghost the whole pool on its class base (creature_classlevelstats basehp0;
    // the_seven.py declares the same numbers, rounded to 3 decimals).
    constexpr double PoolHealthModifier(std::uint32_t classBase, std::uint32_t pool = kPoolHealth.normal)
    {
        return classBase ? static_cast<double>(pool) / static_cast<double>(classBase) : 0.0;
    }
}

#endif
