/*
 * mod-dungeon-bosses, Blackrock Spire B10:
 * Pyroguard Emberseer (9816), the pure, host-testable part (no engine headers). Build spec: docs/dungeons/
 * blackrock-spire-rework.md "Pyroguard Emberseer" (SP 2523-2790, EM1-EM10, rulings 50-54), handoff section 3.4 rows EM,
 * 3.5 row B10, 3.6, 3.8 (his hall), section 10 "Rolling front rulings (2026-11-15)". Tested by
 * tests/brs_emberseer_test.cpp (rules, schedule, the growth math) and tests/brs_emberseer_bots_test.cpp (the bots'
 * ring and nova hits in BM's brain model).
 *
 *   Spells     the WP's ids, inside kSpellsEmberseer (210350-210389), declared in apps/dbc-tools
 *              source/npcs/blackrock_spire/emberseer.py
 *   Tuning     NH<> percents, FlexAB counts and the cadences, straight from the build spec
 *   Growth     EM1 / EM4 / EM5: the cage's and the fight's stack clocks, what a stack changes (damage, the nova, the
 *              rings, Furnace Heat), Full Strength
 *   Pulse      EM2 / EM3: one Furnace Pulse as a kit ring sequence (DungeonKitFrontLogic.h) with the user's rulings:
 *              ring 1's slice shown 5 s ahead, the nova on its own 2.5 s warning, rings 2-4 from the apex
 *   Posts      EM6 / EM8: which pulse flares, when the posts flare and fire, the next pulse's wait, the picks
 *   FightModel the whole timeline on a 100 ms clock (growth, pulses, posts, Pyroblast) for the SP growth math
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_EMBERSEER_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_EMBERSEER_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitFrontLogic.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace BrsEmberseer
{
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    namespace Fronts = DungeonKit::Fronts;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsEmberseer;

    enum EmberseerSpells : std::uint32_t
    {
        SPELL_EM_GROWTH_DAMAGE      = kSpellSlice.first + 0,    // 210350 EM4 +3% damage done a stack (normal)
        SPELL_EM_GROWTH_DAMAGE_H    = kSpellSlice.first + 1,    // 210351 EM4 +4% damage done a stack (heroic)
        SPELL_EM_FURNACE_HEAT       = kSpellSlice.first + 2,    // 210352 EM4 every 3 s: 0.5% + 0.1% a stack, Fire
        SPELL_EM_NOVA               = kSpellSlice.first + 3,    // 210353 EM2 the nova's hit (resolve copy, Fire)
        SPELL_EM_RING               = kSpellSlice.first + 4,    // 210354 EM3 a ring's hit (resolve copy, Fire)
        SPELL_EM_BODY_FLARE         = kSpellSlice.first + 5,    // 210355 EM2 his body flares (look)
        SPELL_EM_RING_LAUNCH        = kSpellSlice.first + 6,    // 210356 EM3 Flame Wave at the apex (look)
        SPELL_EM_FIRE_NOVA_BURST    = kSpellSlice.first + 7,    // 210357 EM2 / EM8 the Fire Nova burst (look)
        SPELL_EM_FULL_STRENGTH      = kSpellSlice.first + 8,    // 210358 EM5 Full Strength on him (look)
        SPELL_EM_SUPERNOVA          = kSpellSlice.first + 9,    // 210359 EM5 Supernova's hit (resolve copy, Fire)
        SPELL_EM_PYROBLAST          = kSpellSlice.first + 10,   // 210360 EM9 the 6 s Pyroblast (interruptible)
        SPELL_EM_SMOLDER            = kSpellSlice.first + 11,   // 210361 EM6 a picked post smolders (post state)
        SPELL_EM_FLARE_COLUMN       = kSpellSlice.first + 12,   // 210362 EM6 the flare's column (post look)
        SPELL_EM_ENCAGE_BEAM        = kSpellSlice.first + 13,   // 210363 EM6 a held post's 2 s beam onto him
        SPELL_EM_SEARING_BOND       = kSpellSlice.first + 14,   // 210364 EM7 heroic: 4% a second on a flared post
        SPELL_EM_SEARED             = kSpellSlice.first + 15,   // 210365 EM7 heroic: 40 s, cannot fire a post
        SPELL_EM_UNSTABLE_POST      = kSpellSlice.first + 16,   // 210366 EM8 heroic: an erupting post's hit
        SPELL_EM_SEARING_STATE      = kSpellSlice.first + 17,   // 210367 EM7 heroic: the holder's flame (look)
        // 210368-210389 spare
    };
    static_assert(SPELL_EM_SEARING_STATE <= kSpellSlice.last, "Emberseer's spells must stay in his slice");

    // Stock spells kept for the cage and the growth (SP "Reused visuals": the growth is the stock 16049 aura, its +5%
    // size a stack; the cage prelude keeps the Incarcerators' channel and his encaged state).
    inline constexpr std::uint32_t SPELL_EMBERSEER_GROWING = 16049;     // +5% size a stack (CumulativeAura 50)
    inline constexpr std::uint32_t SPELL_ENCAGED_EMBERSEER = 15282;     // his caged state (self, lasting)
    inline constexpr std::uint32_t SPELL_FREEZE_ANIM = 16245;           // the stock cage pose
    inline constexpr std::uint32_t SPELL_ENCAGE_CHANNEL = 15281;        // the Incarcerators' channel onto him
    inline constexpr std::uint32_t SPELL_INCARCERATOR_STRIKE = 15580;   // their Strike (kept)

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum EmberseerTags : std::uint32_t
    {
        TAG_NOVA        = 2,    // EM2
        TAG_RING        = 3,    // EM3 (the G8 bar's front tag)
        TAG_SUPERNOVA   = 5,    // EM5
        TAG_POST        = 6,    // EM6 (the Soaks; OneClaimPerBot groups by tag)
        TAG_UNSTABLE    = 8,    // EM8 (the G8 bar's tag 8)
    };

    // creature_text groups of 9816 (lines 0-3 stock, moved; 4-7 the core SQL rev
    // rev_pyroguard_emberseer_blackrock_spire.sql). The Incarcerators' stock line 0 (the flee) is retired.
    enum EmberseerTexts : std::uint8_t
    {
        TEXT_REGAIN_STRENGTH    = 0,    // emote (stock): at 7 stacks (two rings, three heroic)
        TEXT_NEARLY_FULL        = 1,    // emote (stock): at 14 stacks
        TEXT_BREAKS_FREE        = 2,    // emote (stock): the last Incarcerator died (EM1)
        TEXT_THANK_YOU          = 3,    // yell (stock): 2 s later, as he engages
        TEXT_POSTS_SMOLDER      = 4,    // boss emote: "The binding posts begin to smolder!" (EM6)
        TEXT_DRAWS_FLAMES       = 5,    // emote: "%s draws the flames into itself!" (EM9 landed)
        TEXT_FULL_STRENGTH      = 6,    // boss emote: "%s burns at full strength!" (EM5)
        TEXT_UNSTABLE_POSTS     = 7,    // boss emote: "Unstable posts crackle with fire!" (EM8, heroic)
    };

    // The cage protocol (stock boss_pyroguard_emberseer.cpp: the instance's altar event 4884 calls SetData(1, 1)).
    inline constexpr std::uint32_t DATA_ALTAR = 1;
    inline constexpr std::uint32_t DATA_ALTAR_USED = 1;
    inline constexpr std::uint32_t INCARCERATOR_DATA = 1;           // the Incarcerators' SetData(1, x): x below
    inline constexpr std::uint32_t INCARCERATOR_ENGAGE = 1;         // the cage opens: attackable, zone in combat
    inline constexpr std::uint32_t INCARCERATOR_CHANNEL = 2;        // back on their posts: channel onto him
    inline constexpr std::int32_t ACTION_INCARCERATOR_DIED = 1;     // an Incarcerator tells him (DoAction)
    // Stock searched 35 yd; the hall's corners are 42 yd from him, so Incarcerators tanked there went uncounted (the
    // cage poll freed him early, a recage missed them: R-2 m-1). The seven sit 17-26 yd out; none other on the map.
    inline constexpr float kIncarceratorFindYd = 60.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP "Build spec"; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // EM1 the cage: a stack every 5 s while the Incarcerators fight, capped at 8; he breaks free when the last one
    // dies, keeping his stacks. The yell and the engage follow the emote by 2 s; the re-cage after a wipe 5 s (stock).
    inline constexpr std::uint32_t kCageGrowMs = 5000;
    inline constexpr std::uint32_t kCageMaxStacks = 8;
    inline constexpr std::uint32_t kBreakFreeEngageMs = 2000;
    inline constexpr std::uint32_t kRecageMs = 5000;
    inline constexpr std::uint32_t kCageWipeMs = 3000;              // no living Incarcerator engaged this long: wipe
    inline constexpr std::uint32_t kCagePollMs = 500;

    // EM4 The Furnace Grows: a stack every 6 s (heroic 4 s) after he breaks free, to Full Strength at 20; each stack
    // +3% (heroic +4%) on everything he does, +0.3 yd on the nova, more Furnace Heat.
    inline constexpr NH<std::uint32_t> kGrowEveryMs{ 6000, 4000 };
    inline constexpr std::uint32_t kFullStrengthStacks = 20;
    inline constexpr NH<float> kStackDamagePct{ 3.f, 4.f };
    inline constexpr std::uint32_t kHeatEveryMs = 3000;
    inline constexpr float kHeatBasePct = 0.5f;
    inline constexpr float kHeatPerStackPct = 0.1f;
    inline constexpr std::uint32_t kStrengthLine0Stacks = 7;        // line 0, a second ring (a third heroic)
    inline constexpr std::uint32_t kStrengthLine1Stacks = 14;       // line 1, a third ring (a fourth heroic)

    // EM5 Full Strength: Supernova every 6 s at 20 stacks, 50% to everyone, unavoidable (a registry hit, no Weakened).
    inline constexpr std::uint32_t kSupernovaEveryMs = 6000;
    inline constexpr NH<float> kSupernovaPct{ 50.f, 50.f };

    // EM2 the nova: 7 yd + 0.3 yd a stack (7 yd covers the dais, 13 yd at 20), 2.5 s warning, 30% + Weakened, the tank
    // too (ruling 51). EM3 the rings: 30% + Weakened.
    inline constexpr float kNovaBaseYd = 7.f;
    inline constexpr float kNovaPerStackYd = 0.3f;
    inline constexpr std::uint32_t kNovaWarnMs = 2500;
    inline constexpr NH<float> kNovaPct{ 30.f, 30.f };
    inline constexpr NH<float> kRingPct{ 30.f, 30.f };

    // EM2 / EM3 Furnace Pulse: every 15 s (heroic 12 s), the first erupting 8 s after he engages. User ruling (rolling
    // fronts 1, 2026-11-15): ring 1's slice is shown 5 s ahead (the pulse starts then: the apex and the nova's radius
    // are fixed at the pulse's start), the nova keeps its 2.5 s warning and erupts as ring 1 launches.
    inline constexpr NH<std::uint32_t> kPulseEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kFirstEruptionMs = 8000;
    inline constexpr std::uint32_t kRingWarnMs = 5000;
    inline constexpr std::uint32_t kFirstPulseStartMs = kFirstEruptionMs - kRingWarnMs;     // 3 s after the engage
    inline constexpr NH<float> kSliceDeg{ 60.f, 45.f };             // a 300 degree front (heroic 315)
    inline constexpr NH<float> kTurnDeg{ 45.f, 60.f };              // each later ring turned clockwise
    inline constexpr NH<std::uint32_t> kRingSpacingMs{ 2000, 1500 };
    inline constexpr float kRingBandYd = 4.f;
    inline constexpr float kRingSpeed = 8.f;                        // yd/s: about 4 s to the walls
    inline constexpr float kRingEndYd = 45.f;                       // every wall and corner (41.3 to 42.4 yd)
    inline constexpr float kSafeExtraYd = 12.f;                     // FrontSafe: the slice parks until nova + 12 yd

    // EM6 Binding Posts: every second pulse (every 30 s, heroic 24 s); picked at that pulse's nova warning (the
    // smolder, line 4), they flare once its last ring has passed 21 yd, for 8 s; each held post then fires: -2 stacks
    // (-1 at 6 or more players: the push back is the same at any size) and the Encage beam on him for 2 s. The next
    // pulse waits until its first ring cannot reach 15 yd before the posts fire.
    inline constexpr FlexAB kBindingPosts{ 2, 4 };
    inline constexpr FlexAB kPostStackLoss{ 2, 1 };
    inline constexpr float kPostSoakYd = 3.f;
    inline constexpr std::uint32_t kPostWindowMs = 8000;
    inline constexpr float kPostFlareAfterYd = 21.f;
    inline constexpr float kPostReachGuardYd = 15.f;
    inline constexpr std::uint32_t kPostBeamMs = 2000;
    inline constexpr std::uint32_t kPostColumnRecastMs = 5000;      // the column is a 6 s one-shot: re-cast at 5 s

    // EM7 Searing Bond (heroic): 4% a second on a flared post; its firing leaves the holders Seared 40 s (no post).
    inline constexpr float kSearingBondPct = 4.f;
    inline constexpr std::uint32_t kSearingTickMs = 1000;
    inline constexpr std::uint32_t kSearedMs = 40000;

    // EM8 Unstable Posts (heroic): at each flare 2 other posts (3 at 6 or more) erupt as the binding posts fire: 6 yd,
    // 8 s warning from the flare, 30% + Weakened.
    inline constexpr FlexAB kUnstablePosts{ 2, 3 };
    inline constexpr float kUnstableYd = 6.f;
    inline constexpr NH<float> kUnstablePct{ 30.f, 30.f };

    // EM9 Pyroblast: every 20 s (first at 12 s) the stock 6 s cast at a random non-tank, interruptible (a reward on
    // normal, expected on heroic); landed 40% (heroic 50%) plus the stock burn, and +1 (heroic +2) stacks (line 5).
    inline constexpr std::uint32_t kPyroblastFirstMs = 12000;
    inline constexpr std::uint32_t kPyroblastEveryMs = 20000;
    inline constexpr std::uint32_t kPyroblastCastMs = 6000;
    inline constexpr NH<float> kPyroblastPct{ 40.f, 50.f };
    inline constexpr float kPyroblastBurnPct = 1.5f;                // a tick every 3 s for 12 s (the stock burn)
    inline constexpr std::uint32_t kPyroblastBurnMs = 12000;
    inline constexpr NH<std::uint32_t> kPyroblastFeeds{ 1, 2 };
    inline constexpr NH<std::uint8_t> kPyroblastKickPriority{ 2, 3 };

    // His hall between the door lines (handoff section 3.8: x 114.8..174.2, y -288.2..-229.2, floor z 91.2..93.0, the
    // dais top 95.7..96.0): where bots may plan to stand. No lethal wall, so no 2 yd margin; 0.5 yd off the walls.
    inline constexpr float kHallMinX = 115.3f;
    inline constexpr float kHallMaxX = 173.7f;
    inline constexpr float kHallMinY = -287.7f;
    inline constexpr float kHallMaxY = -229.7f;
    inline constexpr float kHallMinZ = 89.f;
    inline constexpr float kHallMaxZ = 98.5f;
    inline constexpr float kPostZ = 91.65f;                         // [db] the Incarcerators' spawns: z 91.62..91.70

    // ----------------------------------------------------------------------------------------------------------------
    // Growth (EM1, EM4, EM5)
    // ----------------------------------------------------------------------------------------------------------------

    // Every hit he deals is raised by his stacks (EM4): x (1 + 3% a stack), heroic 4%.
    inline float DamageMult(std::uint32_t stacks, bool heroic)
    {
        return 1.f + kStackDamagePct(heroic) / 100.f * static_cast<float>(std::min(stacks, kFullStrengthStacks));
    }

    inline float NovaRadius(std::uint32_t stacks)
    {
        return kNovaBaseYd + kNovaPerStackYd * static_cast<float>(std::min(stacks, kFullStrengthStacks));
    }

    // Rings a pulse: normal 1 / 2 / 3 at 0-6 / 7-13 / 14+ stacks; heroic 2 / 3 / 4.
    inline std::uint32_t RingsFor(std::uint32_t stacks, bool heroic)
    {
        std::uint32_t const tier = stacks >= kStrengthLine1Stacks ? 2u : stacks >= kStrengthLine0Stacks ? 1u : 0u;
        return (heroic ? 2u : 1u) + tier;
    }

    // Furnace Heat every 3 s: 0.5% plus 0.1% a stack (its own stack rule: not raised again by DamageMult).
    inline float HeatPct(std::uint32_t stacks)
    {
        return kHeatBasePct + kHeatPerStackPct * static_cast<float>(std::min(stacks, kFullStrengthStacks));
    }

    // The percent of the reference row a hit of `spellId` deals at `stacks` (the spell script of his scripted hits and
    // the registry calls share it). 0 for a spell that is not one of his stack-raised hits.
    inline float HitPct(std::uint32_t spellId, std::uint32_t stacks, bool heroic)
    {
        switch (spellId)
        {
            case SPELL_EM_FURNACE_HEAT: return HeatPct(stacks);
            case SPELL_EM_PYROBLAST:    return kPyroblastPct(heroic) * DamageMult(stacks, heroic);
            case SPELL_EM_SUPERNOVA:    return kSupernovaPct(heroic) * DamageMult(stacks, heroic);
            case SPELL_EM_NOVA:         return kNovaPct(heroic) * DamageMult(stacks, heroic);
            case SPELL_EM_RING:         return kRingPct(heroic) * DamageMult(stacks, heroic);
            default:                    return 0.f;
        }
    }

    // The emote a stack count crossing upward says (line 0 at 7, line 1 at 14), if any.
    inline std::optional<std::uint8_t> StrengthLine(std::uint32_t before, std::uint32_t after)
    {
        if (before < kStrengthLine1Stacks && after >= kStrengthLine1Stacks)
            return TEXT_NEARLY_FULL;
        if (before < kStrengthLine0Stacks && after >= kStrengthLine0Stacks)
            return TEXT_REGAIN_STRENGTH;
        return std::nullopt;
    }

    inline std::uint32_t ClampStacks(std::int64_t stacks)
    {
        return static_cast<std::uint32_t>(std::clamp<std::int64_t>(stacks, 0, kFullStrengthStacks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Pulse (EM2, EM3)
    // ----------------------------------------------------------------------------------------------------------------

    // One pulse's ring sequence as the kit plans it (DungeonKit::RingSequence::plan), with the user's rulings: ring 1
    // registered 5 s ahead from the nova's edge, rings 2-4 from the apex (startYd 0), each shown as the ring before it
    // launches.
    inline Fronts::RingSequenceSpec PulseSpec(std::uint32_t stacks, bool heroic, float firstSlice)
    {
        Fronts::RingSequenceSpec s;
        s.rings = RingsFor(stacks, heroic);
        s.firstSlice = firstSlice;
        s.turnDeg = kTurnDeg(heroic);
        s.sliceDeg = kSliceDeg(heroic);
        s.startYd = NovaRadius(stacks);
        s.laterStartYd = 0.f;
        s.endYd = kRingEndYd;
        s.bandYd = kRingBandYd;
        s.speed = kRingSpeed;
        s.firstWarnMs = kRingWarnMs;
        s.spacingMs = kRingSpacingMs(heroic);
        s.revealAtPreviousLaunch = true;
        return s;
    }

    // ms from the pulse's start: the nova registers (2.5 s warning) and erupts as ring 1 launches.
    inline constexpr std::uint32_t kNovaCueMs = kRingWarnMs - kNovaWarnMs;
    inline constexpr std::uint32_t kEruptionMs = kRingWarnMs;

    // EM6: the pulses that flare posts: every second one, from the first (index 0, 2, 4 ...). The SP growth math
    // (heroic net +5 a minute, about 11 stacks at 1:15) needs the first firing about 20 s in; starting at the second
    // pulse would leave heroic about 15 at 1:15 (brs_emberseer_test prints both rates).
    inline bool IsPostPulse(std::uint32_t index)
    {
        return index % 2 == 0;
    }

    // ms from the pulse's start: the flare (its last ring has passed 21 yd) and the firing 8 s later.
    inline std::uint32_t PostFlareMs(std::span<Fronts::RingStep const> plan, Fronts::RingSequenceSpec const& spec)
    {
        return Fronts::LastPassMs(plan, spec, kPostFlareAfterYd);
    }

    inline std::uint32_t PostFireMs(std::span<Fronts::RingStep const> plan, Fronts::RingSequenceSpec const& spec)
    {
        return PostFlareMs(plan, spec) + kPostWindowMs;
    }

    // The next pulse's start (absolute ms): its cadence `dueMs`, held so its first ring cannot reach 15 yd before the
    // posts fire at `fireAtMs` (EM6). `nextSpec` is the pulse as it would start (its nova radius sets ring 1's start).
    inline std::uint64_t HeldPulseStart(std::uint64_t dueMs, std::optional<std::uint64_t> fireAtMs,
        Fronts::RingSequenceSpec const& nextSpec)
    {
        if (!fireAtMs)
            return dueMs;
        std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(nextSpec);
        std::uint64_t const reach = Fronts::FirstReachMs(plan, nextSpec, kPostReachGuardYd);
        return *fireAtMs > dueMs + reach ? *fireAtMs - reach : dueMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Posts (EM6, EM8)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kPostCount = BlackrockSpireRework::kEmberseerPosts.size();

    struct PostPick
    {
        std::vector<std::uint8_t> bind;         // flare and fire (EM6)
        std::vector<std::uint8_t> unstable;     // erupt (EM8, heroic): never a binding post
    };

    // `bind` distinct posts, then `unstable` distinct others (as many as are left). `rand(n)` returns [0, n).
    template <class Rand>
    PostPick PickPosts(std::uint32_t bind, std::uint32_t unstable, Rand&& rand)
    {
        std::vector<std::uint8_t> pool;
        for (std::uint8_t i = 0; i < kPostCount; ++i)
            pool.push_back(i);
        // Fisher-Yates over the seven.
        for (std::size_t i = pool.size(); i > 1; --i)
            std::swap(pool[i - 1], pool[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(i)))]);
        PostPick out;
        std::size_t const nb = std::min<std::size_t>(bind, pool.size());
        std::size_t const nu = std::min<std::size_t>(unstable, pool.size() - nb);
        out.bind.assign(pool.begin(), pool.begin() + static_cast<std::ptrdiff_t>(nb));
        out.unstable.assign(pool.begin() + static_cast<std::ptrdiff_t>(nb),
            pool.begin() + static_cast<std::ptrdiff_t>(nb + nu));
        return out;
    }

    // Stacks a firing takes away: held posts x 2 (1 at 6 or more players).
    inline std::uint32_t PostLoss(std::uint32_t heldPosts, std::uint32_t players)
    {
        return heldPosts * kPostStackLoss.At(players);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FightModel: the timeline on a 100 ms clock from the engage (the AI's own order of the same rules), for the SP
    // growth math and the pulse / post spacing.
    // ----------------------------------------------------------------------------------------------------------------

    struct FightSetup
    {
        bool heroic = false;
        std::uint32_t players = 5;
        std::uint32_t startStacks = 5;          // SP: a 25 s prelude starts him at about 5
        float postsHeld = 1.f;                  // share of the flared posts held (rounded per flare)
        bool pyroblastLands = false;            // every Pyroblast lands (else every one is kicked)
        std::uint32_t durationMs = 120000;
    };

    struct PulseRecord
    {
        std::uint32_t index = 0;
        std::uint64_t startMs = 0;
        std::uint64_t eruptionMs = 0;
        std::uint32_t stacks = 0;
        std::uint32_t rings = 0;
        float novaYd = 0.f;
        std::uint64_t lastRingOverMs = 0;
        std::uint64_t firstReach15Ms = 0;       // its first ring's outer edge reaches 15 yd
        std::uint64_t lastPass21Ms = 0;         // its last ring's inner edge passes 21 yd
        bool posts = false;
        std::uint64_t flareMs = 0;
        std::uint64_t fireMs = 0;
        std::uint64_t heldByMs = 0;             // how long the post rule held it past its cadence
    };

    struct FightTrace
    {
        std::vector<std::uint32_t> stacksAtSecond;      // stacks at each whole second from the engage
        std::vector<PulseRecord> pulses;
        std::optional<std::uint64_t> fullStrengthAtMs;
        std::uint32_t supernovas = 0;
        std::uint32_t pyroblasts = 0;
        std::uint32_t postsFired = 0;

        std::uint32_t StacksAt(std::uint32_t seconds) const
        {
            if (stacksAtSecond.empty())
                return 0;
            return stacksAtSecond[std::min<std::size_t>(seconds, stacksAtSecond.size() - 1)];
        }
    };

    inline FightTrace SimulateFight(FightSetup const& f)
    {
        FightTrace t;
        std::uint32_t stacks = ClampStacks(f.startStacks);
        std::uint64_t nextGrow = kGrowEveryMs(f.heroic);
        std::uint64_t nextPulseDue = kFirstPulseStartMs;
        std::uint64_t nextPyro = kPyroblastFirstMs;
        std::optional<std::uint64_t> pyroLands;
        std::optional<std::uint64_t> fireAt;
        std::uint32_t fireBind = 0;
        std::optional<std::uint64_t> nextSupernova;
        std::uint32_t index = 0;
        for (std::uint64_t now = 0; now <= f.durationMs; now += 100)
        {
            if (now >= nextGrow)
            {
                nextGrow += kGrowEveryMs(f.heroic);
                stacks = ClampStacks(std::int64_t(stacks) + 1);
            }
            if (fireAt && now >= *fireAt)
            {
                std::uint32_t const held = static_cast<std::uint32_t>(std::lround(f.postsHeld * float(fireBind)));
                stacks = ClampStacks(std::int64_t(stacks) - std::int64_t(PostLoss(held, f.players)));
                t.postsFired += held;
                fireAt.reset();
            }
            if (now >= nextPyro)
            {
                nextPyro += kPyroblastEveryMs;
                ++t.pyroblasts;
                if (f.pyroblastLands)
                    pyroLands = now + kPyroblastCastMs;
            }
            if (pyroLands && now >= *pyroLands)
            {
                stacks = ClampStacks(std::int64_t(stacks) + kPyroblastFeeds(f.heroic));
                pyroLands.reset();
            }
            Fronts::RingSequenceSpec const spec = PulseSpec(stacks, f.heroic, 0.f);
            std::uint64_t const start = HeldPulseStart(nextPulseDue, fireAt, spec);
            if (now >= start)
            {
                std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(spec);
                PulseRecord r;
                r.index = index;
                r.startMs = now;
                r.eruptionMs = now + kEruptionMs;
                r.stacks = stacks;
                r.rings = spec.rings;
                r.novaYd = spec.startYd;
                r.lastRingOverMs = now + Fronts::SequenceOverMs(plan);
                r.firstReach15Ms = now + Fronts::FirstReachMs(plan, spec, kPostReachGuardYd);
                r.lastPass21Ms = now + Fronts::LastPassMs(plan, spec, kPostFlareAfterYd);
                r.heldByMs = now - nextPulseDue;
                if (IsPostPulse(index))
                {
                    r.posts = true;
                    r.flareMs = now + PostFlareMs(plan, spec);
                    r.fireMs = now + PostFireMs(plan, spec);
                    fireAt = r.fireMs;
                    fireBind = kBindingPosts.At(f.players);
                }
                t.pulses.push_back(r);
                ++index;
                nextPulseDue = now + kPulseEveryMs(f.heroic);
            }
            if (stacks >= kFullStrengthStacks)
            {
                if (!t.fullStrengthAtMs)
                    t.fullStrengthAtMs = now;
                if (!nextSupernova)
                    nextSupernova = now + kSupernovaEveryMs;
                else if (now >= *nextSupernova)
                {
                    ++t.supernovas;
                    *nextSupernova += kSupernovaEveryMs;
                }
            }
            else
                nextSupernova.reset();
            if (now % 1000 == 0)
                t.stacksAtSecond.push_back(stacks);
        }
        return t;
    }
}

#endif
