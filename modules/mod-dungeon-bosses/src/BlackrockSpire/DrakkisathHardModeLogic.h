/*
 * mod-dungeon-bosses, Blackrock Spire B15:
 * General Drakkisath's hard mode, the General's Army, the pure, host-testable part (no engine headers). WP-B15 owns
 * this file: its spell ids (inside kSpellsGeneralsArmy of BlackrockSpireRework.h, 210560-210619), tuning constants,
 * flex target pairs, the herald's rule, the Muster's drill (which squad comes when, with what), the phase gate of his
 * kit, the Champion's Call and Challenge (the ring's centre, the blows, Finesse, the win rule), the squads' moves and
 * the room's points, tested by tests/brs_drakkisath_hard_mode_test.cpp. The engine side is drakkisath_hard_mode.cpp (on
 * B14's hooks, DrakkisathFight.h).
 *
 * Build spec SP 3990-4082 rows DR10-DR19 (design SP 3828-3937, rulings 69-72); handoff section 3.7, section 3.5 row
 * B15, section 3.6 (hard mode numbers), section 3.8 (NM 13). The hard mode exists on heroic only: every percent is of
 * the heroic reference row (the pins pick it); counts "a / b" are 5 players / 6 or more (FlexAB); health is the
 * 5-player value x the flex ladder (DungeonKit::Flex::SetHealth).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_HARD_MODE_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DrakkisathLogic.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitMath.h"
#include "DungeonKitRingLogic.h"
#include "DungeonKitState.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <utility>

namespace BrsGeneralsArmy
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point3;
    using DungeonKit::Vec2;

    float constexpr kPi = 3.14159265f;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsGeneralsArmy;

    // apps/dbc-tools source/npcs/blackrock_spire/drakkisath_hard_mode.py declares every one of them.
    enum GeneralsArmySpells : std::uint32_t
    {
        SPELL_GA_RING_STRIKE            = 210560,   // DR17 the ring's strike (INSTAKILL, spell_dungeon_lethal_strike)
        SPELL_GA_RING_LOOK              = 210561,   // DR17 the ring's look: a 12 yd dynamic object on the carrier
                                                    // (Ring of Flame 35831's PersistentArea, V-2's stock pick)
        SPELL_GA_RING_LOOK_ALT          = 210562,   // DR17 the fallback: V-2's minted fixed-size ring state (SV 90616)
        SPELL_GA_CHALLENGE_BAR          = 210563,   // DR18 his 12 s duel bar (Physical, never kicked)
        SPELL_GA_CHALLENGER             = 210564,   // DR17 the challenger's 12 s mark (DUMMY debuff)
        SPELL_GA_SWEEP                  = 210565,   // DR18 Blackblade Sweep (resolve copy, Physical): 40%
        SPELL_GA_OVERHEAD_CLEAVE        = 210566,   // DR18 Overhead Cleave (resolve copy, Physical): 50%
        SPELL_GA_FIRE_BLAST             = 210567,   // DR18 a Fire Blast circle (resolve copy, Fire): 30%; also phase
                                                    // 1's answer to a distant attacker
        SPELL_GA_RING_OF_FLAME          = 210568,   // DR18 the donut (resolve copy, Fire): 40%
        SPELL_GA_THUNDERCLAP            = 210569,   // DR18 Thunderclap (resolve copy, Physical): 40%
        SPELL_GA_FIRE_BLAST_LOOK        = 210570,   // DR18 Fire Blast 2136's hands and flash (self visual)
        SPELL_GA_RING_OF_FLAME_LOOK     = 210571,   // DR18 Conflagration 16805's breath (self visual)
        SPELL_GA_FINESSE                = 210572,   // DR18 +15% damage done a stack, up to 6, on the challenger
        SPELL_GA_HUMBLED                = 210573,   // DR18 won: +30% damage taken for 10 s, on him
        SPELL_GA_TROPHY                 = 210574,   // DR17 / DR18 lost: +10% damage done a stack, on him
        SPELL_GA_CLEAVING_CHARGE_BAR    = 210575,   // DR13 the Dragonspawn's 1.5 s wind-up (Physical)
        SPELL_GA_CLEAVING_CHARGE        = 210576,   // DR13 the cone's hit (resolve copy, Physical): 35%
        SPELL_GA_CLEAVING_CHARGE_LOOK   = 210577,   // DR13 the swing (Wide Swipe 6749's SV 399, self visual)
        SPELL_GA_COMMAND                = 210578,   // DR13 the Captain's command: +25% damage done, 2 s, refreshed
        SPELL_GA_COMMAND_LOOK           = 210579,   // DR13 Battle Shout 6673's ring on the Captain (self visual)
        SPELL_GA_SCATTERING_FLAME       = 210580,   // DR14 a burst (resolve copy, Fire): 30%
        SPELL_GA_SCATTERING_MARK        = 210581,   // DR14 the 3 s mark on a player (DUMMY debuff)
        SPELL_GA_FIREBALL_VOLLEY        = 210582,   // DR14 the Fire Tongue's 2 s interruptible cast (Fire)
        SPELL_GA_VOLLEY_HIT             = 210583,   // DR14 the landed volley (resolve copy, Fire): 20%, everyone
        SPELL_GA_SHIELD_FRONT           = 210584,   // DR15 the Dragon Guard's shield (DUMMY, passive; the script)
        SPELL_GA_SHIELD_CHARGE_BAR      = 210585,   // DR15 the 2 s wind-up, the shield lowered (Physical)
        SPELL_GA_SHIELD_CHARGE          = 210586,   // DR15 the lane's hit (resolve copy, Physical): 30%
    };
    // 210587-210619 spare.
    std::uint32_t constexpr kFirstSpell = SPELL_GA_RING_STRIKE;
    std::uint32_t constexpr kLastSpell = SPELL_GA_SHIELD_CHARGE;
    static_assert(kFirstSpell == kSpellSlice.first, "the General's Army's spells start its slice");
    static_assert(kLastSpell <= kSpellSlice.last, "the General's Army's spells must stay in its slice");

    // Stock spells the squads keep (SP DR13-DR15, the build spec's unit rows).
    std::uint32_t constexpr SPELL_GA_ARCING_SMASH = 16169;     // the Captain's, on his tank
    std::uint32_t constexpr SPELL_GA_MORTAL_STRIKE = 15708;    // the Captain's
    std::uint32_t constexpr SPELL_GA_SHIELD_SLAM = 15655;      // the Dragon Guards'

    // The ring's look: the stock pick (a dynamic object; V-2: the client's scaling to 12 yd is untested) or V-2's
    // minted fixed-size state. One constant to switch after the playtest.
    std::uint32_t constexpr kRingLookSpell = SPELL_GA_RING_LOOK;

    // Registry tags (per encounter: Drakkisath's; B14 uses 1-6).
    enum GeneralsArmyTags : std::uint32_t
    {
        TAG_GA_CALL             = 30,
        TAG_GA_RING             = 31,
        TAG_GA_BLOW             = 32,
        TAG_GA_ANSWER           = 33,
        TAG_GA_CLEAVING_CHARGE  = 34,
        TAG_GA_SCATTERING_FLAME = 35,
        TAG_GA_VOLLEY           = 36,
        TAG_GA_SHIELD_CHARGE    = 37,
    };

    // The cast queue ids (B14's DungeonKit::CastQueue: hard mode ids from BrsDrakkisath::kHardModeCastBase). The
    // Challenge outranks his own wind-ups (priorities 1-3).
    enum GeneralsArmyCasts : std::uint32_t
    {
        CAST_GA_CHALLENGE   = BrsDrakkisath::kHardModeCastBase + 0,
    };
    std::uint8_t constexpr kChallengePriority = 9;

    // The herald's line (creature_text 300740; S0's range 0-0).
    enum HeraldTexts : std::uint8_t
    {
        SAY_HERALD_ARMED    = 0,    // "Let them come" accepted: he runs to the alcove
    };

    // The herald's gossip (the SQL rev: gossip_menu / npc_text / gossip_menu_option 300740, the option's conditions).
    std::uint32_t constexpr kHeraldGossipMenu = 300740;
    std::uint32_t constexpr kHeraldGossipOption = 0;

    // ----------------------------------------------------------------------------------------------------------------
    // DR10 / DR11 the herald: shown with the insult saved (heroic, Drakkisath alive and not fighting); "Let them come"
    // arms the next pull (the instance's GeneralsArmyChangeAllowed decides; this is the herald's own view of it)
    // ----------------------------------------------------------------------------------------------------------------
    enum class HeraldRefusal : std::uint8_t
    {
        None = 0,           // armed by this answer
        NotHeroic,
        NotInsulted,        // without the insult there is no herald (it is hidden; a GM test can still ask)
        Fighting,           // Drakkisath is in combat
        Dead,               // Drakkisath is dead (this lockout)
        AlreadyArmed,       // armed already (until the attempt ends)
    };

    constexpr HeraldRefusal HeraldRefusalFor(bool heroic, bool insulted, std::uint32_t drakkisathState, bool armed)
    {
        if (!heroic)
            return HeraldRefusal::NotHeroic;
        if (!insulted)
            return HeraldRefusal::NotInsulted;
        if (drakkisathState == DungeonKit::State::InProgress)
            return HeraldRefusal::Fighting;
        if (drakkisathState == DungeonKit::State::Done)
            return HeraldRefusal::Dead;
        if (armed)
            return HeraldRefusal::AlreadyArmed;
        return HeraldRefusal::None;
    }

    constexpr char const* HeraldRefusalText(HeraldRefusal r)
    {
        switch (r)
        {
            case HeraldRefusal::None:           return "";
            case HeraldRefusal::NotHeroic:      return "The general's legions muster only for a heroic assault.";
            case HeraldRefusal::NotInsulted:    return "Lord Victor has no quarrel with you. Yet.";
            case HeraldRefusal::Fighting:       return "The battle has already begun.";
            case HeraldRefusal::Dead:           return "The general has fallen. His legions are scattered.";
            case HeraldRefusal::AlreadyArmed:   return "The legions are already on the march.";
        }
        return "";
    }

    // Where the herald stands: at the entrance while the insult is saved and the general waits; at the alcove once
    // armed; hidden while he fights, after his death, without the insult and off heroic (DR19: the herald returns).
    enum class HeraldPlace : std::uint8_t
    {
        Hidden = 0,
        Entrance,
        Alcove,
    };

    constexpr HeraldPlace HeraldPlaceFor(bool heroic, bool insulted, std::uint32_t drakkisathState, bool armed)
    {
        if (!heroic || !insulted || drakkisathState == DungeonKit::State::InProgress
            || drakkisathState == DungeonKit::State::Done)
            return HeraldPlace::Hidden;
        return armed ? HeraldPlace::Alcove : HeraldPlace::Entrance;
    }

    std::uint32_t constexpr kHeraldPollMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // Health (ruling 72; x the flex ladder through DungeonKit::Flex::SetHealth)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBossHealthAt5 = 240000;            // phase 2 (540,000 at 10)
    std::uint32_t constexpr kEliteGuardHealthAt5 = 30000;       // each
    std::uint32_t constexpr kEliteGuardHeroicHealthAt5 = 32000; // WP-H's heroic 10814: put back when the pull ends
    std::uint32_t constexpr kDragonspawnHealthAt5 = 17000;
    std::uint32_t constexpr kCaptainHealthAt5 = 23000;
    std::uint32_t constexpr kFireTongueHealthAt5 = 13000;
    std::uint32_t constexpr kDragonGuardHealthAt5 = 21000;

    // The base (5-player) health a held boss had before the hard mode set his: max health over the ladder (B9's rule).
    inline std::uint32_t BaseBeforeHardMode(std::uint32_t maxHealth, std::uint32_t players)
    {
        double const ladder = DungeonKit::Flex::Ladder(players);
        return static_cast<std::uint32_t>(std::lround(double(maxHealth) / (ladder > 0. ? ladder : 1.)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR12 / DR16 the Muster and the field: squads every 20 s for 1:30, then every 45 s with the Champion's Call
    // ----------------------------------------------------------------------------------------------------------------
    enum class SquadKind : std::uint8_t
    {
        Vanguard = 0,       // DR13: Dragonspawn (fixate, Cleaving Charge) and a Captain (command, Arcing Smash)
        FireLine = 1,       // DR14: Fire Tongues (Scattering Flame, Fireball Volley) behind a Dragon Guard
        ShieldWall = 2,     // DR15: Dragon Guards in a line (shield front, Shield Charge in turn)
    };

    constexpr char const* SquadName(SquadKind k)
    {
        switch (k)
        {
            case SquadKind::Vanguard:   return "vanguard";
            case SquadKind::FireLine:   return "fire-line";
            case SquadKind::ShieldWall: return "shield-wall";
        }
        return "?";
    }

    struct SquadPlan
    {
        SquadKind kind = SquadKind::Vanguard;
        std::uint8_t dragonspawn = 0;
        std::uint8_t captains = 0;
        std::uint8_t fireTongues = 0;
        std::uint8_t dragonGuards = 0;

        constexpr std::uint32_t Soldiers() const
        {
            return std::uint32_t(dragonspawn) + captains + fireTongues + dragonGuards;
        }

        constexpr std::uint32_t HealthAt5() const
        {
            return dragonspawn * kDragonspawnHealthAt5 + captains * kCaptainHealthAt5
                + fireTongues * kFireTongueHealthAt5 + dragonGuards * kDragonGuardHealthAt5;
        }
    };

    // The drill repeats Vanguard, Fire Line, Shield Wall, each time round one soldier larger (SP DR12: squads 1-5 in
    // phase 1, 6 and 7 in phase 2, "then on in order"); the step stops growing at kMaxSquadStep (a fight that long is
    // already lost: the squads stack).
    std::uint32_t constexpr kMaxSquadStep = 3;

    constexpr SquadPlan PlanSquad(std::uint32_t index)
    {
        SquadPlan p;
        p.kind = static_cast<SquadKind>(index % 3);
        std::uint8_t const step = static_cast<std::uint8_t>(std::min<std::uint32_t>(index / 3, kMaxSquadStep));
        switch (p.kind)
        {
            case SquadKind::Vanguard:
                p.dragonspawn = static_cast<std::uint8_t>(2 + step);
                p.captains = 1;
                break;
            case SquadKind::FireLine:
                p.fireTongues = static_cast<std::uint8_t>(2 + step);
                p.dragonGuards = 1;
                break;
            case SquadKind::ShieldWall:
                p.dragonGuards = static_cast<std::uint8_t>(3 + step);
                break;
        }
        return p;
    }

    std::uint32_t constexpr kMusterMs = 90000;                  // phase 1, on a timer (1:30)
    std::uint32_t constexpr kMusterEveryMs = 20000;             // a squad every 20 s, from 0:00
    std::uint32_t constexpr kMusterSquads = (kMusterMs + kMusterEveryMs - 1) / kMusterEveryMs;
    std::uint32_t constexpr kFieldEveryMs = 45000;              // phase 2: a squad every 45 s, from 0:45
    static_assert(kMusterSquads == 5, "SP DR12: squads 1 to 5 in phase 1");

    // When squad `index` (0-based) marches in, ms since the pull.
    constexpr std::uint64_t SquadArrivalMs(std::uint32_t index)
    {
        if (index < kMusterSquads)
            return std::uint64_t(index) * kMusterEveryMs;
        return kMusterMs + std::uint64_t(index - kMusterSquads + 1) * kFieldEveryMs;
    }

    // A phase 2 squad comes with the Champion's Call (DR16, DR17).
    constexpr bool SquadCallsChallenge(std::uint32_t index)
    {
        return index >= kMusterSquads;
    }

    // The gate a squad uses: alternating, the first through 175946 (0), then 175947 (1).
    constexpr std::uint32_t SquadGate(std::uint32_t index)
    {
        return index % 2;
    }

    enum class Phase : std::uint8_t
    {
        Muster = 1,         // DR12: he stays in his alcove, rooted, commanding; the Guards hold its mouth
        Field = 2,          // DR16: he steps down with any living Guards; his kit at heroic values
    };

    constexpr Phase PhaseAt(std::uint64_t fightMs)
    {
        return fightMs < kMusterMs ? Phase::Muster : Phase::Field;
    }

    // His kit, as the gate sees it (BrsDrakkisath::Ability's values; drakkisath_hard_mode.cpp static_asserts them).
    enum class Kit : std::uint8_t
    {
        Brands = 0,
        Thunderclap = 1,
        Flamestrike = 2,
        BlackbladeSweep = 3,
        Rage = 4,
        SearedFlesh = 5,
        Melee = 6,
    };

    // DR12 / DR16 / DR17: the abilities he uses. Phase 1: his brands (as heroic) and his blade on whoever reaches him
    // (rooted; SP "commanding"). Phase 2: all of it (Seared Flesh at 10 too). During the Champion's Call his three
    // wind-ups wait (the queue stays free, so the Challenge starts as the challenger steps in; he still swings and
    // brands). During the Challenge no brands (he fights the challenger only; B14's hold stops the rest).
    constexpr bool UsesKit(Phase phase, bool calling, bool challenging, Kit k)
    {
        if (phase == Phase::Muster)
            return k == Kit::Brands || k == Kit::Melee;
        if (challenging && k == Kit::Brands)
            return false;
        if (calling && (k == Kit::Thunderclap || k == Kit::Flamestrike || k == Kit::BlackbladeSweep))
            return false;
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // No free damage window (wave 2 lesson 2): rooted in phase 1, he answers anyone who hurts him from beyond his
    // blade's reach with a Fire Blast circle at their feet (dodgeable; per attacker at most every kAnswerEveryMs)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kAnswerBeyondYd = 10.f;
    float constexpr kAnswerRadius = 4.f;
    std::uint32_t constexpr kAnswerWarnMs = 1500;
    float constexpr kAnswerPct = 30.f;
    std::uint32_t constexpr kAnswerEveryMs = 6000;

    constexpr bool AnswersAttacker(Phase phase, float distanceYd)
    {
        return phase == Phase::Muster && distanceYd > kAnswerBeyondYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR17 the Champion's Call: a 4 yd circle 8 yd in front of him for 5 s; the first player in it (not his current
    // tank) is the challenger; bots may claim it 2 s in if no human has (framework check: built in the script)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kCallMs = 5000;
    float constexpr kCallRadius = 4.f;
    float constexpr kCallAheadYd = 8.f;
    float constexpr kCallZBand = 5.f;
    std::uint32_t constexpr kCallBotDelayMs = 2000;

    // DR17: the Call's circle, kCallAheadYd in front of him.
    inline Vec2 CallSpot(Vec2 boss, float facing)
    {
        return DungeonKit::Advance(boss, facing, kCallAheadYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR17 / DR18 the Challenge: a 12 yd ring of fire round him and the challenger for 12 s, lethal (the kit's ring,
    // armed 1.5 s after the close); a blow every 2 s, each telegraphed 1.5 s
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kChallengeMs = 12000;
    float constexpr kRingRadius = DungeonKit::kRingDefaultRadiusYd;    // 12 yd
    float constexpr kRingWidth = DungeonKit::kRingDefaultWidthYd;      // a 2 yd band
    std::uint32_t constexpr kRingArmMs = DungeonKit::kRingArmMs;       // 1.5 s: the push lands first
    std::uint32_t constexpr kRingLifeMs = kChallengeMs - kRingArmMs;   // close to end: 12 s
    // User ruling 2026-11-15 (HANDOFF section 10): pets are pushed out, never killed. The kit then declares the ring
    // SparesPets, so a pet owner's bot keeps no pet margin from it (F-3: with one, no spot fit the Thunderclap).
    bool constexpr kRingStrikesPets = false;
    bool constexpr kRingSparesChallenger = false;   // same ruling: the challenger dies stepping out

    // The ring's centre: on him, unless the challenger stands so far out that the band would be under them; then
    // shifted toward the challenger so they stand kChallengerMaxFromCentreYd from it (both well inside the band).
    float constexpr kChallengerMaxFromCentreYd = kRingRadius - kRingWidth * 0.5f - 1.5f;     // 9.5 yd

    inline Vec2 RingCentre(Vec2 boss, Vec2 challenger)
    {
        float const d = DungeonKit::Distance(boss, challenger);
        if (d <= kChallengerMaxFromCentreYd)
            return boss;
        float const shift = d - kChallengerMaxFromCentreYd;
        return { boss.x + (challenger.x - boss.x) / d * shift, boss.y + (challenger.y - boss.y) / d * shift };
    }

    enum class Blow : std::uint8_t
    {
        Sweep = 0,          // Frontal, 180 degrees 10 yd at the challenger: 40%
        OverheadCleave = 1, // Frontal, 60 degrees 15 yd at the challenger: 50% (its own penalty: no Weakened)
        FireBlast = 2,      // 3 circles of 4 yd at and around the challenger: 30% each
        RingOfFlame = 3,    // a donut 4 to 12 yd from him (get in close): 40%
        Thunderclap = 4,    // 8 yd on him (get out): 40%
    };
    std::size_t constexpr kBlowKinds = 5;

    constexpr char const* BlowName(Blow b)
    {
        switch (b)
        {
            case Blow::Sweep:           return "sweep";
            case Blow::OverheadCleave:  return "overhead-cleave";
            case Blow::FireBlast:       return "fire-blast";
            case Blow::RingOfFlame:     return "ring-of-flame";
            case Blow::Thunderclap:     return "thunderclap";
        }
        return "?";
    }

    struct BlowNumbers
    {
        float pct = 0.f;
        bool weakened = true;
        std::uint32_t spell = 0;
    };

    constexpr BlowNumbers NumbersOf(Blow b)
    {
        switch (b)
        {
            case Blow::Sweep:           return { 40.f, true, SPELL_GA_SWEEP };
            case Blow::OverheadCleave:  return { 50.f, false, SPELL_GA_OVERHEAD_CLEAVE };
            case Blow::FireBlast:       return { 30.f, true, SPELL_GA_FIRE_BLAST };
            case Blow::RingOfFlame:     return { 40.f, true, SPELL_GA_RING_OF_FLAME };
            case Blow::Thunderclap:     return { 40.f, true, SPELL_GA_THUNDERCLAP };
        }
        return {};
    }

    std::uint32_t constexpr kBlows = 6;
    std::uint32_t constexpr kBlowEveryMs = 2000;
    std::uint32_t constexpr kBlowWarnMs = 1500;
    std::uint32_t constexpr kBlowJudgeMs = 100;             // a blow is judged this long after it lands (hits are in)
    float constexpr kSweepAngleDeg = 180.f;
    float constexpr kSweepLength = 10.f;
    float constexpr kCleaveAngleDeg = 60.f;
    float constexpr kCleaveLength = 15.f;
    float constexpr kFireBlastRadius = 4.f;
    float constexpr kFireBlastAroundYd = 5.f;               // the two circles beside the challenger
    float constexpr kRingOfFlameInner = 4.f;
    float constexpr kRingOfFlameOuter = 12.f;
    float constexpr kThunderclapRadius = 8.f;

    // Blow k (0-based) starts its telegraph at k x kBlowEveryMs and lands kBlowWarnMs later: 1.5, 3.5 ... 11.5 s, all
    // inside the 12 s ring.
    constexpr std::uint32_t BlowStartMs(std::uint32_t k) { return k * kBlowEveryMs; }
    constexpr std::uint32_t BlowLandMs(std::uint32_t k) { return BlowStartMs(k) + kBlowWarnMs; }
    static_assert(BlowLandMs(kBlows - 1) + kBlowJudgeMs < kChallengeMs, "every blow lands and is judged in the ring");
    static_assert(BlowLandMs(0) >= kRingArmMs, "the first blow lands once the ring has closed");

    // R-2 ruling (2026-11-15): a Blackblade Sweep never comes right after a Thunderclap. The clap sends the challenger
    // out past 8 yd, and the 10 yd Sweep 2 s later leaves only the band's edge of the 12 yd ring (undodgeable in
    // practice). The numbers stay.
    constexpr bool BlowFollowsOk(Blow before, Blow next)
    {
        return !(before == Blow::Thunderclap && next == Blow::Sweep);
    }

    // The six blows: the five kinds once each in a shuffled order, then one more of the first four blows (never the
    // fifth twice in a row). A Thunderclap followed by the Sweep in the shuffle trades places with it, and the sixth is
    // never the Sweep after a fifth Thunderclap (BlowFollowsOk). `rand(n)` returns [0, n).
    template <class Rand>
    std::array<Blow, kBlows> PlanBlows(Rand&& rand)
    {
        std::array<Blow, kBlowKinds> kinds{ { Blow::Sweep, Blow::OverheadCleave, Blow::FireBlast, Blow::RingOfFlame,
            Blow::Thunderclap } };
        for (std::size_t i = kBlowKinds - 1; i > 0; --i)
            std::swap(kinds[i], kinds[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(i + 1))) % (i + 1)]);
        std::array<Blow, kBlows> out{};
        for (std::size_t i = 0; i < kBlowKinds; ++i)
            out[i] = kinds[i];
        for (std::size_t i = 0; i + 1 < kBlowKinds; ++i)
            if (!BlowFollowsOk(out[i], out[i + 1]))
                std::swap(out[i], out[i + 1]);  // the Sweep first: one Thunderclap, so no new pair
        std::array<Blow, kBlowKinds - 1> pool{};
        std::size_t n = 0;
        for (std::size_t i = 0; i + 1 < kBlowKinds; ++i)
            if (BlowFollowsOk(out[kBlowKinds - 1], out[i]))
                pool[n++] = out[i];
        out[kBlows - 1] = pool[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(n))) % n];
        return out;
    }

    // The Fire Blast circles: one at the challenger, two kFireBlastAroundYd away at `bearing` and bearing + 180
    // degrees (radians), each pulled in so the whole circle stays inside the ring's band.
    inline std::array<Vec2, 3> FireBlastSpots(Vec2 challenger, float bearing, Vec2 ringCentre)
    {
        float const maxFromCentre = kRingRadius - kRingWidth * 0.5f - kFireBlastRadius;
        auto clampIn = [ringCentre, maxFromCentre](Vec2 p)
        {
            float const d = DungeonKit::Distance(ringCentre, p);
            if (d <= maxFromCentre)
                return p;
            return Vec2{ ringCentre.x + (p.x - ringCentre.x) / d * maxFromCentre,
                ringCentre.y + (p.y - ringCentre.y) / d * maxFromCentre };
        };
        return { { challenger, clampIn(DungeonKit::Advance(challenger, bearing, kFireBlastAroundYd)),
            clampIn(DungeonKit::Advance(challenger, bearing + kPi, kFireBlastAroundYd)) } };
    }

    // Finesse: each blow the challenger avoids, +15% damage done until the Challenge ends (up to 6).
    std::int32_t constexpr kFinessePctPerStack = 15;
    std::uint8_t constexpr kFinesseMax = 6;
    std::uint32_t constexpr kFinesseMs = kChallengeMs + 1000;   // removed at the end; a safety past it

    // Win: 18,000 damage by the challenger inside the ring, the same at every size (ruling 72), x the empowered level's
    // health multiplier in empowered heroic (no API for it yet: 1.0; the B15 report).
    std::uint32_t constexpr kWinDamage = 18000;

    inline std::uint32_t WinDamage(double empoweredHealthMultiplier = 1.0)
    {
        double const m = empoweredHealthMultiplier > 0. ? empoweredHealthMultiplier : 1.;
        return static_cast<std::uint32_t>(std::lround(double(kWinDamage) * m));
    }

    enum class ChallengeEnd : std::uint8_t
    {
        Won = 0,            // the damage reached: Humbled (line 6)
        Lost,               // time up short of it: a Trophy (line 7)
        ChallengerDied,     // a Trophy (line 7)
        Unanswered,         // nobody stepped into the Call: a Trophy (line 5)
        Aborted,            // the fight ended (wipe, death, evade): nothing
    };

    constexpr char const* ChallengeEndName(ChallengeEnd e)
    {
        switch (e)
        {
            case ChallengeEnd::Won:             return "won";
            case ChallengeEnd::Lost:            return "lost";
            case ChallengeEnd::ChallengerDied:  return "challenger-died";
            case ChallengeEnd::Unanswered:      return "unanswered";
            case ChallengeEnd::Aborted:         return "aborted";
        }
        return "?";
    }

    // The outcome at a check: the win ends it at once (he staggers); a dead challenger loses; time up judges.
    constexpr std::optional<ChallengeEnd> JudgeChallenge(std::uint32_t damage, std::uint32_t target,
        bool challengerAlive, bool timeUp)
    {
        if (damage >= target)
            return ChallengeEnd::Won;
        if (!challengerAlive)
            return ChallengeEnd::ChallengerDied;
        if (timeUp)
            return ChallengeEnd::Lost;
        return std::nullopt;
    }

    constexpr bool GivesTrophy(ChallengeEnd e)
    {
        return e == ChallengeEnd::Lost || e == ChallengeEnd::ChallengerDied || e == ChallengeEnd::Unanswered;
    }

    std::int32_t constexpr kHumbledPct = 30;                    // damage taken, 10 s
    std::uint32_t constexpr kHumbledMs = 10000;
    std::int32_t constexpr kTrophyPctPerStack = 10;             // his damage done, for the rest of the fight
    std::uint8_t constexpr kTrophyMax = 255;                    // no cap (the aura's own limit)

    // R-2 M-3: the duel's challenger (in the ring, or the one the Call just claimed) is no squad's pick, no squad
    // shape's eligible player and never knocked: a 5 yd Shield Charge knock from the safe annulus of the 8 yd blows
    // (8-11 yd) crosses the band, and the ring kills only a challenger who steps out (wave 2 ruling). 0: no duel.
    constexpr std::uint64_t DuelChallengerOf(bool active, std::uint64_t challenger, std::uint64_t pending)
    {
        return active ? challenger : pending;
    }

    // His Trophies on his non-melee hits (the aura raises his melee; his spells and registry hits ignore caster
    // modifiers): B14's DamageDealt hands every hit of his to OnDamageDealt, which scales the non-melee ones, B14's kit
    // (the brands, Thunderclap, Flamestrike, the Sweep) and this hard mode's blows alike (R-2: the Trophy reaches B14's
    // registry hits). The squads own their own hits (R-2 m-7), so neither Seared Flesh nor a Trophy touches them.
    constexpr float TrophyScale(std::uint32_t trophies)
    {
        return 1.f + float(kTrophyPctPerStack) * float(trophies) / 100.f;
    }

    constexpr std::uint32_t TrophyDamage(std::uint32_t damage, std::uint32_t trophies, bool melee)
    {
        if (melee || !trophies)
            return damage;
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(damage)
            * (100u + static_cast<std::uint64_t>(kTrophyPctPerStack) * trophies) / 100u);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR13 Vanguard: the Dragonspawn fixate a random player (the kit's Chaser) and wind up a 90 degree, 8 yd cone in
    // front of them (the fixated player is exempt: it aims it); the Captain's command gives every other soldier within
    // 10 yd 25% more damage (an aura on their melee and stock spells; the script scales their registry hits)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kCleavingChargeFirstMs = 4000;      // after the soldier reaches the hall
    std::uint32_t constexpr kCleavingChargeEveryMs = 8000;
    std::uint32_t constexpr kCleavingChargeCastMs = 1500;
    float constexpr kCleavingChargeAngleDeg = 90.f;
    float constexpr kCleavingChargeLength = 8.f;
    float constexpr kCleavingChargePct = 35.f;
    float constexpr kCommandRadius = 10.f;
    std::int32_t constexpr kCommandPct = 25;
    std::uint32_t constexpr kCommandRefreshMs = 1000;           // the aura is 2 s, refreshed every second
    std::uint32_t constexpr kCommandAuraMs = 2000;
    std::uint32_t constexpr kCommandLookEveryMs = 5000;
    std::uint32_t constexpr kArcingSmashFirstMs = 5000;
    std::uint32_t constexpr kArcingSmashEveryMs = 8000;
    std::uint32_t constexpr kMortalStrikeFirstMs = 8000;
    std::uint32_t constexpr kMortalStrikeEveryMs = 12000;

    constexpr float CommandScale(bool commanded)
    {
        return commanded ? 1.f + float(kCommandPct) / 100.f : 1.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR14 Fire Line: each Fire Tongue marks 2 / 4 players with a 6 yd circle for 3 s, then each bursts on everyone
    // else inside (Spread); Fireball Volley is the expected interrupt (2 s, landed 20% to everyone, no Weakened)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kScatteringFirstMs = 5000;
    std::uint32_t constexpr kScatteringEveryMs = 10000;
    std::uint32_t constexpr kScatteringWarnMs = 3000;
    float constexpr kScatteringRadius = 6.f;
    float constexpr kScatteringPct = 30.f;
    inline constexpr FlexAB kScatteringTargets{ 2, 4 };
    std::uint32_t constexpr kVolleyFirstMs = 8000;
    std::uint32_t constexpr kVolleyEveryMs = 12000;
    std::uint32_t constexpr kVolleyCastMs = 2000;
    float constexpr kVolleyPct = 20.f;
    std::uint8_t constexpr kVolleyKickPriority = 2;             // below his Flamestrike's 3

    // ----------------------------------------------------------------------------------------------------------------
    // DR15 Shield Wall: 50% less damage from the front; one Dragon Guard of the squad in turn lowers its shield toward
    // a random player and charges a 4 yd lane 25 yd after a 2 s wind-up (30%, Weakened, knocked 5 yd aside)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kShieldFrontArcDeg = 180.f;
    std::int32_t constexpr kShieldFrontTakenPct = -50;
    std::uint32_t constexpr kShieldChargeFirstMs = 5000;
    std::uint32_t constexpr kShieldChargeEveryMs = 10000;
    std::uint32_t constexpr kShieldChargeCastMs = 2000;
    float constexpr kShieldChargeLength = 25.f;
    float constexpr kShieldChargeWidth = 4.f;
    float constexpr kShieldChargePct = 30.f;
    float constexpr kShieldChargeKnockYd = 5.f;
    float constexpr kShieldChargeKnockSpeedZ = 5.f;
    float constexpr kShieldChargeSpeed = 30.f;                  // yd/s, the charge's run
    std::uint32_t constexpr kShieldSlamFirstMs = 6000;
    std::uint32_t constexpr kShieldSlamEveryMs = 10000;

    // The damage a Dragon Guard takes from an attacker at `bearingToAttacker` while it faces `facing` (radians).
    inline std::uint32_t ShieldFrontDamage(std::uint32_t damage, float facing, float bearingToAttacker)
    {
        float diff = std::fmod(bearingToAttacker - facing, 2.f * kPi);
        if (diff > kPi)
            diff -= 2.f * kPi;
        if (diff < -kPi)
            diff += 2.f * kPi;
        float const half = kShieldFrontArcDeg * 0.5f * kPi / 180.f;
        if (std::fabs(diff) > half)
            return damage;
        return static_cast<std::uint32_t>(std::uint64_t(damage) * std::uint32_t(100 + kShieldFrontTakenPct) / 100u);
    }

    // Which side of the lane (start, facing) a point is on: +1 left, -1 right (on the axis reads as left).
    inline int LaneSide(Vec2 start, float facing, Vec2 p)
    {
        float const dx = std::cos(facing);
        float const dy = std::sin(facing);
        float const cross = dx * (p.y - start.y) - dy * (p.x - start.x);
        return cross >= 0.f ? 1 : -1;
    }

    // The knockback's source for a player the lane hit: a point on the lane's axis level with them, set 0.5 yd to the
    // other side, so a player on the axis is still pushed (to its left).
    inline Vec2 KnockSource(Vec2 start, float facing, Vec2 p)
    {
        float const dx = std::cos(facing);
        float const dy = std::sin(facing);
        float const along = (p.x - start.x) * dx + (p.y - start.y) * dy;
        int const side = LaneSide(start, facing, p);
        // the left normal is (-dy, dx); the source sits on the other side of the axis from the player
        return { start.x + dx * along + dy * 0.5f * float(side), start.y + dy * along - dx * 0.5f * float(side) };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The room (handoff section 3.8, NM 13). Points marked [placeholder] need a `.gps` walk in the playtest.
    // ----------------------------------------------------------------------------------------------------------------
    // The herald: the throne room's south entrance (SP; NM 13 could not tell whether y -325 is a wall or the way in, so
    // the spot sits on the hall floor near that end, 47 yd from him) [placeholder].
    inline constexpr Point3 kHeraldEntrance{ 5.0f, -320.0f, 111.04f };
    float constexpr kHeraldEntranceFacing = 0.79f;              // toward his alcove
    // Armed: beside the alcove's north-east lobe, out of the fight's way [placeholder].
    inline constexpr Point3 kHeraldAlcove{ 33.0f, -264.0f, 111.04f };
    float constexpr kHeraldAlcoveFacing = 4.71f;

    // DR12: the Elite Guards hold the alcove's mouth on his two flanks (near their stock spots), facing the hall (-x).
    inline constexpr std::array<Point3, 2> kGuardHoldSpots{ {
        { 30.0f, -293.5f, 111.04f },
        { 30.0f, -278.5f, 111.04f },
    } };
    float constexpr kGuardHoldFacing = kPi;
    float constexpr kGuardHoldReachYd = 8.f;

    // The squads march from the lower floor behind each side gate (x 38.8..65.2, z 104.8..109) up into the hall's
    // north-east / south-east lobe [placeholder: the lower floor's spots].
    inline constexpr std::array<Point3, 2> kSquadSpawn{ {
        { 54.0f, -259.7f, 106.5f },
        { 54.0f, -312.5f, 106.5f },
    } };
    float constexpr kSquadSpawnFacing = kPi;
    float constexpr kSquadSpreadYd = 2.5f;                      // the soldiers stand this far apart across the gate

    // A soldier's spot in its squad: lined up across the gate's axis (y), centred.
    constexpr Vec2 SquadSpot(std::uint32_t gate, std::uint32_t slot, std::uint32_t soldiers)
    {
        Point3 const base = kSquadSpawn[gate % 2];
        float const offset = (float(slot) - (float(soldiers) - 1.f) * 0.5f) * kSquadSpreadYd;
        return { base.x, base.y + offset };
    }

    // A soldier has reached the hall (its moves count from here): on the hall or alcove floor.
    inline bool InRoom(Vec2 p, float z)
    {
        if (z < BrsDrakkisath::kRoomZMin || z > BrsDrakkisath::kRoomZMax)
            return false;
        return DungeonKit::PointInPolygon(BrsDrakkisath::kHallBox, p)
            || DungeonKit::PointInPolygon(BrsDrakkisath::kAlcoveBox, p);
    }
}

#endif
