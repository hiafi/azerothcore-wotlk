/*
 * mod-dungeon-bosses, Blackrock Depths D23:
 * Emperor Dagran Thaurissan (9019) and Princess Moira Bronzebeard (8929) / the High Priestess of Thaurissan (10076),
 * the pure, host-testable part (no engine headers). Build spec S4 "Emperor Dagran Thaurissan"
 * (docs/dungeons/blackrock-depths-4-imperial-seat.md, EM1-EM10; rulings 77-80, 88, 90, 91), handoff sections 3.4 (rows
 * D23), 3.5, 3.6, 3.8 (NM: the throne room, the dais, the guard entries), 3.9 (the `beam-block` row of
 * `blackrock-depths-shapes-2`, tag 21), section 7 #19. Tested by tests/brd_emperor_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsEmperor (211610-211659), declared in apps/dbc-tools
 *                source/npcs/blackrock_depths/emperor.py
 *   Tuning       NH<> constants straight from the build spec (normal / heroic); the unset "stock rescaled" cells (Hand
 *                of Thaurissan, Mind Blast, the Flames proc) and the add melee are this WP's defaults (report,
 *                designer questions)
 *   Phases       the court (both alive), the enrage (Moira dead), and the hard mode's transition and Avatar (D24 on
 *                EmperorFight.h): which beat runs in which, the thresholds (70% / 40% heroic), the Dagran-first branch
 *   Beats        every clock of the fight on one struct (Beats); the engine runs this very struct, the test replays it
 *   Beam         the 2 yd line between two units (Nemesis Moira -> Dagran, the Twilight Tether Ambassador -> Dagran):
 *                who stands on it now (the script's own per-tick judge; the registry Soak is the bots' telegraph)
 *   Waves        the Imperial Guard waves: 2 per wave, at most 4 alive (ruling 91: a wave waits while 4 are up), an
 *                Ambassador with each wave from 70% (heroic)
 *
 * Axes: x north, y west (NAVMESH-REPORT). The throne room is a cross x 1333-1429 by y -847 to -715; the dais (z
 * -87.6, 5 yd above the floor at -92.5) is 21 yd wide (x 1370-1391) at the south end (y about -830 to -847); the
 * throne door is the north end (y -710). Orientation 0 looks along +x, pi / 2 along +y: Dagran's spawn faces 1.33
 * (into the room).
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_EMPEROR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_EMPEROR_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdEmperor
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsEmperor;

    enum EmperorSpells : std::uint32_t
    {
        SPELL_EM_HAND_OF_THAURISSAN  = kSpellSlice.first + 0,    // 211610 EM1 a copy of 17492: Fire hit + 2 s stun
        SPELL_EM_NEMESIS             = kSpellSlice.first + 1,    // 211611 EM2 Moira's 8 s channel into Dagran (beam)
        SPELL_EM_RADIANT_BURN        = kSpellSlice.first + 2,    // 211612 EM2 a blocker's tick (Holy, % of the row)
        SPELL_EM_NEMESIS_HEAL        = kSpellSlice.first + 3,    // 211613 EM2 an open tick's heal (exact, base point 0)
        SPELL_EM_MIND_BLAST          = kSpellSlice.first + 4,    // 211614 EM4 a copy of 15587: 1.5 s, interruptible
        SPELL_EM_NECROSIS            = kSpellSlice.first + 5,    // 211615 EM5 (H) Magic DoT, 6% a second for 10 s
        SPELL_EM_TWILIGHT_TETHER     = kSpellSlice.first + 6,    // 211616 EM6 (H) the Ambassador's channel into Dagran
        SPELL_EM_TWILIGHT_BURN       = kSpellSlice.first + 7,    // 211617 EM6 (H) a tether blocker's tick
        SPELL_EM_TETHER_HEAL         = kSpellSlice.first + 8,    // 211618 EM6 (H) an open tether tick's heal (exact)
        SPELL_EM_FLAMESTRIKE         = kSpellSlice.first + 9,    // 211619 EM7 (H) the circle's hit (resolve copy)
        SPELL_EM_FLAMESTRIKE_BURN    = kSpellSlice.first + 10,   // 211620 EM7 (H) the burning ground's tick
        SPELL_EM_FLAMESTRIKE_LOOK    = kSpellSlice.first + 11,   // 211621 look: Flamestrike's fall at a circle
        SPELL_EM_FLAMESTRIKE_GROUND  = kSpellSlice.first + 12,   // 211622 look: the 6 yd burning ground (stalker aura)
        SPELL_EM_AVATAR_OF_FLAME     = kSpellSlice.first + 13,   // 211623 EM8 the enrage: +25% damage, +60% size
        SPELL_EM_FLAMES              = kSpellSlice.first + 14,   // 211624 EM8 the proc on his melee hits
        SPELL_EM_FIRESTORM           = kSpellSlice.first + 15,   // 211625 EM9 a circle's hit (resolve copy)
        SPELL_EM_FIRESTORM_LOOK      = kSpellSlice.first + 16,   // 211626 look: the eruption at a circle
        SPELL_EM_HAMMER_SLAM_CAST    = kSpellSlice.first + 17,   // 211627 EM10 the 1.5 s wind-up bar (Physical)
        SPELL_EM_HAMMER_SLAM         = kSpellSlice.first + 18,   // 211628 EM10 the cone's hit (resolve copy)
        SPELL_EM_HAMMER_SLAM_LOOK    = kSpellSlice.first + 19,   // 211629 look: the ground crack in the cone
        SPELL_EM_MOIRA_CAGE          = kSpellSlice.first + 20,   // 211630 the fire cage at Moira's base (lasting)
        SPELL_EM_MOIRA_CAGE_WHIRL    = kSpellSlice.first + 21,   // 211631 ... and its flame whirl (lasting)
        // 211632-211659 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_EM_MOIRA_CAGE_WHIRL;
    static_assert(kLastSpell <= kSpellSlice.last, "the Emperor's spells must stay in his slice");

    // Registry tags. 21 is G2's `beam-block` drill row (BM MechanicDrill.h kBrd2GroupTags: the sweep's group bar); the
    // others are this fight's.
    enum EmperorTags : std::uint32_t
    {
        TAG_EM_FLAMESTRIKE      = 1,    // EM7 the impact
        TAG_EM_FLAMESTRIKE_BURN = 2,    // EM7 the burning ground
        TAG_EM_FIRESTORM        = 3,    // EM9
        TAG_EM_HAMMER_SLAM      = 4,    // EM10
        TAG_EM_TANK_SPOT        = 5,    // the main tank's Spot (section 7 #19), bots only
        TAG_EM_NEMESIS          = 21,   // EM2 the beam Soak (drill row `beam-block`, Soak/21)
    };

    // creature_text groups. Dagran 9019: 0-7 stock (aggro with the council alive / dead, the kill line, the five
    // senator lines), 8-10 new (S4 "Text"), 11-13 the gap 38 lines this WP writes (11 and 12 are D24's Avatar casts;
    // 13 Hammer Slam). Moira 8929: 0 stock (the stand-down emote), 1 the Nemesis emote. The High Priestess 10076: 0
    // stock (her aggro yell), 1 the Nemesis emote (her row is new too: she runs Moira's kit). Boss emotes are type 41
    // (rule 2).
    enum EmperorTexts : std::uint8_t
    {
        YELL_EM_AGGRO_COUNCIL     = 0,      // stock "Come to aid the Throne!"
        YELL_EM_AGGRO_ALONE       = 1,      // stock "I will crush you into little tiny pieces!" (every senator dead)
        YELL_EM_SLAY              = 2,      // stock "Hail to the king, baby!"
        YELL_EM_SENATORS_20       = 3,      // stock 3-7: 20%, 40%, 60%, 80%, 100% of the room's senators dead
        YELL_EM_SENATORS_100      = 7,
        YELL_EM_GUARDS            = 8,      // EM3 "Guards! Defend your Emperor!"
        YELL_EM_ENRAGE            = 9,      // EM8 "You will pay for her with fire!"
        YELL_EM_RAGNAROS_AWAKENS  = 10,     // EM11 (D24's transition, said here as it starts)
        EMOTE_EM_MAGMA_CLAP       = 11,     // EM12 (D24 says it), gap 38
        EMOTE_EM_VOLCANIC_BLAST   = 12,     // EM13 (D24 says it on the marked player), gap 38
        EMOTE_EM_HAMMER_SLAM      = 13,     // EM10, gap 38 (the text range needs 0-13: shared-file request)
    };
    enum MoiraTexts : std::uint8_t
    {
        EMOTE_MOIRA_STANDS_DOWN   = 0,      // stock (Moira only: "%s is visibly shaken by the death of ...")
        YELL_PRIESTESS_AGGRO      = 0,      // stock (the High Priestess only: "You will not harm Emperor Thaurissan!")
        EMOTE_MOIRA_NEMESIS       = 1,      // EM2 "%s channels a beam of holy fire into the Emperor!" (both)
    };

    // AI messages between the two halves (DoAction / SetGUID; they live in two files).
    enum EmperorActions : std::int32_t
    {
        ACTION_EM_MOIRA_DIED      = 1,      // Moira -> Dagran: she fell (the enrage)
        ACTION_EM_NEMESIS         = 2,      // Dagran -> Moira: channel Nemesis into him now
        ACTION_EM_CAGE            = 3,      // Dagran -> Moira: the fire cage (the hard mode transition)
        ACTION_EM_UNCAGE          = 4,      // Dagran -> Moira: the cage breaks (the stand-down follows on the kill)
        ACTION_EM_STAND_DOWN      = 5,      // Dagran -> Moira: he fell; she stands down (stock, the bug fixed)
        ACTION_EM_STOP            = 6,      // Dagran -> Moira: drop every cast of the court (a phase change)
        GUID_EM_NECROSIS          = 1,      // Dagran -> Moira (SetGUID): Necrosis on this player now
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "Build spec" and "Tuning starting points"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    // Health at 5 players (section 3.6; normal by the DT HealthModifier, heroic by WP-H's overrides).
    inline constexpr NH<std::uint32_t> kDagranHealth{ 160000, 220000 };
    inline constexpr NH<std::uint32_t> kMoiraHealth{ 50000, 70000 };
    inline constexpr NH<std::uint32_t> kGuardHealth{ 8000, 12000 };
    inline constexpr std::uint32_t kAmbassadorHealth = 10000;   // heroic only (the normal row is never summoned)

    // EM1 Hand of Thaurissan: a copy of 17492 (rule 15): the stun drops from 5 s to 2 s (ruling 78), any player, the
    // tank included (rulings 88, 90: the healer watches for it). First at 4 s, then every 12-15 s. The hit is "stock
    // rescaled" (gap 36): this WP's default 12% / 15% of the target's row (the tank row on the tank).
    inline constexpr NH<float> kHandPct{ 12.f, 15.f };
    inline constexpr std::uint32_t kHandStunMs = 2000;
    inline constexpr std::uint32_t kHandFirstMs = 4000;
    inline constexpr std::uint32_t kHandEveryMinMs = 12000;
    inline constexpr std::uint32_t kHandEveryMaxMs = 15000;
    inline constexpr float kHandRangeYd = 30.f;

    // EM2 Shadow Word: Nemesis: Moira, first at 12 s, then every 25 s (heroic 20 s): an 8 s channel into Dagran, not
    // interruptible, a tick a second. A tick with a player on the 2 yd beam burns every blocker for 5% / 8% of their
    // row (Radiant Burn, no Weakened); a tick with nobody on it heals both for 1.5% of their health (8 open ticks =
    // 12%). The bots' Soak (tag 21) is G2's drill row: registered as the channel starts, 3 s to step in, then judged
    // every second for the last 5.
    inline constexpr std::uint32_t kNemesisFirstMs = 12000;
    inline constexpr NH<std::uint32_t> kNemesisEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kNemesisChannelMs = 8000;
    inline constexpr std::uint32_t kNemesisTickMs = 1000;
    inline constexpr std::uint32_t kNemesisTicks = kNemesisChannelMs / kNemesisTickMs;
    inline constexpr NH<float> kRadiantBurnPct{ 5.f, 8.f };
    inline constexpr float kNemesisHealPct = 1.5f;              // of each one's maximum health, per open tick
    inline constexpr float kBeamWidthYd = 2.f;                  // section 7 #19 ("beam 2 yd wide")
    inline constexpr std::uint32_t kNemesisSoakWarnMs = 3000;   // G2: "3 s to step in"
    inline constexpr std::uint32_t kNemesisSoakLiveMs = kNemesisChannelMs - kNemesisSoakWarnMs;    // judged 5 s
    // G2's finding: a two-unit line keeps its registration length. The Soak is registered again when the live beam
    // drifts this far from it (the tank walking Dagran), as Malor's beam does; never in the last 2 s.
    inline constexpr float kBeamRefreshDriftYd = 1.5f;
    inline constexpr std::uint32_t kBeamRefreshMinLeftMs = 2000;
    inline constexpr std::uint32_t kBeamRefreshWarnMs = 1000;

    // EM3 Imperial Guard: first at 20 s, then every 30 s (heroic 25 s): 2 elite guards march in from the wing ends (NM
    // 4.6: the throne room has no other door). At most 4 alive (ruling 91): a wave waits while 4 are up and then
    // brings only as many as fit. No waves once he enrages or rises as the Avatar.
    inline constexpr std::uint32_t kGuardFirstMs = 20000;
    inline constexpr NH<std::uint32_t> kGuardEveryMs{ 30000, 25000 };
    inline constexpr std::uint32_t kGuardsPerWave = 2;
    inline constexpr std::uint32_t kGuardsMaxAlive = 4;

    // EM4 Mind Blast: a copy of 15587 (rule 15): Moira's 1.5 s cast on her target, interruptible (the descriptor's
    // interrupt list: a reward), first at 8 s, then every 14-18 s (stock). "Stock rescaled": 10% / 12% of the row.
    inline constexpr NH<float> kMindBlastPct{ 10.f, 12.f };
    inline constexpr std::uint32_t kMindBlastCastMs = 1500;
    inline constexpr std::uint32_t kMindBlastFirstMs = 8000;
    inline constexpr std::uint32_t kMindBlastEveryMinMs = 14000;
    inline constexpr std::uint32_t kMindBlastEveryMaxMs = 18000;
    inline constexpr float kMindBlastRangeYd = 30.f;

    // EM5 Shadow Word: Necrosis (heroic): Moira, first at 8 s, then every 15 s: a Magic damage over time on a random
    // player (the tank included, ruling 88), 6% a second for 10 s. The dispel is expected (the descriptor).
    inline constexpr std::uint32_t kNecrosisFirstMs = 8000;
    inline constexpr std::uint32_t kNecrosisEveryMs = 15000;
    inline constexpr float kNecrosisTickPct = 6.f;
    inline constexpr std::uint32_t kNecrosisTickMs = 1000;
    inline constexpr std::uint32_t kNecrosisMs = 10000;

    // EM6 Twilight's Hammer Ambassador (heroic, from 70% of Dagran's health): each guard wave from then on brings one.
    // It walks to its stand (kAmbassadorStandYd from Dagran, toward its entry), roots and channels the Twilight Tether
    // into him until it dies: an open tick heals him 0.5% of his health, a blocker takes 3% of their row instead.
    inline constexpr float kAmbassadorPct = 70.f;
    inline constexpr float kTetherHealPct = 0.5f;
    inline constexpr float kTetherBurnPct = 3.f;
    inline constexpr std::uint32_t kTetherTickMs = 1000;
    inline constexpr float kAmbassadorStandYd = 20.f;
    inline constexpr float kTetherRangeYd = 35.f;               // farther (the tank walked Dagran off): it walks again

    // EM7 Flamestrike (heroic, from 40% of Dagran's health): every 12 s a 6 yd circle under every player (the tank
    // too) plus 3 at random floor spots of the room, a 2 s ring, 45% + Weakened, then 4 s of burning ground at 8% a
    // second. Not in the Avatar phase (D24's kit has its own).
    inline constexpr float kFlamestrikePct = 40.f;
    inline constexpr std::uint32_t kFlamestrikeEveryMs = 12000;
    inline constexpr std::uint32_t kFlamestrikeFirstMs = 2000;      // after the threshold is crossed
    inline constexpr float kFlamestrikeRadiusYd = 6.f;
    inline constexpr std::uint32_t kFlamestrikeWarnMs = 2000;
    inline constexpr float kFlamestrikeHitPct = 45.f;
    inline constexpr std::uint32_t kFlamestrikeBurnMs = 4000;
    inline constexpr std::uint32_t kFlamestrikeBurnTickMs = 1000;
    inline constexpr float kFlamestrikeBurnPct = 8.f;
    inline constexpr std::uint32_t kFlamestrikeRandomSpots = 3;
    inline constexpr float kFlamestrikeSpotMinYd = 8.f;             // the random spots: this far from Dagran ...
    inline constexpr float kFlamestrikeSpotMaxYd = 30.f;            // ... to this far

    // EM8 Avatar of Flame (the standard enrage, Moira dead): no immunity any more; +25% damage done, +60% size (the
    // stock look), and the Flames proc on his melee hits ("stock rescaled": 4% / 5% of the victim's row, the tank row
    // on the tank). For the rest of the fight.
    inline constexpr float kEnrageDamagePct = 25.f;
    inline constexpr float kEnrageScalePct = 60.f;
    inline constexpr NH<float> kFlamesPct{ 4.f, 5.f };

    // EM9 Firestorm (enrage; it continues in the Avatar phase on heroic values): from 5 s after the enrage, every 12 s
    // (heroic 10 s), 3 (heroic 4) 6 yd circles under random players (the tank included), a 2 s marker, 25% / 40% +
    // Weakened.
    inline constexpr std::uint32_t kFirestormAfterMs = 5000;
    inline constexpr NH<std::uint32_t> kFirestormEveryMs{ 12000, 10000 };
    inline constexpr NH<std::uint32_t> kFirestormCount{ 3, 4 };
    inline constexpr float kFirestormRadiusYd = 6.f;
    inline constexpr std::uint32_t kFirestormWarnMs = 2000;
    inline constexpr NH<float> kFirestormPct{ 25.f, 40.f };

    // EM10 Hammer Slam (enrage): from 8 s after the enrage, every 15 s: a 1.5 s wind-up, then a 10 yd frontal cone on
    // the tank; the tank is exempt, everyone else in it takes 40% / 60%. No Weakened on any difficulty (the heroic hit
    // is over 50%: its own penalty; wrap-up fix). The cone's angle is unset in the spec: 90 degrees (designer
    // question).
    inline constexpr std::uint32_t kHammerSlamAfterMs = 8000;
    inline constexpr std::uint32_t kHammerSlamEveryMs = 15000;
    inline constexpr std::uint32_t kHammerSlamCastMs = 1500;
    inline constexpr float kHammerSlamLengthYd = 10.f;
    inline constexpr float kHammerSlamAngleDeg = 90.f;
    inline constexpr NH<float> kHammerSlamPct{ 40.f, 60.f };

    // EM11 Ragnaros Awakens (D24, heroic): lethal damage to Dagran while Moira lives starts a 3 s transition (he is
    // held at 1 health); D24 rises as the Avatar at its end.
    inline constexpr std::uint32_t kTransitionMs = 3000;

    // The tank's Spot (section 7 #19: Moira roots at her throne-side spot, the tank holds Dagran 12-20 yd from her): a
    // Spot for the main tank on the floor in front of the dais, re-posted every kTankSpotEveryMs while Moira stands.
    inline constexpr std::uint32_t kTankSpotEveryMs = 20000;
    inline constexpr float kTankSpotRadiusYd = 3.f;
    inline constexpr float kHoldMinYd = 12.f;
    inline constexpr float kHoldMaxYd = 20.f;

    // Shared beats.
    inline constexpr std::uint32_t kRetryMs = 1000;     // a beat refused (a cast going on, nobody to pick): again soon

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry (NAVMESH 4.6; [db] spawns)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kFloorZ = -92.5f;                    // the throne room's floor
    inline constexpr float kDaisZ = -87.6f;                     // the dais (Dagran's and Moira's spawns)
    // Moira's spot: her spawn on the dais, 4.4 yd from his throne. She roots there for the whole fight.
    inline constexpr BlackrockDepthsRework::Point3 kMoiraSpot = BlackrockDepthsRework::kMoiraSpawn;
    // The main tank's Spot: the floor in front of the dais, 16 yd from Moira (Dagran stands within melee reach of it:
    // 13-19 yd from her, inside section 7 #19's 12-20).
    inline constexpr Vec2 kTankSpot{ 1376.0f, -818.0f };
    // The two wing ends of the transept (NM 4.6), where the guards and the Ambassadors march in from.
    inline constexpr std::array<BlackrockDepthsRework::Point3, 2> kGuardEntries{ {
        { 1335.5f, -770.0f, -92.5f },       // west wing
        { 1427.0f, -770.0f, -92.5f },       // east wing
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // Phases
    // ----------------------------------------------------------------------------------------------------------------

    enum class Phase : std::uint8_t
    {
        Idle,           // out of combat
        Court,          // both alive: Nemesis, guards, Hand, Mind Blast, (H) Necrosis, Ambassadors, Flamestrike
        Enraged,        // Moira dead: Avatar of Flame, Firestorm, Hammer Slam, Hand, (H) Flamestrike
        Transition,     // the hard mode (D24): 3 s at 1 health, nothing of his runs
        Avatar,         // the hard mode (D24): D24's kit; of his own, only what EmperorHardMode::AvatarBeat allows
    };

    // The beats of the fight (Moira's Mind Blast is her own; Nemesis and Necrosis are his clocks, cast through her).
    enum class Beat : std::uint8_t
    {
        Hand,
        Nemesis,
        Guards,
        Necrosis,
        Flamestrike,
        Firestorm,
        HammerSlam,
        TankSpot,
        Count,
    };
    inline constexpr std::size_t kBeatCount = static_cast<std::size_t>(Beat::Count);

    // May `beat` run in `phase` (in the Avatar phase this is the default of EmperorHardMode::AvatarBeat: only
    // Firestorm, "Firestorm continues"). `heroic` gates the heroic-only beats.
    constexpr bool BeatRunsIn(Beat beat, Phase phase, bool heroic)
    {
        switch (beat)
        {
            case Beat::Hand:
                return phase == Phase::Court || phase == Phase::Enraged;
            case Beat::Nemesis:
            case Beat::Guards:
            case Beat::TankSpot:
                return phase == Phase::Court;
            case Beat::Necrosis:
                return heroic && phase == Phase::Court;
            case Beat::Flamestrike:
                return heroic && (phase == Phase::Court || phase == Phase::Enraged);
            case Beat::Firestorm:
                return phase == Phase::Enraged || phase == Phase::Avatar;
            case Beat::HammerSlam:
                return phase == Phase::Enraged;
            default:
                return false;
        }
    }

    // The hard mode's branch (S4 "Hard mode", ruling 77): lethal damage to Dagran while Moira lives, on heroic, with
    // D24's hard mode registered, in the court phase, turns into Ragnaros Awakens. Anything else is a real kill (on
    // normal, and on heroic without D24, "Dagran first" ends the fight and Moira stands down, as stock). Once the
    // instance refused the awakening in this pull (`refusedThisPull`), the next lethal hit is a real kill: the 1 health
    // hold is never re-armed (R-2-C m1).
    constexpr bool AwakensOnLethal(bool heroic, bool moiraAlive, bool hardModeRegistered, Phase phase,
        bool refusedThisPull)
    {
        return heroic && moiraAlive && hardModeRegistered && phase == Phase::Court && !refusedThisPull;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The clocks
    // ----------------------------------------------------------------------------------------------------------------

    struct Beats
    {
        bool heroic = false;
        std::array<std::uint64_t, kBeatCount> at{};     // the next firing on the AI's clock; 0 = not scheduled

        std::uint64_t& At(Beat b) { return at[static_cast<std::size_t>(b)]; }
        std::uint64_t At(Beat b) const { return at[static_cast<std::size_t>(b)]; }

        // The pull (the court): Hand 4 s, Nemesis 12 s, guards 20 s, the tank Spot at once, Necrosis 8 s (heroic).
        // Flamestrike waits for 40%, the enrage's beats for the enrage.
        void Start(bool isHeroic, std::uint64_t now)
        {
            heroic = isHeroic;
            at.fill(0);
            At(Beat::Hand) = now + kHandFirstMs;
            At(Beat::Nemesis) = now + kNemesisFirstMs;
            At(Beat::Guards) = now + kGuardFirstMs;
            At(Beat::TankSpot) = now + 1;
            if (heroic)
                At(Beat::Necrosis) = now + kNecrosisFirstMs;
        }

        // Moira fell: the court's beats stop, Firestorm 5 s and Hammer Slam 8 s later (the Hand and a running
        // Flamestrike keep their clocks).
        void Enrage(std::uint64_t now)
        {
            At(Beat::Nemesis) = 0;
            At(Beat::Guards) = 0;
            At(Beat::Necrosis) = 0;
            At(Beat::TankSpot) = 0;
            At(Beat::Firestorm) = now + kFirestormAfterMs;
            At(Beat::HammerSlam) = now + kHammerSlamAfterMs;
        }

        // Heroic, Dagran crossed 40%: the first Flamestrike 2 s later (once).
        void ArmFlamestrike(std::uint64_t now)
        {
            if (heroic && !At(Beat::Flamestrike))
                At(Beat::Flamestrike) = now + kFlamestrikeFirstMs;
        }

        // The hard mode's transition: everything stops.
        void Stop()
        {
            at.fill(0);
        }

        // The Avatar rose: Firestorm (heroic values) `firstFirestormMs` later (D24 may move it); nothing else of his.
        void Avatar(std::uint64_t now, std::uint32_t firstFirestormMs = kFirestormAfterMs)
        {
            at.fill(0);
            At(Beat::Firestorm) = now + firstFirestormMs;
        }

        bool Due(Beat b, std::uint64_t now) const
        {
            std::uint64_t const t = At(b);
            return t && now >= t;
        }

        // A firing: the next one a cadence later (`gapMs`: a random cadence, the Hand's 12-15 s), counted from when it
        // was due, so a beat that waited for a cast never pushes the next one (unless it waited longer than a cadence).
        void Fired(Beat b, std::uint64_t now, std::uint32_t gapMs = 0)
        {
            std::uint32_t const every = gapMs ? gapMs : Every(b);
            if (!every)
            {
                At(b) = 0;
                return;
            }
            std::uint64_t const due = At(b) ? At(b) : now;
            At(b) = std::max<std::uint64_t>(due + every, now + 1);
        }

        void Retry(Beat b, std::uint64_t now, std::uint32_t retryMs = kRetryMs)
        {
            At(b) = now + retryMs;
        }

        std::uint32_t Every(Beat b) const
        {
            switch (b)
            {
                case Beat::Hand:        return kHandEveryMinMs;
                case Beat::Nemesis:     return kNemesisEveryMs(heroic);
                case Beat::Guards:      return kGuardEveryMs(heroic);
                case Beat::Necrosis:    return kNecrosisEveryMs;
                case Beat::Flamestrike: return kFlamestrikeEveryMs;
                case Beat::Firestorm:   return kFirestormEveryMs(heroic);
                case Beat::HammerSlam:  return kHammerSlamEveryMs;
                case Beat::TankSpot:    return kTankSpotEveryMs;
                default:                return 0;
            }
        }
    };

    // A threshold (heroic; Dagran's health) crossed this tick: the health percent fell to or under it, never again
    // once latched.
    constexpr bool Crossed(float healthPct, float threshold, bool latched)
    {
        return !latched && healthPct <= threshold;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beam (Nemesis, the Twilight Tether)
    // ----------------------------------------------------------------------------------------------------------------

    // `p` stands on the beam from `a` to `b` of total width `width`: its projection falls strictly between the two ends
    // (a player beyond either end is not in the beam) and it is within width / 2 of the line.
    inline bool OnBeam(Vec2 a, Vec2 b, float width, Vec2 p)
    {
        float const dx = b.x - a.x;
        float const dy = b.y - a.y;
        float const len2 = dx * dx + dy * dy;
        if (len2 < 1e-4f)
            return false;
        float const t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / len2;
        if (t <= 0.f || t >= 1.f)
            return false;
        float const cx = a.x + t * dx;
        float const cy = a.y + t * dy;
        return std::hypot(p.x - cx, p.y - cy) <= width * 0.5f;
    }

    // The indexes of `points` standing on the beam (every one of them blocks: each takes the burn).
    inline std::vector<std::size_t> BeamBlockers(Vec2 a, Vec2 b, float width, std::vector<Vec2> const& points)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < points.size(); ++i)
            if (OnBeam(a, b, width, points[i]))
                out.push_back(i);
        return out;
    }

    // An open tick's heal: `pct` of `maxHealth`, rounded, at least 1.
    constexpr std::uint32_t TickHeal(std::uint32_t maxHealth, float pct)
    {
        float const amount = static_cast<float>(maxHealth) * pct / 100.f;
        return amount < 1.f ? 1u : static_cast<std::uint32_t>(amount + 0.5f);
    }

    // The Soak's registered length has drifted far enough from the live beam to register it again.
    inline bool BeamNeedsRefresh(float registeredYd, float liveYd)
    {
        return registeredYd > 0.f && std::fabs(registeredYd - liveYd) >= kBeamRefreshDriftYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The guard waves
    // ----------------------------------------------------------------------------------------------------------------

    struct Wave
    {
        std::uint32_t guards = 0;
        bool ambassador = false;
        bool waits = false;         // 4 guards up: the wave waits (ruling 91)
    };

    // The wave due now with `guardsAlive` guards up: 2 at most, never past 4 alive; while 4 are up it waits. From 70%
    // (heroic) a wave that comes brings an Ambassador with it.
    constexpr Wave WaveFor(std::uint32_t guardsAlive, bool ambassadorsArmed)
    {
        Wave w;
        if (guardsAlive >= kGuardsMaxAlive)
        {
            w.waits = true;
            return w;
        }
        w.guards = std::min(kGuardsPerWave, kGuardsMaxAlive - guardsAlive);
        w.ambassador = ambassadorsArmed;
        return w;
    }

    // The entry a guard of a wave marches from: one from each wing (`index` 0 and 1), a lone guard from a random wing
    // (`coin`).
    constexpr std::size_t GuardEntryFor(std::uint32_t index, std::uint32_t count, std::uint32_t coin)
    {
        return count == 1 ? (coin & 1u) : (index & 1u);
    }

    // The Ambassador's stand: `standYd` from Dagran toward its entry (where it walks to, roots and channels).
    inline Vec2 AmbassadorStand(Vec2 dagran, Vec2 entry, float standYd = kAmbassadorStandYd)
    {
        float const d = DungeonKit::Distance(dagran, entry);
        if (d <= standYd || d < 1e-3f)
            return entry;
        float const k = standYd / d;
        return { dagran.x + (entry.x - dagran.x) * k, dagran.y + (entry.y - dagran.y) * k };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Flamestrike (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // The circles of one Flamestrike: one under every player of the fight, plus 3 random spots.
    constexpr std::uint32_t FlamestrikeCircles(std::uint32_t players)
    {
        return players + kFlamestrikeRandomSpots;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The senators (stock: the instance pushes the share of the room's senators dead; a yell per 20%)
    // ----------------------------------------------------------------------------------------------------------------

    // The yell for `pctDead` when `yelled` of the five were said already: groups 3-7 at 20, 40, 60, 80, 100%, one per
    // push (stock). nullopt: none due.
    constexpr std::optional<std::uint8_t> SenatorYell(std::uint32_t pctDead, std::uint32_t yelled)
    {
        if (yelled >= 5 || pctDead < 20 * (yelled + 1))
            return std::nullopt;
        return static_cast<std::uint8_t>(YELL_EM_SENATORS_20 + yelled);
    }

    // The aggro yell: the council line while a senator stands, the "crush you" line once all five yells were said.
    constexpr std::uint8_t AggroYell(std::uint32_t senatorYells)
    {
        return senatorYells >= 5 ? YELL_EM_AGGRO_ALONE : YELL_EM_AGGRO_COUNCIL;
    }
}

#endif
