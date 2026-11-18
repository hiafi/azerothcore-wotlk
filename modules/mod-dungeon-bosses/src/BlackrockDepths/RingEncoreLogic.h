/*
 * mod-dungeon-bosses, Blackrock Depths D6:
 * The Ring of Law's hard mode, the Encore, the pure, host-testable part (no engine headers). Build spec S1 "Hard mode:
 * the Encore" and the Ring's Build spec rows EN1-EN16 (docs/dungeons/blackrock-depths-1-detention-block.md; rulings
 * 19, 21, 28-30, 88, 91), handoff sections 3.5 (row D6), 3.6 (the Encore's health), 3.7 (D6), 3.8 (the Ring's floor),
 * 3.10, section 7 #15 / #16. Tested by tests/brd_ring_encore_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsEncore (210960-211019), declared in apps/dbc-tools
 *              source/npcs/blackrock_depths/ring_encore.py
 *   Tuning     the hard mode values straight from the build spec (one value each: the Encore runs on heroic only);
 *              the unset cells (Multi-Shot's angle, Evasion's dodge, Snap Trap's gap, Malgen's Shoot, the charge's
 *              hold) are this WP's defaults (report, designer questions)
 *   Picks      the team, its leap, Executioner's Charge's target, Chain Heal's targets, the resurrection's candidate,
 *              the end of the fight (every body finished, Theldren last), Vicious Wound, Evasion, Frost Nova's trigger
 *   Geometry   the five gallery spots and landings, Blink and Disengage kept on the floor
 *
 * The engine half: ring_encore_hard_mode.cpp (the five AIs, Korv's totems, the banner, the Encore's per-attempt script
 * on Grimstone's hooks). The frame (Grimstone, Favor, the Sentences, the credit) is D4's: RingOfLawFight.h.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_RING_ENCORE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_RING_ENCORE_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitBodyLogic.h"
#include "DungeonKitMath.h"
#include "RingOfLawLogic.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace BrdEncore
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsEncore;

    enum RingEncoreSpells : std::uint32_t
    {
        // EN2-EN3 Theldren
        SPELL_TH_CHARGE_BAR         = kSpellSlice.first + 0,    // 210960 EN2 the 1.5 s bar at the marked player
        SPELL_TH_CHARGE_MARK        = kSpellSlice.first + 1,    // 210961 EN2 the mark on the target (1.5 s, no number)
        SPELL_TH_CHARGE_HIT         = kSpellSlice.first + 2,    // 210962 EN2 the charge's hit (the script's value)
        SPELL_TH_WOUNDED            = kSpellSlice.first + 3,    // 210963 EN2 -50% healing taken, 6 s
        SPELL_TH_EXECUTE            = kSpellSlice.first + 4,    // 210964 EN2 Execute below 30% (the script's value)
        SPELL_TH_ROAR_BAR           = kSpellSlice.first + 5,    // 210965 EN3 the 2.5 s bar
        SPELL_TH_ROAR               = kSpellSlice.first + 6,    // 210966 EN3 the ring's hit (resolve copy, Physical)
        SPELL_TH_ROAR_FEAR          = kSpellSlice.first + 7,    // 210967 EN3 the 2 s fear (rider)
        SPELL_TH_CHAMPIONS_PRIDE    = kSpellSlice.first + 8,    // 210968 Champion's Pride: +25% attack speed below 30%
        // EN4-EN7 Korv
        SPELL_KO_CHAIN_HEAL         = kSpellSlice.first + 9,    // 210969 EN4 the 2 s kickable cast (Nature)
        SPELL_KO_CHAIN_HEAL_HIT     = kSpellSlice.first + 10,   // 210970 EN4 a teammate's heal (the script's value)
        SPELL_KO_ANCESTRAL_SPIRIT   = kSpellSlice.first + 11,   // 210971 EN5 the 5 s kickable cast at a body (Nature)
        SPELL_KO_SPIRIT_LOOK        = kSpellSlice.first + 12,   // 210972 look: the resurrection burst on the body
        SPELL_KO_EARTH_SHIELD       = kSpellSlice.first + 13,   // 210973 EN7 on Theldren, Magic, 6 charges
        SPELL_KO_EARTH_SHIELD_HEAL  = kSpellSlice.first + 14,   // 210974 EN7 a charge's 2% heal (the script's value)
        SPELL_KO_SEARING_BOLT       = kSpellSlice.first + 15,   // 210975 EN6 the Searing Totem's bolt (script's value)
        SPELL_KO_HEALING_STREAM     = kSpellSlice.first + 16,   // 210976 EN6 the Healing Stream's 2% (script's value)
        SPELL_KO_EARTHBIND          = kSpellSlice.first + 17,   // 210977 EN6 the Earthbind's -50% (2 s, re-applied)
        // EN8-EN10 Lefty
        SPELL_LE_SHADOWSTEP_LOOK    = kSpellSlice.first + 18,   // 210978 look: the Shadowstep
        SPELL_LE_KIDNEY_SHOT        = kSpellSlice.first + 19,   // 210979 EN8 Kidney Shot 27615 cut to 2 s
        SPELL_LE_VICIOUS_WOUND      = kSpellSlice.first + 20,   // 210980 EN9 the bleed's stacks (the count, no dispel)
        SPELL_LE_VICIOUS_WOUND_TICK = kSpellSlice.first + 21,   // 210981 EN9 a tick (1% x stacks, the script's value)
        SPELL_LE_EVASION            = kSpellSlice.first + 22,   // 210982 EN10 8 s, most melee attacks dodged
        // EN11-EN13 Volida
        SPELL_VL_BLIZZARD           = kSpellSlice.first + 23,   // 210983 EN11 a tick's hit (resolve copy, Frost)
        SPELL_VL_BLIZZARD_SLOW      = kSpellSlice.first + 24,   // 210984 EN11 the slow (rider, re-applied each tick)
        SPELL_VL_BLIZZARD_LOOK      = kSpellSlice.first + 25,   // 210985 look: the storm on a stalker (area look)
        SPELL_VL_FROST_NOVA_CAST    = kSpellSlice.first + 26,   // 210986 EN12 the 1.5 s kickable cast (Frost)
        SPELL_VL_FROST_NOVA         = kSpellSlice.first + 27,   // 210987 EN12 the ring's hit (resolve copy, Frost)
        SPELL_VL_FROST_NOVA_ROOT    = kSpellSlice.first + 28,   // 210988 EN12 the 2 s root (rider, Magic)
        SPELL_VL_BLINK_LOOK         = kSpellSlice.first + 29,   // 210989 look: the Blink after a nova
        SPELL_VL_ICE_BARRIER        = kSpellSlice.first + 30,   // 210990 EN13 the shield (10% of her health, Magic)
        // EN14-EN16 Malgen
        SPELL_MA_PIERCING_SHOT_CAST = kSpellSlice.first + 31,   // 210991 EN14 the 3 s kickable cast (Physical)
        SPELL_MA_PIERCING_SHOT      = kSpellSlice.first + 32,   // 210992 EN14 the line's hit (resolve copy, Physical)
        SPELL_MA_SNAP_TRAP          = kSpellSlice.first + 33,   // 210993 EN15 the trap's hit (resolve copy, Physical)
        SPELL_MA_SNAP_TRAP_FREEZE   = kSpellSlice.first + 34,   // 210994 EN15 the 2 s freeze (rider, Magic)
        SPELL_MA_DISENGAGE_LOOK     = kSpellSlice.first + 35,   // 210995 look: the Disengage leap
        SPELL_MA_MULTI_SHOT_BAR     = kSpellSlice.first + 36,   // 210996 EN16 the 2 s bar while the cone fills
        SPELL_MA_MULTI_SHOT         = kSpellSlice.first + 37,   // 210997 EN16 the cone's hit (resolve copy, Physical)
        SPELL_MA_SHOOT              = kSpellSlice.first + 38,   // 210998 his filler between the shots (the script's)
        // EN1 the banner
        SPELL_EN_BANNER_BURN        = kSpellSlice.first + 39,   // 210999 look: the clicking player burns the banner
        // 211000-211019 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_EN_BANNER_BURN;
    static_assert(kLastSpell <= kSpellSlice.last, "the Encore's spells must stay in their slice");

    // Stock spells kept as they are (S1 "Keep"; DD scales them on heroic, none is on DD's double-use list). Retired
    // (never cast by the reworked scripts): Intercept 27577, Frightening Shout 19134, Demoralizing Shout 27579, Lesser
    // Healing Wave 27624, Earthbind Totem 15786, Kidney Shot 27615 (EN8 is the 2 s copy), Aimed Shot 31623 and Freezing
    // Trap 32419 (EN14 / EN15 are new), Blizzard 27618 (EN11 is the registry's).
    enum RingEncoreStockSpells : std::uint32_t
    {
        SPELL_STOCK_BATTLE_SHOUT    = 27578,    // Theldren: at the landing, self
        SPELL_STOCK_MORTAL_STRIKE   = 27580,    // Theldren: the tank, 5-7 s then 8-10 s
        SPELL_STOCK_HAMSTRING       = 27584,    // Theldren: his victim, 12-14 s then 25-27 s
        SPELL_STOCK_FROST_SHOCK     = 21401,    // Korv: his victim, 5-7 s then 8-10 s
        SPELL_STOCK_PURGE           = 27626,    // Korv: a random player, 9 s then 17 s
        SPELL_STOCK_SINISTER_STRIKE = 14873,    // Lefty: his victim, 5-7 s (each hit a Vicious Wound stack)
        SPELL_STOCK_EVISCERATE      = 27611,    // Lefty: his victim, 12-14 s then 25-27 s
        SPELL_STOCK_FROSTBOLT       = 20822,    // Volida: her victim, 9 s then 6 s (3 s cast: a kick is a reward)
        SPELL_STOCK_CONE_OF_COLD    = 20828,    // Volida: a victim within 10 yd, 5-7 s then 9 s
    };

    // Registry tags (the champions use 18-28, the Ring 11-17, G1's drill rows 6-10).
    enum RingEncoreTags : std::uint32_t
    {
        TAG_TH_ROAR             = 29,
        TAG_VL_BLIZZARD         = 30,
        TAG_VL_FROST_NOVA       = 31,
        TAG_MA_PIERCING_SHOT    = 32,
        TAG_MA_SNAP_TRAP        = 33,
        TAG_MA_MULTI_SHOT       = 34,
    };

    // creature_text of Theldren (16059): group 0 his three stock yells (unused in stock: now the leap), group 1 new
    // (his real death).
    enum TheldrenTexts : std::uint8_t
    {
        SAY_TH_LEAP = 0,
        SAY_TH_DEATH = 1,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The team (ruling 28: a fixed roster of five, one per job)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Member : std::uint8_t
    {
        Theldren = 0,
        Korv = 1,
        Lefty = 2,
        Volida = 3,
        Malgen = 4,
    };
    inline constexpr std::size_t kTeamSize = 5;

    inline constexpr std::array<std::uint32_t, kTeamSize> kTeamEntries{ {
        BlackrockDepthsRework::NPC_THELDREN, BlackrockDepthsRework::NPC_KORV, BlackrockDepthsRework::NPC_LEFTY,
        BlackrockDepthsRework::NPC_VOLIDA, BlackrockDepthsRework::NPC_MALGEN_LONGSPEAR,
    } };

    inline constexpr std::size_t IndexOf(Member m) { return static_cast<std::size_t>(m); }
    inline constexpr std::uint32_t EntryOf(Member m) { return kTeamEntries[IndexOf(m)]; }

    inline constexpr std::optional<Member> MemberOf(std::uint32_t entry)
    {
        for (std::size_t i = 0; i < kTeamSize; ++i)
            if (kTeamEntries[i] == entry)
                return static_cast<Member>(i);
        return std::nullopt;
    }

    inline constexpr char const* MemberKey(Member m)
    {
        switch (m)
        {
            case Member::Theldren: return "theldren";
            case Member::Korv:     return "korv";
            case Member::Lefty:    return "lefty";
            case Member::Volida:   return "volida";
            case Member::Malgen:   return "malgen";
        }
        return "?";
    }

    // Korv's three totems (EN6): one of each at a time.
    enum class TotemKind : std::uint8_t
    {
        HealingStream = 0,
        Searing = 1,
        Earthbind = 2,
    };
    inline constexpr std::size_t kTotemKinds = 3;
    inline constexpr std::array<std::uint32_t, kTotemKinds> kTotemEntries{ {
        BlackrockDepthsRework::NPC_BRD_KORV_TOTEM_1, BlackrockDepthsRework::NPC_BRD_KORV_TOTEM_2,
        BlackrockDepthsRework::NPC_BRD_KORV_TOTEM_3,
    } };

    inline constexpr std::optional<TotemKind> TotemOf(std::uint32_t entry)
    {
        for (std::size_t i = 0; i < kTotemKinds; ++i)
            if (kTotemEntries[i] == entry)
                return static_cast<TotemKind>(i);
        return std::nullopt;
    }

    inline constexpr char const* TotemName(TotemKind t)
    {
        switch (t)
        {
            case TotemKind::HealingStream: return "healing-stream";
            case TotemKind::Searing:       return "searing";
            case TotemKind::Earthbind:     return "earthbind";
        }
        return "?";
    }

    // Health (ruling 30; handoff 3.6): the heroic templates (WP-H's overrides of the summon-only units) carry it. The
    // HUB's "about 560,000" sums to 540,000 (section 8 #10); the parts are the rule. A totem dies in one hit: the
    // script sets its health to 1 (WP-H section 7 item 3: no designer value; the tier template is its heroic row).
    inline constexpr std::uint32_t kTheldrenHealth = 160000;
    inline constexpr std::uint32_t kKorvHealth = 80000;
    inline constexpr std::uint32_t kMemberHealth = 100000;      // Lefty, Volida, Malgen
    inline constexpr std::uint32_t kTotemHealth = 1;

    inline constexpr std::uint32_t HealthOf(Member m)
    {
        return m == Member::Theldren ? kTheldrenHealth : m == Member::Korv ? kKorvHealth : kMemberHealth;
    }

    inline constexpr std::uint32_t TeamHealth()
    {
        std::uint32_t sum = 0;
        for (std::size_t i = 0; i < kTeamSize; ++i)
            sum += HealthOf(static_cast<Member>(i));
        return sum;
    }

    // EN5: a landed resurrection brings a teammate back at half its health, once per teammate (HeldBody: one fall
    // held). Korv holds none: nobody brings him back, so his lethal hit is his real death.
    inline constexpr float kRevivePct = 50.f;
    inline constexpr std::uint8_t HoldsOf(Member m) { return m == Member::Korv ? 0 : 1; }

    // The members are summoned with a corpse-timed despawn (KT-D1: TEMPSUMMON_DEAD_DESPAWN would take the corpse loot,
    // Theldren's hard mode list with it); the stock Arena Spoils chest lasts 300 s, the corpses outlast it.
    inline constexpr std::uint32_t kCorpseMs = 30 * 60 * 1000;
    // A member gone without dying (a despawn, a lost summon) this long: summoned again at its landing.
    inline constexpr std::uint32_t kMemberLostMs = 5000;
    // The Encore's bookkeeping runs on Grimstone's update this often.
    inline constexpr std::uint32_t kWatchMs = 250;

    // ----------------------------------------------------------------------------------------------------------------
    // EN1 the banner (ruling 21): thrown in at Favor 10 on heroic (D4), burned by a player's click (this WP)
    // ----------------------------------------------------------------------------------------------------------------
    // Where the crowd's banner lands: the stock banner's spot (the Thelrin focus 181059, S1 "Theldren and his team").
    inline constexpr BlackrockDepthsRework::Point3 kBannerSpot{ 597.f, -189.f, -54.f };
    inline constexpr float kBannerO = 4.9f;
    inline constexpr std::uint32_t kBannerBackstopSec = 4 * 3600;      // the object outlives any attempt
    inline constexpr std::uint32_t kBannerBurnMs = 3000;                // the burning banner, then it is gone
    inline constexpr float kBannerSearchYd = 100.f;

    // ----------------------------------------------------------------------------------------------------------------
    // The leap (S1 "Flow"; section 8 #17: five gallery spots and five landings, to be picked in game)
    // ----------------------------------------------------------------------------------------------------------------
    // The gallery's front row above the east gate (the champions' gate), between the spectators' spawns there [db:
    // creature, map 230, z -36.9]; the landings 25 yd out from the ring center on the same bearings (the floor reaches
    // 35-44 yd east, NM). Members in the team's order.
    inline constexpr std::array<BlackrockDepthsRework::Point3, kTeamSize> kGallery{ {
        { 650.1f, -182.5f, -36.9f },    // Theldren
        { 651.7f, -187.6f, -36.2f },    // Korv
        { 649.8f, -178.2f, -36.9f },    // Lefty
        { 648.5f, -174.5f, -36.9f },    // Volida
        { 649.0f, -170.8f, -36.2f },    // Malgen
    } };
    inline constexpr float kLandingRadius = 25.f;
    inline constexpr float kLeapSpeedXY = 20.f;
    inline constexpr std::uint32_t kLeapTimeoutMs = 4000;      // a jump that never lands: put down at the landing

    inline Vec2 LandingOf(std::size_t index)
    {
        Vec2 const center = BlackrockDepthsRework::kRingCenter.XY();
        BlackrockDepthsRework::Point3 const g = kGallery[std::min(index, kTeamSize - 1)];
        return DungeonKit::Advance(center, DungeonKit::BearingTo(center, g.XY()), kLandingRadius);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EN2-EN3 Theldren (warrior: charges the weakest)
    // ----------------------------------------------------------------------------------------------------------------
    // EN2 Executioner's Charge: every 12 s, a 1.5 s mark on the lowest-health player (the tank too), the charge: 25%
    // and -50% healing 6 s; below 30% health on the landing, Execute for 40%. He then turns back to his top-threat
    // target after a short hold on the charged player; a taunt ends the hold at once (ruling 91).
    inline constexpr std::uint32_t kChargeEveryMs = 12000;
    inline constexpr std::uint32_t kChargeWarnMs = 1500;
    inline constexpr float kChargeSpeed = 30.f;
    inline constexpr std::uint32_t kChargeTimeoutMs = 3000;
    inline constexpr std::uint32_t kChargeStickMs = 3000;      // this WP's default: a few swings on the charged player
    inline constexpr float kChargePct = 25.f;
    inline constexpr float kExecutePct = 40.f;
    inline constexpr float kExecuteBelowPct = 30.f;
    inline constexpr std::uint32_t kWoundedMs = 6000;
    inline constexpr std::int32_t kWoundedHealingPct = 50;
    // EN3 Intimidating Roar: every 18 s (12 s below 30%), 2.5 s, 8 yd round him, the tank too: 35%, fear 2 s.
    inline constexpr std::uint32_t kRoarEveryMs = 18000;
    inline constexpr std::uint32_t kRoarPrideEveryMs = 12000;
    inline constexpr std::uint32_t kRoarWarnMs = 2500;
    inline constexpr float kRoarRadius = 8.f;
    inline constexpr float kRoarPct = 35.f;
    inline constexpr std::uint32_t kRoarFearMs = 2000;
    // Champion's Pride: below 30% health, +25% attack speed and the faster Roar.
    inline constexpr float kPrideBelowPct = 30.f;
    inline constexpr std::int32_t kPrideHastePct = 25;
    // The stock casts (stock SmartAI timers).
    inline constexpr std::uint32_t kMortalStrikeFirstMinMs = 5000;
    inline constexpr std::uint32_t kMortalStrikeFirstMaxMs = 7000;
    inline constexpr std::uint32_t kMortalStrikeMinMs = 8000;
    inline constexpr std::uint32_t kMortalStrikeMaxMs = 10000;
    inline constexpr std::uint32_t kHamstringFirstMinMs = 12000;
    inline constexpr std::uint32_t kHamstringFirstMaxMs = 14000;
    inline constexpr std::uint32_t kHamstringMinMs = 25000;
    inline constexpr std::uint32_t kHamstringMaxMs = 27000;

    inline constexpr bool PrideActive(float healthPct) { return healthPct < kPrideBelowPct; }
    inline constexpr std::uint32_t RoarEveryMs(bool pride) { return pride ? kRoarPrideEveryMs : kRoarEveryMs; }
    inline constexpr bool ExecuteFollows(float targetHealthPct) { return targetHealthPct < kExecuteBelowPct; }

    // First casts at half the cooldown (hub gap 17's default).
    inline constexpr std::uint32_t FirstOf(std::uint32_t everyMs) { return everyMs / 2; }

    // A candidate player for a pick (pure: raw guid, health percent, distance).
    struct Candidate
    {
        std::uint64_t id = 0;
        float healthPct = 100.f;
        float distance = 0.f;
    };

    // EN2: the lowest-health player (ties: the nearer one), the tank included (ruling 88).
    inline std::optional<std::size_t> LowestHealth(std::vector<Candidate> const& c)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (!best || c[i].healthPct < c[*best].healthPct
                || (c[i].healthPct == c[*best].healthPct && c[i].distance < c[*best].distance))
                best = i;
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EN4-EN7 Korv (shaman: heals)
    // ----------------------------------------------------------------------------------------------------------------
    // EN4 Chain Heal: every 8 s, a 2 s kickable cast, up to 3 teammates for 12% each (interrupt expected).
    inline constexpr std::uint32_t kChainHealEveryMs = 8000;
    inline constexpr std::uint32_t kChainHealCastMs = 2000;
    inline constexpr std::uint32_t kChainHealRetryMs = 2000;   // nobody hurt: look again
    inline constexpr std::size_t kChainHealTargets = 3;
    inline constexpr float kChainHealPct = 12.f;
    inline constexpr float kChainHealBelowPct = 99.f;          // a teammate at full health is no target
    inline constexpr float kChainHealRangeYd = 40.f;
    // EN5 Ancestral Spirit: a 5 s kickable cast at a fallen teammate (top kick priority), once per teammate.
    inline constexpr std::uint32_t kSpiritCastMs = 5000;
    inline constexpr float kSpiritRangeYd = 30.f;
    inline constexpr std::uint32_t kSpiritRetryMs = 3000;      // after a kick (the lockout runs too)
    inline constexpr std::uint32_t kSpiritWalkMs = 6000;       // a walk to a body out of range gives up after this
    // EN6 the totems: Healing Stream every 25 s (2% a second to teammates within 20 yd, until killed), Searing every
    // 20 s (a random player within 20 yd, 3% every 2 s, lasts 20 s), Earthbind every 25 s (-50% within 10 yd, 20 s).
    inline constexpr std::array<std::uint32_t, kTotemKinds> kTotemEveryMs{ { 25000, 20000, 25000 } };
    inline constexpr std::array<std::uint32_t, kTotemKinds> kTotemLifeMs{ { 0, 20000, 20000 } };   // 0: until killed
    inline constexpr std::uint32_t kHealingStreamTickMs = 1000;
    inline constexpr float kHealingStreamPct = 2.f;
    inline constexpr float kHealingStreamRangeYd = 20.f;
    inline constexpr std::uint32_t kSearingTickMs = 2000;
    inline constexpr float kSearingPct = 3.f;
    inline constexpr float kSearingRangeYd = 20.f;
    inline constexpr std::uint32_t kEarthbindTickMs = 1000;
    inline constexpr float kEarthbindRangeYd = 10.f;
    inline constexpr std::int32_t kEarthbindSlowPct = 50;
    inline constexpr std::uint32_t kEarthbindSlowMs = 2000;    // re-applied every pulse: it ends soon after leaving
    inline constexpr float kTotemOffsetYd = 2.f;               // dropped at his feet, a little apart
    // EN7 Earth Shield on Theldren every 30 s: Magic, 6 charges, each hit he takes heals him 2%.
    inline constexpr std::uint32_t kEarthShieldEveryMs = 30000;
    inline constexpr std::uint32_t kEarthShieldCharges = 6;
    inline constexpr float kEarthShieldPct = 2.f;
    inline constexpr std::uint32_t kEarthShieldMs = 10 * 60 * 1000;    // the charges end it, or a purge
    // The stock casts.
    inline constexpr std::uint32_t kFrostShockFirstMinMs = 5000;
    inline constexpr std::uint32_t kFrostShockFirstMaxMs = 7000;
    inline constexpr std::uint32_t kFrostShockMinMs = 8000;
    inline constexpr std::uint32_t kFrostShockMaxMs = 10000;
    inline constexpr std::uint32_t kPurgeFirstMs = 9000;
    inline constexpr std::uint32_t kPurgeEveryMs = 17000;
    inline constexpr float kKorvRangeYd = 20.f;                // a healer: he stands off his victim

    // A teammate for Chain Heal or the resurrection (pure).
    struct Mate
    {
        std::uint64_t id = 0;
        float healthPct = 100.f;
        bool fallen = false;        // a held body
        bool revived = false;       // brought back once already
        float distance = 0.f;
    };

    // EN4: up to 3 standing teammates (Korv too) under full health, the lowest first.
    inline std::vector<std::size_t> ChainHealPicks(std::vector<Mate> const& mates)
    {
        std::vector<std::size_t> idx;
        for (std::size_t i = 0; i < mates.size(); ++i)
            if (!mates[i].fallen && mates[i].healthPct < kChainHealBelowPct && mates[i].distance <= kChainHealRangeYd)
                idx.push_back(i);
        std::stable_sort(idx.begin(), idx.end(),
            [&mates](std::size_t a, std::size_t b) { return mates[a].healthPct < mates[b].healthPct; });
        if (idx.size() > kChainHealTargets)
            idx.resize(kChainHealTargets);
        return idx;
    }

    // EN5: the fallen teammate to bring back (never one brought back before), the nearest first.
    inline std::optional<std::size_t> SpiritPick(std::vector<Mate> const& mates)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < mates.size(); ++i)
            if (mates[i].fallen && !mates[i].revived && (!best || mates[i].distance < mates[*best].distance))
                best = i;
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EN8-EN10 Lefty (rogue: dives the healer)
    // ----------------------------------------------------------------------------------------------------------------
    // EN8 Shadowstep: every 15 s back onto the healer, a 2 s Kidney Shot (not a fixate: the healer is made his top
    // threat, so a taunt takes him off).
    inline constexpr std::uint32_t kShadowstepEveryMs = 15000;
    inline constexpr std::uint32_t kKidneyShotMs = 2000;
    inline constexpr float kShadowstepBehindYd = 1.5f;
    inline constexpr float kDiveThreatPct = 10.f;              // over the top threat (MatchUnitThreatToHighestThreat)
    // EN9 Vicious Wound: each Sinister Strike that lands adds a stack, cap 5, 1% a second a stack; no dispel; it ends
    // once the target is healed above 90%.
    inline constexpr std::uint32_t kWoundCap = 5;
    inline constexpr float kWoundPctPerStack = 1.f;
    inline constexpr std::uint32_t kWoundTickMs = 1000;
    inline constexpr float kWoundEndsAbovePct = 90.f;
    inline constexpr std::uint32_t kWoundMs = 60000;           // the aura's cap (the heal ends it, or his death)
    // EN10 Evasion: at 50% and at 25% health, 8 s.
    inline constexpr std::array<float, 2> kEvasionAtPct{ { 50.f, 25.f } };
    inline constexpr std::uint32_t kEvasionMs = 8000;
    inline constexpr std::int32_t kEvasionDodgePct = 75;      // "dodges most physical attacks": this WP's default
    // The stock casts.
    inline constexpr std::uint32_t kSinisterStrikeMinMs = 5000;
    inline constexpr std::uint32_t kSinisterStrikeMaxMs = 7000;
    inline constexpr std::uint32_t kEviscerateFirstMinMs = 12000;
    inline constexpr std::uint32_t kEviscerateFirstMaxMs = 14000;
    inline constexpr std::uint32_t kEviscerateMinMs = 25000;
    inline constexpr std::uint32_t kEviscerateMaxMs = 27000;

    inline constexpr std::uint32_t NextWound(std::uint32_t stacks) { return std::min(stacks + 1, kWoundCap); }
    inline constexpr float WoundTickPct(std::uint32_t stacks) { return kWoundPctPerStack * static_cast<float>(stacks); }
    inline constexpr bool WoundEnds(float healthPct) { return healthPct > kWoundEndsAbovePct; }

    // EN10: how many Evasions are due at `healthPct` after `used` (0, 1 or 2): one at 50%, the second at 25%.
    inline constexpr std::uint32_t EvasionsDue(float healthPct, std::uint32_t used)
    {
        std::uint32_t due = 0;
        for (float at : kEvasionAtPct)
            if (healthPct <= at)
                ++due;
        return due > used ? due - used : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EN11-EN13 Volida (frost mage: locks the group down)
    // ----------------------------------------------------------------------------------------------------------------
    // EN11 Blizzard: every 12 s, a 2 s marker, 8 yd at a random player's spot, then 6 s of 4% a second and a slow.
    inline constexpr std::uint32_t kBlizzardEveryMs = 12000;
    inline constexpr std::uint32_t kBlizzardWarnMs = 2000;
    inline constexpr std::uint32_t kBlizzardMs = 6000;
    inline constexpr std::uint32_t kBlizzardTickMs = 1000;
    inline constexpr float kBlizzardRadius = 8.f;
    inline constexpr float kBlizzardPct = 4.f;
    inline constexpr std::int32_t kBlizzardSlowPct = 50;
    inline constexpr std::uint32_t kBlizzardSlowMs = 2000;
    // EN12 Frost Nova: when 2 or more players are within 10 yd, a 1.5 s kickable cast; inside 10 yd: 20%, root 2 s,
    // Weakened; then she blinks 15 yd away. 15 s between novas; a kicked one is tried again after the lockout.
    inline constexpr std::uint32_t kNovaEveryMs = 15000;
    inline constexpr std::uint32_t kNovaCastMs = 1500;
    inline constexpr std::uint32_t kNovaRetryMs = 4000;
    inline constexpr float kNovaRadius = 10.f;
    inline constexpr std::uint32_t kNovaMinPlayers = 2;
    inline constexpr float kNovaPct = 20.f;
    inline constexpr std::uint32_t kNovaRootMs = 2000;
    inline constexpr float kBlinkYd = 15.f;
    inline constexpr std::uint32_t kBlinkAfterMs = 300;        // after the resolve (the circle is anchored at her spot)
    // EN13 Ice Barrier: every 30 s a shield worth 10% of her health, Magic (Purge or Spellsteal: the reward).
    inline constexpr std::uint32_t kIceBarrierEveryMs = 30000;
    inline constexpr float kIceBarrierPct = 10.f;
    inline constexpr std::uint32_t kIceBarrierMs = 60000;
    // The stock casts.
    inline constexpr std::uint32_t kFrostboltFirstMs = 9000;
    inline constexpr std::uint32_t kFrostboltEveryMs = 6000;
    inline constexpr std::uint32_t kConeFirstMinMs = 5000;
    inline constexpr std::uint32_t kConeFirstMaxMs = 7000;
    inline constexpr std::uint32_t kConeEveryMs = 9000;
    inline constexpr float kConeRangeYd = 10.f;
    inline constexpr float kVolidaRangeYd = 25.f;              // a caster: she stands off her victim

    inline constexpr bool NovaWanted(std::uint32_t playersWithin) { return playersWithin >= kNovaMinPlayers; }

    // ----------------------------------------------------------------------------------------------------------------
    // EN14-EN16 Malgen (hunter: kites and traps)
    // ----------------------------------------------------------------------------------------------------------------
    // EN14 Piercing Shot: every 15 s, a 3 s kickable cast, a 3 yd line from him through a random player to the wall:
    // 40%, Weakened.
    inline constexpr std::uint32_t kPiercingEveryMs = 15000;
    inline constexpr std::uint32_t kPiercingCastMs = 3000;
    inline constexpr float kPiercingWidth = 3.f;
    inline constexpr float kPiercingPct = 40.f;
    inline constexpr float kPiercingWallInset = 0.5f;
    // EN15 Snap Trap: after 3 s with a player in melee, a 3 yd trap at his feet (60 s, up to 3) and a 15 yd Disengage:
    // 20%, freeze 2 s, Weakened.
    inline constexpr std::uint32_t kTrapMeleeMs = 3000;
    inline constexpr float kTrapMeleeYd = 5.f;
    inline constexpr std::uint32_t kTrapGapMs = 6000;          // this WP's default: never two traps back to back
    inline constexpr float kTrapRadius = 3.f;
    inline constexpr std::uint32_t kTrapArmMs = 1000;
    inline constexpr std::uint32_t kTrapGraceMs = 250;
    inline constexpr std::uint32_t kTrapLifeMs = 60000;
    inline constexpr std::uint8_t kTrapCap = 3;
    inline constexpr std::uint32_t kTrapCapGroup = 1;
    inline constexpr float kTrapPct = 20.f;
    inline constexpr std::uint32_t kTrapFreezeMs = 2000;
    inline constexpr float kDisengageYd = 15.f;
    inline constexpr float kDisengageSpeedXY = 25.f;
    // EN16 Multi-Shot: every 10 s, a 2 s cone marker toward a random player, 30 yd: 25%, Weakened.
    inline constexpr std::uint32_t kMultiShotEveryMs = 10000;
    inline constexpr std::uint32_t kMultiShotWarnMs = 2000;
    inline constexpr float kMultiShotLength = 30.f;
    inline constexpr float kMultiShotAngleDeg = 40.f;         // S1 unset: this WP's default
    inline constexpr float kMultiShotPct = 25.f;
    // His filler between the shots (S1 unset: this WP's default), a ranged hit on his victim.
    inline constexpr std::uint32_t kShootEveryMs = 2500;
    inline constexpr float kShootPct = 5.f;
    inline constexpr float kShootMinYd = 5.f;
    inline constexpr float kMalgenRangeYd = 25.f;              // a hunter: he stands off his victim

    // EN15: the melee clock (ms with a player within 5 yd); `inMelee` false resets it.
    inline constexpr std::uint32_t MeleeClock(std::uint32_t ms, std::uint32_t diff, bool inMelee)
    {
        return inMelee ? ms + diff : 0;
    }

    inline constexpr bool TrapDue(std::uint32_t meleeMs, std::uint64_t now, std::uint64_t lastTrapAt)
    {
        return meleeMs >= kTrapMeleeMs && (lastTrapAt == 0 || now >= lastTrapAt + kTrapGapMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry on the Ring's floor (D4's polygon)
    // ----------------------------------------------------------------------------------------------------------------
    // A move of `yd` from `from` along `bearing`, kept on the floor: the first of the bearing, then 45 and 90 degrees
    // off it either way, whose end lies `margin` inside the floor; nullopt when none does.
    inline std::optional<Vec2> FloorStep(Vec2 from, float bearing, float yd, float margin = 2.f)
    {
        float const q = DungeonKit::kPi / 4.f;
        for (float off : { 0.f, q, -q, 2.f * q, -2.f * q })
        {
            Vec2 const to = DungeonKit::Advance(from, bearing + off, yd);
            if (BrdRingOfLaw::WellInside(to, margin))
                return to;
        }
        return std::nullopt;
    }

    // Blink (EN12) and Disengage (EN15): away from `threat` (the nearest player).
    inline std::optional<Vec2> AwayFrom(Vec2 me, Vec2 threat, float yd)
    {
        float const bearing = DungeonKit::Distance(me, threat) > 0.01f ? DungeonKit::BearingTo(threat, me) : 0.f;
        return FloorStep(me, bearing, yd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The end of the Encore
    // ----------------------------------------------------------------------------------------------------------------
    // What the Encore's watch does with the team's states this update.
    enum class Verdict : std::uint8_t
    {
        Fight,          // somebody stands, or a body Korv can still bring back
        FinishBodies,   // every member down (or Korv dead with bodies lying): finish the bodies, Theldren last
        Won,            // all five really dead
    };

    inline Verdict Judge(std::array<DungeonKit::BodyState, kTeamSize> const& team)
    {
        bool allDead = true;
        bool anyFallen = false;
        for (DungeonKit::BodyState s : team)
        {
            allDead = allDead && s == DungeonKit::BodyState::Dead;
            anyFallen = anyFallen || s == DungeonKit::BodyState::Fallen;
        }
        if (allDead)
            return Verdict::Won;
        if (!anyFallen)
            return Verdict::Fight;
        if (DungeonKit::AllDown(std::span<DungeonKit::BodyState const>(team)))
            return Verdict::FinishBodies;
        // Nobody can bring a body back once Korv is dead.
        if (team[IndexOf(Member::Korv)] == DungeonKit::BodyState::Dead)
            return Verdict::FinishBodies;
        return Verdict::Fight;
    }

    // The order the bodies are finished in: Theldren last (his heroic lootid carries the hard mode list, section 7
    // #16).
    inline constexpr std::array<Member, kTeamSize> kFinishOrder{ {
        Member::Malgen, Member::Volida, Member::Lefty, Member::Korv, Member::Theldren,
    } };
}

#endif
