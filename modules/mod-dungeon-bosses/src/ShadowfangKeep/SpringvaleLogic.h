/*
 * mod-dungeon-bosses, Shadowfang Keep: Commander Springvale (WP-S4), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, target picks, the Oath's timeline and the Consecration ledger.
 * Build spec: SK 754-812 (build spec), SK 625-753 (design), SP1-SP10; handoff section 3.5 rows SP and section 3.6 row
 * S4; user ruling handoff section 10 / section 7 #20: the Oath is damage taken -90%, not immunity.
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum
 * (apps/dbc-tools source/npcs/shadowfang_keep/commander_springvale.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the same on both difficulties:
 * the reference row (normal 1,300 / heroic 4,120) makes the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_SPRINGVALE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_SPRINGVALE_LOGIC_H

#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace Springvale
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using Ms = std::chrono::milliseconds;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsSpringvale;

    // apps/dbc-tools source/npcs/shadowfang_keep/commander_springvale.py declares every one of these.
    enum SpringvaleSpells : std::uint32_t
    {
        SPELL_SV_HAMMER                 = 205965,   // SP1 registry resolve copy: the others within 8 yd (25%, Holy)
        SPELL_SV_HAMMER_MARKED          = 205966,   // SP1 the marked player's own 10% (RefFlat), the thrown hammer
        SPELL_SV_HAMMER_STUN            = 205967,   // SP1 / SP2 rider: 1.5 s stun on the others hit (SV 322)
        SPELL_SV_RICOCHET               = 205968,   // SP2 heroic registry resolve copy (25%, Holy)
        SPELL_SV_RICOCHET_MARKED        = 205969,   // SP2 heroic the bounce target's own 10% (RefFlat)
        SPELL_SV_CONSECRATION           = 205970,   // SP3 registry resolve copy (lingering tick, 5% Holy)
        SPELL_SV_CONSECRATION_GROUND    = 205971,   // SP3 normal: the 10 s holy ground look (SV 5600)
        SPELL_SV_CONSECRATION_GROUND_H  = 205972,   // SP3 heroic: the 40 s look
        SPELL_SV_HOLY_LIGHT             = 205973,   // SP4 / SP9 2.5 s interruptible heal, 5% of the target's health
        SPELL_SV_SEARING_LIGHT          = 205974,   // SP5 heroic: 15% Holy to every player (RefFlat, SV 3400)
        SPELL_SV_UNBREAKABLE_OATH       = 205975,   // SP6 damage taken -90% (SV 154)
        SPELL_SV_CRACKED_OATH           = 205976,   // SP6 the cracks: one stack per fallen guardsman (DUMMY)
        SPELL_SV_OATHBROKEN             = 205977,   // SP7 damage taken +25%, 6 s
        SPELL_SV_WRATH_OF_GOD           = 205978,   // SP8 heroic 30 s cast bar (SV 12986), not interruptible
        SPELL_SV_WRATH_OF_GOD_KILL      = 205979,   // SP8 heroic the kill on every player (INSTAKILL)
        SPELL_SV_GUARDSMAN_RISE         = 205980,   // SP6 the rise look on each guardsman (SV 14312)
        // 205981-205989 spare.
    };

    // Registry tags (bookkeeping in `.mech` listings and the failure ledger).
    enum SpringvaleTags : std::uint32_t
    {
        TAG_HAMMER          = 1,
        TAG_RICOCHET        = 2,
        TAG_CONSECRATION    = 3,
    };

    // The descriptor's phases (Mechanic::SetPhase): while the Oath holds the tank goes for the guardsmen too.
    enum SpringvalePhases : std::uint32_t
    {
        PHASE_FIGHT = 0,
        PHASE_OATH  = 1,
    };

    // The Guardsman of the Hammer's own text (creature_text 300507 group 0): the Hammer emote.
    std::uint8_t constexpr EMOTE_GUARDSMAN_HAMMER = 0;

    // ----------------------------------------------------------------------------------------------------------------
    // Damage and heals (percent of the reference row for the difficulty; SK Build spec "Damage N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kHammerOthersPct{ 25.f, 25.f };      // SP1 / SP2 anyone else within 8 yd, Weakened
    inline constexpr NH<float> kHammerMarkedPct{ 10.f, 10.f };      // SP1 / SP2 the marked player (no Weakened)
    inline constexpr NH<float> kConsecrationPct{ 5.f, 5.f };        // SP3 per 1 s tick
    inline constexpr NH<float> kSearingLightPct{ 0.f, 15.f };       // SP5 (heroic only)
    inline constexpr float kHolyLightHealPct = 5.f;                 // SP4 / SP9: of the target's max health
    inline constexpr float kOathDamageTakenPct = -90.f;             // SP6 (user ruling: no immunity)
    inline constexpr float kOathbrokenDamageTakenPct = 25.f;        // SP7

    // ----------------------------------------------------------------------------------------------------------------
    // Shapes
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kHammerYd = 8.f;
    inline constexpr float kConsecrationYd = 8.f;
    // Every player within this range of the boss is "every player" (Searing Light, Wrath of God): the hall is 46 yd
    // long.
    inline constexpr float kRoomRange = 60.f;
    // The thrown hammer (205966 / 205969) flies at this speed (its Speed column): the script launches it so that it
    // lands as the ring ends.
    inline constexpr float kHammerSpeed = 20.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (SK "First, cooldown"; the same on both difficulties unless an NH says otherwise)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr Ms kHammerWarn{ 3000 };                        // SP1 ring
    inline constexpr Ms kRicochetWarn{ 2000 };                      // SP2 ring
    inline constexpr Ms kHammerStun{ 1500 };                        // 205967's duration
    inline constexpr Ms kHammerFirst{ 8000 };
    inline constexpr Ms kHammerEvery{ 18000 };
    inline constexpr Ms kGuardsmanHammerFirst{ 4000 };              // after rising (heroic)
    inline constexpr Ms kGuardsmanHammerEvery{ 12000 };

    inline constexpr Ms kConsecrationFirst{ 12000 };
    inline constexpr Ms kConsecrationEvery{ 20000 };
    inline constexpr NH<Ms> kConsecrationDuration{ Ms(10000), Ms(40000) };
    inline constexpr Ms kConsecrationTick{ 1000 };
    inline constexpr Ms kAltarConsecrationFirst{ 0 };               // at once on rising (heroic): two in 30 s
    inline constexpr Ms kAltarConsecrationEvery{ 15000 };

    inline constexpr float kHolyLightBelowPct = 60.f;               // SP4: Springvale's own heal
    inline constexpr Ms kHolyLightEvery{ 10000 };
    inline constexpr Ms kHolyLightCast{ 2500 };
    inline constexpr Ms kGuardsmanHolyLightFirst{ 10000 };          // after rising (heroic)
    inline constexpr Ms kGuardsmanHolyLightEvery{ 10000 };

    inline constexpr float kOathAtPct = 30.f;                       // SP6, once
    inline constexpr Ms kGuardsmanRise{ 2000 };                     // the rise look, then they act
    inline constexpr Ms kOathCap{ 30000 };                          // SP6 normal: the shield drops on its own
    inline constexpr Ms kWrathOfGodCast{ 30000 };                   // SP8 heroic
    inline constexpr Ms kWrathOfGodEmoteLeft{ 10000 };              // emote line 5 at 10 s left
    inline constexpr Ms kOathbroken{ 6000 };                        // SP7
    inline constexpr Ms kBusyRetry{ 500 };
    inline constexpr Ms kCheckEvery{ 1000 };                        // a gated timer (Holy Light above 60%) retries
    inline constexpr std::uint32_t kGuardsmanCorpseMs = 15000;      // a dead guardsman's corpse stays this long

    inline constexpr std::uint8_t kGuardsmanCount = 3;

    // ----------------------------------------------------------------------------------------------------------------
    // Units: the three Risen Guardsmen (SK "Boss data": kill order Light, Hammer, Altar, then Springvale)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Guardsman : std::uint8_t
    {
        Light,      // SP9 heroic: Holy Light on Springvale or a wounded guardsman, Searing Light
        Hammer,     // SP1 heroic: Hammer of Judgement
        Altar,      // SP3 heroic: Consecration under itself
    };

    struct GuardsmanInfo
    {
        Guardsman kind;
        std::uint32_t entry;
        std::int8_t killPriority;   // descriptor TargetEntry priority (the boss is 0; higher first)
        std::size_t risePoint;      // index into ShadowfangKeepRework::kGuardsmanRisePoints
    };

    // Rise points (ShadowfangKeepRework.h): the two flanks and the middle.
    inline constexpr std::array<GuardsmanInfo, kGuardsmanCount> kGuardsmen{ {
        { Guardsman::Light, ShadowfangKeepRework::NPC_SFK_GUARDSMAN_LIGHT, 3, 0 },
        { Guardsman::Hammer, ShadowfangKeepRework::NPC_SFK_GUARDSMAN_HAMMER, 2, 1 },
        { Guardsman::Altar, ShadowfangKeepRework::NPC_SFK_GUARDSMAN_ALTAR, 1, 2 },
    } };

    inline std::optional<GuardsmanInfo> GuardsmanOf(std::uint32_t entry)
    {
        for (GuardsmanInfo const& g : kGuardsmen)
            if (g.entry == entry)
                return g;
        return std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gates
    // ----------------------------------------------------------------------------------------------------------------

    // SP6: the Oath starts once, the first time he is at or below 30% (after the hit).
    inline bool OathTriggers(float healthPctAfterHit, bool alreadyUsed)
    {
        return !alreadyUsed && healthPctAfterHit <= kOathAtPct;
    }

    // Springvale's own abilities while the Oath holds: on normal he keeps throwing Hammers (SK SP6) and nothing else;
    // on heroic he only casts Wrath of God.
    inline bool BossHammerAllowed(bool heroic, bool oathActive)
    {
        return !oathActive || !heroic;
    }

    inline bool BossConsecrationAllowed(bool oathActive)
    {
        return !oathActive;
    }

    inline bool BossHolyLightAllowed(float healthPct, bool oathActive)
    {
        return !oathActive && healthPct < kHolyLightBelowPct;
    }

    // He stops meleeing while the Oath holds (SK SP6).
    inline bool BossMelees(bool oathActive)
    {
        return !oathActive;
    }

    // SP2: a Hammer bounces only on heroic, only off a marked player standing in a Consecration, and a bounced hammer
    // never bounces again.
    inline bool Ricochets(bool heroic, bool isRicochet, bool markedInConsecration)
    {
        return heroic && !isRicochet && markedInConsecration;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    struct PlayerSpot
    {
        std::uint64_t id = 0;
        Vec2 at;
        bool alive = true;
    };

    // SP2: the player nearest the marked one (the tank included), never the marked player.
    inline std::optional<std::size_t> NearestOther(std::vector<PlayerSpot> const& players, std::uint64_t marked,
        Vec2 from)
    {
        std::optional<std::size_t> best;
        float bestDist = 0.f;
        for (std::size_t i = 0; i < players.size(); ++i)
        {
            PlayerSpot const& p = players[i];
            if (!p.alive || p.id == marked)
                continue;
            float const d = DungeonKit::Distance(p.at, from);
            if (!best || d < bestDist)
            {
                best = i;
                bestDist = d;
            }
        }
        return best;
    }

    struct HealCandidate
    {
        std::uint64_t id = 0;
        float healthPct = 100.f;
        bool alive = true;
    };

    // SP9: the Guardsman of the Light heals the most wounded of Springvale and the guardsmen (below 100%); with
    // nobody wounded, nobody.
    inline std::optional<std::size_t> PickHolyLightTarget(std::vector<HealCandidate> const& candidates)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < candidates.size(); ++i)
        {
            HealCandidate const& c = candidates[i];
            if (!c.alive || c.healthPct >= 100.f)
                continue;
            if (!best || c.healthPct < candidates[*best].healthPct)
                best = i;
        }
        return best;
    }

    // When the thrown hammer leaves, so that it lands as the ring ends: `warn` less the flight (distance / speed),
    // never before now.
    inline Ms HammerLaunchDelay(Ms warn, float distance, float speed = kHammerSpeed)
    {
        if (speed <= 0.f)
            return warn;
        Ms const flight(static_cast<std::int64_t>(std::max(distance, 0.f) / speed * 1000.f));
        return flight >= warn ? Ms(0) : warn - flight;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Consecration ledger: the pools on the floor (their registry ids and when they end), for Ricochet
    // ----------------------------------------------------------------------------------------------------------------
    class PoolLedger
    {
    public:
        void Add(std::uint32_t mechanicId, std::int64_t endsAtMs)
        {
            if (mechanicId)
                _pools.push_back({ mechanicId, endsAtMs });
        }

        // The pools still on the floor at `nowMs` (the expired ones are dropped).
        std::vector<std::uint32_t> Live(std::int64_t nowMs)
        {
            _pools.erase(std::remove_if(_pools.begin(), _pools.end(), [nowMs](Pool const& p)
            {
                return p.endsAtMs <= nowMs;
            }), _pools.end());
            std::vector<std::uint32_t> ids;
            for (Pool const& p : _pools)
                ids.push_back(p.mechanicId);
            return ids;
        }

        void Clear() { _pools.clear(); }
        std::size_t Size() const { return _pools.size(); }

    private:
        struct Pool
        {
            std::uint32_t mechanicId;
            std::int64_t endsAtMs;
        };

        std::vector<Pool> _pools;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The Oath (SP6-SP8): its timeline, driven by the script's tick
    // ----------------------------------------------------------------------------------------------------------------
    enum class OathEnd : std::uint8_t
    {
        None,
        Shattered,      // the third guardsman fell: Oathbroken (and, on heroic, Wrath of God interrupted)
        CapExpired,     // normal: 30 s, the shield drops on its own, no Oathbroken; standing guardsmen fight on
        WrathLanded,    // heroic: the 30 s cast finished, every player dies
    };

    struct OathStep
    {
        bool prayerEmote = false;       // heroic: emote line 5, 10 s left
        OathEnd end = OathEnd::None;
    };

    class OathTimeline
    {
    public:
        void Start(bool heroic)
        {
            _used = true;
            _active = true;
            _heroic = heroic;
            _elapsed = Ms(0);
            _fallen = 0;
            _emoted = false;
        }

        void Reset() { *this = OathTimeline(); }

        // Advances the clock while the Oath holds; the step says what happened in this tick.
        OathStep Advance(Ms diff)
        {
            OathStep step;
            if (!_active)
                return step;
            _elapsed += diff;
            if (_heroic && !_emoted && _elapsed >= kWrathOfGodCast - kWrathOfGodEmoteLeft)
            {
                _emoted = true;
                step.prayerEmote = true;
            }
            if (_elapsed >= Limit())
            {
                _active = false;
                step.end = _heroic ? OathEnd::WrathLanded : OathEnd::CapExpired;
            }
            return step;
        }

        // A guardsman fell. While the Oath holds each death is a crack and the third shatters it; after the normal
        // cap a death changes nothing (no Oathbroken window).
        OathEnd GuardsmanDied()
        {
            if (!_active)
                return OathEnd::None;
            if (_fallen < kGuardsmanCount)
                ++_fallen;
            if (_fallen < kGuardsmanCount)
                return OathEnd::None;
            _active = false;
            return OathEnd::Shattered;
        }

        bool Used() const { return _used; }
        bool Active() const { return _active; }
        bool Heroic() const { return _heroic; }
        std::uint8_t Cracks() const { return _fallen; }
        Ms Elapsed() const { return _elapsed; }
        Ms Limit() const { return _heroic ? kWrathOfGodCast : kOathCap; }
        Ms Left() const { return _elapsed >= Limit() ? Ms(0) : Limit() - _elapsed; }

    private:
        bool _used = false;
        bool _active = false;
        bool _heroic = false;
        bool _emoted = false;
        std::uint8_t _fallen = 0;
        Ms _elapsed{ 0 };
    };
}

#endif
