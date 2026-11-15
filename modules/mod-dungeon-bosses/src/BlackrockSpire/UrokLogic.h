/*
 * mod-dungeon-bosses, Blackrock Spire B5: Urok Doomhowl (10584), "Stolen Magic", the pure, host-testable part (no
 * engine headers). Build spec SP 1630-1688 (docs/dungeons/blackrock-spire-rework.md, rulings 37-39), handoff section
 * 3.4 rows UR and 3.5 row B5. Tested by tests/brs_urok_test.cpp; the engine side is boss_urok_doomhowl_rework.cpp and
 * the shard helpers B8 / B9 reuse are UrokShards.h.
 *
 *   Spells         the WP's ids, inside kSpellsUrok (210150-210179), declared in apps/dbc-tools
 *                  source/npcs/blackrock_spire/urok.py
 *   Tuning         NH<> constants and Cadence{first, every}, straight from the build spec
 *   Rounds         UR1 the Challenge: 3 rounds of 1 Enforcer + 1 Magus from the stock circles at 2.5 / 12.5 / 22.5 s
 *   PreludeClock   UR1 the rounds due, the ogres killed, Urok's arrival (5 s after the last ogre dies, at most 50 s)
 *   Stolen Power   UR5 the cap (8 normal, 5 heroic then Overcharge), the prelude's pile stacks at his arrival
 *   UnstableBook   UR10 heroic: per carrier, the stacks and the 6 s fuse from the first stack (not refreshed)
 *   LaunchDelayMs  UR6 the Wild Bolt missile leaves so it lands as the circle resolves
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_UROK_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_UROK_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace BrsUrok
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point4;
    using DungeonKit::NH;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsUrok;

    enum UrokSpells : std::uint32_t
    {
        SPELL_UR_WAROSHS_POWER      = kSpellSlice.first + 0,    // 210150 UR4 +5% damage / healing a stack, 3, 20 s
        SPELL_UR_STOLEN_POWER       = kSpellSlice.first + 1,    // 210151 UR5 +5% damage done a stack (B9 reuses)
        SPELL_UR_SHARD_RECLAIM      = kSpellSlice.first + 2,    // 210152 UR5 the look as a shard reaches its goal
        SPELL_UR_WILD_BOLT          = kSpellSlice.first + 3,    // 210153 UR6 the hit (resolve copy, Arcane)
        SPELL_UR_WILD_BOLT_MISSILE  = kSpellSlice.first + 4,    // 210154 UR6 the missile to the spot (look only)
        SPELL_UR_WILD_BOLT_LANDING  = kSpellSlice.first + 5,    // 210155 UR6 the landing look (the new shard casts it)
        SPELL_UR_DOOMHOWL_CAST      = kSpellSlice.first + 6,    // 210156 UR7 the 2.5 s cast bar
        SPELL_UR_DOOMHOWL           = kSpellSlice.first + 7,    // 210157 UR7 the hit (resolve copy, Physical)
        SPELL_UR_DOOMHOWL_FEAR      = kSpellSlice.first + 8,    // 210158 UR7 the 2 s fear rider
        SPELL_UR_DOOMHOWL_LOOK      = kSpellSlice.first + 9,    // 210159 UR7 the roar's look (self)
        SPELL_UR_OVERCHARGE_CAST    = kSpellSlice.first + 10,   // 210160 UR9 the 3 s cast bar (heroic; B9 reuses)
        SPELL_UR_OVERCHARGE         = kSpellSlice.first + 11,   // 210161 UR9 the hit (resolve copy, Arcane)
        SPELL_UR_OVERCHARGE_LOOK    = kSpellSlice.first + 12,   // 210162 UR9 the nova's look (self)
        SPELL_UR_UNSTABLE           = kSpellSlice.first + 13,   // 210163 UR10 the carrier's stacks (heroic)
        SPELL_UR_UNSTABLE_LOOK      = kSpellSlice.first + 14,   // 210164 UR10 the rune, re-cast every 2.5 s (self)
        SPELL_UR_UNSTABLE_BURST     = kSpellSlice.first + 15,   // 210165 UR10 the burst (resolve copy, Arcane)
        // 210166-210179 spare
    };
    static_assert(SPELL_UR_UNSTABLE_BURST <= kSpellSlice.last, "Urok's spells must stay in his slice");

    // Stock spells he and his ogres keep (DD scales them on heroic).
    inline constexpr std::uint32_t SPELL_UR_REND = 16509;           // UR8 bleed on his victim
    inline constexpr std::uint32_t SPELL_UR_STRIKE = 15580;         // UR8 weapon hit on his victim
    inline constexpr std::uint32_t SPELL_UR_ARRIVAL = 16473;        // the stock arrival look (Urok Spawn, on himself)
    inline constexpr std::uint32_t SPELL_UR_OGRE_TELEPORT = 12980;  // Simple Teleport: an ogre's arrival look
    inline constexpr std::uint32_t SPELL_UR_MAGUS_SLOW = 13747;     // the Magi's Slow (Magic): the dispel reward

    // creature_text groups of 10584 (BlackrockSpireRework.h kTextRanges: 0-5, 0-1 stock).
    enum UrokTexts : std::uint8_t
    {
        SAY_UR_SUMMON       = 0,    // yell, stock: "You have summoned me, fool! Now DIE!" (his arrival)
        SAY_UR_AGGRO        = 1,    // say, stock, never called before: "Me smash! You die!" (the pull)
        EMOTE_UR_DOOMHOWL   = 2,    // "%s draws a deep breath!"
        EMOTE_UR_RECLAIM    = 3,    // "%s drinks in the stolen magic!"
        EMOTE_UR_OVERCHARGE = 4,    // "The stolen magic boils inside %s!" (heroic)
        SAY_UR_DEATH        = 5,    // yell: "Magic... was... Urok's..."
    };

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum UrokTags : std::uint32_t
    {
        TAG_UR_SHARD        = 1,    // UR3 (the pickup Soak)
        TAG_UR_WILD_BOLT    = 2,    // UR6
        TAG_UR_DOOMHOWL     = 3,    // UR7
        TAG_UR_OVERCHARGE   = 4,    // UR9
        TAG_UR_UNSTABLE     = 5,    // UR10 (the RunOut and the carrier's hit)
    };

    // DoAction on Urok: the pile was used, run the Challenge (he starts hidden and arrives at its end).
    inline constexpr std::int32_t ACTION_UR_CHALLENGE = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP 1547-1616, 1647-1660; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // First start and cadence of a beat, in ms since the pull. Cadences count start to start.
    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    struct MsRange
    {
        std::uint32_t min;
        std::uint32_t max;
    };

    // `r` in [0, 1): a point of the range.
    constexpr std::uint32_t InRange(MsRange range, float r)
    {
        float const span = static_cast<float>(range.max - range.min);
        return range.min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 1.f) * span);
    }

    // UR3 Stolen Magic: a shard is taken on touch (2 yd); left alone it waits 10 s (heroic 7 s), then crawls to its
    // goal (the pile during the prelude, Urok once he is out) at 3 yd/s, still grabbable on the way.
    inline constexpr float kShardRadiusYd = 2.f;
    inline constexpr NH<std::uint32_t> kShardWaitMs{ 10000, 7000 };
    inline constexpr float kShardCrawlYdPerSec = 3.f;
    inline constexpr float kShardReachYd = 1.5f;

    // UR4 Warosh's Power: +5% damage and healing done a stack, up to 3, 20 s, refreshed by every grab.
    inline constexpr std::uint32_t kWaroshMaxStacks = 3;
    inline constexpr std::uint32_t kWaroshMs = 20000;
    inline constexpr std::int32_t kWaroshPctPerStack = 5;

    // UR5 Stolen Power: +5% damage done a stack for the rest of the fight; 8 at most (heroic 5, then Overcharge).
    inline constexpr NH<std::uint32_t> kStolenPowerCap{ 8, 5 };
    inline constexpr std::int32_t kStolenPowerPctPerStack = 5;

    // UR6 Wild Bolt: first 6 s, every 10 s; a 6 yd blast within 8 yd of each of 1 / 2 random non-tanks, 2 s flight.
    inline constexpr Cadence kWildBoltCadence{ 6000, 10000 };
    inline constexpr FlexAB kWildBoltTargets{ 1, 2 };
    inline constexpr std::uint32_t kWildBoltWarnMs = 2000;
    inline constexpr float kWildBoltRadiusYd = 6.f;
    inline constexpr float kWildBoltScatterYd = 8.f;
    inline constexpr NH<float> kWildBoltPct{ 25.f, 30.f };
    inline constexpr float kWildBoltMissileSpeed = 30.f;            // = urok.py's missile Speed (yd/s)
    inline constexpr float kWildBoltTargetRangeYd = 80.f;           // non-tanks this near him can be picked

    // UR7 Doomhowl: first 15 s, every 20 s; a 2.5 s cast (emote line 2), then 12 yd around him, the tank exempt,
    // 20% / 30%, Weakened and a 2 s fear.
    inline constexpr Cadence kDoomhowlCadence{ 15000, 20000 };
    inline constexpr std::uint32_t kDoomhowlCastMs = 2500;
    inline constexpr float kDoomhowlRadiusYd = 12.f;
    inline constexpr NH<float> kDoomhowlPct{ 20.f, 30.f };
    inline constexpr std::uint32_t kDoomhowlFearMs = 2000;

    // UR8 Rend 16509 and Strike 15580 on his victim (the stock timers).
    inline constexpr MsRange kRendFirst{ 17000, 20000 };
    inline constexpr MsRange kStrikeFirst{ 10000, 12000 };
    inline constexpr MsRange kTankHitEvery{ 8000, 10000 };

    // UR9 Overcharge (heroic): at 5 Stolen Power, a 3 s cast (emote line 4), then 40% to every player, stacks to 0.
    inline constexpr std::uint32_t kOverchargeCastMs = 3000;
    inline constexpr float kOverchargePct = 40.f;
    inline constexpr float kOverchargeRangeYd = 100.f;              // every player this near him (the whole plateau)

    // UR10 Unstable (heroic): every grab adds a stack; 6 s after the first (later grabs do not reset it) the carrier
    // bursts: 10% a stack to the carrier (no Weakened), 30% and Weakened to everyone else within 8 yd + 2 a stack past
    // the first. Anyone may grab a 2nd and a 3rd shard in the window (SP: more power and denial, paid for in the
    // carrier's health and a wider burst); bots grab only at 0 or 1 stack (the pickup's claim order, bot-only).
    inline constexpr std::uint32_t kUnstableFuseMs = 6000;
    inline constexpr float kUnstableBaseRadiusYd = 8.f;
    inline constexpr float kUnstablePerStackYd = 2.f;
    inline constexpr float kUnstableCarrierPctPerStack = 10.f;
    inline constexpr float kUnstableOthersPct = 30.f;
    inline constexpr std::uint8_t kUnstableGrabMaxStacks = 2;       // Eligibility maxStacks: anyone grabs at 0 to 2
    inline constexpr std::uint8_t kUnstableBotCapStacks = 2;        // Ordering capStacks: bots stop at 2 (claim only)
    inline constexpr std::uint32_t kUnstableLookEveryMs = 2500;     // SV 969 is a 2.5 s rune: re-cast it

    constexpr float UnstableRadius(std::uint32_t stacks)
    {
        return kUnstableBaseRadiusYd + kUnstablePerStackYd * static_cast<float>(stacks > 0 ? stacks - 1 : 0);
    }

    constexpr float UnstableCarrierPct(std::uint32_t stacks)
    {
        return kUnstableCarrierPctPerStack * static_cast<float>(stacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR1 The Challenge (the prelude)
    // ----------------------------------------------------------------------------------------------------------------

    // The six stock summoning circles [db: smart_scripts 17558400], in stock order.
    inline constexpr std::array<Point4, 6> kCircles{ {
        { -14.36f, -389.37f, 48.78f, 0.f }, { -27.43f, -372.86f, 49.36f, 0.f }, { -19.78f, -372.75f, 49.25f, 0.f },
        { -31.67f, -385.91f, 48.65f, 0.f }, { -37.13f, -369.65f, 50.63f, 0.f }, { -46.26f, -376.98f, 50.51f, 0.f } } };

    // A round: 1 Enforcer and 1 Magus, each from its circle (stock's first wave spots first).
    struct OgreRound
    {
        std::uint32_t atMs;
        std::size_t enforcerCircle;
        std::size_t magusCircle;
    };

    inline constexpr std::array<OgreRound, 3> kRounds{ {
        { 2500, 2, 4 }, { 12500, 0, 1 }, { 22500, 5, 3 } } };
    inline constexpr std::uint32_t kPreludeOgres = 2 * kRounds.size();
    inline constexpr std::uint32_t kArrivalAfterLastDeathMs = 5000;
    inline constexpr std::uint32_t kArrivalCapMs = 50000;
    inline constexpr std::uint32_t kOgreOutOfCombatFailMs = 30000;  // stock: an ogre left 30 s fails the challenge
    inline constexpr std::uint32_t kNobodyFailMs = 15000;           // no living player on the plateau this long: fail
    inline constexpr float kArrivalPullRangeYd = 100.f;             // stock: he pulls everyone within 100 yd
    inline constexpr float kOgreAggroRangeYd = 100.f;               // a new ogre goes for the nearest player this near
    inline constexpr std::uint32_t kPileSelectPollMs = 1000;        // the pile GO re-reads its state this often

    // When Urok arrives: 5 s after the sixth ogre died (never before the last round is out), at most at 50 s.
    constexpr std::uint32_t ArrivalAtMs(std::uint32_t ogresDead, std::uint32_t lastDeathMs)
    {
        if (ogresDead >= kPreludeOgres)
            return std::min(kArrivalCapMs, lastDeathMs + kArrivalAfterLastDeathMs);
        return kArrivalCapMs;
    }

    // The prelude's clock: rounds due, ogres killed, the arrival. Pure; the AI calls Update every tick.
    class PreludeClock
    {
    public:
        void Start()
        {
            *this = PreludeClock();
            _running = true;
        }

        void Stop() { _running = false; }
        bool Running() const { return _running; }
        std::uint32_t Now() const { return _nowMs; }
        std::uint32_t RoundsOut() const { return _roundsOut; }
        std::uint32_t OgresDead() const { return _ogresDead; }

        // Advances the clock; returns the rounds that came due (indices into kRounds, in order).
        std::vector<std::size_t> Update(std::uint32_t elapsedMs)
        {
            std::vector<std::size_t> due;
            if (!_running)
                return due;
            _nowMs += elapsedMs;
            while (_roundsOut < kRounds.size() && _nowMs >= kRounds[_roundsOut].atMs)
                due.push_back(_roundsOut++);
            return due;
        }

        void OgreDied()
        {
            if (_ogresDead < kPreludeOgres)
                ++_ogresDead;
            _lastDeathMs = _nowMs;
        }

        std::uint32_t ArrivalAt() const { return ArrivalAtMs(_ogresDead, _lastDeathMs); }
        bool ArrivalDue() const { return _running && _nowMs >= ArrivalAt(); }

    private:
        std::uint32_t _nowMs = 0;
        std::uint32_t _roundsOut = 0;
        std::uint32_t _ogresDead = 0;
        std::uint32_t _lastDeathMs = 0;
        bool _running = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // UR5 Stolen Power, UR9 Overcharge
    // ----------------------------------------------------------------------------------------------------------------

    // A shard reached him: one more stack, held at the cap.
    constexpr std::uint32_t StolenPowerAfterReach(std::uint32_t before, bool heroic)
    {
        return std::min(before + 1, kStolenPowerCap(heroic));
    }

    // UR2: the prelude's shards that reached the pile become stacks when he arrives (at most the cap).
    constexpr std::uint32_t StacksAtArrival(std::uint32_t atPile, bool heroic)
    {
        return std::min(atPile, kStolenPowerCap(heroic));
    }

    // Heroic: he overcharges at the cap (5), unless a cast already holds him (he starts it when free).
    constexpr bool OverchargeDue(std::uint32_t stacks, bool heroic, bool busy)
    {
        return heroic && !busy && stacks >= kStolenPowerCap(true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR6 Wild Bolt's missile
    // ----------------------------------------------------------------------------------------------------------------

    // The missile leaves this long after the circle is placed so it lands as the circle resolves (now when the flight
    // takes the whole warning or more).
    constexpr std::uint32_t LaunchDelayMs(std::uint32_t warnMs, float distanceYd, float speedYdPerSec)
    {
        if (speedYdPerSec <= 0.f || distanceYd <= 0.f)
            return warnMs;
        float const flightMs = distanceYd / speedYdPerSec * 1000.f;
        if (flightMs >= static_cast<float>(warnMs))
            return 0;
        return warnMs - static_cast<std::uint32_t>(flightMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UR10 Unstable (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    struct UnstableFuse
    {
        std::uint64_t carrier = 0;      // raw guid
        std::uint32_t stacks = 0;
        std::uint64_t burstAtMs = 0;
    };

    // The carriers' fuses: a grab adds a stack, the first stack lights a 6 s fuse that later grabs do not reset.
    class UnstableBook
    {
    public:
        // A grab by `carrier` at `nowMs`: the carrier's fuse after it.
        UnstableFuse Grab(std::uint64_t carrier, std::uint64_t nowMs)
        {
            for (UnstableFuse& f : _fuses)
                if (f.carrier == carrier)
                {
                    ++f.stacks;
                    return f;
                }
            _fuses.push_back({ carrier, 1, nowMs + kUnstableFuseMs });
            return _fuses.back();
        }

        // The fuses that burn out at `nowMs` (removed from the book).
        std::vector<UnstableFuse> TakeDue(std::uint64_t nowMs)
        {
            std::vector<UnstableFuse> due;
            for (auto it = _fuses.begin(); it != _fuses.end();)
            {
                if (nowMs >= it->burstAtMs)
                {
                    due.push_back(*it);
                    it = _fuses.erase(it);
                }
                else
                    ++it;
            }
            return due;
        }

        std::uint32_t Stacks(std::uint64_t carrier) const
        {
            for (UnstableFuse const& f : _fuses)
                if (f.carrier == carrier)
                    return f.stacks;
            return 0;
        }

        std::uint64_t Remaining(std::uint64_t carrier, std::uint64_t nowMs) const
        {
            for (UnstableFuse const& f : _fuses)
                if (f.carrier == carrier)
                    return f.burstAtMs > nowMs ? f.burstAtMs - nowMs : 0;
            return 0;
        }

        std::vector<UnstableFuse> const& All() const { return _fuses; }
        void Clear() { _fuses.clear(); }
        std::size_t Size() const { return _fuses.size(); }

    private:
        std::vector<UnstableFuse> _fuses;
    };

    // Bots' kill order in the prelude (SP "Boss data"): the Magi first (they carry the shards and the Slow), then the
    // Enforcers; Urok alone after.
    inline constexpr std::int8_t kMagusPriority = 3;
    inline constexpr std::int8_t kEnforcerPriority = 2;
    inline constexpr std::uint8_t kSlowDispelPriority = 1;
}

#endif
