/*
 * mod-dungeon-bosses, Gnomeregan D6: Mekgineer Thermaplugg's pure, host-testable part (no engine headers): his spell
 * ids (inside kSpellsThermaplugg, 214490-214539), text groups, the bomb types and faces, the plate ranks, every number
 * of the Build spec (SP 1667-1736, rulings 37-42; handoff sections 3.5 row D6, 3.6, 3.8, 7 #30 A, #31 B, #36-#38, #40
 * A) per mode (normal, heroic, and the Whole Workshop's raised values of SP 1799), the beat clock, the picks, the blast
 * geometry, The Big One's split, the packages' health thresholds and the drill tags. Tested by
 * tests/gnomer_thermaplugg_test.cpp. Health is GnomereganRework.h Health: never restated here. ThermapluggFight.h
 * shares the namespace.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_LOGIC_H

#include "GnomereganRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace GnomerThermaplugg
{
    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsThermaplugg;

    // The DT file (source/npcs/gnomeregan/thermaplugg.py) declares the same ids; lib/test_gnomeregan_thermaplugg.py
    // pins the two together. 214512-214539 are spare.
    enum ThermapluggSpells : std::uint32_t
    {
        SPELL_MT_FACE_BEAM          = 214490,   // MT1 the beam between him and a face (the face stalker casts it)
        SPELL_MT_BOMB_MARK          = 214491,   // MT3 the mark on a bomb's target (the bomb is its caster)
        SPELL_MT_BOMB_BLAST         = 214492,   // MT3 the Walking Bomb's blast (resolve copy, Fire)
        SPELL_MT_BLAST_LOOK         = 214493,   // a bomb's explosion (on itself)
        SPELL_MT_BLAST_FLASH        = 214494,   // the ground flash (the Sticky Bomb's blast, The Big One's)
        SPELL_MT_LOCKED_OUT         = 214495,   // MT4 the plate lockout, 30 s
        SPELL_MT_MINE_LOB           = 214496,   // MT5 the lob (him at a player; a face at a Sticky Bomb's carrier)
        SPELL_MT_MINE_BLAST         = 214497,   // MT5 the mine's blast (resolve copy, Fire)
        SPELL_MT_MINE_LOOK          = 214498,   // MT5 the mine body's explosion
        SPELL_MT_KNOCK_AWAY         = 214499,   // MT7 the stock 10101 copy: weapon hit and knockback
        SPELL_MT_DETONATOR          = 214500,   // MT14 Remote Detonator, the 3 s bar (Fire, kickable)
        SPELL_MT_INCENDIARY_BLAST   = 214501,   // MT9 (resolve copy, Fire)
        SPELL_MT_FIRE_PATCH         = 214502,   // MT9 the patch's tick (resolve copy, Fire)
        SPELL_MT_FIRE_PATCH_LOOK    = 214503,   // MT9 the lasting patch on its stalker
        SPELL_MT_FIRE_PATCH_CAST    = 214504,   // MT9 the patch's one-shot burst
        SPELL_MT_FROST_BLAST        = 214505,   // MT10 (resolve copy, Frost)
        SPELL_MT_FROST_ROOT         = 214506,   // MT10 the 3 s root rider (Magic: a reward)
        SPELL_MT_RADIO_BLAST        = 214507,   // MT11 (resolve copy, Nature)
        SPELL_MT_RADIO_POISON       = 214508,   // MT11 the stacking Poison rider (a reward)
        SPELL_MT_STICKY_BOMB        = 214509,   // MT12 the bomb on its carrier, 5 s
        SPELL_MT_STICKY_BLAST       = 214510,   // MT12 (resolve copy, Fire)
        SPELL_MT_BIG_ONE_BLAST      = 214511,   // MT13 (resolve copy, Fire)
    };

    // creature_text 7800 (handoff rule 35: the stock groups 0-3 stay, re-cut by the rev to SP's table). Groups 9 to 11
    // are the hard mode packages' (D6Ha 9, D6Hb 10 and 11), said through ThermapluggFight::Say.
    enum ThermapluggTexts : std::uint8_t
    {
        SAY_MT_AGGRO        = 0,    // "Usurpers! Gnomeregan is mine!" (5807)
        SAY_MT_OVERRIDE     = 1,    // "My machines are the future! ..." (5808): MT6
        SAY_MT_MINES        = 2,    // "Explosions! MORE explosions! ..." (5809): MT5
        SAY_MT_KILL         = 3,    // "And STAY dead!" (5810): a player's death
        EMOTE_MT_FACE       = 4,    // "%s opens a bomb chute!": MT1
        EMOTE_MT_OVERRIDE   = 5,    // "%s overrides the bomb chutes!": MT6
        EMOTE_MT_STICKY     = 6,    // "A Sticky Bomb latches onto $n!": MT12
        EMOTE_MT_BIG_ONE    = 7,    // "The Big One rolls out. Share the blast!": MT13
        EMOTE_MT_DETONATOR  = 8,    // "%s reaches for his detonator!": MT14
    };
    inline constexpr std::uint8_t kFirstPackageTextGroup = 9;

    // The registry tags of his mechanics: G1's `gnomeregan-shapes` block for rows 8 and 9 (STAGE-G1-REPORT "Bars",
    // BM MechanicDrill.h kGnBarTags; LESSONS A.3 #4), so a live ledger reads as the drill's. 78 and 79 are not drilled.
    enum ThermapluggTags : std::uint32_t
    {
        TAG_MT_BIG_ONE      = 70,   // MT13 the Stack on The Big One (drill Stack/70, gated)
        TAG_MT_PLATE        = 71,   // MT4 the plates, ranked DwellSoaks (drill Soak/71, group)
        TAG_MT_BOMB_RING    = 72,   // MT3 the 8 yd outline on a walking bomb (telegraph only; drill Zone/72, reported)
        TAG_MT_BOMB_BLAST   = 73,   // MT3, MT8 to MT11, MT13, MT14 the blasts (RegistryHit; drill Zone/73, reported)
        TAG_MT_BOMB_RUN     = 74,   // MT3 the marked player's keep-away (RunOut, bots only; drill RunOut/74, gated)
        TAG_MT_MINE         = 75,   // MT5 the mine's trigger ring and its blast (drill Zone/75, gated)
        TAG_MT_MINE_RING    = 76,   // MT5 the 6 yd blast ring (telegraph only; drill Zone/76, reported)
        TAG_MT_DETONATOR    = 77,   // MT14 the drill's "not kicked" bar (Soak/77); live the cast has no zone
        TAG_MT_STICKY       = 78,   // MT12 the Sticky Bomb's RunOut (not drilled)
        TAG_MT_FIRE_PATCH   = 79,   // MT9 the fire patch (not drilled)
    };
    inline constexpr std::uint32_t kFirstPackageTag = 80;    // the packages' own tags (D6Hb's drill row 10: 80-85)

    struct DrillTag
    {
        char const* name;
        std::uint32_t tag;
    };

    // LESSONS A.3 #4: the tag table diffed against BM's gnomeregan-shapes drill (rows 8 and 9) at WP close.
    inline constexpr std::array<DrillTag, 10> kDrillTags{ {
        { "big-one", TAG_MT_BIG_ONE }, { "plate", TAG_MT_PLATE }, { "bomb-ring", TAG_MT_BOMB_RING },
        { "bomb-blast", TAG_MT_BOMB_BLAST }, { "bomb-run", TAG_MT_BOMB_RUN }, { "mine", TAG_MT_MINE },
        { "mine-ring", TAG_MT_MINE_RING }, { "detonator", TAG_MT_DETONATOR }, { "sticky", TAG_MT_STICKY },
        { "fire-patch", TAG_MT_FIRE_PATCH },
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // Modes, faces, bombs
    // ----------------------------------------------------------------------------------------------------------------
    enum class Mode : std::uint8_t
    {
        Normal = 0,
        Heroic = 1,
        HardMode = 2,   // the Whole Workshop: heroic with the packages built (SP 1799's column)
    };
    inline constexpr std::array<char const*, 3> kModeNames{ { "normal", "heroic", "hardmode" } };

    constexpr Mode ModeFor(bool heroic, bool hardMode)
    {
        return !heroic ? Mode::Normal : hardMode ? Mode::HardMode : Mode::Heroic;
    }

    constexpr std::size_t ModeIndex(Mode mode)
    {
        return static_cast<std::size_t>(mode);
    }

    // Ruling 64: face 01 Walking, 02 Incendiary, 03 Frost, 04 Radioactive, 05 Sticky, 06 The Big One (heroic); every
    // face builds Walking Bombs on normal. The face index is the face's number - 1.
    enum class BombType : std::uint8_t
    {
        Walking = 0,
        Incendiary = 1,
        Frost = 2,
        Radioactive = 3,
        Sticky = 4,
        BigOne = 5,
    };
    std::size_t constexpr kBombTypeCount = 6;

    inline constexpr std::array<char const*, kBombTypeCount> kBombTypeNames{ {
        "walking", "incendiary", "frost", "radioactive", "sticky", "big-one" } };

    constexpr BombType FaceBomb(Mode mode, std::uint32_t face)
    {
        return mode == Mode::Normal || face >= GnomereganRework::kFaceCount ? BombType::Walking
            : static_cast<BombType>(face);
    }

    // The creature of a bomb type (0: the Sticky Bomb is an aura, not a unit). Never the gear's 301100 (s7 #40 A).
    constexpr std::uint32_t BombEntry(BombType type)
    {
        switch (type)
        {
            case BombType::Walking:     return GnomereganRework::NPC_WALKING_BOMB;
            case BombType::Incendiary:  return GnomereganRework::NPC_INCENDIARY_BOMB;
            case BombType::Frost:       return GnomereganRework::NPC_FROST_BOMB;
            case BombType::Radioactive: return GnomereganRework::NPC_RADIOACTIVE_BOMB;
            case BombType::BigOne:      return GnomereganRework::NPC_THE_BIG_ONE;
            default:                    return 0;
        }
    }

    // Rule 32: every bomb rule keys by entry, never by name or display.
    constexpr std::optional<BombType> BombTypeOfEntry(std::uint32_t entry)
    {
        if (entry == 0)
            return std::nullopt;
        for (std::size_t i = 0; i < kBombTypeCount; ++i)
            if (BombEntry(static_cast<BombType>(i)) == entry)
                return static_cast<BombType>(i);
        return std::nullopt;
    }

    // The four walking bombs mark a player, walk at them and can be killed (MT3, MT8 to MT11). The hard mode's
    // Duplication (MT16) is theirs only: never The Big One or the Sticky Bomb.
    constexpr bool WalksAtPlayer(BombType type)
    {
        return type == BombType::Walking || type == BombType::Incendiary || type == BombType::Frost
            || type == BombType::Radioactive;
    }

    inline constexpr std::array<std::uint32_t, 4> kWalkingBombEntries{ {
        GnomereganRework::NPC_WALKING_BOMB, GnomereganRework::NPC_INCENDIARY_BOMB, GnomereganRework::NPC_FROST_BOMB,
        GnomereganRework::NPC_RADIOACTIVE_BOMB } };

    // SP 1704: the plates after an Override, The Big One first and the plain Walking Bomb last. KT-G: each plate keeps
    // its face's priority as its DwellSoaks rank at all times (lower is served first).
    constexpr std::int32_t FacePriorityRank(BombType type)
    {
        switch (type)
        {
            case BombType::BigOne:      return 0;
            case BombType::Sticky:      return 1;
            case BombType::Incendiary:  return 2;
            case BombType::Frost:       return 3;
            case BombType::Radioactive: return 4;
            default:                    return 5;
        }
    }

    // Normal plates are all alike: rank 0 for every one keeps the set unranked (DwellSoaks' old path).
    constexpr std::int32_t PlateRank(Mode mode, std::uint32_t face)
    {
        return mode == Mode::Normal ? 0 : FacePriorityRank(FaceBomb(mode, face));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (rule 24: every percent and timer a named constant; percents of the difficulty's reference row; the
    // arrays are by mode: normal, heroic, the Whole Workshop)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        using GnomereganRework::kWarningFloorMs;

        // MT1, MT6 the faces
        inline constexpr std::uint32_t kFaceFirstMs = 10000;
        inline constexpr std::array<std::uint32_t, 3> kFaceEveryMs{ { 20000, 15000, 12000 } };
        inline constexpr std::array<std::uint32_t, 3> kOverrideEveryMs{ { 45000, 45000, 35000 } };
        inline constexpr std::uint32_t kOverrideFacesNormal = 3;        // heroic and up: every closed face (0)

        // MT2 the chutes
        inline constexpr std::uint32_t kBombEveryMs = 8000;
        inline constexpr std::uint32_t kBigOneEveryMs = 16000;
        inline constexpr std::uint32_t kStickyEveryMs = 8000;
        inline constexpr std::uint32_t kBombFirstAfterOpenMs = 2000;    // (guess) SP MT2
        inline constexpr std::uint32_t kBombCapNormal = 8;              // heroic and up: no cap (rule 23)

        // MT3 the Walking Bomb (s7 #31 B: 4.6 yd/s, so the 37 yd walk from the alcove mouth stays 8 s)
        inline constexpr float kBombSpeedYdPerSec = 4.6f;
        inline constexpr float kBombReachYd = 3.f;
        inline constexpr float kBombBlastYd = 8.f;
        inline constexpr float kBlastZBandYd = 6.f;
        inline constexpr std::array<float, 3> kBombBlastPct{ { 40.f, 60.f, 70.f } };
        inline constexpr std::uint32_t kBombWalkMs = 8000;              // SP: "about 8 sec from the wall"
        inline constexpr std::uint32_t kBombFuseMs = 60000;             // (switch, unruled) a kited bomb blows then
        inline constexpr std::uint32_t kBombRingWarnMs = 120000;        // the outline never resolves (canceled first)
        inline constexpr bool kDrawBombRings = true;
        inline constexpr std::uint32_t kBombDespawnMs = 1500;           // the body after its blast look
        inline constexpr std::uint32_t kStopOnControlMs = 1000;         // a stun or a toss halts it (a reward)

        // MT4 the plates (ruling 39, s7 #30 A: 25 yd out on each face's bearing)
        inline constexpr float kPlateTouchYd = 3.f;                     // (guess) the BM Soak disc
        inline constexpr std::uint32_t kLockedOutMs = 30000;            // every mode (ruling 53)

        // MT5 the mines (ruling 41: a 3 yd inner ring sets one off, a 6 yd outer ring is its blast)
        inline constexpr std::array<std::uint32_t, 3> kMineEveryMs{ { 15000, 15000, 12000 } };
        inline constexpr std::uint32_t kMineFirstMs = 8000;             // (guess) SP MT5
        inline constexpr std::uint32_t kMineCountNormal = 3;            // heroic and up: every player (0)
        inline constexpr std::uint32_t kMineArmMs = 3000;
        inline constexpr std::uint32_t kMineGraceMs = 500;
        inline constexpr float kMineTriggerYd = 3.f;
        inline constexpr float kMineBlastYd = 6.f;
        inline constexpr std::array<std::uint32_t, 3> kMineLifeMs{ { 45000, 60000, 75000 } };
        inline constexpr std::array<float, 3> kMinePct{ { 40.f, 60.f, 70.f } };

        // MT7 Knock Away (stock cadence 13-14 s; SP: every 15 s)
        inline constexpr std::uint32_t kKnockFirstMs = 3000;
        inline constexpr std::uint32_t kKnockEveryMs = 15000;
        inline constexpr std::uint32_t kKnockRetryMs = 1000;            // his target out of reach: try again

        // MT9 the fire patch
        inline constexpr float kFirePatchYd = 8.f;
        inline constexpr std::uint32_t kFirePatchMs = 20000;
        inline constexpr std::uint32_t kFirePatchTickMs = 1000;
        inline constexpr float kFirePatchPct = 15.f;

        // MT11 the Radioactive Poison: 4% a second a stack for 12 s (guess; the DT spell carries it in hundredths)
        inline constexpr std::uint32_t kRadioPoisonHundredths = 400;
        inline constexpr std::uint32_t kRadioPoisonMs = 12000;

        // MT12 the Sticky Bomb
        inline constexpr std::uint32_t kStickyFuseMs = 5000;
        inline constexpr float kStickyYd = 8.f;
        inline constexpr std::array<float, 3> kStickyPct{ { 60.f, 60.f, 70.f } };   // normal never builds one

        // MT13 The Big One (s7 #38 h: 3 yd/s; ruling 40)
        inline constexpr float kBigOneSpeedYdPerSec = 3.f;
        inline constexpr float kBigOneYd = 8.f;
        inline constexpr float kBigOnePct = 100.f;
        inline constexpr float kBigOneArriveYd = 1.5f;                  // the log's "arrived" (BigOneBlows)

        // MT14 Remote Detonator (heroic)
        inline constexpr std::uint32_t kDetonatorCastMs = 3000;
        inline constexpr std::uint32_t kDetonatorFirstMs = 20000;       // (guess) SP MT14
        inline constexpr std::array<std::uint32_t, 3> kDetonatorEveryMs{ { 0, 25000, 20000 } };
        inline constexpr std::uint32_t kDetonatorRetryMs = 1000;        // a refused cast (a locked school) retries
        inline constexpr std::uint8_t kDetonatorKickPriority = 3;

        // The bots' boss data: the walking bombs before him for the ranged
        inline constexpr std::int8_t kBombTargetPriority = 2;
        inline constexpr std::uint8_t kFrostRootDispelPriority = 2;
        inline constexpr std::uint8_t kRadioPoisonDispelPriority = 1;

        // His kill line, at most this often (the stock cooldown)
        inline constexpr std::uint32_t kKillLineCooldownMs = 5000;

        // Every warning the players read is at least the 1.5 s floor (SYS 4).
        static_assert(kMineArmMs >= kWarningFloorMs, "a mine arms in no less than 1.5 s");
        static_assert(kBombWalkMs >= kWarningFloorMs, "a bomb walks in no less than 1.5 s");
        static_assert(kStickyFuseMs >= kWarningFloorMs, "the Sticky Bomb's fuse is no less than 1.5 s");
        static_assert(kDetonatorCastMs >= kWarningFloorMs, "the Remote Detonator's bar is no less than 1.5 s");
        static_assert(kKnockEveryMs >= kKnockFirstMs, "Knock Away");
        static_assert(kMineBlastYd > kMineTriggerYd, "ruling 41: the blast ring is larger than the trigger ring");
    }

    // One mode's numbers (SP 1632-1644, and 1799's hard mode column; ruling 53).
    struct ModeValues
    {
        std::uint32_t faceEveryMs;
        std::uint32_t overrideEveryMs;
        std::uint32_t overrideFaces;        // 0: every closed face
        std::uint32_t bombCap;              // 0: no cap
        std::uint32_t bombHealth;
        float blastPct;
        bool blowWhenKilled;                // MT8
        bool typedFaces;                    // MT9 to MT13
        std::uint32_t mineEveryMs;
        std::uint32_t mineCount;            // 0: every player
        std::uint32_t mineLifeMs;
        float minePct;
        std::uint32_t detonatorEveryMs;     // 0: none
        float stickyPct;
    };

    constexpr ModeValues ValuesFor(Mode mode)
    {
        std::size_t const i = ModeIndex(mode);
        bool const normal = mode == Mode::Normal;
        return ModeValues{
            Tune::kFaceEveryMs[i],
            Tune::kOverrideEveryMs[i],
            normal ? Tune::kOverrideFacesNormal : 0,
            normal ? Tune::kBombCapNormal : 0,
            mode == Mode::HardMode ? GnomereganRework::Health::kWalkingBombHardMode
                : GnomereganRework::Health::kWalkingBomb(!normal),
            Tune::kBombBlastPct[i],
            !normal,
            !normal,
            Tune::kMineEveryMs[i],
            normal ? Tune::kMineCountNormal : 0,
            Tune::kMineLifeMs[i],
            Tune::kMinePct[i],
            Tune::kDetonatorEveryMs[i],
            Tune::kStickyPct[i],
        };
    }

    // How often a face's chute builds (MT2): The Big One every 16 s, the rest every 8 s.
    constexpr std::uint32_t ChuteEveryMs(BombType type)
    {
        return type == BombType::BigOne ? Tune::kBigOneEveryMs
            : type == BombType::Sticky ? Tune::kStickyEveryMs : Tune::kBombEveryMs;
    }

    // The blast of a walking bomb type: the spell, its school (SharedDefines SpellSchools) and its rider.
    struct BlastKind
    {
        std::uint32_t spellId;
        std::uint8_t school;
        std::uint32_t rider;
    };

    constexpr BlastKind BlastOf(BombType type)
    {
        switch (type)
        {
            case BombType::Incendiary:  return { SPELL_MT_INCENDIARY_BLAST, 2, 0 };
            case BombType::Frost:       return { SPELL_MT_FROST_BLAST, 4, SPELL_MT_FROST_ROOT };
            case BombType::Radioactive: return { SPELL_MT_RADIO_BLAST, 3, SPELL_MT_RADIO_POISON };
            case BombType::BigOne:      return { SPELL_MT_BIG_ONE_BLAST, 2, 0 };
            case BombType::Sticky:      return { SPELL_MT_STICKY_BLAST, 2, 0 };
            default:                    return { SPELL_MT_BOMB_BLAST, 2, 0 };
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Clocks and picks
    // ----------------------------------------------------------------------------------------------------------------

    // RB-17: the next due time of a beat that fired at `now` (it was due at `due`): one period on, never closer than
    // half a period to now (a late beat never fires twice in a row and never starves another).
    constexpr std::uint64_t NextDue(std::uint64_t due, std::uint32_t period, std::uint64_t now)
    {
        return std::max<std::uint64_t>(due + period, now + period / 2);
    }

    using FaceMask = std::array<bool, GnomereganRework::kFaceCount>;

    constexpr std::uint32_t OpenCount(FaceMask const& open)
    {
        std::uint32_t n = 0;
        for (bool const o : open)
            n += o ? 1 : 0;
        return n;
    }

    // `count` distinct closed faces at random (0: every closed face, in face order); fewer when fewer are closed.
    // `rand(n)` returns [0, n).
    template <class Rand>
    std::vector<std::uint32_t> PickClosedFaces(FaceMask const& open, std::uint32_t count, Rand&& rand)
    {
        std::vector<std::uint32_t> closed;
        for (std::uint32_t i = 0; i < GnomereganRework::kFaceCount; ++i)
            if (!open[i])
                closed.push_back(i);
        if (count == 0 || count >= closed.size())
            return closed;
        std::vector<std::uint32_t> picked;
        while (picked.size() < count)
        {
            std::size_t const at = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(closed.size())))
                % closed.size();
            picked.push_back(closed[at]);
            closed.erase(closed.begin() + static_cast<std::ptrdiff_t>(at));
        }
        return picked;
    }

    // MT2: a due chute builds unless the normal cap of living bombs is reached (the due bomb is skipped, not queued).
    constexpr bool ChuteMayBuild(std::uint32_t cap, std::uint32_t aliveBombs)
    {
        return cap == 0 || aliveBombs < cap;
    }

    // MT5: how many players get a mine (normal 3, heroic and up every player).
    constexpr std::uint32_t MineTargets(std::uint32_t count, std::uint32_t players)
    {
        return count == 0 ? players : std::min(count, players);
    }

    // The blasts' reach: 2D within `radius` and within `zBand` above or below.
    inline bool InBlast(DungeonKit::Vec2 center, float centerZ, DungeonKit::Vec2 p, float pZ, float radius,
        float zBand)
    {
        return DungeonKit::Distance(center, p) <= radius && std::fabs(pZ - centerZ) <= zBand;
    }

    // MT13 (ruling 40, s7 #38 h): The Big One's 100% is split evenly among the players within 8 yd of it; with nobody
    // there the whole fight takes the full blast (designer question 1). The percent each player in `inside` takes, or
    // with `inside` 0 the percent every player of the fight takes.
    constexpr float BigOneSharePct(std::uint32_t inside, float totalPct)
    {
        return inside == 0 ? totalPct : totalPct / static_cast<float>(inside);
    }

    // MT13 (F-1d, STAGE-R-1-C Minor-2): the bots' Stack on The Big One resolves when its walk to the center should end
    // (the straight walk's time, never under the warning floor), and the bomb blows then, wherever it is: on time it is
    // at the center; a point move that ends short holds it there until then; a slower walk blows on the way, under the
    // Stack that follows it. The Stack, the drill's row (the Stack lands at the arrival) and the blast agree, and no
    // walk outlives its Stack.
    constexpr std::uint32_t BigOneStackMs(std::uint32_t walkMs)
    {
        return walkMs < Tune::kWarningFloorMs ? Tune::kWarningFloorMs : walkMs;
    }

    constexpr bool BigOneBlows(std::uint64_t ageMs, std::uint32_t stackMs)
    {
        return ageMs >= stackMs;
    }

    // Milliseconds a walker needs over `distanceYd` at `speedYdPerSec`.
    constexpr std::uint32_t WalkMs(float distanceYd, float speedYdPerSec)
    {
        return speedYdPerSec <= 0.f ? 0 : static_cast<std::uint32_t>(distanceYd / speedYdPerSec * 1000.f + 0.5f);
    }

    // A plate takes a touch while its face is open and the toucher is not Locked Out (MT4).
    constexpr bool PlateTakes(bool faceOpen, bool lockedOut)
    {
        return faceOpen && !lockedOut;
    }

    // The hard mode packages' damage factors (ThermapluggFight.h DamageFactor): the product, never below 0.
    inline float CombinedFactor(std::vector<float> const& factors)
    {
        float f = 1.f;
        for (float const x : factors)
            f *= std::max(0.f, x);
        return f;
    }

    // The packages' health thresholds (MT15: 90 / 75 / 60 / 45 / 30): each fires once per pull, highest first, when
    // his health falls to or under it.
    class ThresholdLatch
    {
    public:
        void Arm(std::vector<float> thresholds)
        {
            _left = std::move(thresholds);
            std::sort(_left.begin(), _left.end(), [](float a, float b) { return a > b; });
        }

        // The thresholds crossed now, highest first; each only once.
        std::vector<float> Crossed(float healthPct)
        {
            std::vector<float> out;
            while (!_left.empty() && healthPct <= _left.front())
            {
                out.push_back(_left.front());
                _left.erase(_left.begin());
            }
            return out;
        }

        std::size_t Left() const { return _left.size(); }
        void Clear() { _left.clear(); }

    private:
        std::vector<float> _left;
    };
}

#endif
