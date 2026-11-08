/*
 * mod-dungeon-bosses, Scholomance S7: Lorekeeper Polkelt (10901), "Chain Reaction", the pure, host-testable part (no
 * engine headers). Build spec SC 1979-2036 (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows PK and 3.5
 * row S7. Tested by tests/scholo_polkelt_test.cpp.
 *
 *   Spells             the WP's ids, inside kSpellsPolkelt (206250-206269), declared in apps/dbc-tools
 *                      source/npcs/scholomance/lorekeeper_polkelt.py
 *   Tuning             NH<> constants: one number per difficulty, straight from the build spec (and the user's
 *                      section 10 ruling: the pool caps stay 6 / 8)
 *   SpecimenChain      PK2 / PK4 the specimens' fuses: a kill fuse (2 s), the chained fuse it lights (1 s, ruling
 *                      18), the ripe fuse (3 s, 12 yd), the order bursts resolve in, which specimens a burst lights,
 *                      and whether it catches the boss (PK3; a ripe burst never does)
 *   PoolQueue          PK5 the acid pools: 60 s each, at most 6 / 8, the oldest dries up first
 *   PickSpots          PK1 raise points on the hall floor (8 yd from every player; heroic rooted 13 yd apart) and the
 *                      detention lesson's ring around the student
 *   IsKillTarget       the bots' conditional kill target (near him, or about to ripen)
 *   Catalyst, Noxious  PK3 the reaction's hit and Corroded; PK7 the soft enrage's stacks
 *   FightProfile       the boss (normal, heroic) and the hard mode's Graduate Examiner (S13: 80k, heroic values)
 *   Lesson             the Hall of Secrets solo lesson (Gandling's detention): 3 / 4 specimens walk at the student
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_POLKELT_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_POLKELT_LOGIC_H

#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <vector>

namespace ScholoPolkelt
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsPolkelt;

    enum PolkeltSpells : std::uint32_t
    {
        SPELL_PK_SPECIMEN_BURST     = kSpellSlice.first + 0,    // 206250 PK2 a kill / chained burst (resolve copy)
        SPELL_PK_RIPE_BURST         = kSpellSlice.first + 1,    // 206251 PK4 a ripe burst (resolve copy)
        SPELL_PK_ACID_POOL          = kSpellSlice.first + 2,    // 206252 PK5 a pool's tick (resolve copy)
        SPELL_PK_ACID_POOL_LOOK     = kSpellSlice.first + 3,    // 206253 PK5 the pool on the floor (60 s, 6 yd)
        SPELL_PK_RAISE              = kSpellSlice.first + 4,    // 206254 PK1 a specimen rises (look)
        SPELL_PK_FUSE               = kSpellSlice.first + 5,    // 206255 PK2 the kill fuse, a 2 s swelling cast
        SPELL_PK_CHAINED_FUSE       = kSpellSlice.first + 6,    // 206256 PK2 the chained fuse, 1 s (ruling 18)
        SPELL_PK_RIPE               = kSpellSlice.first + 7,    // 206257 PK4 the ripe fuse, 3 s
        SPELL_PK_BURST_LOOK         = kSpellSlice.first + 8,    // 206258 PK2 / PK4 the burst (Disease Burst's look)
        SPELL_PK_CATALYST_REACTION  = kSpellSlice.first + 9,    // 206259 PK3 the hit on him (base point 0 by script)
        SPELL_PK_CORRODED           = kSpellSlice.first + 10,   // 206260 PK3 +5% damage taken per stack, 20 s, 10
        SPELL_PK_ROOTED             = kSpellSlice.first + 11,   // 206261 a rooted specimen's root and look
        SPELL_PK_HARDENED           = kSpellSlice.first + 12,   // 206262 PK6 heroic: rooted take 90% less damage
        SPELL_PK_NOXIOUS_CATALYST   = kSpellSlice.first + 13,   // 206263 PK7 heroic: the stacking dot, the enrage
        SPELL_PK_RIPENING           = kSpellSlice.first + 14,   // 206264 PK4 the 30 s clock on a specimen
        // 206265-206269 spare
    };
    static_assert(SPELL_PK_RIPENING <= kSpellSlice.last, "Polkelt's spells must stay in his slice");

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum PolkeltTags : std::uint32_t
    {
        TAG_KILL_BURST      = 1,    // PK2 a kill fuse's ring
        TAG_CHAINED_BURST   = 2,    // PK2 a chained fuse's ring
        TAG_RIPE_BURST      = 3,    // PK4
        TAG_ACID_POOL       = 4,    // PK5
        TAG_LESSON_BURST    = 5,    // detention: a specimen's ring in the Hall of Secrets lesson
    };

    // The specimen AI's data (UnitAI::GetData / SetData between the specimen and the lab).
    enum SpecimenData : std::uint32_t
    {
        DATA_SPECIMEN_COLLAPSED = 1,    // GetData: 1 once a lethal hit dropped it (it never dies on its own)
        DATA_SPECIMEN_FROZEN    = 2,    // SetData(.., 1): fusing or ripening, stands still and takes no damage
    };

    // The boss AI's data (S13's examiner hook): GetData(DATA_EXAMINER_MODE) is 1 on the Graduate Examiner.
    inline constexpr std::uint32_t DATA_EXAMINER_MODE = 0x5C07;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC 1985-2036; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // PK1 Raise Specimens: first at 10 s, then every 15 s; never within 8 yd of a player
    inline constexpr std::uint32_t kFirstBatchMs = 10000;
    inline constexpr std::uint32_t kBatchEveryMs = 15000;
    inline constexpr NH<std::uint32_t> kWalkersPerBatch{ 2, 3 };
    inline constexpr NH<std::uint32_t> kRootedPerBatch{ 1, 3 };
    inline constexpr NH<std::uint32_t> kSpecimenHealth{ 6000, 9000 };     // the DT rows (normal; heroic templates)
    inline constexpr float kRaiseMinFromPlayers = 8.f;
    inline constexpr float kRootedMinApart = 13.f;                        // heroic: a 6 yd burst never reaches two
    inline constexpr float kWalkerMinApart = 3.f;
    inline constexpr float kRaiseMinFromPool = 7.f;                       // a pool's 6 yd and a step: not in a pool

    // PK2 Fuse and burst
    inline constexpr std::uint32_t kFuseMs = 2000;
    inline constexpr std::uint32_t kChainedFuseMs = 1000;                 // ruling 18
    inline constexpr float kBurstRadius = 6.f;
    inline constexpr NH<float> kBurstPct{ 30.f, 40.f };                   // + Weakened (ruling 21), overlaps stack

    // PK3 Catalyst Reaction
    inline constexpr float kCatalystPct = 1.5f;                           // of his maximum health per burst
    inline constexpr std::uint32_t kCorrodedPctPerStack = 5;              // damage taken, per stack
    inline constexpr std::uint32_t kCorrodedMs = 20000;                   // refreshes
    inline constexpr std::uint32_t kCorrodedMaxStacks = 10;

    // PK4 Ripe
    inline constexpr std::uint32_t kRipeAfterMs = 30000;                  // from the raise, walking or rooted
    inline constexpr std::uint32_t kRipeWarnMs = 3000;
    inline constexpr float kRipeRadius = 12.f;
    inline constexpr NH<float> kRipePct{ 40.f, 55.f };                    // no Weakened (55% heroic, ruling 21)
    inline constexpr float kSwellMaxPct = 50.f;                           // the visible swell over the 30 s

    // PK5 Acid Pool
    inline constexpr float kPoolRadius = 6.f;
    inline constexpr std::uint32_t kPoolMs = 60000;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr NH<float> kPoolPct{ 8.f, 12.f };                     // per second
    inline constexpr NH<std::uint32_t> kPoolCap{ 6, 8 };                  // user ruling on section 7 #13: kept

    // PK6 Hardened (heroic)
    inline constexpr std::uint32_t kHardenedPct = 90;

    // PK7 Noxious Catalyst (heroic): +1 stack on every player every 10 s from the pull, 0.3% per second per stack
    inline constexpr std::uint32_t kNoxiousEveryMs = 10000;
    inline constexpr float kNoxiousPctPerStack = 0.3f;
    inline constexpr std::uint32_t kNoxiousTickMs = 1000;
    inline constexpr std::uint32_t kNoxiousAuraMs = 30000;                // refreshed every 10 s; fades if orphaned

    // PK8 Volatile Infection 18149 (stock, kept): first in [7, 15] s, then every 40 s (the stock SmartAI's timers)
    inline constexpr std::uint32_t kVolatileFirstMinMs = 7000;
    inline constexpr std::uint32_t kVolatileFirstMaxMs = 15000;
    inline constexpr std::uint32_t kVolatileEveryMs = 40000;

    // The bots' conditional kill target: within 6 yd of him, or ripe in under 3 s
    inline constexpr float kKillTargetNearBossYd = 6.f;
    inline constexpr std::uint32_t kKillTargetRipeSoonMs = 3000;

    // The Hall of Secrets floor (the frame's z 85; the stair and the gate corridor at z 89 are not)
    inline constexpr float kHallFloorZ = 85.3f;
    inline constexpr float kHallFloorZBand = 2.5f;

    // ----------------------------------------------------------------------------------------------------------------
    // PK2 / PK4 The chain
    // ----------------------------------------------------------------------------------------------------------------
    enum class BurstKind : std::uint8_t
    {
        Kill,       // a lethal hit dropped it (or, in the lesson, it reached its student): 2 s, 6 yd
        Chained,    // another burst's ring caught it: 1 s, 6 yd
        Ripe,       // 30 s after its raise: 3 s, 12 yd, leaves a pool, never reacts with the boss
    };

    enum class SpecimenPhase : std::uint8_t
    {
        Standing,   // walking or rooted, fighting
        Fusing,     // a kill or chained fuse is burning
        Ripening,   // the ripe fuse is burning
        Gone,       // burst, or despawned
    };

    struct ChainTuning
    {
        std::uint32_t fuseMs = kFuseMs;
        std::uint32_t chainedFuseMs = kChainedFuseMs;
        float burstRadius = kBurstRadius;
        bool ripens = true;                     // the detention lesson's specimens never ripen (15 s)
        std::uint32_t ripeAfterMs = kRipeAfterMs;
        std::uint32_t ripeWarnMs = kRipeWarnMs;
        float ripeRadius = kRipeRadius;
    };

    // A fuse that has just started: the engine freezes the specimen, casts its swell and registers the ring.
    struct FuseStart
    {
        std::uint32_t id = 0;
        Vec2 pos;
        BurstKind kind = BurstKind::Kill;
        std::uint32_t warnMs = 0;
        float radius = 0.f;
    };

    // A fuse that has burnt down this update, in resolve order.
    struct Burst
    {
        std::uint32_t id = 0;
        Vec2 pos;
        BurstKind kind = BurstKind::Kill;
        float radius = 0.f;
        bool catalyst = false;                  // PK3: the ring holds the boss (never on a ripe burst)
        bool leavesPool = false;                // PK5: a ripe burst
        std::vector<FuseStart> lit;             // the standing specimens its ring caught (chained fuses, 1 s)
    };

    // PK3: a kill or chained ring holds the boss (center within the radius plus his own bounding radius); a ripe one
    // never reacts (round 4 ruling: the catalyst has gone stale).
    constexpr bool CatalystReacts(BurstKind kind, float distanceToBoss, float radius, float bossBoundingRadius)
    {
        return kind != BurstKind::Ripe && distanceToBoss <= radius + bossBoundingRadius;
    }

    class SpecimenChain
    {
    public:
        struct Specimen
        {
            std::uint32_t id = 0;
            Vec2 pos;
            bool rooted = false;
            std::uint64_t risenMs = 0;
            SpecimenPhase phase = SpecimenPhase::Standing;
            BurstKind kind = BurstKind::Kill;
            std::uint64_t resolveMs = 0;
        };

        explicit SpecimenChain(ChainTuning tuning = {}) : _t(tuning) { }

        void Reset(ChainTuning tuning)
        {
            _t = tuning;
            _specimens.clear();
            _nextId = 1;
        }

        std::uint32_t Add(Vec2 pos, bool rooted, std::uint64_t nowMs)
        {
            Specimen s;
            s.id = _nextId++;
            s.pos = pos;
            s.rooted = rooted;
            s.risenMs = nowMs;
            _specimens.push_back(s);
            return s.id;
        }

        // A standing specimen moved (walkers); a burning fuse keeps the spot its ring was registered on.
        void SetPos(std::uint32_t id, Vec2 pos)
        {
            if (Specimen* s = Get(id); s && s->phase == SpecimenPhase::Standing)
                s->pos = pos;
        }

        // The specimen is gone without a burst (despawned, a GM kill of a frozen one).
        void Remove(std::uint32_t id)
        {
            if (Specimen* s = Get(id))
                s->phase = SpecimenPhase::Gone;
        }

        // A lethal hit dropped it (or, in the lesson, it reached its student): the 2 s kill fuse. Nothing when it is
        // not standing (a fuse already burns).
        std::optional<FuseStart> Kill(std::uint32_t id, std::uint64_t nowMs)
        {
            return StartFuse(id, nowMs, BurstKind::Kill);
        }

        // A burst caught it: the 1 s chained fuse (ruling 18), even at full health.
        std::optional<FuseStart> Light(std::uint32_t id, std::uint64_t nowMs)
        {
            return StartFuse(id, nowMs, BurstKind::Chained);
        }

        // PK4: every standing specimen 30 s after its raise starts its 3 s ripe fuse now.
        std::vector<FuseStart> TakeRipening(std::uint64_t nowMs)
        {
            std::vector<FuseStart> out;
            if (!_t.ripens)
                return out;
            for (Specimen& s : _specimens)
                if (s.phase == SpecimenPhase::Standing && nowMs >= s.risenMs + _t.ripeAfterMs)
                    if (std::optional<FuseStart> f = StartFuse(s.id, nowMs, BurstKind::Ripe))
                        out.push_back(*f);
            return out;
        }

        // Every standing specimen starts its ripe fuse now, whatever its age (`.dbtest scholo polkelt ripe`).
        std::vector<FuseStart> RipenNow(std::uint64_t nowMs)
        {
            std::vector<FuseStart> out;
            for (Specimen& s : _specimens)
                if (s.phase == SpecimenPhase::Standing)
                    if (std::optional<FuseStart> f = StartFuse(s.id, nowMs, BurstKind::Ripe))
                        out.push_back(*f);
            return out;
        }

        // Every fuse due at `nowMs`, in resolve order (then id). Each burst catches the boss when `boss` is given and
        // within reach (CatalystReacts), and lights every standing specimen inside its ring: their chained fuses start
        // now and resolve a second later (never in the same update).
        std::vector<Burst> TakeBursts(std::uint64_t nowMs, std::optional<Vec2> boss = std::nullopt,
            float bossBoundingRadius = 0.f)
        {
            std::vector<std::uint32_t> due;
            for (Specimen const& s : _specimens)
                if ((s.phase == SpecimenPhase::Fusing || s.phase == SpecimenPhase::Ripening) && s.resolveMs <= nowMs)
                    due.push_back(s.id);
            std::sort(due.begin(), due.end(), [this](std::uint32_t a, std::uint32_t b)
            {
                Specimen const* sa = Find(a);
                Specimen const* sb = Find(b);
                return sa->resolveMs != sb->resolveMs ? sa->resolveMs < sb->resolveMs : a < b;
            });

            std::vector<Burst> out;
            for (std::uint32_t id : due)
            {
                Specimen* s = Get(id);
                Burst b;
                b.id = s->id;
                b.pos = s->pos;
                b.kind = s->kind;
                b.radius = s->kind == BurstKind::Ripe ? _t.ripeRadius : _t.burstRadius;
                b.catalyst = boss && CatalystReacts(b.kind, DungeonKit::Distance(*boss, b.pos), b.radius,
                    bossBoundingRadius);
                b.leavesPool = b.kind == BurstKind::Ripe;
                s->phase = SpecimenPhase::Gone;
                std::vector<std::uint32_t> caught;
                for (Specimen const& other : _specimens)
                    if (other.phase == SpecimenPhase::Standing && DungeonKit::Distance(other.pos, b.pos) <= b.radius)
                        caught.push_back(other.id);
                for (std::uint32_t c : caught)
                    if (std::optional<FuseStart> f = StartFuse(c, nowMs, BurstKind::Chained))
                        b.lit.push_back(*f);
                out.push_back(std::move(b));
            }
            return out;
        }

        Specimen const* Find(std::uint32_t id) const
        {
            for (Specimen const& s : _specimens)
                if (s.id == id)
                    return &s;
            return nullptr;
        }

        // ms until it ripens (0 when due or not standing; UINT64_MAX when this chain never ripens).
        std::uint64_t MsToRipe(std::uint32_t id, std::uint64_t nowMs) const
        {
            Specimen const* s = Find(id);
            if (!s || s->phase != SpecimenPhase::Standing)
                return 0;
            if (!_t.ripens)
                return UINT64_MAX;
            std::uint64_t const at = s->risenMs + _t.ripeAfterMs;
            return at > nowMs ? at - nowMs : 0;
        }

        std::size_t Count(SpecimenPhase phase) const
        {
            return static_cast<std::size_t>(std::count_if(_specimens.begin(), _specimens.end(),
                [phase](Specimen const& s) { return s.phase == phase; }));
        }

        // Not gone (standing or burning).
        std::size_t Live() const { return _specimens.size() - Count(SpecimenPhase::Gone); }

        // Drops the gone ones (the engine calls it after it handled an update's bursts).
        void Compact()
        {
            _specimens.erase(std::remove_if(_specimens.begin(), _specimens.end(),
                [](Specimen const& s) { return s.phase == SpecimenPhase::Gone; }), _specimens.end());
        }

        std::vector<Specimen> const& All() const { return _specimens; }
        ChainTuning const& Tuning() const { return _t; }

    private:
        Specimen* Get(std::uint32_t id)
        {
            for (Specimen& s : _specimens)
                if (s.id == id)
                    return &s;
            return nullptr;
        }

        std::optional<FuseStart> StartFuse(std::uint32_t id, std::uint64_t nowMs, BurstKind kind)
        {
            Specimen* s = Get(id);
            if (!s || s->phase != SpecimenPhase::Standing)
                return std::nullopt;
            std::uint32_t const warn = kind == BurstKind::Kill ? _t.fuseMs
                : kind == BurstKind::Chained ? _t.chainedFuseMs : _t.ripeWarnMs;
            s->phase = kind == BurstKind::Ripe ? SpecimenPhase::Ripening : SpecimenPhase::Fusing;
            s->kind = kind;
            s->resolveMs = nowMs + warn;
            FuseStart f;
            f.id = s->id;
            f.pos = s->pos;
            f.kind = kind;
            f.warnMs = warn;
            f.radius = kind == BurstKind::Ripe ? _t.ripeRadius : _t.burstRadius;
            return f;
        }

        ChainTuning _t;
        std::vector<Specimen> _specimens;
        std::uint32_t _nextId = 1;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // PK5 The acid pools: each lasts 60 s; at the cap, a new one dries up the oldest (the user's caps: 6 / 8)
    // ----------------------------------------------------------------------------------------------------------------
    class PoolQueue
    {
    public:
        struct Pool
        {
            std::uint32_t handle = 0;       // the registry linger's MechanicHandle id
            Vec2 pos;
            std::uint64_t untilMs = 0;
        };

        // Drops the dried ones (their linger ended by itself); returns how many.
        std::size_t Expire(std::uint64_t nowMs)
        {
            std::size_t n = 0;
            while (!_pools.empty() && _pools.front().untilMs <= nowMs)
            {
                _pools.pop_front();
                ++n;
            }
            return n;
        }

        // A new pool at `nowMs`. Returns the pools it dries up (oldest first) to stay at `cap`.
        std::vector<Pool> Push(std::uint32_t handle, Vec2 pos, std::uint64_t nowMs, std::uint32_t cap,
            std::uint32_t lifeMs = kPoolMs)
        {
            Expire(nowMs);
            std::vector<Pool> dried;
            while (cap && _pools.size() >= cap)
            {
                dried.push_back(_pools.front());
                _pools.pop_front();
            }
            if (cap)
                _pools.push_back({ handle, pos, nowMs + lifeMs });
            return dried;
        }

        std::size_t Size() const { return _pools.size(); }
        std::deque<Pool> const& All() const { return _pools; }
        void Clear() { _pools.clear(); }

    private:
        std::deque<Pool> _pools;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // PK1 Raise points
    // ----------------------------------------------------------------------------------------------------------------
    struct SpotRules
    {
        DungeonKit::FrameRect floor = ScholomanceRework::kHallOfSecrets;
        float inset = 1.5f;                     // yd inside the frame (21 yd wide, so a specimen never hugs a wall)
        Vec2 arenaCenter{ 250.0f, 0.5f };       // PolkeltArena()
        float arenaRadius = 32.f;
        float arenaMargin = 2.f;
        float minFromPlayers = kRaiseMinFromPlayers;
        float minApart = kWalkerMinApart;       // from this call's picks and `apartFrom`
        float minFromAvoid = kRaiseMinFromPool; // from `avoid` (live pools)
        std::optional<Vec2> center;             // the lesson: a ring around the student
        float maxFromCenter = 0.f;
        std::uint32_t tries = 48;               // candidates per point
        std::uint32_t attempts = 8;             // whole batches
    };

    inline bool OnHallFloor(SpotRules const& rules, Vec2 p)
    {
        DungeonKit::FrameRect inner = rules.floor;
        inner.origin = DungeonKit::FramePoint(rules.floor, rules.inset, rules.inset);
        inner.sizeX = std::max(0.f, rules.floor.sizeX - 2.f * rules.inset);
        inner.sizeY = std::max(0.f, rules.floor.sizeY - 2.f * rules.inset);
        return DungeonKit::InsideFrame(inner, p, 0.f)
            && DungeonKit::Distance(rules.arenaCenter, p) <= rules.arenaRadius - rules.arenaMargin;
    }

    // How well a point fits the rules.
    struct SpotScore
    {
        bool players = false;
        bool apart = false;
        bool avoid = false;
        bool ring = false;
        float nearestPlayer = 0.f;

        bool Full() const { return players && apart && avoid && ring; }
        float Value() const
        {
            return (ring ? 100000.f : 0.f) + (players ? 10000.f : 0.f) + (apart ? 1000.f : 0.f)
                + (avoid ? 100.f : 0.f) + std::min(nearestPlayer, 50.f);
        }
    };

    inline SpotScore ScoreSpot(SpotRules const& rules, Vec2 p, std::vector<Vec2> const& players,
        std::vector<Vec2> const& apartFrom, std::vector<Vec2> const& avoid, std::vector<Vec2> const& picks)
    {
        SpotScore s;
        s.nearestPlayer = 1000.f;
        for (Vec2 const& q : players)
            s.nearestPlayer = std::min(s.nearestPlayer, DungeonKit::Distance(p, q));
        s.players = s.nearestPlayer >= rules.minFromPlayers;
        s.apart = true;
        for (Vec2 const& q : apartFrom)
            s.apart = s.apart && DungeonKit::Distance(p, q) >= rules.minApart;
        for (Vec2 const& q : picks)
            s.apart = s.apart && DungeonKit::Distance(p, q) >= rules.minApart;
        s.avoid = true;
        for (Vec2 const& q : avoid)
            s.avoid = s.avoid && DungeonKit::Distance(p, q) >= rules.minFromAvoid;
        s.ring = !rules.center || DungeonKit::Distance(*rules.center, p) <= rules.maxFromCenter;
        return s;
    }

    // `count` raise points. Each candidate is uniform on the inset hall frame (rand01() in [0, 1)), inside the arena,
    // and accepted by `valid(p)` (the engine's floor height check). Per point, the first candidate that keeps every
    // rule is taken; else the first of `fixed` that keeps every rule (the measured rooted spots); else the best scored
    // candidate (ring, players, apart, pools, then the farthest from a player), so a batch always rises while the
    // floor has a point. A greedy batch can block its own last point (13 yd apart on a 21 yd hall), so the whole batch
    // is drawn up to `rules.attempts` times and the first one that keeps every rule, else the one with the most, wins.
    template <class Rand01, class Valid>
    std::vector<Vec2> PickSpots(SpotRules const& rules, std::uint32_t count, std::vector<Vec2> const& players,
        std::vector<Vec2> const& apartFrom, std::vector<Vec2> const& avoid, Rand01&& rand01, Valid&& valid,
        std::vector<Vec2> const& fixed = {})
    {
        std::vector<Vec2> bestBatch;
        std::uint32_t bestFull = 0;
        for (std::uint32_t attempt = 0; attempt < std::max<std::uint32_t>(1, rules.attempts); ++attempt)
        {
            std::vector<Vec2> picks;
            std::uint32_t fullCount = 0;
            for (std::uint32_t i = 0; i < count; ++i)
            {
                std::optional<Vec2> best;
                float bestScore = -1.f;
                bool full = false;
                for (std::uint32_t t = 0; t < rules.tries && !full; ++t)
                {
                    float const fx = rand01();
                    float const fy = rand01();
                    Vec2 const p = DungeonKit::FramePoint(rules.floor,
                        rules.inset + fx * std::max(0.f, rules.floor.sizeX - 2.f * rules.inset),
                        rules.inset + fy * std::max(0.f, rules.floor.sizeY - 2.f * rules.inset));
                    if (!OnHallFloor(rules, p) || !valid(p))
                        continue;
                    SpotScore const s = ScoreSpot(rules, p, players, apartFrom, avoid, picks);
                    if (s.Full())
                    {
                        best = p;
                        full = true;
                    }
                    else if (s.Value() > bestScore)
                    {
                        bestScore = s.Value();
                        best = p;
                    }
                }
                for (std::size_t f = 0; !full && f < fixed.size(); ++f)
                {
                    Vec2 const p = fixed[f];
                    if (OnHallFloor(rules, p) && valid(p)
                        && ScoreSpot(rules, p, players, apartFrom, avoid, picks).Full())
                    {
                        best = p;
                        full = true;
                    }
                }
                if (!best)
                    break;
                fullCount += full ? 1 : 0;
                picks.push_back(*best);
            }
            if (picks.size() > bestBatch.size() || (picks.size() == bestBatch.size() && fullCount > bestFull))
            {
                bestBatch = picks;
                bestFull = fullCount;
            }
            if (bestBatch.size() == count && bestFull == count)
                break;
        }
        return bestBatch;
    }

    // A batch's rules: heroic rooted specimens 13 yd apart (from each other and from the rooted ones still up).
    inline SpotRules RaiseRules(bool rooted)
    {
        SpotRules rules;
        rules.minApart = rooted ? kRootedMinApart : kWalkerMinApart;
        return rules;
    }

    // The measured rooted spots (NAVMESH-REPORT section 7: pairs 17.0 to 26.0 yd apart), the fallback of a rooted pick.
    inline std::vector<Vec2> RootedFallbackSpots()
    {
        std::vector<Vec2> spots;
        for (ScholomanceRework::Point3 const& p : ScholomanceRework::kRootedSpecimenSpots)
            spots.push_back(p.XY());
        return spots;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bots, PK3, PK4, PK7
    // ----------------------------------------------------------------------------------------------------------------

    // The conditional kill target (SC "Boss data"): a specimen is a target once it is within 6 yd of him or ripe in
    // under 3 s, never otherwise (DPS hold fire until the pile is on him).
    constexpr bool IsKillTarget(float distanceToBoss, std::uint64_t msToRipe)
    {
        return distanceToBoss <= kKillTargetNearBossYd || msToRipe <= kKillTargetRipeSoonMs;
    }

    // PK3: the reaction's base points, 1.5% of his maximum health. His Corroded stacks raise every damage he takes,
    // this hit too, so the base is divided by them: the hit lands at 1.5% (before resistances).
    constexpr std::int32_t CatalystBasePoints(std::uint64_t maxHealth, std::uint32_t corrodedStacks)
    {
        double const pct = static_cast<double>(maxHealth) * kCatalystPct / 100.0;
        double const taken = 1.0 + static_cast<double>(std::min(corrodedStacks, kCorrodedMaxStacks))
            * kCorrodedPctPerStack / 100.0;
        return static_cast<std::int32_t>(pct / taken + 0.5);
    }

    // PK3: Corroded after one more reaction (refreshes; capped).
    constexpr std::uint32_t CorrodedAfterReaction(std::uint32_t stacks)
    {
        return std::min(kCorrodedMaxStacks, stacks + 1);
    }

    // PK4: the specimen's scale over its 30 s (1 at the raise, 1.5 when it ripens).
    constexpr float SwellScale(std::uint64_t ageMs, std::uint32_t ripeAfterMs = kRipeAfterMs,
        float maxPct = kSwellMaxPct)
    {
        float const f = ripeAfterMs ? std::min(1.f, static_cast<float>(ageMs) / static_cast<float>(ripeAfterMs))
            : 1.f;
        return 1.f + maxPct / 100.f * f;
    }

    // PK7: the stacks every player carries `elapsedMs` after the pull (one per 10 s, uncapped).
    constexpr std::uint32_t NoxiousStacksAt(std::uint64_t elapsedMs)
    {
        return static_cast<std::uint32_t>(elapsedMs / kNoxiousEveryMs);
    }

    // `r` in [0, 1): a point of [min, max].
    constexpr std::uint32_t InRange(std::uint32_t min, std::uint32_t max, float r)
    {
        return min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 1.f) * static_cast<float>(max - min));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's modes: the boss (normal or heroic) and the hard mode's Graduate Examiner (S13)
    // ----------------------------------------------------------------------------------------------------------------
    struct FightProfile
    {
        bool heroic = false;                    // the numbers (NH<>.heroic)
        bool hardened = false;                  // PK6: rooted specimens take 90% less damage
        bool noxious = false;                   // PK7: the soft enrage
        bool talks = true;                      // creature_text (the examiner entry has none)
        bool grades = true;                     // Passing Grades (GradeWatch) from the real fight only
        bool bossState = true;                  // BOSS_POLKELT: the door data, Gandling's reveal, the save
        std::uint32_t walkers = 2;
        std::uint32_t rooted = 1;
        std::uint32_t poolCap = 6;
        std::uint32_t maxHealth = 0;            // 0: the template's
    };

    // The examiner (SC 2997-3001: 80,000, both mechanics at heroic values; hard mode is heroic only).
    inline constexpr std::uint32_t kExaminerHealth = 80000;

    constexpr FightProfile ProfileFor(bool heroic, bool examiner)
    {
        FightProfile p;
        bool const h = heroic || examiner;
        p.heroic = h;
        p.hardened = h;
        p.noxious = h && !examiner;             // the heroic fight's enrage, not one of his two mechanics
        p.talks = !examiner;
        p.grades = !examiner;
        p.bossState = !examiner;
        p.walkers = kWalkersPerBatch(h);
        p.rooted = kRootedPerBatch(h);
        p.poolCap = kPoolCap(h);
        p.maxHealth = examiner ? kExaminerHealth : 0;
        return p;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Detention: the Hall of Secrets lesson (SC 2967: 3 / 4 Unstable Specimens walk at the student and burst on
    // reaching them or on death, 6 yd ring; pass: never in a burst; failure hit 15% / 25% + Weakened, SoloLesson.h)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<std::uint32_t> kLessonSpecimens{ 3, 4 };
    inline constexpr std::uint32_t kLessonSpawnGapMs = 2000;              // one every 2 s from the start
    inline constexpr float kLessonMinFromStudent = 10.f;
    inline constexpr float kLessonMaxFromStudent = 14.f;
    inline constexpr float kLessonReachYd = 2.5f;                         // this close to the student: it bursts
    inline constexpr float kLessonMinApart = 2.f;

    // When the `index`th specimen rises, ms from the lesson's start.
    constexpr std::uint32_t LessonSpawnAtMs(std::uint32_t index) { return index * kLessonSpawnGapMs; }

    inline SpotRules LessonRules(Vec2 student)
    {
        SpotRules rules;
        rules.minFromPlayers = kLessonMinFromStudent;
        rules.minApart = kLessonMinApart;
        rules.center = student;
        rules.maxFromCenter = kLessonMaxFromStudent;
        return rules;
    }

    inline ChainTuning LessonChain()
    {
        ChainTuning t;
        t.ripens = false;
        return t;
    }

    // The lesson has nothing left to do: every specimen rose and is gone.
    constexpr bool LessonCleared(std::uint32_t risen, std::uint32_t planned, std::size_t live)
    {
        return risen >= planned && live == 0;
    }
}

#endif
