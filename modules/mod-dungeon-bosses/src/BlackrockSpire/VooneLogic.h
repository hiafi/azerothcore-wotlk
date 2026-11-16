/*
 * mod-dungeon-bosses, Blackrock Spire B3:
 * War Master Voone (9237), the pure, host-testable part (no engine headers). Build spec SP "War Master Voone"
 * (docs/dungeons/blackrock-spire-rework.md, VO1-VO13), handoff sections 3.4 (rows VO), 3.5 (row B3), 3.6, 3.8 (the
 * troll hall frame). Tested by tests/brs_voone_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsVoone (210090-210119), declared in apps/dbc-tools
 *                  source/npcs/blackrock_spire/voone.py
 *   Tuning         NH<> constants and FlexAB pairs, straight from the build spec
 *   StanceClock    VO2 Brawler, Thrasher, War Master on a 30 s (heroic 25 s) timer; the throw beat inside each stance
 *                  (VO3 6 s, VO4 10 s, VO5 8 s, the first 3 s in); a throw never lands after its stance ends
 *   AxeBook        the stuck axes (VO6): the cap, the oldest first, recalled ones, the lanes' geometry
 *   BerserkClock   VO10 / VO12 Berserking: the War Master stance and the War Cry's 10 s, whichever ends later
 *   HoldReleased   VO1 after the charge he holds in the hall until the group arrives (his quarters have one gate,
 *                  97 yd of floor from the hall); HoldThrow* answers damage from beyond 12 yd while he holds
 *   FightArena     the leash: his quarters, the troll hall and the walk between them
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_VOONE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_VOONE_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace BrsVoone
{
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsVoone;

    enum VooneSpells : std::uint32_t
    {
        SPELL_VO_AXE_THROW      = kSpellSlice.first + 0,    // 210090 VO3 the Brawler lane's hit (resolve copy)
        SPELL_VO_AXE_FAN        = kSpellSlice.first + 1,    // 210091 VO4 the Thrasher fan's hit (resolve copy)
        SPELL_VO_AXE_RAIN       = kSpellSlice.first + 2,    // 210092 VO5 the War Master rain's hit (resolve copy)
        SPELL_VO_RECALL_HIT     = kSpellSlice.first + 3,    // 210093 VO7 a Recall lane's hit (resolve copy)
        SPELL_VO_CHAIN_HIT      = kSpellSlice.first + 4,    // 210094 VO11 a chain crossing's hit (resolve copy)
        SPELL_VO_AXE_FLIGHT     = kSpellSlice.first + 5,    // 210095 look: an axe flies from him to a point
        SPELL_VO_AXE_RETURN     = kSpellSlice.first + 6,    // 210096 look: a stuck axe flies from its spot to him
        SPELL_VO_CHAINED_AXE    = kSpellSlice.first + 7,    // 210097 VO11 the chain beam (aura channeled at him)
        SPELL_VO_WAR_CRY        = kSpellSlice.first + 8,    // 210098 VO12 the 2.5 s interruptible cast (heroic)
        SPELL_VO_BERSERKING     = kSpellSlice.first + 9,    // 210099 VO10 +30% attack speed
        SPELL_VO_CHARGE         = kSpellSlice.first + 10,   // 210100 VO1 the charge's look (Berserker Charge)
        SPELL_VO_RECALL_BAR     = kSpellSlice.first + 11,   // 210101 VO7 the 3 s cast bar naming the Recall
        // 210102-210119 spare
    };
    static_assert(SPELL_VO_RECALL_BAR <= kSpellSlice.last, "Voone's spells must stay in his slice");

    // Stock kit kept (VO8 / VO9; DD scales them on heroic once 229 is in Heroic.Maps).
    inline constexpr std::uint32_t SPELL_VO_THRASH = 3391;
    inline constexpr std::uint32_t SPELL_VO_CLEAVE = 15284;
    inline constexpr std::uint32_t SPELL_VO_MORTAL_STRIKE = 16856;

    // The Chain Anchor (BlackrockSpireRework.h NPC_BRS_CHAIN_ANCHOR 300704) and the Stuck Axe gameobject
    // (GO_BRS_STUCK_AXE 301250, display 8494) are named in the shared header; the script reads them from there.

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum VooneTags : std::uint32_t
    {
        TAG_VO_AXE_THROW    = 3,
        TAG_VO_AXE_FAN      = 4,
        TAG_VO_AXE_RAIN     = 15,   // VO5, numbered off 5 (the G1 drill's chain tag) so a mixed ledger reads clean
        TAG_VO_RECALL       = 7,
        TAG_VO_CLEAVE       = 9,
        TAG_VO_CHAINS       = 11,
        TAG_VO_PARK         = 14,
        TAG_VO_HOLD_THROW   = 16,   // VO1 the hold's answer to a ranged attacker (R-1 ruling 1)
    };

    // creature_text group ids of 9237 (the SQL rev writes them; SP "Text").
    enum VooneTexts : std::uint8_t
    {
        YELL_VOONE_PULL         = 0,    // VO1
        YELL_VOONE_BRAWLER      = 1,    // VO2
        YELL_VOONE_THRASHER     = 2,
        YELL_VOONE_WAR_MASTER   = 3,
        EMOTE_VOONE_RECALL      = 4,    // VO7 "%s calls his axes home!" (type 41, a boss emote)
        YELL_VOONE_DEATH        = 5,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Stances (VO2)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Stance : std::uint8_t
    {
        Brawler = 0,        // Thrash; the single throw
        Thrasher = 1,       // Mortal Strike, Cleave; the fan
        WarMaster = 2,      // Berserking; the rain
    };
    inline constexpr std::uint8_t kStanceCount = 3;

    inline constexpr char const* StanceName(Stance s)
    {
        return s == Stance::Brawler ? "brawler" : (s == Stance::Thrasher ? "thrasher" : "war-master");
    }

    inline constexpr std::uint8_t NextStance(std::uint8_t stance)
    {
        return static_cast<std::uint8_t>((stance + 1) % kStanceCount);
    }

    // Each stance lasts 30 s (heroic 25 s) and ends in a Recall (the stance change).
    inline constexpr NH<std::uint32_t> kStanceMs{ 30000, 25000 };

    // VO3 / VO4 / VO5: the first throw 3 s into the stance, then 6 s / 10 s / 8 s; the lanes and circles warn 2 s.
    inline constexpr std::uint32_t kThrowFirstMs = 3000;
    inline constexpr std::uint32_t kThrowWarnMs = 2000;
    inline constexpr std::uint32_t ThrowEveryMs(Stance s)
    {
        return s == Stance::Brawler ? 6000u : (s == Stance::Thrasher ? 10000u : 8000u);
    }

    // The counts, "a / b" at 5 players / 6 or more (ruling 8).
    inline constexpr FlexAB kThrowLanes{ 1, 2 };        // VO3 Brawler: axes a throw (one lane each)
    inline constexpr FlexAB kFanCount{ 1, 2 };          // VO4 Thrasher: fans a volley (three lanes each)
    inline constexpr FlexAB kRainCount{ 2, 4 };         // VO5 War Master: circles a volley
    inline constexpr std::uint32_t kFanLanes = 3;
    inline constexpr FlexAB kStuckCapNormal{ 6, 8 };    // VO6
    inline constexpr FlexAB kStuckCapHeroic{ 8, 10 };

    inline constexpr std::uint32_t StuckCap(bool heroic, std::uint32_t players)
    {
        return (heroic ? kStuckCapHeroic : kStuckCapNormal).At(players);
    }

    // Axes one throw puts on the floor in `stance` at `players`.
    inline constexpr std::uint32_t AxesPerThrow(Stance stance, std::uint32_t players)
    {
        return stance == Stance::Brawler ? static_cast<std::uint32_t>(kThrowLanes.At(players))
            : (stance == Stance::Thrasher ? static_cast<std::uint32_t>(kFanCount.At(players)) * kFanLanes
                : static_cast<std::uint32_t>(kRainCount.At(players)));
    }

    // Damage, % of the reference health row (normal 3,670 non-tank / heroic 4,120); Weakened on every hit.
    inline constexpr NH<float> kAxePct{ 30.f, 40.f };       // VO3, VO4, VO5
    inline constexpr NH<float> kRecallPct{ 30.f, 40.f };    // VO7
    inline constexpr float kChainPct = 10.f;                // VO11 (heroic only)

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry (SP VO3 / VO4 / VO5 / VO7 / VO11, the G1 drill's lines)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kLaneWidth = 4.f;
    inline constexpr float kLaneLength = 30.f;
    inline constexpr float kFanSpreadDeg = 30.f;
    inline constexpr float kRainRadius = 4.f;
    // A lane the room's edge cuts short stops this far inside it, but never shorter than kMinLaneYd.
    inline constexpr float kLaneInsetYd = 1.f;
    inline constexpr float kMinLaneYd = 6.f;

    // VO7: every lane is 4 yd wide and stops 5 yd short of him; warnings 3 s (the stance change), 1.5 s (War Cry),
    // 2 s (the cap's one lane). The G1 drill's tag 7 line is `line 5 1500 width=4 exclude=5`
    // (blackrock-spire-followups).
    inline constexpr float kRecallWidth = 4.f;
    inline constexpr float kRecallExcludeSourceEnd = 5.f;
    inline constexpr std::uint32_t kRecallWarnMs = 3000;
    inline constexpr std::uint32_t kEarlyRecallWarnMs = 1500;
    inline constexpr std::uint32_t kCapRecallWarnMs = 2000;
    // The flying axes' look: the missile speeds (yd/s) of SPELL_VO_AXE_RETURN and SPELL_VO_AXE_FLIGHT (dbc-tools
    // voone.py): a 30 yd lane in the stance change's 3 s warning, and in a throw's 2 s warning.
    inline constexpr float kReturnMissileSpeed = 10.f;
    inline constexpr float kThrowMissileSpeed = 15.f;

    // VO11 (heroic): a 2 yd chain from every stuck axe to him; 10% once per chain every 2 s. The G1 drill's tag 5 line
    // is `line 5 2000 width=2 ... persist=6000 tick=2000 pct=10`. The first crossing tick is 2 s after the axe lands.
    inline constexpr float kChainWidth = 2.f;
    inline constexpr std::uint32_t kChainTickMs = 2000;
    inline constexpr std::uint32_t kChainWarnMs = 2000;
    inline constexpr std::uint32_t kChainLifeMs = 180000;       // cancelled with the axe; the cap on a lost handle
    // SP gives the chain no source-end exclusion (the Recall has 5 yd): 0 keeps the build spec; a designer who wants
    // the melee at his side spared sets it (report, designer question 2).
    inline constexpr float kChainExcludeSourceEnd = 0.f;

    // The facing (radians, the map's orientation) of `from` toward `aim`, or `fallback` when the two points coincide
    // (a target standing on him).
    inline float LaneFacing(Vec2 from, Vec2 aim, float fallback)
    {
        if (DungeonKit::Distance(from, aim) < 0.5f)
            return fallback;
        return DungeonKit::BearingTo(from, aim);
    }

    inline float NormalizeFacing(float facing)
    {
        while (facing < 0.f)
            facing += DungeonKit::kTwoPi;
        while (facing >= DungeonKit::kTwoPi)
            facing -= DungeonKit::kTwoPi;
        return facing;
    }

    // VO4: three lanes 30 degrees apart, the middle one on `base`.
    inline std::array<float, 3> FanFacings(float base)
    {
        float const spread = kFanSpreadDeg * DungeonKit::kPi / 180.f;
        return { NormalizeFacing(base - spread), NormalizeFacing(base), NormalizeFacing(base + spread) };
    }

    // The length of a lane: kLaneLength, cut to stay kLaneInsetYd inside the room's edge (`edgeYd`: the distance to
    // the edge along the ray, nullopt: none met), never under kMinLaneYd.
    inline float LaneLength(std::optional<float> edgeYd)
    {
        if (!edgeYd)
            return kLaneLength;
        return std::clamp(*edgeYd - kLaneInsetYd, kMinLaneYd, kLaneLength);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stance clock (VO2 and the throw beat)
    // ----------------------------------------------------------------------------------------------------------------

    class StanceClock
    {
    public:
        static constexpr std::uint64_t kNever = std::numeric_limits<std::uint64_t>::max();

        // Brawler starts now.
        void Start(std::uint64_t nowMs, bool heroic)
        {
            _heroic = heroic;
            _index = 0;
            _startMs = nowMs;
            _changes = 0;
            ArmThrow();
        }

        Stance Current() const { return static_cast<Stance>(_index); }
        std::uint64_t StartMs() const { return _startMs; }
        std::uint32_t LengthMs() const { return kStanceMs(_heroic); }
        std::uint64_t EndMs() const { return _startMs + LengthMs(); }
        std::uint32_t Changes() const { return _changes; }
        std::uint64_t NextThrowMs() const { return _nextThrowMs; }

        // True once per stance change (a late tick skips no stance's start: the clock stays aligned to the stance
        // grid and reports one change for the lot).
        bool Advance(std::uint64_t nowMs)
        {
            if (nowMs < EndMs())
                return false;
            while (nowMs >= EndMs())
            {
                _startMs = EndMs();
                _index = NextStance(_index);
                ++_changes;
            }
            ArmThrow();
            return true;
        }

        // A throw is due when its time came and it would land (kThrowWarnMs later) before the stance ends.
        bool ThrowDue(std::uint64_t nowMs) const
        {
            return _nextThrowMs != kNever && nowMs >= _nextThrowMs && _nextThrowMs + kThrowWarnMs <= EndMs();
        }

        void ThrowFired() { _nextThrowMs += ThrowEveryMs(Current()); }

        // The throws a whole stance of this clock fires (host tests, the report).
        std::uint32_t ThrowsPerStance(Stance stance) const
        {
            std::uint32_t n = 0;
            for (std::uint64_t t = kThrowFirstMs; t + kThrowWarnMs <= LengthMs(); t += ThrowEveryMs(stance))
                ++n;
            return n;
        }

    private:
        void ArmThrow() { _nextThrowMs = _startMs + kThrowFirstMs; }

        bool _heroic = false;
        std::uint8_t _index = 0;
        std::uint32_t _changes = 0;
        std::uint64_t _startMs = 0;
        std::uint64_t _nextThrowMs = kNever;
    };

    // A stock cast's own clock: armed at its first time, due until fired, then every `every` ms.
    class BeatClock
    {
    public:
        static constexpr std::uint64_t kNever = StanceClock::kNever;

        void Arm(std::uint64_t atMs) { _dueMs = atMs; }
        void Disarm() { _dueMs = kNever; }
        bool Due(std::uint64_t nowMs) const { return _dueMs != kNever && nowMs >= _dueMs; }
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs) { _dueMs = nowMs + everyMs; }
        std::uint64_t DueMs() const { return _dueMs; }

    private:
        std::uint64_t _dueMs = kNever;
    };

    // VO8 / VO9 stock timers, from the stance's start (the stock phase-entry offsets of boss_warmaster_voone:
    // Thrash 3 s then 10 s; Mortal Strike 12 s then 10 s; Cleave 14 s then 12 s). War Master has none.
    struct Beat
    {
        std::uint32_t first;
        std::uint32_t every;
    };
    inline constexpr Beat kThrashBeat{ 3000, 10000 };
    inline constexpr Beat kMortalStrikeBeat{ 12000, 10000 };
    inline constexpr Beat kCleaveBeat{ 14000, 12000 };

    // VO9 Cleave's frontal (telegraph only: the stock cast's own damage stays): a cone in front of him that non-tanks
    // leave, drawn 1.5 s before the cast. SP gives no numbers; the stock cleave is a melee strike.
    inline constexpr float kCleaveConeDeg = 90.f;
    inline constexpr float kCleaveConeYd = 8.f;
    inline constexpr std::uint32_t kCleaveWarnMs = 1500;

    // ----------------------------------------------------------------------------------------------------------------
    // The stuck axes (VO6, VO7)
    // ----------------------------------------------------------------------------------------------------------------

    // Axes to send back before `incoming` more land: the cap holds the floor at `cap`, counting the throws already in
    // flight (`pending`), and the oldest axes go first. Only axes still stuck can be sent (`stuck`).
    inline std::uint32_t CapRecalls(std::uint32_t stuck, std::uint32_t pending, std::uint32_t incoming,
        std::uint32_t cap)
    {
        std::uint32_t const total = stuck + pending + incoming;
        std::uint32_t const over = total > cap ? total - cap : 0;
        return std::min(over, stuck);
    }

    struct StuckAxe
    {
        std::uint32_t id = 0;
        Vec2 at;
        float z = 0.f;
        std::uint64_t landedMs = 0;
        bool recalling = false;
        std::uint64_t recallDoneMs = 0;
    };

    class AxeBook
    {
    public:
        std::uint32_t Add(Vec2 at, float z, std::uint64_t nowMs)
        {
            StuckAxe axe;
            axe.id = ++_nextId;
            axe.at = at;
            axe.z = z;
            axe.landedMs = nowMs;
            _axes.push_back(axe);
            return axe.id;
        }

        StuckAxe* Find(std::uint32_t id)
        {
            for (StuckAxe& axe : _axes)
                if (axe.id == id)
                    return &axe;
            return nullptr;
        }

        StuckAxe const* Find(std::uint32_t id) const
        {
            for (StuckAxe const& axe : _axes)
                if (axe.id == id)
                    return &axe;
            return nullptr;
        }

        // Axes on the floor that no lane is bringing back, the oldest first (landing order).
        std::vector<std::uint32_t> StuckIds() const
        {
            std::vector<std::uint32_t> ids;
            for (StuckAxe const& axe : _axes)
                if (!axe.recalling)
                    ids.push_back(axe.id);
            return ids;
        }

        std::uint32_t StuckCount() const
        {
            std::uint32_t n = 0;
            for (StuckAxe const& axe : _axes)
                n += axe.recalling ? 0u : 1u;
            return n;
        }

        std::uint32_t Count() const { return static_cast<std::uint32_t>(_axes.size()); }

        // A lane is bringing it back; it is gone at `doneMs`.
        bool MarkRecall(std::uint32_t id, std::uint64_t doneMs)
        {
            StuckAxe* axe = Find(id);
            if (!axe || axe->recalling)
                return false;
            axe->recalling = true;
            axe->recallDoneMs = doneMs;
            return true;
        }

        // Removes and returns the recalled axes whose lanes have arrived.
        std::vector<StuckAxe> TakeArrived(std::uint64_t nowMs)
        {
            std::vector<StuckAxe> done;
            for (auto it = _axes.begin(); it != _axes.end();)
            {
                if (it->recalling && nowMs >= it->recallDoneMs)
                {
                    done.push_back(*it);
                    it = _axes.erase(it);
                }
                else
                    ++it;
            }
            return done;
        }

        std::vector<StuckAxe> const& All() const { return _axes; }

        void Clear() { _axes.clear(); }

    private:
        std::vector<StuckAxe> _axes;
        std::uint32_t _nextId = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // War Cry (VO12, heroic) and Berserking (VO10)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kWarCryFirstMs = 15000;      // from the fight's start
    inline constexpr std::uint32_t kWarCryEveryMs = 25000;
    inline constexpr std::uint32_t kWarCryCastMs = 2500;        // the spell's cast time (dbc-tools voone.py)
    inline constexpr std::uint32_t kWarCryBerserkMs = 10000;
    inline constexpr std::uint8_t kWarCryKickPriority = 3;      // the descriptor's interrupt entry (expected, heroic)
    inline constexpr std::uint32_t kBerserkingPct = 30;         // +30% attack speed (dbc-tools voone.py)

    // Berserking has two sources, the War Master stance and a landed War Cry; he wears it until the later one ends.
    class BerserkClock
    {
    public:
        void SetStance(std::uint64_t untilMs) { _stanceUntil = untilMs; }
        void ClearStance() { _stanceUntil = 0; }
        void SetCry(std::uint64_t untilMs) { _cryUntil = std::max(_cryUntil, untilMs); }
        void Clear()
        {
            _stanceUntil = 0;
            _cryUntil = 0;
        }
        std::uint64_t Until() const { return std::max(_stanceUntil, _cryUntil); }
        bool Active(std::uint64_t nowMs) const { return nowMs < Until(); }
        std::uint32_t RemainingMs(std::uint64_t nowMs) const
        {
            return nowMs < Until() ? static_cast<std::uint32_t>(Until() - nowMs) : 0u;
        }

    private:
        std::uint64_t _stanceUntil = 0;
        std::uint64_t _cryUntil = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The charge out (VO1) and the walk to him
    // ----------------------------------------------------------------------------------------------------------------

    // The jump (Berserker Charge's look): 23.6 yd from his spawn to the hall's charge spot.
    inline constexpr float kChargeSpeedXY = 25.f;
    inline constexpr float kChargeMinSpeedZ = 8.f;
    // His quarters have one gate, 97 yd of floor from the hall (NAVMESH-REPORT 3): after the jump he holds the spot
    // (rooted once the jump has landed) until a player is this close, or for kHoldMaxMs; the stances start then.
    inline constexpr std::uint32_t kChargeLandMs = 1500;
    inline constexpr float kHoldReleaseYd = 12.f;
    inline constexpr std::uint32_t kHoldMaxMs = 60000;

    inline constexpr bool HoldReleased(float nearestPlayerYd, std::uint32_t heldMs)
    {
        return nearestPlayerYd <= kHoldReleaseYd || heldMs >= kHoldMaxMs;
    }

    // R-1 ruling 1 (2026-11-15): while he holds, anyone who damages him from beyond kHoldReleaseYd is answered with an
    // axe throw at that attacker (a pet, totem or DoT counts as its player; the distance is the damaging unit's). One
    // single-target hit (Axe Throw's resolve copy, Physical, no Weakened, through the registry so the healers see it),
    // at most one per attacker every kHoldThrowEveryMs, landing when the axe arrives (the flight look's 15 yd/s).
    // Plain single-target damage: the bots need no solver; the group walking in (a player within 12 yd) ends it.
    inline constexpr NH<float> kHoldThrowPct{ 20.f, 25.f };
    inline constexpr std::uint32_t kHoldThrowEveryMs = 2000;
    inline constexpr float kHoldThrowFlightYdPerSec = kThrowMissileSpeed;     // 210095's 15 yd/s
    inline constexpr std::uint32_t kHoldThrowMaxFlightMs = 3000;

    inline constexpr bool HoldThrowAnswers(float attackerYd)
    {
        return attackerYd > kHoldReleaseYd;
    }

    // Ready for `attacker` again: never thrown at, or kHoldThrowEveryMs since the last throw.
    inline constexpr bool HoldThrowReady(std::uint64_t nowMs, std::optional<std::uint64_t> lastThrowMs)
    {
        return !lastThrowMs || nowMs >= *lastThrowMs + kHoldThrowEveryMs;
    }

    inline constexpr std::uint32_t HoldThrowFlightMs(float distanceYd)
    {
        float const ms = std::max(0.f, distanceYd) * 1000.f / kHoldThrowFlightYdPerSec;
        return ms >= static_cast<float>(kHoldThrowMaxFlightMs) ? kHoldThrowMaxFlightMs : static_cast<std::uint32_t>(ms);
    }

    // The leash (SP: "he resets if he leaves the hall"): his quarters, the hall box of section 3.8 and the walk from
    // the gate around to the hall's west edge, which the group takes while he holds the charge spot. The route box
    // runs from the gate's south side down to the hall's x edge and along the hall's y edge back up to the gate
    // (NAVMESH-REPORT 3).
    inline constexpr float kRouteMinX = -60.5f;
    inline constexpr float kRouteMaxX = -28.5f;
    inline constexpr float kRouteMinY = -474.0f;
    inline constexpr float kRouteMaxY = -443.5f;

    inline DungeonKit::Arena FightArena()
    {
        DungeonKit::Arena arena = BlackrockSpireRework::VooneArena();
        arena.Add(BlackrockSpireRework::BoxRegion(kRouteMinX, kRouteMaxX, kRouteMinY, kRouteMaxY, -22.5f, -14.0f));
        return arena;
    }

    // The Park circle the heroic tank holds him in (the chains sweep when he moves): the charge spot.
    inline constexpr float kParkRadius = 5.f;
}

#endif
