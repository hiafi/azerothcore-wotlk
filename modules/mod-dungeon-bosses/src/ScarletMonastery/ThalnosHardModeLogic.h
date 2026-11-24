/*
 * mod-dungeon-bosses, Scarlet Monastery D4H:
 * Bloodmage Thalnos's hard mode, the Desecration, the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Hard mode" and "Build spec" (TH7, TH8, RH1-RH6, the Desecration),
 * handoff sections 3.6 (360k, the risen 20k), 3.7 row D4H, 3.8 (the lawn, NAVMESH "Thalnos hard mode"), 7 #18 A (the
 * stones on the disc (1796.5, 1369.5), the rite in the z 0 court, the stones refuse while the council lives). Tested
 * by tests/sm_thalnos_hard_mode_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsDesecration (212480-212539), declared in apps/dbc-tools
 *                  source/npcs/scarlet_monastery/thalnos_hard_mode.py
 *   The heroes     Galvar, Fairbell, Voss, Goodchilde: entries, kill order, their stones, their beats and numbers
 *   The stones     the four gravestones (by entry, never by spot: RB-3), the rite, the refusals and their texts
 *   TH7            the 75% teleport: the 3 s bar, the landing arc on the lawn, the arrival wait
 *   Rising         two at the landing, Voss 20 s later, Goodchilde 20 s after, then every 20 s the first dead one
 *                  (Galvar, Fairbell, Voss, Goodchilde); at most four standing
 *   TH8            Blood Pact: 20% less damage taken per living risen, at most 80% (the kit's WardOfTheLiving)
 *   RH1            the Rallying Banner's 25% (script math on the risen's own hits; a damage hook on the rest)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_THALNOS_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_THALNOS_HARD_MODE_LOGIC_H

#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include "ThalnosLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>

namespace SmDesecration
{
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;
    using ScarletMonasteryRework::Point4;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsDesecration;

    enum DesecrationSpells : std::uint32_t
    {
        SPELL_DS_HARD_MODE_AURA     = kSpellSlice.first + 0,    // 212480 Thalnos's red aura (the flag is lit)
        SPELL_DS_NO_REST            = kSpellSlice.first + 1,    // 212481 TH7 the 3 s teleport bar (Arcane, no kick)
        SPELL_DS_BLOOD_PACT         = kSpellSlice.first + 2,    // 212482 TH8 his buff, one stack per living risen
        SPELL_DS_PACT_TETHER        = kSpellSlice.first + 3,    // 212483 TH8 a risen's tether into him (a channel)
        SPELL_DS_RISE               = kSpellSlice.first + 4,    // 212484 a risen's rising look
        SPELL_DS_STONE_STIR         = kSpellSlice.first + 5,    // 212485 a touched stone's faint glow (a stalker's)
        SPELL_DS_STONE_BLOOD        = kSpellSlice.first + 6,    // 212486 the answered stones' and the rite's red
        SPELL_DS_DISTURB_THE_GRAVE  = kSpellSlice.first + 7,    // 212487 the 2 s use on a stone (a player's cast)
        SPELL_DS_RALLIED            = kSpellSlice.first + 8,    // 212488 RH1 the banner's buff (25% more damage)
        SPELL_DS_CHARGE_LOOK        = kSpellSlice.first + 9,    // 212489 RH2 Galvar's charge look
        SPELL_DS_CHARGE_HIT         = kSpellSlice.first + 10,   // 212490 RH2 the landing's hit (resolve copy)
        SPELL_DS_REPENT             = kSpellSlice.first + 11,   // 212491 RH3 Fairbell's 2 s cast, 2 s incapacitate
        SPELL_DS_GREATER_HEAL       = kSpellSlice.first + 12,   // 212492 RH4 Voss's 3 s heal, 10% of the target
        SPELL_DS_POWER_WORD_SHIELD  = kSpellSlice.first + 13,   // 212493 RH5 Voss's absorb (a purge reward)
        SPELL_DS_WHIRLWIND_WINDUP   = kSpellSlice.first + 14,   // 212494 RH6 Goodchilde's 2 s wind-up bar
        SPELL_DS_WHIRLWIND          = kSpellSlice.first + 15,   // 212495 RH6 the 4 s spin's look on him
        SPELL_DS_WHIRLWIND_HIT      = kSpellSlice.first + 16,   // 212496 RH6 a spin tick's hit (resolve copy)
        // 212497-212539 spare
    };
    static_assert(SPELL_DS_WHIRLWIND_HIT <= kSpellSlice.last, "the Desecration's spells must stay in its slice");

    // Registry tags (the failure ledger, the playtest greps): RH1, RH2, RH6 (D4 holds 2-4).
    enum DesecrationTags : std::uint32_t
    {
        RH1 = 11,   // the banner's tank-only zone (the tank drags them off it)
        RH2 = 12,   // Crusader's Charge's landing
        RH6 = 16,   // Whirlwind round Goodchilde
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_thalnos_hard_mode_scarlet_monastery.sql): Thalnos's
    // 4 is SmThalnos::SAY_WAKE_THEM_ALL (1, SAY_NO_REST, is the teleport's); each risen's 0.
    inline constexpr std::uint8_t EMOTE_RISEN = 0;     // Galvar: the banner; Goodchilde: the spin

    // ----------------------------------------------------------------------------------------------------------------
    // The heroes (GY "The fallen of the Crusade"; the order is the rising order and the stones' answer)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Hero : std::uint8_t
    {
        Galvar,         // High Commander Galvar Pureblood: Rallying Banner, Crusader's Charge
        Fairbell,       // Inquisitor Fairbell: Repent
        Voss,           // Benedictus Voss: Greater Heal, Power Word: Shield
        Goodchilde,     // High Commander Goodchilde: Whirlwind
    };
    inline constexpr std::size_t kHeroCount = 4;
    inline constexpr std::array<Hero, kHeroCount> kHeroes{ Hero::Galvar, Hero::Fairbell, Hero::Voss, Hero::Goodchilde };

    constexpr std::size_t IndexOf(Hero h) { return static_cast<std::size_t>(h); }

    constexpr std::uint32_t EntryOf(Hero h)
    {
        switch (h)
        {
            case Hero::Galvar:      return ScarletMonasteryRework::NPC_SM_GALVAR;
            case Hero::Fairbell:    return ScarletMonasteryRework::NPC_SM_FAIRBELL;
            case Hero::Voss:        return ScarletMonasteryRework::NPC_SM_VOSS;
            case Hero::Goodchilde:  return ScarletMonasteryRework::NPC_SM_GOODCHILDE;
        }
        return 0;
    }

    // "Is this unit one of mine" by entry (RB-3).
    constexpr std::optional<Hero> HeroOfEntry(std::uint32_t entry)
    {
        for (Hero h : kHeroes)
            if (EntryOf(h) == entry)
                return h;
        return std::nullopt;
    }

    constexpr char const* NameOf(Hero h)
    {
        switch (h)
        {
            case Hero::Galvar:      return "galvar";
            case Hero::Fairbell:    return "fairbell";
            case Hero::Voss:        return "voss";
            case Hero::Goodchilde:  return "goodchilde";
        }
        return "?";
    }

    // The kill order (GY: Voss, Fairbell, Galvar, Goodchilde, then Thalnos): the descriptor's target priority, higher
    // first, Thalnos 0 (Blood Pact enforces it).
    constexpr std::int8_t KillPriority(Hero h)
    {
        switch (h)
        {
            case Hero::Voss:        return 4;
            case Hero::Fairbell:    return 3;
            case Hero::Galvar:      return 2;
            case Hero::Goodchilde:  return 1;
        }
        return 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stones and the rite (section 7 #18 A; NAVMESH "Thalnos hard mode": the disc (1796.5, 1369.5) r 16.1, the
    // stones 11.4 yd apart; the rite in the z 0 court). Each stone faces the disc's center. A stone's hero is its
    // entry's (the order Galvar, Fairbell, Voss, Goodchilde = DATA_DESECRATION_TOUCH 0-3)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kStoneDisc{ 1796.5f, 1369.5f };
    inline constexpr std::array<Point3, kHeroCount> kStoneSpots{ {
        { 1802.2f, 1375.2f, 18.8f },    // Galvar
        { 1790.8f, 1375.2f, 18.8f },    // Fairbell
        { 1790.8f, 1363.8f, 18.7f },    // Voss
        { 1802.2f, 1363.8f, 18.4f },    // Goodchilde
    } };
    // The rite on the stair head's wall in the court (z 0), facing south (-x) into the court (unconfirmed in game).
    inline constexpr Point4 kRiteSpot{ 1788.5f, 1417.f, 0.3f, DungeonKit::kPi };

    constexpr std::optional<Hero> HeroOfStone(std::uint32_t goEntry)
    {
        switch (goEntry)
        {
            case ScarletMonasteryRework::GO_SM_GRAVESTONE_GALVAR:       return Hero::Galvar;
            case ScarletMonasteryRework::GO_SM_GRAVESTONE_FAIRBELL:     return Hero::Fairbell;
            case ScarletMonasteryRework::GO_SM_GRAVESTONE_VOSS:         return Hero::Voss;
            case ScarletMonasteryRework::GO_SM_GRAVESTONE_GOODCHILDE:   return Hero::Goodchilde;
            default:                                                    return std::nullopt;
        }
    }

    // A stone's facing: toward the disc's center.
    inline float StoneFacing(Hero h)
    {
        Point3 const& s = kStoneSpots[IndexOf(h)];
        return DungeonKit::BearingTo(s.XY(), kStoneDisc);
    }

    // The gossip texts (npc_text rows of the SQL rev, ids = the objects' entries): the four epitaphs and the rite.
    inline constexpr std::uint32_t kRiteTextId = ScarletMonasteryRework::GO_SM_BLOOD_RITE;
    constexpr std::uint32_t EpitaphTextId(Hero h)
    {
        return ScarletMonasteryRework::GO_SM_GRAVESTONE_GALVAR + static_cast<std::uint32_t>(IndexOf(h));
    }
    inline constexpr char const* kDisturbOption = "Disturb the Grave.";

    // Why a stone does not answer a touch now (the instance judges again: DesecrationTouchAllowed).
    enum class StoneRefusal : std::uint8_t
    {
        None,
        NotHeroic,          // the stones stand on heroic only (spawn mask 2)
        Lit,                // already answered: the stones bleed and no longer answer
        CouncilAlive,       // section 7 #18 A: "the dead are not yet at rest"
        ThalnosFighting,
        ThalnosDead,
    };

    constexpr StoneRefusal RefusalFor(bool heroic, std::uint32_t thalnos, std::uint32_t council, bool lit)
    {
        if (!heroic)
            return StoneRefusal::NotHeroic;
        if (lit)
            return StoneRefusal::Lit;
        if (thalnos == DungeonKit::State::Done)
            return StoneRefusal::ThalnosDead;
        if (thalnos == DungeonKit::State::InProgress)
            return StoneRefusal::ThalnosFighting;
        if (council != DungeonKit::State::Done)
            return StoneRefusal::CouncilAlive;
        return StoneRefusal::None;
    }

    constexpr char const* RefusalText(StoneRefusal r)
    {
        switch (r)
        {
            case StoneRefusal::CouncilAlive:    return "The dead are not yet at rest.";
            case StoneRefusal::ThalnosFighting: return "The ground shakes. The dead will not wake now.";
            case StoneRefusal::ThalnosDead:     return "Nothing stirs below. The Bloodmage is gone.";
            case StoneRefusal::Lit:             return "The grave bleeds. It has answered.";
            case StoneRefusal::NotHeroic:       return "The grave is silent.";
            case StoneRefusal::None:            break;
        }
        return "";
    }
    inline constexpr char const* kRepeatText = "This grave already stirs.";

    // The touch's 2 s use (GY: "each takes a 2 s Disturb the Grave use").
    inline constexpr std::uint32_t kDisturbCastMs = 2000;
    inline constexpr float kDisturbRangeYd = 5.f;

    // What a stone shows (its stalker's look). The touched flag clears when the instance's count does (a judge).
    enum class StoneLook : std::uint8_t
    {
        None,
        Stir,       // touched this attempt: a faint glow, no right or wrong signal
        Blood,      // answered: all four glow red (persistent)
    };

    constexpr StoneLook LookFor(bool lit, bool touched, std::uint32_t touchesThisAttempt)
    {
        if (lit)
            return StoneLook::Blood;
        return touched && touchesThisAttempt > 0 ? StoneLook::Stir : StoneLook::None;
    }

    // A wrong answer: three Haunting Phantasms rise from the lawn round the disc (stock trash 6427; on heroic its
    // heroic copy, the map's difficulty) and attack the toucher.
    inline constexpr std::uint32_t kPhantasmCount = 3;
    inline constexpr float kPhantasmRingYd = 5.f;
    inline constexpr std::uint32_t kPhantasmCorpseMs = 60000;

    inline Vec2 PhantasmSpot(std::uint32_t i)
    {
        float const a = DungeonKit::kTwoPi * static_cast<float>(i) / static_cast<float>(kPhantasmCount);
        return { kStoneDisc.x + kPhantasmRingYd * std::cos(a), kStoneDisc.y + kPhantasmRingYd * std::sin(a) };
    }

    // How often a stone and the rite sync their look with the instance.
    inline constexpr std::uint32_t kStonePollMs = 1000;
    inline constexpr std::uint32_t kRitePollMs = 5000;

    // ----------------------------------------------------------------------------------------------------------------
    // Health (section 3.6): Thalnos 360k from the pull of a hard mode attempt (back on reset); the risen 20k (their
    // heroic template, WP-H's override; the normal row carries the same)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kThalnosHardModeHealth = 360000;
    inline constexpr std::uint32_t kRisenHealth = 20000;

    // ----------------------------------------------------------------------------------------------------------------
    // TH7 No Rest for the Angry Dead: at 75% (D4's kNoRestPct), line 1 and a 3 s bar; then every fight player near
    // him (the crypt, its stair and the court: within kTeleportGatherYd) and Thalnos land on the lawn disc (section 7
    // #18 A: (1798.5, 1348.5), r 19.1). He faces away from the stones, the players land on an arc 8 yd in front of him
    // facing him; the risen rise once everyone has arrived (or after kArrivalMaxMs)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kNoRestCastMs = 3000;
    inline constexpr std::uint32_t kArrivalMaxMs = 2000;
    inline constexpr float kTeleportGatherYd = 60.f;
    inline constexpr float kLandingRingYd = 8.f;
    inline constexpr float kLandingStepRad = 0.42f;    // about 3.4 yd between neighbours on the 8 yd arc
    inline constexpr Vec2 kLawnLanding = SmThalnos::kLawnCenter;

    inline float ThalnosLandingFacing()
    {
        return DungeonKit::BearingTo(kStoneDisc, kLawnLanding);
    }

    // The `index`-th of `count` players' landing: an arc centered on his facing; each faces him.
    inline Point4 PlayerLanding(std::uint32_t index, std::uint32_t count)
    {
        float const facing = ThalnosLandingFacing();
        float const centered = static_cast<float>(index) - (static_cast<float>(count ? count : 1) - 1.f) * 0.5f;
        float const a = facing + centered * kLandingStepRad;
        Vec2 const p{ kLawnLanding.x + kLandingRingYd * std::cos(a), kLawnLanding.y + kLandingRingYd * std::sin(a) };
        float o = a + DungeonKit::kPi;
        while (o >= DungeonKit::kTwoPi)
            o -= DungeonKit::kTwoPi;
        while (o < 0.f)
            o += DungeonKit::kTwoPi;
        return { p.x, p.y, ScarletMonasteryRework::kCouncilLawn.z, o };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The rising (GY "The fallen of the Crusade", Build spec "Hard mode rising"): Galvar and Fairbell at the landing,
    // Voss 20 s later, Goodchilde 20 s after that; from then on every 20 s the first dead one in the order rises again.
    // No cap on rises (level 60: it acts as the enrage); at most four stand at once (one of each)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kRiseEveryMs = 20000;

    // A risen rises at its own stone, kRiseInYd toward the landing (in front of the stone, never inside it).
    inline constexpr float kRiseInYd = 2.5f;

    inline Point4 RiseSpot(Hero h)
    {
        Point3 const& s = kStoneSpots[IndexOf(h)];
        float const o = DungeonKit::BearingTo(s.XY(), kLawnLanding);
        return { s.x + kRiseInYd * std::cos(o), s.y + kRiseInYd * std::sin(o), s.z, o };
    }

    using AliveMask = std::array<bool, kHeroCount>;

    class RiseClock
    {
    public:
        // The landing: Galvar and Fairbell rise now (returned), the clock starts.
        std::array<Hero, 2> Start(std::uint64_t nowMs)
        {
            _on = true;
            _step = 1;
            _dueMs = nowMs + kRiseEveryMs;
            return { Hero::Galvar, Hero::Fairbell };
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }
        std::uint32_t Step() const { return _step; }

        // The hero who rises at `nowMs` (none: not due, or nobody is dead at this beat). Steps 1 and 2 are Voss's and
        // Goodchilde's first rising (if that one already stands, the first dead one instead); every later beat the
        // first dead one in the order.
        std::optional<Hero> Due(std::uint64_t nowMs, AliveMask const& alive)
        {
            if (!_on || nowMs < _dueMs)
                return std::nullopt;
            _dueMs += kRiseEveryMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + kRiseEveryMs;
            std::uint32_t const step = _step++;
            if (step == 1 && !alive[IndexOf(Hero::Voss)])
                return Hero::Voss;
            if (step == 2 && !alive[IndexOf(Hero::Goodchilde)])
                return Hero::Goodchilde;
            return FirstDead(alive);
        }

        static std::optional<Hero> FirstDead(AliveMask const& alive)
        {
            for (Hero h : kHeroes)
                if (!alive[IndexOf(h)])
                    return h;
            return std::nullopt;
        }

    private:
        std::uint64_t _dueMs = 0;
        std::uint32_t _step = 0;
        bool _on = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TH8 Blood Pact (L38, the kit's WardOfTheLiving): 20% less damage taken per living risen, at most 80%
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kPactPctPerRisen = 20.f;
    inline constexpr float kPactCapPct = 80.f;
    // A risen re-channels its tether when it is missing (a kick, a channel that ended) this often.
    inline constexpr std::uint32_t kTetherCheckMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // The risen's beats: first after its rise, then the cooldown (Build spec RH1-RH6 "First, cooldown")
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    inline constexpr Beat kBannerBeat{ 5000, 25000 };      // RH1 Galvar
    inline constexpr Beat kChargeBeat{ 8000, 15000 };      // RH2 Galvar
    inline constexpr Beat kRepentBeat{ 6000, 12000 };      // RH3 Fairbell
    inline constexpr Beat kHealBeat{ 4000, 12000 };        // RH4 Voss
    inline constexpr Beat kShieldBeat{ 10000, 20000 };     // RH5 Voss
    inline constexpr Beat kWhirlwindBeat{ 6000, 20000 };   // RH6 Goodchilde
    // A beat that cannot fire now (a cast, nobody to aim at) is tried again this soon.
    inline constexpr std::uint32_t kHeroRetryMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // RH1 Rallying Banner: planted at Galvar's feet for 30 s (emote line 0); Thalnos and the risen within 10 yd deal
    // 25% more damage. The registry shows a 10 yd zone only the tank is eligible for (no damage): the tank drags them
    // off it (the G1 banner-drag row: a 3 s warning, a 1 s tick)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kBannerRadius = 10.f;
    inline constexpr std::uint32_t kBannerMs = 30000;
    inline constexpr std::uint32_t kBannerWarnMs = 3000;
    inline constexpr std::uint32_t kBannerTickMs = 1000;
    inline constexpr float kBannerBoostPct = 25.f;
    // The rallied buff is refreshed this often and lasts a little longer (it drops soon after a unit leaves the 10 yd).
    inline constexpr std::uint32_t kRallyRefreshMs = 500;
    inline constexpr std::uint32_t kRalliedMs = 1500;

    // A hit's percent when its dealer is rallied.
    constexpr float Rallied(float pct, bool rallied)
    {
        return rallied ? pct * (1.f + kBannerBoostPct / 100.f) : pct;
    }

    // A damage value when its dealer is rallied (the module's damage hooks: melee and the spells not boosted already).
    inline std::uint32_t RalliedDamage(std::uint32_t damage)
    {
        return static_cast<std::uint32_t>(std::lround(static_cast<double>(damage) * (1.0 + kBannerBoostPct / 100.0)));
    }

    // The hook boosts every spell of a rallied dealer but the hard mode's own hits (their percent is boosted at the
    // registration: no double count).
    constexpr bool HookBoosts(std::uint32_t spellId)
    {
        return !kSpellSlice.Contains(spellId);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RH2 Crusader's Charge: the farthest player on the lawn; a 2 s marker of 5 yd at their spot, then Galvar lands on
    // it: 30% (H) Physical and Weakened to everyone inside (the tank included)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kChargeRadius = 5.f;
    inline constexpr std::uint32_t kChargeWarnMs = 2000;
    inline constexpr float kChargePct = 30.f;
    inline constexpr float kChargeSpeed = 42.f;        // SPEED_CHARGE (yd/s)
    inline constexpr std::uint32_t kChargeLandEarlyMs = 150;

    // When Galvar starts his run (ms after the marker) so he lands just before it resolves.
    inline std::uint32_t ChargeStartMs(float distanceYd)
    {
        float const travelMs = std::max(0.f, distanceYd) / kChargeSpeed * 1000.f;
        float const start = static_cast<float>(kChargeWarnMs - kChargeLandEarlyMs) - travelMs;
        return start <= 0.f ? 0 : static_cast<std::uint32_t>(start);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RH3 Repent: a 2 s Holy cast on a random player (the tank included), a 2 s incapacitate; kickable (a reward)
    // RH4 Greater Heal: a 3 s Holy cast on the most wounded ally (Thalnos included), 10% of its health; kickable
    //     (expected: a missed heal on Thalnos is a lasting setback)
    // RH5 Power Word: Shield: an absorb on an ally without it (the most wounded first), 20 s (a purge reward)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kRepentCastMs = 2000;
    inline constexpr std::uint32_t kRepentMs = 2000;
    inline constexpr std::uint32_t kHealCastMs = 3000;
    inline constexpr std::uint32_t kHealPct = 10;
    // Designer gap 9: "starting guess 5k, about 1.3 s of hard mode group damage".
    inline constexpr std::uint32_t kShieldAbsorb = 5000;
    inline constexpr std::uint32_t kShieldMs = 20000;

    // 10% of `maxHealth` (at least 1).
    constexpr std::uint32_t HealAmount(std::uint32_t maxHealth)
    {
        std::uint32_t const v = static_cast<std::uint32_t>(static_cast<std::uint64_t>(maxHealth) * kHealPct / 100u);
        return v ? v : 1;
    }

    struct Ally
    {
        std::uint64_t id = 0;
        float healthPct = 100.f;
        bool shielded = false;
    };

    inline constexpr std::size_t kMaxAllies = kHeroCount + 1;      // Thalnos and the four risen

    // The most wounded ally of the first `count` (ties to the first given: Thalnos is passed first).
    constexpr std::optional<std::size_t> MostWounded(std::array<Ally, kMaxAllies> const& allies, std::size_t count,
        bool unshieldedOnly = false)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < count && i < kMaxAllies; ++i)
        {
            if (unshieldedOnly && allies[i].shielded)
                continue;
            if (!best || allies[i].healthPct < allies[*best].healthPct)
                best = i;
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RH6 Whirlwind: emote line 0 and a 2 s wind-up (he stands still), then 4 s spinning in place: 30% (H) Physical and
    // Weakened each second within 8 yd (the tank included: everyone steps out; staying the whole spin, 120%, is lethal
    // by design). A player is one Blood Ritual stack for the whole spin (once per player per cast)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kWhirlwindRadius = 8.f;
    inline constexpr std::uint32_t kWhirlwindWindupMs = 2000;
    inline constexpr std::uint32_t kWhirlwindSpinMs = 4000;
    inline constexpr std::uint32_t kWhirlwindTickMs = 1000;
    inline constexpr float kWhirlwindPct = 30.f;
    // He walks again once the spin has ended.
    inline constexpr std::uint32_t kWhirlwindHoldMs = kWhirlwindWindupMs + kWhirlwindSpinMs;

    // The risen's melee swings give no Blood Ritual stacks, only their abilities (designer question 1 of the report).
    inline constexpr bool kRisenMeleeFeedsRitual = false;

    // A risen farther than this from the lawn's center (chasing a player off the lawn) walks back: the lawn holds the
    // fight (the arena guard holds Thalnos at 40 yd).
    inline constexpr float kRisenLeashYd = SmThalnos::kLawnArenaYd + 5.f;
    // ...or 5 yd past the lawn's cut on Ironspine's side (RF-1 m-4): a chase never drags a risen into his yard.
    inline constexpr float kRisenLeashSouthY = SmThalnos::kLawnSouthCutY - 5.f;
    inline bool RisenOffLawn(Vec2 p)
    {
        return DungeonKit::Distance(p, SmThalnos::kLawnCenter) > kRisenLeashYd || p.y < kRisenLeashSouthY;
    }
}

#endif
