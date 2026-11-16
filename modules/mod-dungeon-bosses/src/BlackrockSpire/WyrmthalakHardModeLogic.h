/*
 * mod-dungeon-bosses, Blackrock Spire B9:
 * Overlord Wyrmthalak's hard mode, the war horn, the pure, host-testable part (no engine headers). WP-B9 owns this
 * file: its spell ids (inside kSpellsWarHorn of BlackrockSpireRework.h, 210290-210339), tuning constants, flex target
 * pairs, the unlock book (which casts the champions' deaths unlock and when they are due), the burn rule, the rider
 * cap, the horn's refusals and the G1 drill parity of the chained axes, tested by
 * tests/brs_wyrmthalak_hard_mode_test.cpp. The engine side is wyrmthalak_hard_mode.cpp (on B8's hooks,
 * WyrmthalakFight.h).
 *
 * Build spec SP 2436-2521 rows WT9-WT17 (design SP 2322-2389, rulings 48-49); handoff section 3.7, section 3.4 row
 * "WT hard mode", section 7 #14 (the horn is a per-pull flag), #22 (hard mode health x the flex ladder), #25 (the spit
 * patches and the spear chain crossings: WeakenedOncePerPlayer), #26 (the haul is G1 drill tag 6), #28 (the cap of 3
 * burns: the ledge's open edge is about 28 yd by chord, short of the 35 yd the edge walk needs). The hard mode uses
 * the heroic reference row (it exists on heroic only); counts "a / b" are 5 players / 6 or more (FlexAB).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_HARD_MODE_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include "WyrmthalakLogic.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrsWarHorn
{
    using BlackrockSpireRework::FlexAB;
    using BrsWyrmthalak::Tribe;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsWarHorn;

    // apps/dbc-tools source/npcs/blackrock_spire/wyrmthalak_hard_mode.py declares every one of them.
    enum WyrmthalakHardModeSpells : std::uint32_t
    {
        SPELL_WH_TRIBAL_WARD        = kSpellSlice.first + 0,    // 210290 WT13 -20% damage taken a stack (one a living
                                                                // champion), on him
        SPELL_WH_HORN_BLOWN         = kSpellSlice.first + 1,    // 210291 WT9 the horn's burst (V-1's SV 90602), cast by
                                                                // a stalker at the horn on itself
        SPELL_WH_CAUSTIC_POISON     = kSpellSlice.first + 2,    // 210292 WT14 Poison, 0.5% a stack every 2 s, 10, 20 s
        SPELL_WH_CAUSTIC_ROAR       = kSpellSlice.first + 3,    // 210293 WT14 the 2.5 s interruptible cast (Nature)
        SPELL_WH_CAUSTIC_ROAR_HIT   = kSpellSlice.first + 4,    // 210294 WT14 the landed roar (resolve copy, Nature)
        SPELL_WH_SPEAR_THROW        = kSpellSlice.first + 5,    // 210295 WT15 the spear in flight (look only)
        SPELL_WH_SPEAR_IMPACT       = kSpellSlice.first + 6,    // 210296 WT15 the impact (resolve copy, Physical)
        SPELL_WH_SPEAR_CHAIN        = kSpellSlice.first + 7,    // 210297 WT15 the chain beam on the speared player (an
                                                                // anchor channels it; its aura keeps them off the line)
        SPELL_WH_SPEAR_CHAIN_HIT    = kSpellSlice.first + 8,    // 210298 WT15 a chain crossing (resolve copy, Physical)
        SPELL_WH_SPIT               = kSpellSlice.first + 9,    // 210299 WT16 a spit circle (resolve copy, Shadow)
        SPELL_WH_SPIT_MISSILE       = kSpellSlice.first + 10,   // 210300 WT16 the spit in flight (look only)
        SPELL_WH_SPIT_LANDING       = kSpellSlice.first + 11,   // 210301 WT16 the spit's landing burst (look only)
        SPELL_WH_SPIT_PATCH         = kSpellSlice.first + 12,   // 210302 WT16 a patch's tick (resolve copy, Shadow)
        SPELL_WH_AXE_CHAIN_HIT      = kSpellSlice.first + 13,   // 210303 WT11 a chain crossing (resolve copy, Physical)
        SPELL_WH_HAUL               = kSpellSlice.first + 14,   // 210304 WT11 the haul (resolve copy, Physical)
        SPELL_WH_RABIES             = kSpellSlice.first + 15,   // 210305 WT12 Disease, 1.5% a stack every 3 s, 5, 30 s
        SPELL_WH_RABID_BITE         = kSpellSlice.first + 16,   // 210306 WT12 the kept rider's melee proc (-> Rabies)
    };
    // 210307-210339 spare.
    std::uint32_t constexpr kFirstSpell = SPELL_WH_TRIBAL_WARD;
    std::uint32_t constexpr kLastSpell = SPELL_WH_RABID_BITE;
    static_assert(kLastSpell <= kSpellSlice.last, "the war horn's spells must stay in its slice");

    // Registry tags (per encounter: Wyrmthalak's; B8 uses 1-6).
    enum WarHornTags : std::uint32_t
    {
        TAG_WH_SHARD        = 20,
        TAG_WH_OVERCHARGE   = 21,
        TAG_WH_AXE_CHAIN    = 22,
        TAG_WH_HAUL         = 23,
        TAG_WH_ROAR         = 24,
        TAG_WH_SPEAR        = 25,
        TAG_WH_SPEAR_CHAIN  = 26,
        TAG_WH_SPIT         = 27,
        TAG_WH_SPIT_PATCH   = 28,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // WT9 the war horn: usable on heroic, before the pull, before the kill, once per attempt
    // ----------------------------------------------------------------------------------------------------------------
    enum class HornRefusal : std::uint8_t
    {
        None = 0,           // usable: blowing it lights the hard mode for the next pull
        NotHeroic,
        Fighting,           // Wyrmthalak is in combat
        Dead,               // Wyrmthalak is dead (this lockout)
        AlreadyBlown,       // lit already (until the attempt ends)
    };

    // The same rule as the instance's WarHornChangeAllowed (BlackrockSpireRework.h), plus "already lit".
    constexpr HornRefusal HornRefusalFor(bool heroic, std::uint32_t wyrmthalakState, bool lit)
    {
        if (!heroic)
            return HornRefusal::NotHeroic;
        if (wyrmthalakState == DungeonKit::State::InProgress)
            return HornRefusal::Fighting;
        if (wyrmthalakState == DungeonKit::State::Done)
            return HornRefusal::Dead;
        if (lit)
            return HornRefusal::AlreadyBlown;
        return HornRefusal::None;
    }

    constexpr char const* HornRefusalText(HornRefusal r)
    {
        switch (r)
        {
            case HornRefusal::None:         return "";
            case HornRefusal::NotHeroic:    return "The war horn is silent. Only a heroic assault musters the Spire.";
            case HornRefusal::Fighting:     return "The battle has already begun.";
            case HornRefusal::Dead:         return "Overlord Wyrmthalak is dead. No one is left to muster.";
            case HornRefusal::AlreadyBlown: return "The war horn has already sounded.";
        }
        return "";
    }

    std::uint32_t constexpr kHornPollMs = 1000;         // the object's selectable flag follows the refusal
    std::uint32_t constexpr kHornLookMs = 5000;         // the burst's stalker lives this long

    // ----------------------------------------------------------------------------------------------------------------
    // Health (ruling 49; section 7 #22: x the flex ladder at the pull, applied through DungeonKit::Flex::SetHealth)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBossHealthAt5 = 400000;     // 900,000 at 10
    std::uint32_t constexpr kChampionHealthAt5 = 100000; // 225,000 at 10
    std::uint32_t constexpr kRiderHealthAt5 = 6000;      // 13,500 at 10

    // The base (5-player) health a held boss had before the hard mode raised it: his max health over the ladder of the
    // held count. Put back on an evade or a reset (DD keeps the base a script sets and restores that base on evade).
    inline std::uint32_t BaseBeforeHardMode(std::uint32_t maxHealth, std::uint32_t players)
    {
        double const ladder = DungeonKit::Flex::Ladder(players);
        return static_cast<std::uint32_t>(std::lround(double(maxHealth) / (ladder > 0. ? ladder : 1.)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WT4 in the hard mode: two tribes an order, all three champions at the first order (10 s), heroic's 25 s cadence
    // ----------------------------------------------------------------------------------------------------------------
    std::uint8_t constexpr kTribesPerOrder = 2;

    // ----------------------------------------------------------------------------------------------------------------
    // WT13 Tribal Ward: 20% less damage taken per champion alive (60% with all three)
    // ----------------------------------------------------------------------------------------------------------------
    std::int32_t constexpr kTribalWardPctPerChampion = -20;
    std::uint8_t constexpr kTribalWardMaxStacks = 3;

    constexpr std::uint8_t TribalWardStacks(std::uint32_t championsAlive)
    {
        return static_cast<std::uint8_t>(championsAlive > kTribalWardMaxStacks ? kTribalWardMaxStacks : championsAlive);
    }

    constexpr std::int32_t TribalWardTakenPct(std::uint32_t championsAlive)
    {
        return kTribalWardPctPerChampion * TribalWardStacks(championsAlive);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The unlocks: a champion's death unlocks one of his abilities for the rest of the fight
    // ----------------------------------------------------------------------------------------------------------------
    enum class Unlock : std::uint8_t
    {
        CausticVenom = 0,           // the Bloodaxe Champion died: WT14 Caustic Poison on his hits, Caustic Roar
        EmpoweredDragonfire = 1,    // the Smolderthorn Champion died: WT15 the 120 s burns and the Spear Chain
        ShadowflameSpit = 2,        // the Spirestone Champion died: WT16
    };
    std::size_t constexpr kUnlockCount = 3;
    inline constexpr std::array<Unlock, kUnlockCount> kUnlocks{ { Unlock::CausticVenom, Unlock::EmpoweredDragonfire,
        Unlock::ShadowflameSpit } };

    constexpr std::size_t Index(Unlock u) { return static_cast<std::size_t>(u); }

    constexpr Unlock UnlockOf(Tribe t)
    {
        switch (t)
        {
            case Tribe::Bloodaxe:       return Unlock::CausticVenom;
            case Tribe::Smolderthorn:   return Unlock::EmpoweredDragonfire;
            case Tribe::Spirestone:     return Unlock::ShadowflameSpit;
        }
        return Unlock::CausticVenom;
    }

    constexpr char const* UnlockName(Unlock u)
    {
        switch (u)
        {
            case Unlock::CausticVenom:          return "caustic-venom";
            case Unlock::EmpoweredDragonfire:   return "empowered-dragonfire";
            case Unlock::ShadowflameSpit:       return "shadowflame-spit";
        }
        return "?";
    }

    // The casts the unlocks add to his cast queue (B8's DungeonKit::CastQueue: ids from kHardModeCastBase; the breath
    // is priority 2 and goes first when two are due).
    enum WarHornCasts : std::uint32_t
    {
        CAST_CAUSTIC_ROAR       = BrsWyrmthalak::kHardModeCastBase + 1,
        CAST_SPEAR_CHAIN        = BrsWyrmthalak::kHardModeCastBase + 2,
        CAST_SHADOWFLAME_SPIT   = BrsWyrmthalak::kHardModeCastBase + 3,
    };

    struct CastRule
    {
        std::uint32_t id = 0;
        std::uint32_t firstMs = 0;      // after the unlock
        std::uint32_t everyMs = 0;      // from one cast's start to the next
        std::uint32_t holdMs = 0;       // how long it holds him (no melee, nothing else from the queue)
        std::uint8_t priority = 1;
    };

    // WT14 8 s after the unlock, every 20 s, a 2.5 s cast; WT15 10 s, every 30 s (the throw holds him 1 s); WT16 5 s,
    // every 15 s (the spit holds him 1 s).
    constexpr CastRule RuleOf(Unlock u)
    {
        switch (u)
        {
            case Unlock::CausticVenom:          return { CAST_CAUSTIC_ROAR, 8000, 20000, 2500, 1 };
            case Unlock::EmpoweredDragonfire:   return { CAST_SPEAR_CHAIN, 10000, 30000, 1000, 1 };
            case Unlock::ShadowflameSpit:       return { CAST_SHADOWFLAME_SPIT, 5000, 15000, 1000, 1 };
        }
        return {};
    }

    constexpr std::optional<Unlock> UnlockOfCast(std::uint32_t id)
    {
        for (Unlock u : kUnlocks)
            if (RuleOf(u).id == id)
                return u;
        return std::nullopt;
    }

    // The unlocks and their casts' due times, on the fight's clock (WyrmthalakFight::FightMs). B8's queue drops an
    // entry when it starts (StartHardModeCast: before OnCast, so a ScheduleCast from OnCast would also stay), and the
    // next one is pushed from the following OnUpdate: TakePushes hands over every cast whose due time changed since
    // the last call.
    class UnlockBook
    {
    public:
        struct Push
        {
            std::uint32_t id = 0;
            std::uint32_t inMs = 0;     // from `nowMs`
            std::uint8_t priority = 0;
        };

        // False when it was unlocked already.
        bool Open(Unlock u, std::uint64_t nowMs)
        {
            Slot& s = _slots[Index(u)];
            if (s.open)
                return false;
            s.open = true;
            s.dueMs = nowMs + RuleOf(u).firstMs;
            s.push = true;
            return true;
        }

        bool IsOpen(Unlock u) const { return _slots[Index(u)].open; }

        // The cast started at `nowMs`: the next one is due a cadence later.
        void Started(Unlock u, std::uint64_t nowMs)
        {
            Slot& s = _slots[Index(u)];
            s.dueMs = nowMs + RuleOf(u).everyMs;
            s.push = true;
        }

        // The cast could not start (no target, a refused cast): try again in a second.
        void Refused(Unlock u, std::uint64_t nowMs)
        {
            Slot& s = _slots[Index(u)];
            s.dueMs = nowMs + BrsWyrmthalak::kRetryMs;
            s.push = true;
        }

        std::optional<std::uint64_t> DueAt(Unlock u) const
        {
            Slot const& s = _slots[Index(u)];
            return s.open ? std::optional<std::uint64_t>(s.dueMs) : std::nullopt;
        }

        std::vector<Push> TakePushes(std::uint64_t nowMs)
        {
            std::vector<Push> out;
            for (Unlock u : kUnlocks)
            {
                Slot& s = _slots[Index(u)];
                if (!s.open || !s.push)
                    continue;
                s.push = false;
                CastRule const rule = RuleOf(u);
                out.push_back({ rule.id, s.dueMs > nowMs ? static_cast<std::uint32_t>(s.dueMs - nowMs) : 0u,
                    rule.priority });
            }
            return out;
        }

    private:
        struct Slot
        {
            bool open = false;
            bool push = false;
            std::uint64_t dueMs = 0;
        };

        std::array<Slot, kUnlockCount> _slots{};
    };

    // ----------------------------------------------------------------------------------------------------------------
    // WT10 Stolen Boulders (Urok's shard, UrokShards.h): one a boulder, 10 s still, 3 yd/s to the Spirestone Champion;
    // 5 Stolen Power stacks: the Overcharge (3 s cast, 40% to everyone), the stacks reset
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kShardWaitMs = 10000;
    std::uint32_t constexpr kStolenPowerCap = 5;
    float constexpr kOverchargePct = 40.f;
    float constexpr kOverchargeRangeYd = 100.f;         // the ledge, the ramp and the hall below

    constexpr bool OverchargesAt(std::uint32_t stacks) { return stacks >= kStolenPowerCap; }

    // ----------------------------------------------------------------------------------------------------------------
    // WT11 Chained Axes (as Voone's heroic) and the haul. G1 drill `blackrock-spire-followups` rows 5 and 6 (tag 6
    // gates the heroic sign-off, section 7 #26): the chain is 2 yd, its first crossing tick 2 s after it appears, then
    // every 2 s until 8 s (persist 6 s), 10% and Weakened; at 8 s the 1.5 s taut warning of the 3 yd haul, 35% and
    // Weakened, frozen at its registration (the drill's to=last) from the axe to the champion, no exclusion at his end
    // (as SP and the drill; designer question G1 #2).
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kAxeChainWidth = 2.f;
    std::uint32_t constexpr kAxeChainWarnMs = 2000;
    std::uint32_t constexpr kAxeChainLifeMs = 8000;     // from the axe's landing; the haul's warning starts then
    std::uint32_t constexpr kAxeChainTickMs = 2000;
    float constexpr kAxeChainPct = 10.f;
    float constexpr kHaulWidth = 3.f;
    std::uint32_t constexpr kHaulWarnMs = 1500;
    float constexpr kHaulPct = 35.f;
    float constexpr kHaulExcludeChampionEnd = 0.f;
    float constexpr kAxeAnchorLiftYd = 1.f;             // the anchor floats over the stuck axe (Voone's)
    std::uint32_t constexpr kAxeObjectLifeSec = 12;     // a safety: the script removes the axe at the haul

    // The drill's numbers (MechanicDrill.h "Blackrock Spire follow-ups" rows 5 and 6; kBrsFollowupMs 1500).
    std::uint32_t constexpr kDrillChainWarnMs = 2000;
    std::uint32_t constexpr kDrillChainPersistMs = 6000;
    std::uint32_t constexpr kDrillChainTickMs = 2000;
    std::uint32_t constexpr kDrillFollowupMs = 1500;
    static_assert(kAxeChainWarnMs == kDrillChainWarnMs && kAxeChainLifeMs - kAxeChainWarnMs == kDrillChainPersistMs
        && kAxeChainTickMs == kDrillChainTickMs, "the chains are the G1 drill's row 5");
    static_assert(kHaulWarnMs == kDrillFollowupMs, "the haul is the G1 drill's tag 6 follow-up (1.5 s)");

    // ----------------------------------------------------------------------------------------------------------------
    // WT12 riders that stay: cap 4 / 8 alive, each after a random player (switching every 8 s), Rabies on their melee
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr FlexAB kRiderCap{ 4, 8 };
    std::uint32_t constexpr kRiderRetargetMs = 8000;
    float constexpr kRiderChaseSpeed = 7.f;             // a player's run: kiting does not shake one
    float constexpr kRiderReach = 3.f;
    std::uint32_t constexpr kRiderCorpseMs = 10000;

    constexpr bool KeepRider(std::uint32_t keptAlive, std::uint32_t players)
    {
        return keptAlive < kRiderCap.At(players);
    }

    // Rabies (SP: Gizrul's HG6 heroic numbers): 1.5% of the reference row a stack every 3 s, 5 stacks, 30 s refreshed.
    std::uint32_t constexpr kRabiesHundredthsPerStack = 150;
    std::uint32_t constexpr kRabiesTickMs = 3000;
    std::uint32_t constexpr kRabiesMaxStacks = 5;
    std::uint32_t constexpr kRabiesMs = 30000;

    // ----------------------------------------------------------------------------------------------------------------
    // WT14 Caustic Venom: Caustic Poison on every hit of his abilities (Cleave, Black Dragonfire, Tail Swipe, the
    // spear's impact, the spit's circles; never a burn, patch or chain tick); Caustic Roar
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kPoisonHundredthsPerStack = 50;
    std::uint32_t constexpr kPoisonTickMs = 2000;
    std::uint32_t constexpr kPoisonMaxStacks = 10;
    std::uint32_t constexpr kPoisonMs = 20000;
    std::uint32_t constexpr kRoarCastMs = 2500;
    float constexpr kRoarPct = 20.f;
    std::uint32_t constexpr kRoarPoisonStacks = 2;
    std::uint8_t constexpr kRoarKickPriority = 3;
    static_assert(kRoarCastMs == RuleOf(Unlock::CausticVenom).holdMs, "the roar holds him its cast");

    // ----------------------------------------------------------------------------------------------------------------
    // WT15 Empowered Dragonfire and the Spear Chain
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kEmpoweredBurnLifeMs = 120000;
    std::uint32_t constexpr kBurnCap = 3;               // section 7 #28: the cap-3 fallback (no 35 yd open edge)
    float constexpr kSpearImpactPct = 10.f;
    float constexpr kSpearMissileSpeed = 30.f;          // SPELL_WH_SPEAR_THROW's Speed (yd/s)
    float constexpr kSpearChainWidth = 2.f;
    std::uint32_t constexpr kSpearChainMs = 20000;
    std::uint32_t constexpr kSpearChainWarnMs = 2000;   // the first crossing tick
    std::uint32_t constexpr kSpearChainTickMs = 2000;
    float constexpr kSpearChainPct = 10.f;

    // A breath's burn: B8's BurnSpec numbers (WyrmthalakFight.h), pure.
    struct BurnNumbers
    {
        float length = BrsWyrmthalak::kBurnLength;
        std::uint32_t lifeMs = BrsWyrmthalak::kBurnLifeMs;
        std::uint32_t graceMs = BrsWyrmthalak::kBurnGraceMs;
        std::uint32_t maxAlive = 0;
    };

    // Before the Smolderthorn Champion dies: heroic's burn (20 yd, 8 s). After: 120 s on the whole 25 yd cone, the
    // oldest going out when a fourth lands (the cap-3 fallback, section 7 #28).
    constexpr BurnNumbers HardModeBurn(BurnNumbers base, bool empowered)
    {
        if (!empowered)
            return base;
        base.length = BrsWyrmthalak::kBreathLength;
        base.lifeMs = kEmpoweredBurnLifeMs;
        base.maxAlive = kBurnCap;
        return base;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WT16 Shadowflame Spit: a 4 yd circle under every player, 2 s; 2 / 3 of them stay as 40 s patches
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kSpitRadius = 4.f;
    std::uint32_t constexpr kSpitWarnMs = 2000;
    float constexpr kSpitPct = 25.f;
    float constexpr kSpitMissileSpeed = 20.f;           // SPELL_WH_SPIT_MISSILE's Speed (yd/s)
    inline constexpr FlexAB kSpitPatches{ 2, 3 };
    std::uint32_t constexpr kPatchLifeMs = 40000;       // from the spit's landing
    std::uint32_t constexpr kPatchTickMs = 1000;        // its first tick a second after the landing
    float constexpr kPatchPct = 5.f;

    // At most this many patches at once: a spit every 15 s, each patch 40 s.
    constexpr std::uint32_t MaxPatchesAlive(std::uint32_t players)
    {
        std::uint32_t const every = RuleOf(Unlock::ShadowflameSpit).everyMs;
        std::uint32_t const spits = (kPatchLifeMs + every - 1) / every;
        return spits * kSpitPatches.At(players);
    }

    // `k` distinct indices of [0, n) picked with `rand(m)` in [0, m) (a partial Fisher-Yates), in pick order.
    template <class Rand>
    std::vector<std::uint32_t> PickIndices(std::uint32_t n, std::uint32_t k, Rand&& rand)
    {
        std::vector<std::uint32_t> pool(n);
        for (std::uint32_t i = 0; i < n; ++i)
            pool[i] = i;
        std::vector<std::uint32_t> out;
        for (std::uint32_t i = 0; i < n && out.size() < k; ++i)
        {
            std::uint32_t const j = i + static_cast<std::uint32_t>(rand(n - i));
            std::uint32_t const t = pool[i];
            pool[i] = pool[j];
            pool[j] = t;
            out.push_back(pool[i]);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Space (SP "Space math"; handoff section 3.8 NM 8: the ledge is 1,176 sq yd as one mesh piece)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kLedgeAreaSqYd = 1176.f;
    float constexpr kOpenEdgeChordYd = 28.2f;           // edge A
    float constexpr kEdgeWalkNeedsYd = 35.f;            // SP: 8 steps of 3-4 yd before the first burn goes out

    inline float ConeArea(float length, float angleDeg)
    {
        return length * length * angleDeg * DungeonKit::kPi / 360.f;
    }
}

#endif
