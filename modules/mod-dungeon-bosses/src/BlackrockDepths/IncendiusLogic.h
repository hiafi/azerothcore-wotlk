/*
 * mod-dungeon-bosses, Blackrock Depths D11:
 * Lord Incendius (9017) and the Ember of Incendius (300794), the pure, host-testable part (no engine headers). Build
 * spec: docs/dungeons/blackrock-depths-2-shadowforge-city.md "Lord Incendius" (IN1-IN8; rulings 47, 48, 88), handoff
 * sections 3.4 row D11, 3.5 row D11, 3.6, 3.8 (the causeway), 3.10, 7 #14 A (the arena D12 shares). Tested by
 * tests/brd_incendius_test.cpp; apps/dbc-tools source/npcs/blackrock_depths/incendius.py declares the same ids.
 *
 *   Spells      the WP's ids, inside kSpellsIncendius (211140-211179)
 *   Tuning      NH<> values and the cadences, straight from the build spec (gap 36 picks marked)
 *   Causeway    NOT an island (NAVMESH 2.5): the z -72 causeway with the Anvil bulge. A frame along the causeway's axis
 *               (s from his spawn toward Fineous, w across it toward the north-west), the real edge profile read from
 *               the navmesh (2026-11-17, mesh edge + 0.5 yd), the floor polygon the edge pushes go over, the arena of
 *               section 7 #14 A (s -24 to +24), the neck seals and the long-edge crumble steps (IN8; D12 adds a third
 *               step), the bots' safe bounds, the Lava Surge strip (IN5) and the Ember spots (IN6)
 *   Rebirth     IN6 / IN7: how many, how many Embers, the reborn health
 *   FightClock  a repeating beat on the AI's own ms clock
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_INCENDIUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_INCENDIUS_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitEdgeLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace BrdIncendius
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsIncendius;

    enum IncendiusSpells : std::uint32_t
    {
        SPELL_IN_CURSE              = kSpellSlice.first + 0,    // 211140 IN1 +10% Fire taken, 45 yd, 60 s, Curse
        SPELL_IN_FIERY_BURST        = kSpellSlice.first + 1,    // 211141 IN2 1.5 s, 10 yd round his victim (refflat)
        SPELL_IN_FIRE_STORM         = kSpellSlice.first + 2,    // 211142 IN3 a patch tick (resolve copy, Fire)
        SPELL_IN_FIRE_STORM_CAST    = kSpellSlice.first + 3,    // 211143 IN3 the cast hands on him (look)
        SPELL_IN_FIRE_STORM_PATCH   = kSpellSlice.first + 4,    // 211144 IN3 the 5 yd lava pool on a stalker (look)
        SPELL_IN_MAGMA_FIST         = kSpellSlice.first + 5,    // 211145 IN4 the line's hit (resolve copy, Fire)
        SPELL_IN_MAGMA_FIST_WAVE    = kSpellSlice.first + 6,    // 211146 IN4 the magma wave to the line's end (look)
        SPELL_IN_MAGMA_FIST_RING    = kSpellSlice.first + 7,    // 211147 IN4 the ring at his feet (look)
        SPELL_IN_LAVA_SURGE         = kSpellSlice.first + 8,    // 211148 IN5 the strip's hit (resolve copy, Fire)
        SPELL_IN_LAVA_SURGE_BURST   = kSpellSlice.first + 9,    // 211149 IN5 Lava Strike along the strip (look)
        SPELL_IN_SHATTER            = kSpellSlice.first + 10,   // 211150 IN6 the eruption as he breaks (look)
        SPELL_IN_REBORN             = kSpellSlice.first + 11,   // 211151 IN7 the fire pillar at the Anvil (look)
        SPELL_IN_EMBER_ARRIVES      = kSpellSlice.first + 12,   // 211152 IN6 an Ember sinks into the Anvil (look)
        SPELL_IN_CRUMBLE_BURST      = kSpellSlice.first + 13,   // 211153 IN8 Lava Strike along a band (look)
        SPELL_IN_CRUMBLED_EDGE      = kSpellSlice.first + 14,   // 211154 IN8 the crack state on a stalker (look)
        SPELL_IN_CRUMBLING_GROUND   = kSpellSlice.first + 15,   // 211155 IN8 the burst on a unit thrown off (look)
        // 211156-211179 spare
    };
    static_assert(SPELL_IN_CRUMBLING_GROUND <= kSpellSlice.last, "Lord Incendius's spells must stay in his slice");

    // The stock spells he no longer casts (SmartAI 9017 rows 0-4, dropped by the S0 rev): Curse of the Elemental Lord
    // 26977, Fiery Burst 13900 and Fire Storm 13899 are copies above (rule 15); Mighty Blow 14099 is retired (Magma
    // Fist). Named for the tests.
    inline constexpr std::uint32_t kStockCurse = 26977;
    inline constexpr std::uint32_t kStockFieryBurst = 13900;
    inline constexpr std::uint32_t kStockFireStorm = 13899;
    inline constexpr std::uint32_t kStockMightyBlow = 14099;

    // Registry tags (the failure ledger and the playtest greps key on them). 13 and 14 are the BM drill's
    // `blackrock-depths-shapes` band tags (kBrdTagEdgeBand, kBrdTagCrumble; MechanicDrill.h), so the sweep's ledger
    // keys read the same in the fight; 15 (kBrdTagSweep) is D12's Arm Sweep.
    enum IncendiusTags : std::uint32_t
    {
        TAG_IN_FIRE_STORM   = 3,    // IN3
        TAG_IN_MAGMA_FIST   = 4,    // IN4
        TAG_IN_LAVA_SURGE   = 5,    // IN5
        TAG_IN_NECK_SEAL    = 13,   // IN8 the two 4 yd neck bands (kBrdTagEdgeBand)
        TAG_IN_CRUMBLE      = 14,   // IN8 a 2 yd step of the long edges (kBrdTagCrumble)
        TAG_IN_ARM_SWEEP    = 15,   // D12 IN11 (kBrdTagSweep): reserved here so the two files never collide
    };

    // creature_text 9017 groups (data/sql/updates/pending_db_world/rev_incendius_blackrock_depths.sql). 4, 6 and 7 are
    // the hard mode's (D12 says them); D12 owns 8-9.
    enum IncendiusTexts : std::uint8_t
    {
        YELL_IN_SHATTER             = 0,    // stock (made a yell): IN6
        YELL_IN_REBORN              = 1,    // IN7
        EMOTE_IN_CRUMBLES           = 2,    // IN8 the crumble
        YELL_IN_DEATH               = 3,    // the final death
        YELL_IN_LORD_OF_THE_LAKE    = 4,    // D12 IN9 (the Cinder)
        EMOTE_IN_EDGE_CRACKS        = 5,    // IN8 / IN13 the 5 s warning, every difficulty
        EMOTE_IN_ARM_RAISED         = 6,    // D12 IN11
        EMOTE_IN_BREATH             = 7,    // D12 IN14
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Build spec"; damage = % of the reference row, N level 53, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // Health (handoff section 3.6): normal 100k (HealthModifier 40.766 on the level 53 warrior base 2,453, the DT
    // stub), heroic 160k (WP-H's override). The Ember: 6k / 9k (its heroic template is WP-H's extra=).
    inline constexpr NH<std::uint32_t> kBossHealth{ 100000, 160000 };
    inline constexpr NH<std::uint32_t> kEmberHealth{ 6000, 9000 };
    inline constexpr std::uint32_t kWarrior53Base = 2453;
    inline constexpr std::uint32_t kEmberLevel = 53;

    // IN1 Curse of the Elemental Lord: +10% Fire damage taken on everyone within 45 yd for 60 s; a Curse (removal is
    // a reward). The stock timers.
    inline constexpr std::uint32_t kCurseFirstMs = 16000;
    inline constexpr std::uint32_t kCurseEveryMs = 22000;
    inline constexpr float kCurseFirePct = 10.f;
    inline constexpr float kCurseRadiusYd = 45.f;
    inline constexpr std::uint32_t kCurseMs = 60000;

    // IN2 Fiery Burst: a 1.5 s interruptible cast on his victim, everyone within 10 yd of it. The stock timers. "Stock
    // rescaled" is unset in the spec (gap 36): a group pulse at the BRS convention, 12% / 15% (designer question 1).
    inline constexpr std::uint32_t kBurstFirstMs = 9000;
    inline constexpr std::uint32_t kBurstMinMs = 9000;
    inline constexpr std::uint32_t kBurstMaxMs = 13000;
    inline constexpr std::uint32_t kBurstCastMs = 1500;
    inline constexpr float kBurstRadiusYd = 10.f;
    inline constexpr float kBurstRangeYd = 40.f;
    inline constexpr NH<float> kBurstPct{ 12.f, 15.f };

    // IN3 Fire Storm: a 2 s marker at a random player's spot (the tank included), then a 5 yd patch for 30 s ticking
    // 4% / 6% a second. Every 10 s (heroic 8 s) from 6 s.
    inline constexpr std::uint32_t kFireStormFirstMs = 6000;
    inline constexpr NH<std::uint32_t> kFireStormEveryMs{ 10000, 8000 };
    inline constexpr std::uint32_t kFireStormWarnMs = 2000;
    inline constexpr std::uint32_t kFireStormLifeMs = 30000;
    inline constexpr std::uint32_t kFireStormTickMs = 1000;
    inline constexpr float kFireStormRadiusYd = 5.f;
    inline constexpr NH<float> kFireStormPct{ 4.f, 6.f };

    // IN4 Magma Fist: every 20 s from 12 s, a random player (the tank included, ruling 88): a 2 s line from him
    // through them, then the fist along it: 25% / 40% + Weakened and a 10 yd throw along the line (PushAlong: on the
    // floor, or over the edge). The width and the overrun are unset in the spec (designer question 2).
    inline constexpr std::uint32_t kFistFirstMs = 12000;
    inline constexpr std::uint32_t kFistEveryMs = 20000;
    inline constexpr std::uint32_t kFistWarnMs = 2000;
    inline constexpr float kFistWidthYd = 4.f;
    inline constexpr float kFistOverrunYd = 8.f;
    inline constexpr float kFistMinLengthYd = 12.f;
    inline constexpr float kFistMaxLengthYd = 40.f;
    inline constexpr float kFistThrowYd = 10.f;
    inline constexpr NH<float> kFistPct{ 25.f, 40.f };

    // IN5 Lava Surge: every 25 s (heroic 20 s) from 15 s, a 3 s marker, a 6 yd strip along one long edge of the bulge:
    // 30% / 45% + Weakened.
    inline constexpr std::uint32_t kSurgeFirstMs = 15000;
    inline constexpr NH<std::uint32_t> kSurgeEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kSurgeWarnMs = 3000;
    inline constexpr float kSurgeWidthYd = 6.f;
    inline constexpr NH<float> kSurgePct{ 30.f, 45.f };
    inline constexpr std::uint32_t kSurgeBursts = 4;            // Lava Strike looks along the strip at the hit

    // IN6 / IN7 Reborn at the Anvil: a lethal hit shatters him into 4 (heroic 5) Embers at the edges; they roll to The
    // Black Anvil over about 10 s; 12 s after the shatter he reforms there with 40% of his health + 10% per Ember that
    // arrived (an Ember still alive at the reform joins him too: "an Ember left alive is 10% more health"). Once on
    // normal, twice on heroic; the last death is real.
    inline constexpr NH<std::uint32_t> kRebirths{ 1, 2 };
    inline constexpr NH<std::uint32_t> kEmbers{ 4, 5 };
    inline constexpr std::uint32_t kEmberRollMs = 10000;
    inline constexpr std::uint32_t kReformMs = 12000;
    inline constexpr float kRebornBasePct = 40.f;
    inline constexpr float kRebornPerEmberPct = 10.f;
    inline constexpr float kEmberArriveYd = 3.f;                // 2D, to the Anvil's centre
    inline constexpr float kEmberMinSpeedYdS = 0.5f;
    inline constexpr std::uint32_t kEmberReaimMs = 1000;        // re-aimed this often (slows, stuns, roots count)
    inline constexpr float kEmberEdgeInsetYd = 1.5f;            // spawned this far inside the current edge
    inline constexpr std::uint32_t kEmberCorpseMs = 5000;
    // Where he stands up: this far from the Anvil's centre toward the bulge's middle (the Anvil is a game object).
    inline constexpr float kReformOffsetYd = 2.5f;

    // IN8 The trap closes (section 7 #14 A, the arena D12 layers on): at each rebirth, a 5 s edge marker, then the
    // band crumbles for the rest of the fight. The first rebirth also seals the two necks (4 yd bands across the
    // causeway just outside the arena); every rebirth eats the next 2 yd of both long edges. Normal one step, heroic
    // two; D12's timer three. The bands are raised kReformMs - kBandWarnMs after the shatter, so the edge goes as he
    // stands up.
    inline constexpr float kNeckSealWidthYd = 4.f;
    inline constexpr float kCrumbleStepYd = 2.f;
    inline constexpr std::uint32_t kCrumbleMaxSteps = 3;       // D12's third step; D11 uses 1 / 2
    inline constexpr std::uint32_t kBandWarnMs = DungeonKit::kBandWarnMs;
    inline constexpr std::uint32_t kBandRaiseAfterShatterMs = kReformMs - kBandWarnMs;
    inline constexpr float kBandExtendYd = 1.f;                // closes the gaps at the profile's reflex corners
    inline constexpr float kNeckSealOverhangYd = 1.f;          // the seal reaches this far past both rims
    inline constexpr float kCrackSpacingYd = 10.f;             // the crack look every 10 yd along a band (V-1)

    // Falls (ruling 48: lethal): the kit's FallWatch kills anyone caught this far under the causeway over the lake.
    inline constexpr float kFloorZ = -71.9f;
    inline constexpr float kFallCatchBelowYd = 20.f;
    inline constexpr float kLakeZMin = -108.f;                  // the lava's surface is at -109 to -112
    inline constexpr std::uint32_t kFallGraceMs = 3000;
    // The lake under the causeway the watch covers (frame s and w), well past the arena.
    inline constexpr float kLakeSMin = -60.f;
    inline constexpr float kLakeSMax = 60.f;
    inline constexpr float kLakeHalfWidthYd = 45.f;

    // The bots' bounds: this far inside the current lethal edge (rule 5).
    inline constexpr float kBoundsMarginYd = 2.f;

    constexpr std::uint32_t RebirthsFor(bool heroic) { return kRebirths(heroic); }
    constexpr std::uint32_t EmbersFor(bool heroic) { return kEmbers(heroic); }

    // The reborn health in percent of his maximum: 40% + 10% per Ember that arrived, at most 100%.
    constexpr float RebornHealthPct(std::uint32_t arrived)
    {
        float const pct = kRebornBasePct + kRebornPerEmberPct * static_cast<float>(arrived);
        return pct > 100.f ? 100.f : pct;
    }

    // The crumble steps one rebirth leaves (rebirth 1 -> 1 step, rebirth 2 -> 2), never past kCrumbleMaxSteps.
    constexpr std::uint32_t CrumbleStepsAfter(std::uint32_t rebirthsDone)
    {
        return rebirthsDone > kCrumbleMaxSteps ? kCrumbleMaxSteps : rebirthsDone;
    }

    // The long edges' crumbled depth after `steps` steps.
    constexpr float CrumbledDepth(std::uint32_t steps)
    {
        return kCrumbleStepYd * static_cast<float>(steps > kCrumbleMaxSteps ? kCrumbleMaxSteps : steps);
    }

    // An Ember's roll speed over `distanceYd` (it arrives in kEmberRollMs when nothing slows it).
    inline float EmberSpeed(float distanceYd)
    {
        return std::max(kEmberMinSpeedYdS, distanceYd * 1000.f / static_cast<float>(kEmberRollMs));
    }

    // Magma Fist's line length for a target `distanceYd` away.
    inline float FistLength(float distanceYd)
    {
        return std::clamp(distanceYd + kFistOverrunYd, kFistMinLengthYd, kFistMaxLengthYd);
    }

    // How far along the bearing the line starts when it starts at its near end (the hard mode, R-1-B m3): far enough
    // that a target `distanceYd` away still gets the full overrun inside kFistMaxLengthYd. 0 within reach.
    inline float FistStartOffset(float distanceYd)
    {
        return std::max(0.f, distanceYd + kFistOverrunYd - kFistMaxLengthYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The causeway frame (NAVMESH 2.5; section 3.8): s along kIncendiusAxis from his spawn (positive toward Fineous,
    // north-east), w across it (positive north-west: the StripRegion convention n = (-axis.y, axis.x)).
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kOrigin = BlackrockDepthsRework::kIncendiusSpawn.XY();
    inline constexpr Vec2 kAxis = BlackrockDepthsRework::kIncendiusAxis;
    inline constexpr Vec2 kAcross{ -BlackrockDepthsRework::kIncendiusAxis.y, BlackrockDepthsRework::kIncendiusAxis.x };
    // The Black Anvil 172911, the Embers' goal and his reform spot [db 2026-11-17].
    inline constexpr Point3 kAnvil{ 895.1f, -273.6f, -71.9f };

    constexpr Vec2 ToWorld(float s, float w)
    {
        return { kOrigin.x + kAxis.x * s + kAcross.x * w, kOrigin.y + kAxis.y * s + kAcross.y * w };
    }

    struct FramePoint
    {
        float s = 0.f;
        float w = 0.f;
    };

    constexpr FramePoint ToFrame(Vec2 p)
    {
        float const dx = p.x - kOrigin.x;
        float const dy = p.y - kOrigin.y;
        return { dx * kAxis.x + dy * kAxis.y, dx * kAcross.x + dy * kAcross.y };
    }

    // The real edge profile: at each s, the south-east edge wLo and the north-west edge wHi (yd), read from the six
    // map 230 mmtiles 2026-11-17 (the mesh edge plus its 0.5 yd shrink), simplified to these vertices (within 1.1 yd of
    // the mesh, mostly inside it). The bulge is s -6 to +18 (25.5 yd at s 6); the necks are 9 to 10 yd (s -24 to -6
    // and s 18 to 32); the causeway runs on past both ends.
    struct ProfilePoint
    {
        float s = 0.f;
        float wLo = 0.f;
        float wHi = 0.f;
    };

    inline constexpr std::array<ProfilePoint, 9> kProfile{ {
        { -46.f, -15.50f, 4.00f },
        { -24.f, -10.00f, 0.75f },
        {  -6.f,  -8.50f, 1.25f },
        {   0.f, -14.00f, 7.75f },
        {   6.f, -16.00f, 9.50f },
        {  10.f, -15.00f, 8.50f },
        {  18.f,  -7.25f, 2.00f },
        {  24.f,  -7.25f, 2.75f },
        {  46.f,  -8.75f, 6.50f },
    } };

    // The arena (section 7 #14 A): the Anvil bulge and its necks from s -24 to s +24. The neck seals lie just outside.
    inline constexpr float kArenaSMin = -24.f;
    inline constexpr float kArenaSMax = 24.f;

    // The edge profile at `s` (clamped to the profile's ends), linear between the vertices.
    inline ProfilePoint ProfileAt(float s)
    {
        if (s <= kProfile.front().s)
            return { s, kProfile.front().wLo, kProfile.front().wHi };
        for (std::size_t i = 1; i < kProfile.size(); ++i)
            if (s <= kProfile[i].s)
            {
                ProfilePoint const& a = kProfile[i - 1];
                ProfilePoint const& b = kProfile[i];
                float const t = (s - a.s) / (b.s - a.s);
                return { s, a.wLo + (b.wLo - a.wLo) * t, a.wHi + (b.wHi - a.wHi) * t };
            }
        return { s, kProfile.back().wLo, kProfile.back().wHi };
    }

    // The middle of the floor across at `s`.
    inline float MidlineAt(float s)
    {
        ProfilePoint const p = ProfileAt(s);
        return (p.wLo + p.wHi) * 0.5f;
    }

    // The real floor's edge polygon (s -46 to +46): the south-east edge in rising s, then the north-west edge back. The
    // pushes (PushOverEdge / PushAlong) go over its edges; its two end caps are far outside the arena, so the shortest
    // way out of any band is always over a long edge.
    inline std::vector<Vec2> CausewayFloor()
    {
        std::vector<Vec2> poly;
        poly.reserve(kProfile.size() * 2);
        for (ProfilePoint const& p : kProfile)
            poly.push_back(ToWorld(p.s, p.wLo));
        for (auto it = kProfile.rbegin(); it != kProfile.rend(); ++it)
            poly.push_back(ToWorld(it->s, it->wHi));
        return poly;
    }

    // CausewayFloor's edges inside the arena (both ends within s -24..+24): the long edges a crumble eats. South-east
    // edges 1-6 (s -24 to +24), north-west edges 10-15 (s +24 back to -24).
    inline constexpr std::array<std::size_t, 12> kLongEdges{ { 1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15 } };

    // A two-point band (a registry Line's centre line and width).
    struct Band
    {
        Vec2 from;
        Vec2 to;
        float width = 0.f;
    };

    // A neck seal: a band across the causeway centred kNeckSealWidthYd / 2 outside an arena end.
    inline Band NeckSeal(bool east)
    {
        float const s = east ? kArenaSMax + kNeckSealWidthYd * 0.5f : kArenaSMin - kNeckSealWidthYd * 0.5f;
        ProfilePoint const p = ProfileAt(s);
        return { ToWorld(s, p.wLo - kNeckSealOverhangYd), ToWorld(s, p.wHi + kNeckSealOverhangYd), kNeckSealWidthYd };
    }

    // The sealed necks hold the fight (R-1-B m4, orchestrator default): a player of the fight standing on the causeway
    // past a sealed neck (the seal's far side, within the floor's width plus the overhang, on the causeway's height,
    // out to the lake box's ends) is put back onto the arena: kNeckGripInsetYd inside that neck's end, on the midline.
    inline constexpr float kNeckGripZBandYd = 4.f;
    inline constexpr float kNeckGripInsetYd = 4.f;
    inline constexpr std::uint32_t kNeckGripCheckMs = 500;
    inline constexpr std::uint32_t kNeckGripGraceMs = 1500;
    inline constexpr std::uint32_t kNeckGripCooldownMs = 3000;

    // 0: not past a neck; +1: past the east (Fineous) neck; -1: past the west one.
    inline int PastSealedNeck(Vec2 p, float z)
    {
        FramePoint const f = ToFrame(p);
        if (std::fabs(z - kFloorZ) > kNeckGripZBandYd || std::fabs(f.s) > kLakeSMax)
            return 0;
        int side = 0;
        if (f.s >= kArenaSMax + kNeckSealWidthYd)
            side = 1;
        else if (f.s <= kArenaSMin - kNeckSealWidthYd)
            side = -1;
        if (!side)
            return 0;
        ProfilePoint const pp = ProfileAt(f.s);
        return f.w >= pp.wLo - kNeckSealOverhangYd && f.w <= pp.wHi + kNeckSealOverhangYd ? side : 0;
    }

    // Where a player past neck `side` (+1 east, -1 west) is put back.
    inline Vec2 NeckGripLanding(int side)
    {
        float const s = side > 0 ? kArenaSMax - kNeckGripInsetYd : kArenaSMin + kNeckGripInsetYd;
        return ToWorld(s, MidlineAt(s));
    }

    // The long-edge band of crumble step `step` (1-based) on CausewayFloor's edge `edge`: kit EdgeBand between the
    // step's depths, stretched kBandExtendYd at both ends.
    inline Band CrumbleBand(std::vector<Vec2> const& floor, std::size_t edge, std::uint32_t step)
    {
        float const from = CrumbledDepth(step - 1);
        float const to = CrumbledDepth(step);
        DungeonKit::WallLine const w = DungeonKit::EdgeBand(std::span<Vec2 const>(floor), edge, from, to,
            kBandExtendYd);
        return { w.from, w.to, w.width };
    }

    // The lateral shift that moves profile vertex `i` `depthYd` (measured square to its edges) inward: the steeper of
    // its two edges decides (depth * sqrt(1 + slope^2)), so the shifted line never comes closer than `depthYd`.
    inline float LateralShift(std::size_t i, bool lo, float depthYd)
    {
        auto slope = [lo](ProfilePoint const& a, ProfilePoint const& b)
        {
            float const dw = lo ? b.wLo - a.wLo : b.wHi - a.wHi;
            return dw / (b.s - a.s);
        };
        float factor = 1.f;
        if (i > 0)
        {
            float const m = slope(kProfile[i - 1], kProfile[i]);
            factor = std::max(factor, std::sqrt(1.f + m * m));
        }
        if (i + 1 < kProfile.size())
        {
            float const m = slope(kProfile[i], kProfile[i + 1]);
            factor = std::max(factor, std::sqrt(1.f + m * m));
        }
        return depthYd * factor;
    }

    // The floor between sMin and sMax with both long edges moved `insetYd` inward (a crumbled depth, plus a margin),
    // as a polygon in map coordinates: the south-east side in rising s, then the north-west side back. Where the two
    // sides would cross, both sit on the middle line (a zero-width neck: nothing safe there).
    inline std::vector<Vec2> InsetFloor(float sMin, float sMax, float insetYd)
    {
        struct Row
        {
            float s;
            float lo;
            float hi;
        };
        std::vector<Row> rows;
        auto add = [&rows](float s, float lo, float hi)
        {
            if (lo > hi)
                lo = hi = (lo + hi) * 0.5f;
            rows.push_back({ s, lo, hi });
        };
        // An interpolated end: the larger of its two neighbouring vertices' shifts.
        auto endRow = [insetYd](float s)
        {
            std::size_t upper = 1;
            while (upper + 1 < kProfile.size() && kProfile[upper].s < s)
                ++upper;
            std::size_t const lower = upper - 1;
            ProfilePoint const p = ProfileAt(s);
            float const shiftLo = std::max(LateralShift(lower, true, insetYd), LateralShift(upper, true, insetYd));
            float const shiftHi = std::max(LateralShift(lower, false, insetYd), LateralShift(upper, false, insetYd));
            return Row{ s, p.wLo + shiftLo, p.wHi - shiftHi };
        };
        Row const first = endRow(sMin);
        add(first.s, first.lo, first.hi);
        for (std::size_t i = 0; i < kProfile.size(); ++i)
            if (kProfile[i].s > sMin && kProfile[i].s < sMax)
                add(kProfile[i].s, kProfile[i].wLo + LateralShift(i, true, insetYd),
                    kProfile[i].wHi - LateralShift(i, false, insetYd));
        Row const last = endRow(sMax);
        add(last.s, last.lo, last.hi);

        std::vector<Vec2> poly;
        poly.reserve(rows.size() * 2);
        for (Row const& r : rows)
            poly.push_back(ToWorld(r.s, r.lo));
        for (auto it = rows.rbegin(); it != rows.rend(); ++it)
            poly.push_back(ToWorld(it->s, it->hi));
        return poly;
    }

    // The arena's real floor (s -24 to +24, the real edges): the boss's leash and the playtest's area.
    inline std::vector<Vec2> ArenaFloor()
    {
        return InsetFloor(kArenaSMin, kArenaSMax, 0.f);
    }

    // The bots' safe ground after `steps` crumble steps: the arena kBoundsMarginYd inside the lethal edges (rule 5).
    // The neck ends (s -24 / +24) are kept back by the margin too.
    inline std::vector<Vec2> SafeFloor(std::uint32_t steps)
    {
        return InsetFloor(kArenaSMin + kBoundsMarginYd, kArenaSMax - kBoundsMarginYd,
            CrumbledDepth(steps) + kBoundsMarginYd);
    }

    // The shoelace area of a polygon (sq yd).
    inline float PolygonArea(std::vector<Vec2> const& poly)
    {
        float twice = 0.f;
        for (std::size_t i = 0; i < poly.size(); ++i)
        {
            Vec2 const& a = poly[i];
            Vec2 const& b = poly[(i + 1) % poly.size()];
            twice += a.x * b.y - b.x * a.y;
        }
        return std::fabs(twice) * 0.5f;
    }

    // IN5's strip: along the bulge (s -3 to +15) on one long edge, its outer side on the bulge's widest point of that
    // edge (s 6) moved in by the crumbled depth; 6 yd wide. Players outside it (toward the middle) are clear.
    inline constexpr float kSurgeSMin = -3.f;
    inline constexpr float kSurgeSMax = 15.f;
    inline constexpr float kSurgeWidestS = 6.f;

    enum class Side : std::uint8_t
    {
        SouthEast = 0,      // wLo
        NorthWest = 1,      // wHi
    };

    constexpr char const* SideName(Side side)
    {
        return side == Side::SouthEast ? "south-east" : "north-west";
    }

    inline Band SurgeStrip(Side side, std::uint32_t steps)
    {
        ProfilePoint const widest = ProfileAt(kSurgeWidestS);
        float const depth = CrumbledDepth(steps);
        float const w = side == Side::SouthEast ? widest.wLo + depth + kSurgeWidthYd * 0.5f
            : widest.wHi - depth - kSurgeWidthYd * 0.5f;
        return { ToWorld(kSurgeSMin, w), ToWorld(kSurgeSMax, w), kSurgeWidthYd };
    }

    // The side a point is on (by the floor's middle line at its s).
    inline Side SideOf(Vec2 p)
    {
        FramePoint const f = ToFrame(p);
        return f.w < MidlineAt(f.s) ? Side::SouthEast : Side::NorthWest;
    }

    // The surge goes where more players stand; a tie is the roll's (`roll` 0 or 1).
    constexpr Side PickSurgeSide(std::uint32_t southEast, std::uint32_t northWest, std::uint32_t roll)
    {
        if (southEast != northWest)
            return southEast > northWest ? Side::SouthEast : Side::NorthWest;
        return roll ? Side::NorthWest : Side::SouthEast;
    }

    // IN6: where the Embers appear, kEmberEdgeInsetYd inside the current (crumbled) edge: two on each long edge of the
    // bulge (s 0 and s 12), and on heroic a fifth in the west neck's middle. `w` is a side sign: -1 the south-east
    // edge, +1 the north-west edge, 0 the middle line.
    inline constexpr std::array<FramePoint, 5> kEmberSlots{ {
        { 0.f, -1.f },
        { 12.f, -1.f },
        { 0.f, 1.f },
        { 12.f, 1.f },
        { -14.f, 0.f },
    } };

    // The lateral shift at `s` (between vertices) that keeps `depthYd` square to that side's edge there.
    inline float LateralShiftAt(float s, bool lo, float depthYd)
    {
        std::size_t upper = 1;
        while (upper + 1 < kProfile.size() && kProfile[upper].s < s)
            ++upper;
        ProfilePoint const& a = kProfile[upper - 1];
        ProfilePoint const& b = kProfile[upper];
        float const m = ((lo ? b.wLo - a.wLo : b.wHi - a.wHi)) / (b.s - a.s);
        return depthYd * std::sqrt(1.f + m * m);
    }

    inline std::vector<Vec2> EmberSpots(std::uint32_t count, std::uint32_t steps)
    {
        std::vector<Vec2> spots;
        float const depth = CrumbledDepth(steps) + kEmberEdgeInsetYd;
        for (std::size_t i = 0; i < kEmberSlots.size() && spots.size() < count; ++i)
        {
            FramePoint const slot = kEmberSlots[i];
            ProfilePoint const p = ProfileAt(slot.s);
            float w = MidlineAt(slot.s);
            if (slot.w < 0.f)
                w = std::min(p.wLo + LateralShiftAt(slot.s, true, depth), w);
            else if (slot.w > 0.f)
                w = std::max(p.wHi - LateralShiftAt(slot.s, false, depth), w);
            spots.push_back(ToWorld(slot.s, w));
        }
        return spots;
    }

    // Where he reforms: kReformOffsetYd from the Anvil toward the floor's middle line.
    inline Vec2 ReformSpot()
    {
        FramePoint const anvil = ToFrame(kAnvil.XY());
        float const dir = MidlineAt(anvil.s) >= anvil.w ? 1.f : -1.f;
        return ToWorld(anvil.s, anvil.w + dir * kReformOffsetYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FightClock: a repeating beat on the AI's own ms clock (FineousLogic.h's, plus a hold)
    // ----------------------------------------------------------------------------------------------------------------

    class FightClock
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

        // Holds the beat: due no sooner than `notBeforeMs` (D12's "nothing lands during the Sweep").
        void NotBefore(std::uint64_t notBeforeMs)
        {
            if (_on && _dueMs < notBeforeMs)
                _dueMs = notBeforeMs;
        }

        // It fired: the next one is `everyMs` after this one's due time (start to start), never in the past.
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
