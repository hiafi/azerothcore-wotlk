/*
 * mod-dungeon-bosses, Blackrock Depths D1:
 * High Interrogator Gerstahn (9018), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/blackrock-depths-1-detention-block.md "High Interrogator Gerstahn" (S1 45-228, GE1-GE7, rulings 9-12
 * and 88), handoff section 3.4 rows D1, 3.5 row D1, 3.6, 3.8 (her hall). Tested by tests/brd_gerstahn_test.cpp.
 *
 *   Spells      the WP's ids, inside kSpellsGerstahn (210720-210749), declared in apps/dbc-tools
 *               source/npcs/blackrock_depths/gerstahn.py
 *   Tuning      NH<> percents and cadences, straight from the build spec (percents of the reference row)
 *   Doubt       GE1 the stack rule: a break at 5 (Broken + Dread, Doubt back to 0), the swirl at 4
 *   Knowledge   GE1 her stack per break: +10% damage each, capped at 5 on normal, uncapped on heroic
 *   Pain        GE2 which Shadow Word: Pain ticks add Doubt (every other tick on normal, every tick on heroic)
 *   Mind Flay   GE3 the player with the most Doubt, random on a tie (the tank included, ruling 88)
 *   Beats       the fight's clock: first delay and cadence per mechanic and difficulty
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_GERSTAHN_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_GERSTAHN_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdGerstahn
{
    using DungeonKit::NH;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsGerstahn;

    enum GerstahnSpells : std::uint32_t
    {
        SPELL_GE_DOUBT              = kSpellSlice.first + 0,    // 210720 GE1 the stacking debuff (no duration)
        SPELL_GE_DOUBT_SWIRL        = kSpellSlice.first + 1,    // 210721 GE1 the high-Doubt swirl at 4 stacks (gap 6)
        SPELL_GE_BROKEN             = kSpellSlice.first + 2,    // 210722 GE1 the 2 s fear of a break
        SPELL_GE_DREAD              = kSpellSlice.first + 3,    // 210723 GE1 the Shadow DoT of a break
        SPELL_GE_KNOWLEDGE          = kSpellSlice.first + 4,    // 210724 GE1 her stack per break (+10% damage)
        SPELL_GE_SHADOW_WORD_PAIN   = kSpellSlice.first + 5,    // 210725 GE2 the copy of 14032 (Magic DoT)
        SPELL_GE_MIND_FLAY          = kSpellSlice.first + 6,    // 210726 GE3 the interruptible 3 s channel
        SPELL_GE_CIRCLE_CAST        = kSpellSlice.first + 7,    // 210727 GE4 the 2.5 s cast bar (Arcane)
        SPELL_GE_CIRCLE             = kSpellSlice.first + 8,    // 210728 GE4 the ring's hit (resolve copy, Shadow)
        SPELL_GE_MIND_SEAR          = kSpellSlice.first + 9,    // 210729 GE5 the 5 s sear on its target (the look)
        SPELL_GE_MIND_SEAR_TICK     = kSpellSlice.first + 10,   // 210730 GE5 a tick on each other player in 8 yd
        SPELL_GE_SHADOW_SHIELD      = kSpellSlice.first + 11,   // 210731 GE7 the copy of 12040, normal absorb
        SPELL_GE_SHADOW_SHIELD_H    = kSpellSlice.first + 12,   // 210732 GE7 the same, heroic absorb
        SPELL_GE_LINGERING_DOUBT    = kSpellSlice.first + 13,   // 210733 GE6 the pool's look on a stalker (heroic)
        // 210734-210749 spare
    };
    static_assert(SPELL_GE_LINGERING_DOUBT <= kSpellSlice.last, "Gerstahn's spells must stay in her slice");

    // Stock spells of 9018 retired from the kit (S1 "Stock kit", ruling 10): never cast by the rework. Shadow Word:
    // Pain 14032 has a SpellDifficulty row (14032 -> 15654) and Shadow Shield 12040 is rescaled, so both are copies in
    // the slice (rule 15).
    inline constexpr std::uint32_t SPELL_STOCK_SHADOW_WORD_PAIN = 14032;
    inline constexpr std::uint32_t SPELL_STOCK_MANA_BURN = 14033;
    inline constexpr std::uint32_t SPELL_STOCK_PSYCHIC_SCREAM = 13704;
    inline constexpr std::uint32_t SPELL_STOCK_SHADOW_SHIELD = 12040;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum GerstahnTags : std::uint32_t
    {
        TAG_GE_CIRCLE       = 4,    // GE4 the Interrogation Circle
        TAG_GE_MIND_SEAR    = 5,    // GE5 the bots' run-out from the sear target (telegraph; the script ticks)
        TAG_GE_LINGERING    = 6,    // GE6 a Lingering Doubt pool (heroic; telegraph; the script adds Doubt)
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_gerstahn_blackrock_depths.sql, S1 "Text").
    enum GerstahnTexts : std::uint8_t
    {
        SAY_PULL        = 0,    // yell: "More visitors for my cells? Everyone talks eventually."
        SAY_BREAK       = 1,    // yell: "There it is. I knew you would break." (a break, Knowledge gained)
        EMOTE_CIRCLE    = 2,    // emote: "%s begins to interrogate everyone around her!"
        EMOTE_MIND_SEAR = 3,    // emote: "%s sears the mind of $n!"
        SAY_DEATH       = 4,    // yell: "The Hammer... will learn... what I could not..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S1 "Build spec"; percents of the reference row: N level 52, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // GE1 Doubt: no duration, not dispellable; only a clear (a kicked Mind Flay, a dispelled Shadow Word: Pain) or a
    // break removes it. At 5 the player breaks; at 4 the swirl shows.
    inline constexpr std::uint32_t kDoubtBreakAt = 5;
    inline constexpr std::uint32_t kDoubtSwirlAt = 4;

    // GE1 Broken: a 2 s fear (the shared doc's limit for a penalty) and Dread, 30% (heroic 40%) of the row over 10 s.
    inline constexpr std::uint32_t kBrokenMs = 2000;
    inline constexpr std::uint32_t kDreadMs = 10000;
    inline constexpr std::uint32_t kDreadTickMs = 2000;
    inline constexpr std::uint32_t kDreadTicks = kDreadMs / kDreadTickMs;
    inline constexpr NH<float> kDreadTotalPct{ 30.f, 40.f };
    inline constexpr NH<float> kDreadTickPct{ 6.f, 8.f };
    static_assert(kDreadTicks == 5, "Dread ticks every 2 s for 10 s");

    // GE1 Knowledge: +10% damage done a stack; 5 at most on normal (a capped group failure below level 60), no cap on
    // heroic (the soft enrage). The aura's own counter (255) is the heroic limit.
    inline constexpr float kKnowledgePctPerStack = 10.f;
    inline constexpr NH<std::uint32_t> kKnowledgeCap{ 5, 0 };      // 0 = no cap
    inline constexpr std::uint32_t kKnowledgeAuraCap = 255;
    // The yell of a break at most this often (a Circle can break three players at once).
    inline constexpr std::uint32_t kBreakYellGapMs = 5000;

    // GE2 Shadow Word: Pain: random player, the tank included; 18 s, a tick every 3 s; Magic.
    inline constexpr std::uint32_t kPainMs = 18000;
    inline constexpr std::uint32_t kPainTickMs = 3000;
    inline constexpr std::uint32_t kPainTicks = kPainMs / kPainTickMs;
    inline constexpr NH<float> kPainPct{ 2.f, 3.f };

    // GE3 Mind Flay: the player with the most Doubt, the tank included; a 3 s channel, 3 ticks of 6% (heroic 8%) and
    // 1 Doubt each. Interruptible (a kick or a silence); the interrupt clears all of the target's Doubt.
    inline constexpr std::uint32_t kFlayMs = 3000;
    inline constexpr std::uint32_t kFlayTickMs = 1000;
    inline constexpr std::uint32_t kFlayTicks = kFlayMs / kFlayTickMs;
    inline constexpr NH<float> kFlayPct{ 6.f, 8.f };
    inline constexpr std::uint32_t kFlayDoubtPerTick = 1;
    // The channel has not taken yet this long after the cast (UpdateFlay waits before calling it done).
    inline constexpr std::uint32_t kFlayStartGraceMs = 250;

    // GE4 Interrogation Circle: a 2.5 s cast bar, a 10 yd ring around her; inside when it lands: 15% (heroic 25%)
    // Shadow and 3 Doubt, the tank included (ruling 88). Doubt replaces Weakened (ruling 11).
    inline constexpr float kCircleRadius = 10.f;
    inline constexpr std::uint32_t kCircleCastMs = 2500;
    inline constexpr NH<float> kCirclePct{ 15.f, 25.f };
    inline constexpr std::uint32_t kCircleDoubt = 3;

    // GE5 Mind Sear: 5 s on a random non-tank who is not the Mind Flay target; every second everyone else within 8 yd
    // of the target takes 3% (heroic 5%) Shadow and 1 Doubt. The target takes neither.
    inline constexpr float kSearRadius = 8.f;
    inline constexpr float kSearZBand = 5.f;
    inline constexpr std::uint32_t kSearMs = 5000;
    inline constexpr std::uint32_t kSearTickMs = 1000;
    inline constexpr std::uint32_t kSearTicks = kSearMs / kSearTickMs;
    inline constexpr NH<float> kSearPct{ 3.f, 5.f };
    inline constexpr std::uint32_t kSearDoubtPerTick = 1;

    // GE6 Lingering Doubt (heroic): a dispelled Shadow Word: Pain leaves a 5 yd pool where its player stood, 8 s;
    // each second inside adds 1 Doubt. No damage. The first second is the warning (the pool's player steps off).
    inline constexpr float kPoolRadius = 5.f;
    inline constexpr std::uint32_t kPoolMs = 8000;
    inline constexpr std::uint32_t kPoolWarnMs = 1000;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr std::uint32_t kPoolDoubtPerTick = 1;
    // Space math (S1 "Heroic", gap 7, NAVMESH 1.1): with a dispel about every 6 s, 2 or 3 pools are down at once:
    // 3 pools of 5 yd are 236 sq yd, a quarter of the 934 sq yd of floor within 20 yd of her spawn.
    inline constexpr float kHallFloorWithin20Yd = 934.f;
    inline constexpr std::uint32_t kPoolsAtOnce = 3;
    constexpr float PoolArea(std::uint32_t pools)
    {
        return static_cast<float>(pools) * DungeonKit::kPi * kPoolRadius * kPoolRadius;
    }
    static_assert(PoolArea(kPoolsAtOnce) <= 240.f, "three pools fit the spec's 160-240 sq yd");
    static_assert(PoolArea(kPoolsAtOnce) <= 0.3f * kHallFloorWithin20Yd, "the pools leave most of her hall free");

    // GE7 Shadow Shield (the stock 12040 rescaled): 30 s, absorbs about 4,000 (heroic 6,500) of every school, a small
    // Shadow hit on melee attackers (unset in the spec, gap 36: 50 / 60, about 1.5% of the row). Magic: a purge is a
    // reward.
    inline constexpr std::uint32_t kShieldMs = 30000;
    inline constexpr NH<std::uint32_t> kShieldAbsorb{ 4000, 6500 };
    inline constexpr NH<std::uint32_t> kShieldReflect{ 50, 60 };

    constexpr std::uint32_t ShieldSpell(bool heroic)
    {
        return heroic ? SPELL_GE_SHADOW_SHIELD_H : SPELL_GE_SHADOW_SHIELD;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE1 Doubt and Knowledge
    // ----------------------------------------------------------------------------------------------------------------

    struct DoubtStep
    {
        std::uint32_t stacks = 0;   // the count after the step (0 after a break)
        bool broke = false;         // the step reached kDoubtBreakAt: Broken, Dread, Knowledge
    };

    // `add` Doubt on a player at `current`: at 5 or more the player breaks and Doubt goes back to 0 (the excess is
    // lost: a break is the whole penalty).
    constexpr DoubtStep AddDoubt(std::uint32_t current, std::uint32_t add)
    {
        std::uint32_t const total = current + add;
        if (total >= kDoubtBreakAt)
            return { 0, true };
        return { total, false };
    }

    // The swirl shows at 4 (and only below a break).
    constexpr bool SwirlOn(std::uint32_t stacks)
    {
        return stacks >= kDoubtSwirlAt && stacks < kDoubtBreakAt;
    }

    // The stack limit of her Knowledge: 5 on normal; the aura's counter on heroic (no cap).
    constexpr std::uint32_t KnowledgeStackLimit(bool heroic)
    {
        return kKnowledgeCap(heroic) ? kKnowledgeCap(heroic) : kKnowledgeAuraCap;
    }

    // Her Knowledge after a break: one more, up to the limit.
    constexpr std::uint32_t KnowledgeAfterBreak(std::uint32_t stacks, bool heroic)
    {
        return std::min(stacks + 1, KnowledgeStackLimit(heroic));
    }

    // Her damage multiplier at `stacks` Knowledge. The aura (+10% damage done, every school) raises her melee; her own
    // spells ignore caster modifiers (rule 2), so the scripts and the registry calls multiply their percents by this.
    constexpr float KnowledgeScale(std::uint32_t stacks)
    {
        return 1.f + kKnowledgePctPerStack / 100.f * static_cast<float>(stacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE2 Shadow Word: Pain
    // ----------------------------------------------------------------------------------------------------------------

    // Tick `tick` (1-based, AuraEffect::GetTickNumber) adds a Doubt: every 6 s on normal (ticks 2, 4, 6: 3 a cast),
    // every 3 s on heroic (6 a cast: a missed dispel breaks the player).
    constexpr bool PainTickAddsDoubt(std::uint32_t tick, bool heroic)
    {
        if (tick == 0 || tick > kPainTicks)
            return false;
        return heroic || tick % 2 == 0;
    }

    constexpr std::uint32_t PainDoubtPerCast(bool heroic)
    {
        std::uint32_t n = 0;
        for (std::uint32_t tick = 1; tick <= kPainTicks; ++tick)
            if (PainTickAddsDoubt(tick, heroic))
                ++n;
        return n;
    }
    static_assert(PainDoubtPerCast(false) == 3, "normal: 1 Doubt every 6 s, 3 a cast");
    static_assert(PainDoubtPerCast(true) == 6, "heroic: 1 Doubt every 3 s, 6 a cast");
    static_assert(PainDoubtPerCast(true) >= kDoubtBreakAt, "heroic: a missed dispel breaks the player");

    // ----------------------------------------------------------------------------------------------------------------
    // Percent spells: the base percent of each of her own damage spells (before Knowledge)
    // ----------------------------------------------------------------------------------------------------------------

    // The per-hit (or per-tick) percent of the reference row of `spellId`; 0 for a spell that deals none.
    constexpr float BasePct(std::uint32_t spellId, bool heroic)
    {
        switch (spellId)
        {
            case SPELL_GE_SHADOW_WORD_PAIN: return kPainPct(heroic);
            case SPELL_GE_MIND_FLAY:        return kFlayPct(heroic);
            case SPELL_GE_DREAD:            return kDreadTickPct(heroic);
            case SPELL_GE_MIND_SEAR_TICK:   return kSearPct(heroic);
            case SPELL_GE_CIRCLE:           return kCirclePct(heroic);
            default:                        return 0.f;
        }
    }

    // The percent with her Knowledge on top.
    constexpr float ScaledPct(std::uint32_t spellId, bool heroic, std::uint32_t knowledge)
    {
        return BasePct(spellId, heroic) * KnowledgeScale(knowledge);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE3 Mind Flay's target
    // ----------------------------------------------------------------------------------------------------------------

    struct FlayCandidate
    {
        std::uint64_t id = 0;
        std::uint32_t doubt = 0;
    };

    // The index of the candidate with the most Doubt; a tie goes to `rand(n)` among the tied ([0, n)). nullopt when
    // there is nobody.
    template <class Rand>
    std::optional<std::size_t> PickFlayTarget(std::vector<FlayCandidate> const& candidates, Rand&& rand)
    {
        if (candidates.empty())
            return std::nullopt;
        std::uint32_t most = 0;
        for (FlayCandidate const& c : candidates)
            most = std::max(most, c.doubt);
        std::vector<std::size_t> tied;
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].doubt == most)
                tied.push_back(i);
        std::size_t const n = tied.size();
        std::size_t const r = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(n)));
        return tied[std::min(r, n - 1)];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE5 Mind Sear's reach
    // ----------------------------------------------------------------------------------------------------------------

    // Another player `dist2d` yd from the sear target on the plane, `dz` yd above or below it, takes the tick.
    constexpr bool InSear(float dist2d, float dz)
    {
        return dist2d <= kSearRadius && (dz < 0.f ? -dz : dz) <= kSearZBand;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (S1 "Build spec" first / cooldown, normal / heroic)
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    inline constexpr NH<Beat> kPainBeat{ { 4000, 8000 }, { 4000, 6000 } };        // GE2
    inline constexpr NH<Beat> kFlayBeat{ { 8000, 12000 }, { 8000, 10000 } };      // GE3
    inline constexpr NH<Beat> kCircleBeat{ { 15000, 25000 }, { 15000, 20000 } };  // GE4
    inline constexpr NH<Beat> kSearBeat{ { 20000, 20000 }, { 20000, 15000 } };    // GE5 (never during a GE4 cast)
    inline constexpr NH<Beat> kShieldBeat{ { 8000, 25000 }, { 8000, 25000 } };    // GE7

    // A repeating beat on the AI's own ms clock (start to start); a beat that cannot fire yet stays due.
    class BeatClock
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t inMs)
        {
            _on = true;
            _dueMs = nowMs + inMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time, never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
