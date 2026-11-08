/*
 * mod-dungeon-bosses, Scholomance S8: The Ravenian (10507) and Master Corvane (300542), the pure, host-testable part
 * (no engine headers): the spell ids, the per-difficulty tuning, the order rotation (never the same twice), the phase
 * rules (the 50% transition, Unbound, Driven, Bereaved), the landing pick, the vault's walls for Trample, Corvane's
 * filler rule, the never-paused fight timeline and the Vault of the Ravenian's solo lesson plan. Build spec: SC
 * 2193-2259 (build spec), SC 2052-2192 (design: pitch A "The Leash", rounds 1-3 and the side questions), RV1-RV11;
 * handoff section 3.4 rows RV, section 3.5 row S8, section 3.6 (normal 160k / 50k, heroic 210k / 65k, examiners
 * 60k / 20k), section 3.7 (the solo lesson), section 3.8 (the vault) and the user ruling of 2026-11-08 (Corvane's
 * phase 1 seat is kRavenianUserSpot, right behind the Ravenian; the block perch is retired).
 *
 * Damage percentages are of the reference health row (normal 3,670 / heroic 4,120 non-tank at level 60).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAVENIAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAVENIAN_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include "SoloLessonLogic.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace ScholoRavenian
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScholomanceRework::Arena;
    using ScholomanceRework::ArenaRegion;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRavenian;

    // Declared in apps/dbc-tools source/npcs/scholomance/the_ravenian.py (same ids).
    enum RavenianSpells : std::uint32_t
    {
        SPELL_RV_LEASH              = 206270,   // the leash beam: Corvane's channel on the Ravenian (casts go on)
        SPELL_RV_ORDER_TRAMPLE      = 206271,   // RV1 Corvane's 2 s order (interruptible; unselectable in phase 1)
        SPELL_RV_ORDER_SWEEP        = 206272,   // RV2
        SPELL_RV_ORDER_SMASH        = 206273,   // RV3
        SPELL_RV_TRAMPLE            = 206274,   // RV1 the line's hit: resolve copy (Physical)
        SPELL_RV_SWEEP              = 206275,   // RV2 the frontal's hit: resolve copy (Physical)
        SPELL_RV_SMASH              = 206276,   // RV3 the ring's hit: resolve copy (Physical)
        SPELL_RV_MEND_TRANSITION    = 206277,   // RV5 the 50% Mend Construct from the seat: cannot be stopped
        SPELL_RV_MEND               = 206278,   // RV8 the phase 2 Mend Construct: 3 s, interruptible
        SPELL_RV_TELEPORT           = 206279,   // RV5 the teleport's look (Corvane, at both ends)
        SPELL_RV_UNBOUND_STRIKE     = 206280,   // RV6 the move on Corvane: 8% of his health
        SPELL_RV_UNBOUND            = 206281,   // RV6 the Ravenian's 2 s stand (the leash snapped)
        SPELL_RV_DRIVEN             = 206282,   // RV7 heroic: +10% damage a stack, for the fight, uncapped
        SPELL_RV_SHADOW_BOLT        = 206283,   // RV9 Corvane's filler
        SPELL_RV_BEREAVED           = 206284,   // RV10 the survivor: +10% damage a stack every 5 s, uncapped
        SPELL_RV_SUNDERING_CLEAVE   = 206285,   // RV11 stock 25174 on one target (the tank)
        // 206286-206289 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_RV_LEASH), "Ravenian spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_RV_SUNDERING_CLEAVE), "Ravenian spells sit in his slice");

    // Stock look: Ghost Visual 9617 (the Ravenian's echo in the solo lesson; WP-V AURA_GHOST_VISUAL).
    std::uint32_t constexpr kAuraGhostVisual = 9617;

    // Registry tags (the build spec's RV numbers).
    enum RavenianTags : std::uint32_t
    {
        TAG_TRAMPLE         = 1,    // RV1
        TAG_SWEEP           = 2,    // RV2
        TAG_SMASH           = 3,    // RV3
    };

    // Script names. The boss's is bound by the DT file; Corvane's on his entry 300542 (this WP); the two Graduate
    // Examiners (S13's entries NPC_SC_EXAMINER_RAVENIAN 300551 and NPC_SC_EXAMINER_CORVANE 300552) are registered once
    // wave C binds (kWaveCBound). The examiner Ravenian brings its own examiner Corvane (it summons 300552 at the
    // seat), so S13 summons only 300551.
    char constexpr kCorvaneScriptName[] = "npc_sc_master_corvane";
    char constexpr kExaminerRavenianScriptName[] = "npc_sc_examiner_ravenian";
    char constexpr kExaminerCorvaneScriptName[] = "npc_sc_examiner_corvane";
    std::uint32_t constexpr kExaminerRavenianHealth = 60000;   // handoff section 3.6, SC "Hard mode"
    std::uint32_t constexpr kExaminerCorvaneHealth = 20000;

    // The examiners fight at heroic values on any map (SC: "both mechanics at H values").
    constexpr bool HeroicValues(bool heroicMap, bool examiner)
    {
        return heroicMap || examiner;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The orders (RV1-RV4): Corvane's 2 s cast and a yell naming the move, then the Ravenian's own 2 s marker
    // ----------------------------------------------------------------------------------------------------------------

    enum class Order : std::uint8_t
    {
        Trample = 0,
        Sweep = 1,
        Smash = 2,
    };
    std::size_t constexpr kOrderCount = 3;

    constexpr char const* OrderName(Order o)
    {
        switch (o)
        {
            case Order::Trample: return "trample";
            case Order::Sweep:   return "sweep";
            case Order::Smash:   return "smash";
        }
        return "?";
    }

    constexpr std::uint32_t OrderCastSpell(Order o)
    {
        switch (o)
        {
            case Order::Trample: return SPELL_RV_ORDER_TRAMPLE;
            case Order::Sweep:   return SPELL_RV_ORDER_SWEEP;
            case Order::Smash:   return SPELL_RV_ORDER_SMASH;
        }
        return 0;
    }

    constexpr std::uint32_t OrderHitSpell(Order o)
    {
        switch (o)
        {
            case Order::Trample: return SPELL_RV_TRAMPLE;
            case Order::Sweep:   return SPELL_RV_SWEEP;
            case Order::Smash:   return SPELL_RV_SMASH;
        }
        return 0;
    }

    constexpr std::uint8_t OrderYell(Order o)
    {
        switch (o)
        {
            case Order::Trample: return ScholomanceRework::YELL_CORVANE_TRAMPLE;
            case Order::Sweep:   return ScholomanceRework::YELL_CORVANE_SWEEP;
            case Order::Smash:   return ScholomanceRework::YELL_CORVANE_SMASH;
        }
        return ScholomanceRework::YELL_CORVANE_TRAMPLE;
    }

    constexpr std::uint32_t OrderTag(Order o)
    {
        return std::uint32_t(o) + 1;
    }

    // The order of a cast bar spell (Corvane's OnSpellCast / OnSpellFailed), none for any other spell.
    constexpr std::optional<Order> OrderOfCast(std::uint32_t spellId)
    {
        for (std::size_t i = 0; i < kOrderCount; ++i)
            if (OrderCastSpell(Order(i)) == spellId)
                return Order(i);
        return std::nullopt;
    }

    // RV4: a random order, never the same twice in a row. `roll` is any random number (the caller's urand); with no
    // last order it picks among all three, else among the other two.
    constexpr Order NextOrder(std::optional<Order> last, std::uint32_t roll)
    {
        if (!last)
            return Order(roll % kOrderCount);
        std::uint32_t const skip = std::uint32_t(*last);
        std::uint32_t const pick = roll % (kOrderCount - 1);
        return Order(pick >= skip ? pick + 1 : pick);
    }

    std::uint32_t constexpr kOrderCastMs = 2000;            // Corvane's cast and yell
    std::uint32_t constexpr kOrderMarkerMs = 2000;          // then the Ravenian's own marker
    // RV1 Trample: a line from the Ravenian through a random non-tank player to the wall, 4 yd wide (L4). 35% / 50%.
    float constexpr kTrampleWidth = 4.f;
    float constexpr kTrampleOverrun = 60.f;                 // past the player, then stopped by the vault's walls
    inline constexpr NH<float> kTramplePct{ 35.f, 50.f };
    // RV2 Sweep: a 120 degree frontal, 12 yd, toward his tank (the tank is exempt: a Frontal). 45% / 60%.
    float constexpr kSweepAngle = 120.f;
    float constexpr kSweepLength = 12.f;
    inline constexpr NH<float> kSweepPct{ 45.f, 60.f };
    // RV3 Smash: a 6 yd ring on a random non-tank player. 30% / 40% plus Weakened (ruling 21, both difficulties).
    float constexpr kSmashRadius = 6.f;
    inline constexpr NH<float> kSmashPct{ 30.f, 40.f };

    constexpr float OrderPct(Order o, bool heroic)
    {
        switch (o)
        {
            case Order::Trample: return kTramplePct(heroic);
            case Order::Sweep:   return kSweepPct(heroic);
            case Order::Smash:   return kSmashPct(heroic);
        }
        return 0.f;
    }

    // Phase 1: first at 8 s, every 12 s (heroic: a pair, the second called as the first's marker appears, so its move
    // lands right after the first's). Phase 2: every 15 s, the first kHandOrderFirstMs after Corvane lands.
    std::uint32_t constexpr kLeashOrderFirstMs = 8000;
    std::uint32_t constexpr kLeashOrderEveryMs = 12000;
    std::uint32_t constexpr kHandOrderFirstMs = 5000;
    std::uint32_t constexpr kHandOrderEveryMs = 15000;
    inline constexpr NH<bool> kPairedOrders{ false, true };

    // ----------------------------------------------------------------------------------------------------------------
    // The transition (RV5), phase 2 (RV6-RV9), Bereaved (RV10)
    // ----------------------------------------------------------------------------------------------------------------

    // RV5: at 50% Corvane casts Mend Construct from his seat (cannot be stopped: he is out of reach), heals the
    // Ravenian 10% / 15% of his health, yells line 4, then teleports to his landing and becomes attackable.
    float constexpr kTransitionHealthPct = 50.f;
    std::uint32_t constexpr kTransitionCastMs = 2000;
    std::uint32_t constexpr kTransitionFallbackMs = 3500;   // no word from the cast by then: he lands anyway
    inline constexpr NH<float> kTransitionHealPct{ 10.f, 15.f };

    enum class Stage : std::uint8_t
    {
        Leash = 1,          // phase 1: Corvane on his seat, unselectable, orders nobody can stop
        Transition = 2,     // the one-off Mend Construct, then the teleport
        Hand = 3,           // phase 2: Corvane on the floor; orders and Mend are interruptible
        Bereaved = 4,       // one of them is dead: the survivor enrages (RV10)
    };

    constexpr bool TransitionDue(Stage stage, float ravenianHealthPct)
    {
        return stage == Stage::Leash && ravenianHealthPct <= kTransitionHealthPct;
    }

    // RV6 Unbound: an interrupted order in phase 2 makes the Ravenian do the move on Corvane: 8% of Corvane's health,
    // and the Ravenian stands still 2 s (the leash snapping). RV7 Driven (heroic): an order nobody interrupts in
    // phase 2 gives the Ravenian +10% damage, stacking, for the fight (ruling 24: uncapped).
    float constexpr kUnboundPct = 8.f;
    std::uint32_t constexpr kUnboundStandMs = 2000;
    inline constexpr NH<bool> kDriven{ false, true };
    float constexpr kStackDamagePct = 10.f;                 // Driven and Bereaved, each stack

    // What an order's cast ends in. Phase 1 orders cannot be stopped (he is out of reach); a phase 1 cast that fails
    // anyway (his own death) is simply lost.
    enum class OrderOutcome : std::uint8_t
    {
        Performed,          // the Ravenian does the move on the group
        PerformedDriven,    // ... and gains a Driven stack (heroic phase 2)
        Unbound,            // the move on Corvane, the 2 s stand
        Lost,               // nothing
    };

    constexpr OrderOutcome OrderResult(Stage stage, bool completed, bool heroic)
    {
        if (stage == Stage::Hand)
        {
            if (!completed)
                return OrderOutcome::Unbound;
            return kDriven(heroic) ? OrderOutcome::PerformedDriven : OrderOutcome::Performed;
        }
        if (stage == Stage::Leash || stage == Stage::Transition)
            return completed ? OrderOutcome::Performed : OrderOutcome::Lost;
        return OrderOutcome::Lost;
    }

    // RV8 Mend Construct: 3 s, first kMendFirstMs after he lands, every 20 s; 6% / 10% of the Ravenian's health.
    // Capped by Corvane's death.
    std::uint32_t constexpr kMendCastMs = 3000;
    std::uint32_t constexpr kMendFirstMs = 10000;
    std::uint32_t constexpr kMendEveryMs = 20000;
    inline constexpr NH<float> kMendPct{ 6.f, 10.f };

    // RV9 Shadow Bolt: Corvane's filler at a random player, between orders and heals: 15% / 20% Shadow. A 2.5 s cast,
    // at most one every kShadowBoltEveryMs, and only when the next order or Mend is not due before the bolt is out.
    std::uint32_t constexpr kShadowBoltCastMs = 2500;
    std::uint32_t constexpr kShadowBoltEveryMs = 4000;
    std::uint32_t constexpr kShadowBoltMarginMs = 500;
    float constexpr kShadowBoltRange = 40.f;
    inline constexpr NH<float> kShadowBoltPct{ 15.f, 20.f };

    // The bolt fits when every other beat of Corvane's is at least the bolt's cast (plus a margin) away.
    constexpr bool BoltFits(std::uint32_t now, std::uint32_t nextOrder, std::uint32_t nextMend)
    {
        std::uint32_t const clear = now + kShadowBoltCastMs + kShadowBoltMarginMs;
        return nextOrder >= clear && nextMend >= clear;
    }

    // RV10 Bereaved: whichever falls first (Corvane's death, the Ravenian's collapse: see Pair below) enrages the
    // other: +10% damage every 5 s, stacking, uncapped. The Ravenian unleashed also does a random order on his own
    // every 10 s at random players (no cast: his 2 s marker is the warning), the first kUnleashedOrderFirstMs after
    // Corvane's death.
    std::uint32_t constexpr kBereavedEveryMs = 5000;
    std::uint32_t constexpr kUnleashedOrderFirstMs = 5000;
    std::uint32_t constexpr kUnleashedOrderEveryMs = 10000;

    // Damage done from Driven and Bereaved stacks. The aura raises his melee; his orders and Corvane's bolt ignore
    // caster modifiers (the registry's percent, RefFlat), so the script scales them by the same factor.
    constexpr float DamageScale(std::uint32_t stacks)
    {
        return 1.f + float(stacks) * kStackDamagePct / 100.f;
    }

    // Driven and Bereaved are two auras, so the engine multiplies them on his melee (two MOD_DAMAGE_PERCENT_DONE
    // auras); the script's orders and bolts do the same, so a move and a swing scale alike.
    constexpr float StackedDamageScale(std::uint32_t driven, std::uint32_t bereaved)
    {
        return DamageScale(driven) * DamageScale(bereaved);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pair's lives (user ruling 1, 2026-11-08). The Ravenian never dies before Corvane: lethal damage while
    // Corvane stands leaves him at 1 HP, collapsed (inert, not selectable, not attackable), and Corvane fights on
    // alone (Bereaved). Corvane's death then kills the collapsed Ravenian for real (a player killer: the credit, the
    // loot and DONE land together). A wipe while he is collapsed resets both (his evade); Corvane gone without a death
    // (a despawn) does the same. Corvane dying first is the other order (the Ravenian unleashed, RV10).
    // ----------------------------------------------------------------------------------------------------------------

    enum class Pair : std::uint8_t
    {
        Both = 0,           // both stand (phases 1 and 2), or the Ravenian fights on alone after Corvane (Bereaved)
        Collapsed = 1,      // the Ravenian lies at 1 HP; Corvane fights alone
        Over = 2,           // the Ravenian is dead
    };

    struct RavenianHit
    {
        std::uint32_t damage = 0;       // what lands
        bool collapse = false;          // this hit collapses him
    };

    // A hit of `damage` on the Ravenian at `health`. Lethal while Corvane stands: he keeps 1 HP and collapses.
    // Collapsed: nothing lands (he is not attackable; a damage over time effect still ticking does nothing).
    constexpr RavenianHit RavenianDamage(Pair pair, std::uint32_t health, std::uint32_t damage, bool corvaneStanding)
    {
        if (pair == Pair::Collapsed)
            return { 0, false };
        if (pair == Pair::Both && corvaneStanding && damage >= health)
            return { health > 1 ? health - 1 : 0, true };
        return { damage, false };
    }

    // The collapsed Ravenian's tick: what happens next.
    enum class CollapsedStep : std::uint8_t
    {
        Hold = 0,           // Corvane still fights
        Kill = 1,           // Corvane is dead: the Ravenian dies for real
        Reset = 2,          // a wipe, or Corvane gone without a death: both reset (the Ravenian evades)
    };

    // `corvaneDied`: his death was reported (or he lies dead); `wipe`: Corvane alone found nobody left to fight;
    // `corvanePresent`: his unit is still on the map.
    constexpr CollapsedStep NextCollapsedStep(bool corvaneDied, bool wipe, bool corvanePresent)
    {
        if (corvaneDied)
            return CollapsedStep::Kill;
        if (wipe || !corvanePresent)
            return CollapsedStep::Reset;
        return CollapsedStep::Hold;
    }

    // Boss data (build spec): in phase 2 both are targets, kept close (kill together: DPS hit whichever has more health
    // left, by percent, so they fall within about 10 s of each other).
    float constexpr kKillTogetherPct = 10.f;

    // RV11 Sundering Cleave (a copy of 25174 on one target): the stock SmartAI timers, 1 to 22 s, then every 14 to
    // 24 s, on his victim in melee range.
    std::uint32_t constexpr kCleaveFirstMinMs = 1000;
    std::uint32_t constexpr kCleaveFirstMaxMs = 22000;
    std::uint32_t constexpr kCleaveEveryMinMs = 14000;
    std::uint32_t constexpr kCleaveEveryMaxMs = 24000;

    // Melee: DamageModifier 3.5 (the AzerothCore base value; the live 7 is a mod-progression leftover), set by the DT
    // file; heroic is the heroic template's (WP-T).

    // ----------------------------------------------------------------------------------------------------------------
    // The vault: Corvane's seat, his landing, Trample's walls
    // ----------------------------------------------------------------------------------------------------------------

    // User ruling 2026-11-08 (overrides handoff section 7 #15): Corvane's phase 1 seat is the user's spot right behind
    // the Ravenian, at the vault's west wall, inside RavenianArena() (so nothing there leashes or evades him). He
    // stands there unselectable and not attackable until the transition.
    inline constexpr ScholomanceRework::Point4 kCorvaneSeat = ScholomanceRework::kRavenianUserSpot;

    // His landing (RV5, SC gap 12): a fixed spot at least 15 yd from the Ravenian. ScholomanceRework::kCorvaneLandings
    // in order: (128, -1) first (the user's pick), then (140, -1), then (122, 0); the first one far enough from where
    // the Ravenian stands now, else the farthest.
    float constexpr kLandingMinYd = 15.f;

    inline std::size_t PickLanding(Vec2 ravenian)
    {
        std::size_t farthest = 0;
        float best = -1.f;
        for (std::size_t i = 0; i < ScholomanceRework::kCorvaneLandings.size(); ++i)
        {
            float const d = DungeonKit::Distance(ScholomanceRework::kCorvaneLandings[i].XY(), ravenian);
            if (d >= kLandingMinYd)
                return i;
            if (d > best)
            {
                best = d;
                farthest = i;
            }
        }
        return farthest;
    }

    // The vault's walls for Trample (KS: the line must not run past the vault): the central band
    // (ScholomanceRework::kRavenianVault, x 92-150, y -11.5 to 8) joined with the north hall (kRavenianNorthHall,
    // x 128-150, y -18 to 16) as one polygon, z 72-82. A source off it (the Ravenian held at the arena's edge) uses
    // the arena circle. LineStrikePath stops a line 0.5 yd short of the wall it meets.
    inline Arena VaultWalls()
    {
        Arena walls(ArenaRegion::Polygon({ { 92.0f, -11.5f }, { 128.0f, -11.5f }, { 128.0f, -18.0f },
            { 150.0f, -18.0f }, { 150.0f, 16.0f }, { 128.0f, 16.0f }, { 128.0f, 8.0f }, { 92.0f, 8.0f } },
            72.0f, 82.0f));
        walls.Add(ArenaRegion::Circle({ 122.0f, -1.0f }, 32.f, 72.0f, 82.0f));
        return walls;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). A beat that comes due
    // while its caster casts stays due until the cast ends.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        Order = 0,          // Corvane's order (phases 1, 2) or the unleashed Ravenian's own (Bereaved)
        Mend = 1,           // phase 2
        Bolt = 2,           // phase 2 (Corvane alone runs his own)
        Cleave = 3,         // the Ravenian's Sundering Cleave
        Bereaved = 4,       // a stack on the survivor
        Leash = 5,          // the beam's upkeep check
    };
    std::size_t constexpr kBeatCount = 6;
    std::uint32_t constexpr kNever = 0xFFFFFFFFu;
    std::uint32_t constexpr kRetryMs = 1000;                // nobody to target, or Corvane busy: try again this soon
    std::uint32_t constexpr kLeashCheckMs = 1000;

    struct Timeline
    {
        std::uint32_t now = 0;                              // ms since the pull
        std::array<std::uint32_t, kBeatCount> next{ { kNever, kNever, kNever, kNever, kNever, kNever } };

        void Start(std::uint32_t cleaveFirst)
        {
            now = 0;
            next = { { kLeashOrderFirstMs, kNever, kNever, cleaveFirst, kNever, kLeashCheckMs } };
        }

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        bool Due(Beat b) const
        {
            return next[std::size_t(b)] != kNever && now >= next[std::size_t(b)];
        }

        std::uint32_t At(Beat b) const
        {
            return next[std::size_t(b)];
        }

        // Fired: the next one is `in` from now.
        void Set(Beat b, std::uint32_t in)
        {
            next[std::size_t(b)] = now + in;
        }

        void Stop(Beat b)
        {
            next[std::size_t(b)] = kNever;
        }

        void Retry(Beat b)
        {
            Set(b, kRetryMs);
        }

        // Corvane lands (phase 2): orders every 15 s from kHandOrderFirstMs, Mend from kMendFirstMs, bolts at once.
        void Land()
        {
            Set(Beat::Order, kHandOrderFirstMs);
            Set(Beat::Mend, kMendFirstMs);
            Set(Beat::Bolt, 0);
        }

        // Corvane is dead: no Mend, no bolt; the Ravenian's own orders and his Bereaved stacks.
        void Unleash()
        {
            Stop(Beat::Mend);
            Stop(Beat::Bolt);
            Set(Beat::Order, kUnleashedOrderFirstMs);
            Set(Beat::Bereaved, kBereavedEveryMs);
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The Vault of the Ravenian's solo lesson (SC 2960-2971, handoff section 3.7): the Ravenian's echo carries out 3
    // orders on the student (Trample, Sweep and Smash, each once, in a random order: never the same twice); each is
    // called (the echo's 2 s order bar) and then its 2 s marker lands, as in the fight. Any hit fails the lesson
    // (15% / 25% plus Weakened, SoloLessonLogic.h). Orders are called at 0.5, 5 and 9.5 s, so the last lands at 13.5 s,
    // inside the 15 s. The echo stands kLessonSourceYd from the student when it calls (so the Sweep reaches).
    // ----------------------------------------------------------------------------------------------------------------

    std::size_t constexpr kLessonOrders = 3;
    inline std::array<std::uint32_t, kLessonOrders> constexpr kLessonCallAtMs{ { 500, 5000, 9500 } };
    std::uint32_t constexpr kLessonCallMs = kOrderCastMs;
    std::uint32_t constexpr kLessonMarkerMs = kOrderMarkerMs;
    float constexpr kLessonSourceYd = 6.f;

    constexpr float LessonPct(bool heroic)
    {
        return float(heroic ? ScholomanceRework::kLessonFailurePctHeroic : ScholomanceRework::kLessonFailurePctNormal);
    }

    // The three orders in a random order (a permutation, so never the same twice in a row): `first` and `second` are
    // two random numbers.
    constexpr std::array<Order, kLessonOrders> LessonOrders(std::uint32_t first, std::uint32_t second)
    {
        Order const a = NextOrder(std::nullopt, first);
        Order const b = NextOrder(a, second);
        Order c = Order::Trample;
        for (std::size_t i = 0; i < kOrderCount; ++i)
            if (Order(i) != a && Order(i) != b)
                c = Order(i);
        return { { a, b, c } };
    }
}

#endif
