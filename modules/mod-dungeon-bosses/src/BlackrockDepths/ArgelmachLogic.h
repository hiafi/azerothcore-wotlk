/*
 * mod-dungeon-bosses, Blackrock Depths D15:
 * Golem Lord Argelmach (8983), his three golems (Toxitron 300833, Electron 300834, Arcanoton 300835) and the Arcane Orb
 * (300837), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/blackrock-depths-3-manufactory.md "Golem Lord Argelmach" (AR1-AR10; rulings 55, 56, 88, 91), handoff
 * sections 3.4 rows D15, 3.5 row D15, 3.6, 3.8 (the chamber, the pedestal spots P1-P4), 3.10, 7 #20, 8 #20. Tested by
 * tests/brd_argelmach_test.cpp; apps/dbc-tools source/npcs/blackrock_depths/argelmach.py declares the same ids. The
 * hard mode (D16, the Prototype) builds on ArgelmachFight.h; its numbers live in ArgelmachHardModeLogic.h.
 *
 *   Spells    the WP's ids, inside kSpellsArgelmach (211330-211369)
 *   Tuning    NH<> values and the cadences, straight from the build spec (gap 36 picks marked)
 *   Golems    the three golems, their pedestals (NAVMESH 3.2), the wake order, the wake thresholds
 *   Chamber   the real floor polygon (the navmesh, 2026-11-17), the Arcane Overcharge spot pick
 *   Beat      a repeating beat on the AI's own ms clock
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_ARGELMACH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_ARGELMACH_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace BrdArgelmach
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsArgelmach;

    enum ArgelmachSpells : std::uint32_t
    {
        SPELL_AR_CHAIN_LIGHTNING        = kSpellSlice.first + 0,    // 211330 AR1 3 s, 5 targets, kickable (copy)
        SPELL_AR_SHOCK                  = kSpellSlice.first + 1,    // 211331 AR2 instant on the tank (copy)
        SPELL_AR_LIGHTNING_SHIELD       = kSpellSlice.first + 2,    // 211332 AR3 self, 3 charges, purgeable (copy)
        SPELL_AR_GOLEM_WAKES            = kSpellSlice.first + 3,    // 211333 AR4 the golem's own wake (look)
        SPELL_AR_CHEMICAL_BOMB          = kSpellSlice.first + 4,    // 211334 AR5 the 4 s mark on a player (debuff)
        SPELL_AR_CHEMICAL_CLOUD         = kSpellSlice.first + 5,    // 211335 AR5 a cloud tick (resolve copy, Nature)
        SPELL_AR_CHEMICAL_CLOUD_LOOK    = kSpellSlice.first + 6,    // 211336 AR5 the cloud on a stalker (look)
        SPELL_AR_POISON_MIST            = kSpellSlice.first + 7,    // 211337 AR6 2 s, everyone, + a Poison DoT (H)
        SPELL_AR_LETHAL_ATTRACTION      = kSpellSlice.first + 8,    // 211338 AR7 the 8 s tether on the pair (debuff)
        SPELL_AR_LETHAL_JOLT            = kSpellSlice.first + 9,    // 211339 AR7 the pair's hit (resolve copy, Nature)
        SPELL_AR_LIVEWIRE               = kSpellSlice.first + 10,   // 211340 AR8 12 s Magic debuff (H)
        SPELL_AR_LIVEWIRE_PULSE         = kSpellSlice.first + 11,   // 211341 AR8 a 2 s pulse (resolve copy, Nature)
        SPELL_AR_LIVEWIRE_BURST         = kSpellSlice.first + 12,   // 211342 AR8 the dispel burst (resolve copy)
        SPELL_AR_POWER_SURGE            = kSpellSlice.first + 13,   // 211343 AR9 the popper's hit (resolve copy)
        SPELL_AR_OVERCHARGED            = kSpellSlice.first + 14,   // 211344 AR9 +10% damage, 30 s, 3 stacks (buff)
        SPELL_AR_EMPOWERED              = kSpellSlice.first + 15,   // 211345 AR9 +15% damage, 30 s, 5 stacks (him)
        SPELL_AR_OVERCHARGE_BOMB        = kSpellSlice.first + 16,   // 211346 AR10 the bomb's flight (look, H)
        SPELL_AR_OVERCHARGE_CATCH       = kSpellSlice.first + 17,   // 211347 AR10 the catcher's hit (resolve copy)
        SPELL_AR_OVERCHARGE_BLAST       = kSpellSlice.first + 18,   // 211348 AR10 uncaught: everyone (resolve copy)
        SPELL_AR_STATUE                 = kSpellSlice.first + 19,   // 211349 AR4 the dormant statue look (Stoned copy)
        // 211350-211369 spare
    };
    static_assert(SPELL_AR_STATUE <= kSpellSlice.last, "Argelmach's spells must stay in his slice");

    // The stock spells he cast (SmartAI 8983, dropped by rev_argelmach_blackrock_depths.sql): Chain Lightning 15305
    // (on DD's double-use list), Shock 15605 and Lightning Shield 15507 are copies above (rule 15). Named for the
    // tests.
    inline constexpr std::uint32_t kStockChainLightning = 15305;
    inline constexpr std::uint32_t kStockShock = 15605;
    inline constexpr std::uint32_t kStockLightningShield = 15507;
    // Stoned (10255, the statue look; a dummy aura with EffectMechanic FREEZE): the stock hall golems lose it (section
    // 7 #20: plain trash). The dormant pedestal golems and Magmatron wear SPELL_AR_STATUE instead: their immunity set
    // 1972 holds FREEZE, so the engine drops the stock aura on them (Unit::AddAura, IsImmunedToSpellEffect); the copy
    // has no mechanic and pierces immunities (R-2-A MA-1).
    inline constexpr std::uint32_t kSpellStoned = 10255;

    // Registry tags (the failure ledger and the playtest greps key on them). 23 and 24 are G2's Livewire rows in the BM
    // drill `blackrock-depths-shapes-2` (MechanicDrill.h), so the ledger keys read the same in the fight. 6 and 7 are
    // reserved for D16 (Incineration's cloud bursts, the Flamethrower).
    enum ArgelmachTags : std::uint32_t
    {
        TAG_AR_CHEMICAL_BOMB        = 1,    // AR5 the mark's landing
        TAG_AR_CHEMICAL_CLOUD       = 2,    // AR5 the cloud
        TAG_AR_LETHAL_ATTRACTION    = 3,    // AR7
        TAG_AR_POWER_GENERATOR      = 4,    // AR9 the orb
        TAG_AR_ARCANE_OVERCHARGE    = 5,    // AR10
        TAG_AR_INCINERATION         = 6,    // D16 AR11 (reserved)
        TAG_AR_FLAMETHROWER         = 7,    // D16 AR12 (reserved)
        TAG_AR_LIVEWIRE             = 23,   // AR8 the RunOut and its pulses (G2's Livewire tick row)
        TAG_AR_LIVEWIRE_BURST       = 24,   // AR8 the dispel burst (G2's Livewire burst row)
    };

    // creature_text 8983 groups (data/sql/updates/pending_db_world/rev_argelmach_blackrock_depths.sql). Group 4 is the
    // hard mode's console line (D16's rev owns it); 5 and 6 are D16's emotes (this rev writes them).
    enum ArgelmachTexts : std::uint8_t
    {
        YELL_AR_AGGRO               = 0,    // stock say made a yell, moved to aggro
        YELL_AR_TOXITRON            = 1,    // AR4 (90%; hard mode 80%)
        YELL_AR_ELECTRON            = 2,    // AR4 (65%; hard mode 60%)
        YELL_AR_ARCANOTON           = 3,    // AR4 (40%)
        YELL_AR_CONSOLE             = 4,    // D16 the console
        EMOTE_AR_INCINERATE         = 5,    // D16 AR11
        EMOTE_AR_CORE               = 6,    // D16 AR13
        YELL_AR_DEATH               = 7,    // death
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Build spec"; damage = % of the reference row, N level 55, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // Health (handoff section 3.6): Argelmach 150k normal (HealthModifier 71.736 on the level 55 paladin base 2,091,
    // the DT stub), 220k heroic (WP-H's override); each golem 25k / 37k (level 55 elite warrior base 2,614 x 9.56388;
    // heroic: WP-H's extra=). The hard mode's 500k / 50k / 100k are D16's.
    inline constexpr NH<std::uint32_t> kBossHealth{ 150000, 220000 };
    inline constexpr NH<std::uint32_t> kGolemHealth{ 25000, 37000 };
    inline constexpr std::uint32_t kPaladin55Base = 2091;
    inline constexpr std::uint32_t kWarrior55Base = 2614;
    inline constexpr std::uint32_t kGolemLevel = 55;

    // AR1 Chain Lightning: the stock 3 s cast on his victim, chaining to 5, first at 14 s then every 15 s (stock). An
    // interrupt is a reward on normal, expected on heroic. "Stock rescaled" (gap 36): a group pulse at the BRS
    // convention, 12% / 15% a target (designer question 1).
    inline constexpr std::uint32_t kChainFirstMs = 14000;
    inline constexpr std::uint32_t kChainEveryMs = 15000;
    inline constexpr std::uint32_t kChainCastMs = 3000;
    inline constexpr std::uint32_t kChainTargets = 5;
    inline constexpr NH<float> kChainPct{ 12.f, 15.f };

    // AR2 Shock: instant on the tank, first at 6 s then every 7 s (stock). "Stock rescaled": a tank swing-class hit,
    // 20% / 25% of the tank row (designer question 1).
    inline constexpr std::uint32_t kShockFirstMs = 6000;
    inline constexpr std::uint32_t kShockEveryMs = 7000;
    inline constexpr NH<float> kShockPct{ 20.f, 25.f };

    // AR3 Lightning Shield: on aggro and every 45 s, 10 min, 3 charges, 50% to strike a melee or ranged attacker
    // (stock); Magic: a purge is a reward. Each strike 3% / 4% of the non-tank row (designer question 1).
    inline constexpr std::uint32_t kShieldEveryMs = 45000;
    inline constexpr NH<float> kShieldStrikePct{ 3.f, 4.f };

    // AR9 Empowered (an orb that reached him, ruling 91): +15% damage for 30 s, up to 5 stacks. His melee takes it
    // from the aura; Chain Lightning and Shock (which ignore caster modifiers) by EmpoweredFactor in their script.
    inline constexpr float kEmpoweredPctPerStack = 15.f;
    inline constexpr std::uint32_t kEmpoweredMaxStacks = 5;
    inline constexpr std::uint32_t kEmpoweredMs = 30000;

    constexpr float EmpoweredFactor(std::uint32_t stacks)
    {
        return 1.f + kEmpoweredPctPerStack / 100.f * static_cast<float>(std::min(stacks, kEmpoweredMaxStacks));
    }

    // His own hits (Chain Lightning, Shock): the percent of the row on this difficulty times Empowered.
    constexpr float ScaledPct(std::uint32_t spellId, bool heroic, std::uint32_t empoweredStacks)
    {
        float const base = spellId == SPELL_AR_SHOCK ? kShockPct(heroic) : kChainPct(heroic);
        return base * EmpoweredFactor(empoweredStacks);
    }

    // AR5 Chemical Bomb (Toxitron): 5 s after the wake, then every 15 s (heroic 12 s): 2 players (the tank included,
    // ruling 88) are marked for 4 s; a 5 yd cloud then drops where each stands for 30 s: 6% / 9% a second (and the
    // kit's Standing in It slow). Carry it to the edge.
    inline constexpr std::uint32_t kBombFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kBombEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kBombMarks = 2;
    inline constexpr std::uint32_t kBombWarnMs = 4000;
    inline constexpr float kCloudRadiusYd = 5.f;
    inline constexpr std::uint32_t kCloudLifeMs = 30000;
    inline constexpr std::uint32_t kCloudTickMs = 1000;
    inline constexpr NH<float> kCloudPct{ 6.f, 9.f };
    inline constexpr float kBombPedestalAvoidYd = 6.f;      // the carrier bots keep their clouds off the pedestals

    // AR6 Poison Mist (Toxitron, heroic): 8 s after the wake, then every 20 s: a 2 s cast, 25% to everyone, then a
    // Poison DoT, 2% every 2 s for 10 s (handoff 7 #21: "Poison Mist 2% per 2 s"); a removal is a reward.
    inline constexpr std::uint32_t kMistFirstMs = 8000;
    inline constexpr std::uint32_t kMistEveryMs = 20000;
    inline constexpr std::uint32_t kMistCastMs = 2000;
    inline constexpr float kMistPct = 25.f;
    inline constexpr float kMistTickPct = 2.f;
    inline constexpr std::uint32_t kMistTickMs = 2000;
    inline constexpr std::uint32_t kMistDotMs = 10000;
    inline constexpr float kMistRadiusYd = 60.f;           // the whole chamber

    // AR7 Lethal Attraction (Electron): 5 s after the wake, then every 20 s (heroic 15 s): two players (the tank
    // included) are tethered; after 8 s, more than 5 yd apart, both are hit for 40% / 60%.
    inline constexpr std::uint32_t kTetherFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kTetherEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kTetherMs = 8000;
    inline constexpr float kTetherRangeYd = 5.f;
    inline constexpr NH<float> kTetherPct{ 40.f, 60.f };

    constexpr bool TetherHolds(float distanceYd)
    {
        return distanceYd <= kTetherRangeYd;
    }

    // AR8 Livewire (Electron, heroic): 8 s after the wake, then every 20 s: a Magic debuff on one player (not the
    // tank) for 12 s; everyone within 8 yd of the carrier (the carrier too) takes 4% every 2 s; a dispel bursts for
    // 30% on everyone else within 8 yd. Move out, then dispel (expected; the bots dispel once no ally is within 8 yd).
    // The carrier is never the tank (orchestrator default 2026-11-17, R-2-A designer question 1: the 2026-11-14 rule's
    // exception, the RunOut would push the melee off the boss for 12 s); a tank alone in the fight still gets it.
    inline constexpr bool kLivewireMarksTank = false;
    inline constexpr std::uint32_t kLivewireFirstMs = 8000;
    inline constexpr std::uint32_t kLivewireEveryMs = 20000;
    inline constexpr std::uint32_t kLivewireMs = 12000;
    inline constexpr std::uint32_t kLivewirePulseMs = 2000;
    inline constexpr float kLivewireRadiusYd = 8.f;
    inline constexpr float kLivewireZBandYd = 6.f;          // DS's NearPlayer height band
    inline constexpr float kLivewirePulsePct = 4.f;
    inline constexpr float kLivewireBurstPct = 30.f;

    // The pick rule for the carrier: not the tank (kLivewireMarksTank) unless nobody else is in the fight.
    inline DungeonKit::PickRule LivewirePickRule()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = !kLivewireMarksTank;
        rule.tankIfAlone = true;
        return rule;
    }

    // Inside a pulse: on the plane within the radius (edge inclusive) and within the height band.
    constexpr bool InLivewire(float planeDistanceYd, float heightDiffYd)
    {
        return planeDistanceYd <= kLivewireRadiusYd
            && (heightDiffYd < 0.f ? -heightDiffYd : heightDiffYd) <= kLivewireZBandYd;
    }

    // AR9 Power Generator (Arcanoton): 5 s after the wake, then every 20 s (heroic 15 s): an Arcane Orb leaves the
    // golem and drifts to Argelmach in 10 s (section 8 #20: a fixed travel time, whatever the distance). Walking into
    // it pops it: the popper takes 10% / 15% and gains Overcharged (+10% damage, 30 s, stacks 3). An orb that arrives
    // gives him Empowered (above).
    inline constexpr std::uint32_t kOrbFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kOrbEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kOrbTravelMs = 10000;
    inline constexpr float kOrbMinSpeed = 0.5f;             // yd/s: an orb summoned on top of him still drifts
    inline constexpr float kOrbRadiusYd = 2.5f;             // the touch (handoff 7 #21 "soak radii 3 yd" less reach)
    inline constexpr float kOrbReachYd = 3.f;               // from his center: arrived
    inline constexpr std::uint32_t kOrbLifeMs = 15000;      // a safety: an orb held back this long is gone
    inline constexpr NH<float> kOrbPopPct{ 10.f, 15.f };
    inline constexpr float kOverchargedPct = 10.f;
    inline constexpr std::uint32_t kOverchargedMaxStacks = 3;
    inline constexpr std::uint32_t kOverchargedMs = 30000;

    // yd/s for a fixed kOrbTravelMs flight over `distanceYd`.
    constexpr float OrbSpeed(float distanceYd)
    {
        float const speed = distanceYd * 1000.f / static_cast<float>(kOrbTravelMs);
        return speed < kOrbMinSpeed ? kOrbMinSpeed : speed;
    }

    // AR10 Arcane Overcharge (Arcanoton, heroic): 8 s after the wake, then every 20 s: a bomb lands on a spot after
    // 4 s; one player catches it for 30%, or everyone takes 40%.
    inline constexpr std::uint32_t kOverchargeFirstMs = 8000;
    inline constexpr std::uint32_t kOverchargeEveryMs = 20000;
    inline constexpr std::uint32_t kOverchargeWarnMs = 4000;
    inline constexpr float kOverchargeRadiusYd = 3.f;      // handoff 7 #21 "soak radii 3 yd"
    inline constexpr float kOverchargeCatchPct = 30.f;
    inline constexpr float kOverchargeBlastPct = 40.f;

    // ----------------------------------------------------------------------------------------------------------------
    // The golems and their pedestals (NAVMESH 3.2, gap 27; handoff 3.8)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Golem : std::uint8_t
    {
        Toxitron = 0,
        Electron = 1,
        Arcanoton = 2,
    };
    inline constexpr std::size_t kGolemCount = 3;
    inline constexpr std::array<Golem, kGolemCount> kGolems{ Golem::Toxitron, Golem::Electron, Golem::Arcanoton };

    constexpr std::size_t IndexOf(Golem g)
    {
        return static_cast<std::size_t>(g);
    }

    constexpr std::uint32_t EntryOf(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return BlackrockDepthsRework::NPC_BRD_TOXITRON;
            case Golem::Electron:   return BlackrockDepthsRework::NPC_BRD_ELECTRON;
            case Golem::Arcanoton:  return BlackrockDepthsRework::NPC_BRD_ARCANOTON;
        }
        return 0;
    }

    constexpr std::optional<Golem> GolemOfEntry(std::uint32_t entry)
    {
        for (Golem g : kGolems)
            if (EntryOf(g) == entry)
                return g;
        return std::nullopt;
    }

    constexpr char const* NameOf(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return "toxitron";
            case Golem::Electron:   return "electron";
            case Golem::Arcanoton:  return "arcanoton";
        }
        return "?";
    }

    constexpr std::uint8_t WakeYellOf(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return YELL_AR_TOXITRON;
            case Golem::Electron:   return YELL_AR_ELECTRON;
            case Golem::Arcanoton:  return YELL_AR_ARCANOTON;
        }
        return YELL_AR_TOXITRON;
    }

    // The pedestal spots on the chamber rim (NAVMESH 3.2; clearance 3.5-4.5 yd, 14+ yd apart). P4 is the hard mode's
    // fourth pedestal (D16: Magmatron, GO 301288), named here so both WPs read one table.
    inline constexpr Point3 kPedestal1{ 839.2f, 37.8f, -53.5f };
    inline constexpr Point3 kPedestal2{ 853.8f, 41.2f, -53.4f };
    inline constexpr Point3 kPedestal3{ 865.8f, 24.2f, -53.6f };
    inline constexpr Point3 kPedestal4{ 841.2f, 4.2f, -53.7f };
    inline constexpr std::array<Point3, 4> kPedestals{ kPedestal1, kPedestal2, kPedestal3, kPedestal4 };
    inline constexpr Vec2 kChamberMiddle{ 851.f, 22.f };

    constexpr Point3 PedestalOf(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return kPedestal1;
            case Golem::Electron:   return kPedestal2;
            case Golem::Arcanoton:  return kPedestal3;
        }
        return kPedestal1;
    }

    constexpr std::uint32_t PedestalGoOf(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return BlackrockDepthsRework::GO_BRD_PEDESTAL_1;
            case Golem::Electron:   return BlackrockDepthsRework::GO_BRD_PEDESTAL_2;
            case Golem::Arcanoton:  return BlackrockDepthsRework::GO_BRD_PEDESTAL_3;
        }
        return 0;
    }

    // A golem on its pedestal looks at the chamber's middle.
    inline float PedestalFacing(Golem g)
    {
        return DungeonKit::BearingTo(PedestalOf(g).XY(), kChamberMiddle);
    }

    // AR4: at 90%, 65% and 40% of his health one golem wakes, in a fixed order (Toxitron, Electron, Arcanoton). The
    // hard mode moves them (80 / 60 / 40, D16's hook). Thresholds are one-time wakes, not a repeating set piece.
    inline constexpr std::array<float, kGolemCount> kWakePct{ 90.f, 65.f, 40.f };
    inline constexpr std::uint32_t kSignatureDelayMs = 5000;    // AR5, AR7, AR9: 5 s after the wake

    // The golems to wake now at `healthPct`, in the fixed order: every golem whose threshold is at or above the health
    // and not yet woken (a big hit past two thresholds wakes both: the failing path stacks them).
    inline std::vector<Golem> GolemsToWake(float healthPct, std::array<float, kGolemCount> const& thresholds,
        std::array<bool, kGolemCount> const& woken)
    {
        std::vector<Golem> out;
        for (Golem g : kGolems)
            if (!woken[IndexOf(g)] && healthPct <= thresholds[IndexOf(g)])
                out.push_back(g);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The chamber (the navmesh 2026-11-17, polys.json along the z -57..-50 floor; mesh edge less ~0.5 yd)
    // ----------------------------------------------------------------------------------------------------------------

    // x north, y west. The south side narrows into the passage (x 816-836, 16-19 yd wide); the north-west wall runs
    // diagonally from (856, 42) to (868, 30); the north-east side from (850, 0) to (868, 19). 1,022 sq yd (the mesh
    // north of x 836: 1,108; 28 sq yd of the polygon are off the mesh, the notch at x 851-856, y 4-12; NAVMESH's
    // 1,300 counts the floor down to x 822).
    inline constexpr std::array<Vec2, 10> kChamber{ {
        { 836.5f, 3.5f }, { 839.5f, 0.5f }, { 850.5f, 0.5f }, { 856.5f, 14.5f }, { 868.5f, 19.5f },
        { 868.5f, 29.5f }, { 856.5f, 42.5f }, { 839.5f, 42.5f }, { 836.5f, 39.5f }, { 836.5f, 21.5f },
    } };
    inline constexpr float kChamberZ = -53.6f;
    inline constexpr float kChamberZMin = -56.f;
    inline constexpr float kChamberZMax = -50.f;

    inline bool InChamber(Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(kChamber), p);
    }

    // The distance from p to the chamber's edge (0 outside).
    inline float ChamberClearance(Vec2 p)
    {
        if (!InChamber(p))
            return 0.f;
        float best = 1e9f;
        for (std::size_t i = 0, j = kChamber.size() - 1; i < kChamber.size(); j = i++)
            best = std::min(best, DungeonKit::SegmentDistance(kChamber[j], kChamber[i], p));
        return best;
    }

    inline float ChamberArea()
    {
        float twice = 0.f;
        for (std::size_t i = 0, j = kChamber.size() - 1; i < kChamber.size(); j = i++)
            twice += kChamber[j].x * kChamber[i].y - kChamber[i].x * kChamber[j].y;
        return std::fabs(twice) / 2.f;
    }

    // AR10's spot: a point on the open floor, kOverchargeEdgeYd off the walls, kOverchargePedestalYd from every
    // pedestal and between kOverchargeMinYd and kOverchargeMaxYd from Argelmach (`boss`), so somebody has to walk to
    // it. `rand01` returns [0, 1). Falls back to the chamber's middle after kOverchargeTries draws.
    inline constexpr float kOverchargeEdgeYd = 3.f;
    inline constexpr float kOverchargePedestalYd = 6.f;
    inline constexpr float kOverchargeMinYd = 8.f;
    inline constexpr float kOverchargeMaxYd = 25.f;
    inline constexpr std::uint32_t kOverchargeTries = 64;

    inline bool OverchargeSpotFits(Vec2 p, Vec2 boss)
    {
        if (ChamberClearance(p) < kOverchargeEdgeYd)
            return false;
        for (Point3 const& pedestal : kPedestals)
            if (DungeonKit::Distance(p, pedestal.XY()) < kOverchargePedestalYd)
                return false;
        float const d = DungeonKit::Distance(p, boss);
        return d >= kOverchargeMinYd && d <= kOverchargeMaxYd;
    }

    template <class Rand01>
    Vec2 PickOverchargeSpot(Vec2 boss, Rand01&& rand01)
    {
        float minX = kChamber[0].x;
        float maxX = minX;
        float minY = kChamber[0].y;
        float maxY = minY;
        for (Vec2 const& v : kChamber)
        {
            minX = std::min(minX, v.x);
            maxX = std::max(maxX, v.x);
            minY = std::min(minY, v.y);
            maxY = std::max(maxY, v.y);
        }
        for (std::uint32_t i = 0; i < kOverchargeTries; ++i)
        {
            float const x = minX + (maxX - minX) * rand01();
            float const y = minY + (maxY - minY) * rand01();
            Vec2 const p{ x, y };
            if (OverchargeSpotFits(p, boss))
                return p;
        }
        return kChamberMiddle;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Beat: a repeating beat on the AI's own ms clock (start to start, never in the past)
    // ----------------------------------------------------------------------------------------------------------------

    class Beat
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t afterMs)
        {
            _on = true;
            _dueMs = nowMs + afterMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }
        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        std::uint64_t _dueMs = 0;
        bool _on = false;
    };
}

#endif
