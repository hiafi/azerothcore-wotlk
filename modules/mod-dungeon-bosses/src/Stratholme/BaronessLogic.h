/*
 * mod-dungeon-bosses, Stratholme S10: Baroness Anastari (10436), the pure, host-testable part (no engine headers).
 * Build spec ST 2630-2677 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows BA and 3.5 row S10. Tested by
 * tests/strat_baroness_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsBaroness (206625-206644), declared in apps/dbc-tools
 *                  source/npcs/stratholme/baroness_anastari.py
 *   Tuning         NH<> constants and Cadence{first, every}: one number per difficulty, straight from the build spec
 *   PickIsolated   BA1 who is doomed: the player with the fewest allies within 10 yd, ties to the one farthest from
 *                  her, then random (Death's Echo does not matter, ruling 42)
 *   KnellInside    BA2 who shares the Death Knell: the players within 6 yd of the doomed
 *   KnellShares    BA2 / BA3 the even split of the total, each share raised by 100% per Death's Echo stack
 *   CastPlan       BA4 / BA6 / BA7 and the stock Banshee Wail: the cast queue with the cadences, so her casts never
 *                  overlap (the second waits for the first) and the stock filler never delays a mechanic
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARONESS_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARONESS_LOGIC_H

#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <climits>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratBaroness
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBaroness;

    enum BaronessSpells : std::uint32_t
    {
        SPELL_BA_KEENED             = kSpellSlice.first + 0,    // 206625 BA1 the doomed player's debuff (the skull)
        SPELL_BA_DEATH_KNELL        = kSpellSlice.first + 1,    // 206626 BA2 one share of the Knell (base point 0)
        SPELL_BA_DEATHS_ECHO        = kSpellSlice.first + 2,    // 206627 BA3 the stacking debuff, no cap, 45 s
        SPELL_BA_WAIL_BAR           = kSpellSlice.first + 3,    // 206628 BA4 the 3 s cast bar
        SPELL_BA_WAIL_HIT           = kSpellSlice.first + 4,    // 206629 BA4 the ring's hit (resolve copy)
        SPELL_BA_TERRIFIED          = kSpellSlice.first + 5,    // 206630 the 2 s fear (the rider of BA4, BA5, BA6)
        SPELL_BA_WAIL_ECHO_HIT      = kSpellSlice.first + 6,    // 206631 BA5 heroic: the donut's hit (resolve copy)
        SPELL_BA_VISAGE_BAR         = kSpellSlice.first + 7,    // 206632 BA6 the 2 s cast bar (normal)
        SPELL_BA_VISAGE_BAR_HEROIC  = kSpellSlice.first + 8,    // 206633 BA6 the 1.5 s cast bar (heroic)
        SPELL_BA_VISAGE_HIT         = kSpellSlice.first + 9,    // 206634 BA6 the cone's hit (resolve copy)
        SPELL_BA_LAMENT             = kSpellSlice.first + 10,   // 206635 BA7 heroic: the 2.5 s interruptible cast
        // 206636-206644 spare
    };
    static_assert(SPELL_BA_LAMENT <= kSpellSlice.last, "the Baroness's spells must stay in her slice");

    // Stock: Banshee Wail 16565, 1.5 s on the tank every 4 s (StratholmeRework::SPELL_BANSHEE_WAIL, BA8; DD scales it
    // on heroic).
    inline constexpr std::uint32_t kStockBansheeWailCastMs = 1500;

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum BaronessTags : std::uint32_t
    {
        TAG_KEEN_STACK  = 1,    // BA1 the Stack on the doomed
        TAG_KEEN_AVOID  = 2,    // BA1 the keep-out circle for Echo holders (telegraph-only, no marker)
        TAG_WAIL        = 3,    // BA4
        TAG_WAIL_ECHO   = 4,    // BA5
        TAG_VISAGE      = 5,    // BA6
        TAG_WAIL_ECHO_DRAWN = 6,    // BA5 the drawn donut (a Decoy: no hit, bots never see it)
    };

    // BA1: her keening sound (SoundEntries 1171, BansheeDeath), played at the keen's start.
    inline constexpr std::uint32_t kSoundKeening = 1171;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 2630-2677; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // First start and cadence of a beat, in ms since the pull (ST "First, cooldown"). Cadences count start to start.
    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    // BA1 The Keening: 6 s, then every 30 s. The doomed carries Keened for 6 s (heroic 5 s) and the Death Knell lands
    // when it ends.
    inline constexpr Cadence kKeen{ 6000, 30000 };
    inline constexpr NH<std::uint32_t> kKeenMs{ 6000, 5000 };
    inline constexpr float kIsolationRadius = 10.f;         // "allies near" for the pick
    inline constexpr float kIsolationZBand = 8.f;           // yd above or below that still count as near
    inline constexpr float kFightRange = 60.f;              // a player farther from her than this is not in the fight

    // BA2 Death Knell: 90% (heroic 100%) split evenly among the doomed and every player within 6 yd, each share raised
    // by Death's Echo; no Weakened.
    inline constexpr NH<float> kKnellPct{ 90.f, 100.f };
    inline constexpr float kKnellRadius = 6.f;
    inline constexpr float kKnellZBand = 8.f;

    // BA3 Death's Echo: +100% Death Knell damage taken per stack, 45 s, each stack refreshes it, no cap.
    inline constexpr float kEchoPerStack = 1.f;
    inline constexpr std::uint32_t kEchoDurationMs = 45000;

    // BA4 Wail of the Banshee: 16 s, every 20 s; a 3 s cast, 45% (heroic 50%) in 12 yd + Terrified, no Weakened.
    inline constexpr Cadence kWail{ 16000, 20000 };
    inline constexpr std::uint32_t kWailCastMs = 3000;
    inline constexpr float kWailRadius = 12.f;
    inline constexpr NH<float> kWailPct{ 45.f, 50.f };

    // BA5 The Wail's echo (heroic): 2 s after BA4 lands, beyond 8 yd from her, 40% + Terrified, no Weakened. The hit
    // is a hidden 8 / 60 yd donut (everyone beyond 8 yd, ST BA5; her arena runs to about 41 yd from her on the plaza
    // side); below an inner / outer ratio of 0.25 the marker draws no hole, so the drawn donut is a separate 8 / 32 yd
    // Decoy (F-1 ruling, Maleki's eye pattern).
    inline constexpr float kWailEchoInner = 8.f;
    inline constexpr float kWailEchoReachYd = 60.f;
    inline constexpr float kWailEchoDrawnOuter = 32.f;
    inline constexpr std::uint32_t kWailEchoWarnMs = 2000;
    inline constexpr float kWailEchoPct = 40.f;

    // BA6 Horrifying Visage: 12 s, every 20 s; a 2 s (heroic 1.5 s) cast, a 60 degree 30 yd cone toward a random
    // non-tank's spot, fixed at the cast start (heroic: two cones at two players); 30% (heroic 35%) + Weakened +
    // Terrified.
    inline constexpr Cadence kVisage{ 12000, 20000 };
    inline constexpr NH<std::uint32_t> kVisageCastMs{ 2000, 1500 };
    inline constexpr float kVisageAngleDeg = 60.f;
    inline constexpr float kVisageLengthYd = 30.f;
    inline constexpr NH<float> kVisagePct{ 30.f, 35.f };
    inline constexpr NH<std::uint32_t> kVisageCones{ 1, 2 };

    // BA7 Lament for the Living (heroic): 21 s, every 30 s; a 2.5 s interruptible cast, completed: a Death's Echo stack
    // on every player.
    inline constexpr Cadence kLament{ 21000, 30000 };
    inline constexpr std::uint32_t kLamentCastMs = 2500;

    // Terrified: one 2 s fear, mechanic Fear (the shared limit on loss of control).
    inline constexpr std::uint32_t kTerrifiedMs = 2000;

    // BA8 stock Banshee Wail 16565 on the tank: 1.5 s cast every 4 s, waits for her mechanic casts.
    inline constexpr Cadence kBansheeWail{ 2000, 4000 };

    // Her casts never overlap: the second waits for the first, then this long (so a bar is not cut by the next).
    inline constexpr std::uint32_t kCastSpacingMs = 300;
    // A stock Banshee Wail that has waited this long past its turn is skipped (it never queues behind a mechanic).
    inline constexpr std::uint32_t kFillerDropAfterMs = 2500;
    // The stock Wail does not start when a mechanic cast is due within its cast time plus this margin.
    inline constexpr std::uint32_t kFillerMarginMs = 150;
    inline constexpr std::uint32_t kCastRetryMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // BA1 The Keening: the most isolated player
    // ----------------------------------------------------------------------------------------------------------------

    struct Candidate
    {
        std::uint64_t id = 0;
        Vec2 pos;
        float z = 0.f;
        float distToBoss = 0.f;
    };

    // How many of the others stand within `radius` (and `zBand` in height) of candidate i.
    inline std::uint32_t AlliesNear(std::vector<Candidate> const& c, std::size_t i, float radius, float zBand)
    {
        std::uint32_t n = 0;
        for (std::size_t j = 0; j < c.size(); ++j)
            if (j != i && DungeonKit::Distance(c[i].pos, c[j].pos) <= radius && std::fabs(c[i].z - c[j].z) <= zBand)
                ++n;
        return n;
    }

    // The doomed player: the fewest allies within `radius`; ties go to the one farthest from the boss (within half a
    // yard counts as equal), then to `roll01` (a uniform number in [0, 1)) among what is left. The tank is a
    // candidate, and Death's Echo is not looked at (ruling 42). nullopt: nobody.
    inline std::optional<std::size_t> PickIsolated(std::vector<Candidate> const& c, float radius, float zBand,
        float roll01)
    {
        if (c.empty())
            return std::nullopt;
        std::vector<std::uint32_t> allies;
        allies.reserve(c.size());
        std::uint32_t fewest = UINT32_MAX;
        for (std::size_t i = 0; i < c.size(); ++i)
        {
            allies.push_back(AlliesNear(c, i, radius, zBand));
            fewest = std::min(fewest, allies.back());
        }
        float farthest = -1.f;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (allies[i] == fewest)
                farthest = std::max(farthest, c[i].distToBoss);
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (allies[i] == fewest && c[i].distToBoss >= farthest - 0.5f)
                pool.push_back(i);
        std::size_t const pick = std::min(pool.size() - 1,
            static_cast<std::size_t>(std::clamp(roll01, 0.f, 0.9999f) * static_cast<float>(pool.size())));
        return pool[pick];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BA2 / BA3 Death Knell and Death's Echo
    // ----------------------------------------------------------------------------------------------------------------

    // The candidates (indices) within `radius` and `zBand` of the Knell's center: the doomed and everyone close.
    inline std::vector<std::size_t> KnellInside(std::vector<Candidate> const& c, Vec2 center, float centerZ,
        float radius, float zBand)
    {
        std::vector<std::size_t> inside;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (DungeonKit::Distance(c[i].pos, center) <= radius && std::fabs(c[i].z - centerZ) <= zBand)
                inside.push_back(i);
        return inside;
    }

    // `total` split evenly among the takers, each share x (1 + 1.0 x its Echo stacks): 90% of 3,670 is 3,303 alone,
    // 1,652 and 1,651 for two, 1,101 each for three; a taker with one stack takes two even shares. Same rule as
    // DungeonKit::WeightedShares.
    inline std::vector<std::uint32_t> KnellShares(std::uint32_t total, std::vector<std::uint32_t> const& echoStacks)
    {
        return DungeonKit::WeightedSplit(total, echoStacks, kEchoPerStack);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cast plan: BA4, BA6, BA7 and the stock Banshee Wail on one queue (the CastQueue of the kit)
    // ----------------------------------------------------------------------------------------------------------------

    class CastPlan
    {
    public:
        using Ms = std::uint64_t;

        enum Cast : std::uint32_t
        {
            Wail        = 1,
            Visage      = 2,
            Lament      = 3,
            BansheeWail = 4,
        };

        static constexpr std::uint8_t kPriorityFiller = 0;
        static constexpr std::uint8_t kPriorityMechanic = 2;
        static constexpr std::uint8_t kPriorityLament = 3;      // the interruptible cast goes first when two are due

        CastPlan() : _queue(kCastSpacingMs) { Reset(false); }

        // The pull (or a reset): the first casts at their ST times; the Lament on heroic only.
        void Reset(bool heroic)
        {
            _heroic = heroic;
            _queue = DungeonKit::CastQueue(kCastSpacingMs);
            _nominal.fill(0);
            Arm(Wail, kWail.first);
            Arm(Visage, kVisage.first);
            if (heroic)
                Arm(Lament, kLament.first);
            _queue.Schedule(BansheeWail, kBansheeWail.first, kPriorityFiller, kFillerDropAfterMs);
        }

        bool Heroic() const { return _heroic; }

        static constexpr Ms CastMs(Cast c, bool heroic)
        {
            switch (c)
            {
                case Wail:          return kWailCastMs;
                case Visage:        return kVisageCastMs(heroic);
                case Lament:        return kLamentCastMs;
                case BansheeWail:   return kStockBansheeWailCastMs;
            }
            return 0;
        }

        static constexpr Ms Every(Cast c)
        {
            switch (c)
            {
                case Wail:          return kWail.every;
                case Visage:        return kVisage.every;
                case Lament:        return kLament.every;
                case BansheeWail:   return kBansheeWail.every;
            }
            return 0;
        }

        // The cast to start now, if any. The stock Banshee Wail comes back only when no mechanic cast is due within its
        // cast time (a filler never delays a mechanic); one that waited too long is dropped and its next turn booked.
        std::optional<Cast> Next(Ms now)
        {
            for (std::uint32_t const id : _queue.DropStale(now))
                if (id == BansheeWail)
                    _queue.Schedule(BansheeWail, now + kBansheeWail.every, kPriorityFiller, kFillerDropAfterMs);
            std::optional<std::uint32_t> const next = _queue.Next(now);
            if (!next)
                return std::nullopt;
            Cast const cast = static_cast<Cast>(*next);
            if (cast == BansheeWail && MechanicDueWithin(now, kStockBansheeWailCastMs + kFillerMarginMs))
                return std::nullopt;
            return cast;
        }

        // `cast` began at `now`: it holds the caster for its cast time, and the next one is booked from its planned
        // time (a start that slipped behind another cast does not push the cadence; a stock filler counts from its
        // start).
        void Started(Cast cast, Ms now)
        {
            bool const filler = cast == BansheeWail;
            _queue.Started(cast, now, CastMs(cast, _heroic), !filler);
            if (filler)
            {
                _queue.Schedule(cast, now + Every(cast), kPriorityFiller, kFillerDropAfterMs);
                return;
            }
            Ms next = _nominal[cast] + Every(cast);
            if (next < now)
                next = now;
            Arm(cast, next);
        }

        // The cast was refused (a silence, no target): try again soon, the cadence unchanged.
        void Refused(Cast cast, Ms now)
        {
            _queue.Schedule(cast, now + kCastRetryMs, PriorityOf(cast), cast == BansheeWail ? kFillerDropAfterMs : 0);
        }

        // Her current cast ended early at `now` (interrupted, cancelled).
        void Interrupted(Ms now) { _queue.Interrupted(now); }

        // When `cast` is next planned (nullopt: not queued).
        std::optional<Ms> DueAt(Cast cast) const { return _queue.DueAt(cast); }

    private:
        static constexpr std::uint8_t PriorityOf(Cast c)
        {
            return c == BansheeWail ? kPriorityFiller : (c == Lament ? kPriorityLament : kPriorityMechanic);
        }

        void Arm(Cast cast, Ms at)
        {
            _nominal[cast] = at;
            _queue.Schedule(cast, at, PriorityOf(cast));
        }

        bool MechanicDueWithin(Ms now, Ms window) const
        {
            for (Cast const c : { Wail, Visage, Lament })
                if (std::optional<Ms> const due = _queue.DueAt(c); due && *due <= now + window)
                    return true;
            return false;
        }

        bool _heroic = false;
        DungeonKit::CastQueue _queue;
        std::array<Ms, 5> _nominal{};
    };
}

#endif
