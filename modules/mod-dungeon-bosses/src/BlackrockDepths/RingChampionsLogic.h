/*
 * mod-dungeon-bosses, Blackrock Depths D5:
 * The Ring of Law: the six champions, the pure, host-testable part (no engine headers). Build spec S1 "Champion: Gorosh
 * the Dervish" to "Champion: Hedrum the Creeper" and the Ring's Build spec rows CH1, GO1-GO2, GZ1-GZ3, EV1-EV3,
 * OK1-OK3, AN1-AN3, HE1-HE2 (docs/dungeons/blackrock-depths-1-detention-block.md; rulings 23-25, 27, 88), handoff
 * sections 3.4 (rows D5), 3.5 (row D5), 3.6, 3.8 (NM: the floor is ~3,800 sq yd and not round; "to the wall" lines are
 * 23-43 yd), 3.9 (G1's `axe-return` and `rupture` rows), 3.10, section 7 #16. Tested by
 * tests/brd_ring_champions_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsRingChampions (210870-210959), declared in apps/dbc-tools
 *              source/npcs/blackrock_depths/ring_champions.py
 *   Tuning     NH<> constants straight from the build spec (normal / heroic); the unset cells (Bull Rush's width and
 *              speed, the Volley's rescale, Dervish Dance's speed) are this WP's defaults (report, designer questions)
 *   Picks      Killing Frenzy's cap, Devoured Magic, Raise Dead's count and cap, the Risen entries
 *   Geometry   the champions' lines to the wall (Bull Rush, Web Strands: BrdRingOfLaw::WallEnd), Arcane Rupture's
 *              outer edge (the farthest floor point from him), Web Strands' bearings
 *
 * The engine half: boss_ring_champions_rework.cpp (the six AIs, the Risen beasts and the Risen Champion). The frame
 * (Grimstone, Favor, the Sentences) is D4's: RingOfLawFight.h / RingOfLawLogic.h.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_RING_CHAMPIONS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_RING_CHAMPIONS_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include "RingOfLawLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdRingChampions
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsRingChampions;

    // The binding switch (S0): the six champions (9027-9032) are bound to this WP's scripts by apps/dbc-tools
    // source/npcs/blackrock_depths/ring_champions.py in the same change (they have no SmartAI rows to drop; the rev
    // takes Hedrum's Hate to Zero off his template addon). lib/test_blackrock_depths_ring_champions.py pins the two.
    inline constexpr bool kBound = true;

    enum RingChampionsSpells : std::uint32_t
    {
        // CH1 and the Risen
        SPELL_CH_TITLE_HOLDER       = kSpellSlice.first + 0,    // 210870 CH1 +10% damage done (the second champion)
        SPELL_CH_TITLE_FLASH        = kSpellSlice.first + 1,    // 210871 look: the title holder's arrival flash
        SPELL_CH_RISEN              = kSpellSlice.first + 2,    // 210872 look: the lasting purple state on a Risen unit
        // GO1-GO2 Gorosh
        SPELL_GO_DANCE_BAR          = kSpellSlice.first + 3,    // 210873 GO1 the 2 s bar while the line shows
        SPELL_GO_DANCE_LINE         = kSpellSlice.first + 4,    // 210874 GO1 the line's hit (resolve copy, Physical)
        SPELL_GO_DANCE_END          = kSpellSlice.first + 5,    // 210875 GO1 the end's Whirlwind (resolve copy)
        SPELL_GO_DANCE_LOOK         = kSpellSlice.first + 6,    // 210876 look: the cyclone state while he whirls
        SPELL_GO_AXE_LAND           = kSpellSlice.first + 7,    // 210877 GO2 the landing's hit (resolve copy)
        SPELL_GO_AXE_RETURN         = kSpellSlice.first + 8,    // 210878 GO2 the return line's hit (resolve copy)
        SPELL_GO_AXE_THROW_LOOK     = kSpellSlice.first + 9,    // 210879 look: the thrown axe (a dest missile)
        SPELL_GO_AXE_RETURN_LOOK    = kSpellSlice.first + 10,   // 210880 look: the axe flies home (a dest missile)
        SPELL_GO_AXE_CHAIN          = kSpellSlice.first + 11,   // 210881 look: the return line's chain (a channel)
        // GZ1-GZ3 Grizzle
        SPELL_GZ_RUSH_BAR           = kSpellSlice.first + 12,   // 210882 GZ1 the 2 s bar while the line shows
        SPELL_GZ_RUSH               = kSpellSlice.first + 13,   // 210883 GZ1 the charge's hit (resolve copy)
        SPELL_GZ_RUSH_LOOK          = kSpellSlice.first + 14,   // 210884 look: the dust trail while he charges
        SPELL_GZ_DAZED              = kSpellSlice.first + 15,   // 210885 GZ1 he hit the wall: +30% damage taken, 4 s
        SPELL_GZ_WALL_IMPACT        = kSpellSlice.first + 16,   // 210886 look: the wall impact
        SPELL_GZ_STOMP_BAR          = kSpellSlice.first + 17,   // 210887 GZ2 the 2.5 s wind-up
        SPELL_GZ_STOMP              = kSpellSlice.first + 18,   // 210888 GZ2 the ring's hit (resolve copy)
        SPELL_GZ_STOMP_STUN         = kSpellSlice.first + 19,   // 210889 GZ2 the 2 s stun (rider)
        SPELL_GZ_KILLING_FRENZY     = kSpellSlice.first + 20,   // 210890 GZ3 the stacking Enrage
        SPELL_GZ_FRENZY_FLASH       = kSpellSlice.first + 21,   // 210891 look: one flash per stack
        // EV1-EV3 Eviscerator
        SPELL_EV_SPELL_EATER        = kSpellSlice.first + 22,   // 210892 EV1 the 8 s shell (Magic: purge reward)
        SPELL_EV_DEVOURED           = kSpellSlice.first + 23,   // 210893 EV1 the Devoured stacks on him (the count)
        SPELL_EV_DEVOURED_MAGIC     = kSpellSlice.first + 24,   // 210894 EV1 the release's hit (the script's value)
        SPELL_EV_DEVOURED_LOOK      = kSpellSlice.first + 25,   // 210895 look: the shadow nova on the release
        SPELL_EV_OPEN_WOUNDS        = kSpellSlice.first + 26,   // 210896 EV2 the bleed (refflat periodic)
        SPELL_EV_OPEN_WOUNDS_JUMP   = kSpellSlice.first + 27,   // 210897 EV2 the jump's resolve (no damage)
        SPELL_EV_VOLLEY             = kSpellSlice.first + 28,   // 210898 EV3 Shadow Bolt Volley 15245 rescaled
        // OK1-OK3 Ok'thor
        SPELL_OK_RUPTURE_BAR        = kSpellSlice.first + 29,   // 210899 OK1 the 3 s bar (Physical: rule 5)
        SPELL_OK_RUPTURE            = kSpellSlice.first + 30,   // 210900 OK1 the donut's hit (resolve copy, Arcane)
        SPELL_OK_SHEEP_BOLT         = kSpellSlice.first + 31,   // 210901 OK2 the circle's hit (resolve copy, Arcane)
        SPELL_OK_SHEEP              = kSpellSlice.first + 32,   // 210902 OK2 the 2 s Polymorph (rider)
        SPELL_OK_SLOW               = kSpellSlice.first + 33,   // 210903 OK3 Slow 19137 on one player, 8 s
        // AN1-AN3 Anub'shiah
        SPELL_AN_RAISE_DEAD_BAR     = kSpellSlice.first + 34,   // 210904 AN1 the 2 s bar
        SPELL_AN_RAISE_DEAD_LOOK    = kSpellSlice.first + 35,   // 210905 look: the hands at the corpse spot
        SPELL_AN_WEB_SPIT           = kSpellSlice.first + 36,   // 210906 AN2 the impact's hit (resolve copy, Nature)
        SPELL_AN_WEB_ROOT           = kSpellSlice.first + 37,   // 210907 AN2 the 2 s root (rider)
        SPELL_AN_WEB_SLOW           = kSpellSlice.first + 38,   // 210908 AN2 the patch's -50% (the linger's rider)
        SPELL_AN_WEB_PATCH          = kSpellSlice.first + 39,   // 210909 look: the 20 s patch on a stalker
        SPELL_AN_WEB_SPIT_LOOK      = kSpellSlice.first + 40,   // 210910 look: the spit (a dest missile)
        SPELL_AN_CURSE_OF_TONGUES   = kSpellSlice.first + 41,   // 210911 AN3 Curse of Tongues 15470, one player, 15 s
        SPELL_AN_CURSE_OF_WEAKNESS  = kSpellSlice.first + 42,   // 210912 AN3 Curse of Weakness, -20%, one player, 15 s
        SPELL_AN_PATCH_TICK         = kSpellSlice.first + 43,   // 210913 AN2 the patch's tick (resolve copy, no damage)
        // HE1-HE2 Hedrum
        SPELL_HE_STRANDS_BAR        = kSpellSlice.first + 44,   // 210914 HE1 the 2 s bar (Web Spray's cast)
        SPELL_HE_STRANDS            = kSpellSlice.first + 45,   // 210915 HE1 a strand's hit (resolve copy, Nature)
        SPELL_HE_STRANDS_ROOT       = kSpellSlice.first + 46,   // 210916 HE1 the 2 s root (rider)
        SPELL_HE_STRANDS_SLOW       = kSpellSlice.first + 47,   // 210917 HE1 a strand's -30% (the linger's rider)
        SPELL_HE_STRAND_PATCH       = kSpellSlice.first + 48,   // 210918 look: web patches along a strand
        SPELL_HE_REEL_IN            = kSpellSlice.first + 49,   // 210919 HE2 look: the web wrap on the reeled player
        SPELL_HE_BANEFUL_BURST      = kSpellSlice.first + 50,   // 210920 HE2 the burst's hit (resolve copy, Nature)
        SPELL_HE_BANEFUL_POISON     = kSpellSlice.first + 51,   // 210921 HE2 the poison (rider; a dispel is a reward)
        SPELL_HE_BANEFUL_LOOK       = kSpellSlice.first + 52,   // 210922 look: the poison nova at him
        SPELL_HE_STRAND_TICK        = kSpellSlice.first + 53,   // 210923 HE1 a strand's tick (resolve copy, no damage)
        // 210924-210959 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_HE_STRAND_TICK;
    static_assert(kLastSpell <= kSpellSlice.last, "the champions' spells must stay in their slice");

    // Stock spells kept as they are (no rescale in S1): Gorosh's Mortal Strike and Bloodlust, Ok'thor's Arcane Bolt,
    // Anub'shiah's Shadow Bolt and Demon Armor. Retired (never cast): Whirlwind 15589, Ground Tremor 6524, Frenzy 8269,
    // Anti-Magic Shield 7121, Vicious Rend 14331, Arcane Explosion 1467, Polymorph 15534, Slow 19137 (the self-area
    // stock; OK3 is the one-target copy), Curse of Tongues 15470 and Curse of Weakness 12493 (30 yd / 120 s stock: AN3
    // are one-target copies), Enveloping Web 15471, Paralyzing Poison 3609, Baneful Poison 15475, Web Explosion 15474,
    // Hate to Zero 13767, Shadow Bolt Volley 15245 (EV3 is the rescaled copy).
    enum RingChampionsStockSpells : std::uint32_t
    {
        SPELL_STOCK_MORTAL_STRIKE   = 15708,    // Gorosh: 300% weapon damage, -50% healing 5 s (the tank)
        SPELL_STOCK_BLOODLUST       = 21049,    // Gorosh: +30% attack speed 30 s, Magic (a purge is a reward)
        SPELL_STOCK_ARCANE_BOLT     = 13748,    // Ok'thor: a 1 s filler on a random player
        SPELL_STOCK_SHADOW_BOLT     = 15472,    // Anub'shiah: a 3 s kickable bolt on the tank (an interrupt reward)
        SPELL_STOCK_DEMON_ARMOR     = 13787,    // Anub'shiah: +210 armor, 30 min (once, at the pull)
        SPELL_STOCK_HATE_TO_ZERO    = 13767,    // Hedrum's template aura (removed: a threat wipe breaks bot tanking)
    };

    // Registry tags. 6-10 are G1's drill rows (`axe-return` 6 landing, 7 shown, 8 locked; `rupture` 9 normal, 10
    // heroic: STAGE-G1-REPORT); the rest follow the Ring's 11-17 (D4).
    enum RingChampionsTags : std::uint32_t
    {
        TAG_GO_AXE              = 6,    // G1 kBrdTagAxe
        TAG_GO_AXE_SHOWN        = 7,    // G1 kBrdTagAxeShown (no damage)
        TAG_GO_AXE_RETURN       = 8,    // G1 kBrdTagAxeReturn
        TAG_OK_RUPTURE          = 9,    // G1 kBrdTagRupture (normal, 8 yd)
        TAG_OK_RUPTURE_HEROIC   = 10,   // G1 kBrdTagRuptureHeroic (6 yd)
        TAG_GO_DANCE_LINE       = 18,
        TAG_GO_DANCE_END        = 19,
        TAG_GZ_BULL_RUSH        = 20,
        TAG_GZ_STOMP            = 21,
        TAG_EV_OPEN_WOUNDS      = 22,
        TAG_OK_SHEEP_BOLT       = 23,
        TAG_AN_WEB_SPIT         = 24,
        TAG_AN_WEB_PATCH        = 25,
        TAG_HE_STRANDS          = 26,
        TAG_HE_STRAND_WEB       = 27,
        TAG_HE_BANEFUL_BURST    = 28,
    };

    // creature_text of Grizzle (9028): the stock "%s goes into a killing frenzy!" on each Killing Frenzy stack (the
    // rev turns its stock monster emote into a boss emote, type 41).
    enum GrizzleTexts : std::uint8_t
    {
        EMOTE_GZ_KILLING_FRENZY = 0,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The champions
    // ----------------------------------------------------------------------------------------------------------------
    enum class Champion : std::uint8_t
    {
        Gorosh = 0,
        Grizzle = 1,
        Eviscerator = 2,
        Okthor = 3,
        Anubshiah = 4,
        Hedrum = 5,
    };

    inline constexpr std::optional<Champion> ChampionOf(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < BlackrockDepthsRework::kRingChampions.size(); ++i)
            if (BlackrockDepthsRework::kRingChampions[i] == entry)
                return static_cast<Champion>(i);
        return std::nullopt;
    }

    inline constexpr char const* ChampionKey(Champion c)
    {
        switch (c)
        {
            case Champion::Gorosh:      return "gorosh";
            case Champion::Grizzle:     return "grizzle";
            case Champion::Eviscerator: return "eviscerator";
            case Champion::Okthor:      return "okthor";
            case Champion::Anubshiah:   return "anubshiah";
            case Champion::Hedrum:      return "hedrum";
        }
        return "?";
    }

    // Health (S1 Build spec, rulings 24-25: one shared baseline, two champions back to back): 90k normal on the
    // template (HealthModifier on the level 52 class base), 150k heroic (WP-H's overrides). Warriors (Gorosh, Grizzle,
    // Hedrum) on 2,371, paladins (Eviscerator, Ok'thor, Anub'shiah) on 1,897 [db creature_classlevelstats].
    inline constexpr std::uint32_t kChampionNormalHealth = 90000;
    inline constexpr std::uint32_t kChampionHeroicHealth = 150000;
    inline constexpr std::uint32_t kWarriorBaseHealth = 2371;
    inline constexpr std::uint32_t kPaladinBaseHealth = 1897;
    inline constexpr float kWarriorHealthModifier = 37.959f;
    inline constexpr float kPaladinHealthModifier = 47.443f;
    inline constexpr float kChampionDamageModifier = 7.5f;     // the stock value (unchanged)

    inline constexpr std::uint32_t HealthOf(std::uint32_t base, float modifier)
    {
        double const v = static_cast<double>(base) * static_cast<double>(modifier);
        std::uint32_t const floor = static_cast<std::uint32_t>(v);
        return static_cast<double>(floor) < v ? floor + 1 : floor;
    }

    // CH1 Title Holder (ruling 25): the second champion, +10% damage done for its fight.
    inline constexpr std::int32_t kTitleHolderDamagePct = 10;
    // The Molten legs token drops from the second champion at every difficulty (section 7 #16): Grimstone's title
    // holder gets this loot mode with Title Holder (rule 1: at its entry, never in JustDied). WP-L-1 puts the token's
    // rows on each champion's lootids (normal and heroic) at LootMode 4 (LOOT_MODE_HARD_MODE_2): the challenger lacks
    // the bit and never drops it. LootMode 2 stays the Encore's (Theldren).
    inline constexpr std::uint16_t kTitleHolderLootMode = 4;
    // A champion's death is recorded in Grimstone's DeathSpots (RingFrame::BeastDeaths) under this tag (the beasts use
    // their wave type + 1): AN1's Risen Champion rises where the challenger fell.
    inline constexpr std::uint32_t kChampionDeathTag = 50;

    // Every player aura the champions apply (rule 6: a champion's death or evade removes them; D4's wipe can take the
    // list too: RingOfLawFight.h's EndFrame, shared-file request in the D5 report).
    inline constexpr std::array<std::uint32_t, 12> kChampionPlayerAuras{ {
        SPELL_GZ_STOMP_STUN, SPELL_EV_OPEN_WOUNDS, SPELL_OK_SHEEP, SPELL_OK_SLOW, SPELL_AN_WEB_ROOT, SPELL_AN_WEB_SLOW,
        SPELL_AN_CURSE_OF_TONGUES, SPELL_AN_CURSE_OF_WEAKNESS, SPELL_HE_STRANDS_ROOT, SPELL_HE_STRANDS_SLOW,
        SPELL_HE_BANEFUL_POISON, SPELL_HE_REEL_IN,
    } };

    // A champion that has no frame to read (`.dbtest brd champions spawn`): every player within this range fights it.
    inline constexpr float kNoFrameRangeYd = 60.f;

    // ----------------------------------------------------------------------------------------------------------------
    // GO1-GO2 Gorosh the Dervish
    // ----------------------------------------------------------------------------------------------------------------
    // GO1 Dervish Dance: a random player (the tank too), a 2 s line from him to their spot, 6 yd wide; he whirls down
    // it and ends in an 8 yd Whirlwind at its end.
    inline constexpr NH<std::uint32_t> kDanceEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kDanceWarnMs = 2000;
    inline constexpr float kDanceWidth = 6.f;
    inline constexpr float kDanceEndRadius = 8.f;
    inline constexpr float kDanceSpeed = 20.f;              // yd/s down the line (this WP's default)
    inline constexpr float kDanceMinLength = 5.f;           // a target at his feet: the line runs at least this far
    inline constexpr NH<float> kDanceLinePct{ 20.f, 35.f };
    inline constexpr NH<float> kDanceEndPct{ 25.f, 40.f };
    // GO2 Returning Axe (G1's `axe-return` row: 3 yd 2 s landing, a 4 yd return line shown 4 s, locked the last 2 s).
    inline constexpr std::uint32_t kAxeEveryMs = 20000;
    inline constexpr std::uint32_t kAxeLandMs = 2000;
    inline constexpr float kAxeLandRadius = 3.f;
    inline constexpr std::uint32_t kAxeStuckMs = 6000;      // in the floor; the return line shows all of it
    inline constexpr std::uint32_t kAxeLockMs = 2000;       // the line locks this long before the axe flies
    inline constexpr std::uint32_t kAxeShownMs = kAxeStuckMs - kAxeLockMs;
    inline constexpr float kAxeReturnWidth = 4.f;           // section 7 #21 default (S1 unset; G1 kAxeReturnWidth)
    inline constexpr NH<float> kAxeLandPct{ 15.f, 25.f };
    inline constexpr NH<float> kAxeReturnPct{ 20.f, 35.f };
    inline constexpr float kAxeThrowSpeed = 20.f;           // the look's missile (yd/s)
    inline constexpr float kAxeReturnSpeed = 25.f;
    inline constexpr float kAxeMinReturnLength = 3.f;       // shorter than this (he stands on it): no return line
    // The stock casts kept (stock timers, S1 "Gorosh": Mortal Strike 4.4 s then 20-24 s, Bloodlust 6 s then 28-32 s).
    inline constexpr std::uint32_t kMortalStrikeFirstMs = 4400;
    inline constexpr std::uint32_t kMortalStrikeMinMs = 20000;
    inline constexpr std::uint32_t kMortalStrikeMaxMs = 24000;
    inline constexpr std::uint32_t kBloodlustFirstMs = 6000;
    inline constexpr std::uint32_t kBloodlustMinMs = 28000;
    inline constexpr std::uint32_t kBloodlustMaxMs = 32000;

    // GO2's timeline from the throw: the landing resolves at 2 s, the shown line runs 2-6 s, the locked one 6-8 s.
    inline constexpr std::uint32_t AxeLockAtMs() { return kAxeLandMs + kAxeShownMs; }
    inline constexpr std::uint32_t AxeReturnAtMs() { return kAxeLandMs + kAxeStuckMs; }

    // GO1: where the line ends (the target's spot, or kDanceMinLength along the same bearing when it is closer).
    inline Vec2 DanceEnd(Vec2 from, Vec2 target)
    {
        float const d = DungeonKit::Distance(from, target);
        if (d >= kDanceMinLength)
            return target;
        float const o = d > 0.01f ? DungeonKit::BearingTo(from, target) : 0.f;
        return DungeonKit::Advance(from, o, kDanceMinLength);
    }

    // GO1: the whirl's travel time down a line of `length` (the end's Whirlwind waits for it).
    inline constexpr std::uint32_t DanceTravelMs(float length)
    {
        return static_cast<std::uint32_t>(std::max(0.f, length) / kDanceSpeed * 1000.f + 0.5f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GZ1-GZ3 Grizzle
    // ----------------------------------------------------------------------------------------------------------------
    // GZ1 Bull Rush: a random player (the tank too); a 2 s line from him through them to the wall, then the charge.
    inline constexpr std::uint32_t kRushEveryMs = 25000;
    inline constexpr std::uint32_t kRushWarnMs = 2000;
    inline constexpr float kRushWidth = 5.f;                // S1 unset: this WP's default
    inline constexpr float kRushSpeed = 30.f;               // yd/s (this WP's default; 23-43 yd in about 1-1.5 s)
    inline constexpr float kRushWallInset = 1.f;            // he stops this short of the wall
    inline constexpr NH<float> kRushPct{ 35.f, 50.f };      // no Weakened (heroic is 50%)
    inline constexpr float kRushKnockXY = 12.f;
    inline constexpr float kRushKnockZ = 6.f;
    inline constexpr std::uint32_t kDazedMs = 4000;
    inline constexpr std::int32_t kDazedDamageTakenPct = 30;
    inline constexpr std::uint32_t kRushTimeoutMs = 4000;   // a charge that never arrives is dazed anyway
    // GZ2 Earthshaker Stomp: a 2.5 s wind-up, 12 yd round him, everyone (the tank too).
    inline constexpr std::uint32_t kStompEveryMs = 18000;
    inline constexpr std::uint32_t kStompWarnMs = 2500;
    inline constexpr float kStompRadius = 12.f;
    inline constexpr NH<float> kStompPct{ 25.f, 40.f };
    inline constexpr std::uint32_t kStompStunMs = 2000;
    // GZ3 Killing Frenzy: a stack every 15 s, +10% attack speed and damage each, cap 5 normal, uncapped heroic.
    inline constexpr std::uint32_t kFrenzyEveryMs = 15000;
    inline constexpr std::int32_t kFrenzyPctPerStack = 10;
    inline constexpr std::uint32_t kFrenzyCapNormal = 5;
    inline constexpr std::uint32_t kFrenzyCapHeroic = 50;   // "uncapped": the aura's CumulativeAura (never reached)

    inline constexpr std::uint32_t FrenzyCap(bool heroic) { return heroic ? kFrenzyCapHeroic : kFrenzyCapNormal; }

    // The next stack count (the cap holds it).
    inline constexpr std::uint32_t NextFrenzy(std::uint32_t stacks, bool heroic)
    {
        return std::min(stacks + 1, FrenzyCap(heroic));
    }

    // A Soothe / Tranquilizing Shot took one stack (a dispel removes one): it clears them all (S1: "clears every
    // stack"). True when the aura dropped below what the script put there (the script removes the rest).
    inline constexpr bool FrenzyDispelled(std::uint32_t expected, std::uint32_t now)
    {
        return expected > 0 && now < expected;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EV1-EV3 Eviscerator
    // ----------------------------------------------------------------------------------------------------------------
    // EV1 Spell Eater: an 8 s shell; each magic hit is absorbed and adds a Devoured stack (cap 15); when it ends, 2%
    // per stack on everyone. A Purge or Spellsteal of the shell ends it with nothing released (the reward; default).
    inline constexpr std::uint32_t kSpellEaterEveryMs = 25000;
    inline constexpr std::uint32_t kSpellEaterMs = 8000;
    inline constexpr std::uint32_t kDevouredCap = 15;
    inline constexpr float kDevouredPctPerStack = 2.f;

    inline constexpr std::uint32_t AddDevoured(std::uint32_t stacks) { return std::min(stacks + 1, kDevouredCap); }
    inline constexpr float DevouredPct(std::uint32_t stacks)
    {
        return kDevouredPctPerStack * static_cast<float>(std::min(stacks, kDevouredCap));
    }

    // EV2 Open Wounds: a 15 s bleed on a random non-tank, 2% every 3 s; every 3 s it jumps to anyone within 5 yd.
    inline constexpr std::uint32_t kOpenWoundsEveryMs = 20000;
    inline constexpr std::uint32_t kOpenWoundsMs = 15000;
    inline constexpr std::uint32_t kOpenWoundsTickMs = 3000;
    inline constexpr float kOpenWoundsPct = 2.f;
    inline constexpr float kOpenWoundsJumpYd = 5.f;
    inline constexpr std::uint32_t kOpenWoundsJumps = kOpenWoundsMs / kOpenWoundsTickMs;     // 5
    // EV3 Shadow Bolt Volley: the stock 3 s interruptible cast, every 15 s / 12 s, rescaled (S1 "stock rescaled":
    // this WP's default 10% / 15%, the BRS group-pulse convention), everyone within 30 yd.
    inline constexpr NH<std::uint32_t> kVolleyEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kVolleyCastMs = 3000;
    inline constexpr float kVolleyRadius = 30.f;
    inline constexpr NH<float> kVolleyPct{ 10.f, 15.f };
    inline constexpr NH<std::uint8_t> kVolleyKickPriority{ 1, 3 };  // a reward on normal, expected on heroic

    // ----------------------------------------------------------------------------------------------------------------
    // OK1-OK3 Ok'thor the Breaker
    // ----------------------------------------------------------------------------------------------------------------
    // OK1 Arcane Rupture: a 3 s cast, then everything beyond 8 yd (heroic 6 yd) of him erupts.
    inline constexpr NH<std::uint32_t> kRuptureEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kRuptureCastMs = 3000;
    inline constexpr NH<float> kRuptureInner{ 8.f, 6.f };
    inline constexpr float kRuptureMinOuter = 45.f;         // G1 kRuptureOuterYd; grown to the farthest floor point
    inline constexpr float kRupturePad = 2.f;
    inline constexpr NH<float> kRupturePct{ 30.f, 45.f };
    // OK2 Sheep Bolt: 10 s after each Rupture, a 2 s marker, a 5 yd circle at a random player's spot (heroic 2).
    inline constexpr std::uint32_t kSheepAfterRuptureMs = 10000;
    inline constexpr std::uint32_t kSheepWarnMs = 2000;
    inline constexpr float kSheepRadius = 5.f;
    inline constexpr NH<std::uint32_t> kSheepCount{ 1, 2 };
    inline constexpr NH<float> kSheepPct{ 15.f, 25.f };
    inline constexpr std::uint32_t kSheepPolyMs = 2000;
    // OK3 Slow: one random player, 8 s, Magic (stock: self-area 20 yd, 20 s); stock timer 15 s.
    inline constexpr std::uint32_t kSlowEveryMs = 15000;
    inline constexpr std::uint32_t kSlowMs = 8000;
    inline constexpr std::int32_t kSlowMovePct = 60;
    inline constexpr std::int32_t kSlowHastePct = 55;
    // Arcane Bolt (stock filler): 1.4 s, then every 5-9 s, a random player.
    inline constexpr std::uint32_t kArcaneBoltFirstMs = 1400;
    inline constexpr std::uint32_t kArcaneBoltMinMs = 5000;
    inline constexpr std::uint32_t kArcaneBoltMaxMs = 9000;

    inline constexpr std::uint32_t RuptureTag(bool heroic) { return heroic ? TAG_OK_RUPTURE_HEROIC : TAG_OK_RUPTURE; }

    // OK1: the donut's outer edge from `at` (the floor polygon's farthest vertex, padded; never under G1's 45 yd).
    inline float RuptureOuter(Vec2 at)
    {
        float best = 0.f;
        for (Vec2 const& v : BrdRingOfLaw::RingFloor())
            best = std::max(best, DungeonKit::Distance(at, v));
        return std::max(kRuptureMinOuter, best + kRupturePad);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AN1-AN3 Anub'shiah
    // ----------------------------------------------------------------------------------------------------------------
    // AN1 Raise Dead: every 15 s one beast of the opener's type rises where one died (heroic 2), as a Risen beast; at
    // most the wave's size alive. Heroic, as the title holder below 50%: once, the fallen challenger as the Risen
    // Champion.
    inline constexpr std::uint32_t kRaiseEveryMs = 15000;
    inline constexpr std::uint32_t kRaiseCastMs = 2000;
    inline constexpr NH<std::uint32_t> kRaisePerCast{ 1, 2 };
    inline constexpr float kRisenChampionAtPct = 50.f;

    inline constexpr std::uint32_t RisenEntry(std::uint32_t waveType)
    {
        return BlackrockDepthsRework::NPC_BRD_RISEN_WORM + std::min<std::uint32_t>(waveType, 5);
    }

    inline constexpr std::optional<std::uint32_t> RisenWaveType(std::uint32_t entry)
    {
        if (entry >= BlackrockDepthsRework::NPC_BRD_RISEN_WORM && entry <= BlackrockDepthsRework::NPC_BRD_RISEN_BEETLE)
            return entry - BlackrockDepthsRework::NPC_BRD_RISEN_WORM;
        return std::nullopt;
    }

    // How many rise on this cast: the per-cast count, held under the wave's size, and no more than the spots left.
    inline constexpr std::uint32_t RaiseCount(bool heroic, std::uint32_t waveSize, std::uint32_t alive,
        std::uint32_t spotsLeft)
    {
        std::uint32_t const room = alive >= waveSize ? 0 : waveSize - alive;
        return std::min({ kRaisePerCast(heroic), room, spotsLeft });
    }

    inline constexpr bool RaisesChampion(bool heroic, std::uint8_t order, float healthPct, bool done)
    {
        return heroic && order == 2 && !done && healthPct < kRisenChampionAtPct;
    }

    // The Risen (S1 Build spec: 6k normal, 10k heroic; the Risen Champion heroic only, 40k): level 51 / 52 bodies.
    inline constexpr std::uint32_t kRisenNormalHealth = 6000;
    inline constexpr std::uint32_t kRisenHeroicHealth = 10000;
    inline constexpr std::uint32_t kRisenBaseHealth = 2292;    // level 51, class 1 (the wave mobs' base)
    inline constexpr float kRisenHealthModifier = 2.617801f;
    inline constexpr std::uint32_t kRisenChampionNormalHealth = 24000;     // never spawned on normal
    inline constexpr std::uint32_t kRisenChampionHeroicHealth = 40000;
    inline constexpr float kRisenChampionHealthModifier = 10.122f;        // on 2,371 (level 52, class 1)
    // Heroic, the Risen keep their wave mechanic (ruling 20): the group signatures (Burrow, Tail Sting, Venom Spit)
    // run on Anub'shiah's clock, one Risen at a time; Screech and Thunderclap on each Risen's own; Acid Burst on death.

    // AN2 Web Spit: a 2 s marker, a 6 yd circle at a random player's spot, root 2 s; the web stays 20 s (-50%).
    inline constexpr std::uint32_t kWebSpitEveryMs = 18000;
    inline constexpr std::uint32_t kWebSpitWarnMs = 2000;
    inline constexpr float kWebSpitRadius = 6.f;
    inline constexpr NH<float> kWebSpitPct{ 15.f, 25.f };
    inline constexpr std::uint32_t kWebRootMs = 2000;
    inline constexpr std::uint32_t kWebPatchMs = 20000;
    inline constexpr std::uint32_t kWebPatchTickMs = 1000;
    inline constexpr std::int32_t kWebPatchSlowPct = 50;
    inline constexpr float kWebSpitSpeed = 25.f;            // the look's missile
    // AN3 the curses: one random player each, 15 s (stock timers: Tongues 4.8 s then 22-26 s, Weakness 2.4 s then
    // 10-14 s); Shadow Bolt on the tank 1.4 s then 5-9 s.
    inline constexpr std::uint32_t kCurseMs = 15000;
    inline constexpr std::int32_t kTonguesCastPct = 50;
    inline constexpr std::int32_t kWeaknessPhysicalPct = 20;
    inline constexpr std::uint32_t kTonguesFirstMs = 4800;
    inline constexpr std::uint32_t kTonguesMinMs = 22000;
    inline constexpr std::uint32_t kTonguesMaxMs = 26000;
    inline constexpr std::uint32_t kWeaknessFirstMs = 2400;
    inline constexpr std::uint32_t kWeaknessMinMs = 10000;
    inline constexpr std::uint32_t kWeaknessMaxMs = 14000;
    inline constexpr std::uint32_t kShadowBoltFirstMs = 1400;
    inline constexpr std::uint32_t kShadowBoltMinMs = 5000;
    inline constexpr std::uint32_t kShadowBoltMaxMs = 9000;

    // ----------------------------------------------------------------------------------------------------------------
    // HE1-HE2 Hedrum the Creeper
    // ----------------------------------------------------------------------------------------------------------------
    // HE1 Web Strands: three 4 yd lines from him to the wall, 2 s; a hit roots 2 s; they stay 20 s (heroic 30 s: two
    // sets up at once) at -30%.
    inline constexpr std::uint32_t kStrandsEveryMs = 25000;
    inline constexpr std::uint32_t kStrandsWarnMs = 2000;
    inline constexpr std::uint32_t kStrandsCount = 3;
    inline constexpr float kStrandsWidth = 4.f;
    inline constexpr NH<std::uint32_t> kStrandsLifeMs{ 20000, 30000 };
    inline constexpr std::uint32_t kStrandsTickMs = 1000;
    inline constexpr NH<float> kStrandsPct{ 20.f, 35.f };
    inline constexpr std::uint32_t kStrandsRootMs = 2000;
    inline constexpr std::int32_t kStrandsSlowPct = 30;
    inline constexpr float kStrandsMinLength = 6.f;         // a strand shorter than this (he stands at a wall) drops
    inline constexpr float kStrandPatchStep = 8.f;          // the decoration patches along a strand
    // HE2 Reel In + Baneful Burst: the farthest player (heroic 2) pulled to his feet, then 3 s, 10 yd round him.
    inline constexpr std::uint32_t kReelEveryMs = 20000;
    inline constexpr NH<std::uint32_t> kReelCount{ 1, 2 };
    inline constexpr std::uint32_t kBurstWarnMs = 3000;
    inline constexpr float kBurstRadius = 10.f;
    inline constexpr NH<float> kBurstPct{ 30.f, 45.f };
    inline constexpr float kBurstPoisonPct = 2.f;           // per second, 8 s (both difficulties)
    inline constexpr std::uint32_t kBurstPoisonTickMs = 1000;
    inline constexpr std::uint32_t kBurstPoisonMs = 8000;
    inline constexpr float kReelLandYd = 2.f;               // the reeled player lands this far in front of him
    inline constexpr float kReelSpeedXY = 30.f;
    inline constexpr float kReelSpeedZ = 6.f;

    // HE1: the three strands' bearings: the first toward a random player, the others a third of a turn apart.
    inline std::array<float, kStrandsCount> StrandBearings(float first)
    {
        std::array<float, kStrandsCount> out{};
        for (std::uint32_t i = 0; i < kStrandsCount; ++i)
            out[i] = BrdRingOfLaw::NormalizeOrientation(first + DungeonKit::kTwoPi * static_cast<float>(i)
                / static_cast<float>(kStrandsCount));
        return out;
    }

    // GZ1 / HE1: a line from `origin` along `bearing` to the floor's wall (BrdRingOfLaw::WallEnd through a point on
    // the bearing), `inset` short of it; nullopt from off the floor.
    inline std::optional<Vec2> WallAlong(Vec2 origin, float bearing, float inset)
    {
        return BrdRingOfLaw::WallEnd(origin, DungeonKit::Advance(origin, bearing, 1.f), inset);
    }

    // The common first-cast rule (hub gap 17): half the cooldown.
    inline constexpr std::uint32_t FirstOf(std::uint32_t everyMs) { return everyMs / 2; }
}

#endif
